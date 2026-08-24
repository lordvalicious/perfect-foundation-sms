from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import AcademicYear, Campus, Class, School, Section, Subject
from apps.teachers.models import Teacher


class Period(models.Model):
    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="periods",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=50)
    number = models.PositiveIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_break = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        default="active",
    )

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "number"],
                name="unique_period_number_per_institution",
            ),
        ]

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError(
                "Period end time must be after start time."
            )

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class TimetableEntry(models.Model):
    DAY_CHOICES = [
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
        ("saturday", "Saturday"),
    ]

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )

    period = models.ForeignKey(
        Period,
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )

    day = models.CharField(
        max_length=15,
        choices=DAY_CHOICES,
    )

    room = models.CharField(
        max_length=100,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        default="active",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "day",
            "period__number",
            "class_obj__name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "academic_year",
                    "section",
                    "day",
                    "period",
                ],
                name="unique_section_period",
            ),
            models.UniqueConstraint(
                fields=[
                    "academic_year",
                    "teacher",
                    "day",
                    "period",
                ],
                name="unique_teacher_period",
            ),
        ]

    def clean(self):
        errors = {}

        if self.class_obj_id and self.campus_id:
            if self.class_obj.unit.campus_id != self.campus_id:
                errors["class_obj"] = (
                    "The selected class does not belong "
                    "to the selected campus."
                )

        if self.section_id and self.class_obj_id:
            if self.section.class_obj_id != self.class_obj_id:
                errors["section"] = (
                    "The selected section does not belong "
                    "to the selected class."
                )

        if self.academic_year_id and self.campus_id:
            if self.campus.school_id != self.academic_year.school_id:
                errors["academic_year"] = (
                    "The academic year does not belong "
                    "to the campus school."
                )

        if self.subject_id and self.class_obj_id and self.academic_year_id:
            from apps.schools.models import SubjectOffering

            offered = SubjectOffering.objects.filter(
                subject=self.subject,
                class_obj=self.class_obj,
                academic_year=self.academic_year,
            ).exists()

            if not offered:
                errors["subject"] = (
                    "This subject is not offered to the "
                    "selected class for this academic year."
                )

        if self.teacher_id:
            teacher_campus = self.teacher.campus

            if (
                teacher_campus
                and self.campus_id
                and teacher_campus.strip().lower()
                != self.campus.name.strip().lower()
            ):
                errors["teacher"] = (
                    "The selected teacher is not assigned "
                    "to the selected campus."
                )

        if self.period_id and self.day:
            if self.period.is_break:
                errors["period"] = (
                    "A timetable entry cannot be assigned "
                    "to a break period."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.day.title()} | "
            f"{self.period.name} | "
            f"{self.class_obj.name} | "
            f"{self.section.name} | "
            f"{self.subject.name} | "
            f"{self.teacher}"
        )