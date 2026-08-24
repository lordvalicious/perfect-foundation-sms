"""Outbound email helpers built on Django's SMTP backend."""

import logging

from django.conf import settings
from django.core.mail import get_connection, send_mail

logger = logging.getLogger(__name__)


def email_configured():
    return bool(getattr(settings, "EMAIL_HOST", ""))


def send_email_message(recipient_email, subject, body):
    """Send one email. Returns (ok: bool, error: str)."""
    if not email_configured():
        return False, "Email is not configured (DJANGO_EMAIL_HOST missing)."

    try:
        connection = get_connection(fail_silently=False)
        sent = send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[recipient_email],
            fail_silently=False,
            connection=connection,
        )
        return sent > 0, "" if sent else "No email was sent."
    except Exception as exc:
        logger.warning("Email to %s failed: %s", recipient_email, exc)
        return False, str(exc)
