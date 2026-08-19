
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import AcademicYear, Campus, Class
from apps.students.models import Enrollment, Student


class FeeCategory(models.Model):
    FREQUENCY_CHOICES = [
        ("one_time", "One Time"),
        ("monthly", "Monthly"),
        ("term", "Per Term"),
        ("annual", "Annual"),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default="monthly",
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

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class FeeStructure(models.Model):
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="fee_structures",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="fee_structures",
    )

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name="fee_structures",
    )

    category = models.ForeignKey(
        FeeCategory,
        on_delete=models.PROTECT,
        related_name="fee_structures",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    due_day = models.PositiveIntegerField(
        default=10,
        help_text="Day of month on which the fee is due.",
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

    class Meta:
        ordering = [
            "campus",
            "class_obj",
            "category",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "academic_year",
                    "campus",
                    "class_obj",
                    "category",
                ],
                name="unique_fee_structure",
            )
        ]

    def clean(self):
        errors = {}

        if self.class_obj_id and self.campus_id:
            if self.class_obj.unit.campus_id != self.campus_id:
                errors["class_obj"] = (
                    "Class must belong to the selected campus."
                )

        if self.academic_year_id and self.campus_id:
            if self.academic_year.school_id != self.campus.school_id:
                errors["academic_year"] = (
                    "Academic year must belong to the same school "
                    "as the campus."
                )

        if self.amount < Decimal("0"):
            errors["amount"] = "Amount cannot be negative."

        if not 1 <= self.due_day <= 31:
            errors["due_day"] = "Due day must be between 1 and 31."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.campus.name} - "
            f"{self.class_obj.name} - "
            f"{self.category.name} - "
            f"{self.amount}"
        )


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("issued", "Issued"),
        ("partial", "Partially Paid"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    issue_date = models.DateField()
    due_date = models.DateField()

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date", "-id"]

    @property
    def subtotal(self):
        return sum(
            (item.amount for item in self.items.all()),
            Decimal("0.00"),
        )

    @property
    def total_amount(self):
        total = self.subtotal - self.discount
        return max(total, Decimal("0.00"))

    @property
    def paid_amount(self):
        return sum(
            (
                payment.net_amount
                for payment in self.payments.filter(
                    status="completed"
                )
            ),
            Decimal("0.00"),
        )

    @property
    def balance(self):
        return max(
            self.total_amount - self.paid_amount,
            Decimal("0.00"),
        )

    def refresh_status(self, save=True):
        """
        Recalculate the invoice status from its payments.

        Called automatically whenever a payment on this invoice
        is created or updated.
        """
        total = self.total_amount
        paid = self.paid_amount

        if total <= 0 or paid >= total:
            new_status = "paid"
        elif paid > 0:
            new_status = "partial"
        elif self.due_date < date.today():
            new_status = "overdue"
        else:
            new_status = "issued"

        if new_status != self.status:
            self.status = new_status

            if save:
                self.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

    def clean(self):
        errors = {}

        if self.enrollment_id:
            enrollment = self.enrollment

            if self.student_id != enrollment.student_id:
                errors["student"] = (
                    "Student must match the enrollment."
                )

            if self.academic_year_id != enrollment.academic_year_id:
                errors["academic_year"] = (
                    "Academic year must match the enrollment."
                )

        if self.discount < Decimal("0"):
            errors["discount"] = "Discount cannot be negative."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.invoice_number} - "
            f"{self.student.full_name}"
        )


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )

    category = models.ForeignKey(
        FeeCategory,
        on_delete=models.PROTECT,
        related_name="invoice_items",
    )

    description = models.CharField(max_length=200)

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.amount < Decimal("0"):
            raise ValidationError(
                {"amount": "Amount cannot be negative."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} - {self.amount}"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("bank", "Bank Transfer"),
        ("jazzcash", "JazzCash"),
        ("easypaisa", "EasyPaisa"),
        ("card", "Card"),
        ("stripe", "Stripe (Online)"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("pending", "Pending"),
        ("cancelled", "Cancelled"),
    ]

    receipt_number = models.CharField(
        max_length=50,
        unique=True,
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    payment_date = models.DateField()

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="cash",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="completed",
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
    )

    notes = models.TextField(blank=True)

    stripe_session_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Stripe Checkout Session ID for online payments.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}

        if self.amount <= Decimal("0"):
            errors["amount"] = "Payment amount must be greater than zero."

        if self.invoice_id and self.amount > self.invoice.balance:
            errors["amount"] = (
                "Payment cannot be greater than the invoice balance."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        if self.status == "completed":
            self.invoice.refresh_status()

    @property
    def reversed_amount(self):
        return sum(
            (reversal.amount for reversal in self.reversals.filter(status="completed")),
            Decimal("0.00"),
        )

    @property
    def net_amount(self):
        return max(self.amount - self.reversed_amount, Decimal("0.00"))

    def __str__(self):
        return (
            f"{self.receipt_number} - "
            f"{self.invoice.student.full_name} - "
            f"{self.amount}"
        )


class PaymentReversal(models.Model):
    """An auditable correction to a completed payment; payments are never deleted."""

    STATUS_CHOICES = [("completed", "Completed"), ("cancelled", "Cancelled")]

    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="reversals")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reversal_date = models.DateField(default=date.today)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_reversals")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.amount <= Decimal("0.00"):
            raise ValidationError({"amount": "Reversal amount must be greater than zero."})
        prior = self.payment.reversed_amount
        if self.pk:
            prior -= self.amount
        if self.amount + prior > self.payment.amount:
            raise ValidationError({"amount": "Reversal cannot exceed the original payment."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.payment.invoice.refresh_status()

