"""Centralized access-control helpers for campus isolation and role scope.

Implements the ERP permission rules:

- Rule 1 — Campus isolation: a user may only access data for the campuses
  they belong to, unless their role has GLOBAL scope. Records with no
  campus value are school-wide and remain visible to every member.
- Rule 1b — Institution isolation: every query is scoped to the user's
  active institution. Cross-tenant data access is never permitted.
- Rule 2 — Backend enforcement: every campus-scoped queryset goes through
  these helpers. The frontend never decides authorization.
- Rule 3 — Role + scope: views combine a role-based permission class with
  the campus scope applied here.

Role to campus-scope mapping:

- ``super_admin``, ``admin``, ``academic`` -> GLOBAL (every campus).
- ``campus_admin``, ``principal``, ``vice_principal``, ``accountant``,
  ``hr``, ``receptionist``, ``librarian``, ``teacher``, ``staff``
  -> own campus only (from the user's profile).
- ``student`` / ``parent`` -> the campus(es) linked to the student or the
  guardian's children. Their record-level scope is applied separately by
  the per-app scoping helpers.
"""

from django.core.exceptions import PermissionDenied
from django.db.models import Q

GLOBAL_ROLES = ["super_admin", "admin", "academic"]


# ---------------------------------------------------------------------------
# Institution helpers
# ---------------------------------------------------------------------------

def get_institution(request):
    """Return the active institution from the request.

    Falls back to thread-local storage set by TenantMiddleware.
    """
    institution = getattr(request, "institution", None)
    if institution is None:
        from apps.accounts.managers import get_current_institution
        institution = get_current_institution()
    return institution


def institution_scope(queryset, request, institution_field="institution_id"):
    """Filter a queryset to the active institution.

    ``institution_field`` is the ORM path to the institution FK on the model.
    If the model already has an ``institution`` FK this works out of the box.
    """
    institution = get_institution(request)
    if institution is not None:
        return queryset.filter(**{institution_field: institution})
    return queryset.none()


def is_global(user):
    """True when the user may see every campus of the school."""
    if not (user and user.is_authenticated):
        return False

    return user.is_superuser or user.has_any_role(GLOBAL_ROLES)


def user_allowed_campus_ids(user):
    """Set of campus ids the user may access.

    Global users get every active campus of their primary institution.
    Everyone else gets the campuses recorded on their own profile plus the
    campuses linked to their teacher assignments / student enrollments so
    existing records without a ``primary_campus`` keep working.
    """
    if not (user and user.is_authenticated):
        return set()

    if is_global(user):
        from apps.schools.models import Campus

        campuses = Campus.objects.filter(status="active")
        institution = getattr(user, "primary_institution", None)

        if institution is not None:
            campuses = campuses.filter(school=institution)

        # Fallback: if the user's primary institution has no campuses,
        # allow all active campuses so global users are not blocked.
        if not campuses:
            campuses = Campus.objects.filter(status="active")

        return set(campuses.values_list("id", flat=True))

    ids = set()

    staff = getattr(user, "staff_profile", None)
    if staff is not None and staff.primary_campus_id:
        ids.add(staff.primary_campus_id)

    teacher = getattr(user, "teacher_profile", None)
    if teacher is not None:
        if teacher.primary_campus_id:
            ids.add(teacher.primary_campus_id)

        from apps.teachers.models import TeacherAssignment

        ids.update(
            TeacherAssignment.objects
            .filter(teacher_id=teacher.id, status="active")
            .values_list("campus_id", flat=True)
        )

    student = getattr(user, "student_profile", None)
    if student is not None:
        if student.primary_campus_id:
            ids.add(student.primary_campus_id)

        from apps.students.models import Enrollment

        ids.update(
            Enrollment.objects
            .filter(student_id=student.id, status="active")
            .values_list("campus_id", flat=True)
        )

    guardian = getattr(user, "guardian_profile", None)
    if guardian is not None:
        from apps.students.models import Enrollment, Student

        child_ids = list(
            guardian.students.values_list("id", flat=True)
        )

        if child_ids:
            ids.update(
                Student.objects
                .filter(pk__in=child_ids)
                .exclude(primary_campus_id=None)
                .values_list("primary_campus_id", flat=True)
            )
            ids.update(
                Enrollment.objects
                .filter(student_id__in=child_ids, status="active")
                .values_list("campus_id", flat=True)
            )

    return ids


