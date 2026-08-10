from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.exams.models import Exam
from apps.students.models import Student


class ReportCard(models.Model):
    """
    Overall report card for one student and one exam.

    Marks are NOT duplicated here.
    They are calculated from StudentResult.
    """

    RESULT_CHOICES = [
        ("pass", "Pass"),
        ("fail", "Fail"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("published", "Published"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="report_cards",
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="report_cards",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    teacher_remarks = models.TextField(
        blank=True,
    )

    principal_remarks = models.TextField(
        blank=True,
    )

    position = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "exam",
            "position",
            "student__first_name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "exam",
                ],
                name="unique_report_card_per_student_exam",
            )
        ]

    def clean(self):
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
                raise ValidationError(
                    "The student is not actively enrolled "
                    "in this exam's class and campus."
                )

    @property
    def results(self):
        """
        Return this student's results for this exam.
        """
        from apps.exams.models import StudentResult

        return (
            StudentResult.objects
            .filter(
                exam=self.exam,
                student=self.student,
            )
            .select_related(
                "exam_subject__subject",
            )
            .order_by(
                "exam_subject__subject__name",
            )
        )

    @property
    def subject_count(self):
        return self.results.count()

    @property
    def total_marks(self):
        total = Decimal("0.00")

        for result in self.results:
            total += result.obtained_marks

        return total.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def maximum_marks(self):
        total = Decimal("0.00")

        for result in self.results:
            total += Decimal(
                str(result.exam_subject.maximum_marks)
            )

        return total

    @property
    def percentage(self):
        maximum = self.maximum_marks

        if maximum <= 0:
            return Decimal("0.00")

        percentage = (
            self.total_marks / maximum
        ) * Decimal("100")

        return percentage.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def grade(self):
        band = GradeBand.band_for_percentage(self.percentage)

        return band.letter_grade if band else ""

    @property
    def grade_point(self):
        band = GradeBand.band_for_percentage(self.percentage)

        return band.grade_point if band else Decimal("0.00")

    @property
    def is_pass(self):
        """
        A student passes the report card only if every
        recorded subject result is passed.
        """
        results = list(self.results)

        if not results:
            return False

        return all(
            result.is_pass
            for result in results
        )

    @property
    def overall_result(self):
        return (
            "Pass"
            if self.is_pass
            else "Fail"
        )

    @property
    def absent_subjects(self):
        """
        Subjects that have no StudentResult yet.
        """

        from apps.exams.models import ExamSubject

        subject_ids = set(
            self.results.values_list(
                "exam_subject_id",
                flat=True,
            )
        )

        return (
            ExamSubject.objects
            .filter(exam=self.exam)
            .exclude(id__in=subject_ids)
            .select_related("subject")
        )

    @property
    def is_complete(self):
        """
        True when a result exists for every subject
        included in the exam.
        """

        expected = self.exam.exam_subjects.count()

        return (
            expected > 0
            and self.subject_count == expected
        )

    @property
    def can_edit(self):
        """Published report cards are locked."""
        return self.status != "published"

    @property
    def status_display(self):
        return self.get_status_display()

    def calculate_position(self):
        """
        Calculate position among students enrolled in
        the same exam class.

        Students with higher total marks rank higher.
        Equal totals receive the same position.
        """

        from apps.students.models import Enrollment

        enrolled_student_ids = (
            Enrollment.objects
            .filter(
                academic_year=self.exam.academic_year,
                campus=self.exam.campus,
                class_obj=self.exam.class_obj,
                status="active",
            )
            .values_list(
                "student_id",
                flat=True,
            )
        )

        report_cards = (
            ReportCard.objects
            .filter(
                exam=self.exam,
                student_id__in=enrolled_student_ids,
            )
            .select_related("student")
        )

        rankings = []

        for report_card in report_cards:
            rankings.append(
                (
                    report_card.student_id,
                    report_card.total_marks,
                )
            )

        rankings.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        current_position = 0
        previous_marks = None

        for index, (student_id, marks) in enumerate(
            rankings,
            start=1,
        ):
            if marks != previous_marks:
                current_position = index

            if student_id == self.student_id:
                return current_position

            previous_marks = marks

        return None

    def update_position(self):
        """
        Calculate and save the student's position.
        """

        self.position = self.calculate_position()

        self.save(
            update_fields=[
                "position",
                "updated_at",
            ]
        )

    def generate_teacher_remarks(self):
        """
        Generate a sensible default remark based on
        the student's overall performance.
        """

        percentage = self.percentage

        if not self.is_complete:
            return "Result is incomplete."

        if self.is_pass:
            if percentage >= Decimal("90"):
                return "Outstanding performance. Keep up the excellent work."
            elif percentage >= Decimal("80"):
                return "Excellent performance. Keep working hard."
            elif percentage >= Decimal("70"):
                return "Very good performance. Continue improving."
            elif percentage >= Decimal("60"):
                return "Good performance. Further improvement is encouraged."
            elif percentage >= Decimal("50"):
                return "Satisfactory performance. More effort is recommended."
            else:
                return "Passed. Additional effort will help improve performance."

        return "The student needs additional academic support and practice."

    def approve(self, user=None):
        """
        Move a draft report card to the approved state.

        Publishing (which exposes the result to students) is a
        separate, later step performed by an academic administrator.
        """
        from apps.audit.models import record_audit

        if self.status == "draft":
            self.status = "approved"

            self.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            record_audit(
                user=user,
                action="grade_publish",
                model_name="ReportCard",
                object_id=str(self.pk),
                object_repr=str(self),
                details={"status": "approved"},
            )

    def publish(self, user=None):
        """
        Publish the report card so students can view it.

        A published report card is locked; further corrections
        must go through a grade amendment.
        """
        from apps.audit.models import record_audit

        self.status = "published"
        self.published_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "published_at",
                "updated_at",
            ]
        )

        record_audit(
            user=user,
            action="grade_publish",
            model_name="ReportCard",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"status": "published"},
        )

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.teacher_remarks:
            self.teacher_remarks = (
                self.generate_teacher_remarks()
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.student.full_name} - "
            f"{self.exam.name}"
        )


