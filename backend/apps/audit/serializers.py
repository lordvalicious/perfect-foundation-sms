from rest_framework import serializers

from .models import AuditLog, CSPViolation


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    action_label = serializers.CharField(
        source="get_action_display",
        read_only=True,
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_name",
            "action",
            "action_label",
            "model_name",
            "object_id",
            "object_repr",
            "details",
            "ip_address",
            "timestamp",
        ]

    def get_user_name(self, obj):
        if obj.user is None:
            return None

        return obj.user.get_full_name() or obj.user.username


class CSPViolationSerializer(serializers.ModelSerializer):
    """Serializer for CSP violation reports."""

    class Meta:
        model = CSPViolation
        fields = [
            "id",
            "document_uri",
            "referrer",
            "blocked_uri",
            "violated_directive",
            "effective_directive",
            "original_policy",
            "disposition",
            "script_sample",
            "source_file",
            "line_number",
            "column_number",
            "user_agent",
            "ip_address",
            "user",
            "institution",
            "status_code",
            "resource_type",
            "timestamp",
        ]
        read_only_fields = fields

    def validate(self, attrs):
        """Validate the CSP report data."""
        # Ensure required fields are present
        required_fields = ["document_uri", "violated_directive"]
        for field in required_fields:
            if not attrs.get(field):
                raise serializers.ValidationError(
                    {field: "This field is required."}
                )
        return attrs
