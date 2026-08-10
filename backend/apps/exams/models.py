from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import AcademicYear, Campus, Class
from apps.students.models import Student

class Exam(models.Model):
    EXAM_TYPE_CHOICES = [
        ("monthly", "Monthly Test"),
        ("midterm", "Mid-Term"),
        ("final", "Final-Term"),
        ("annual", "Annual"),
    ]

    name = models.CharField(max_length=100)
    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES,
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="exams",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="exams",
    )

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name="exams",
    )

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("completed", "Completed"),
        ],
        default="draft",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]

    def clean(self):
        if self.class_obj_id and self.campus_id:
            if self.class_obj.unit.campus_id != self.campus_id:
                raise ValidationError(
                    "The selected class does not belong to the selected campus."
                )

        if self.academic_year_id and self.campus_id:
            if self.campus.school_id != self.academic_year.school_id:
                raise ValidationError(
                    "The academic year does not belong to the campus school."
                )

        if self.end_date < self.start_date:
            raise ValidationError(
                "Exam end date cannot be before the start date."
            )

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.campus.name} - "
            f"{self.class_obj.name}"
        )


class ExamSubject(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="exam_subjects",
    )

    subject = models.ForeignKey(
        "schools.Subject",
        on_delete=models.PROTECT,
        related_name="exam_subjects",
    )

    maximum_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=40)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exam", "subject"],
                name="unique_subject_per_exam",
            )
        ]

    def clean(self):
        if self.passing_marks > self.maximum_marks:
            raise ValidationError(
                "Passing marks cannot exceed maximum marks."
            )

        if self.exam_id and self.subject_id:
            from apps.schools.models import SubjectOffering

            offered = SubjectOffering.objects.filter(
                subject=self.subject,
                class_obj=self.exam.class_obj,
                academic_year=self.exam.academic_year,
            ).exists()

            if not offered:
                raise ValidationError(
                    "This subject is not offered to this class "
                    "for the selected academic year."
                )

    def __str__(self):
        return (
            f"{self.exam.name} - "
            f"{self.subject.name}"
        )


class StudentResult(models.Model):
    GRADE_CHOICES = [
        ("A+", "A+"),
        ("A", "A"),
        ("B+", "B+"),
        ("B", "B"),
        ("C+", "C+"),
        ("C", "C"),
        ("D", "D"),
        ("F", "F"),
    ]

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="results",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="exam_results",
    )

    exam_subject = models.ForeignKey(
        ExamSubject,
        on_delete=models.CASCADE,
        related_name="results",
    )

    obtained_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    is_absent = models.BooleanField(
        default=False,
        help_text=(
            "Store absence separately from a score of zero."
        ),
    )

    grade = models.CharField(
        max_length=3,
        choices=GRADE_CHOICES,
        blank=True,
    )

    is_pass = models.BooleanField(default=False)

    remarks = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "exam",
                    "student",
                    "exam_subject",
                ],
                name="unique_student_exam_subject_result",
            )
        ]

    def clean(self):
        errors = {}

        if self.exam_id and self.exam_subject_id:
            if self.exam_subject.exam_id != self.exam_id:
                errors["exam_subject"] = (
                    "The selected subject does not belong to this exam."
                )

        if self.student_id and self.exam_id:
            from apps.students.models import Enrollment

            enrolled = Enrollment.objects.filter(
                student=self.student,
                academic_year=self.exam.academic_year,
                campus=self.exam.campus,
                class_obj=self.exam.class_obj,
                status="active",
            ).exists()

            if not enrolled:
                errors["student"] = (
                    "The student is not actively enrolled "
                    "in this exam's class and campus."
                )

        if self.obtained_marks < 0:
            errors["obtained_marks"] = (
                "Obtained marks cannot be negative."
            )

        if self.is_absent and self.obtained_marks != 0:
            errors["obtained_marks"] = (
                "An absent student must have zero obtained marks."
            )

        if self.exam_subject_id and not self.is_absent:
            if self.obtained_marks > self.exam_subject.maximum_marks:
                errors["obtained_marks"] = (
                    "Obtained marks cannot exceed maximum marks."
                )

        if self.student_id and self.exam_id:
            from apps.reportcards.models import ReportCard

            report_card = ReportCard.objects.filter(
                student=self.student,
                exam=self.exam,
            ).first()

            if report_card is not None and not report_card.can_edit:
                errors["__all__"] = (
                    "This result belongs to a published report card. "
                    "Use a grade amendment to correct it."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()

        from apps.reportcards.models import GradeBand

        if self.is_absent:
            self.obtained_marks = Decimal("0.00")
            self.grade = ""
            self.is_pass = False
        else:
            maximum = Decimal(
                str(self.exam_subject.maximum_marks)
            )

            percentage = (
                self.obtained_marks / maximum
            ) * Decimal("100")

            band = GradeBand.band_for_percentage(percentage)

            self.grade = band.letter_grade if band else ""

            self.is_pass = (
                self.obtained_marks
                >= self.exam_subject.passing_marks
            )

        super().save(*args, **kwargs)

    @property
    def percentage(self):
        if not self.exam_subject.maximum_marks:
            return Decimal("0.00")

        return (
            self.obtained_marks
            / Decimal(str(self.exam_subject.maximum_marks))
        ) * Decimal("100")

    def __str__(self):
        return (
            f"{self.student.full_name} - "
            f"{self.exam.name} - "
            f"{self.exam_subject.subject.name}"
        )