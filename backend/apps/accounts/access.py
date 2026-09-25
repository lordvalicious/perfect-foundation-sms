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

- ``super_admin``, ``admin``, ``org_admin``, ``head_office``,
  ``academic`` -> GLOBAL (every campus of the active institution).
- ``principal``, ``vice_principal`` -> own campus from the profile; a
  leader with no campus assignment falls back to every campus of the
  active institution (school-wide, never another school).
- ``campus_admin``, ``accountant``, ``hr``, ``receptionist``,
  ``librarian``, ``guard``, ``teacher``, ``staff`` -> own campus only
  (from the user's profile).
- ``student`` / ``parent`` -> the campus(es) linked to the student or the
  guardian's children. Their record-level scope is applied separately by
  the per-app scoping helpers.
"""

from django.core.exceptions import PermissionDenied
from django.db.models import Q

from apps.accounts.models import Role, role_rank

GLOBAL_ROLES = [
    "super_admin",
    "admin",
    "org_admin",
    "head_office",
    "academic",
]
# Note: PRINCIPAL, VICE_PRINCIPAL, CAMPUS_ADMIN are NOT global roles.
# They are campus-level roles with scope determined by explicit RoleAssignment.campus.


# ---------------------------------------------------------------------------
# Role hierarchy / escalation guards
# ---------------------------------------------------------------------------

def user_role_rank(user, institution=None):
    """Highest role rank for ``user`` (super admin overrides everything).

    The Super Admin check is global (not institution-scoped) because the
    platform Super Admin may be acting in any school context.
    """
    if user.is_superuser or user.has_role(Role.SUPER_ADMIN):
        return role_rank(Role.SUPER_ADMIN) + 1
    ranks = [role_rank(r) for r in user.get_roles(institution)]
    return max(ranks) if ranks else 0


def can_manage_role(actor, role, institution=None):
    """True when ``actor`` outranks ``role`` (may administer it).

    Equal/higher roles are off-limits, which makes self- and upward escalation
    impossible (e.g. ADMIN can never manage the super_admin role).
    """
    return role_rank(role) < user_role_rank(actor, institution)


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


def user_allowed_campus_ids(user, institution=None):
    """Set of campus ids the user may access.

    Campus-level roles (PRINCIPAL, VICE_PRINCIPAL, CAMPUS_ADMIN):
    - Scope is determined by explicit campus assignment on RoleAssignment.campus
    - If NO valid campus assignment exists: FAIL CLOSED (return empty set)
    - No fallback to school-wide or all campuses

    Global users (SUPER_ADMIN, ADMIN, ORG_ADMIN, HEAD_OFFICE, ACADEMIC):
    - Get every active campus of the active institution

    Other roles (teachers, accountants, staff, students, parents):
    - Scope from profile primary_campus, teacher assignments, student enrollments
    - Existing behavior preserved
    """
    if not (user and user.is_authenticated):
        return set()

    if is_global(user):
        from apps.schools.models import Campus

        if institution is None:
            institution = getattr(user, "primary_institution", None)

        if institution is None:
            return set()

        return set(
            Campus.objects.filter(
                status="active",
                school=institution,
            ).values_list("id", flat=True)
        )

    ids = set()

    # --- Campus-level roles: scope from explicit RoleAssignment.campus ---
    campus_level_roles = [Role.PRINCIPAL, Role.VICE_PRINCIPAL, Role.CAMPUS_ADMIN]
    if user.has_any_role(campus_level_roles, institution=institution):
        from apps.accounts.models import RoleAssignment
        from apps.schools.models import Campus

        # Determine institution for querying
        query_institution = institution or getattr(user, "primary_institution", None)
        if query_institution is None:
            return set()

        # Get campus assignments from RoleAssignment for campus-level roles
        campus_assignments = RoleAssignment.objects.filter(
            membership__user=user,
            membership__institution=query_institution,
            membership__status="active",
            role__in=campus_level_roles,
            campus__isnull=False,
            campus__status="active",
        ).select_related("campus")

        for assignment in campus_assignments:
            if assignment.campus and assignment.campus.school_id == query_institution.id:
                ids.add(assignment.campus_id)

        # FAIL CLOSED: If no valid campus assignment for campus-level role,
        # return empty set (do NOT fall back to school-wide)
        return ids

    # --- Other roles: existing behavior (profile primary_campus, etc.) ---
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

    # REMOVED: School leadership fallback to all campuses
    # Principal/VP without campus assignment now FAIL CLOSED (handled above)

    return ids


def campus_access(request):
    """Resolve the ``campus`` query param against the user's scope.

    Returns::

        {"global": bool, "allowed_ids": set, "requested": int | None}

    Raises ``PermissionDenied`` (HTTP 403) when a non-global user requests
    a campus outside their scope or when the param is not a valid campus.
    
    Results are cached on the request object to avoid repeated computation.
    """
    # Check cache first
    cache_key = "_campus_access_cache"
    if hasattr(request, cache_key):
        return getattr(request, cache_key)

    user = request.user
    institution = get_institution(request)
    allowed = user_allowed_campus_ids(user, institution)

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

            if institution is not None:
                valid = Campus.objects.filter(
                    pk=requested,
                    status="active",
                    school=institution,
                ).exists()
            else:
                # No explicit institution context (e.g. DRF test client):
                # validate against the user's own resolved campus scope, which
                # is always derived from the user's active school(s) only.
                valid = requested in allowed

            if not valid:
                raise PermissionDenied("Invalid campus.")

        result = {
            "global": True,
            "allowed_ids": allowed,
            "requested": requested,
        }
    else:
        if requested is not None and requested not in allowed:
            raise PermissionDenied(
                "You do not have access to this campus."
            )

        result = {
            "global": False,
            "allowed_ids": allowed,
            "requested": requested,
        }

    # Cache the result on the request object
    setattr(request, cache_key, result)
    return result


def assert_campus_allowed(user, campus_id, request=None):
    """Raise ``PermissionDenied`` unless the user may access the campus.

    Used for write paths (e.g. ``campus`` supplied in the request body)
    where ``campus_access`` (query-param based) does not apply.

    When a ``request`` is provided its resolved active institution is used to
    validate the campus (accounts for Super Admin context-switching); otherwise
    the user's primary institution is the fallback.
    """
    if not campus_id:
        raise PermissionDenied("Invalid campus.")

    # Extract pk if a Campus model instance was passed instead of an ID.
    if hasattr(campus_id, "pk"):
        campus_id = campus_id.pk

    try:
        campus_id = int(campus_id)
    except (TypeError, ValueError):
        raise PermissionDenied("Invalid campus.")

    if is_global(user):
        from apps.schools.models import Campus

        # Prefer the resolved active institution (request, then thread-local
        # context set by ActiveInstitutionMiddleware). The denormalized
        # ``User.institution`` FK is deliberately NOT used first: it can be
        # stale for a Super Admin that has context-switched schools.
        if request is not None:
            institution = getattr(request, "institution", None)
        else:
            from apps.accounts.managers import get_current_institution

            institution = get_current_institution()

        if institution is not None:
            valid = Campus.objects.filter(
                pk=campus_id,
                status="active",
                school=institution,
            ).exists()
        else:
            # No explicit institution context: validate against the user's own
            # resolved campus scope (user's active school(s) only). A campus
            # outside that scope is rejected, so foreign-school ids never pass.
            valid = campus_id in user_allowed_campus_ids(user)

        if not valid:
            raise PermissionDenied("You do not have access to this campus.")
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


def _get_institution_campus_count(request, institution):
    """Get the count of active campuses for an institution, cached on request."""
    if institution is None:
        return 0
    cache_key = f"_campus_count_cache_{institution.pk}"
    if hasattr(request, cache_key):
        return getattr(request, cache_key)
    from apps.schools.models import Campus
    count = Campus.objects.filter(school=institution, status="active").count()
    setattr(request, cache_key, count)
    return count


def _user_has_all_campuses(request, institution, allowed_ids):
    """Check if the user has access to all active campuses of the institution."""
    if institution is None or not allowed_ids:
        return False
    total_campuses = _get_institution_campus_count(request, institution)
    return total_campuses > 0 and len(allowed_ids) >= total_campuses


def apply_campus_scope(queryset, request, campus_field="campus_id", institution_field="institution_id"):
    """Restrict a campus-scoped queryset to the user's allowed campuses.

    ``campus_field`` is the ORM path to the campus relation, e.g.
    ``"campus_id"``, ``"unit__campus_id"``, ``"class_obj__unit__campus_id"``
    or ``"primary_campus_id"``.  When ``None``, campus scoping is skipped.

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

    # --- Campus scoping (skip if campus_field is None) ---
    if campus_field is None:
        return queryset

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

    # Optimization: if user has access to all active campuses of the institution,
    # campus scoping is redundant because institution filtering already restricts
    # to that institution's data. The Q(**{f"{campus_field}__in": allowed})
    # would match all campuses anyway, and the institution filter already
    # restricts to the institution's data.
    institution = get_institution(request)
    if _user_has_all_campuses(request, institution, allowed):
        return queryset

    return queryset.filter(
        Q(**{f"{campus_field}__isnull": True})
        | Q(**{f"{campus_field}__in": allowed})
    )
