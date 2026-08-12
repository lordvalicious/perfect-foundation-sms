from rest_framework import serializers

from .models import (
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    School,
    Section,
    Subject,
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

    class Meta:
        model = Campus
        fields = [
            "id",
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
            "unit_type",
            "status",
            "class_count",
            "created_at",
            "updated_at",
        ]


class ClassSerializer(serializers.ModelSerializer):
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
