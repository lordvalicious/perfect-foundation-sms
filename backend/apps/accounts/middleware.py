"""Attach the authenticated user's selected institution to each request.

Also sets thread-local state so that TenantManager can auto-filter querysets
even in contexts where the request is not directly available (e.g. management
commands, Celery tasks, or model-level code).
"""


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

        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            memberships = user.get_active_memberships()
            selected_id = request.session.get(self.session_key)
            membership = memberships.filter(
                institution_id=selected_id
            ).first()
            if membership is None:
                membership = memberships.first()
                if membership is not None:
                    request.session[self.session_key] = membership.institution_id
                else:
                    request.session.pop(self.session_key, None)

            if membership is not None:
                request.institution = membership.institution
                request.institution_membership = membership

        # Set thread-local state for TenantManager
        set_current_institution(request.institution)
        set_current_request(request)

        try:
            response = self.get_response(request)
        finally:
            clear_current_institution()
            clear_current_request()

        return response
