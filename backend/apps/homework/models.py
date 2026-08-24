from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import Campus, Class, School, Section, Subject
from apps.students.models import Student
from apps.teachers.models import Teacher


class Homework(models.Model):
    """A homework assignment given by a teacher for a class/section."""

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="homework",
        null=True,
        blank=True,
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="homework_given",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="homework",
    )

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name="homework",
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="homework",
        help_text="Leave empty to assign the whole class.",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="homework",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assigned_date = models.DateField()
    due_date = models.DateField()

    max_marks = models.PositiveIntegerField(
        default=10,
        help_text="Maximum score a student can receive.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_homework",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-assigned_date", "-id"]

    def clean(self):
        if self.due_date and self.assigned_date and self.due_date < self.assigned_date:
            raise ValidationError(
                {"due_date": "Due date cannot be before the assigned date."}
            )

        if self.class_obj_id and self.campus_id:
            if self.class_obj.unit.campus_id != self.campus_id:
                raise ValidationError(
                    {"class_obj": "Class does not belong to this campus."}
                )

    def __str__(self):
        return f"{self.title} ({self.class_obj.name})"


class Submission(models.Model):
    """A student's submission (and grade) for a homework."""

    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("graded", "Graded"),
        ("returned", "Returned"),
    ]

    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="homework_submissions",
    )

    content = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to="homework/%Y/%m/",
        blank=True,
        null=True,
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    marks_obtained = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default="submitted",
    )

    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_homework",
    )

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["homework", "student"],
                name="unique_submission_per_homework_student",
            )
        ]

    def clean(self):
        if (
            self.marks_obtained is not None
            and self.homework_id
            and self.marks_obtained > self.homework.max_marks
        ):
            raise ValidationError(
                {
                    "marks_obtained": (
                        f"Marks cannot exceed {self.homework.max_marks}."
                    )
                }
            )

    def __str__(self):
        return f"{self.student.full_name} - {self.homework.title}"
