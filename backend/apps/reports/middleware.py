"""Audit logging middleware for report access tracking."""

import json
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings


class ReportAuditMiddleware(MiddlewareMixin):
    """Middleware to audit report access and exports."""

    # Paths to audit
    AUDIT_PATHS = [
        "/api/reports/",
    ]

    # Actions to audit based on method and params
    ACTION_MAP = {
        "GET": "view",
        "POST": "generate",
    }

    EXPORT_PARAMS = {
        "csv": "export_csv",
        "excel": "export_excel",
        "pdf": "export_pdf",
        "print": "print",
    }

    def process_response(self, request, response):
        # Check if this is a report API call
        if not any(request.path.startswith(path) for path in self.AUDIT_PATHS):
            return response

        # Skip if not authenticated
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return response

        # Determine action
        action = self.get_action(request, response)

        if not action:
            return response

        # Get report info from URL
        report_definition = self.get_report_definition(request)
        campus_id = self.get_campus_id(request)
        academic_year_id = self.get_academic_year_id(request)

        # Get filters from query params
        filters = self.get_filters(request)

        # Record count (if available in response)
        record_count = self.get_record_count(response)

        # File size for exports
        file_size = 0
        if action.startswith("export_") and hasattr(response, "content"):
            file_size = len(response.content)

        # Create audit log
        try:
            from apps.reports.models import ReportAuditLog
            ReportAuditLog.objects.create(
                user=request.user,
                report_definition=report_definition,
                action=action,
                campus_id=campus_id,
                campus_name=self.get_campus_name(campus_id),
                academic_year_id=academic_year_id,
                academic_year_name=self.get_academic_year_name(academic_year_id),
                filters_used=filters,
                record_count=record_count,
                file_size=file_size,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        except Exception:
            # Silently fail audit logging to not break the request
            pass

        return response

    def get_action(self, request, response):
        """Determine the action from request/response."""
        # Check for export format
        fmt = request.GET.get("format") or request.POST.get("format")
        if fmt in self.EXPORT_PARAMS:
            return self.EXPORT_PARAMS[fmt]

        # Check for print
        if request.GET.get("print") == "true":
            return "print"

        # Default to view
        return self.ACTION_MAP.get(request.method, "view")

    def get_report_definition(self, request):
        """Get report definition from URL."""
        from apps.reports.models import ReportDefinition

        # Try to match URL to report definition
        path = request.path
        for report in ReportDefinition.objects.filter(is_active=True):
            if report.endpoint_url and path.startswith(report.endpoint_url):
                return report

        return None

    def get_campus_id(self, request):
        """Get campus ID from request."""
        campus = request.GET.get("campus")
        if campus:
            try:
                return int(campus)
            except (ValueError, TypeError):
                pass
        return None

    def get_campus_name(self, campus_id):
        """Get campus name from ID."""
        if not campus_id:
            return ""
        try:
            from apps.schools.models import Campus
            campus = Campus.objects.filter(pk=campus_id).first()
            return campus.name if campus else ""
        except Exception:
            return ""

    def get_academic_year_id(self, request):
        """Get academic year ID from request."""
        ay = request.GET.get("academic_year")
        if ay:
            try:
                return int(ay)
            except (ValueError, TypeError):
                pass
        return None

    def get_academic_year_name(self, academic_year_id):
        """Get academic year name from ID."""
        if not academic_year_id:
            return ""
        try:
            from apps.schools.models import AcademicYear
            ay = AcademicYear.objects.filter(pk=academic_year_id).first()
            return ay.name if ay else ""
        except Exception:
            return ""

    def get_filters(self, request):
        """Extract filters from request."""
        filters = {}
        skip_params = ["format", "page", "page_size", "sort", "group_by", "columns", "print", "campus", "academic_year"]

        for key, value in request.GET.items():
            if key not in skip_params and value:
                filters[key] = value

        for key, value in request.POST.items():
            if key not in skip_params and value:
                filters[key] = value

        return filters

    def get_record_count(self, response):
        """Extract record count from response."""
        try:
            if hasattr(response, "data") and isinstance(response.data, dict):
                return response.data.get("count", 0) or len(response.data.get("results", []))
        except Exception:
            pass
        return 0

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")