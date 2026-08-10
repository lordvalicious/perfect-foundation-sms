import json

from .models import record_audit


class LoginAttemptAuditMiddleware:
    """Record failed login attempts for the session login endpoint."""

    LOGIN_PATH = "/api/auth/login/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method != "POST":
            return response

        if not request.path.rstrip("/").endswith(
            self.LOGIN_PATH.rstrip("/")
        ):
            return response

        if response.status_code not in (400, 401, 403):
            return response

        record_audit(
            request=request,
            action="login_failed",
            details={
                "username": self._extract_identifier(request),
            },
        )

        return response

    @staticmethod
    def _extract_identifier(request):
        try:
            data = json.loads(request.body or b"{}")
        except Exception:
            data = {}

        return (
            data.get("username")
            or data.get("email")
            or ""
        )
