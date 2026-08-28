from datetime import date

from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import StaffProfile
from apps.schools.models import Campus, School
from apps.teachers.models import Teacher


class Department(models.Model):
    """Organizational department within an institution/campus."""

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="departments"
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="departments"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    head = models.ForeignKey(
        "Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_departments"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_departments"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        default="active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_department_code_per_institution"
            ),
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="unique_department_name_per_institution"
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        errors = {}
        if self.campus_id and self.campus.school_id != self.institution_id:
            errors["campus"] = "Campus must belong to the institution."
        if self.head_id and self.head.institution_id != self.institution_id:
            errors["head"] = "Department head must belong to the same institution."
        if self.parent_id and self.parent.institution_id != self.institution_id:
            errors["parent"] = "Parent department must belong to the same institution."
        if self.parent_id and self.parent_id == self.id:
            errors["parent"] = "A department cannot be its own parent."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Designation(models.Model):
    """Job designation/title within an institution."""

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="designations"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="designations"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    level = models.PositiveSmallIntegerField(
        default=1,
        help_text="Hierarchy level (1=entry, higher=senior)"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        default="active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["level", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_designation_code_per_institution"
            ),
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="unique_designation_name_per_institution"
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        errors = {}
        if self.department_id and self.department.institution_id != self.institution_id:
            errors["department"] = "Designation's department must belong to the same institution."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Employee(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("on_leave", "On leave"),
        ("inactive", "Inactive"),
        ("resigned", "Resigned"),
        ("terminated", "Terminated"),
        ("probation", "Probation"),
        ("suspended", "Suspended"),
        ("retired", "Retired"),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ("permanent", "Permanent"),
        ("contract", "Contract"),
        ("temporary", "Temporary"),
        ("part_time", "Part-time"),
        ("intern", "Intern"),
        ("probationary", "Probationary"),
    ]

    institution = models.ForeignKey(School, on_delete=models.CASCADE, related_name="employees")
    teacher = models.OneToOneField(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_record")
    staff_profile = models.OneToOneField(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_record")
    employee_number = models.CharField(max_length=50)
    primary_campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employees"
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employees"
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default="permanent"
    )
    joining_date = models.DateField(null=True, blank=True)
    confirmation_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates"
    )
    employee_number = models.CharField(max_length=50)
    primary_campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
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
        if self.department_id and self.department.institution_id != self.institution_id:
            errors["department"] = "Department must belong to the institution."
        if self.designation_id and self.designation.institution_id != self.institution_id:
            errors["designation"] = "Designation must belong to the institution."
        if self.manager_id and self.manager.institution_id != self.institution_id:
            errors["manager"] = "Manager must belong to the same institution."
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
    contract_number = models.CharField(max_length=50)
    contract_type = models.CharField(max_length=50, default="Permanent")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    terms = models.TextField(blank=True)
    document = models.FileField(upload_to="hr/contracts/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=[("draft", "Draft"), ("active", "Active"), ("expired", "Expired"), ("terminated", "Terminated")], default="draft")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "contract_number"], name="unique_contract_number_per_employee"),
        ]

    def clean(self):
        errors = {}
        if self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "End date must be on or after the start date."
        if self.salary < 0:
            errors["salary"] = "Salary cannot be negative."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class EmployeeDocument(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="hr/documents/")
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    uploaded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_employee_documents")
    created_at = models.DateTimeField(auto_now_add=True)


class WorkloadAssignment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="workload_assignments")
    academic_year = models.ForeignKey("schools.AcademicYear", on_delete=models.PROTECT, related_name="employee_workloads")
    title = models.CharField(max_length=200)
    weekly_periods = models.PositiveSmallIntegerField(default=0)
    hours_per_week = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[("active", "Active"), ("completed", "Completed")], default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.hours_per_week < 0:
            raise ValidationError({"hours_per_week": "Hours cannot be negative."})


class PerformanceReview(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="performance_reviews")
    reviewer = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="employee_reviews")
    review_date = models.DateField(default=date.today)
    period = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField()
    strengths = models.TextField(blank=True)
    improvements = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[("draft", "Draft"), ("final", "Final")], default="draft")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not 1 <= self.rating <= 5:
            raise ValidationError({"rating": "Rating must be between 1 and 5."})


