from rest_framework import serializers

from .models import DisciplinaryAction, Incident


class IncidentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )

    admission_number = serializers.CharField(
        source="student.admission_number",
        read_only=True,
    )

    campus_name = serializers.CharField(
        source="campus.name",
        read_only=True,
    )

    reported_by_name = serializers.CharField(
        source="reported_by.get_full_name",
        read_only=True,
        default="",
    )

    class Meta:
        model = Incident
        fields = [
            "id",
            "student",
            "student_name",
            "admission_number",
            "campus",
            "campus_name",
            "title",
            "description",
            "location",
            "incident_date",
            "severity",
            "status",
            "action_taken",
            "points",
            "parent_notified",
            "reported_by",
            "reported_by_name",
            "resolved_at",
            "created_at",
        ]
        read_only_fields = [
            "status",
            "points",
            "resolved_at",
            "created_at",
        ]


class DisciplinaryActionSerializer(serializers.ModelSerializer):
    action_type_display = serializers.CharField(
        source="get_action_type_display",
        read_only=True,
    )

    recorded_by_name = serializers.CharField(
        source="recorded_by.get_full_name",
        read_only=True,
        default="",
    )

    class Meta:
        model = DisciplinaryAction
        fields = [
            "id",
            "incident",
            "action_type",
            "action_type_display",
            "details",
            "action_date",
            "recorded_by",
            "recorded_by_name",
            "created_at",
        ]
        read_only_fields = ["incident", "created_at"]
