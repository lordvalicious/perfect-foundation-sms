"""Request-path middleware for SaaS usage tracking.

``UsageTrackingMiddleware`` counts authenticated ``/api/`` traffic per
institution into the cache buffer (``apps.saas.services.record_usage``).
Buffers are persisted to ``DailyUsageSnapshot`` by the ``collect_usage``
management command (or on-demand by the analytics views).
"""

from .services import record_usage


class UsageTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method == "GET":
            return response
        if not request.path.startswith("/api/"):
            return response

        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return response

        institution = getattr(request, "institution", None)
        if institution is None:
            return response

        record_usage(institution.pk, "api_requests")
        return response