class EmploymentEvent(models.Model):
    EVENT_CHOICES = [("joined", "Joined"), ("transferred", "Transferred"), ("promoted", "Promoted"), ("resigned", "Resigned"), ("terminated", "Terminated"), ("status_changed", "Status changed")]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="employment_events")
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    effective_date = models.DateField(default=date.today)
    from_campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name="employment_events_from")
    to_campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name="employment_events_to")
    previous_designation = models.CharField(max_length=100, blank=True)
    new_designation = models.CharField(max_length=100, blank=True)
    reason = models.TextField(blank=True)
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="recorded_employment_events")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-effective_date", "-created_at"]


class LeaveType(models.Model):
    """Types of leave available in the institution."""

    CATEGORY_CHOICES = [
        ("annual", "Annual Leave"),
        ("sick", "Sick Leave"),
        ("casual", "Casual Leave"),
        ("maternity", "Maternity Leave"),
        ("paternity", "Paternity Leave"),
        ("emergency", "Emergency Leave"),
        ("study", "Study Leave"),
        ("unpaid", "Unpaid Leave"),
        ("compensatory", "Compensatory Off"),
        ("other", "Other"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="leave_types"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    requires_document = models.BooleanField(default=False)
    max_days_per_year = models.PositiveSmallIntegerField(null=True, blank=True)
    max_consecutive_days = models.PositiveSmallIntegerField(null=True, blank=True)
    carry_forward = models.BooleanField(default=False)
    max_carry_forward_days = models.PositiveSmallIntegerField(default=0)
    gender_specific = models.CharField(
        max_length=10,
        choices=[("", "All"), ("male", "Male"), ("female", "Female")],
        blank=True,
        default=""
    )
    min_service_months = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[("active", "Active"), ("inactive", "Inactive")],
        default="active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_leave_type_code_per_institution"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        errors = {}
        if self.max_consecutive_days and self.max_days_per_year and self.max_consecutive_days > self.max_days_per_year:
            errors["max_consecutive_days"] = "Max consecutive days cannot exceed max days per year."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class LeavePolicy(models.Model):
    """Leave policy configuration for an institution/department."""

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="leave_policies"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="leave_policies"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="policies"
    )
    eligibility_months = models.PositiveSmallIntegerField(default=0)
    accrual_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Days accrued per month"
    )
    max_accumulation = models.PositiveSmallIntegerField(default=0)
    probation_leave_allowed = models.BooleanField(default=False)
    notice_days = models.PositiveSmallIntegerField(default=1)
    approval_hierarchy = models.JSONField(
        default=list,
        blank=True,
        help_text="List of role codes for approval chain"
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("active", "Active"), ("inactive", "Inactive")],
        default="active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_from"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "department", "leave_type", "effective_from"],
                name="unique_leave_policy_per_dept"
            ),
        ]

    def __str__(self):
        dept = f" - {self.department.name}" if self.department else ""
        return f"{self.leave_type.name}{dept} Policy"

    def clean(self):
        errors = {}
        if self.department_id and self.department.institution_id != self.institution_id:
            errors["department"] = "Department must belong to the institution."
        if self.leave_type_id and self.leave_type.institution_id != self.institution_id:
            errors["leave_type"] = "Leave type must belong to the institution."
        if self.effective_to and self.effective_to < self.effective_from:
            errors["effective_to"] = "Effective to must be on or after effective from."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class LeaveBalance(models.Model):
    """Current leave balance for an employee."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_balances"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="balances"
    )
    academic_year = models.ForeignKey(
        "schools.AcademicYear",
        on_delete=models.CASCADE,
        related_name="leave_balances"
    )
    opening_balance = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    accrued = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    used = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    pending = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    carried_forward = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    adjusted = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    last_accrual_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-academic_year", "leave_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "leave_type", "academic_year"],
                name="unique_leave_balance_per_employee_per_year"
            ),
        ]

    @property
    def available_balance(self):
        return self.opening_balance + self.accrued + self.carried_forward + self.adjusted - self.used - self.pending

    def __str__(self):
        return f"{self.employee} - {self.leave_type}: {self.available_balance} days"

    def clean(self):
        errors = {}
        if self.employee_id and self.leave_type_id:
            if self.employee.institution_id != self.leave_type.institution_id:
                errors["leave_type"] = "Leave type must belong to the same institution as employee."
        if self.academic_year_id and self.employee_id:
            if self.academic_year.school_id != self.employee.institution_id:
                errors["academic_year"] = "Academic year must belong to the employee's institution."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class LeaveRequest(models.Model):
    """Employee leave request."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_requests"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="requests"
    )
    leave_policy = models.ForeignKey(
        LeavePolicy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requests"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    half_day = models.BooleanField(default=False)
    half_day_session = models.CharField(
        max_length=10,
        choices=[("morning", "Morning"), ("afternoon", "Afternoon")],
        blank=True
    )
    total_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    reason = models.TextField()
    attachment = models.FileField(upload_to="hr/leave/", blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )
    applied_on = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_leave_requests"
    )
    reviewed_on = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leave_requests"
    )
    approved_on = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_leave_requests"
    )
    rejected_on = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_leave_requests"
    )
    cancelled_on = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_on"]
        indexes = [
            models.Index(fields=["employee", "status", "start_date"]),
            models.Index(fields=["leave_type", "start_date", "end_date"]),
        ]

    def __str__(self):
        return f"{self.employee} - {self.leave_type}: {self.start_date} to {self.end_date} ({self.status})"

    def clean(self):
        errors = {}
        if self.end_date < self.start_date:
            errors["end_date"] = "End date must be on or after start date."
        if self.employee_id and self.leave_type_id:
            if self.employee.institution_id != self.leave_type.institution_id:
                errors["leave_type"] = "Leave type must belong to the same institution as employee."
        if self.leave_policy_id:
            if self.leave_policy.leave_type_id != self.leave_type_id:
                errors["leave_policy"] = "Leave policy must match the leave type."
            if self.employee_id and self.leave_policy.department_id:
                if self.employee.department_id != self.leave_policy.department_id:
                    errors["leave_policy"] = "Leave policy must match employee's department."
        if self.half_day and not self.half_day_session:
            errors["half_day_session"] = "Session is required for half day leave."
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors["start_date"] = "Start date must be before end date."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.total_days:
            self.calculate_total_days()
        super().save(*args, **kwargs)

    def calculate_total_days(self):
        """Calculate total leave days based on start and end date."""
        from datetime import timedelta
        delta = self.end_date - self.start_date
        self.total_days = delta.days + 1
        if self.half_day:
            self.total_days = self.total_days - 0.5

    def approve(self, user, comments=""):
        from apps.audit.models import record_audit
        self.status = "approved"
        self.approved_by = user
        self.approved_on = date.today()
        self.review_comments = comments
        self.save(update_fields=["status", "approved_by", "approved_on", "review_comments"])
        record_audit(
            request=None,
            user=user,
            action="approve",
            model_name="LeaveRequest",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "leave_approved", "comments": comments}
        )

    def reject(self, user, reason):
        from apps.audit.models import record_audit
        self.status = "rejected"
        self.rejected_by = user
        self.rejected_on = date.today()
        self.rejection_reason = reason
        self.save(update_fields=["status", "rejected_by", "rejected_on", "rejection_reason"])
        record_audit(
            request=None,
            user=user,
            action="reject",
            model_name="LeaveRequest",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "leave_rejected", "reason": reason}
        )

    def cancel(self, user, reason=""):
        from apps.audit.models import record_audit
        self.status = "cancelled"
        self.cancelled_by = user
        self.cancelled_on = date.today()
        self.cancellation_reason = reason
        self.save(update_fields=["status", "cancelled_by", "cancelled_on", "cancellation_reason"])
        record_audit(
            request=None,
            user=user,
            action="cancel",
            model_name="LeaveRequest",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "leave_cancelled", "reason": reason}
        )