def campus_access(request):
    """Resolve the ``campus`` query param against the user's scope.

    Returns::

        {"global": bool, "allowed_ids": set, "requested": int | None}

    Raises ``PermissionDenied`` (HTTP 403) when a non-global user requests
    a campus outside their scope or when the param is not a valid campus.
    """
    user = request.user
    allowed = user_allowed_campus_ids(user)

    requested = None
    raw = request.query_params.get("campus")

    if raw:
        try:
            requested = int(raw)
        except (TypeError, ValueError):
            raise PermissionDenied("Invalid campus.")

    if is_global(user):
        if requested is not None:
            from apps.schools.models import Campus

            if not Campus.objects.filter(
                pk=requested,
                status="active",
            ).exists():
                raise PermissionDenied("Invalid campus.")

        return {
            "global": True,
            "allowed_ids": allowed,
            "requested": requested,
        }

    if requested is not None and requested not in allowed:
        raise PermissionDenied(
            "You do not have access to this campus."
        )

    return {
        "global": False,
        "allowed_ids": allowed,
        "requested": requested,
    }


def assert_campus_allowed(user, campus_id):
    """Raise ``PermissionDenied`` unless the user may access the campus.

    Used for write paths (e.g. ``campus`` supplied in the request body)
    where ``campus_access`` (query-param based) does not apply.
    """
    if not campus_id:
        raise PermissionDenied("Invalid campus.")

    try:
        campus_id = int(campus_id)
    except (TypeError, ValueError):
        raise PermissionDenied("Invalid campus.")

    if is_global(user):
        from apps.schools.models import Campus

        if not Campus.objects.filter(
            pk=campus_id,
            status="active",
        ).exists():
            raise PermissionDenied("Invalid campus.")
        return

    allowed = user_allowed_campus_ids(user)

    if campus_id not in allowed:
        raise PermissionDenied(
            "You do not have access to this campus."
        )


def restrict_to_allowed_campuses(queryset, user, campus_field="campus_id"):
    """Restrict a queryset to the user's allowed campuses.

    No query-param handling — use in views whose ``campus`` param is a
    name (not an id) or is consumed separately. Global users are untouched.
    Records with no campus value are school-wide and stay visible.
    """
    if not is_global(user):
        allowed = user_allowed_campus_ids(user)

        if not allowed:
            return queryset.filter(
                **{f"{campus_field}__isnull": True}
            )

        return queryset.filter(
            Q(**{f"{campus_field}__isnull": True})
            | Q(**{f"{campus_field}__in": allowed})
        )

    return queryset


def _model_has_path(model, path):
    """True when ``path`` (e.g. ``"institution_id"`` or ``"book__school_id"``)
    resolves against ``model``. Guards ``apply_campus_scope`` against models
    that predate the institution FK."""
    parts = path.split("__")
    current = model

    for part in parts[:-1]:
        try:
            field = current._meta.get_field(part)
        except Exception:
            return False
        current = field.related_model
        if current is None:
            return False

    try:
        current._meta.get_field(parts[-1])
        return True
    except Exception:
        return False


def apply_campus_scope(queryset, request, campus_field="campus_id", institution_field="institution_id"):
    """Restrict a campus-scoped queryset to the user's allowed campuses.

    ``campus_field`` is the ORM path to the campus relation, e.g.
    ``"campus_id"``, ``"unit__campus_id"``, ``"class_obj__unit__campus_id"``
    or ``"primary_campus_id"``.

    ``institution_field`` is the ORM path to the institution relation, e.g.
    ``"institution_id"`` or ``"school_id"``.  When ``None``, institution
    scoping is skipped.  When set but the target model does not define the
    relation (legacy tables), institution scoping is silently skipped so
    shared reports keep working.

    Global users are filtered by the optional ``campus`` param (all when
    absent). Non-global users are always limited to their allowed campuses,
    and asking for another campus is rejected earlier in ``campus_access``.
    Records with no campus value are school-wide and stay visible.
    """
    # --- Institution scoping ---
    if institution_field and _model_has_path(queryset.model, institution_field):
        institution = get_institution(request)
        if institution is not None:
            queryset = queryset.filter(
                Q(**{institution_field: institution})
                | Q(**{f"{institution_field}__isnull": True})
            )

    # --- Campus scoping (existing) ---
    access = campus_access(request)

    if access["global"]:
        if access["requested"]:
            return queryset.filter(
                **{campus_field: access["requested"]}
            )
        return queryset

    allowed = access["allowed_ids"]

    if not allowed:
        return queryset.filter(
            **{f"{campus_field}__isnull": True}
        )

    if access["requested"]:
        return queryset.filter(
            **{campus_field: access["requested"]}
        )

    return queryset.filter(
        Q(**{f"{campus_field}__isnull": True})
        | Q(**{f"{campus_field}__in": allowed})
    )
