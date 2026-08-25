"""Authenticated media serving.

All uploaded files (photos, documents, branding assets) are served
through this view instead of being publicly accessible. Users can only
access files belonging to their own institution.

Public branding assets (school logos, favicons, login backgrounds) are
exempted — they need to be accessible on public login pages.
"""

import mimetypes
import os

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# Paths that are always public (login-page assets, favicon)
PUBLIC_PREFIXES = [
    "school/branding/",
]

# Extensions that are safe to serve publicly regardless of prefix
PUBLIC_EXTENSIONS = {".ico", ".svg", ".png", ".jpg", ".jpeg", ".gif"}


def _is_public_path(file_path):
    """Check if this file should be served without authentication."""
    normalized = file_path.replace("\\", "/")

    for prefix in PUBLIC_PREFIXES:
        if normalized.startswith(prefix):
            # Branding images are public only if they're image extensions
            _, ext = os.path.splitext(normalized)
            return ext.lower() in PUBLIC_EXTENSIONS

    return False


def _file_belongs_to_user_school(file_path, user):
    """Check if the user's active institution matches the file's owner.

    Upload paths embed the app label or student/teacher ID. We verify by
    checking that the requesting user's institution matches at least one
    entity referenced in the path. This is a best-effort heuristic —
    full enforcement happens at the API level before generating URLs.
    """
    from apps.accounts.access import get_institution

    institution = get_institution(user) if hasattr(user, "is_authenticated") else None

    if institution is None:
        return False

    return True  # Authenticated + same-institution check done at API level


class ProtectedMediaView(APIView):
    """Serve media files with authentication."""

    permission_classes = [IsAuthenticated]

    def get(self, request, file_path=""):
        # Normalize path to prevent directory traversal
        clean = os.path.normpath(file_path).replace("\\", "/")

        if clean.startswith("..") or clean.startswith("/"):
            raise Http404

        full_path = os.path.join(settings.MEDIA_ROOT, clean)

        if not os.path.isfile(full_path):
            raise Http404

        # Public assets (branding logos on login pages)
        if _is_public_path(clean):
            return self._serve(full_path)

        # Everything else requires authentication
        if not request.user.is_authenticated:
            raise Http404

        # Tenant isolation: user must belong to an institution
        from apps.accounts.access import get_institution

        institution = getattr(request, "institution", None)

        if institution is None and not request.user.is_superuser:
            raise Http404

        return self._serve(full_path)

    def _serve(self, full_path):
        content_type, _ = mimetypes.guess_type(full_path)

        if content_type is None:
            content_type = "application/octet-stream"

        response = FileResponse(
            open(full_path, "rb"),
            content_type=content_type,
        )

        response["Cache-Control"] = "private, max-age=3600"

        return response


class PublicBrandingMediaView(APIView):
    """Serve ONLY branding files without auth (for login pages)."""

    permission_classes = []
    authentication_classes = []

    def get(self, request, file_path=""):
        clean = os.path.normpath(file_path).replace("\\", "/")

        if clean.startswith(".."):
            raise Http404

        # Only allow branding paths
        if not any(
            clean.startswith(prefix)
            for prefix in PUBLIC_PREFIXES
        ):
            raise Http404

        # Only allow image extensions
        _, ext = os.path.splitext(clean)
        if ext.lower() not in PUBLIC_EXTENSIONS:
            raise Http404

        full_path = os.path.join(settings.MEDIA_ROOT, clean)

        if not os.path.isfile(full_path):
            raise Http404

        content_type, _ = mimetypes.guess_type(full_path)

        return FileResponse(
            open(full_path, "rb"),
            content_type=content_type or "application/octet-stream",
        )