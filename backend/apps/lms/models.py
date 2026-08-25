from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import Campus, Class, School, Subject
from apps.teachers.models import Teacher


class Course(models.Model):
    """A simple online course: ordered lessons students work through."""

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="lms_courses",
        null=True,
        blank=True,
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="courses",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="lms_courses",
    )

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lms_courses",
        help_text="Target class. Students of this class can self-enrol.",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lms_courses",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.class_obj_id and self.campus_id:
            if self.class_obj.unit.campus_id != self.campus_id:
                raise ValidationError(
                    {"class_obj": "Class does not belong to this campus."}
                )

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
    )
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order"],
                name="unique_lesson_order_per_course",
            )
        ]

    def __str__(self):
        return f"{self.course.title} #{self.order} {self.title}"


class LessonCompletion(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="completions",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="completed_lessons",
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "student"],
                name="unique_completion_per_student_lesson",
            )
        ]


class Quiz(models.Model):
    """An auto-graded MCQ quiz attached to a course."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    is_published = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.course.title})"

    @property
    def total_marks(self):
        return sum(q.marks for q in self.questions.all())


class Question(models.Model):
    OPTION_CHOICES = [
        ("a", "A"),
        ("b", "B"),
        ("c", "C"),
        ("d", "D"),
    ]

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES,
    )
    marks = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Q{self.pk}: {self.text[:50]}"


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    answers = models.JSONField(default=dict)
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
    )
    total_marks = models.PositiveSmallIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "student"],
                name="unique_attempt_per_quiz_student",
            )
        ]
