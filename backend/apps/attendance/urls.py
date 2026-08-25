from django.urls import path

from apps.communication.cron_views import AbsenceAlertCronView

from .device_sync import BiometricSyncView
from .views import (
    AttendanceBulkMarkView,
    AttendanceListView,
    AttendanceMonthlyView,
    AttendanceSummaryView,
)


urlpatterns = [
    path("", AttendanceListView.as_view(), name="attendance-list"),
    path(
        "bulk/",
        AttendanceBulkMarkView.as_view(),
        name="attendance-bulk",
    ),
    path(
        "summary/",
        AttendanceSummaryView.as_view(),
        name="attendance-summary",
    ),
    path(
        "monthly/",
        AttendanceMonthlyView.as_view(),
        name="attendance-monthly",
    ),
    path(
        "device-sync/",
        BiometricSyncView.as_view(),
        name="attendance-device-sync",
    ),
    path(
        "cron/absence-alerts/",
        AbsenceAlertCronView.as_view(),
        name="absence-alert-cron",
    ),
]
