"""Attach the authenticated user's selected institution to each request.

Resolution order:
1. Custom domain / subdomain match (white-label hosting)
2. Session-selected institution (user switched via UI)
3. First active membership (default)

Also sets thread-local state so that TenantManager can auto-filter querysets
even in contexts where the request is not directly available (e.g. management
commands, Celery tasks, or model-level code).
"""

import logging

logger = logging.getLogger(__name__)

# Fail-closed classifications of the request's active-school context. Views
# that draw school-scoped data should reject (403) for ``stale``/``inactive``
# contexts and treat ``missing`` as an empty/400 tenant-context error.
ACTIVE_SCHOOL_OK = "ok"
ACTIVE_SCHOOL_MISSING = "missing"
ACTIVE_SCHOOL_STALE = "stale"
ACTIVE_SCHOOL_INACTIVE = "inactive"


def active_school_state(request):
    """Classify how the active school resolved for this request.

    Rules (active-school failure policy, §5A):

    * ``missing``  - no active school could be resolved at all.
    * ``stale``    - the session explicitly pointed at a school the user is
                     not authorized for (invalid, deleted, foreign, or a
                     non-active membership); the middleware silently fell
                     back to the user's first active membership.
    * ``inactive`` - the resolved school exists but is not currently in an
                     active/operational state.
    * ``ok``       - resolved to an active school the user is authorized to
                     access.
    """
    institution = getattr(request, "institution", None)

    if institution is None:
        return ACTIVE_SCHOOL_MISSING

    if getattr(request, "institution_context_stale", False):
        return ACTIVE_SCHOOL_STALE

    is_paused = getattr(institution, "is_paused", False)

    if getattr(institution, "status", "active") != "active" or is_paused:
        return ACTIVE_SCHOOL_INACTIVE

    return ACTIVE_SCHOOL_OK


def require_active_school(request):
    """Return the reliably confirmed active school, or ``None`` when absent.

    Fail-closed enforcement a backend already has the DRF exception handler
    installed for: a stale/unauthorized session context or an inactive/
    archived school raises a 403 ``PermissionDenied``; a genuinely absent
    context returns ``None`` (read paths then yield empty results, write
    paths return the documented 400 tenant error).
    """
    from rest_framework.exceptions import PermissionDenied

    state = active_school_state(request)

    if state == ACTIVE_SCHOOL_STALE:
        raise PermissionDenied(
            detail=(
                "Your active school context is no longer valid. "
                "Please select a school to continue."
            )
        )

    if state == ACTIVE_SCHOOL_INACTIVE:
        raise PermissionDenied(
            detail=(
                "This school is no longer active. "
                "Please select another school."
            )
        )

    return getattr(request, "institution", None)


class ActiveInstitutionMiddleware:
    """Keep tenant selection server-side instead of trusting a URL or client id."""

    session_key = "active_institution_id"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from apps.accounts.managers import (
            set_current_institution,
            set_current_request,
            clear_current_institution,
            clear_current_request,
        )

        request.institution = None
        request.institution_membership = None
        request.institution_context_stale = False

        # --- 1) Domain-based resolution (works for anonymous users too) ---
        host_school = self._resolve_by_host(request)

        user = getattr(request, "user", None)

        if host_school is not None:
            # White-label domain: force institution regardless of user
            request.institution = host_school

            # Still link the user's membership if they belong here
            if user is not None and user.is_authenticated:
                membership = user.get_active_memberships().filter(
                    institution=host_school
                ).first()

                if membership is not None:
                    request.institution_membership = membership
                    request.session[self.session_key] = (
                        membership.institution_id
                    )
        elif user is not None and user.is_authenticated:
            # --- 2) Session/membership-based resolution ---
            memberships = user.get_active_memberships()
            selected_id = request.session.get(self.session_key)
            membership = memberships.filter(
                institution_id=selected_id
            ).first()

            if membership is None:
                # The platform Super Admin can manage every school even without
                # a membership row for it (they may self-provision memberships
                # lazily). Honor their explicit context switch to any active
                # school.
                if selected_id is not None and (
                    user.is_superuser or user.has_any_role(["super_admin"])
                ):
                    from apps.schools.models import School

                    active_school = School.objects.filter(
                        pk=selected_id, status="active"
                    ).first()
                    if active_school is not None:
                        request.institution = active_school

                if membership is None and request.institution is None:
                    membership = memberships.first()
                    if membership is not None:
                        # The session explicitly selected a school the user is
                        # not authorized for (invalid, deleted, foreign, or a
                        # non-active context). Flag it so school-scoped views
                        # can fail closed instead of silently serving the
                        # substituted first membership (§5A "Unauthorized
                        # school must never become a fallback").
                        if selected_id is not None:
                            request.institution_context_stale = True
                        request.session[self.session_key] = membership.institution_id
                    else:
                        request.session.pop(self.session_key, None)

                if request.institution is not None and membership is None:
                    request.institution_membership = None
                    request.session[self.session_key] = selected_id

            if membership is not None:
                request.institution = membership.institution
                request.institution_membership = membership

        # Set contextvar state for TenantManager (async-safe)
        set_current_institution(request.institution)
        set_current_request(request)

        try:
            response = self.get_response(request)
        finally:
            clear_current_institution()
            clear_current_request()

        return response

    @staticmethod
    def _resolve_by_host(request):
        """Try to resolve School from the request hostname."""
        import os

        try:
            host = request.get_host().split(":")[0].lower()
        except Exception:
            return None

        # Skip known non-tenant hosts
        platform_host = os.environ.get("PLATFORM_HOST", "")
        if not platform_host:
            platform_host = "vercel.app"

        if not host or host in ("localhost", "127.0.0.1", "0.0.0.0", "testserver"):
            return None

        # Validate host against allowed platforms to prevent host header spoofing
        allowed_hosts = os.environ.get("ALLOWED_HOSTS", "").split(",")
        if allowed_hosts and host not in allowed_hosts and not host.endswith(f".{platform_host}"):
            return None

        from apps.schools.models import School

        # 1) Exact custom_domain match
        try:
            school = School.objects.filter(
                custom_domain__iexact=host, status="active"
            ).select_related("settings").first()
        except Exception:
            # Handle case where migration hasn't been applied yet (e.g., is_paused column missing)
            school = None

        if school:
            return school

        # 2) Subdomain pattern: <code>.platform-host
        if host.endswith(f".{platform_host}"):
            subdomain = host[: -len(platform_host) - 1]
            try:
                school = School.objects.filter(
                    code__iexact=subdomain, status="active"
                ).select_related("settings").first()
            except Exception:
                school = None

            if school:
                return school

        return None
