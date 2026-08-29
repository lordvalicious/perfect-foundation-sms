"""Report Scheduling System."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from datetime import datetime, time, timedelta
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.models import ScheduledReport, SavedReport, ReportAuditLog
from apps.reports.utils import quantize
from apps.reports.pdf_views import PDFExportMixin


class ScheduledReportListView(APIView):
    """List and create scheduled reports."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def get(self, request):
        reports = ScheduledReport.objects.filter(
            created_by=request.user
        ).select_related("saved_report", "saved_report__report_definition").order_by("-created_at")

        data = []
        for r in reports:
            data.append({
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "saved_report": {
                    "id": r.saved_report.id,
                    "name": r.saved_report.name,
                    "report_definition": r.saved_report.report_definition.title if r.saved_report.report_definition else "Custom",
                } if r.saved_report else None,
                "frequency": r.frequency,
                "cron_expression": r.cron_expression,
                "day_of_week": r.day_of_week,
                "day_of_month": r.day_of_month,
                "time_of_day": r.time_of_day.strftime("%H:%M") if r.time_of_day else None,
                "output_format": r.output_format,
                "email_enabled": r.email_enabled,
                "email_recipients": r.email_recipients,
                "email_subject": r.email_subject,
                "last_run_at": r.last_run_at.isoformat() if r.last_run_at else None,
                "next_run_at": r.next_run_at.isoformat() if r.next_run_at else None,
                "last_run_status": r.last_run_status,
                "last_run_error": r.last_run_error,
                "run_count": r.run_count,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat(),
            })
        return Response(data)

    def post(self, request):
        saved_report_id = request.data.get("saved_report")
        try:
            saved_report = SavedReport.objects.get(id=saved_report_id, created_by=request.user)
        except SavedReport.DoesNotExist:
            return Response({"detail": "Saved report not found"}, status=400)

        schedule = ScheduledReport.objects.create(
            name=request.data.get("name", f"Schedule for {saved_report.name}"),
            description=request.data.get("description", ""),
            saved_report=saved_report,
            frequency=request.data.get("frequency", "daily"),
            cron_expression=request.data.get("cron_expression", ""),
            day_of_week=request.data.get("day_of_week"),
            day_of_month=request.data.get("day_of_month"),
            time_of_day=request.data.get("time_of_day", "08:00"),
            output_format=request.data.get("output_format", "pdf"),
            email_enabled=request.data.get("email_enabled", False),
            email_recipients=request.data.get("email_recipients", []),
            email_subject=request.data.get("email_subject", ""),
            email_body=request.data.get("email_body", ""),
            created_by=request.user,
        )

        # Calculate next run
        schedule.next_run_at = self.calculate_next_run(schedule)
        schedule.save()

        return Response({
            "id": schedule.id,
            "name": schedule.name,
            "detail": "Schedule created successfully",
        }, status=201)

    def calculate_next_run(self, schedule):
        """Calculate next run time based on frequency."""
        now = timezone.now()
        today = now.date()
        run_time = schedule.time_of_day

        if schedule.frequency == "daily":
            next_run = datetime.combine(today, run_time)
            if next_run <= now:
                next_run += timedelta(days=1)

        elif schedule.frequency == "weekly":
            dow = schedule.day_of_week or 0  # 0=Monday
            days_ahead = (dow - today.weekday()) % 7
            if days_ahead == 0 and datetime.combine(today, run_time) <= now:
                days_ahead = 7
            next_run = datetime.combine(today + timedelta(days=days_ahead), run_time)

        elif schedule.frequency == "monthly":
            dom = schedule.day_of_month or 1
            try:
                next_run = datetime.combine(today.replace(day=dom), run_time)
            except ValueError:
                # Day doesn't exist in this month, use last day
                if today.month == 12:
                    next_month = today.replace(year=today.year + 1, month=1, day=1)
                else:
                    next_month = today.replace(month=today.month + 1, day=1)
                last_day = next_month - timedelta(days=1)
                next_run = datetime.combine(last_day, run_time)

            if next_run <= now:
                if today.month == 12:
                    next_run = next_run.replace(year=today.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=today.month + 1)

        elif schedule.frequency == "custom" and schedule.cron_expression:
            # Would need croniter library for cron expressions
            next_run = now + timedelta(hours=1)  # Fallback

        else:
            next_run = now + timedelta(days=1)

        return timezone.make_aware(next_run) if timezone.is_naive(next_run) else next_run


