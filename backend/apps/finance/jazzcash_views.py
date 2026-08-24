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
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.models import record_audit

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

        invoice = Invoice.objects.filter(id=invoice_id).first()

        if invoice is None:
            return JsonResponse(
                {"detail": "Invoice not found."},
                status=404,
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

        return JsonResponse({
            "post_url": config["post_url"],
            "params": params,
        })


@csrf_exempt
@require_POST
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

    if hmac.compare_digest(received_hash, expected):
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
        receipt_number=next_receipt_number(),
        invoice=invoice,
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
