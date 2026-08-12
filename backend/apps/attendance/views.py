from collections import OrderedDict
from datetime import date as date_cls

from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    IsAcademicMemberRole,
    IsTeacherRole,
)
from apps.accounts.scopes import (
    get_student_profile,
    is_manager,
    is_parent,
    is_student,
    is_teacher,
    parent_student_ids,
    teacher_class_ids,
    teacher_student_ids,
)
from apps.audit.models import record_audit
from apps.students.models import Enrollment

from .models import Attendance
from .serializers import AttendanceSerializer


class AttendanceListView(generics.ListAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAcademicMemberRole]

    def get_queryset(self):
        queryset = (
            Attendance.objects
            .select_related(
                "student",
                "campus",
                "class_obj",
                "section",
                "academic_year",
            )
            .order_by("-date", "student__first_name")
        )

        user = self.request.user

        if not is_manager(user):
            if is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(student=profile)
            elif is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)
            elif is_teacher(user):
                student_ids = teacher_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(student__first_name__icontains=search)
                | Q(student__middle_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(student__admission_number__icontains=search)
            )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        date = self.request.query_params.get("date")

        if date:
            queryset = queryset.filter(date=date)

        student = self.request.query_params.get("student")

        if student:
            queryset = queryset.filter(student_id=student)

        campus = self.request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus_id=campus)

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        return queryset


