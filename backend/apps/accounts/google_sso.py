"""Google Sign-In (Identity Services) backend.

Flow: the frontend loads Google's GIS script, obtains an ID token,
and posts it here. We verify it against Google's tokeninfo endpoint,
match the email to an existing active account, and open a session.

Accounts are NOT auto-created — an administrator must add the person
first, so only pre-provisioned staff can use SSO.

Env:
    GOOGLE_CLIENT_ID   enables the flow when set
"""

import logging
import urllib.parse
import urllib.request

from django.contrib.auth import login as django_login
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.audit.models import record_audit

logger = logging.getLogger(__name__)

TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def google_enabled():
    import os

    return bool(os.environ.get("GOOGLE_CLIENT_ID", ""))


def verify_id_token(credential):
    """Verify a Google ID token; returns the payload dict or None."""
    import os

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")

    try:
        query = urllib.parse.urlencode({"id_token": credential})
        with urllib.request.urlopen(
            f"{TOKENINFO_URL}?{query}", timeout=15
        ) as response:
            payload = __import__("json").loads(response.read().decode())
    except Exception as exc:
        logger.warning("Google tokeninfo failed: %s", exc)
        return None

    if client_id and payload.get("aud") != client_id:
        logger.warning("Google token aud mismatch")
        return None

    if payload.get("email_verified") not in ("true", True):
        return None

    return payload


class GoogleConfigView(APIView):
    """GET /api/auth/google/config/ -> lets the login page know."""

    permission_classes = [AllowAny]

    def get(self, request):
        import os

        return JsonResponse({
            "enabled": bool(os.environ.get("GOOGLE_CLIENT_ID", "")),
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
        })


class GoogleLoginView(APIView):
    """POST {credential} -> session login for a pre-provisioned user."""

    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        if not google_enabled():
            return JsonResponse(
                {"detail": "Google sign-in is not configured."},
                status=503,
            )

        credential = request.data.get("credential") or ""

        payload = verify_id_token(credential)

        if payload is None:
            return JsonResponse(
                {"detail": "Invalid Google token."}, status=400
            )

        email = (payload.get("email") or "").strip().lower()
        user = User.objects.filter(
            email__iexact=email, is_active=True
        ).first()

        if user is None:
            return JsonResponse(
                {
                    "detail": (
                        "No account exists for this Google address. "
                        "Ask the school office to create one."
                    )
                },
                status=403,
            )

        django_login(request, user)

        memberships = user.get_active_memberships()

        if memberships.exists():
            request.session["active_institution_id"] = (
                memberships.first().institution_id
            )

        record_audit(
            request=request,
            action="login",
            details={"method": "google", "role": user.primary_role},
        )

        from .serializers import UserSerializer

        return JsonResponse(
            UserSerializer(user, context={"request": request}).data
        )
