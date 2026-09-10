import json

from django.core.cache import cache

from .models import get_client_ip, record_audit


class LoginAttemptAuditMiddleware:
    """Record failed login attempts and success login usage.

    * Failed logins -> ``login_failed`` audit row + an IP-based brute-force
      counter in cache.
    * A single IP crossing ``BRUTE_FORCE_IP_THRESHOLD`` failures inside one
      day emits ONE ``brute_force_detected`` audit row (deduplicated via a
      per-IP cache key so the alert does not spam the log).
    * Successful logins bump the per-institution ``logins`` usage counter only
      (the ``login`` audit row is already written by ``LoginView``).
    """

    LOGIN_PATH = "/api/auth/login/"
    #: IPs with this many failed attempts in a single day are flagged.
    BRUTE_FORCE_IP_THRESHOLD = 10
    #: 24h window plus a small drift allowance.
    BRUTE_FORCE_WINDOW_SECONDS = 60 * 60 * 25

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

        if response.status_code in (400, 401, 403):
            self._record_failed(request)
        elif response.status_code == 200:
            self._record_success(request)

        return response

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _record_failed(self, request):
        record_audit(
            request=request,
            action="login_failed",
            details={
                "username": self._extract_identifier(request),
            },
        )
        self._track_ip(request)

    def _record_success(self, request):
        # Login audit row already created by the view; only bump analytics.
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return
        institution = getattr(request, "session", {}).get(
            "active_institution_id"
        ) or getattr(user, "institution_id", None)
        if institution:
            from apps.saas.services import record_usage

            record_usage(institution, "logins")

    def _track_ip(self, request):
        ip = get_client_ip(request)
        if not ip:
            return

        counter_key = f"saas:security:failed_login:{ip}"
        try:
            count = cache.get(counter_key, 0) + 1
            cache.set(
                counter_key, count, self.BRUTE_FORCE_WINDOW_SECONDS
            )
            if (
                count == self.BRUTE_FORCE_IP_THRESHOLD
                and cache.get(f"saas:security:flagged:{ip}") is None
            ):
                cache.set(
                    f"saas:security:flagged:{ip}",
                    True,
                    self.BRUTE_FORCE_WINDOW_SECONDS,
                )
                record_audit(
                    request=request,
                    action="brute_force_detected",
                    details={
                        "ip_address": ip,
                        "failed_attempts": count,
                        "window_hours": 24,
                    },
                )
        except Exception:
            # Security telemetry must never break the login cycle.
            pass

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