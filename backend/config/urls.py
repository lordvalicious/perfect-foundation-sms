from django.conf import settings  # type: ignore[reportMissingModuleSource]
from django.contrib import admin  # type: ignore[reportMissingModuleSource]
from django.http import JsonResponse
from django.urls import include, path, re_path  # type: ignore[reportMissingModuleSource]
from apps.core.views import run_migrations_view


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/health/", health_check, name="health-check"),
    path("api/admin/run-migrations/", run_migrations_view, name="run-migrations"),

    path(
        "api/auth/",
        include("apps.accounts.urls"),
    ),

    path(
        "api/staff/",
        include("apps.accounts.staff_urls"),
    ),

    path(
        "api/dashboard/",
        include("apps.dashboard.urls"),
    ),

    path(
        "api/students/",
        include("apps.students.urls"),
    ),

    path(
        "api/teachers/",
        include("apps.teachers.urls"),
    ),

    path(
        "api/attendance/",
        include("apps.attendance.urls"),
    ),

    path(
        "api/schools/",
        include("apps.schools.urls"),
    ),

    path(
        "api/finance/",
        include("apps.finance.urls"),
    ),

    path(
        "api/exams/",
        include("apps.exams.urls"),
    ),

    path(
        "api/report-cards/",
        include("apps.reportcards.urls"),
    ),

    path(
        "api/timetable/",
        include("apps.timetable.urls"),
    ),

    path(
        "api/events/",
        include("apps.events.urls"),
    ),

    path(
        "api/communication/",
        include("apps.communication.urls"),
    ),

    path(
        "api/audit/",
        include("apps.audit.urls"),
    ),

    path(
        "api/library/",
        include("apps.library.urls"),
    ),

    path(
        "api/transport/",
        include("apps.transport.urls"),
    ),

    path(
        "api/inventory/",
        include("apps.inventory.urls"),
    ),

    path(
        "api/payroll/",
        include("apps.payroll.urls"),
    ),

    path(
        "api/hr/",
        include("apps.hr.urls"),
    ),

    path(
        "api/reports/",
        include("apps.reports.urls"),
    ),

    path(
        "api/search/",
        include("apps.search.urls"),
    ),

    path(
        "api/documents/",
        include("apps.documents.urls"),
    ),

    path(
        "api/discipline/",
        include("apps.discipline.urls"),
    ),

    path(
        "api/homework/",
        include("apps.homework.urls"),
    ),

    path(
        "api/health-records/",
        include("apps.health.urls"),
    ),

    path(
        "api/alumni/",
        include("apps.alumni.urls"),
    ),

    path(
        "api/hostel/",
        include("apps.hostel.urls"),
    ),

    path(
        "api/lms/",
        include("apps.lms.urls"),
    ),

    path(
        "api/portal/",
        include("apps.portal.urls"),
    ),

    path(
        "api/workflow/",
        include("apps.workflow.urls"),
    ),

    path(
        "api/helpdesk/",
        include("apps.helpdesk.urls"),
    ),

    path(
        "api/visitors/",
        include("apps.visitors.urls"),
    ),

    path(
        "api/digital-ids/",
        include("apps.digital_ids.urls"),
    ),
]

# Protected media serving (replaces public static() serving)
from apps.schools.media_views import ProtectedMediaView, PublicBrandingMediaView  # noqa: E402

urlpatterns += [
    path(
        settings.MEDIA_URL.lstrip("/") + "school/branding/<path:file_path>",
        PublicBrandingMediaView.as_view(),
        name="public-branding-media",
    ),
    re_path(
        r"^" + settings.MEDIA_URL.lstrip("/") + "(?P<file_path>.+)$",
        ProtectedMediaView.as_view(),
        name="protected-media",
    ),
]
