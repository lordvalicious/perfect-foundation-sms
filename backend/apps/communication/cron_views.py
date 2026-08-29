"""Cron-triggered parent notification jobs."""

import os

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.access import is_global


def _cron_secret_valid(request):
    expected = os.environ.get("CRON_SECRET", "")

    if not expected:
        return False

    header = request.META.get("HTTP_AUTHORIZATION", "")

    return header == f"Bearer {expected}"


def _authorized(request):
    return _cron_secret_valid(request) or is_global(request.user)


class FeeReminderCronView(APIView):
    """GET /api/communication/cron/fee-reminders/?days=3[&dry_run=1]"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _authorized(request):
            return JsonResponse({"detail": "Unauthorized."}, status=401)

        from .notification_service import send_fee_reminders

        try:
            days = int(request.query_params.get("days", 3))
        except (TypeError, ValueError):
            days = 3

        summary = send_fee_reminders(
            min_days_overdue=max(0, days),
            dry_run=request.query_params.get("dry_run") == "1",
        )

        return JsonResponse(summary)


class AbsenceAlertCronView(APIView):
    """GET /api/attendance/cron/absence-alerts/[?dry_run=1]"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _authorized(request):
            return JsonResponse({"detail": "Unauthorized."}, status=401)

        from .notification_service import send_absence_alerts

        summary = send_absence_alerts(
            dry_run=request.query_params.get("dry_run") == "1"
        )

        return JsonResponse(summary)


class ProcessNotificationsCronView(APIView):
    """GET /api/communication/cron/process-notifications/[?limit=50]

    Scheduler entry point: delivers every due queued notification with
    retry/backoff. Called by the platform cron (see vercel.json).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _authorized(request):
            return JsonResponse({"detail": "Unauthorized."}, status=401)

        from .notification_queue import (
            process_due_notifications,
            queue_status,
        )

        try:
            limit = int(request.query_params.get("limit", 50))
        except (TypeError, ValueError):
            limit = 50

        summary = process_due_notifications(
            limit=max(1, min(500, limit))
        )
        summary["queue"] = queue_status()

        return JsonResponse(summary)
