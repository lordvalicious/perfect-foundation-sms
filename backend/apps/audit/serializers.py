from rest_framework import serializers

from .models import AuditLog


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
