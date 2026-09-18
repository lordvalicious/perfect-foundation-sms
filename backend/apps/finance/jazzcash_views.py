"""JazzCash hosted-checkout integration.

Follows the Stripe pattern: create a checkout request, then a
server-to-server callback confirms the payment. Credentials come from
environment variables:

    JAZZCASH_MERCHANT_ID      (pp_MerchantId)
    JAZZCASH_PASSWORD         (pp_Password)
    JAZZCASH_INTEGRITY_SALT   (integer salt for the secure hash)
    JAZZCASH_ENV              "sandbox" (default) or "live"

When credentials are missing the checkout endpoint answers 503 so the
UI can hide/disable JazzCash payments.
"""

import hashlib
import hmac
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope
from apps.audit.models import record_audit

from .decorators import require_post_json
from .models import Invoice, Payment
from .services import next_receipt_number

logger = logging.getLogger(__name__)

SANDBOX_URL = (
    "https://sandbox.jazzcash.com.pk/CustomerPortal/transactionmanagement/merchantform"
)
LIVE_URL = (
    "https://payments.jazzcash.com.pk/CustomerPortal/transactionmanagement/merchantform"
)

# How long the customer has to complete payment at the portal.
_EXPIRY_HOURS = 1


def jazzcash_config():
    merchant_id = os.environ.get("JAZZCASH_MERCHANT_ID", "")
    password = os.environ.get("JAZZCASH_PASSWORD", "")
    salt = os.environ.get("JAZZCASH_INTEGRITY_SALT", "")

    if not (merchant_id and password and salt):
        return None

    return {
        "merchant_id": merchant_id,
        "password": password,
        "salt": salt,
        "post_url": LIVE_URL
        if os.environ.get("JAZZCASH_ENV") == "live"
        else SANDBOX_URL,
    }


