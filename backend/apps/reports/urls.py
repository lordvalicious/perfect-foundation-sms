from django.urls import path

from .views import (
    AttendanceReportView,
    EnrollmentReportView,
    FeesReportView,
    ResultsReportView,
    StaffReportView,
)


urlpatterns = [
    path(
        "enrollment/",
        EnrollmentReportView.as_view(),
        name="report-enrollment",
    ),
    path(
        "attendance/",
        AttendanceReportView.as_view(),
        name="report-attendance",
    ),
    path(
        "results/",
        ResultsReportView.as_view(),
        name="report-results",
    ),
    path(
        "fees/",
        FeesReportView.as_view(),
        name="report-fees",
    ),
    path(
        "staff/",
        StaffReportView.as_view(),
        name="report-staff",
    ),
]
