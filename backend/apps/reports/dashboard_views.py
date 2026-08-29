"""Reports Dashboard with Charts and Analytics."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.utils import timezone
from datetime import date, timedelta
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.models import ReportAuditLog, SavedReport
from apps.reports.utils import quantize


class ReportsDashboardView(APIView):
    """Main reports dashboard with key metrics and charts."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def get(self, request):
        # Get time range
        days = int(request.query_params.get("days", 30))
        date_from = timezone.now().date() - timedelta(days=days)
        date_to = timezone.now().date()

        # Get campus scope
        from apps.accounts.access import user_allowed_campus_ids
        allowed_campuses = user_allowed_campus_ids(request.user)

        # Build dashboard data
        dashboard = {
            "overview": self.get_overview_metrics(request, date_from, date_to, allowed_campuses),
            "charts": self.get_charts(request, date_from, date_to, allowed_campuses),
            "recent_reports": self.get_recent_reports(request),
            "favorites": self.get_favorites(request),
        }

        return Response(dashboard)

    def get_overview_metrics(self, request, date_from, date_to, allowed_campuses):
        """Get overview metric cards."""
        from apps.students.models import Student, Enrollment
        from apps.attendance.models import Attendance
        from apps.finance.models import Invoice, Payment
        from apps.reportcards.models import ReportCard
        from apps.accounts.models import StaffProfile
        from apps.schools.models import Campus

        # Total students
        students = Student.objects.filter(status="active")
        if not request.user.has_role("super_admin") and not request.user.has_role("admin"):
            students = students.filter(primary_campus_id__in=allowed_campuses)
        total_students = students.count()

        # Attendance rate (current month)
        current_month_start = timezone.now().date().replace(day=1)
        attendance = Attendance.objects.filter(date__gte=current_month_start)
        if allowed_campuses:
            attendance = attendance.filter(campus_id__in=allowed_campuses)
        att_total = attendance.count()
        att_present = attendance.filter(status__in=["present", "late"]).count()
        attendance_rate = round(att_present / att_total * 100, 1) if att_total else 0

        # Fee collection (current academic year)
        from apps.schools.models import AcademicYear
        current_year = AcademicYear.objects.filter(status="active").first()
        invoices = Invoice.objects.all()
        if current_year:
            invoices = invoices.filter(academic_year=current_year)
        if allowed_campuses:
            invoices = invoices.filter(enrollment__campus_id__in=allowed_campuses)
        total_invoiced = sum(inv.total_amount for inv in invoices)
        total_collected = sum(inv.paid_amount for inv in invoices)
        total_outstanding = sum(inv.balance for inv in invoices)
        collection_rate = round(float(total_collected) / float(total_invoiced) * 100, 1) if total_invoiced else 0

        # Admissions (last 30 days)
        from apps.students.models import AdmissionApplication
        admissions = AdmissionApplication.objects.filter(
            submitted_at__date__gte=date_from,
            status="accepted"
        )
        if allowed_campuses:
            admissions = admissions.filter(campus_id__in=allowed_campuses)
        new_admissions = admissions.count()

        # Academic performance (latest exam)
        latest_exam = ReportCard.objects.order_by("-exam__start_date").first()
        pass_rate = 0
        if latest_exam:
            rcs = ReportCard.objects.filter(exam=latest_exam)
            if allowed_campuses:
                rcs = rcs.filter(exam__campus_id__in=allowed_campuses)
            passed = rcs.filter(overall_result="Pass").count()
            total = rcs.count()
            pass_rate = round(passed / total * 100, 1) if total else 0

        # Staff count
        staff = StaffProfile.objects.filter(status="active")
        if allowed_campuses:
            staff = staff.filter(primary_campus_id__in=allowed_campuses)
        total_staff = staff.count()

        # Campus count
        campuses = Campus.objects.filter(status="active")
        if allowed_campuses:
            campuses = campuses.filter(id__in=allowed_campuses)
        campus_count = campuses.count()

        return {
            "total_students": total_students,
            "attendance_rate": attendance_rate,
            "total_invoiced": quantize(total_invoiced),
            "total_collected": quantize(total_collected),
            "total_outstanding": quantize(total_outstanding),
            "collection_rate": collection_rate,
            "new_admissions": new_admissions,
            "pass_rate": pass_rate,
            "total_staff": total_staff,
            "campus_count": campus_count,
        }

    def get_charts(self, request, date_from, date_to, allowed_campuses):
        """Get chart data for dashboard."""
        charts = {}

        # Student growth trend
        charts["student_growth"] = self.get_student_growth_chart(request, date_from, date_to, allowed_campuses)

        # Attendance trend
        charts["attendance_trend"] = self.get_attendance_trend_chart(request, date_from, date_to, allowed_campuses)

        # Fee collection trend
        charts["fee_collection_trend"] = self.get_fee_collection_chart(request, date_from, date_to, allowed_campuses)

        # Admission trend
        charts["admission_trend"] = self.get_admission_trend_chart(request, date_from, date_to, allowed_campuses)

        # Academic performance
        charts["academic_performance"] = self.get_academic_performance_chart(request, allowed_campuses)

        # Gender distribution
        charts["gender_distribution"] = self.get_gender_distribution_chart(request, allowed_campuses)

        # Campus comparison
        charts["campus_comparison"] = self.get_campus_comparison_chart(request, allowed_campuses)

        # Class strength
        charts["class_strength"] = self.get_class_strength_chart(request, allowed_campuses)

        return charts

    def get_student_growth_chart(self, request, date_from, date_to, allowed_campuses):
        """Student enrollment growth over time."""
        from apps.students.models import Student

        students = Student.objects.filter(admission_date__gte=date_from, admission_date__lte=date_to)
        if allowed_campuses:
            students = students.filter(primary_campus_id__in=allowed_campuses)

        # Group by month
        monthly = students.annotate(month=TruncMonth("admission_date")).values("month").annotate(
            count=Count("id")
        ).order_by("month")

        labels = []
        data = []
        for m in monthly:
            labels.append(m["month"].strftime("%b %Y"))
            data.append(m["count"])

        return {
            "type": "line",
            "title": "Student Growth",
            "labels": labels,
            "datasets": [{
                "label": "New Students",
                "data": data,
                "borderColor": "#1a73e8",
                "backgroundColor": "rgba(26, 115, 232, 0.1)",
                "fill": True,
            }],
        }

    def get_attendance_trend_chart(self, request, date_from, date_to, allowed_campuses):
        """Attendance rate trend over time."""
        from apps.attendance.models import Attendance

        attendance = Attendance.objects.filter(date__gte=date_from, date__lte=date_to)
        if allowed_campuses:
            attendance = attendance.filter(campus_id__in=allowed_campuses)

        monthly = attendance.annotate(month=TruncMonth("date")).values("month").annotate(
            total=Count("id"),
            present=Count(Case(When(status__in=["present", "late"], then=1))),
        ).order_by("month")

        labels = []
        rates = []
        for m in monthly:
            labels.append(m["month"].strftime("%b %Y"))
            rate = round(m["present"] / m["total"] * 100, 1) if m["total"] else 0
            rates.append(rate)

        return {
            "type": "line",
            "title": "Attendance Trend",
            "labels": labels,
            "datasets": [{
                "label": "Attendance Rate (%)",
                "data": rates,
                "borderColor": "#34a853",
                "backgroundColor": "rgba(52, 168, 83, 0.1)",
                "fill": True,
            }],
        }

    def get_fee_collection_chart(self, request, date_from, date_to, allowed_campuses):
        """Fee collection trend."""
        from apps.finance.models import Invoice

        invoices = Invoice.objects.filter(issue_date__gte=date_from, issue_date__lte=date_to)
        if allowed_campuses:
            invoices = invoices.filter(enrollment__campus_id__in=allowed_campuses)

        monthly = invoices.annotate(month=TruncMonth("issue_date")).values("month").annotate(
            invoiced=Sum("total_amount"),
            collected=Sum("paid_amount"),
        ).order_by("month")

        labels = []
        invoiced_data = []
        collected_data = []
        for m in monthly:
            labels.append(m["month"].strftime("%b %Y"))
            invoiced_data.append(float(m["invoiced"] or 0))
            collected_data.append(float(m["collected"] or 0))

        return {
            "type": "bar",
            "title": "Fee Collection Trend",
            "labels": labels,
            "datasets": [
                {
                    "label": "Invoiced",
                    "data": invoiced_data,
                    "backgroundColor": "#1a73e8",
                },
                {
                    "label": "Collected",
                    "data": collected_data,
                    "backgroundColor": "#34a853",
                },
            ],
        }

    def get_admission_trend_chart(self, request, date_from, date_to, allowed_campuses):
        """Admission applications trend."""
        from apps.students.models import AdmissionApplication

        apps = AdmissionApplication.objects.filter(submitted_at__date__gte=date_from, submitted_at__date__lte=date_to)
        if allowed_campuses:
            apps = apps.filter(campus_id__in=allowed_campuses)

        monthly = apps.annotate(month=TruncMonth("submitted_at")).values("month").annotate(
            total=Count("id"),
            accepted=Count(Case(When(status="accepted", then=1))),
        ).order_by("month")

        labels = []
        total_data = []
        accepted_data = []
        for m in monthly:
            labels.append(m["month"].strftime("%b %Y"))
            total_data.append(m["total"])
            accepted_data.append(m["accepted"])

        return {
            "type": "bar",
            "title": "Admissions Trend",
            "labels": labels,
            "datasets": [
                {
                    "label": "Applications",
                    "data": total_data,
                    "backgroundColor": "#fbbc04",
                },
                {
                    "label": "Accepted",
                    "data": accepted_data,
                    "backgroundColor": "#34a853",
                },
            ],
        }

    def get_academic_performance_chart(self, request, allowed_campuses):
        """Academic performance by exam."""
        from apps.reportcards.models import ReportCard

        exams = ReportCard.objects.values("exam__name", "exam__exam_type").annotate(
            total=Count("id"),
            passed=Count(Case(When(overall_result="Pass", then=1))),
            avg_pct=Avg("percentage"),
        ).order_by("-exam__start_date")[:10]

        labels = []
        pass_rates = []
        avg_data = []
        for e in exams:
            labels.append(f"{e['exam__name']} ({e['exam__exam_type']})")
            total = e["total"]
            passed = e["passed"]
            pass_rates.append(round(passed / total * 100, 1) if total else 0)
            avg_data.append(round(e["avg_pct"], 1) if e["avg_pct"] else 0)

        return {
            "type": "bar",
            "title": "Exam Performance",
            "labels": labels[::-1],  # Reverse to show oldest first
            "datasets": [
                {
                    "label": "Pass Rate (%)",
                    "data": pass_rates[::-1],
                    "backgroundColor": "#34a853",
                    "yAxisID": "y",
                },
                {
                    "label": "Avg Percentage",
                    "data": avg_data[::-1],
                    "backgroundColor": "#1a73e8",
                    "yAxisID": "y1",
                    "type": "line",
                },
            ],
        }

    def get_gender_distribution_chart(self, request, allowed_campuses):
        """Gender distribution."""
        from apps.students.models import Student

        students = Student.objects.filter(status="active")
        if allowed_campuses:
            students = students.filter(primary_campus_id__in=allowed_campuses)

        male = students.filter(gender="male").count()
        female = students.filter(gender="female").count()

        return {
            "type": "doughnut",
            "title": "Gender Distribution",
            "labels": ["Male", "Female"],
            "datasets": [{
                "data": [male, female],
                "backgroundColor": ["#1a73e8", "#ea4335"],
            }],
        }

    def get_campus_comparison_chart(self, request, allowed_campuses):
        """Campus comparison - students, attendance, fees."""
        from apps.schools.models import Campus
        from apps.students.models import Student
        from apps.attendance.models import Attendance
        from apps.finance.models import Invoice

        campuses = Campus.objects.filter(status="active")
        if allowed_campuses:
            campuses = campuses.filter(id__in=allowed_campuses)

        campus_names = []
        students_data = []
        attendance_data = []
        fees_data = []

        for campus in campuses:
            campus_names.append(campus.name)

            # Students
            students_data.append(Student.objects.filter(primary_campus=campus, status="active").count())

            # Attendance (current month)
            month_start = timezone.now().date().replace(day=1)
            att = Attendance.objects.filter(campus=campus, date__gte=month_start)
            att_total = att.count()
            att_present = att.filter(status__in=["present", "late"]).count()
            attendance_data.append(round(att_present / att_total * 100, 1) if att_total else 0)

            # Fees (current year)
            from apps.schools.models import AcademicYear
            current_year = AcademicYear.objects.filter(status="active").first()
            inv = Invoice.objects.filter(enrollment__campus=campus)
            if current_year:
                inv = inv.filter(academic_year=current_year)
            total_inv = sum(i.total_amount for i in inv)
            total_coll = sum(i.paid_amount for i in inv)
            fees_data.append(round(float(total_coll) / float(total_inv) * 100, 1) if total_inv else 0)

        return {
            "type": "radar",
            "title": "Campus Comparison",
            "labels": ["Students", "Attendance %", "Fee Collection %", "Staff"],
            "datasets": [
                {
                    "label": campus_names[i],
                    "data": [students_data[i], attendance_data[i], fees_data[i], 0],  # Staff would need separate query
                    "backgroundColor": f"rgba({26 + i * 50}, {115 + i * 30}, {232 - i * 40}, 0.2)",
                    "borderColor": f"rgba({26 + i * 50}, {115 + i * 30}, {232 - i * 40}, 1)",
                }
                for i in range(len(campus_names))
            ],
        }

    def get_class_strength_chart(self, request, allowed_campuses):
        """Class strength distribution."""
        from apps.students.models import Enrollment

        enrollments = Enrollment.objects.filter(status="active")
        if allowed_campuses:
            enrollments = enrollments.filter(campus_id__in=allowed_campuses)

        class_strength = enrollments.values("class_obj__name").annotate(
            count=Count("id")
        ).order_by("class_obj__level")[:15]

        labels = [c["class_obj__name"] for c in class_strength]
        data = [c["count"] for c in class_strength]

        return {
            "type": "horizontalBar",
            "title": "Class Strength",
            "labels": labels,
            "datasets": [{
                "label": "Students",
                "data": data,
                "backgroundColor": "#1a73e8",
            }],
        }

    def get_recent_reports(self, request):
        """Get recently accessed reports."""
        from apps.reports.models import ReportAuditLog

        logs = ReportAuditLog.objects.filter(user=request.user).order_by("-created_at")[:10]

        seen = set()
        recent = []
        for log in logs:
            key = log.report_definition_id
            if key and key not in seen:
                seen.add(key)
                recent.append({
                    "report_id": key,
                    "title": log.report_definition.title if log.report_definition else "Custom Report",
                    "action": log.action,
                    "created_at": log.created_at.isoformat(),
                })

        return recent[:5]

    def get_favorites(self, request):
        """Get favorite reports."""
        favorites = SavedReport.objects.filter(
            created_by=request.user, is_favorite=True
        ).select_related("report_definition")[:5]

        return [
            {
                "id": f.id,
                "name": f.name,
                "report_definition": {
                    "key": f.report_definition.key,
                    "title": f.report_definition.title,
                } if f.report_definition else None,
            }
            for f in favorites
        ]