def _secure_hash(params, salt):
    """HMAC-SHA256 over '&'joined values in the documented order."""
    message = "&".join(str(value) for value in params.values())
    return hmac.new(
        salt.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest().upper()


def _timestamp_parts():
    now = timezone.now()
    expiry = now + timedelta(hours=_EXPIRY_HOURS)

    return (
        now.strftime("%Y%m%d%H%M%S"),
        expiry.strftime("%Y%m%d%H%M%S"),
    )


def build_checkout_params(config, invoice, request, reference, now_stamp, expiry_stamp):
    """Construct the signed JazzCash merchant-form parameter set.

    This runs entirely server-side: the merchant password and integrity
    salt are consumed here and must never be returned to a client.
    """
    return {
        "pp_Version": "1.1",
        "pp_TxnType": "MWALLET",
        "pp_Language": "EN",
        "pp_MerchantId": config["merchant_id"],
        "pp_SubMerchantId": "",
        "pp_Password": config["password"],
        "pp_BillReference": invoice.invoice_number,
        "pp_Description": f"School fees {invoice.invoice_number}",
        "pp_TxnRefNo": reference,
        "pp_Amount": int(invoice.balance * 100),
        "pp_TxnDateTime": now_stamp,
        "pp_BillExpiryDate": expiry_stamp,
        "pp_TxnExpiryDateTime": expiry_stamp,
        "pp_ReturnURL": request.build_absolute_uri(
            "/api/finance/jazzcash/callback/"
        ),
        "ppmpf_1": str(invoice.id),
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Capture the gateway's redirect instead of following it server-side."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_REDIRECT_CODES = {301, 302, 303, 307, 308}


def submit_checkout_to_gateway(post_url, params):
    """POST the signed checkout to the JazzCash portal server-side.

    Returns ``(checkout_url, error)``. On a redirect the gateway's target
    URL is returned so the client can continue at the hosted payment page;
    on any other outcome an ``error`` string is returned and the secret
    parameter set never reaches the client.
    """
    encoded = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(post_url, data=encoded, method="POST")

    try:
        opener = urllib.request.build_opener(_NoRedirect)
        with opener.open(req, timeout=20) as response:
            status = getattr(response, "status", 200)
            if status in _REDIRECT_CODES:
                location = response.headers.get("Location")
                if location:
                    return response.geturl() + location if False else location, None
            return None, f"gateway_http_{status}"
    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location")
        if exc.code in _REDIRECT_CODES and location:
            return location, None
        logger.warning(
            "JazzCash checkout submission returned HTTP %s", exc.code
        )
        return None, f"gateway_http_{exc.code}"
    except Exception as exc:
        logger.warning("JazzCash checkout submission failed: %s", exc)
        return None, "gateway_unreachable"


class JazzCashCheckoutView(APIView):
    """POST {invoice_id} -> signed parameter set for the JazzCash form."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        config = jazzcash_config()

        if config is None:
            return JsonResponse(
                {
                    "detail": (
                        "JazzCash is not configured. Set JAZZCASH_MERCHANT_ID, "
                        "JAZZCASH_PASSWORD and JAZZCASH_INTEGRITY_SALT."
                    )
                },
                status=503,
            )

        invoice_id = request.data.get("invoice_id")

        if not invoice_id:
            return JsonResponse(
                {"detail": "invoice_id is required."},
                status=400,
            )

        from django.shortcuts import get_object_or_404
        invoice = get_object_or_404(
            apply_campus_scope(Invoice.objects.all(), request),
            pk=invoice_id,
        )

        balance = invoice.balance

        if balance <= 0:
            return JsonResponse(
                {"detail": "Invoice has no outstanding balance."},
                status=400,
            )

        now_stamp, expiry_stamp = _timestamp_parts()
        amount = int(balance * 100)  # paisa, no decimals

        reference = f"JC-{invoice.invoice_number}-{now_stamp}"

        params = {
            "pp_Version": "1.1",
            "pp_TxnType": "MWALLET",
            "pp_Language": "EN",
            "pp_MerchantId": config["merchant_id"],
            "pp_SubMerchantId": "",
            "pp_Password": config["password"],
            "pp_BillReference": invoice.invoice_number,
            "pp_Description": f"School fees {invoice.invoice_number}",
            "pp_TxnRefNo": reference,
            "pp_Amount": amount,
            "pp_TxnDateTime": now_stamp,
            "pp_BillExpiryDate": expiry_stamp,
            "pp_TxnExpiryDateTime": expiry_stamp,
            "pp_ReturnURL": request.build_absolute_uri(
                "/api/finance/jazzcash/callback/"
            ),
            "ppmpf_1": str(invoice.id),
        }

        params["pp_SecureHash"] = _secure_hash(params, config["salt"])

        record_audit(
            action="payment",
            model_name="Invoice",
            object_id=str(invoice.pk),
            object_repr=str(invoice),
            details={
                "gateway": "jazzcash",
                "reference": reference,
                "amount": str(balance),
            },
        )

        checkout_url, gateway_error = submit_checkout_to_gateway(
            config["post_url"], params
        )

        if gateway_error:
            logger.warning(
                "JazzCash checkout submission failed: %s", gateway_error
            )
            return JsonResponse(
                {
                    "detail": "Could not start the JazzCash checkout.",
                    "code": gateway_error,
                },
                status=502,
            )

        return JsonResponse({
            "checkout_url": checkout_url,
            "invoice_id": invoice.id,
            "reference": reference,
        })


@require_post_json
def jazzcash_callback(request):
    """Server-to-server response from JazzCash.

    Verifies pp_SecureHash then records a completed Payment when the
    response code is '000' (success). Idempotent on pp_TxnRefNo.
    """
    config = jazzcash_config()

    if config is None:
        return JsonResponse({"detail": "JazzCash not configured."}, status=503)

    received_hash = str(request.POST.get("pp_SecureHash", ""))
    response_code = str(request.POST.get("pp_ResponseCode", ""))
    reference = str(request.POST.get("pp_TxnRefNo", ""))

    verification = {
        key: value
        for key, value in request.POST.items()
        if key != "pp_SecureHash"
    }

    expected = _secure_hash(verification, config["salt"])

    if not hmac.compare_digest(received_hash, expected):
        logger.warning(
            "JazzCash callback hash mismatch for %s", reference
        )
        return JsonResponse({"detail": "Invalid signature."}, status=400)

    invoice_id = request.POST.get("ppmpf_1")

    try:
        invoice = Invoice.objects.get(id=int(invoice_id or 0))
    except (Invoice.DoesNotExist, ValueError, TypeError):
        logger.warning(
            "JazzCash callback references invalid invoice %s", invoice_id
        )
        return JsonResponse({"detail": "Unknown invoice."}, status=400)

    existing = Payment.objects.filter(reference__endswith=reference).first()

    if existing:
        return JsonResponse({"status": "already processed"})

    if response_code != "000":
        logger.info(
            "JazzCash payment failed (%s) for %s", response_code, reference
        )
        return JsonResponse({"status": "declined", "code": response_code})

    amount_paisa = int(request.POST.get("pp_Amount", "0") or 0)
    amount = max(amount_paisa, int(invoice.balance * 100)) / 100

    payment = Payment(
        receipt_number=next_receipt_number(invoice.institution),
        invoice=invoice,
        institution=invoice.institution,
        campus=invoice.campus,
        amount=amount,
        payment_date=timezone.now().date(),
        payment_method="jazzcash",
        status="completed",
        reference=f"JazzCash: {reference}",
    )
    payment.save()

    record_audit(
        action="payment",
        model_name="Payment",
        object_id=str(payment.pk),
        object_repr=str(payment),
        details={
            "receipt_number": payment.receipt_number,
            "invoice": invoice.invoice_number,
            "amount": str(payment.amount),
            "method": "jazzcash",
            "txn_ref": reference,
        },
    )

    return JsonResponse({"status": "ok"})
