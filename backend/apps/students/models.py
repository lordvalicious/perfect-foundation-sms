
from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import AcademicYear, Campus, Class, Section


class Guardian(models.Model):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guardian_profile",
    )

    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=50)
    phone = models.CharField(max_length=30)
    alternate_phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.relationship})"


class Student(models.Model):
    admission_number = models.CharField(
        max_length=50,
        unique=True,
    )

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
    )

    membership = models.OneToOneField("accounts.InstitutionMembership", on_delete=models.SET_NULL, null=True, blank=True, related_name="student_profile")
    primary_campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_students")

    photo = models.ImageField(
        upload_to="profiles/students/",
        blank=True,
        null=True,
    )

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
    ]

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
    )

    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.PROTECT,
        related_name="students",
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    address = models.TextField(blank=True)

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("graduated", "Graduated"),
        ("withdrawn", "Withdrawn"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    admission_date = models.DateField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.admission_number} - {self.full_name}"

    def clean(self):
        if self.membership_id and self.user_id and self.membership.user_id != self.user_id:
            raise ValidationError({"membership": "Membership must belong to this user."})
        if self.membership_id and self.primary_campus_id and self.primary_campus.school_id != self.membership.institution_id:
            raise ValidationError({"primary_campus": "Campus must belong to the membership institution."})

    @property
    def full_name(self):
        return " ".join(
            part
            for part in [
                self.first_name,
                self.middle_name,
                self.last_name,
            ]
            if part
        )


class Enrollment(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="student_enrollments",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="student_enrollments",
    )

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name="student_enrollments",
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name="student_enrollments",
    )

    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("withdrawn", "Withdrawn"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    enrollment_date = models.DateField(
        auto_now_add=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student__first_name", "student__last_name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "academic_year",
                ],
                name="unique_student_per_academic_year",
            )
        ]

    def clean(self):
        errors = {}

        # ---------------------------------------------------------
        # 1. Make sure the selected class belongs to the campus
        # ---------------------------------------------------------
        if self.campus_id and self.class_obj_id:
            if self.class_obj.unit.campus_id != self.campus_id:
                errors["class_obj"] = (
                    "The selected class does not belong to the selected campus."
                )

        # ---------------------------------------------------------
        # 2. Make sure the selected section belongs to the class
        # ---------------------------------------------------------
        if self.class_obj_id and self.section_id:
            if self.section.class_obj_id != self.class_obj_id:
                errors["section"] = (
                    "The selected section does not belong to the selected class."
                )

        # ---------------------------------------------------------
        # 3. Make sure Academic Year belongs to the same school
        #    as the selected campus
        # ---------------------------------------------------------
        if self.academic_year_id and self.campus_id:
            if self.academic_year.school_id != self.campus.school_id:
                errors["academic_year"] = (
                    "The selected academic year does not belong "
                    "to the selected campus's school."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.student.full_name} - "
            f"{self.academic_year.name} - "
            f"{self.class_obj.name} - "
            f"{self.section.name}"
        )


class StudentDocument(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    DOCUMENT_TYPE_CHOICES = [
        ("birth_certificate", "Birth Certificate"),
        ("b_form", "B-Form / CNIC"),
        ("report_card", "Report Card"),
        ("transfer_certificate", "Transfer Certificate"),
        ("fee_challan", "Fee Challan"),
        ("medical", "Medical Record"),
        ("other", "Other"),
    ]

    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
    )

    title = models.CharField(max_length=200)
    file = models.FileField(
        upload_to="students/documents/",
    )
    notes = models.TextField(blank=True)

    uploaded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_student_documents",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.admission_number} - {self.title}"

