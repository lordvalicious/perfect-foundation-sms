from django.contrib import admin

from apps.workflow.models import (
    WorkflowApproval,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowTransition,
)


@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "object_type", "initial_state", "is_active")
    list_filter = ("is_active", "object_type")
    search_fields = ("name", "slug", "object_type")


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "definition",
        "object_type",
        "object_id",
        "current_state",
        "institution",
        "campus",
        "created_by",
        "created_at",
    )
    list_filter = ("current_state", "definition", "institution")
    search_fields = ("object_type", "object_id")


@admin.register(WorkflowApproval)
class WorkflowApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "instance", "sequence", "role", "status", "approver", "decided_at")
    list_filter = ("status", "role")
    search_fields = ("role",)


@admin.register(WorkflowTransition)
class WorkflowTransitionAdmin(admin.ModelAdmin):
    list_display = ("id", "instance", "action", "from_state", "to_state", "actor", "created_at")
    list_filter = ("action", "from_state", "to_state")
    search_fields = ("comment",)