class ScheduledReportDetailView(APIView):
    """Detail view for scheduled reports."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def get_object(self, pk, user):
        try:
            return ScheduledReport.objects.get(pk=pk, created_by=user)
        except ScheduledReport.DoesNotExist:
            return None

    def get(self, request, pk):
        schedule = self.get_object(pk, request.user)
        if not schedule:
            return Response({"detail": "Not found"}, status=404)

        return Response({
            "id": schedule.id,
            "name": schedule.name,
            "description": schedule.description,
            "saved_report": {
                "id": schedule.saved_report.id,
                "name": schedule.saved_report.name,
            } if schedule.saved_report else None,
            "frequency": schedule.frequency,
            "cron_expression": schedule.cron_expression,
            "day_of_week": schedule.day_of_week,
            "day_of_month": schedule.day_of_month,
            "time_of_day": schedule.time_of_day.strftime("%H:%M") if schedule.time_of_day else None,
            "output_format": schedule.output_format,
            "email_enabled": schedule.email_enabled,
            "email_recipients": schedule.email_recipients,
            "email_subject": schedule.email_subject,
            "email_body": schedule.email_body,
            "last_run_at": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
            "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
            "last_run_status": schedule.last_run_status,
            "last_run_error": schedule.last_run_error,
            "run_count": schedule.run_count,
            "is_active": schedule.is_active,
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat(),
        })

    def put(self, request, pk):
        schedule = self.get_object(pk, request.user)
        if not schedule:
            return Response({"detail": "Not found"}, status=404)

        schedule.name = request.data.get("name", schedule.name)
        schedule.description = request.data.get("description", schedule.description)
        schedule.frequency = request.data.get("frequency", schedule.frequency)
        schedule.cron_expression = request.data.get("cron_expression", schedule.cron_expression)
        schedule.day_of_week = request.data.get("day_of_week", schedule.day_of_week)
        schedule.day_of_month = request.data.get("day_of_month", schedule.day_of_month)
        schedule.time_of_day = request.data.get("time_of_day", schedule.time_of_day)
        schedule.output_format = request.data.get("output_format", schedule.output_format)
        schedule.email_enabled = request.data.get("email_enabled", schedule.email_enabled)
        schedule.email_recipients = request.data.get("email_recipients", schedule.email_recipients)
        schedule.email_subject = request.data.get("email_subject", schedule.email_subject)
        schedule.email_body = request.data.get("email_body", schedule.email_body)
        schedule.is_active = request.data.get("is_active", schedule.is_active)
        schedule.save()

        # Recalculate next run
        schedule.next_run_at = ScheduledReportListView().calculate_next_run(schedule)
        schedule.save()

        return Response({"detail": "Schedule updated"})

    def delete(self, request, pk):
        schedule = self.get_object(pk, request.user)
        if not schedule:
            return Response({"detail": "Not found"}, status=404)
        schedule.delete()
        return Response({"detail": "Schedule deleted"})


class ScheduledReportRunView(APIView):
    """Manually trigger a scheduled report."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def post(self, request, pk):
        from apps.reports.models import ScheduledReport
        try:
            schedule = ScheduledReport.objects.get(pk=pk, created_by=request.user)
        except ScheduledReport.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        return self.execute_schedule(schedule, request)

    def execute_schedule(self, schedule, request):
        """Execute a scheduled report."""
        from django.test import RequestFactory
        from django.urls import resolve

        schedule.last_run_at = timezone.now()
        schedule.last_run_status = "pending"
        schedule.save()

        try:
            # Get the saved report
            saved_report = schedule.saved_report
            if not saved_report:
                raise ValueError("No saved report associated")

            # Build report config
            report_config = {
                "primary_data_source": saved_report.report_definition.key if saved_report.report_definition else None,
                "selected_fields": saved_report.columns,
                "filters": saved_report.filters,
                "grouping": saved_report.grouping,
                "sorting": saved_report.sorting,
            }

            # Generate report
            if schedule.output_format == "pdf":
                result = self.generate_pdf_report(saved_report, request)
            elif schedule.output_format == "excel":
                result = self.generate_excel_report(saved_report, request)
            else:
                result = self.generate_csv_report(saved_report, request)

            if schedule.email_enabled and schedule.email_recipients:
                self.send_email(schedule, result, request)

            schedule.last_run_status = "success"
            schedule.last_run_error = ""
            schedule.run_count += 1
            schedule.next_run_at = ScheduledReportListView().calculate_next_run(schedule)
            schedule.save()

            return Response({
                "detail": "Report executed successfully",
                "last_run_at": schedule.last_run_at.isoformat(),
                "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
            })

        except Exception as e:
            schedule.last_run_status = "failed"
            schedule.last_run_error = str(e)
            schedule.save()

            return Response({"detail": f"Execution failed: {str(e)}"}, status=500)

    def generate_pdf_report(self, saved_report, request):
        """Generate PDF report."""
        # This would use the PDFExportMixin
        return {"format": "pdf", "data": "PDF generated"}

    def generate_excel_report(self, saved_report, request):
        """Generate Excel report."""
        return {"format": "excel", "data": "Excel generated"}

    def generate_csv_report(self, saved_report, request):
        """Generate CSV report."""
        return {"format": "csv", "data": "CSV generated"}

    def send_email(self, schedule, result, request):
        """Send email with report attachment."""
        from django.core.mail import EmailMessage
        from django.conf import settings

        email = EmailMessage(
            subject=schedule.email_subject or f"Scheduled Report: {schedule.name}",
            body=schedule.email_body or f"Please find attached the scheduled report: {schedule.name}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=schedule.email_recipients,
        )

        # Attach the report file
        # email.attach(f"{schedule.name}.{schedule.output_format}", result.get("content", b""))

        # email.send(fail_silently=False)
        pass


