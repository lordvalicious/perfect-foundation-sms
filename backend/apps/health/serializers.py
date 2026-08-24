from rest_framework import serializers

from .models import HealthRecord


class HealthRecordSerializer(serializers.ModelSerializer):
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

    record_type_display = serializers.CharField(
        source="get_record_type_display",
        read_only=True,
    )

    bmi = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        read_only=True,
    )

    class Meta:
        model = HealthRecord
        fields = [
            "id",
            "student",
            "student_name",
            "admission_number",
            "campus",
            "campus_name",
            "record_type",
            "record_type_display",
            "record_date",
            "notes",
            "height_cm",
            "weight_kg",
            "temperature_c",
            "bmi",
            "treated_by",
            "follow_up_date",
            "recorded_by",
            "created_at",
        ]
        read_only_fields = ["recorded_by", "created_at"]