class Allowance(models.Model):
    """Configurable allowance types."""

    CALCULATION_CHOICES = [
        ("fixed", "Fixed Amount"),
        ("percent_basic", "Percentage of Basic"),
        ("percent_gross", "Percentage of Gross"),
        ("per_day", "Per Day"),
        ("per_hour", "Per Hour"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="allowances"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_CHOICES, default="fixed")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_taxable = models.BooleanField(default=True)
    is_fixed = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    applicable_to = models.JSONField(
        default=list,
        blank=True,
        help_text="List of designation codes this allowance applies to"
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_allowance_code_per_institution"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        errors = {}
        if self.effective_to and self.effective_to < self.effective_from:
            errors["effective_to"] = "Effective to must be on or after effective from."
        if self.calculation_type == "percent_basic" and self.percentage <= 0:
            errors["percentage"] = "Percentage must be greater than 0 for percentage-based calculation."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Deduction(models.Model):
    """Configurable deduction types."""

    CALCULATION_CHOICES = [
        ("fixed", "Fixed Amount"),
        ("percent_basic", "Percentage of Basic"),
        ("percent_gross", "Percentage of Gross"),
        ("percent_net", "Percentage of Net"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="deductions"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_CHOICES, default="fixed")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_mandatory = models.BooleanField(default=False)
    is_pre_tax = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    applicable_to = models.JSONField(
        default=list,
        blank=True,
        help_text="List of designation codes this deduction applies to"
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_deduction_code_per_institution"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        errors = {}
        if self.effective_to and self.effective_to < self.effective_from:
            errors["effective_to"] = "Effective to must be on or after effective from."
        if self.calculation_type in ["percent_basic", "percent_gross", "percent_net"] and self.percentage <= 0:
            errors["percentage"] = "Percentage must be greater than 0 for percentage-based calculation."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Bonus(models.Model):
    """Bonus configurations and records."""

    BONUS_TYPE_CHOICES = [
        ("performance", "Performance Bonus"),
        ("annual", "Annual Bonus"),
        ("festival", "Festival Bonus"),
        ("attendance", "Attendance Bonus"),
        ("referral", "Referral Bonus"),
        ("retention", "Retention Bonus"),
        ("project", "Project Bonus"),
        ("other", "Other"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="bonus_types"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    bonus_type = models.CharField(max_length=20, choices=BONUS_TYPE_CHOICES, default="performance")
    description = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    frequency = models.CharField(
        max_length=20,
        choices=[
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
        ],
        blank=True
    )
    calculation_method = models.CharField(
        max_length=20,
        choices=[
            ("fixed", "Fixed Amount"),
            ("percent_basic", "Percentage of Basic"),
            ("percent_gross", "Percentage of Gross"),
        ],
        default="fixed"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    eligibility_criteria = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_bonus_code_per_institution"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        errors = {}
        if self.effective_to and self.effective_to < self.effective_from:
            errors["effective_to"] = "Effective to must be on or after effective from."
        if self.calculation_method in ["percent_basic", "percent_gross"] and self.percentage <= 0:
            errors["percentage"] = "Percentage must be greater than 0 for percentage-based calculation."
        if self.is_recurring and not self.frequency:
            errors["frequency"] = "Frequency is required for recurring bonuses."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Overtime(models.Model):
    """Overtime records for employees."""

    OVERTIME_TYPE_CHOICES = [
        ("weekday", "Weekday"),
        ("weekend", "Weekend"),
        ("holiday", "Holiday"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="overtime_records"
    )
    date = models.DateField()
    overtime_type = models.CharField(max_length=20, choices=OVERTIME_TYPE_CHOICES)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    rate_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_overtime"
    )
    approved_on = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("paid", "Paid"),
        ],
        default="pending"
    )
    payroll_period = models.ForeignKey(
        "PayrollPeriod",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="overtime_records"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "employee"]
        indexes = [
            models.Index(fields=["employee", "date", "status"]),
        ]

    def __str__(self):
        return f"{self.employee} - {self.date}: {self.hours} hrs"

    def clean(self):
        errors = {}
        if self.hours <= 0:
            errors["hours"] = "Hours must be greater than 0."
        if self.rate_per_hour < 0:
            errors["rate_per_hour"] = "Rate per hour cannot be negative."
        if self.amount != (self.hours * self.rate_per_hour):
            errors["amount"] = "Amount must equal hours * rate_per_hour."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.amount:
            self.amount = self.hours * self.rate_per_hour
        super().save(*args, **kwargs)


class Loan(models.Model):
    """Employee loans with repayment tracking."""

    LOAN_TYPE_CHOICES = [
        ("personal", "Personal Loan"),
        ("housing", "Housing Loan"),
        ("vehicle", "Vehicle Loan"),
        ("education", "Education Loan"),
        ("medical", "Medical Loan"),
        ("emergency", "Emergency Loan"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("rejected", "Rejected"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="loans"
    )
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES, default="personal")
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    interest_type = models.CharField(
        max_length=20,
        choices=[
            ("flat", "Flat Rate"),
            ("reducing", "Reducing Balance"),
        ],
        default="reducing"
    )
    tenure_months = models.PositiveSmallIntegerField()
    installment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_installments = models.PositiveSmallIntegerField()
    paid_installments = models.PositiveSmallIntegerField(default=0)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    applied_on = models.DateField(auto_now_add=True)
    approved_on = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_loans"
    )
    disbursed_on = models.DateField(null=True, blank=True)
    first_installment_date = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    purpose = models.TextField(blank=True)
    documents = models.FileField(upload_to="hr/loans/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_on"]
        indexes = [
            models.Index(fields=["employee", "status"]),
        ]

    def __str__(self):
        return f"{self.employee} - {self.loan_type}: {self.principal_amount}"

    def clean(self):
        errors = {}
        if self.principal_amount <= 0:
            errors["principal_amount"] = "Principal amount must be greater than 0."
        if self.interest_rate < 0:
            errors["interest_rate"] = "Interest rate cannot be negative."
        if self.tenure_months <= 0:
            errors["tenure_months"] = "Tenure must be greater than 0."
        if self.installment_amount <= 0:
            errors["installment_amount"] = "Installment amount must be greater than 0."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.remaining_balance:
            self.remaining_balance = self.principal_amount
        super().save(*args, **kwargs)

    def record_payment(self, amount, user):
        from apps.audit.models import record_audit
        self.paid_installments += 1
        self.remaining_balance -= amount
        if self.remaining_balance <= 0:
            self.remaining_balance = 0
            self.status = "completed"
        elif self.paid_installments >= self.total_installments:
            self.status = "completed"
        self.save(update_fields=["paid_installments", "remaining_balance", "status"])
        record_audit(
            request=None,
            user=user,
            action="update",
            model_name="Loan",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "loan_payment", "amount": str(amount)}
        )


class Advance(models.Model):
    """Salary advances."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("rejected", "Rejected"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="advances"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    requested_on = models.DateField(auto_now_add=True)
    approved_on = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_advances"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    repayment_method = models.CharField(
        max_length=20,
        choices=[
            ("lump_sum", "Lump Sum"),
            ("installments", "Installments"),
        ],
        default="installments"
    )
    number_of_installments = models.PositiveSmallIntegerField(default=1)
    installment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rejection_reason = models.TextField(blank=True)
    purpose = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-requested_on"]
        indexes = [
            models.Index(fields=["employee", "status"]),
        ]

    def __str__(self):
        return f"{self.employee} - Advance: {self.amount}"

    def clean(self):
        errors = {}
        if self.amount <= 0:
            errors["amount"] = "Advance amount must be greater than 0."
        if self.number_of_installments <= 0:
            errors["number_of_installments"] = "Number of installments must be greater than 0."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.remaining_balance:
            self.remaining_balance = self.amount
        if not self.installment_amount and self.number_of_installments > 0:
            self.installment_amount = self.amount / self.number_of_installments
        super().save(*args, **kwargs)


class SalaryRevision(models.Model):
    """Salary revision history."""

    REVISION_TYPE_CHOICES = [
        ("increment", "Increment"),
        ("promotion", "Promotion"),
        ("adjustment", "Adjustment"),
        ("correction", "Correction"),
        ("decrement", "Decrement"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="salary_revisions"
    )
    revision_type = models.CharField(max_length=20, choices=REVISION_TYPE_CHOICES)
    previous_basic = models.DecimalField(max_digits=12, decimal_places=2)
    new_basic = models.DecimalField(max_digits=12, decimal_places=2)
    previous_gross = models.DecimalField(max_digits=12, decimal_places=2)
    new_gross = models.DecimalField(max_digits=12, decimal_places=2)
    effective_date = models.DateField()
    reason = models.TextField()
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_salary_revisions"
    )
    approved_on = models.DateTimeField(null=True, blank=True)
    effective_from = models.DateField()
    document = models.FileField(upload_to="hr/salary_revisions/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_date"]
        indexes = [
            models.Index(fields=["employee", "effective_date"]),
        ]

    def __str__(self):
        return f"{self.employee} - {self.revision_type}: {self.previous_basic} → {self.new_basic}"

    def clean(self):
        errors = {}
        if self.new_basic < 0:
            errors["new_basic"] = "New basic salary cannot be negative."
        if self.effective_from > date.today():
            # Allow future effective dates
            pass
        if self.effective_from and self.effective_date and self.effective_date > self.effective_from:
            errors["effective_date"] = "Approval date cannot be after effective date."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class PayrollPeriod(models.Model):
    """Payroll periods for processing."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("open", "Open for Processing"),
        ("processing", "Processing"),
        ("calculated", "Calculated"),
        ("pending_approval", "Pending Approval"),
        ("approved", "Approved"),
        ("paid", "Paid"),
        ("closed", "Closed"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="payroll_periods"
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payroll_periods"
    )
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    payment_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    processed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_payroll_periods"
    )
    processed_on = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payroll_periods"
    )
    approved_on = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_payroll_periods"
    )
    closed_on = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "campus", "start_date", "end_date"],
                name="unique_payroll_period_per_campus"
            ),
        ]

    def __str__(self):
        campus_str = f" - {self.campus.name}" if self.campus else ""
        return f"{self.name}{campus_str} ({self.start_date} to {self.end_date})"

    def clean(self):
        errors = {}
        if self.end_date < self.start_date:
            errors["end_date"] = "End date must be on or after start date."
        if self.payment_date < self.end_date:
            errors["payment_date"] = "Payment date must be on or after end date."
        if self.campus_id and self.campus.school_id != self.institution_id:
            errors["campus"] = "Campus must belong to the institution."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def open_for_processing(self, user):
        from apps.audit.models import record_audit
        self.status = "open"
        self.save(update_fields=["status"])
        record_audit(
            request=None,
            user=user,
            action="update",
            model_name="PayrollPeriod",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "period_opened"}
        )

    def approve(self, user):
        from apps.audit.models import record_audit
        self.status = "approved"
        self.approved_by = user
        self.approved_on = date.today()
        self.save(update_fields=["status", "approved_by", "approved_on"])
        record_audit(
            request=None,
            user=user,
            action="approve",
            model_name="PayrollPeriod",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "period_approved"}
        )

    def close(self, user):
        from apps.audit.models import record_audit
        self.status = "closed"
        self.closed_by = user
        self.closed_on = date.today()
        self.save(update_fields=["status", "closed_by", "closed_on"])
        record_audit(
            request=None,
            user=user,
            action="update",
            model_name="PayrollPeriod",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "period_closed"}
        )


