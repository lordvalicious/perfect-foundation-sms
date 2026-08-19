"""SMS sending service with Twilio backend.

Falls back to console logging when Twilio credentials are not configured,
making local development and testing easy without a Twilio account.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(to_number, message):
    """Send an SMS to *to_number*.

    Returns (success: bool, error: str | None).
    """
    to_number = (to_number or "").strip()

    if not to_number:
        return False, "No phone number provided."

    if not message or not message.strip():
        return False, "Empty message."

    sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    from_number = getattr(settings, "TWILIO_PHONE_NUMBER", "")

    if not all([sid, token, from_number]):
        logger.info(
            "SMS (console fallback) to %s: %s",
            to_number,
            message[:120],
        )
        return True, None

    try:
        from twilio.rest import Client

        client = Client(sid, token)
        client.messages.create(
            body=message,
            from_=from_number,
            to=to_number,
        )
        return True, None

    except Exception as exc:
        logger.error("Twilio SMS failed to %s: %s", to_number, exc)
        return False, str(exc)


def send_bulk_sms(phone_and_message_pairs):
    """Send SMS to a list of (phone_number, message) tuples.

    Returns a list of (phone, success, error) tuples.
    """
    results = []

    for phone, message in phone_and_message_pairs:
        ok, err = send_sms(phone, message)
        results.append((phone, ok, err))

    return results
