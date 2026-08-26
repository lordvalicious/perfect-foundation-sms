"""EasyPaisa (Easypay) hosted-checkout integration.

Mirrors the JazzCash views. Credentials via environment:

    EASYPAISA_STORE_ID     merchant store id
    EASYPAISA_STORE_KEY    secret key used for AES-128/ECB hashing
    EASYPAISA_ENV          "sandbox" (default) or "live"

The request hash is the documented AES-128/ECB/PKCS5 base64 encoding of
the sorted ``key=value`` parameters joined by '&'. The callback
confirms the transaction server-to-server against Easypay's ConfirmURL.
"""

import base64
import json
import logging
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.models import record_audit

from .decorators import require_post_json
from .models import Invoice, Payment
from .services import next_receipt_number

logger = logging.getLogger(__name__)

SANDBOX_INDEX_URL = "https://easypay.easypaisa.com.pk/easypay/Index.jsf"
LIVE_INDEX_URL = "https://easypay.easypaisa.com.pk/easypay-service/ez/dev/Index"
CONFIRM_URL = (
    "https://easypay.easypaisa.com.pk/easypay-service/ez/dev/Confirm"
)


def easypaisa_config():
    store_id = os.environ.get("EASYPAISA_STORE_ID", "")
    store_key = os.environ.get("EASYPAISA_STORE_KEY", "")

    if not (store_id and store_key):
        return None

    return {
        "store_id": store_id,
        "store_key": store_key,
        "index_url": LIVE_INDEX_URL
        if os.environ.get("EASYPAISA_ENV") == "live"
        else SANDBOX_INDEX_URL,
    }


def _request_hash(params, key):
    plain = "&".join(
        f"{name}={params[name]}" for name in sorted(params)
    )

    cipher = AES.new(key.encode(), AES.MODE_ECB)

    return base64.b64encode(
        cipher.encrypt(pad(plain.encode(), AES.block_size))
    ).decode()


def _confirm_transaction(auth_token):
    """Server-to-server confirmation with Easypay."""
    config = easypaisa_config()

    if config is None:
        return None

    payload = urllib.parse.urlencode({
        "storeId": config["store_id"],
        "authToken": auth_token,
    }).encode()

    try:
        with urllib.request.urlopen(
            CONFIRM_URL,
            data=payload,
            timeout=30,
        ) as response:
            return json.loads(response.read().decode())
    except Exception as exc:
        logger.warning("Easypay confirm failed: %s", exc)
        return None


class EasyPaisaCheckoutView(APIView):
    """POST {invoice_id} -> signed parameter set for the Easypay form."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        config = easypaisa_config()

        if config is None:
            return JsonResponse(
                {
                    "detail": (
                        "EasyPaisa is not configured. Set "
                        "EASYPAISA_STORE_ID and EASYPAISA_STORE_KEY."
                    )
                },
                status=503,
            )

        invoice_id = request.data.get("invoice_id")

        if not invoice_id:
            return JsonResponse(
                {"detail": "invoice_id is required."}, status=400
            )

        invoice = Invoice.objects.filter(id=invoice_id).first()

        if invoice is None:
            return JsonResponse(
                {"detail": "Invoice not found."}, status=404
            )

        balance = invoice.balance

        if balance <= 0:
            return JsonResponse(
                {"detail": "Invoice has no outstanding balance."},
                status=400,
            )

        expiry = timezone.now() + timedelta(hours=1)

        order_ref = (
            f"EP-{invoice.invoice_number}-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        params = {
            "storeId": config["store_id"],
            "amount": f"{balance:.0f}",
            "postBackURL": request.build_absolute_uri(
                "/api/finance/easypaisa/callback/"
            ),
            "orderRefNum": order_ref,
            "expiryDate": expiry.strftime("%Y%m%d %H%M%S"),
            "autoRedirect": "1",
            "emailAddr": (
                request.user.email
                or "no-reply@perfectfoundation.edu"
            ),
            "mobileNum": request.user.phone or "",
        }

        params["merchantHashedReq"] = _request_hash(
            params,
            config["store_key"],
        )

        record_audit(
            action="payment",
            model_name="Invoice",
            object_id=str(invoice.pk),
            object_repr=str(invoice),
            details={
                "gateway": "easypaisa",
                "reference": order_ref,
                "amount": str(balance),
            },
        )

        return JsonResponse({
            "post_url": config["index_url"],
            "params": params,
        })


@require_post_json
def easypaisa_callback(request):
    """Customer return + confirmation from Easypay.

    A successful response carries statusToken '0000'. We confirm
    server-to-server before recording a completed Payment. Idempotent
    on orderRefNumber.
    """
    auth_token = request.POST.get("authToken", "")
    order_ref = request.POST.get("orderRefNumber", "")
    response_code = request.POST.get("statusToken", "")

    if not auth_token:
        return JsonResponse({"detail": "Missing authToken."}, status=400)

    confirmation = _confirm_transaction(auth_token)

    if not confirmation:
        return JsonResponse(
            {"detail": "Could not confirm transaction."}, status=400
        )

    invoice_number = order_ref.split("-")[1] if "-" in order_ref else ""
    invoice = Invoice.objects.filter(invoice_number=invoice_number).first()

    if invoice is None:
        logger.warning(
            "Easypay callback references unknown invoice %s", invoice_number
        )
        return JsonResponse({"detail": "Unknown invoice."}, status=400)

    existing = Payment.objects.filter(
        reference__endswith=order_ref
    ).first()

    if existing:
        return JsonResponse({"status": "already processed"})

    confirmed = str(
        confirmation.get("responseCode")
        or confirmation.get("statusToken")
        or ""
    )

    if confirmed != "0000":
        logger.info(
            "Easypay payment not confirmed (%s) for %s",
            confirmed,
            order_ref,
        )
        return JsonResponse({"status": "declined", "code": confirmed})

    payment = Payment(
        receipt_number=next_receipt_number(),
        invoice=invoice,
        amount=invoice.balance,
        payment_date=timezone.now().date(),
        payment_method="easypaisa",
        status="completed",
        reference=f"EasyPaisa: {order_ref}",
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
            "method": "easypaisa",
            "order_ref": order_ref,
        },
    )

    return JsonResponse({"status": "ok"})
