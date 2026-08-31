from rest_framework import serializers

from .models import (
    AcademicUnit,
    AcademicYear,
    AcademicCalendar,
    Campus,
    Class,
    ClassTeacher,
    School,
    Section,
    Subject,
    SubjectGroup,
    SubjectOffering,
    Term,
)


class SchoolSerializer(serializers.ModelSerializer):
    campus_count = serializers.IntegerField(
        source="campuses.count",
        read_only=True,
    )

    class Meta:
        model = School
        fields = [
            "id",
            "name",
            "code",
            "institution_type",
            "timezone",
            "currency",
            "address",
            "city",
            "status",
            "campus_count",
            "created_at",
            "updated_at",
        ]


class CampusSerializer(serializers.ModelSerializer):
    class_count = serializers.IntegerField(
        read_only=True,
    )
    section_count = serializers.IntegerField(
        read_only=True,
    )
    student_count = serializers.IntegerField(
        read_only=True,
    )
    school_name = serializers.CharField(
        source="school.name",
        read_only=True,
    )
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.all(),
        required=False,
    )

    class Meta:
        model = Campus
        fields = [
            "id",
            "school",
            "school_name",
            "name",
            "address",
            "city",
            "status",
            "class_count",
            "section_count",
            "student_count",
            "created_at",
            "updated_at",
        ]


class AcademicUnitSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(
        source="campus.name",
        read_only=True,
    )
    class_count = serializers.IntegerField(
        source="classes.count",
        read_only=True,
    )

    class Meta:
        model = AcademicUnit
        fields = [
            "id",
            "campus",
            "campus_name",
            "name",
            "status",
            "class_count",
            "created_at",
            "updated_at",
        ]


class ClassSerializer(serializers.ModelSerializer):
    campus = serializers.IntegerField(
        source="unit.campus_id",
        read_only=True,
    )
    campus_name = serializers.CharField(
        source="unit.campus.name",
        read_only=True,
    )
    unit_name = serializers.CharField(
        source="unit.name",
        read_only=True,
    )
    section_count = serializers.IntegerField(
        source="sections.count",
        read_only=True,
    )
    student_count = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = Class
        fields = [
            "id",
            "unit",
            "unit_name",
            "campus",
            "campus_name",
            "name",
            "level",
            "status",
            "section_count",
            "student_count",
            "created_at",
            "updated_at",
        ]


class SectionSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(
        source="class_obj.name",
        read_only=True,
    )
    campus_name = serializers.CharField(
        source="class_obj.unit.campus.name",
        read_only=True,
    )
    student_count = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = Section
        fields = [
            "id",
            "class_obj",
            "class_name",
            "campus_name",
            "name",
            "capacity",
            "status",
            "student_count",
            "created_at",
            "updated_at",
        ]


class AcademicYearSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(
        source="school.name",
        read_only=True,
    )

    class Meta:
        model = AcademicYear
        fields = [
            "id",
            "school",
            "school_name",
            "name",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
        ]


class TermSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )

    class Meta:
        model = Term
        fields = [
            "id",
            "academic_year",
            "academic_year_name",
            "name",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        ]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = [
            "id",
            "name",
            "code",
            "subject_type",
            "practical_required",
            "status",
            "created_at",
            "updated_at",
        ]


class SubjectOfferingSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True,
    )
    class_name = serializers.CharField(
        source="class_obj.name",
        read_only=True,
    )
    campus_name = serializers.CharField(
        source="class_obj.unit.campus.name",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )

    class Meta:
        model = SubjectOffering
        fields = [
            "id",
            "subject",
            "subject_name",
            "class_obj",
            "class_name",
            "campus_name",
            "academic_year",
            "academic_year_name",
            "created_at",
            "updated_at",
        ]


class SubjectGroupSerializer(serializers.ModelSerializer):
    subject_count = serializers.IntegerField(
        source="subjects.count",
        read_only=True,
    )

    class Meta:
        model = SubjectGroup
        fields = [
            "id",
            "institution",
            "name",
            "code",
            "description",
            "status",
            "subjects",
            "subject_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ClassTeacherSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)

    class Meta:
        model = ClassTeacher
        fields = [
            "id",
            "teacher",
            "teacher_name",
            "section",
            "section_name",
            "academic_year",
            "academic_year_name",
            "status",
            "assigned_date",
            "removed_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AcademicCalendarSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)
    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AcademicCalendar
        fields = [
            "id",
            "institution",
            "campus",
            "campus_name",
            "academic_year",
            "academic_year_name",
            "event_type",
            "event_type_display",
            "title",
            "description",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "is_all_day",
            "is_for_all_campuses",
            "target_classes",
            "target_sections",
            "status",
            "status_display",
            "is_recurring",
            "recurrence_rule",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SubjectGroupSerializer(serializers.ModelSerializer):
    subject_count = serializers.IntegerField(
        source="subjects.count",
        read_only=True,
    )

    class Meta:
        model = SubjectGroup
        fields = [
            "id",
            "institution",
            "name",
            "code",
            "description",
            "status",
            "subjects",
            "subject_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]