"""Stripe payment views: checkout session creation and webhook handler."""

import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.models import record_audit
from apps.students.models import Student

from .models import Invoice, Payment
from .services import next_receipt_number
from .stripe_service import construct_webhook_event, create_checkout_session

logger = logging.getLogger(__name__)


class StripeCheckoutView(APIView):
    """POST to create a Stripe Checkout Session for an invoice.

    Body:
        invoice_id: int
        success_url: str (optional, default: /finance?paid=1)
        cancel_url: str (optional, default: /finance?cancelled=1)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        invoice_id = request.data.get("invoice_id")
        success_url = request.data.get(
            "success_url",
            f"{request.build_absolute_uri('/').rstrip('/')}/finance?paid=1",
        )
        cancel_url = request.data.get(
            "cancel_url",
            f"{request.build_absolute_uri('/').rstrip('/')}/finance?cancelled=1",
        )

        if not invoice_id:
            return JsonResponse(
                {"detail": "invoice_id is required."},
                status=400,
            )

        try:
            invoice = Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            return JsonResponse(
                {"detail": "Invoice not found."},
                status=404,
            )

        if invoice.balance <= 0:
            return JsonResponse(
                {"detail": "Invoice has no outstanding balance."},
                status=400,
            )

        session_id, session_url, error = create_checkout_session(
            invoice,
            success_url=f"{success_url}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url,
        )

        if error:
            return JsonResponse({"detail": error}, status=400)

        return JsonResponse({
            "session_id": session_id,
            "session_url": session_url,
        })


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events.

    Verifies the signature and creates a Payment record on
    checkout.session.completed.
    """
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    payload = request.body

    event, error = construct_webhook_event(payload, sig_header)

    if error:
        logger.warning("Webhook verification failed: %s", error)
        return JsonResponse({"detail": error}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        _handle_checkout_completed(session)

    return JsonResponse({"status": "ok"})


def _handle_checkout_completed(session):
    """Process a successful Stripe Checkout Session."""
    session_id = session.get("id", "")
    invoice_id = session.get("metadata", {}).get("invoice_id")

    if not invoice_id:
        logger.warning(
            "Checkout session %s missing invoice_id metadata", session_id
        )
        return

    try:
        invoice = Invoice.objects.get(id=int(invoice_id))
    except (Invoice.DoesNotExist, ValueError, TypeError):
        logger.warning(
            "Checkout session %s references invalid invoice %s",
            session_id,
            invoice_id,
        )
        return

    existing = Payment.objects.filter(stripe_session_id=session_id).first()
    if existing:
        return

    amount = invoice.balance
    if amount <= 0:
        return

    payment = Payment(
        receipt_number=next_receipt_number(),
        invoice=invoice,
        amount=amount,
        payment_date=timezone.now().date(),
        payment_method="stripe",
        status="completed",
        reference=f"Stripe: {session_id}",
        stripe_session_id=session_id,
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
            "method": "stripe",
        },
    )

    logger.info(
        "Stripe payment created: %s for invoice %s",
        payment.receipt_number,
        invoice.invoice_number,
    )