class ExitClearance(models.Model):
    """Employee exit clearance process."""

    CLEARANCE_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("cleared", "Cleared"),
        ("blocked", "Blocked"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="exit_clearances"
    )
    resignation = models.ForeignKey(
        "EmploymentEvent",
        on_delete=models.CASCADE,
        related_name="clearances",
        null=True,
        blank=True
    )
    initiated_on = models.DateField(auto_now_add=True)
    expected_completion = models.DateField()
    completed_on = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=CLEARANCE_STATUS_CHOICES,
        default="pending"
    )
    initiated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="initiated_clearances"
    )
    completed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_clearances"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-initiated_on"]

    def __str__(self):
        return f"Clearance for {self.employee} - {self.status}"


class ClearanceItem(models.Model):
    """Individual clearance items for exit clearance."""

    DEPARTMENT_CHOICES = [
        ("hr", "HR"),
        ("finance", "Finance"),
        ("library", "Library"),
        ("it", "IT"),
        ("administration", "Administration"),
        ("transport", "Transport"),
        ("inventory", "Inventory"),
        ("security", "Security"),
        ("hostel", "Hostel"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("cleared", "Cleared"),
        ("blocked", "Blocked"),
        ("not_applicable", "Not Applicable"),
    ]

    clearance = models.ForeignKey(
        ExitClearance,
        on_delete=models.CASCADE,
        related_name="items"
    )
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    department_name = models.CharField(max_length=100)
    responsible_person = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responsible_clearances"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    outstanding_items = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    cleared_on = models.DateTimeField(null=True, blank=True)
    cleared_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cleared_items"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["department"]

    def __str__(self):
        return f"{self.clearance} - {self.department_name}: {self.status}"

    def clear(self, user, remarks=""):
        from apps.audit.models import record_audit
        self.status = "cleared"
        self.cleared_on = date.today()
        self.cleared_by = user
        self.remarks = remarks
        self.save(update_fields=["status", "cleared_on", "cleared_by", "remarks"])
        record_audit(
            request=None,
            user=user,
            action="update",
            model_name="ClearanceItem",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "item_cleared", "department": self.department_name}
        )


