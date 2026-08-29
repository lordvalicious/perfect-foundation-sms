"""Attendance Reports."""

from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class DailyAttendanceReportView(AggregateReportView):
    """Daily attendance report for a specific date."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "daily_attendance"
    model = "apps.attendance.models.Attendance"

    def get_base_queryset(self, request):
        from apps.attendance.models import Attendance
        return Attendance.objects.select_related(
            "student", "student__user", "campus", "class_obj", "section", "academic_year"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        # Date filter
        report_date = request.query_params.get("date")
        if report_date:
            queryset = queryset.filter(date=report_date)
        else:
            queryset = queryset.filter(date=timezone.now().date())

        class_obj = request.query_params.get("class")
        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        section = request.query_params.get("section")
        if section:
            queryset = queryset.filter(section_id=section)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        present = queryset.filter(status="present").count()
        absent = queryset.filter(status="absent").count()
        late = queryset.filter(status="late").count()
        leave = queryset.filter(status="leave").count()

        by_class = queryset.values("class_obj__name").annotate(
            total=Count("id"),
            present=Count(Case(When(status="present", then=1), output_field=IntegerField())),
            absent=Count(Case(When(status="absent", then=1), output_field=IntegerField())),
            late=Count(Case(When(status="late", then=1), output_field=IntegerField())),
            leave=Count(Case(When(status="leave", then=1), output_field=IntegerField())),
        )

        return {
            "date": request.query_params.get("date", str(timezone.now().date())),
            "total_students": total,
            "present": present,
            "absent": absent,
            "late": late,
            "leave": leave,
            "attendance_rate": round((present + late) / total * 100, 2) if total else 0,
            "by_class": list(by_class),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for record in queryset:
            rows.append({
                "admission_number": record.student.admission_number,
                "student": record.student.full_name,
                "campus": record.campus.name,
                "class": record.class_obj.name,
                "section": record.section.name if record.section else "-",
                "status": record.get_status_display(),
                "notes": record.notes,
            })
        return rows


class MonthlyAttendanceReportView(AggregateReportView):
    """Monthly attendance summary by class."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "monthly_attendance"
    model = "apps.attendance.models.Attendance"

    def get_base_queryset(self, request):
        from apps.attendance.models import Attendance
        return Attendance.objects.select_related("campus", "class_obj", "section")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        month = request.query_params.get("month")
        year = request.query_params.get("year", str(timezone.now().year))

        if month:
            queryset = queryset.filter(date__year=year, date__month=month)
        elif year:
            queryset = queryset.filter(date__year=year)

        class_obj = request.query_params.get("class")
        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        return queryset

    def get_summary(self, queryset, request):
        month = request.query_params.get("month")
        year = request.query_params.get("year", str(timezone.now().year))

        classes = {}
        for record in queryset:
            key = (record.campus.name, record.class_obj.name)
            if key not in classes:
                classes[key] = {
                    "campus": record.campus.name,
                    "class": record.class_obj.name,
                    "total_records": 0,
                    "present": 0,
                    "absent": 0,
                    "late": 0,
                    "leave": 0,
                }
            entry = classes[key]
            entry["total_records"] += 1
            if record.status in entry:
                entry[record.status] += 1

        for entry in classes.values():
            total = entry["total_records"]
            entry["attendance_rate"] = round(
                (entry["present"] + entry["late"]) / total * 100, 2
            ) if total else 0

        total_records = sum(c["total_records"] for c in classes.values())
        total_present = sum(c["present"] for c in classes.values())
        total_late = sum(c["late"] for c in classes.values())

        return {
            "month": f"{year}-{month.zfill(2)}" if month else year,
            "total_records": total_records,
            "overall_rate": round((total_present + total_late) / total_records * 100, 2) if total_records else 0,
        }

    def get_detail_rows(self, queryset, request):
        classes = {}
        for record in queryset:
            key = (record.campus.name, record.class_obj.name, record.section.name if record.section else "-")
            if key not in classes:
                classes[key] = {
                    "campus": record.campus.name,
                    "class": record.class_obj.name,
                    "section": record.section.name if record.section else "-",
                    "total_records": 0,
                    "present": 0,
                    "absent": 0,
                    "late": 0,
                    "leave": 0,
                }
            entry = classes[key]
            entry["total_records"] += 1
            if record.status in entry:
                entry[record.status] += 1

        rows = []
        for entry in classes.values():
            total = entry["total_records"]
            entry["attendance_rate"] = round(
                (entry["present"] + entry["late"]) / total * 100, 2
            ) if total else 0
            rows.append(entry)

        return sorted(rows, key=lambda x: (x["campus"], x["class"], x["section"]))


