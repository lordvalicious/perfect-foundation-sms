from django.urls import path

from .views import (
    EmployeeContractListCreateView,
    EmployeeDetailView,
    EmployeeDocumentListCreateView,
    EmployeeListView,
    EmployeeReviewListCreateView,
    EmployeeWorkloadListCreateView,
    EmploymentEventCreateView,
    EmploymentEventListView,
)

urlpatterns = [
    path("employees/", EmployeeListView.as_view(), name="employee-list"),
    path("employees/<int:pk>/", EmployeeDetailView.as_view(), name="employee-detail"),
    path("employees/<int:employee_id>/contracts/", EmployeeContractListCreateView.as_view(), name="employee-contract-list"),
    path("employees/<int:employee_id>/documents/", EmployeeDocumentListCreateView.as_view(), name="employee-document-list"),
    path("employees/<int:employee_id>/workload/", EmployeeWorkloadListCreateView.as_view(), name="employee-workload-list"),
    path("employees/<int:employee_id>/reviews/", EmployeeReviewListCreateView.as_view(), name="employee-review-list"),
    path("employment-events/", EmploymentEventListView.as_view(), name="employment-event-list"),
    path("employment-events/create/", EmploymentEventCreateView.as_view(), name="employment-event-create"),
]
