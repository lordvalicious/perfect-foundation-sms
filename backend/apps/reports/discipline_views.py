"""Discipline Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class DisciplineIncidentsReportView(AggregateReportView):
    """Discipline incidents report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "discipline_incidents"
    model = "apps.discipline.models.DisciplineIncident"

    def get_base_queryset(self, request):
        from apps.discipline.models import DisciplineIncident
        return DisciplineIncident.objects.select_related(
            "student", "student__primary_campus", "campus", "reported_by", "action_taken_by"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        incident_type = request.query_params.get("incident_type")
        if incident_type:
            queryset = queryset.filter(incident_type=incident_type)

        severity = request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(incident_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(incident_date__lte=date_to)

        student = request.query_params.get("student")
        if student:
            queryset = queryset.filter(student_id=student)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_type = queryset.values("incident_type").annotate(count=Count("id"))
        by_severity = queryset.values("severity").annotate(count=Count("id"))
        by_campus = queryset.values("campus__name").annotate(count=Count("id"))
        by_status = queryset.values("status").annotate(count=Count("id"))

        return {
            "total_incidents": total,
            "by_type": list(by_type),
            "by_severity": list(by_severity),
            "by_campus": list(by_campus),
            "by_status": list(by_status),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for incident in queryset:
            rows.append({
                "incident_id": incident.incident_id,
                "date": incident.incident_date,
                "student": incident.student.full_name,
                "admission_number": incident.student.admission_number,
                "campus": incident.campus.name if incident.campus else "-",
                "class": incident.student.enrollments.filter(status="active").first().class_obj.name
                if incident.student.enrollments.filter(status="active").exists() else "-",
                "incident_type": incident.get_incident_type_display(),
                "severity": incident.get_severity_display(),
                "description": incident.description,
                "status": incident.get_status_display(),
                "reported_by": incident.reported_by.get_full_name() if incident.reported_by else "-",
                "action_taken": incident.action_taken,
                "action_by": incident.action_taken_by.get_full_name() if incident.action_taken_by else "-",
            })
        return rows


class StudentIncidentsReportView(AggregateReportView):
    """Student-wise discipline incidents."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "discipline_student"
    model = "apps.discipline.models.DisciplineIncident"

    def get_base_queryset(self, request):
        from apps.discipline.models import DisciplineIncident
        return DisciplineIncident.objects.select_related("student", "campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        student = request.query_params.get("student")
        if student:
            queryset = queryset.filter(student_id=student)

        return queryset

    def get_summary(self, queryset, request):
        students = {}
        for incident in queryset:
            sid = incident.student_id
            if sid not in students:
                students[sid] = {"student": incident.student, "count": 0, "types": set()}
            students[sid]["count"] += 1
            students[sid]["types"].add(incident.incident_type)

        return {
            "students_with_incidents": len(students),
            "total_incidents": queryset.count(),
        }

    def get_detail_rows(self, queryset, request):
        students = {}
        for incident in queryset:
            sid = incident.student_id
            if sid not in students:
                students[sid] = {"student": incident.student, "incidents": []}
            students[sid]["incidents"].append(incident)

        rows = []
        for data in students.values():
            student = data["student"]
            for incident in data["incidents"]:
                rows.append({
                    "admission_number": student.admission_number,
                    "student": student.full_name,
                    "campus": incident.campus.name if incident.campus else "-",
                    "date": incident.incident_date,
                    "incident_type": incident.get_incident_type_display(),
                    "severity": incident.get_severity_display(),
                    "description": incident.description,
                    "status": incident.get_status_display(),
                })
        return rows


class ClassIncidentsReportView(AggregateReportView):
    """Class-wise discipline incidents."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "discipline_class"
    model = "apps.discipline.models.DisciplineIncident"

    def get_base_queryset(self, request):
        from apps.discipline.models import DisciplineIncident
        return DisciplineIncident.objects.select_related("student", "campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")
        return queryset

    def get_summary(self, queryset, request):
        classes = {}
        for incident in queryset:
            enrollment = incident.student.enrollments.filter(status="active").first()
            if enrollment:
                key = (incident.campus.name if incident.campus else "-", enrollment.class_obj.name)
                if key not in classes:
                    classes[key] = {"campus": key[0], "class": key[1], "count": 0}
                classes[key]["count"] += 1

        return {
            "classes_with_incidents": len(classes),
            "total_incidents": queryset.count(),
        }

    def get_detail_rows(self, queryset, request):
        classes = {}
        for incident in queryset:
            enrollment = incident.student.enrollments.filter(status="active").first()
            if enrollment:
                key = (incident.campus.name if incident.campus else "-", enrollment.class_obj.name)
                if key not in classes:
                    classes[key] = {"campus": key[0], "class": key[1], "count": 0, "types": set()}
                classes[key]["count"] += 1
                classes[key]["types"].add(incident.incident_type)

        rows = []
        for c in classes.values():
            c["types"] = ", ".join(sorted(c["types"]))
            rows.append(c)
        return sorted(rows, key=lambda x: (x["campus"], x["class"]))


class CampusIncidentsReportView(AggregateReportView):
    """Campus-wise discipline incidents."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "discipline_campus"
    model = "apps.discipline.models.DisciplineIncident"

    def get_base_queryset(self, request):
        from apps.discipline.models import DisciplineIncident
        return DisciplineIncident.objects.select_related("campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

    def get_summary(self, queryset, request):
        campuses = queryset.values("campus__name").annotate(count=Count("id"))
        return {"total_incidents": queryset.count()}

    def get_detail_rows(self, queryset, request):
        campuses = queryset.values("campus__name").annotate(
            total=Count("id"),
            warning=Count(Case(When(severity="warning", then=1))),
            suspension=Count(Case(When(severity="suspension", then=1))),
            expulsion=Count(Case(When(severity="expulsion", then=1))),
        )
        rows = []
        for c in campuses:
            rows.append({
                "campus": c["campus__name"] or "-",
                "total": c["total"],
                "warnings": c["warning"],
                "suspensions": c["suspension"],
                "expulsions": c["expulsion"],
            })
        return rows


class IncidentTypeReportView(AggregateReportView):
    """Incident type breakdown report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "discipline_type"
    model = "apps.discipline.models.DisciplineIncident"

    def get_base_queryset(self, request):
        from apps.discipline.models import DisciplineIncident
        return DisciplineIncident.objects.select_related("campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

    def get_summary(self, queryset, request):
        types = queryset.values("incident_type").annotate(
            count=Count("id"),
            warning=Count(Case(When(severity="warning", then=1))),
            suspension=Count(Case(When(severity="suspension", then=1))),
            expulsion=Count(Case(When(severity="expulsion", then=1))),
        )
        return {"total_types": types.count()}

    def get_detail_rows(self, queryset, request):
        types = queryset.values("incident_type").annotate(
            count=Count("id"),
            warning=Count(Case(When(severity="warning", then=1))),
            suspension=Count(Case(When(severity="suspension", then=1))),
            expulsion=Count(Case(When(severity="expulsion", then=1))),
        )
        rows = []
        for t in types:
            rows.append({
                "incident_type": t["incident_type"],
                "total": t["count"],
                "warnings": t["warning"],
                "suspensions": t["suspension"],
                "expulsions": t["expulsion"],
            })
        return rows


class DateRangeIncidentsReportView(AggregateReportView):
    """Date range incidents report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "discipline_date_range"
    model = "apps.discipline.models.DisciplineIncident"

    def get_base_queryset(self, request):
        from apps.discipline.models import DisciplineIncident
        return DisciplineIncident.objects.select_related("student", "campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(incident_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(incident_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        return {"total_incidents": queryset.count()}

    def get_detail_rows(self, queryset, request):
        rows = []
        for incident in queryset:
            rows.append({
                "date": incident.incident_date,
                "student": incident.student.full_name,
                "admission_number": incident.student.admission_number,
                "campus": incident.campus.name if incident.campus else "-",
                "incident_type": incident.get_incident_type_display(),
                "severity": incident.get_severity_display(),
            })
        return rows


class WarningReportView(AggregateReportView):
    """Warnings report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "discipline_warnings"
    model = "apps.discipline.models.DisciplineIncident"

    def get_base_queryset(self, request):
        from apps.discipline.models import DisciplineIncident
        return DisciplineIncident.objects.filter(severity="warning").select_related(
            "student", "campus", "reported_by"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(incident_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(incident_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        return {"total_warnings": queryset.count()}

    def get_detail_rows(self, queryset, request):
        rows = []
        for incident in queryset:
            rows.append({
                "date": incident.incident_date,
                "student": incident.student.full_name,
                "admission_number": incident.student.admission_number,
                "campus": incident.campus.name if incident.campus else "-",
                "incident_type": incident.get_incident_type_display(),
                "description": incident.description,
                "reported_by": incident.reported_by.get_full_name() if incident.reported_by else "-",
            })
        return rows


class SuspensionReportView(AggregateReportView):
    """Suspension report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "discipline_suspensions"
    model = "apps.discipline.models.DisciplineIncident"

    def get_base_queryset(self, request):
        from apps.discipline.models import DisciplineIncident
        return DisciplineIncident.objects.filter(severity="suspension").select_related(
            "student", "campus", "action_taken_by"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(incident_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(incident_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        return {"total_suspensions": queryset.count()}

    def get_detail_rows(self, queryset, request):
        rows = []
        for incident in queryset:
            rows.append({
                "date": incident.incident_date,
                "student": incident.student.full_name,
                "admission_number": incident.student.admission_number,
                "campus": incident.campus.name if incident.campus else "-",
                "incident_type": incident.get_incident_type_display(),
                "description": incident.description,
                "action_taken": incident.action_taken,
                "action_by": incident.action_taken_by.get_full_name() if incident.action_taken_by else "-",
            })
        return rows


class RepeatIncidentsReportView(AggregateReportView):
    """Students with repeat incidents."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "discipline_repeat"
    model = "apps.discipline.models.DisciplineIncident"

    def get_base_queryset(self, request):
        from apps.discipline.models import DisciplineIncident
        return DisciplineIncident.objects.select_related("student", "campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")
        return queryset

    def get_summary(self, queryset, request):
        students = {}
        for incident in queryset:
            sid = incident.student_id
            students[sid] = students.get(sid, 0) + 1

        repeat_count = sum(1 for c in students.values() if c > 1)
        max_incidents = max(students.values()) if students else 0

        return {
            "total_students": len(students),
            "repeat_offenders": repeat_count,
            "max_incidents": max_incidents,
        }

    def get_detail_rows(self, queryset, request):
        students = {}
        for incident in queryset:
            sid = incident.student_id
            if sid not in students:
                students[sid] = {"student": incident.student, "incidents": []}
            students[sid]["incidents"].append(incident)

        rows = []
        for data in students.values():
            if len(data["incidents"]) > 1:
                student = data["student"]
                for incident in data["incidents"]:
                    rows.append({
                        "admission_number": student.admission_number,
                        "student": student.full_name,
                        "campus": incident.campus.name if incident.campus else "-",
                        "date": incident.incident_date,
                        "incident_type": incident.get_incident_type_display(),
                        "severity": incident.get_severity_display(),
                    })
        return rows


class DisciplinaryHistoryReportView(BaseReportView):
    """Complete disciplinary history for a student."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "discipline_history"
    model = "apps.discipline.models.DisciplineIncident"

    def get_base_queryset(self, request):
        from apps.discipline.models import DisciplineIncident
        return DisciplineIncident.objects.select_related(
            "student", "campus", "reported_by", "action_taken_by"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        student_id = request.query_params.get("student")
        if not student_id:
            return queryset.none()
        queryset = queryset.filter(student_id=student_id)
        return queryset.order_by("-incident_date")

    def get(self, request):
        queryset = self.get_queryset(request)
        student_id = request.query_params.get("student")

        if not student_id:
            return Response({"detail": "Student ID required"}, status=400)

        from apps.students.models import Student
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found"}, status=404)

        rows = []
        for incident in queryset:
            rows.append({
                "date": incident.incident_date,
                "incident_type": incident.get_incident_type_display(),
                "severity": incident.get_severity_display(),
                "description": incident.description,
                "campus": incident.campus.name if incident.campus else "-",
                "status": incident.get_status_display(),
                "reported_by": incident.reported_by.get_full_name() if incident.reported_by else "-",
                "action_taken": incident.action_taken,
                "action_by": incident.action_taken_by.get_full_name() if incident.action_taken_by else "-",
            })

        return Response({
            "student": {
                "admission_number": student.admission_number,
                "name": student.full_name,
            },
            "incidents": rows,
            "total": len(rows),
        })