"""Email verification endpoints.

Accounts are provisioned by administrators; every account should confirm the
email address on it before first use. ``SendView`` mails a single-use,
expiring link; ``ConfirmView`` marks the account verified when the link is
opened. Works with the frontend SPA page ``/verify-email``.
"""

import os
import secrets

from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.audit.models import record_audit

from .models import EmailVerification

VERIFY_TOKEN_HOURS = 24


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Session auth without CSRF for token-bearing public endpoints.

    The emailed link token inside the request body is the credential here,
    so requiring a CSRF header would break one-click clicks from new tabs
    while the user is already logged in to the app.
    """

    def enforce_csrf(self, request):
        return None


def build_verification_url(token, origin=None):
    if origin:
        return origin.rstrip("/") + f"/verify-email?token={token}"
    env_origin = os.environ.get("EMAIL_VERIFY_ORIGIN", "").strip()
    if env_origin:
        return env_origin.rstrip("/") + f"/verify-email?token={token}"
    return f"/verify-email?token={token}"


def send_verification_email(user, request=None, origin=None):
    """Create a fresh token and mail the verification link to the user."""
    stale = EmailVerification.objects.filter(user=user).exclude(
        used=True, expires_at__gt=timezone.now()
    )
    stale.delete()

    token_url = secrets.token_urlsafe(32)

    EmailVerification.objects.create(
        user=user,
        token=token_url,
        expires_at=timezone.now() + timezone.timedelta(hours=VERIFY_TOKEN_HOURS),
    )

    if origin is None and request is not None:
        origin = request.build_absolute_uri("/")

    verify_url = build_verification_url(token_url, origin)

    send_mail(
        subject=f"Verify your email — {user.get_full_name() or user.username}",
        message=(
            "You (or an administrator) set up this account with your email "
            "address.\n\n"
            "Open the link below to confirm this address is yours:\n"
            f"{verify_url}\n\n"
            "This link expires in 24 hours. If you did not expect this "
            "email, you can ignore it."
        ),
        from_email=None,
        recipient_list=[user.email],
    )


class EmailVerificationSendView(APIView):
    """POST /api/auth/email-verify/send/ -> email a verification link."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email_verify"

    def post(self, request):
        user = request.user

        if user.email_verified:
            return Response(
                {"detail": "Your email address is already verified."},
                status=400,
            )

        if not user.email:
            return Response(
                {"detail": "This account does not have an email address."},
                status=400,
            )

        try:
            send_verification_email(user, request)
        except Exception:
            return Response(
                {
                    "detail": (
                        "The verification email could not be sent. Please "
                        "try again in a few minutes or contact the school "
                        "office."
                    )
                },
                status=400,
            )

        return Response(
            {"detail": "A verification link has been sent to your email."}
        )


class EmailVerificationConfirmView(APIView):
    """POST /api/auth/email-verify/confirm/ {token} -> mark email verified.

    The random link token in the body is the credential, so the endpoint is
    CSRF-exempt: a logged-in user may still open the emailed link directly
    in a new tab without a CSRF token.
    """

    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email_verify"

    def post(self, request):
        token = (request.data.get("token") or "").strip()

        if not token:
            return Response(
                {"detail": "A verification token is required."}, status=400
            )

        verification = EmailVerification.objects.filter(token=token).first()

        if verification is None or not verification.is_valid:
            return Response(
                {
                    "detail": (
                        "This verification link is invalid or has expired. "
                        "Request a new one from your account page."
                    )
                },
                status=400,
            )

        user = verification.user

        verification.used = True
        verification.save(update_fields=["used"])

        user.email_verified = True
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified", "email_verified_at"])

        record_audit(
            request=request,
            user=user,
            action="email_verified",
            details={"method": "email-link"},
        )

        return Response({"detail": "Your email address has been verified."})