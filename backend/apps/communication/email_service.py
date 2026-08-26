"""Outbound email helpers built on Django's SMTP backend."""

import logging

from django.conf import settings
from django.core.mail import get_connection, send_mail

logger = logging.getLogger(__name__)


def email_configured():
    return bool(getattr(settings, "EMAIL_HOST", ""))


def send_email_message(recipient_email, subject, body,
                       from_name=None, from_address=None,
                       connection=None):
    """Send one email. Returns (ok: bool, error: str).

    ``from_name`` / ``from_address`` optionally override the platform
    DEFAULT_FROM_EMAIL for white-label sending (per-school branding).
    ``connection`` lets callers reuse one SMTP session for a batch,
    which keeps bulk sends well inside serverless time limits.
    """
    if not email_configured():
        return False, "Email is not configured (DJANGO_EMAIL_HOST missing)."

    sender = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    if from_address:
        sender = (
            f'"{from_name}" <{from_address}>' if from_name else from_address
        )

    try:
        conn = connection or get_connection(timeout=10)
        sent = send_mail(
            subject=subject,
            message=body,
            from_email=sender,
            recipient_list=[recipient_email],
            fail_silently=False,
            connection=conn,
        )
        return sent > 0, "" if sent else "No email was sent."
    except Exception as exc:
        logger.warning("Email to %s failed: %s", recipient_email, exc)
        return False, str(exc)
