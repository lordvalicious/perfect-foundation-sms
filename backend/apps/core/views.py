from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import os


MIGRATION_SECRET = os.environ.get("MIGRATION_SECRET", "")


@csrf_exempt
@require_http_methods(["POST"])
def run_migrations_view(request):
    """Secure endpoint to run migrations. Requires MIGRATION_SECRET in Authorization header."""
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

    auth_header = request.headers.get("Authorization", "")
    expected_token = f"Bearer {MIGRATION_SECRET}"

    if auth_header != expected_token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        call_command("migrate", "--noinput")
        return JsonResponse({"status": "success", "message": "Migrations applied successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)