from django.urls import path

from .views import (
    StudentListCreateView,
    StudentDetailView,
    StudentMyView,
    EnrollmentListCreateView,
    EnrollmentDetailView,
)


urlpatterns = [
    path(
        "",
        StudentListCreateView.as_view(),
        name="student-list",
    ),

    path(
        "me/",
        StudentMyView.as_view(),
        name="student-my",
    ),

    path(
        "enrollments/",
        EnrollmentListCreateView.as_view(),
        name="enrollment-list",
    ),

    path(
        "enrollments/<int:pk>/",
        EnrollmentDetailView.as_view(),
        name="enrollment-detail",
    ),

    path(
        "<int:pk>/",
        StudentDetailView.as_view(),
        name="student-detail",
    ),
]