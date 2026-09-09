"""Authenticated media serving.

All uploaded files (photos, documents, branding assets) are served
through this view instead of being publicly accessible. Access checks
are **fail closed**: a file must resolve to a real ORM record whose
owner belongs to the requester's active institution, the requester must
have campus-level access, and (for documents) an applicable role. A
manipulated path or an unknown upload prefix is never served.
"""

import mimetypes
import os

from django.conf import settings
from django.db.models import Q
from django.http import FileResponse, Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.access import get_institution

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


def _resolve_media_owner(file_path):
    """Return the ORM record that owns ``file_path``, or None.

    Every known upload prefix maps exactly to the owning model's file
    field, so a manipulated path either resolves to a genuine record or
    is denied. Unknown prefixes return None (deny).
    """
    normalized = file_path.replace("\\", "/")

    if normalized.startswith("students/documents/"):
        from apps.students.models import StudentDocument

        return (
            StudentDocument.objects
            .select_related("student", "institution")
            .filter(file=normalized)
            .first()
        )

    if normalized.startswith("profiles/students/"):
        from apps.students.models import Student

        return (
            Student.objects
            .select_related("primary_campus")
            .filter(photo=normalized)
            .first()
        )

    if normalized.startswith("profiles/teachers/"):
        from apps.teachers.models import Teacher

        return (
            Teacher.objects
            .select_related("primary_campus")
            .filter(photo=normalized)
            .first()
        )

    if normalized.startswith("profiles/staff/"):
        from apps.accounts.models import StaffProfile

        return (
            StaffProfile.objects
            .select_related("primary_campus")
            .filter(photo=normalized)
            .first()
        )

    if normalized.startswith("profiles/users/"):
        from apps.accounts.models import User

        return User.objects.filter(photo=normalized).first()

    if normalized.startswith("hr/candidates/resumes/"):
        from apps.hr.models import Candidate

        return (
            Candidate.objects
            .select_related("institution", "campus")
            .filter(resume=normalized)
            .first()
        )

    if normalized.startswith("hr/"):
        from apps.hr.models import (
            EmployeeDocument,
            EmploymentContract,
            LeaveRequest,
            Loan,
            SalaryRevision,
        )

        if normalized.startswith("hr/documents/"):
            return (
                EmployeeDocument.objects
                .select_related("employee", "campus")
                .filter(file=normalized)
                .first()
            )

        if normalized.startswith("hr/contracts/"):
            return (
                EmploymentContract.objects
                .select_related("employee", "campus")
                .filter(document=normalized)
                .first()
            )

        if normalized.startswith("hr/leave/"):
            return (
                LeaveRequest.objects
                .select_related("employee", "campus")
                .filter(attachment=normalized)
                .first()
            )

        if normalized.startswith("hr/loans/"):
            return (
                Loan.objects
                .select_related("employee", "campus")
                .filter(documents=normalized)
                .first()
            )

        if normalized.startswith("hr/salary_revisions/"):
            return (
                SalaryRevision.objects
                .select_related("employee", "campus")
                .filter(document=normalized)
                .first()
            )

        return None

    if normalized.startswith("homework/"):
        from apps.homework.models import Homework

        return (
            Homework.objects
            .select_related("campus", "institution")
            .filter(attachment=normalized)
            .first()
        )

    if normalized.startswith("visitors/"):
        from apps.visitors.models import Visitor

        return (
            Visitor.objects
            .select_related("campus", "institution")
            .filter(photo=normalized)
            .first()
        )

    if normalized.startswith("digital_ids/"):
        from apps.digital_ids.models import IdCard

        return (
            IdCard.objects
            .select_related("campus", "institution")
            .filter(photo=normalized)
            .first()
        )

    if normalized.startswith("payslips/"):
        from apps.payroll.models import Payslip

        return (
            Payslip.objects
            .select_related(
                "record__employee",
                "record__employee__primary_campus",
            )
            .filter(document=normalized)
            .first()
        )

    if normalized.startswith("white_label/"):
        from apps.white_label.models import WhiteLabelBranding

        fields = [
            "logo",
            "logo_dark",
            "favicon",
            "favicon_dark",
            "login_background_image",
            "email_header_image",
            "document_watermark",
            "certificate_border",
            "og_image",
        ]
        for record in (
            WhiteLabelBranding
            .objects
            .select_related("school")
            .all()
        ):
            for field in fields:
                value = getattr(record, field, None)
                if value and value.name == normalized:
                    return record

        return None

    if normalized.startswith("branding/"):
        from apps.schools.models import School

        return (
            School.objects
            .filter(
                Q(logo=normalized) | Q(favicon=normalized),
                status="active",
            )
            .first()
        )

    return None


