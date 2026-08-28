"""TOTP two-factor authentication endpoints."""

import pyotp
import secrets
import hashlib
from django.contrib.auth import authenticate
from django.db import models
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TwoFABackupCode


class TwoFAStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        backup_codes_remaining = user.twofa_backup_codes.filter(used_at__isnull=True).count()
        return Response({
            "enabled": bool(user.twofa_enabled),
            "backup_codes_remaining": backup_codes_remaining,
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

        # Generate backup codes
        self._generate_backup_codes(user)

        return Response({"enabled": True, "backup_codes_generated": True})

    def _generate_backup_codes(self, user):
        """Generate 10 backup codes for 2FA recovery."""
        # Delete existing unused backup codes
        user.twofa_backup_codes.filter(used_at__isnull=True).delete()

        codes = []
        for _ in range(10):
            # Generate 8-character alphanumeric code
            code = secrets.token_hex(4).upper()
            # Format as XXXX-XXXX
            formatted = f"{code[:4]}-{code[4:]}"
            # Hash for storage
            code_hash = hashlib.sha256(formatted.encode()).hexdigest()
            codes.append({
                "code": formatted,
                "hash": code_hash,
            })

        TwoFABackupCode.objects.bulk_create([
            TwoFABackupCode(user=user, code_hash=c["hash"])
            for c in codes
        ])

        return [c["code"] for c in codes]


class TwoFABackupCodesView(APIView):
    """Generate new backup codes (invalidates old ones)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.twofa_enabled:
            return Response(
                {"detail": "2FA is not enabled."}, status=400
            )

        # Generate new backup codes
        codes = []
        for _ in range(10):
            code = secrets.token_hex(4).upper()
            formatted = f"{code[:4]}-{code[4:]}"
            code_hash = hashlib.sha256(formatted.encode()).hexdigest()
            codes.append({
                "code": formatted,
                "hash": code_hash,
            })

        # Invalidate old codes
        user.twofa_backup_codes.filter(used_at__isnull=True).update(used_at=timezone.now())

        TwoFABackupCode.objects.bulk_create([
            TwoFABackupCode(user=user, code_hash=c["hash"])
            for c in codes
        ])

        return Response({
            "backup_codes": [c["code"] for c in codes],
            "detail": "New backup codes generated. Save them securely."
        })


class TwoFAVerifyBackupCodeView(APIView):
    """Verify a backup code for 2FA login."""

    permission_classes = []

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        identifier = request.data.get("username") or request.data.get("email", "")
        backup_code = str(request.data.get("backup_code") or "").strip().upper()

        if not identifier or not backup_code:
            return Response(
                {"detail": "Username/email and backup code required."}, status=400
            )

        user = User.objects.filter(
            models.Q(email__iexact=identifier) | models.Q(username=identifier)
        ).first()

        if not user or not user.twofa_enabled:
            return Response(
                {"detail": "Invalid credentials."}, status=401
            )

        # Check backup codes
        unused_codes = user.twofa_backup_codes.filter(used_at__isnull=True)
        for code_obj in unused_codes:
            if hashlib.sha256(backup_code.encode()).hexdigest() == code_obj.code_hash:
                code_obj.used_at = timezone.now()
                code_obj.save(update_fields=["used_at"])
                return Response({"valid": True})

        return Response(
            {"detail": "Invalid or used backup code."}, status=401
        )


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

        # Delete all backup codes
        user.twofa_backup_codes.all().delete()

        return Response({"enabled": False})
