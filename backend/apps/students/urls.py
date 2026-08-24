from django.urls import path

from .certificates import StudentCertificatePdfView
from .public_views import (
    PublicAdmissionApplyView,
    PublicAdmissionOptionsView,
)
from .transcripts import StudentTranscriptPdfView
from .views import (
    AdmissionApplicationAcceptView,
    AdmissionApplicationDetailView,
    AdmissionApplicationListCreateView,
    AdmissionApplicationReviewView,
    GuardianListCreateView,
    GuardianDetailView,
    GuardianMyView,
    StudentListCreateView,
    StudentDetailView,
    StudentGuardianListCreateView,
    StudentLifecycleActionView,
    StudentLifecycleListView,
    StudentLeaveRequestActionView,
    StudentLeaveRequestListCreateView,
    StudentMyView,
    StudentDocumentListCreateView,
    StudentDocumentDetailView,
    EnrollmentListCreateView,
    EnrollmentDetailView,
    PromotionView,
)


urlpatterns = [
    path(
        "admissions/",
        AdmissionApplicationListCreateView.as_view(),
        name="admission-list",
    ),
    path(
        "admissions/<int:pk>/",
        AdmissionApplicationDetailView.as_view(),
        name="admission-detail",
    ),
    path(
        "admissions/<int:pk>/review/",
        AdmissionApplicationReviewView.as_view(),
        name="admission-review",
    ),
    path(
        "admissions/<int:pk>/accept/",
        AdmissionApplicationAcceptView.as_view(),
        name="admission-accept",
    ),
    path(
        "admissions/public/options/",
        PublicAdmissionOptionsView.as_view(),
        name="public-admission-options",
    ),
    path(
        "admissions/public/apply/",
        PublicAdmissionApplyView.as_view(),
        name="public-admission-apply",
    ),
    path(
        "guardian-links/",
        StudentGuardianListCreateView.as_view(),
        name="student-guardian-list",
    ),
    path(
        "lifecycle/",
        StudentLifecycleListView.as_view(),
        name="student-lifecycle-list",
    ),
    path(
        "leave/",
        StudentLeaveRequestListCreateView.as_view(),
        name="student-leave-list",
    ),
    path(
        "leave/<int:pk>/action/",
        StudentLeaveRequestActionView.as_view(),
        name="student-leave-action",
    ),
    path(
        "promotions/",
        PromotionView.as_view(),
        name="student-promotion",
    ),
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
        "<int:pk>/certificate/<str:cert_type>/",
        StudentCertificatePdfView.as_view(),
        name="student-certificate",
    ),

    path(
        "<int:pk>/transcript.pdf",
        StudentTranscriptPdfView.as_view(),
        name="student-transcript",
    ),

    path(
        "enrollments/<int:pk>/",
        EnrollmentDetailView.as_view(),
        name="enrollment-detail",
    ),

    path(
        "<int:pk>/lifecycle/",
        StudentLifecycleActionView.as_view(),
        name="student-lifecycle-action",
    ),

    path(
        "<int:pk>/",
        StudentDetailView.as_view(),
        name="student-detail",
    ),
]
