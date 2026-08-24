from rest_framework import serializers

from .models import Homework, Submission


class HomeworkSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
        source="teacher.full_name",
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
        default="",
    )

    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True,
        default="",
    )

    submission_count = serializers.SerializerMethodField()

    class Meta:
        model = Homework
        fields = [
            "id",
            "teacher",
            "teacher_name",
            "campus",
            "campus_name",
            "class_obj",
            "class_name",
            "section",
            "section_name",
            "subject",
            "subject_name",
            "title",
            "description",
            "assigned_date",
            "due_date",
            "max_marks",
            "submission_count",
            "created_at",
        ]
        read_only_fields = ["teacher", "created_by", "created_at"]

    def get_submission_count(self, obj):
        return obj.submissions.count()


class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )

    admission_number = serializers.CharField(
        source="student.admission_number",
        read_only=True,
    )

    class Meta:
        model = Submission
        fields = [
            "id",
            "homework",
            "student",
            "student_name",
            "admission_number",
            "content",
            "attachment",
            "submitted_at",
            "marks_obtained",
            "feedback",
            "status",
            "graded_by",
        ]
        read_only_fields = ["homework", "submitted_at", "graded_by", "status"]
