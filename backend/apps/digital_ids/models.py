from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import School


class IdCard(models.Model):
    """A digital / printable ID card issued to a student, teacher or staff."""

    HOLDER_TYPE_CHOICES = [
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("staff", "Staff"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("revoked", "Revoked"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="id_cards",
    )

    # Snapshot of the holder's campus at issue time (for scoping).
    campus = models.ForeignKey(
        "schools.Campus",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="id_cards",
    )

    holder_type = models.CharField(
        max_length=20,
        choices=HOLDER_TYPE_CHOICES,
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="id_cards",
    )

    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="id_cards",
    )

    staff = models.ForeignKey(
        "accounts.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="id_cards",
    )

    card_number = models.CharField(max_length=40)
    barcode_data = models.CharField(max_length=80, blank=True)

    issue_date = models.DateField()
    expiry_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    photo = models.ImageField(
        upload_to="digital_ids/",
        blank=True,
        null=True,
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_id_cards",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "card_number"],
                name="unique_card_number_per_institution",
            )
        ]

    def clean(self):
        if self.holder_type == "student" and not self.student_id:
            raise ValidationError({"student": "Student is required for a student card."})
        if self.holder_type == "teacher" and not self.teacher_id:
            raise ValidationError({"teacher": "Teacher is required for a teacher card."})
        if self.holder_type == "staff" and not self.staff_id:
            raise ValidationError({"staff": "Staff is required for a staff card."})

    # ------------------------------------------------------------------
    # Holder helpers
    # ------------------------------------------------------------------

    @property
    def holder(self):
        if self.holder_type == "student":
            return self.student
        if self.holder_type == "teacher":
            return self.teacher
        return self.staff

    @property
    def holder_name(self):
        person = self.holder
        if person is None:
            return ""
        return person.full_name or str(person)

    @property
    def holder_code(self):
        person = self.holder
        if person is None:
            return ""
        if self.holder_type == "student":
            return person.admission_number
        return person.employee_number or ""

    @property
    def holder_photo(self):
        person = self.holder
        if person is None:
            return None
        photo = getattr(person, "photo", None)
        if not photo:
            return None
        return photo.url

    @property
    def student_class_label(self):
        if self.holder_type != "student" or not self.student_id:
            return None
        enrollment = (
            self.student.enrollments.filter(status="active")
            .select_related("class_obj", "section")
            .order_by("-academic_year__start_date")
            .first()
        )
        if not enrollment:
            return None
        label = enrollment.class_obj.name
        if enrollment.section:
            label += f" - {enrollment.section.name}"
        return label

    def __str__(self):
        return f"{self.holder_name} ({self.card_number})"