class StudentAttendanceReportView(AggregateReportView):
    """Individual student attendance history."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "student_attendance"
    model = "apps.attendance.models.Attendance"

    def get_base_queryset(self, request):
        from apps.attendance.models import Attendance
        return Attendance.objects.select_related(
            "student", "campus", "class_obj", "section", "academic_year"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        student_id = request.query_params.get("student")
        if not student_id:
            return queryset.none()
        queryset = queryset.filter(student_id=student_id)

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset.order_by("-date")

    def get_summary(self, queryset, request):
        total = queryset.count()
        present = queryset.filter(status="present").count()
        absent = queryset.filter(status="absent").count()
        late = queryset.filter(status="late").count()
        leave = queryset.filter(status="leave").count()

        # Monthly breakdown
        monthly = {}
        for record in queryset:
            key = record.date.strftime("%Y-%m")
            if key not in monthly:
                monthly[key] = {"month": key, "total": 0, "present": 0, "absent": 0, "late": 0, "leave": 0}
            monthly[key]["total"] += 1
            if record.status in monthly[key]:
                monthly[key][record.status] += 1

        for m in monthly.values():
            m["rate"] = round((m["present"] + m["late"]) / m["total"] * 100, 2) if m["total"] else 0

        return {
            "total_days": total,
            "present": present,
            "absent": absent,
            "late": late,
            "leave": leave,
            "attendance_rate": round((present + late) / total * 100, 2) if total else 0,
            "monthly": sorted(monthly.values(), key=lambda x: x["month"]),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for record in queryset:
            rows.append({
                "date": record.date,
                "campus": record.campus.name,
                "class": record.class_obj.name,
                "section": record.section.name if record.section else "-",
                "status": record.get_status_display(),
                "notes": record.notes,
            })
        return rows


class ClassAttendanceReportView(AggregateReportView):
    """Class-wise attendance summary."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "class_attendance"
    model = "apps.attendance.models.Attendance"

    def get_base_queryset(self, request):
        from apps.attendance.models import Attendance
        return Attendance.objects.select_related("campus", "class_obj", "section")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        month = request.query_params.get("month")
        year = request.query_params.get("year", str(timezone.now().year))

        if month:
            queryset = queryset.filter(date__year=year, date__month=month)
        elif year:
            queryset = queryset.filter(date__year=year)

        class_obj = request.query_params.get("class")
        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        return queryset

    def get_summary(self, queryset, request):
        total_records = queryset.count()
        present = queryset.filter(status="present").count()
        absent = queryset.filter(status="absent").count()
        late = queryset.filter(status="late").count()
        leave = queryset.filter(status="leave").count()

        return {
            "total_records": total_records,
            "present": present,
            "absent": absent,
            "late": late,
            "leave": leave,
            "overall_rate": round((present + late) / total_records * 100, 2) if total_records else 0,
        }

    def get_detail_rows(self, queryset, request):
        classes = {}
        for record in queryset:
            key = (record.campus.name, record.class_obj.name, record.section.name if record.section else "-")
            if key not in classes:
                classes[key] = {
                    "campus": record.campus.name,
                    "class": record.class_obj.name,
                    "section": record.section.name if record.section else "-",
                    "students": set(),
                    "total_records": 0,
                    "present": 0,
                    "absent": 0,
                    "late": 0,
                    "leave": 0,
                }
            entry = classes[key]
            entry["students"].add(record.student_id)
            entry["total_records"] += 1
            if record.status in entry:
                entry[record.status] += 1

        rows = []
        for entry in classes.values():
            total = entry["total_records"]
            student_count = len(entry["students"])
            entry["student_count"] = student_count
            entry["attendance_rate"] = round(
                (entry["present"] + entry["late"]) / total * 100, 2
            ) if total else 0
            del entry["students"]
            rows.append(entry)

        return sorted(rows, key=lambda x: (x["campus"], x["class"], x["section"]))


