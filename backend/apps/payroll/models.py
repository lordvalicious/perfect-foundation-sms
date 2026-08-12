from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class SalaryStructure(models.Model):
    """The salary template for a teacher: basic pay plus allowances."""

    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        related_name="salary_structures",
    )
    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    allowances = models.JSONField(
        default=dict,
        blank=True,
        help_text="Map of allowance names to amounts, e.g. "
        "{'housing': 25000, 'transport': 10000}.",
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

    @property
    def total_allowances(self):
        total = Decimal("0")

        for value in (self.allowances or {}).values():
            try:
                total += Decimal(str(value))
            except (TypeError, ValueError):
                continue

        return total

    @property
    def gross_salary(self):
        return self.basic_salary + self.total_allowances

    def __str__(self):
        return (
            f"{self.teacher.full_name} - "
            f"{self.effective_date} ({self.basic_salary})"
        )


class PayrollRecord(models.Model):
    """A monthly payroll record for one teacher."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("processed", "Processed"),
        ("paid", "Paid"),
    ]

    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        related_name="payroll_records",
    )
    structure = models.ForeignKey(
        SalaryStructure,
        on_delete=models.PROTECT,
        related_name="payroll_records",
    )
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()

    working_days = models.PositiveSmallIntegerField(default=0)
    paid_days = models.PositiveSmallIntegerField(default=0)

    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    allowances = models.JSONField(default=dict, blank=True)
    gross_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    deductions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Map of deduction names to amounts.",
    )
    total_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    net_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="draft",
    )

    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_payrolls",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month", "teacher__first_name"]

        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "month", "year"],
                name="unique_teacher_payroll_period",
            )
        ]

    def clean(self):
        if not 1 <= self.month <= 12:
            raise ValidationError(
                {"month": "Month must be between 1 and 12."}
            )

    def compute(self):
        self.basic_salary = self.structure.basic_salary
        self.allowances = self.structure.allowances or {}
        self.gross_salary = self.structure.gross_salary

        deductions = self.deductions or {}
        total = Decimal("0")

        for value in deductions.values():
            try:
                total += Decimal(str(value))
            except (TypeError, ValueError):
                continue

        self.total_deductions = total
        self.net_salary = self.gross_salary - total

    def save(self, *args, **kwargs):
        self.full_clean()
        self.compute()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.teacher.full_name} - "
            f"{self.year}/{self.month:02d} ({self.status})"
        )


class Payslip(models.Model):
    """The generated payslip document for a payroll record."""

    record = models.OneToOneField(
        PayrollRecord,
        on_delete=models.CASCADE,
        related_name="payslip",
    )
    document = models.FileField(
        upload_to="payslips/%Y/%m/",
        blank=True,
        null=True,
    )
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payslip {self.record}"
