"""Attach the authenticated user's selected institution to each request."""


class ActiveInstitutionMiddleware:
    """Keep tenant selection server-side instead of trusting a URL or client id."""

    session_key = "active_institution_id"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
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

        return self.get_response(request)
