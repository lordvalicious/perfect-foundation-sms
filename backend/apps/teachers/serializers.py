from rest_framework import serializers

from .models import Teacher


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = [
            "id",
            "employee_number",
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "phone",
            "email",
            "campus",
            "joining_date",
            "designation",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]
