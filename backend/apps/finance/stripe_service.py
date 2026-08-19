"""Stripe payment integration for online fee collection."""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def create_checkout_session(invoice, success_url, cancel_url):
    """Create a Stripe Checkout Session for an invoice.

    Returns (session_id, session_url, error).
    """
    secret_key = getattr(settings, "STRIPE_SECRET_KEY", "")

    if not secret_key:
        return None, None, "Stripe is not configured."

    try:
        import stripe

        stripe.api_key = secret_key

        balance = invoice.balance
        if balance <= 0:
            return None, None, "Invoice has no outstanding balance."

        student_name = ""
        if invoice.student:
            student_name = invoice.student.full_name or ""

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "pkr",
                        "product_data": {
                            "name": f"Invoice {invoice.invoice_number}",
                            "description": (
                                f"Fee payment for {student_name}"
                                if student_name
                                else f"Fee payment - {invoice.invoice_number}"
                            ),
                        },
                        "unit_amount": int(balance * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "student_name": student_name,
            },
        )

        return session.id, session.url, None

    except Exception as exc:
        logger.error("Stripe checkout failed for invoice %s: %s", invoice.id, exc)
        return None, None, str(exc)


def retrieve_session(session_id):
    """Retrieve a Stripe Checkout Session by ID.

    Returns (session, error).
    """
    secret_key = getattr(settings, "STRIPE_SECRET_KEY", "")

    if not secret_key:
        return None, "Stripe is not configured."

    try:
        import stripe

        stripe.api_key = secret_key
        session = stripe.checkout.Session.retrieve(session_id)
        return session, None

    except Exception as exc:
        logger.error("Stripe session retrieval failed: %s", exc)
        return None, str(exc)


def construct_webhook_event(payload, sig_header):
    """Verify and construct a Stripe webhook event.

    Returns (event, error).
    """
    secret_key = getattr(settings, "STRIPE_SECRET_KEY", "")
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    if not secret_key:
        return None, "Stripe is not configured."

    try:
        import stripe

        stripe.api_key = secret_key

        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            event = stripe.Event.construct_from(
                stripe.api_key, payload
            )

        return event, None

    except Exception as exc:
        logger.error("Stripe webhook verification failed: %s", exc)
        return None, str(exc)