class ReportAnalyticsView(APIView):
    """Advanced analytics for a specific report."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def get(self, request, report_key):
        from apps.reports.models import ReportDefinition, ReportAuditLog

        try:
            report = ReportDefinition.objects.get(key=report_key, is_active=True)
        except ReportDefinition.DoesNotExist:
            return Response({"detail": "Report not found"}, status=404)

        # Get audit logs for this report
        logs = ReportAuditLog.objects.filter(report_definition=report)

        # Time range
        days = int(request.query_params.get("days", 30))
        date_from = timezone.now().date() - timedelta(days=days)
        logs = logs.filter(created_at__date__gte=date_from)

        # Usage stats
        total_views = logs.filter(action="view").count()
        total_exports = logs.filter(action__in=["export_csv", "export_pdf", "export_excel"]).count()
        total_prints = logs.filter(action="print").count()

        # Unique users
        unique_users = logs.values("user").distinct().count()

        # Daily usage
        daily = logs.annotate(day=TruncDay("created_at")).values("day").annotate(
            views=Count(Case(When(action="view", then=1))),
            exports=Count(Case(When(action__in=["export_csv", "export_pdf", "export_excel"], then=1))),
        ).order_by("day")

        # Top users
        top_users = logs.values("user__username").annotate(
            count=Count("id")
        ).order_by("-count")[:5]

        # Export formats
        export_formats = logs.filter(action__startswith="export").values("action").annotate(
            count=Count("id")
        )

        return Response({
            "report": {
                "key": report.key,
                "title": report.title,
            },
            "summary": {
                "total_views": total_views,
                "total_exports": total_exports,
                "total_prints": total_prints,
                "unique_users": unique_users,
            },
            "daily_usage": list(daily),
            "top_users": list(top_users),
            "export_formats": list(export_formats),
        })


class DrillDownView(APIView):
    """Handle drill-down navigation from summary to detail."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def get(self, request):
        source_report = request.query_params.get("source_report")
        drill_field = request.query_params.get("field")
        drill_value = request.query_params.get("value")

        if not all([source_report, drill_field, drill_value]):
            return Response({"detail": "Missing required parameters"}, status=400)

        from apps.reports.models import ReportDefinition
        try:
            report = ReportDefinition.objects.get(key=source_report, is_active=True)
        except ReportDefinition.DoesNotExist:
            return Response({"detail": "Source report not found"}, status=404)

        if not report.supports_drilldown:
            return Response({"detail": "This report does not support drill-down"}, status=400)

        target = report.drilldown_target
        if not target:
            return Response({"detail": "No drill-down target configured"}, status=400)

        # Redirect to target report with appropriate filters
        from django.urls import reverse
        try:
            target_report = ReportDefinition.objects.get(key=target, is_active=True)
            url = target_report.endpoint_url
        except ReportDefinition.DoesNotExist:
            return Response({"detail": "Drill-down target not found"}, status=404)

        # Build filter params
        filter_param = f"{drill_field}={drill_value}"
        return Response({
            "drilldown_url": f"{url}?{filter_param}",
            "target_report": target_report.title,
            "filter": {drill_field: drill_value},
        })


class SavedReportAnalyticsView(APIView):
    """Analytics for saved reports."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def get(self, request):
        from apps.reports.models import SavedReport, ReportAuditLog

        reports = SavedReport.objects.filter(created_by=request.user).select_related("report_definition")

        data = []
        for report in reports:
            logs = ReportAuditLog.objects.filter(saved_report=report)

            total_runs = logs.count()
            last_run = logs.order_by("-created_at").first()
            exports = logs.filter(action__startswith="export").count()

            data.append({
                "id": report.id,
                "name": report.name,
                "report_definition": report.report_definition.title if report.report_definition else "Custom",
                "run_count": report.run_count,
                "total_audit_runs": total_runs,
                "exports": exports,
                "last_run_at": last_run.created_at.isoformat() if last_run else None,
                "is_favorite": report.is_favorite,
            })

        return Response(data)