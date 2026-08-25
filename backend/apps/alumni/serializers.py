from rest_framework import serializers

from .models import AlumniProfile


class AlumniProfileSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(
        source="campus.name",
        read_only=True,
        default="",
    )

    class Meta:
        model = AlumniProfile
        fields = [
            "id",
            "student",
            "campus",
            "campus_name",
            "full_name",
            "batch_year",
            "email",
            "phone",
            "occupation",
            "organization",
            "city",
            "notes",
            "is_active_member",
            "created_at",
        ]

    def validate_batch_year(self, value):
        if value < 1980 or value > 2100:
            raise serializers.ValidationError(
                "Batch year looks invalid."
            )

        return value
