
from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import AcademicYear, Campus, Class, Section


class Guardian(models.Model):
    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="guardians",
        null=True,
        blank=True,
    )

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


class StudentGuardian(models.Model):
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="guardian_links",
    )
    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.CASCADE,
        related_name="guardian_links",
    )
    relationship = models.CharField(max_length=50)
    is_primary = models.BooleanField(default=False)
    can_pick_up = models.BooleanField(default=False)
    is_emergency_contact = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "guardian"],
                name="unique_student_guardian_link",
            )
        ]
        ordering = ["-is_primary", "guardian__name"]

    def __str__(self):
        return f"{self.student.full_name} - {self.guardian.name}"


class AdmissionApplication(models.Model):
    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="admission_applications_tenant",
        null=True,
        blank=True,
    )

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("under_review", "Under review"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
    ]

    application_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ("male", "Male"),
            ("female", "Female"),
        ],
    )
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="admission_applications",
    )
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    class_obj = models.ForeignKey(Class, on_delete=models.PROTECT)
    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_admission_applications",
    )
    review_notes = models.TextField(blank=True)
    student = models.OneToOneField(
        "Student",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admission_application",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        errors = {}
        if self.class_obj_id and self.campus_id:
            if self.class_obj.unit.campus_id != self.campus_id:
                errors["class_obj"] = "The selected class does not belong to the selected campus."
        if self.section_id and self.class_obj_id:
            if self.section.class_obj_id != self.class_obj_id:
                errors["section"] = "The selected section does not belong to the selected class."
        if self.academic_year_id and self.campus_id:
            if self.academic_year.school_id != self.campus.school_id:
                errors["academic_year"] = "The academic year does not belong to the selected school."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def applicant_name(self):
        return " ".join(part for part in [self.first_name, self.middle_name, self.last_name] if part)


class StudentLifecycleEvent(models.Model):
    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="student_lifecycle_events",
        null=True,
        blank=True,
    )

    EVENT_CHOICES = [
        ("activated", "Activated"),
        ("inactive", "Marked inactive"),
        ("withdrawn", "Withdrawn"),
        ("transferred", "Transferred"),
        ("graduated", "Graduated"),
    ]

    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="lifecycle_events",
    )
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    effective_date = models.DateField()
    reason = models.TextField(blank=True)
    from_campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lifecycle_events_from",
    )
    to_campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lifecycle_events_to",
    )
    from_enrollment = models.ForeignKey(
        "Enrollment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lifecycle_events_from",
    )
    to_enrollment = models.ForeignKey(
        "Enrollment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lifecycle_events_to",
    )
    recorded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_student_lifecycle_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-effective_date", "-created_at"]


class Student(models.Model):
    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="students",
        null=True,
        blank=True,
    )

    admission_number = models.CharField(
        max_length=50,
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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "admission_number"],
                name="unique_admission_number_per_institution",
            )
        ]

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

    roll_number = models.CharField(max_length=20, blank=True)

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
    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="student_documents",
        null=True,
        blank=True,
    )

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


class StudentLeaveRequest(models.Model):
    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="student_leave_requests",
        null=True,
        blank=True,
    )

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    requested_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="requested_student_leave",
    )
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_student_leave",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        errors = {}
        if self.end_date < self.start_date:
            errors["end_date"] = "End date must be on or after the start date."
        if not self.reason.strip():
            errors["reason"] = "A reason is required."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

