from django.db import models
from django.utils import timezone
from django.utils.text import slugify


STATUS_CHOICES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
]


class School(models.Model):
    """The institution/tenant model (kept as School for API compatibility)."""

    INSTITUTION_TYPE_CHOICES = [
        ("school", "School"),
        ("college", "College"),
        ("university", "University"),
    ]

    name = models.CharField(max_length=200)
    code = models.SlugField(max_length=50, unique=True, null=True, blank=True)
    institution_type = models.CharField(
        max_length=20,
        choices=INSTITUTION_TYPE_CHOICES,
        default="school",
    )
    timezone = models.CharField(max_length=64, default="UTC")
    currency = models.CharField(max_length=3, default="PKR")
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("archived", "Archived"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    is_paused = models.BooleanField(
        default=False,
        help_text="Pause all operations for this school (login, attendance, fees, etc.)",
    )

    paused_at = models.DateTimeField(null=True, blank=True)
    paused_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paused_schools",
    )

    custom_domain = models.CharField(
        max_length=255,
        blank=True,
        unique=True,
        null=True,
        help_text="Custom domain for this school (e.g., school.example.com). "
                    "Used for domain-based tenant resolution.",
    )

    enabled_modules = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "List of enabled module keys from schools.modules.ALL_MODULES. "
            "An empty list means ALL modules are enabled (backwards "
            "compatible default)."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            base = slugify(self.name)[:40] or "school"
            candidate = base

            suffix = 2

            while type(self).objects.filter(code=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base[:40 - len(str(suffix)) - 1]}-{suffix}"
                suffix += 1

            self.code = candidate

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def pause(self, user):
        """Pause the school - prevents login, attendance, fees, etc."""
        from django.utils import timezone
        self.is_paused = True
        self.paused_at = timezone.now()
        self.paused_by = user
        self.save(update_fields=["is_paused", "paused_at", "paused_by"])

    def activate(self):
        """Activate the school - resume all operations."""
        self.is_paused = False
        self.paused_at = None
        self.paused_by = None
        self.save(update_fields=["is_paused", "paused_at", "paused_by"])

    def archive(self, user):
        """Archive the school - sets status to archived."""
        self.status = "archived"
        self.is_paused = True
        self.paused_at = timezone.now()
        self.paused_by = user
        self.save(update_fields=["status", "is_paused", "paused_at", "paused_by"])

    def unarchive(self):
        """Unarchive the school - sets status back to active."""
        self.status = "active"
        self.is_paused = False
        self.paused_at = None
        self.paused_by = None
        self.save(update_fields=["status", "is_paused", "paused_at", "paused_by"])

    def is_operational(self):
        """Check if school is operational (not paused or archived)."""
        return self.status == "active" and not self.is_paused


class Campus(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="campuses",
    )
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.name} - {self.name}"


class AcademicUnit(models.Model):
    campus = models.ForeignKey(
        Campus,
        on_delete=models.CASCADE,
        related_name="academic_units",
    )
    name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Academic Units"

    def __str__(self):
        return self.name


class Class(models.Model):
    unit = models.ForeignKey(
        AcademicUnit,
        on_delete=models.CASCADE,
        related_name="classes",
    )
    name = models.CharField(max_length=100)
    level = models.IntegerField(null=True, blank=True)

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["level", "name"]

    def __str__(self):
        return self.name


class Section(models.Model):
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(default=30)

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["class_obj__name", "name"]

    def __str__(self):
        return self.name


class AcademicYear(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="academic_years",
    )
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()

    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("active", "Active"),
        ("completed", "Completed"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_school_year",
            ),
        ]

    def __str__(self):
        return self.name


class Term(models.Model):
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="terms",
    )
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("active", "Active"),
        ("completed", "Completed"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_date"]

    def __str__(self):
        return self.name


class Subject(models.Model):
    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="subjects",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    subject_type = models.CharField(
        max_length=20,
        choices=[("theory", "Theory"), ("practical", "Practical")],
        default="theory",
    )
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    practical_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_subject_code_per_institution",
            ),
        ]

    def __str__(self):
        return self.name


class SubjectOffering(models.Model):
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="subject_offerings",
    )
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name="subject_offerings",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="subject_offerings",
    )
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.PROTECT,
        related_name="subject_offerings",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["class_obj__name", "subject__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "class_obj", "subject"],
                name="unique_subject_offering_per_class_per_year",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}

        if self.class_obj_id:
            class_school = self.class_obj.unit.campus.school
            if self.subject_id and self.subject.institution_id != class_school.pk:
                errors["subject"] = (
                    "Subject must belong to the same school as the class."
                )

            if self.teacher_id:
                teacher_school = self.teacher.primary_campus.school
                if teacher_school.pk != class_school.pk:
                    errors["teacher"] = "Teacher must belong to the same school."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.subject.name} ({self.class_obj.name})"


class SchoolSettings(models.Model):
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="settings",
    )
    logo = models.ImageField(upload_to="school/branding/", blank=True, null=True)
    favicon = models.ImageField(upload_to="school/branding/", blank=True, null=True)
    primary_color = models.CharField(max_length=7, default="#1a73e8")
    secondary_color = models.CharField(max_length=7, default="#34a853")
    accent_color = models.CharField(max_length=7, default="#fbbc04")
    motto = models.CharField(max_length=300, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_website = models.URLField(blank=True)
    address_line = models.TextField(blank=True)
    footer_text = models.TextField(blank=True)
    sidebar_color = models.CharField(max_length=7, blank=True)
    header_color = models.CharField(max_length=7, blank=True)
    login_background = models.ImageField(
        upload_to="school/branding/", blank=True, null=True
    )

    SHORT_NAME_HELP = "Compact name used in tight UI spaces."
    short_name = models.CharField(max_length=50, blank=True, help_text=SHORT_NAME_HELP)

    DATE_FORMAT_CHOICES = [
        ("dd-mm-yyyy", "31-12-2026"),
        ("dd MMM yyyy", "31 Dec 2026"),
        ("mm/dd/yyyy", "12/31/2026"),
        ("yyyy-mm-dd", "2026-12-31"),
    ]
    date_format = models.CharField(
        max_length=20,
        choices=DATE_FORMAT_CHOICES,
        default="dd-mm-yyyy",
    )

    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("ur", "اردو"),
    ]
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default="en",
    )

    working_days = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "List of working day keys, e.g. "
            '["mon","tue","wed","thu","fri"]. Empty = Mon-Fri.'
        ),
    )

    email_from_name = models.CharField(
        max_length=120,
        blank=True,
        help_text="White-label display name on outgoing emails.",
    )
    email_from_address = models.EmailField(
        blank=True,
        help_text="Per-school from address override for outgoing emails.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


