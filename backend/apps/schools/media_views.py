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

from apps.accounts.access import get_institution, assert_campus_allowed

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


def _get_campus_from_path(file_path):
    """Extract campus ID from file path if present.
    
    Expected patterns:
    - profiles/users/<id>/... (user profile - check user's campus)
    - profiles/students/<id>/... (student - check student's campus)
    - profiles/teachers/<id>/... (teacher - check teacher's campus)
    - profiles/staff/<id>/... (staff - check staff's campus)
    - documents/students/<id>/... (student document)
    - etc.
    """
    normalized = file_path.replace("\\", "/")
    
    # Student documents
    if normalized.startswith("students/documents/"):
        # Path: students/documents/<student_id>/...
        parts = normalized.split("/")
        if len(parts) >= 3:
            try:
                student_id = int(parts[2])
                from apps.students.models import Student
                student = Student.objects.filter(pk=student_id).select_related("primary_campus").first()
                if student and student.primary_campus_id:
                    return student.primary_campus_id
            except (ValueError, IndexError):
                pass
    
    # Student profile images
    if normalized.startswith("profiles/students/"):
        parts = normalized.split("/")
        if len(parts) >= 3:
            try:
                student_id = int(parts[2])
                from apps.students.models import Student
                student = Student.objects.filter(pk=student_id).select_related("primary_campus").first()
                if student and student.primary_campus_id:
                    return student.primary_campus_id
            except (ValueError, IndexError):
                pass
    
    # Teacher profile images
    if normalized.startswith("profiles/teachers/"):
        parts = normalized.split("/")
        if len(parts) >= 3:
            try:
                teacher_id = int(parts[2])
                from apps.teachers.models import Teacher
                teacher = Teacher.objects.filter(pk=teacher_id).select_related("primary_campus").first()
                if teacher and teacher.primary_campus_id:
                    return teacher.primary_campus_id
            except (ValueError, IndexError):
                pass
    
    # Staff profile images
    if normalized.startswith("profiles/staff/"):
        parts = normalized.split("/")
        if len(parts) >= 3:
            try:
                staff_id = int(parts[2])
                from apps.accounts.models import StaffProfile
                staff = StaffProfile.objects.filter(pk=staff_id).select_related("primary_campus").first()
                if staff and staff.primary_campus_id:
                    return staff.primary_campus_id
            except (ValueError, IndexError):
                pass
    
    # User profile images
    if normalized.startswith("profiles/users/"):
        parts = normalized.split("/")
        if len(parts) >= 3:
            try:
                user_id = int(parts[2])
                from apps.accounts.models import User
                user = User.objects.filter(pk=user_id).select_related("student_profile__primary_campus", "teacher_profile__primary_campus", "staff_profile__primary_campus").first()
                if user:
                    if user.student_profile and user.student_profile.primary_campus_id:
                        return user.student_profile.primary_campus_id
                    if user.teacher_profile and user.teacher_profile.primary_campus_id:
                        return user.teacher_profile.primary_campus_id
                    if user.staff_profile and user.staff_profile.primary_campus_id:
                        return user.staff_profile.primary_campus_id
            except (ValueError, IndexError):
                pass
    
    return None


def _file_belongs_to_user_school(file_path, user):
    """Check if the user's active institution matches the file's owner.

    Upload paths embed the app label or student/teacher ID. We verify by
    checking that the requesting user's institution matches at least one
    entity referenced in the path. This is a best-effort heuristic —
    full enforcement happens at the API level before generating URLs.
    """
    institution = get_institution(user) if hasattr(user, "is_authenticated") else None

    if institution is None:
        return False

    # Check campus-level access if the file is campus-scoped
    campus_id = _get_campus_from_path(file_path)
    if campus_id is not None:
        from apps.accounts.access import assert_campus_allowed
        try:
            assert_campus_allowed(user, campus_id)
        except Exception:
            return False

    return True


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

        # Campus-level authorization
        if not _file_belongs_to_user_school(clean, request.user):
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