from django.urls import path

from apps.workflow.views import (
    WorkflowApprovalDecideView,
    WorkflowApprovalListView,
    WorkflowDefinitionListView,
    WorkflowInstanceActionView,
    WorkflowInstanceDetailView,
    WorkflowInstanceListCreateView,
    WorkflowTransitionListView,
)

urlpatterns = [
    path(
        "definitions/",
        WorkflowDefinitionListView.as_view(),
        name="workflow-definition-list",
    ),
    path(
        "instances/",
        WorkflowInstanceListCreateView.as_view(),
        name="workflow-instance-list",
    ),
    path(
        "instances/<int:pk>/",
        WorkflowInstanceDetailView.as_view(),
        name="workflow-instance-detail",
    ),
    path(
        "instances/<int:pk>/action/",
        WorkflowInstanceActionView.as_view(),
        name="workflow-instance-action",
    ),
    path(
        "instances/<int:pk>/history/",
        WorkflowTransitionListView.as_view(),
        name="workflow-instance-history",
    ),
    path(
        "approvals/",
        WorkflowApprovalListView.as_view(),
        name="workflow-approval-pending",
    ),
    path(
        "approvals/<int:pk>/decide/",
        WorkflowApprovalDecideView.as_view(),
        name="workflow-approval-decide",
    ),
]