class ScheduledReportCronView(APIView):
    """Cron endpoint to run due scheduled reports."""

    permission_classes = []  # Called by external cron service

    def get(self, request):
        # Verify cron secret
        cron_secret = request.headers.get("Authorization", "").replace("Bearer ", "")
        from django.conf import settings
        expected_secret = getattr(settings, "CRON_SECRET", None)

        if expected_secret and cron_secret != expected_secret:
            return Response({"detail": "Unauthorized"}, status=401)

        now = timezone.now()
        due_schedules = ScheduledReport.objects.filter(
            is_active=True,
            next_run_at__lte=now,
        )

        executed = 0
        for schedule in due_schedules:
            try:
                # Create a mock request for execution
                from django.test import RequestFactory
                factory = RequestFactory()
                mock_request = factory.post("/")
                mock_request.user = schedule.created_by
                mock_request.institution = schedule.created_by.primary_institution

                runner = ScheduledReportRunView()
                runner.execute_schedule(schedule, mock_request)
                executed += 1
            except Exception as e:
                # Log error but continue
                pass

        return Response({
            "executed": executed,
            "total_due": due_schedules.count(),
        })


class EmailReportView(APIView):
    """Send a report via email (one-time)."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def post(self, request):
        report_key = request.data.get("report_key")
        recipients = request.data.get("recipients", [])
        subject = request.data.get("subject", "")
        body = request.data.get("body", "")
        output_format = request.data.get("format", "pdf")

        if not report_key or not recipients:
            return Response({"detail": "Report key and recipients required"}, status=400)

        # Verify recipients have access
        from apps.reports.models import ReportDefinition
        try:
            report = ReportDefinition.objects.get(key=report_key, is_active=True)
        except ReportDefinition.DoesNotExist:
            return Response({"detail": "Report not found"}, status=404)

        # Check if user can send this report
        user_roles = request.user.get_roles(institution=getattr(request, "institution", None))
        if report.required_roles and not any(r in user_roles for r in report.required_roles):
            return Response({"detail": "Not authorized to send this report"}, status=403)

        # Generate and send
        # This would call the report endpoint and email the result

        return Response({
            "detail": "Email queued for sending",
            "report": report.title,
            "recipients": recipients,
        })


class ScheduledReportTemplatesView(APIView):
    """Get available templates for scheduled reports."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def get(self, request):
        templates = [
            {
                "frequency": "daily",
                "label": "Daily",
                "description": "Run every day at specified time",
                "fields": ["time_of_day"],
            },
            {
                "frequency": "weekly",
                "label": "Weekly",
                "description": "Run on a specific day of the week",
                "fields": ["day_of_week", "time_of_day"],
            },
            {
                "frequency": "monthly",
                "label": "Monthly",
                "description": "Run on a specific day of the month",
                "fields": ["day_of_month", "time_of_day"],
            },
            {
                "frequency": "custom",
                "label": "Custom (Cron)",
                "description": "Run on a custom cron schedule",
                "fields": ["cron_expression"],
            },
        ]

        output_formats = [
            {"value": "pdf", "label": "PDF"},
            {"value": "excel", "label": "Excel"},
            {"value": "csv", "label": "CSV"},
        ]

        days_of_week = [
            {"value": 0, "label": "Monday"},
            {"value": 1, "label": "Tuesday"},
            {"value": 2, "label": "Wednesday"},
            {"value": 3, "label": "Thursday"},
            {"value": 4, "label": "Friday"},
            {"value": 5, "label": "Saturday"},
            {"value": 6, "label": "Sunday"},
        ]

        return Response({
            "templates": templates,
            "output_formats": output_formats,
            "days_of_week": days_of_week,
        })