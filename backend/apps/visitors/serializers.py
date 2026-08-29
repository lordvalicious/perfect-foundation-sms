from rest_framework import serializers

from .models import Visitor


class VisitorSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Visitor
        fields = [
            "id",
            "campus",
            "campus_name",
            "full_name",
            "phone",
            "id_number",
            "company",
            "vehicle_number",
            "purpose",
            "meeting_party",
            "check_in",
            "check_out",
            "badge_number",
            "photo",
            "notes",
            "status",
            "is_active",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "check_in",
            "check_out",
            "badge_number",
            "status",
            "created_by",
            "created_at",
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return "—"

    def validate_campus(self, value):
        if value is None:
            raise serializers.ValidationError("Campus is required.")
        return value