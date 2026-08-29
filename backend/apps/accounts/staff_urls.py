from django.urls import path

from .views import (
    StaffAttendanceCorrectionListView,
    StaffAttendanceCorrectionView,
    StaffAttendanceDetailView,
    StaffAttendanceListCreateView,
    StaffDetailView,
    StaffLeaveActionView,
    StaffLeaveDetailView,
    StaffLeaveListCreateView,
    StaffListCreateView,
    StaffMyView,
)


urlpatterns = [
    path(
        "",
        StaffListCreateView.as_view(),
        name="staff-list",
    ),
    path(
        "me/",
        StaffMyView.as_view(),
        name="staff-my",
    ),
    path(
        "attendance/",
        StaffAttendanceListCreateView.as_view(),
        name="staff-attendance-list",
    ),
    path(
        "attendance/<int:pk>/",
        StaffAttendanceDetailView.as_view(),
        name="staff-attendance-detail",
    ),
    path(
        "attendance/<int:pk>/correct/",
        StaffAttendanceCorrectionView.as_view(),
        name="staff-attendance-correct",
    ),
    path(
        "attendance/corrections/",
        StaffAttendanceCorrectionListView.as_view(),
        name="staff-attendance-corrections",
    ),
    path(
        "leave/",
        StaffLeaveListCreateView.as_view(),
        name="staff-leave-list",
    ),
    path(
        "leave/<int:pk>/",
        StaffLeaveDetailView.as_view(),
        name="staff-leave-detail",
    ),
    path(
        "leave/<int:pk>/action/",
        StaffLeaveActionView.as_view(),
        name="staff-leave-action",
    ),
    path(
        "<int:pk>/",
        StaffDetailView.as_view(),
        name="staff-detail",
    ),
]
