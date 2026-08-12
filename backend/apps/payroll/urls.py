from django.urls import path

from .views import (
    PayrollProcessView,
    PayrollRecordDetailView,
    PayrollRecordListView,
    PayslipListView,
    SalaryStructureDetailView,
    SalaryStructureListView,
)


urlpatterns = [
    path(
        "salary-structures/",
        SalaryStructureListView.as_view(),
        name="salary-structure-list",
    ),
    path(
        "salary-structures/<int:pk>/",
        SalaryStructureDetailView.as_view(),
        name="salary-structure-detail",
    ),
    path(
        "records/",
        PayrollRecordListView.as_view(),
        name="payroll-record-list",
    ),
    path(
        "records/<int:pk>/",
        PayrollRecordDetailView.as_view(),
        name="payroll-record-detail",
    ),
    path(
        "records/<int:pk>/process/",
        PayrollProcessView.as_view(),
        name="payroll-process",
    ),
    path("payslips/", PayslipListView.as_view(), name="payslip-list"),
]
