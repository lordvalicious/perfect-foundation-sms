"""TOTP two-factor authentication endpoints."""

import pyotp
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class TwoFAStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "enabled": bool(request.user.twofa_enabled),
        })


class TwoFASetupView(APIView):
    """Generate (or regenerate) the TOTP secret for this account.

    Returns the secret and an otpauth:// URI. The user adds it to an
    authenticator app, then confirms with a code via /activate/.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.twofa_secret:
            user.twofa_secret = pyotp.random_base32()
            user.save(update_fields=["twofa_secret"])

        uri = pyotp.totp.TOTP(user.twofa_secret).provisioning_uri(
            name=user.email or user.username,
            issuer_name=(
                getattr(request, "institution", None).name
                if getattr(request, "institution", None)
                else "School Management"
            ),
        )

        return Response({
            "secret": user.twofa_secret,
            "otpauth_uri": uri,
            "enabled": user.twofa_enabled,
        })


class TwoFAActivateView(APIView):
    """Confirm a code from the authenticator app to enable 2FA."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = str(request.data.get("code") or "").strip()
        user = request.user

        if not user.twofa_secret:
            return Response(
                {"detail": "Call setup first."}, status=400
            )

        totp = pyotp.TOTP(user.twofa_secret)

        if not totp.verify(code, valid_window=1):
            return Response(
                {"detail": "Invalid or expired code."}, status=400
            )

        user.twofa_enabled = True
        user.save(update_fields=["twofa_enabled"])

        return Response({"enabled": True})


class TwoFADisableView(APIView):
    """Disable 2FA. Requires the account password."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get("password") or ""
        user = request.user

        if not authenticate(
            request=request,
            username=user.username,
            password=password,
        ):
            return Response(
                {"detail": "Password is incorrect."}, status=400
            )

        user.twofa_enabled = False
        user.twofa_secret = ""
        user.save(update_fields=["twofa_enabled", "twofa_secret"])

        return Response({"enabled": False})
