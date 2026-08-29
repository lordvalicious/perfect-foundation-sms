from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.workflow import services
from apps.workflow.models import WorkflowApproval, WorkflowDefinition, WorkflowInstance, WorkflowTransition


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDefinition
        fields = [
            "id",
            "name",
            "slug",
            "object_type",
            "states",
            "initial_state",
            "approval_steps",
            "transitions",
            "is_active",
        ]
        read_only_fields = fields


class WorkflowApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(
        source="approver.get_full_name",
        read_only=True,
        default="",
    )

    class Meta:
        model = WorkflowApproval
        fields = [
            "id",
            "instance",
            "sequence",
            "role",
            "status",
            "approver",
            "approver_name",
            "comment",
            "decided_at",
        ]
        read_only_fields = fields


class WorkflowTransitionSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(
        source="actor.get_full_name",
        read_only=True,
        default="",
    )

    class Meta:
        model = WorkflowTransition
        fields = [
            "id",
            "action",
            "from_state",
            "to_state",
            "actor",
            "actor_name",
            "comment",
            "created_at",
        ]
        read_only_fields = fields


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    definition_slug = serializers.CharField(max_length=100, write_only=True)
    definition_name = serializers.CharField(source="definition.name", read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.get_full_name",
        read_only=True,
        default="",
    )
    comment = serializers.CharField(write_only=True, required=False, allow_blank=True, default="")

    class Meta:
        model = WorkflowInstance
        fields = [
            "id",
            "definition_slug",
            "definition",
            "definition_name",
            "object_type",
            "object_id",
            "current_state",
            "is_terminal",
            "campus",
            "institution",
            "created_by",
            "created_by_name",
            "comment",
            "submitted_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "definition",
            "definition_name",
            "current_state",
            "is_terminal",
            "created_by",
            "created_by_name",
            "submitted_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        definition_slug = validated_data.pop("definition_slug")
        object_id = validated_data.get("object_id")
        object_type = validated_data.get("object_type")
        campus = validated_data.get("campus")
        comment = validated_data.pop("comment", "") or ""

        definition = services.get_definition(object_type)
        if definition is None or definition.slug != definition_slug:
            raise serializers.ValidationError(
                {"definition_slug": "No active workflow definition for this object type."}
            )

        request = self.context.get("request")
        actor = request.user if request else None
        institution = (
            request.institution
            if request and getattr(request, "institution", None)
            else getattr(actor, "primary_institution", None)
        )

        return services.start(
            object_type,
            object_id,
            institution=institution,
            campus=campus,
            actor=actor,
            comment=comment,
        )


class WorkflowInstanceDetailSerializer(WorkflowInstanceSerializer):
    approvals = WorkflowApprovalSerializer(many=True, read_only=True)
    transitions = WorkflowTransitionSerializer(many=True, read_only=True)

    class Meta(WorkflowInstanceSerializer.Meta):
        fields = WorkflowInstanceSerializer.Meta.fields + ["approvals", "transitions"]


class WorkflowActionSerializer(serializers.Serializer):
    action = serializers.CharField()
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class WorkflowApprovalDecideSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=[services.ACTION_APPROVE, services.ACTION_REJECT])
    comment = serializers.CharField(required=False, allow_blank=True, default="")