def _owner_context(record, file_path):
    """Return ``(institution_id, campus_ids)`` for an owning record.

    Institution is taken from the record's own FK, from its related
    entity (student / employee), or from the campus's school. ``None``
    means "unknown" and is treated as a denial upstream.
    """
    model_name = type(record).__name__

    if model_name == "StudentDocument":
        student = record.student
        inst = record.institution_id
        if inst is None and student is not None:
            inst = student.institution_id
        if inst is None and student is not None and student.primary_campus_id:
            inst = student.primary_campus.school_id
        campus = student.primary_campus_id if student else None
        return inst, [campus] if campus else []

    if model_name == "Student":
        inst = record.institution_id
        if inst is None and record.primary_campus_id:
            inst = record.primary_campus.school_id
        campus = record.primary_campus_id
        return inst, [campus] if campus else []

    if model_name == "Teacher":
        inst = record.institution_id
        if inst is None and record.primary_campus_id:
            inst = record.primary_campus.school_id
        campus = record.primary_campus_id
        return inst, [campus] if campus else []

    if model_name == "StaffProfile":
        inst = record.institution_id
        if inst is None and record.primary_campus_id:
            inst = record.primary_campus.school_id
        campus = record.primary_campus_id
        return inst, [campus] if campus else []

    if model_name in (
        "EmployeeDocument",
        "EmploymentContract",
        "LeaveRequest",
        "Loan",
        "SalaryRevision",
    ):
        employee = record.employee
        inst = getattr(employee, "institution_id", None)
        campus = getattr(record, "campus_id", None)
        if campus is None:
            campus = getattr(employee, "primary_campus_id", None)
        return inst, [campus] if campus else []

    if model_name == "Candidate":
        return record.institution_id, (
            [record.campus_id] if record.campus_id else []
        )

    if model_name == "Payslip":
        employee = record.record.employee
        return employee.institution_id, (
            [employee.primary_campus_id]
            if employee.primary_campus_id
            else []
        )

    if model_name in ("Homework", "Visitor", "IdCard"):
        inst = record.institution_id
        if inst is None and record.campus_id:
            inst = record.campus.school_id
        return inst, [record.campus_id] if record.campus_id else []

    if model_name == "WhiteLabelBranding":
        return record.school_id, []

    if model_name == "School":
        return record.pk, []

    return None, []


def _role_allows_student_document(request, student):
    """Non-managers may only open documents of students in their scope."""
    from apps.accounts.scopes import (
        is_manager,
        is_parent,
        is_student,
        is_teacher,
        parent_student_ids,
        teacher_student_ids,
    )

    if is_manager(request.user):
        return True

    if student is None:
        return False

    if is_student(request.user):
        return (
            request.user.student_profile_id is not None
            and request.user.student_profile_id == student.pk
        )

    if is_parent(request.user):
        return student.pk in parent_student_ids(request.user)

    if is_teacher(request.user):
        return student.pk in teacher_student_ids(request.user)

    return False


def _role_allows_hr_document(request, employee):
    """HR files are for school managers or the employee themself."""
    from apps.accounts.scopes import is_manager

    if is_manager(request.user):
        return True

    if employee is None:
        return False

    teacher = getattr(employee, "teacher", None)
    if teacher is not None and getattr(teacher, "user_id", None) == request.user.pk:
        return True

    staff = getattr(employee, "staff_profile", None)
    if staff is not None and getattr(staff, "user_id", None) == request.user.pk:
        return True

    return False


def _role_allows_homework(request, homework):
    """Homework attachments are visible to managers and class students."""
    from apps.accounts.scopes import (
        is_manager,
        is_student,
        student_class_ids,
    )

    if is_manager(request.user):
        return True

    if is_student(request.user):
        return homework.class_obj_id in student_class_ids(request.user)

    return False


def _can_access_file(file_path, request):
    """Fail-closed authorization for a protected media file."""
    if request.user.is_superuser:
        return True

    institution = getattr(request, "institution", None)
    if institution is None:
        institution = get_institution(request)
        if institution is None:
            return False

    normalized = file_path.replace("\\", "/")
    owner = _resolve_media_owner(normalized)

    if owner is None:
        return False

    if normalized.startswith("profiles/users/"):
        return (
            # Same owner + school check, no campus constraint.
            owner.pk == request.user.pk
            or owner.memberships.filter(
                status="active",
                institution_id=institution.pk,
            ).exists()
        )

    inst_id, campus_ids = _owner_context(owner, normalized)

    if inst_id is not None and inst_id != institution.pk:
        return False

    from apps.accounts.access import assert_campus_allowed

    for campus_id in campus_ids:
        try:
            assert_campus_allowed(request.user, campus_id)
        except Exception:
            return False

    if normalized.startswith("students/documents/"):
        return _role_allows_student_document(
            request,
            getattr(owner, "student", None),
        )

    if normalized.startswith("profiles/students/"):
        return _role_allows_student_document(request, owner)

    if normalized.startswith("hr/candidates/resumes/"):
        return _role_allows_hr_document(request, None)

    if normalized.startswith("hr/"):
        return _role_allows_hr_document(
            request,
            getattr(owner, "employee", None),
        )

    if normalized.startswith("payslips/"):
        return _role_allows_hr_document(
            request,
            getattr(owner, "record").employee,
        )

    if normalized.startswith("homework/"):
        return _role_allows_homework(request, owner)

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

        # Fail-closed ownership + institution + campus + role checks
        if not _can_access_file(clean, request):
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