class AttendanceBulkMarkView(APIView):
    """
    Mark (or update) attendance for a whole class/section on a date.

    Body::

        {
          "academic_year": 1,
          "campus": 1,
          "class": 1,
          "section": 1,
          "date": "2026-08-12",
          "records": [
            {"student": 5, "status": "present", "notes": ""},
            {"student": 8, "status": "absent", "notes": ""}
          ]
        }

    Teachers may only mark classes they are assigned to.
    """

    permission_classes = [IsTeacherRole]

    def post(self, request):
        user = request.user
        data = request.data

        academic_year = data.get("academic_year")
        campus = data.get("campus")
        class_obj = data.get("class")
        section = data.get("section")
        day = data.get("date")
        records = data.get("records") or []

        for field in [
            "academic_year",
            "campus",
            "class",
            "section",
            "date",
        ]:
            if not data.get(field):
                return Response(
                    {"detail": f"{field} is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not records:
            return Response(
                {"detail": "records is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not is_manager(user):
            if int(class_obj) not in teacher_class_ids(user):
                return Response(
                    {
                        "detail": (
                            "You can only mark attendance for "
                            "classes you are assigned to."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        if day > str(date_cls.today()):
            return Response(
                {"detail": "Attendance cannot be marked for a future date."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollments = Enrollment.objects.filter(
            academic_year_id=academic_year,
            campus_id=campus,
            class_obj_id=class_obj,
            section_id=section,
            status="active",
        ).select_related("student")

        enrollment_map = {
            enrollment.student_id: enrollment
            for enrollment in enrollments
        }

        created = 0
        updated = 0
        skipped = []

        for record in records:
            student_id = record.get("student")
            att_status = record.get("status")
            notes = record.get("notes", "")

            enrollment = enrollment_map.get(student_id)

            if enrollment is None:
                skipped.append(
                    {
                        "student": student_id,
                        "reason": "No active enrollment in this class.",
                    }
                )
                continue

            try:
                attendance, was_created = (
                    Attendance.objects.get_or_create(
                        student_id=student_id,
                        date=day,
                        defaults={
                            "enrollment": enrollment,
                            "academic_year_id": academic_year,
                            "campus_id": campus,
                            "class_obj_id": class_obj,
                            "section_id": section,
                            "status": att_status,
                            "notes": notes,
                        },
                    )
                )

                if not was_created:
                    attendance.status = att_status
                    attendance.notes = notes
                    attendance.save(update_fields=["status", "notes"])
                    updated += 1
                else:
                    created += 1
            except ValidationError as exc:
                skipped.append(
                    {
                        "student": student_id,
                        "reason": exc.message_dict,
                    }
                )

        record_audit(
            request=request,
            action="create",
            model_name="Attendance",
            object_id=str(day),
            object_repr=f"Bulk attendance for class {class_obj} on {day}",
            details={
                "created": created,
                "updated": updated,
                "skipped": len(skipped),
            },
        )

        return Response(
            {
                "created": created,
                "updated": updated,
                "skipped": skipped,
            }
        )


class AttendanceSummaryView(APIView):
    """
    Attendance statistics.

    For a single student:

        GET /api/attendance/summary/?student=5&month=2026-08

    For a class (manager/teacher only):

        GET /api/attendance/summary/?academic_year=1&campus=1
            &class=1&section=1&month=2026-08
    """

    permission_classes = [IsAcademicMemberRole]

    def get(self, request):
        user = request.user
        queryset = Attendance.objects.all()

        if not is_manager(user):
            if is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return Response({"detail": "No student profile."}, status=403)

                queryset = queryset.filter(student=profile)
            elif is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return Response({"detail": "No children found."}, status=403)

                queryset = queryset.filter(student_id__in=student_ids)
            elif is_teacher(user):
                student_ids = teacher_student_ids(user)

                if not student_ids:
                    return Response({"detail": "No assigned students."}, status=403)

                queryset = queryset.filter(student_id__in=student_ids)

        student = request.query_params.get("student")

        if student:
            queryset = queryset.filter(student_id=student)

        month = request.query_params.get("month")
        start = request.query_params.get("start")
        end = request.query_params.get("end")

        if month:
            queryset = queryset.filter(date__startswith=month)

        if start:
            queryset = queryset.filter(date__gte=start)

        if end:
            queryset = queryset.filter(date__lte=end)

        academic_year = request.query_params.get("academic_year")

        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        campus = request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus_id=campus)

        class_obj = request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        section = request.query_params.get("section")

        if section:
            queryset = queryset.filter(section_id=section)

        grouped = queryset.values("status").annotate(
            count=Count("id")
        )

        counts = {
            "present": 0,
            "absent": 0,
            "late": 0,
            "leave": 0,
        }

        for row in grouped:
            counts[row["status"]] = row["count"]

        total = sum(counts.values())
        present_like = counts["present"] + counts["late"]

        percentage = (
            round((present_like / total) * 100, 2)
            if total
            else 0.0
        )

        return Response(
            {
                **counts,
                "total": total,
                "attendance_percentage": percentage,
            }
        )


class AttendanceMonthlyView(APIView):
    """
    Per-day attendance breakdown for a class/section within a month.

        GET /api/attendance/monthly/?academic_year=1&campus=1
            &class=1&section=1&month=2026-08
    """

    permission_classes = [IsTeacherRole]

    def get(self, request):
        user = request.user
        queryset = Attendance.objects.all()

        academic_year = request.query_params.get("academic_year")
        campus = request.query_params.get("campus")
        class_obj = request.query_params.get("class")
        section = request.query_params.get("section")
        month = request.query_params.get("month")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

            if not is_manager(user):
                if int(class_obj) not in teacher_class_ids(user):
                    return Response(
                        {
                            "detail": (
                                "You can only view attendance for "
                                "classes you are assigned to."
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
        elif is_student(user) or is_parent(user):
            if is_student(user):
                profile = get_student_profile(user)
                queryset = queryset.filter(student=profile)
            elif is_parent(user):
                student_ids = parent_student_ids(user)
                queryset = queryset.filter(student_id__in=student_ids)

        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        if campus:
            queryset = queryset.filter(campus_id=campus)

        if section:
            queryset = queryset.filter(section_id=section)

        if month:
            queryset = queryset.filter(date__startswith=month)

        rows = (
            queryset
            .values("date", "status")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        daily = OrderedDict()

        for row in rows:
            day = row["date"]
            entry = daily.setdefault(
                day,
                {
                    "date": str(day),
                    "present": 0,
                    "absent": 0,
                    "late": 0,
                    "leave": 0,
                    "total": 0,
                },
            )
            entry[row["status"]] = row["count"]
            entry["total"] += row["count"]

        for entry in daily.values():
            present_like = entry["present"] + entry["late"]
            entry["attendance_percentage"] = (
                round(
                    (present_like / entry["total"]) * 100,
                    2,
                )
                if entry["total"]
                else 0.0
            )

        return Response(list(daily.values()))
