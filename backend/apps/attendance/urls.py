from django.urls import path

from apps.communication.cron_views import AbsenceAlertCronView

from .device_sync import BiometricSyncView
from .views import (
    AttendanceBulkMarkView,
    AttendanceCorrectionListView,
    AttendanceCorrectionView,
    AttendanceHistoryView,
    AttendanceListView,
    AttendanceMarkView,
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
        "mark/",
        AttendanceMarkView.as_view(),
        name="attendance-mark",
    ),
    path(
        "history/",
        AttendanceHistoryView.as_view(),
        name="attendance-history",
    ),
    path(
        "corrections/",
        AttendanceCorrectionListView.as_view(),
        name="attendance-corrections",
    ),
    path(
        "corrections/<int:pk>/",
        AttendanceCorrectionView.as_view(),
        name="attendance-correction",
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
