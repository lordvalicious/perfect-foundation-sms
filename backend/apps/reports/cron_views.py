"""Scheduled email digests for administrators."""

import os

from django.http import JsonResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.access import is_global

from .views import REPORT_VIEW_MAP


def _cron_secret_valid(request):
    expected = os.environ.get("CRON_SECRET", "")

    if not expected:
        return False

    header = request.META.get("HTTP_AUTHORIZATION", "")

    return header == f"Bearer {expected}"


def _build_digest(request):
    """Compile the weekly numbers from the existing report views."""
    from django.utils.module_loading import import_string
    from django.utils import timezone
    from django.test import RequestFactory
    from rest_framework.request import Request as DRFRequest

    today = timezone.localdate()
    month_start = today.replace(day=1)

    factory = RequestFactory()

    def sub(report_type, **filters):
        view_class = import_string(REPORT_VIEW_MAP[report_type])
        query = "&".join(f"{k}={v}" for k, v in filters.items() if v)
        raw = factory.get(f"/api/reports/{report_type}/?{query}")
        req = DRFRequest(raw)
        req._user = request.user

        try:
            return view_class()._data(req)
        except Exception:
            return {}

    sections = []

    enrollment = sub("enrollment")
    if isinstance(enrollment, dict):
        sections.append(
            (
                "Enrollment",
                [
                    f"Active students: {enrollment.get('total_students', 0)}",
                    f"Classes: {enrollment.get('total_classes', 0)}",
                ],
            )
        )
    elif isinstance(enrollment, list) and enrollment:
        total = sum(row.get("total", 0) for row in enrollment)
        sections.append(
            (
                "Enrollment",
                [
                    f"Active students: {total}",
                    f"Class groups: {len(enrollment)}",
                ],
            )
        )

    attendance = sub("attendance", year=str(today.year), month=str(today.month))
    if isinstance(attendance, dict):
        sections.append(
            (
                f"Attendance ({today.strftime('%B')})",
                [
                    f"Overall rate: {attendance.get('overall_attendance_rate', 0)}%",
                ],
            )
        )
    elif isinstance(attendance, list) and attendance:
        records = sum(row.get("total_records", 0) for row in attendance)
        attended = sum(
            row.get("present", 0) + row.get("late", 0)
            for row in attendance
        )
        rate = round(attended / records * 100, 1) if records else 0
        sections.append(
            (
                f"Attendance ({today.strftime('%B')})",
                [f"Overall rate: {rate}%"],
            )
        )

    fees = sub(
        "fees",
        start_date=month_start.isoformat(),
        end_date=today.isoformat(),
    )
    if fees:
        summary = fees.get("summary", {})
        sections.append(
            (
                f"Fees ({today.strftime('%B')})",
                [
                    f"Invoiced: {summary.get('total_invoiced', 0)}",
                    f"Collected: {summary.get('total_collected', 0)}",
                    f"Outstanding: {summary.get('total_outstanding', 0)}",
                    f"Collection rate: {summary.get('collection_rate', 0)}%",
                ],
            )
        )

    defaulters = sub("fee_defaulters")
    if defaulters:
        summary = defaulters.get("summary", {})
        sections.append(
            (
                "Fee defaulters",
                [
                    f"Students with dues: {summary.get('total_defaulters', 0)}",
                    f"Total outstanding: {summary.get('total_outstanding', 0)}",
                ],
            )
        )

    lines = []
    for title, items in sections:
        lines.append(title.upper())
        lines.extend(f"  - {item}" for item in items)
        lines.append("")

    return "\n".join(lines) or "No data available this week."


class WeeklyReportEmailCronView(APIView):
    """GET /api/reports/cron/email-weekly/

    Sends a summary digest to every admin/super_admin account.
    Guarded by CRON_SECRET bearer token (Vercel Cron) or a signed-in
    administrator.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (_cron_secret_valid(request) or is_global(request.user)):
            return JsonResponse({"detail": "Unauthorized."}, status=401)

        from apps.communication.email_service import (
            email_configured,
            send_email_message,
        )
        from apps.communication.models import EmailLog

        if not email_configured():
            return JsonResponse(
                {
                    "detail": (
                        "Email not configured — set DJANGO_EMAIL_* "
                        "variables first."
                    )
                },
                status=503,
            )

        from django.db.models import Q

        from apps.accounts.models import User

        admins = list(
            User.objects.filter(is_active=True)
            .filter(
                Q(is_superuser=True)
                | Q(
                    memberships__status="active",
                    memberships__role_assignments__role__in=[
                        "super_admin",
                        "admin",
                    ],
                )
            )
            .exclude(email="")
            .distinct()
            .values_list("email", flat=True)
        )

        subject = (
            f"Weekly school summary — "
            f"{timezone.localdate().strftime('%d %b %Y')}"
        )

        sent, failed, errors = 0, 0, []

        for email in sorted(set(admins)):
            ok, err = send_email_message(email, subject, _build_digest(request))

            EmailLog.objects.create(
                recipient_email=email,
                subject=subject,
                body="Weekly digest",
                status="sent" if ok else "failed",
                error=err or "",
                sent_by=request.user if request.user.is_authenticated else None,
            )

            if ok:
                sent += 1
            else:
                failed += 1
                errors.append(err)

        return JsonResponse({
            "sent": sent,
            "failed": failed,
            "recipients": len(admins),
            "errors": errors[:5],
        })
