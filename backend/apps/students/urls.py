from django.urls import path

from .views import (
    GuardianListCreateView,
    GuardianDetailView,
    GuardianMyView,
    StudentListCreateView,
    StudentDetailView,
    StudentMyView,
    StudentDocumentListCreateView,
    StudentDocumentDetailView,
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
        "guardians/",
        GuardianListCreateView.as_view(),
        name="guardian-list",
    ),

    path(
        "guardians/me/",
        GuardianMyView.as_view(),
        name="guardian-my",
    ),

    path(
        "guardians/<int:pk>/",
        GuardianDetailView.as_view(),
        name="guardian-detail",
    ),

    path(
        "documents/",
        StudentDocumentListCreateView.as_view(),
        name="document-list",
    ),

    path(
        "documents/<int:pk>/",
        StudentDocumentDetailView.as_view(),
        name="document-detail",
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
