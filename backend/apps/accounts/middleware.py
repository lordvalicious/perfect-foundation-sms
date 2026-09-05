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
