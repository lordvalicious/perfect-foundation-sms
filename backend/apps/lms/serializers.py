from rest_framework import serializers

from .models import (
    Course,
    Lesson,
    LessonCompletion,
    Question,
    Quiz,
    QuizAttempt,
)


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "title",
            "content",
            "video_url",
            "order",
        ]
        read_only_fields = ["course"]


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
        source="teacher.full_name", read_only=True
    )
    campus_name = serializers.CharField(
        source="campus.name", read_only=True
    )
    class_name = serializers.CharField(
        source="class_obj.name", read_only=True, default=""
    )
    subject_name = serializers.CharField(
        source="subject.name", read_only=True, default=""
    )
    lesson_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "teacher",
            "teacher_name",
            "campus",
            "campus_name",
            "class_obj",
            "class_name",
            "subject",
            "subject_name",
            "title",
            "description",
            "is_published",
            "lesson_count",
            "created_at",
        ]
        read_only_fields = ["teacher"]

    def get_lesson_count(self, obj):
        return obj.lessons.count()


class LessonCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonCompletion
        fields = ["id", "lesson", "student", "completed_at"]


class QuestionPublicSerializer(serializers.ModelSerializer):
    """For students: options only, never the correct answer."""

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "marks",
        ]


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "quiz",
            "text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
            "marks",
        ]
        read_only_fields = ["quiz"]


class QuizListSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    attempt_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "course",
            "title",
            "description",
            "is_published",
            "due_date",
            "question_count",
            "attempt_count",
        ]

    def get_question_count(self, obj):
        return obj.questions.count()

    def get_attempt_count(self, obj):
        return obj.attempts.count()


class QuizAttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name", read_only=True
    )
    admission_number = serializers.CharField(
        source="student.admission_number", read_only=True
    )
    percentage = serializers.SerializerMethodField()
    breakdown = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "student",
            "student_name",
            "admission_number",
            "answers",
            "breakdown",
            "score",
            "total_marks",
            "percentage",
            "submitted_at",
        ]

    def get_percentage(self, obj):
        if not obj.total_marks:
            return 0

        return round(float(obj.score) / obj.total_marks * 100, 1)

    def get_breakdown(self, obj):
        return (obj.answers or {}).get("breakdown", {})