class AttendanceAnalyticsReportView(AggregateReportView):
    """Advanced attendance analytics."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "attendance_analytics"
    model = "apps.attendance.models.Attendance"

    def get_base_queryset(self, request):
        from apps.attendance.models import Attendance
        return Attendance.objects.select_related("student", "campus", "class_obj", "section")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        # Overall stats
        total_records = queryset.count()
        present = queryset.filter(status="present").count()
        absent = queryset.filter(status="absent").count()
        late = queryset.filter(status="late").count()
        leave = queryset.filter(status="leave").count()

        # By campus
        by_campus = queryset.values("campus__name").annotate(
            total=Count("id"),
            present=Count(Case(When(status="present", then=1))),
            absent=Count(Case(When(status="absent", then=1))),
            late=Count(Case(When(status="late", then=1))),
            leave=Count(Case(When(status="leave", then=1))),
        )

        # By class
        by_class = queryset.values("class_obj__name").annotate(
            total=Count("id"),
            present=Count(Case(When(status="present", then=1))),
            absent=Count(Case(When(status="absent", then=1))),
            late=Count(Case(When(status="late", then=1))),
            leave=Count(Case(When(status="leave", then=1))),
        )

        # Students below threshold
        threshold = float(request.query_params.get("threshold", 75))
        students = {}
        for record in queryset:
            sid = record.student_id
            if sid not in students:
                students[sid] = {"total": 0, "present": 0, "late": 0}
            students[sid]["total"] += 1
            if record.status in ("present", "late"):
                students[sid]["present"] += 1

        below_threshold = []
        for sid, data in students.items():
            rate = (data["present"] / data["total"] * 100) if data["total"] else 0
            if rate < threshold:
                from apps.students.models import Student
                try:
                    student = Student.objects.get(id=sid)
                    below_threshold.append({
                        "admission_number": student.admission_number,
                        "name": student.full_name,
                        "campus": student.primary_campus.name if student.primary_campus else "-",
                        "rate": round(rate, 2),
                    })
                except Student.DoesNotExist:
                    pass

        # Perfect attendance
        perfect = []
        for sid, data in students.items():
            rate = (data["present"] / data["total"] * 100) if data["total"] else 0
            if rate == 100:
                from apps.students.models import Student
                try:
                    student = Student.objects.get(id=sid)
                    perfect.append({
                        "admission_number": student.admission_number,
                        "name": student.full_name,
                        "campus": student.primary_campus.name if student.primary_campus else "-",
                    })
                except Student.DoesNotExist:
                    pass

        return {
            "overall": {
                "total_records": total_records,
                "present": present,
                "absent": absent,
                "late": late,
                "leave": leave,
                "attendance_rate": round((present + late) / total_records * 100, 2) if total_records else 0,
            },
            "by_campus": [
                {
                    **c,
                    "rate": round((c["present"] + c["late"]) / c["total"] * 100, 2) if c["total"] else 0
                } for c in by_campus
            ],
            "by_class": [
                {
                    **c,
                    "rate": round((c["present"] + c["late"]) / c["total"] * 100, 2) if c["total"] else 0
                } for c in by_class
            ],
            "below_threshold": below_threshold[:50],
            "perfect_attendance": perfect[:50],
            "threshold": threshold,
        }

    def get_detail_rows(self, queryset, request):
        return []


class ChronicAbsenteeReportView(AggregateReportView):
    """Students with attendance below threshold."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "chronic_absentee"
    model = "apps.attendance.models.Attendance"

    def get_base_queryset(self, request):
        from apps.attendance.models import Attendance
        return Attendance.objects.select_related("student", "campus", "class_obj", "section")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        month = request.query_params.get("month")
        year = request.query_params.get("year", str(timezone.now().year))

        if month:
            queryset = queryset.filter(date__year=year, date__month=month)
        elif year:
            queryset = queryset.filter(date__year=year)

        class_obj = request.query_params.get("class")
        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        return queryset

    def get_summary(self, queryset, request):
        threshold = float(request.query_params.get("threshold", 75))

        students = {}
        for record in queryset:
            sid = record.student_id
            if sid not in students:
                students[sid] = {
                    "total": 0, "present": 0, "absent": 0, "late": 0, "leave": 0,
                    "student": record.student
                }
            students[sid]["total"] += 1
            if record.status in students[sid]:
                students[sid][record.status] += 1

        flagged = []
        for sid, data in students.items():
            rate = round(data["present"] / data["total"] * 100, 2) if data["total"] else 100
            data["attendance_rate"] = rate
            if rate < threshold:
                student = data["student"]
                flagged.append({
                    "admission_number": student.admission_number,
                    "name": student.full_name,
                    "campus": student.primary_campus.name if student.primary_campus else "-",
                    "class": data["student"].enrollments.filter(status="active").first().class_obj.name
                    if data["student"].enrollments.filter(status="active").exists() else "-",
                    "total_days": data["total"],
                    "present": data["present"],
                    "absent": data["absent"],
                    "leave": data["leave"],
                    "rate": rate,
                })

        flagged.sort(key=lambda x: x["rate"])

        return {
            "threshold": threshold,
            "students_tracked": len(students),
            "students_flagged": len(flagged),
        }

    def get_detail_rows(self, queryset, request):
        threshold = float(request.query_params.get("threshold", 75))

        students = {}
        for record in queryset:
            sid = record.student_id
            if sid not in students:
                students[sid] = {
                    "total": 0, "present": 0, "absent": 0, "late": 0, "leave": 0,
                    "student": record.student
                }
            students[sid]["total"] += 1
            if record.status in students[sid]:
                students[sid][record.status] += 1

        flagged = []
        for sid, data in students.items():
            rate = round(data["present"] / data["total"] * 100, 2) if data["total"] else 100
            if rate < threshold:
                student = data["student"]
                flagged.append({
                    "admission_number": student.admission_number,
                    "student": student.full_name,
                    "campus": student.primary_campus.name if student.primary_campus else "-",
                    "class": student.enrollments.filter(status="active").first().class_obj.name
                    if student.enrollments.filter(status="active").exists() else "-",
                    "section": student.enrollments.filter(status="active").first().section.name
                    if student.enrollments.filter(status="active").first().section else "-",
                    "total_days": data["total"],
                    "present": data["present"],
                    "absent": data["absent"],
                    "leave": data["leave"],
                    "attendance_rate": rate,
                })

        flagged.sort(key=lambda x: x["attendance_rate"])
        return flagged


class SubjectAttendanceReportView(AggregateReportView):
    """Subject-wise attendance if supported."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "subject_attendance"
    model = "apps.attendance.models.Attendance"

    def get_base_queryset(self, request):
        from apps.attendance.models import Attendance
        return Attendance.objects.select_related("campus", "class_obj", "section")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        # Note: Subject attendance would need a separate model or timetable integration
        # This is a placeholder for when subject attendance is implemented
        return queryset

    def get_summary(self, queryset, request):
        return {"message": "Subject attendance requires timetable integration"}

    def get_detail_rows(self, queryset, request):
        return []