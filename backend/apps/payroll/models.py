from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.hr.models import Employee, Allowance, Deduction


class SalaryStructureComponent(models.Model):
    """Individual component of a salary structure (allowance or deduction)."""

    COMPONENT_TYPE_CHOICES = [
        ("allowance", "Allowance"),
        ("deduction", "Deduction"),
    ]

    CALCULATION_CHOICES = [
        ("fixed", "Fixed Amount"),
        ("percent_basic", "Percentage of Basic"),
        ("percent_gross", "Percentage of Gross"),
        ("percent_net", "Percentage of Net"),
        ("per_day", "Per Day"),
        ("per_hour", "Per Hour"),
    ]

    salary_structure = models.ForeignKey(
        "SalaryStructure",
        on_delete=models.CASCADE,
        related_name="components"
    )
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_CHOICES, default="fixed")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sequence = models.PositiveSmallIntegerField(default=0)
    applicable_to = models.JSONField(
        default=list,
        blank=True,
        help_text="List of designation codes this component applies to"
    )
    condition = models.TextField(blank=True, help_text="Python expression for conditional application")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sequence", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["salary_structure", "code"],
                name="unique_component_code_per_structure"
            ),
        ]

    def __str__(self):
        return f"{self.get_component_type_display()}: {self.name} ({self.code})"

    def calculate_amount(self, basic_salary, gross_salary, net_salary=0):
        """Calculate the component amount based on calculation type."""
        if self.calculation_type == "fixed":
            return self.amount
        elif self.calculation_type == "percent_basic":
            return (basic_salary * self.percentage) / Decimal("100")
        elif self.calculation_type == "percent_gross":
            return (gross_salary * self.percentage) / Decimal("100")
        elif self.calculation_type == "percent_net":
            return (net_salary * self.percentage) / Decimal("100")
        elif self.calculation_type == "per_day":
            return self.amount  # Per day calculation handled in payroll
        elif self.calculation_type == "per_hour":
            return self.amount  # Per hour calculation handled in payroll
        return Decimal("0")

    def clean(self):
        errors = {}
        if self.calculation_type in ["percent_basic", "percent_gross", "percent_net"] and self.percentage <= 0:
            errors["percentage"] = "Percentage must be greater than 0 for percentage-based calculation."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class SalaryStructure(models.Model):
    """The salary template for an employee: basic pay plus components."""

    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="salary_structures"
    )
    employee = models.ForeignKey(
        "hr.Employee",
        on_delete=models.CASCADE,
        related_name="salary_structures"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    effective_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=[
            ("active", "Active"),
            ("archived", "Archived"),
        ],
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_salary_structure_code_per_institution"
            ),
        ]
        indexes = [
            models.Index(
                fields=["employee", "status", "effective_date"],
                name="salstruct_emp_sts_date_idx",
            ),
        ]

    @property
    def total_allowances(self):
        total = Decimal("0")
        for component in self.components.filter(component_type="allowance", is_active=True):
            total += component.amount
        return total

    @property
    def total_deductions_components(self):
        total = Decimal("0")
        for component in self.components.filter(component_type="deduction", is_active=True):
            total += component.amount
        return total

    @property
    def gross_salary(self):
        return self.basic_salary + self.total_allowances

    def __str__(self):
        return f"{self.employee.full_name} - {self.code} ({self.effective_date})"

    def clean(self):
        errors = {}
        if self.basic_salary < 0:
            errors["basic_salary"] = "Basic salary cannot be negative."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class PayrollRecord(models.Model):
    """A monthly payroll record for one employee."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("processed", "Processed"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    employee = models.ForeignKey(
        "hr.Employee",
        on_delete=models.CASCADE,
        related_name="payroll_records"
    )
    campus = models.ForeignKey(
        "schools.Campus",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payroll_records",
        help_text="Campus where employee was assigned during this period",
    )
    salary_structure = models.ForeignKey(
        SalaryStructure,
        on_delete=models.PROTECT,
        related_name="payroll_records"
    )
    payroll_period = models.ForeignKey(
        "hr.PayrollPeriod",
        on_delete=models.PROTECT,
        related_name="payroll_records"
    )
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()

    working_days = models.PositiveSmallIntegerField(default=0)
    paid_days = models.PositiveSmallIntegerField(default=0)
    leave_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    gross_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    total_allowances = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    total_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    gross_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    net_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    component_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed breakdown of each component"
    )

    status = models.CharField(
        max_length=16,
        choices=[
            ("draft", "Draft"),
            ("processed", "Processed"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
    )

    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_payrolls"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payrolls"
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paid_payrolls"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month", "employee__employee_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "payroll_period"],
                name="unique_employee_payroll_period"
            ),
        ]
        indexes = [
            models.Index(
                fields=["campus", "year", "month", "status"],
                name="payroll_campus_ym_status_idx",
            ),
            models.Index(
                fields=["employee", "year", "month"],
                name="payroll_employee_ym_idx",
            ),
            models.Index(
                fields=["status", "year", "month"],
                name="payroll_status_ym_idx",
            ),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.year}/{self.month:02d} ({self.status})"

    def clean(self):
        errors = {}
        if not 1 <= self.month <= 12:
            errors["month"] = "Month must be between 1 and 12."
        if self.campus_id and self.campus.school_id != self.employee.institution_id:
            errors["campus"] = "Campus must belong to the employee's institution."
        if errors:
            raise ValidationError(errors)

    def compute(self):
        """Compute payroll based on salary structure and components."""
        # Get active components
        allowances = self.salary_structure.components.filter(
            component_type="allowance",
            is_active=True
        ).order_by("sequence")

        deductions = self.salary_structure.components.filter(
            component_type="deduction",
            is_active=True
        ).order_by("sequence")

        # Calculate allowances
        total_allowances = Decimal("0")
        component_details = {"allowances": {}, "deductions": {}}

        for component in allowances:
            amount = component.calculate_amount(
                self.basic_salary,
                self.basic_salary + self.gross_salary,  # gross_salary not yet calculated
                Decimal("0")
            )
            total_allowances += amount
            component_details["allowances"][component.code] = {
                "name": component.name,
                "amount": str(amount),
                "calculation_type": component.calculation_type,
                "is_taxable": component.is_taxable,
            }

        # Calculate gross earnings
        gross_earnings = self.basic_salary + total_allowances

        # Calculate deductions
        total_deductions = Decimal("0")
        for component in deductions:
            # For deduction calculation, use gross_salary as base
            gross_for_deduction = gross_earnings
            amount = component.calculate_amount(
                self.basic_salary,
                gross_earnings,
                gross_earnings  # net not yet calculated
            )
            total_deductions += amount
            component_details["deductions"][component.code] = {
                "name": component.name,
                "amount": str(amount),
                "calculation_type": component.calculation_type,
                "is_pre_tax": component.is_pre_tax if hasattr(component, 'is_pre_tax') else False,
            }

        # Update record
        self.total_allowances = total_allowances
        self.gross_earnings = gross_earnings
        self.total_deductions = total_deductions
        self.gross_salary = gross_earnings
        self.net_salary = gross_earnings - total_deductions
        self.component_details = component_details

    def save(self, *args, **kwargs):
        self.full_clean()
        self.compute()
        super().save(*args, **kwargs)

    def process(self, user):
        from apps.audit.models import record_audit
        if self.status == "paid":
            raise ValidationError({"status": "This payroll record has already been paid."})
        self.compute()
        self.status = "processed"
        self.processed_at = models.DateTimeField(auto_now=True)
        self.processed_by = user
        self.save()
        record_audit(
            request=None,
            user=user,
            action="update",
            model_name="PayrollRecord",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "payroll_processed"}
        )

    def approve(self, user):
        from apps.audit.models import record_audit
        if self.status not in ["processed", "draft"]:
            raise ValidationError({"status": "Payroll must be processed before approval."})
        self.status = "approved"
        self.approved_at = models.DateTimeField(auto_now=True)
        self.approved_by = user
        self.save(update_fields=["status", "approved_at", "approved_by"])
        from apps.audit.models import record_audit
        record_audit(
            request=None,
            user=user,
            action="approve",
            model_name="PayrollRecord",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "payroll_approved"}
        )

    def pay(self, user):
        from apps.audit.models import record_audit
        if self.status != "approved":
            raise ValidationError({"status": "Payroll must be approved before payment."})
        self.status = "paid"
        self.paid_at = models.DateTimeField(auto_now=True)
        self.paid_by = user
        self.save(update_fields=["status", "paid_at", "paid_by"])
        from apps.audit.models import record_audit
        record_audit(
            request=None,
            user=user,
            action="update",
            model_name="PayrollRecord",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"action": "payroll_paid"}
        )

    def __str__(self):
        return f"{self.employee.full_name} - {self.year}/{self.month:02d} ({self.status})"


class Payslip(models.Model):
    """The generated payslip document for a payroll record."""

    record = models.OneToOneField(
        PayrollRecord,
        on_delete=models.CASCADE,
        related_name="payslip"
    )
    document = models.FileField(
        upload_to="payslips/%Y/%m/",
        blank=True,
        null=True,
    )
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payslip {self.record}"


class SalaryComponentTemplate(models.Model):
    """Pre-defined salary component templates for quick structure creation."""

    COMPONENT_TYPE_CHOICES = [
        ("allowance", "Allowance"),
        ("deduction", "Deduction"),
    ]

    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="salary_component_templates"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    component_type = models.CharField(max_length=20, choices=[
        ("allowance", "Allowance"),
        ("deduction", "Deduction"),
    ])
    calculation_type = models.CharField(max_length=20, choices=[
        ("fixed", "Fixed Amount"),
        ("percent_basic", "Percentage of Basic"),
        ("percent_gross", "Percentage of Gross"),
        ("percent_net", "Percentage of Net"),
        ("per_day", "Per Day"),
        ("per_hour", "Per Hour"),
    ])
    default_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    default_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_component_template_code_per_institution"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"