"""Biometric / RFID device attendance sync.

POST /api/attendance/device-sync/ with header X-Device-Key matching an
entry in the ATTENDANCE_DEVICE_KEYS env (comma-separated).

Body:
    type: "student" | "staff"
    identifier: admission_number (student) or employee_number (staff)
    date: YYYY-MM-DD (optional, defaults to today)
    time: HH:MM (optional, stored as check_in for staff)
    status: present | absent | late | leave | half_day
"""

import os

from django.http import JsonResponse
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class BiometricSyncView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        allowed = [
            key.strip()
            for key in os.environ.get("ATTENDANCE_DEVICE_KEYS", "").split(",")
            if key.strip()
        ]

        if request.META.get("HTTP_X_DEVICE_KEY", "") not in allowed:
            return JsonResponse(
                {"detail": "Invalid device key."}, status=401
            )

        kind = (request.data.get("type") or "").strip().lower()
        identifier = (request.data.get("identifier") or "").strip()

        if kind not in ("student", "staff") or not identifier:
            return JsonResponse(
                {
                    "detail": (
                        "type (student|staff) and identifier are required."
                    )
                },
                status=400,
            )

        date_raw = request.data.get("date")

        try:
            day = (
                timezone.datetime.fromisoformat(date_raw).date()
                if date_raw
                else timezone.localdate()
            )
        except ValueError:
            return JsonResponse(
                {"detail": "date must be YYYY-MM-DD."}, status=400
            )

        status_value = (
            (request.data.get("status") or "present").strip().lower()
        )
        time_raw = (request.data.get("time") or "").strip() or None

        if kind == "student":
            from apps.attendance.models import Attendance
            from apps.students.models import Enrollment

            student_enrollment = (
                Enrollment.objects.filter(
                    student__admission_number__iexact=identifier,
                    status="active",
                )
                .select_related(
                    "campus", "class_obj", "section", "academic_year"
                )
                .first()
            )

            if student_enrollment is None:
                return JsonResponse(
                    {"detail": f"Unknown student '{identifier}'."},
                    status=404,
                )

            record, created = Attendance.objects.update_or_create(
                student_id=student_enrollment.student_id,
                date=day,
                defaults={
                    "enrollment": student_enrollment,
                    "academic_year": student_enrollment.academic_year,
                    "campus": student_enrollment.campus,
                    "class_obj": student_enrollment.class_obj,
                    "section": student_enrollment.section,
                    "status": status_value,
                    "notes": "Synced from biometric device.",
                },
            )

            return JsonResponse({
                "ok": True,
                "created": created,
                "who": record.student.full_name,
            })

        from apps.accounts.models import StaffAttendance, StaffProfile

        profile = StaffProfile.objects.filter(
            employee_number__iexact=identifier
        ).first()

        if profile is None:
            return JsonResponse(
                {"detail": f"Unknown staff '{identifier}'."}, status=404
            )

        check_in = time_raw if status_value in ("present", "late") else None

        record, created = StaffAttendance.objects.update_or_create(
            staff=profile,
            date=day,
            defaults={
                "status": status_value,
                "check_in": check_in,
                "notes": "Synced from biometric device.",
            },
        )

        return JsonResponse({
            "ok": True,
            "created": created,
            "who": profile.full_name,
        })
