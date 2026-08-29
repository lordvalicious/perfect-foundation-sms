from rest_framework import serializers

from .models import Attendance, AttendanceCorrection


class AttendanceSerializer(serializers.ModelSerializer):
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
    class_name = serializers.CharField(
        source="class_obj.name",
        read_only=True,
    )
    section_name = serializers.CharField(
        source="section.name",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    marked_by_name = serializers.CharField(
        source="marked_by.get_full_name",
        read_only=True,
    )

    class Meta:
        model = Attendance
        fields = [
            "id",
            "student",
            "student_name",
            "admission_number",
            "campus",
            "campus_name",
            "class_obj",
            "class_name",
            "section",
            "section_name",
            "academic_year",
            "date",
            "status",
            "status_display",
            "notes",
            "marked_by",
            "marked_by_name",
        ]


class AttendanceMarkSerializer(serializers.Serializer):
    """Input validator for marking/updating a single student's attendance."""

    student = serializers.IntegerField()
    date = serializers.DateField()
    status = serializers.ChoiceField(
        choices=Attendance.STATUS_CHOICES
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class AttendanceCorrectionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )
    corrected_by_name = serializers.CharField(
        source="corrected_by.get_full_name",
        read_only=True,
    )
    from_status_display = serializers.CharField(
        source="get_from_status_display",
        read_only=True,
    )
    to_status_display = serializers.CharField(
        source="get_to_status_display",
        read_only=True,
    )
    date = serializers.DateField(source="attendance.date", read_only=True)

    class Meta:
        model = AttendanceCorrection
        fields = [
            "id",
            "attendance",
            "student",
            "student_name",
            "date",
            "from_status",
            "from_status_display",
            "to_status",
            "to_status_display",
            "reason",
            "corrected_by",
            "corrected_by_name",
            "corrected_at",
        ]
        read_only_fields = [
            "id",
            "student",
            "student_name",
            "date",
            "from_status",
            "to_status",
            "reason",
            "corrected_by",
            "corrected_by_name",
            "corrected_at",
        ]
