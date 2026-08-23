from django.db import models


class School(models.Model):
    """The institution/tenant model (kept as School for API compatibility)."""

    INSTITUTION_TYPE_CHOICES = [
        ("school", "School"),
        ("college", "College"),
        ("university", "University"),
    ]

    name = models.CharField(max_length=200)
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
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


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

    UNIT_TYPE_CHOICES = [
        ("campus", "Campus"),
        ("school", "School"),
        ("section", "Section"),
        ("other", "Other"),
    ]

    unit_type = models.CharField(
        max_length=20,
        choices=UNIT_TYPE_CHOICES,
        default="school",
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.campus.name} - {self.name}"


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
        return f"{self.unit.name} - {self.name}"


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
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["class_obj", "name"],
                name="unique_section_per_class",
            )
        ]

    def __str__(self):
        return f"{self.class_obj.name} - {self.name}"


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
        default="upcoming",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_academic_year_per_school",
            )
        ]

    def __str__(self):
        return f"{self.school.name} - {self.name}"


class Term(models.Model):
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="terms",
    )
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "name"],
                name="unique_term_per_academic_year",
            )
        ]

    def __str__(self):
        return f"{self.academic_year.name} - {self.name}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    SUBJECT_TYPE_CHOICES = [
        ("general", "General"),
        ("science", "Science"),
        ("language", "Language"),
        ("religious", "Religious"),
        ("computer", "Computer"),
        ("social_science", "Social Science"),
        ("elective", "Elective"),
    ]

    subject_type = models.CharField(
        max_length=30,
        choices=SUBJECT_TYPE_CHOICES,
        default="general",
    )

    practical_required = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class SubjectOffering(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="offerings",
    )

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="subject_offerings",
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="subject_offerings",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "class_obj", "academic_year"],
                name="unique_subject_offering",
            )
        ]

    def __str__(self):
        return (
            f"{self.academic_year.name} - "
            f"{self.class_obj.name} - "
            f"{self.subject.name}"
        )



class SchoolSettings(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name="settings")
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.school.name}"