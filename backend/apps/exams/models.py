from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.campus_validation import CampusValidationMixin
from apps.schools.models import AcademicYear, Campus, Class, Section, Term
from apps.students.models import Student


class Exam(models.Model):
    campus_field = "campus"
    institution_field = "academic_year__school"
    
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

    term = models.ForeignKey(
        Term,
        on_delete=models.PROTECT,
        related_name="exams",
        null=True,
        blank=True,
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
        indexes = [
            models.Index(
                fields=["campus", "academic_year", "status"],
                name="exam_campus_year_status_idx",
            ),
            models.Index(
                fields=["class_obj", "exam_type", "status"],
                name="exam_class_type_status_idx",
            ),
            models.Index(
                fields=["start_date", "end_date"],
                name="exam_date_range_idx",
            ),
        ]

    def clean(self):
        # Validate campus belongs to the same institution as academic_year
        if self.campus_id and self.academic_year_id:
            if self.campus.school_id != self.academic_year.school_id:
                raise ValidationError(
                    "The academic year does not belong to the campus school."
                )

        if self.class_obj_id and self.campus_id:
            if self.class_obj.unit.campus_id != self.campus_id:
                raise ValidationError(
                    "The selected class does not belong to the selected campus."
                )

        if self.term_id and self.academic_year_id:
            if self.term.academic_year_id != self.academic_year_id:
                raise ValidationError(
                    "The selected term does not belong to the selected "
                    "academic year."
                )

        if self.end_date < self.start_date:
            raise ValidationError(
                "Exam end date cannot be before the start date."
            )
        
        # Run campus validation
        # super().clean()  # Removed CampusValidationMixin

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.campus.name} - "
            f"{self.class_obj.name}"
        )


