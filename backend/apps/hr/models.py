from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import StaffProfile
from apps.schools.models import Campus, School
from apps.teachers.models import Teacher


class Employee(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("on_leave", "On leave"),
        ("inactive", "Inactive"),
        ("resigned", "Resigned"),
        ("terminated", "Terminated"),
    ]

    institution = models.ForeignKey(School, on_delete=models.CASCADE, related_name="employees")
    teacher = models.OneToOneField(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_record")
    staff_profile = models.OneToOneField(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_record")
    employee_number = models.CharField(max_length=50)
    primary_campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    designation = models.CharField(max_length=100, default="Staff")
    department = models.CharField(max_length=100, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee_number"]
        constraints = [
            models.UniqueConstraint(fields=["institution", "employee_number"], name="unique_employee_number_per_institution"),
        ]

    @property
    def full_name(self):
        profile = self.staff_profile or self.teacher
        return profile.full_name if profile else self.employee_number

    def clean(self):
        errors = {}
        if not self.teacher_id and not self.staff_profile_id:
            errors["teacher"] = "An employee must link to a teacher or staff profile."
        if self.teacher_id and self.staff_profile_id:
            errors["teacher"] = "An employee cannot link to both profile types."
        if self.primary_campus_id and self.primary_campus.school_id != self.institution_id:
            errors["primary_campus"] = "Campus must belong to the institution."
        profile = self.staff_profile or self.teacher
        if profile and getattr(profile, "membership_id", None) and profile.membership.institution_id != self.institution_id:
            errors["institution"] = "Employee profile must belong to the institution."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class EmploymentContract(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="contracts")
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employment_contracts",
        help_text="Campus where this contract applies (optional, defaults to employee's primary campus)",
    )
    contract_number = models.CharField(max_length=50)
    contract_type = models.CharField(max_length=50, default="Permanent")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    terms = models.TextField(blank=True)
    document = models.FileField(upload_to="hr/contracts/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=[("draft", "Draft"), ("active", "Active"), ("expired", "Expired"), ("terminated", "Terminated")], default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "contract_number"], name="unique_contract_number_per_employee"),
        ]
        indexes = [
            models.Index(
                fields=["employee", "status"],
                name="contract_emp_status_idx",
            ),
            models.Index(
                fields=["campus", "status"],
                name="contract_campus_status_idx",
            ),
        ]

    def clean(self):
        errors = {}
        if self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "End date must be on or after the start date."
        if self.salary < 0:
            errors["salary"] = "Salary cannot be negative."
        if self.campus_id and self.campus.school_id != self.employee.institution_id:
            errors["campus"] = "Campus must belong to the employee's institution."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class EmployeeDocument(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="documents")
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_documents",
    )
    document_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="hr/documents/")
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    uploaded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_employee_documents")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["employee", "document_type"],
                name="empdoc_emp_type_idx",
            ),
            models.Index(
                fields=["campus", "expiry_date"],
                name="empdoc_campus_expiry_idx",
            ),
        ]


class WorkloadAssignment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="workload_assignments")
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="workload_assignments",
    )
    academic_year = models.ForeignKey("schools.AcademicYear", on_delete=models.PROTECT, related_name="employee_workloads")
    title = models.CharField(max_length=200)
    weekly_periods = models.PositiveSmallIntegerField(default=0)
    hours_per_week = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[("active", "Active"), ("completed", "Completed")], default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["employee", "academic_year", "status"],
                name="workload_emp_year_status_idx",
            ),
            models.Index(
                fields=["campus", "academic_year"],
                name="workload_campus_year_idx",
            ),
        ]

    def clean(self):
        errors = {}
        if self.hours_per_week < 0:
            errors["hours_per_week"] = "Hours cannot be negative."
        if self.campus_id and self.campus.school_id != self.employee.institution_id:
            errors["campus"] = "Campus must belong to the employee's institution."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class PerformanceReview(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="performance_reviews")
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="performance_reviews",
    )
    reviewer = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="employee_reviews")
    review_date = models.DateField(default=date.today)
    period = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField()
    strengths = models.TextField(blank=True)
    improvements = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[("draft", "Draft"), ("final", "Final")], default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["employee", "review_date"],
                name="perfrev_emp_date_idx",
            ),
            models.Index(
                fields=["campus", "review_date"],
                name="perfrev_campus_date_idx",
            ),
        ]

    def clean(self):
        errors = {}
        if not 1 <= self.rating <= 5:
            errors["rating"] = "Rating must be between 1 and 5."
        if self.campus_id and self.campus.school_id != self.employee.institution_id:
            errors["campus"] = "Campus must belong to the employee's institution."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class EmploymentEvent(models.Model):
    EVENT_CHOICES = [("joined", "Joined"), ("transferred", "Transferred"), ("promoted", "Promoted"), ("resigned", "Resigned"), ("terminated", "Terminated"), ("status_changed", "Status changed")]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="employment_events")
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    effective_date = models.DateField(default=date.today)
    from_campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name="employment_events_from")
    to_campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name="employment_events_to")
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employment_events",
        help_text="Current campus for this event (for filtering)",
    )
    previous_designation = models.CharField(max_length=100, blank=True)
    new_designation = models.CharField(max_length=100, blank=True)
    reason = models.TextField(blank=True)
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="recorded_employment_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_date", "-created_at"]
        indexes = [
            models.Index(
                fields=["employee", "effective_date"],
                name="empevent_emp_date_idx",
            ),
            models.Index(
                fields=["campus", "effective_date"],
                name="empevent_campus_date_idx",
            ),
        ]