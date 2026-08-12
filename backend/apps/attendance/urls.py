from django.urls import path

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
]
