from django.urls import path

from .views import (
    AttendanceReportView,
    EnrollmentReportView,
    FeeCategoryReportView,
    FeesReportView,
    PaymentMethodsReportView,
    ResultsReportView,
    StaffReportView,
    StudentStatusReportView,
    SubjectPerformanceReportView,
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
    path(
        "subjects/",
        SubjectPerformanceReportView.as_view(),
        name="report-subject-performance",
    ),
    path(
        "payments/",
        PaymentMethodsReportView.as_view(),
        name="report-payment-methods",
    ),
    path(
        "student-status/",
        StudentStatusReportView.as_view(),
        name="report-student-status",
    ),
    path(
        "fee-categories/",
        FeeCategoryReportView.as_view(),
        name="report-fee-categories",
    ),
]
