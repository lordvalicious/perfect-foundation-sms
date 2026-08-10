from rest_framework import serializers

from .models import Period, TimetableEntry


class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = [
            "id",
            "name",
            "number",
            "start_time",
            "end_time",
            "is_break",
            "status",
        ]


class TimetableEntrySerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(
        source="get_day_display",
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
    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True,
    )
    subject_code = serializers.CharField(
        source="subject.code",
        read_only=True,
    )
    teacher_name = serializers.SerializerMethodField()
    period_name = serializers.CharField(
        source="period.name",
        read_only=True,
    )
    period_number = serializers.IntegerField(
        source="period.number",
        read_only=True,
    )
    start_time = serializers.TimeField(
        source="period.start_time",
        read_only=True,
    )
    end_time = serializers.TimeField(
        source="period.end_time",
        read_only=True,
    )

    def get_teacher_name(self, entry):
        teacher = entry.teacher

        return (
            f"{teacher.first_name} {teacher.last_name}".strip()
            or "—"
        )

    class Meta:
        model = TimetableEntry
        fields = [
            "id",
            "academic_year",
            "campus",
            "campus_name",
            "class_obj",
            "class_name",
            "section",
            "section_name",
            "subject",
            "subject_name",
            "subject_code",
            "teacher",
            "teacher_name",
            "period",
            "period_name",
            "period_number",
            "start_time",
            "end_time",
            "day",
            "day_display",
            "room",
            "status",
            "notes",
        ]