class ReportCardSubject(models.Model):
    """
    A printable snapshot/reference for one subject on a
    report card.

    This does not replace StudentResult.
    It stores the subject-level report-card information
    when a snapshot is needed.
    """

    report_card = models.ForeignKey(
        ReportCard,
        on_delete=models.CASCADE,
        related_name="subject_entries",
    )

    exam_subject = models.ForeignKey(
        "exams.ExamSubject",
        on_delete=models.PROTECT,
        related_name="report_card_entries",
    )

    obtained_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    maximum_marks = models.PositiveIntegerField()

    percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    grade = models.CharField(
        max_length=3,
        blank=True,
    )

    is_pass = models.BooleanField(
        default=False,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
    )

    class Meta:
        ordering = [
            "exam_subject__subject__name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "report_card",
                    "exam_subject",
                ],
                name="unique_report_card_subject",
            )
        ]

    def clean(self):
        if self.exam_subject_id and self.report_card_id:
            if (
                self.exam_subject.exam_id
                != self.report_card.exam_id
            ):
                raise ValidationError(
                    "The exam subject does not belong "
                    "to this report card's exam."
                )

    def __str__(self):
        return (
            f"{self.report_card.student.full_name} - "
            f"{self.exam_subject.subject.name}"
        )


class GradeScale(models.Model):
    """
    A named set of letter-grade bands (a grading scale).

    Institutions may configure their own scales; the default scale
    is used for automated grade calculation.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Used for automated grade calculation.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if self.is_default:
            GradeScale.objects.filter(
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class GradeBand(models.Model):
    """
    One letter-grade band within a GradeScale.

    minimum_percentage is inclusive, maximum_percentage is
    exclusive, so bands cannot silently overlap.
    """

    scale = models.ForeignKey(
        GradeScale,
        on_delete=models.CASCADE,
        related_name="bands",
    )

    letter_grade = models.CharField(max_length=3)
    grade_point = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    minimum_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    maximum_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    class Meta:
        ordering = ["-minimum_percentage"]

        constraints = [
            models.UniqueConstraint(
                fields=["scale", "letter_grade"],
                name="unique_band_per_scale",
            ),
            models.UniqueConstraint(
                fields=["scale", "minimum_percentage"],
                name="unique_min_per_scale",
            ),
        ]

    def clean(self):
        errors = {}

        if self.minimum_percentage < 0:
            errors["minimum_percentage"] = (
                "Minimum percentage cannot be negative."
            )

        if self.maximum_percentage > Decimal("100"):
            errors["maximum_percentage"] = (
                "Maximum percentage cannot exceed 100."
            )

        if self.minimum_percentage >= self.maximum_percentage:
            errors["minimum_percentage"] = (
                "Minimum percentage must be lower than the maximum."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @classmethod
    def band_for_percentage(cls, percentage, scale=None):
        """Return the band matching a percentage on a scale."""
        if scale is None:
            scale = GradeScale.objects.filter(
                is_default=True,
            ).first()

        if scale is None:
            return None

        band = cls.objects.filter(
            scale=scale,
            minimum_percentage__lte=percentage,
            maximum_percentage__gt=percentage,
        ).first()

        if band is None:
            # A perfect score sits exactly on the upper edge of
            # the top band (its maximum is exclusive), so fall back
            # to the highest band that reaches this percentage.
            band = (
                cls.objects.filter(
                    scale=scale,
                    maximum_percentage__gte=percentage,
                )
                .order_by("-maximum_percentage")
                .first()
            )

        return band

    def __str__(self):
        return (
            f"{self.scale.name} - {self.letter_grade} "
            f"({self.minimum_percentage}-{self.maximum_percentage})"
        )


class GradeAmendment(models.Model):
    """
    A recorded, audited correction to a published report card.

    Published grades are locked, so changes must carry a reason
    and are traced back to the person who made them.
    """

    report_card = models.ForeignKey(
        ReportCard,
        on_delete=models.CASCADE,
        related_name="amendments",
    )

    exam_subject = models.ForeignKey(
        "exams.ExamSubject",
        on_delete=models.PROTECT,
        related_name="amendments",
    )

    student_result = models.OneToOneField(
        "exams.StudentResult",
        on_delete=models.PROTECT,
        related_name="amendment",
    )

    previous_obtained_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    new_obtained_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    previous_grade = models.CharField(
        max_length=3,
        blank=True,
    )

    new_grade = models.CharField(
        max_length=3,
        blank=True,
    )

    reason = models.TextField()

    amended_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grade_amendments",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.report_card} - {self.exam_subject.subject.name}"
        )