class JobPosition(models.Model):
    """Job positions for recruitment."""

    EMPLOYMENT_TYPE_CHOICES = [
        ("permanent", "Permanent"),
        ("contract", "Contract"),
        ("temporary", "Temporary"),
        ("part_time", "Part-time"),
        ("intern", "Intern"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="job_positions"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="job_positions"
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.PROTECT,
        related_name="job_positions"
    )
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    qualifications = models.TextField(blank=True)
    experience_required = models.PositiveSmallIntegerField(default=0)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default="permanent")
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vacancies = models.PositiveSmallIntegerField(default=1)
    location = models.CharField(max_length=200, blank=True)
    is_remote = models.BooleanField(default=False)
    posted_on = models.DateField(auto_now_add=True)
    closes_on = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
            ("filled", "Filled"),
        ],
        default="draft"
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_job_positions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-posted_on"]

    def __str__(self):
        return f"{self.title} ({self.code})"


class Candidate(models.Model):
    """Job candidates."""

    SOURCE_CHOICES = [
        ("portal", "Job Portal"),
        ("referral", "Employee Referral"),
        ("walk_in", "Walk-in"),
        ("agency", "Recruitment Agency"),
        ("social_media", "Social Media"),
        ("website", "Company Website"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("applied", "Applied"),
        ("screening", "Screening"),
        ("shortlisted", "Shortlisted"),
        ("interview", "Interview Scheduled"),
        ("selected", "Selected"),
        ("rejected", "Rejected"),
        ("hired", "Hired"),
        ("withdrawn", "Withdrawn"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="candidates"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    current_organization = models.CharField(max_length=200, blank=True)
    current_designation = models.CharField(max_length=100, blank=True)
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    current_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notice_period_days = models.PositiveSmallIntegerField(null=True, blank=True)
    resume = models.FileField(upload_to="hr/candidates/resumes/", blank=True, null=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="other")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applied")
    applied_position = models.ForeignKey(
        JobPosition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidates"
    )
    applied_on = models.DateTimeField(auto_now_add=True)
    screened_on = models.DateTimeField(null=True, blank=True)
    screened_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="screened_candidates"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_on"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.status}"


class Application(models.Model):
    """Job applications."""

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    position = models.ForeignKey(
        JobPosition,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    applied_on = models.DateTimeField(auto_now_add=True)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("submitted", "Submitted"),
            ("under_review", "Under Review"),
            ("shortlisted", "Shortlisted"),
            ("rejected", "Rejected"),
            ("withdrawn", "Withdrawn"),
        ],
        default="submitted"
    )
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_applications"
    )
    reviewed_on = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_on"]

    def __str__(self):
        return f"{self.candidate} - {self.position}"


class Interview(models.Model):
    """Interview scheduling and feedback."""

    TYPE_CHOICES = [
        ("phone", "Phone Screening"),
        ("video", "Video Interview"),
        ("in_person", "In-Person"),
        ("technical", "Technical Assessment"),
        ("hr", "HR Interview"),
        ("final", "Final Round"),
    ]

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled"),
        ("no_show", "No Show"),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="interviews"
    )
    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    round_number = models.PositiveSmallIntegerField(default=1)
    scheduled_on = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    interviewer = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conducted_interviews"
    )
    location = models.CharField(max_length=200, blank=True)
    meeting_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    feedback = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ("strong_hire", "Strong Hire"),
            ("hire", "Hire"),
            ("no_hire", "No Hire"),
            ("strong_no_hire", "Strong No Hire"),
        ],
        blank=True
    )
    conducted_on = models.DateTimeField(null=True, blank=True)
    scheduled_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_interviews"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_on"]

    def __str__(self):
        return f"Interview: {self.application.candidate} - {self.application.position}"