from rest_framework import serializers

from .models import Guardian, Student, Enrollment


class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = [
            "id",
            "name",
            "relationship",
            "phone",
            "alternate_phone",
            "email",
            "address",
        ]


class EnrollmentSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    campus_name = serializers.CharField(
        source="campus.name",
        read_only=True,
    )
    class_name = serializers.CharField(
        source="class_obj.name",
        read_only=True,
    )
    section_name = serializers.CharField(
        source="section.name",
        read_only=True,
    )

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "academic_year",
            "academic_year_name",
            "campus",
            "campus_name",
            "class_obj",
            "class_name",
            "section",
            "section_name",
            "status",
            "enrollment_date",
        ]


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    guardian_details = GuardianSerializer(
        source="guardian",
        read_only=True,
    )

    enrollments = EnrollmentSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Student
        fields = [
            "id",
            "admission_number",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "gender",
            "guardian",
            "guardian_details",
            "phone",
            "address",
            "status",
            "admission_date",
            "enrollments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "created_at",
            "updated_at",
        ]