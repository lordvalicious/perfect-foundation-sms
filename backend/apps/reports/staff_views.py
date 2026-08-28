"""Staff and Teacher Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class StaffMasterReportView(AggregateReportView):
    """Staff master report with all details."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "staff_master"
    model = "apps.accounts.models.StaffProfile"

    def get_base_queryset(self, request):
        from apps.accounts.models import StaffProfile
        return StaffProfile.objects.select_related(
            "user", "membership", "primary_campus", "institution"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")

        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        designation = request.query_params.get("designation")
        if designation:
            queryset = queryset.filter(designation__icontains=designation)

        department = request.query_params.get("department")
        if department:
            queryset = queryset.filter(department__icontains=department)

        campus = request.query_params.get("campus")
        if campus:
            queryset = queryset.filter(primary_campus_id=campus)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_status = queryset.values("status").annotate(count=Count("id"))
        by_designation = queryset.values("designation").annotate(count=Count("id"))
        by_department = queryset.values("department").annotate(count=Count("id"))
        by_campus = queryset.values("primary_campus__name").annotate(count=Count("id"))

        return {
            "total_staff": total,
            "by_status": list(by_status),
            "by_designation": list(by_designation),
            "by_department": list(by_department),
            "by_campus": list(by_campus),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for staff in queryset:
            rows.append({
                "employee_number": staff.employee_number,
                "full_name": staff.full_name,
                "photo": staff.photo.url if staff.photo else None,
                "gender": staff.gender,
                "date_of_birth": staff.date_of_birth,
                "designation": staff.designation,
                "department": staff.department,
                "phone": staff.phone,
                "email": staff.email,
                "campus": staff.campus if staff.campus else (staff.primary_campus.name if staff.primary_campus else "-"),
                "primary_campus": staff.primary_campus.name if staff.primary_campus else "-",
                "joining_date": staff.joining_date,
                "status": staff.status,
                "user_email": staff.user.email if staff.user else "-",
                "user_phone": staff.user.phone if staff.user else "-",
            })
        return rows


class TeacherMasterReportView(AggregateReportView):
    """Teacher master report with assignments."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "teacher_master"
    model = "apps.teachers.models.Teacher"

    def get_base_queryset(self, request):
        from apps.teachers.models import Teacher
        return Teacher.objects.select_related(
            "user", "primary_campus", "membership", "institution"
        ).prefetch_related("assignments__class_obj", "assignments__section", "assignments__subject", "assignments__campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")

        department = request.query_params.get("department")
        if department:
            queryset = queryset.filter(department__icontains=department)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_department = queryset.values("department").annotate(count=Count("id"))
        by_campus = queryset.values("primary_campus__name").annotate(count=Count("id"))

        # Teachers with active assignments
        with_assignments = 0
        for t in queryset:
            if t.assignments.filter(status="active").exists():
                with_assignments += 1

        return {
            "total_teachers": total,
            "with_assignments": with_assignments,
            "without_assignments": total - with_assignments,
            "by_department": list(by_department),
            "by_campus": list(by_campus),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for teacher in queryset:
            active_assignments = teacher.assignments.filter(status="active")
            subjects = ", ".join(set(a.subject.name for a in active_assignments))
            classes = ", ".join(set(a.class_obj.name for a in active_assignments))

            rows.append({
                "employee_number": teacher.employee_number,
                "full_name": teacher.full_name,
                "photo": teacher.photo.url if teacher.photo else None,
                "gender": teacher.gender,
                "date_of_birth": teacher.date_of_birth,
                "qualification": teacher.qualification,
                "experience_years": teacher.experience_years,
                "department": teacher.department,
                "phone": teacher.phone,
                "email": teacher.email,
                "bank_name": teacher.bank_name,
                "account_number": teacher.account_number,
                "primary_campus": teacher.primary_campus.name if teacher.primary_campus else "-",
                "joining_date": teacher.joining_date,
                "status": teacher.status,
                "subjects": subjects or "-",
                "classes": classes or "-",
                "assignments_count": active_assignments.count(),
            })
        return rows


class StaffAttendanceReportView(AggregateReportView):
    """Staff attendance report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "staff_attendance_report"
    model = "apps.accounts.models.StaffAttendance"

    def get_base_queryset(self, request):
        from apps.accounts.models import StaffAttendance
        return StaffAttendance.objects.select_related("staff", "staff__user", "marked_by")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "staff__primary_campus_id")

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        staff = request.query_params.get("staff")
        if staff:
            queryset = queryset.filter(staff_id=staff)

        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        present = queryset.filter(status="present").count()
        absent = queryset.filter(status="absent").count()
        late = queryset.filter(status="late").count()
        half_day = queryset.filter(status="half_day").count()
        leave = queryset.filter(status="leave").count()

        by_staff = queryset.values("staff__full_name").annotate(
            total=Count("id"),
            present=Count(Case(When(status="present", then=1))),
            absent=Count(Case(When(status="absent", then=1))),
            late=Count(Case(When(status="late", then=1))),
            leave=Count(Case(When(status="leave", then=1))),
        )

        return {
            "total_records": total,
            "present": present,
            "absent": absent,
            "late": late,
            "half_day": half_day,
            "leave": leave,
            "attendance_rate": round((present + late + half_day) / total * 100, 2) if total else 0,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for record in queryset:
            rows.append({
                "date": record.date,
                "employee_number": record.staff.employee_number,
                "staff": record.staff.full_name,
                "status": record.get_status_display(),
                "check_in": record.check_in,
                "check_out": record.check_out,
                "notes": record.notes,
                "marked_by": record.marked_by.get_full_name() if record.marked_by else "-",
            })
        return rows


class TeacherAttendanceReportView(StaffAttendanceReportView):
    """Teacher attendance report - reuses staff attendance model."""
    report_definition_key = "teacher_attendance_report"


class StaffLeaveReportView(AggregateReportView):
    """Staff leave report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "staff_leave_report"
    model = "apps.accounts.models.StaffLeave"

    def get_base_queryset(self, request):
        from apps.accounts.models import StaffLeave
        return StaffLeave.objects.select_related("staff", "staff__user", "reviewed_by")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "staff__primary_campus_id")

        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        leave_type = request.query_params.get("leave_type")
        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_status = queryset.values("status").annotate(count=Count("id"))
        by_type = queryset.values("leave_type").annotate(count=Count("id"))

        total_days = sum(l.days for l in queryset)
        approved_days = sum(l.days for l in queryset.filter(status="approved"))

        return {
            "total_requests": total,
            "total_days": total_days,
            "approved_days": approved_days,
            "by_status": list(by_status),
            "by_type": list(by_type),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for leave in queryset:
            rows.append({
                "staff": leave.staff.full_name,
                "employee_number": leave.staff.employee_number,
                "leave_type": leave.get_leave_type_display(),
                "start_date": leave.start_date,
                "end_date": leave.end_date,
                "days": leave.days,
                "reason": leave.reason,
                "status": leave.get_status_display(),
                "reviewed_by": leave.reviewed_by.get_full_name() if leave.reviewed_by else "-",
                "review_notes": leave.review_notes,
            })
        return rows


class TeacherLeaveReportView(StaffLeaveReportView):
    """Teacher leave report - reuses staff leave model."""
    report_definition_key = "teacher_leave_report"


class TeacherWorkloadReportView(AggregateReportView):
    """Teacher workload: subjects, sections, assignments."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "teacher_workload"
    model = "apps.teachers.models.TeacherAssignment"

    def get_base_queryset(self, request):
        from apps.teachers.models import TeacherAssignment
        return TeacherAssignment.objects.filter(status="active").select_related(
            "teacher", "teacher__user", "campus", "class_obj", "section", "subject", "academic_year"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        return queryset

    def get_summary(self, queryset, request):
        teachers = {}
        for assignment in queryset:
            tid = assignment.teacher_id
            if tid not in teachers:
                teachers[tid] = {
                    "teacher": assignment.teacher.full_name,
                    "employee_number": assignment.teacher.employee_number,
                    "campus": assignment.campus.name,
                    "assignments": 0,
                    "subjects": set(),
                    "classes": set(),
                    "sections": set(),
                }
            t = teachers[tid]
            t["assignments"] += 1
            t["subjects"].add(assignment.subject.name)
            t["classes"].add(assignment.class_obj.name)
            t["sections"].add(assignment.section.name)

        total_assignments = sum(t["assignments"] for t in teachers.values())

        return {
            "total_teachers": len(teachers),
            "total_assignments": total_assignments,
        }

    def get_detail_rows(self, queryset, request):
        teachers = {}
        for assignment in queryset:
            tid = assignment.teacher_id
            if tid not in teachers:
                teachers[tid] = {
                    "teacher": assignment.teacher.full_name,
                    "employee_number": assignment.teacher.employee_number,
                    "campus": assignment.campus.name,
                    "assignments": 0,
                    "subjects": set(),
                    "classes": set(),
                    "sections": set(),
                }
            t = teachers[tid]
            t["assignments"] += 1
            t["subjects"].add(assignment.subject.name)
            t["classes"].add(assignment.class_obj.name)
            t["sections"].add(assignment.section.name)

        rows = []
        for t in teachers.values():
            t["subjects"] = ", ".join(sorted(t["subjects"]))
            t["classes"] = ", ".join(sorted(t["classes"]))
            t["sections"] = ", ".join(sorted(t["sections"]))
            rows.append(t)

        return sorted(rows, key=lambda x: x["teacher"])


class DepartmentReportView(AggregateReportView):
    """Department-wise staff report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "department_report"
    model = "apps.accounts.models.StaffProfile"

    def get_base_queryset(self, request):
        from apps.accounts.models import StaffProfile
        return StaffProfile.objects.exclude(department="").select_related("primary_campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")
        return queryset

    def get_summary(self, queryset, request):
        departments = queryset.values("department").annotate(
            count=Count("id"),
            campus_count=Count("primary_campus", distinct=True),
        ).order_by("-count")

        return {
            "total_departments": departments.count(),
            "total_staff": queryset.count(),
        }

    def get_detail_rows(self, queryset, request):
        departments = {}
        for staff in queryset:
            dept = staff.department or "Unassigned"
            campus = staff.primary_campus.name if staff.primary_campus else "Unassigned"
            key = (dept, campus)

            if key not in departments:
                departments[key] = {
                    "department": dept,
                    "campus": campus,
                    "staff_count": 0,
                    "designations": set(),
                }
            departments[key]["staff_count"] += 1
            departments[key]["designations"].add(staff.designation or "Staff")

        rows = []
        for d in departments.values():
            d["designations"] = ", ".join(sorted(d["designations"]))
            rows.append(d)

        return sorted(rows, key=lambda x: (x["department"], x["campus"]))


class DesignationReportView(AggregateReportView):
    """Designation-wise staff report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "designation_report"
    model = "apps.accounts.models.StaffProfile"

    def get_base_queryset(self, request):
        from apps.accounts.models import StaffProfile
        return StaffProfile.objects.select_related("primary_campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")
        return queryset

    def get_summary(self, queryset, request):
        designations = queryset.values("designation").annotate(
            count=Count("id"),
        ).order_by("-count")

        return {
            "total_designations": designations.count(),
            "total_staff": queryset.count(),
        }

    def get_detail_rows(self, queryset, request):
        designations = {}
        for staff in queryset:
            desig = staff.designation or "Staff"
            campus = staff.primary_campus.name if staff.primary_campus else "Unassigned"
            key = (desig, campus)

            if key not in designations:
                designations[key] = {
                    "designation": desig,
                    "campus": campus,
                    "count": 0,
                }
            designations[key]["count"] += 1

        return sorted(designations.values(), key=lambda x: (x["designation"], x["campus"]))


class StaffJoiningReportView(AggregateReportView):
    """Staff joining report by period."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "staff_joining"
    model = "apps.accounts.models.StaffProfile"

    def get_base_queryset(self, request):
        from apps.accounts.models import StaffProfile
        return StaffProfile.objects.select_related("primary_campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(joining_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(joining_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_month = queryset.extra(select={"month": "strftime('%%Y-%%m', joining_date)"}).values("month").annotate(count=Count("id")).order_by("month")

        return {
            "total_joined": total,
            "by_month": list(by_month),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for staff in queryset.order_by("joining_date"):
            rows.append({
                "employee_number": staff.employee_number,
                "full_name": staff.full_name,
                "designation": staff.designation,
                "department": staff.department,
                "campus": staff.primary_campus.name if staff.primary_campus else "-",
                "joining_date": staff.joining_date,
            })
        return rows


class StaffResignationReportView(AggregateReportView):
    """Staff resignation/termination report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "staff_resignation"
    model = "apps.accounts.models.StaffProfile"

    def get_base_queryset(self, request):
        from apps.accounts.models import StaffProfile
        return StaffProfile.objects.filter(status="inactive").select_related("primary_campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")
        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_campus = queryset.values("primary_campus__name").annotate(count=Count("id"))
        by_department = queryset.values("department").annotate(count=Count("id"))

        return {
            "total_resigned": total,
            "by_campus": list(by_campus),
            "by_department": list(by_department),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for staff in queryset:
            rows.append({
                "employee_number": staff.employee_number,
                "full_name": staff.full_name,
                "designation": staff.designation,
                "department": staff.department,
                "campus": staff.primary_campus.name if staff.primary_campus else "-",
                "joining_date": staff.joining_date,
                "status": staff.get_status_display(),
            })
        return rows