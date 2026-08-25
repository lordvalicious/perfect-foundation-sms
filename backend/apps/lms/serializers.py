from rest_framework import serializers

from .models import Course, Lesson, LessonCompletion


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