class ExamSubject(models.Model):
    exam = models.ForeignKey(
        "exams.Exam",
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
        "exams.Exam",
        on_delete=models.CASCADE,
        related_name="results",
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="exam_results",
    )

    exam_subject = models.ForeignKey(
        "exams.ExamSubject",
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

    is_locked = models.BooleanField(
        default=False,
        help_text='Prevents editing of this result record.',
    )

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
        indexes = [
            models.Index(
                fields=["exam", "student"],
                name="result_exam_student_idx",
            ),
            models.Index(
                fields=["exam_subject", "is_pass"],
                name="result_subject_pass_idx",
            ),
            models.Index(
                fields=["grade", "is_pass"],
                name="result_grade_pass_idx",
            ),
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


class PracticalResult(models.Model):
    """Practical examination marks for a student on an exam subject.

    Practical marks are stored separately from theory (StudentResult)
    and can be combined with them for a final subject total.
    """

    GRADE_CHOICES = StudentResult.GRADE_CHOICES

    exam = models.ForeignKey(
        "exams.Exam",
        on_delete=models.CASCADE,
        related_name="practical_results",
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="practical_exam_results",
    )

    exam_subject = models.ForeignKey(
        "exams.ExamSubject",
        on_delete=models.CASCADE,
        related_name="practical_results",
    )

    obtained_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    maximum_marks = models.PositiveIntegerField(default=50)
    passing_marks = models.PositiveIntegerField(default=20)

    is_absent = models.BooleanField(default=False)

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
                fields=["exam", "student", "exam_subject"],
                name="unique_student_exam_subject_practical",
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

            from apps.reportcards.models import ReportCard

            report_card = ReportCard.objects.filter(
                student=self.student,
                exam=self.exam,
            ).first()

            if report_card is not None and not report_card.can_edit:
                errors["__all__"] = (
                    "This result belongs to a report card that is "
                    "no longer editable. Use a grade amendment to "
                    "correct it."
                )

        if self.obtained_marks < 0:
            errors["obtained_marks"] = (
                "Obtained marks cannot be negative."
            )

        if self.maximum_marks <= 0:
            errors["maximum_marks"] = (
                "Maximum marks must be greater than zero."
            )

        if self.passing_marks > self.maximum_marks:
            errors["passing_marks"] = (
                "Passing marks cannot exceed maximum marks."
            )

        if self.is_absent and self.obtained_marks != 0:
            errors["obtained_marks"] = (
                "An absent student must have zero obtained marks."
            )

        if self.exam_subject_id and not self.is_absent:
            if self.obtained_marks > self.maximum_marks:
                errors["obtained_marks"] = (
                    "Obtained marks cannot exceed maximum marks."
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
            percentage = (
                self.obtained_marks / Decimal(str(self.maximum_marks))
            ) * Decimal("100")

            band = GradeBand.band_for_percentage(percentage)

            self.grade = band.letter_grade if band else ""
            self.is_pass = self.obtained_marks >= self.passing_marks

        super().save(*args, **kwargs)

    @property
    def percentage(self):
        if not self.maximum_marks:
            return Decimal("0.00")

        return (
            self.obtained_marks / Decimal(str(self.maximum_marks))
        ) * Decimal("100")

    def __str__(self):
        return (
            f"{self.student.full_name} - "
            f"{self.exam.name} - "
            f"{self.exam_subject.subject.name} (Practical)"
        )


class ExamSchedule(models.Model):
    """A single examination slot for a section on a given date and time.

    Each schedule binds an exam to a section, subject and room, and is
    validated to prevent:

    * one section sitting two exams at overlapping date/time, and
    * two exams competing for the same room at overlapping date/time.
    """

    exam = models.ForeignKey(
        "exams.Exam",
        on_delete=models.CASCADE,
        related_name="schedules",
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name="exam_schedules",
    )

    exam_subject = models.ForeignKey(
        "exams.ExamSubject",
        on_delete=models.PROTECT,
        related_name="schedules",
        null=True,
        blank=True,
    )

    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    room = models.CharField(
        max_length=100,
        blank=True,
        help_text="Room, hall or location for the exam.",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "start_time", "section__name"]
        indexes = [
            models.Index(
                fields=["exam", "date", "start_time"],
                name="examsched_exam_date_idx",
            ),
            models.Index(
                fields=["section", "date", "start_time"],
                name="examsched_sec_date_idx",
            ),
            models.Index(
                fields=["date", "room"],
                name="examsched_date_room_idx",
            ),
        ]

    def clean(self):
        errors = {}

        if self.end_time and self.start_time:
            if self.end_time <= self.start_time:
                errors["end_time"] = (
                    "Exam end time must be after start time."
                )

        if self.exam_id and self.date:
            if self.date < self.exam.start_date or self.date > self.exam.end_date:
                errors["date"] = (
                    "Exam date must fall within the exam period "
                    f"({self.exam.start_date} to {self.exam.end_date})."
                )

        if self.exam_id and self.section_id:
            if self.section.class_obj_id != self.exam.class_obj_id:
                errors["section"] = (
                    "The selected section does not belong "
                    "to the exam's class."
                )

        if self.exam_id and self.exam_subject_id:
            if self.exam_subject.exam_id != self.exam_id:
                errors["exam_subject"] = (
                    "The selected subject does not belong to this exam."
                )

        errors.update(self._validate_conflicts())

        if errors:
            raise ValidationError(errors)

    def _validate_conflicts(self):
        """Detect overlapping sections and rooms at the same date/time."""
        errors = {}

        if not (self.date and self.start_time and self.end_time):
            return errors

        overlap = (
            lambda qs: qs.exclude(pk=self.pk).filter(
                date=self.date,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )
        )

        if self.section_id:
            conflicting_section = overlap(
                ExamSchedule.objects.filter(section_id=self.section_id)
            ).exists()

            if conflicting_section:
                errors["section"] = (
                    "This section already has an exam scheduled "
                    "overlapping this date and time."
                )

        if self.room:
            conflicting_room = overlap(
                ExamSchedule.objects.filter(room=self.room)
            ).only("pk").exists()

            if conflicting_room:
                errors["room"] = (
                    "This room is already booked for an exam "
                    "overlapping this date and time."
                )

        return errors

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.exam.name} | "
            f"{self.section} | "
            f"{self.date} "
            f"{self.start_time}-{self.end_time}"
        )