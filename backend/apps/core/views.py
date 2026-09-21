from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle
from pathlib import Path
import hmac
import logging
import os


logger = logging.getLogger(__name__)

MIGRATION_SECRET = os.environ.get("MIGRATION_SECRET", "")

# F14: endpoint-specific DRF scoped throttle. Rate lives in
# DEFAULT_THROTTLE_RATES["run_migrations"] (base), and tests override
# ScopedRateThrottle.THROTTLE_RATES + a dedicated cache when asserting 429.
MIGRATIONS_THROTTLE_SCOPE = "run_migrations"


def home_view(request):
    index_path = Path(settings.BASE_DIR) / "index.html"
    if index_path.exists():
        return HttpResponse(index_path.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")
    return JsonResponse({"name": "Perfect Foundation SMS API", "status": "ok"})


@csrf_exempt
@require_http_methods(["POST"])
def run_migrations_view(request):
    """Secure endpoint to run migrations. Requires MIGRATION_SECRET in Authorization header."""
    # F14: endpoint-specific DRF scoped throttle, applied before any
    # secret/auth/migrate work so failed-auth attempts are throttled too and
    # the bearer token cannot be brute-forced. Rate lives in
    # DEFAULT_THROTTLE_RATES["run_migrations"] (base); tests override
    # ScopedRateThrottle.THROTTLE_RATES + a dedicated cache when asserting 429.
    throttle = ScopedRateThrottle()

    class MigrationThrottleTarget:
        throttle_scope = MIGRATIONS_THROTTLE_SCOPE

    if not throttle.allow_request(request, MigrationThrottleTarget()):
        wait = throttle.wait()
        return JsonResponse(
            {"error": "Rate limit exceeded."},
            status=429,
            headers={"Retry-After": str(int(wait)) if wait else "60"},
        )

    if settings.DEBUG:
        return JsonResponse(
            {"error": "Not allowed while DEBUG is enabled."},
            status=403,
        )

    if not MIGRATION_SECRET:
        return JsonResponse(
            {"error": "MIGRATION_SECRET is not configured."},
            status=503,
        )

    auth_header = request.headers.get("Authorization", "").encode("utf-8", "surrogateescape")
    expected_token = f"Bearer {MIGRATION_SECRET}".encode("utf-8", "surrogateescape")

    # F14: constant-time comparison so the bearer token cannot be recovered
    # through response-timing on unauthorized attempts.
    if not hmac.compare_digest(auth_header, expected_token):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        call_command("migrate", "--noinput")
        return JsonResponse({"status": "success", "message": "Migrations applied successfully"})
    except Exception:
        logger.exception("run_migrations_view: migration failed")
        return JsonResponse(
            {"error": "Migration failed."},
            status=500,
        )