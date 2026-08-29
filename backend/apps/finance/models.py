
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.campus_validation import (
    CampusAssignmentValidationMixin,
    CampusValidationMixin,
)
from apps.core.models import SoftDeleteMixin, SoftDeleteManager
from apps.schools.models import AcademicYear, Campus, Class, School, Section
from apps.students.models import Enrollment, Student


class FeeCategory(SoftDeleteMixin):
    objects = SoftDeleteManager()

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="fee_categories",
        null=True,
        blank=True,
    )

    FREQUENCY_CHOICES = [
        ("one_time", "One Time"),
        ("monthly", "Monthly"),
        ("term", "Per Term"),
        ("annual", "Annual"),
    ]

    name = models.CharField(max_length=100)
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
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="unique_fee_category_name_per_institution",
            )
        ]

    def __str__(self):
        return self.name


class FeeStructure(SoftDeleteMixin):
    objects = SoftDeleteManager()
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

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name="fee_structures",
        null=True,
        blank=True,
        help_text="Optional: restrict to a specific section. Null means all sections.",
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

    installment_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of installments. 1 = single payment.",
    )

    installment_frequency = models.CharField(
        max_length=20,
        choices=[
            ("monthly", "Monthly"),
            ("termly", "Per Term"),
            ("quarterly", "Quarterly"),
        ],
        default="monthly",
        help_text="Frequency of installments when count > 1.",
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
            "section",
            "category",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "academic_year",
                    "campus",
                    "class_obj",
                    "section",
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

        if self.section_id and self.class_obj_id:
            if self.section.class_obj_id != self.class_obj_id:
                errors["section"] = "Section must belong to the selected class."

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

        if self.installment_count < 1:
            errors["installment_count"] = "Installment count must be at least 1."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        parts = [
            f"{self.campus.name}",
            f"{self.class_obj.name}",
        ]
        if self.section_id:
            parts.append(f"{self.section.name}")
        parts.extend([f"{self.category.name}", f"{self.amount}"])
        if self.installment_count > 1:
            parts.append(f"{self.installment_count}x {self.installment_frequency}")
        return " - ".join(parts)


class Invoice(SoftDeleteMixin):
    objects = SoftDeleteManager()
    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="invoices",
        null=True,
        blank=True,
    )

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
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    enrollment = models.ForeignKey(
        "students.Enrollment",
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

    # Installment fields
    installment_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of installments this invoice is split into.",
    )
    installment_frequency = models.CharField(
        max_length=20,
        choices=[
            ("monthly", "Monthly"),
            ("termly", "Per Term"),
            ("quarterly", "Quarterly"),
        ],
        default="monthly",
        blank=True,
    )
    next_installment_due = models.DateField(
        null=True,
        blank=True,
        help_text="Due date of the next pending installment.",
    )

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

    # Late fee tracking
    late_fee_applied = models.BooleanField(
        default=False,
        help_text="Whether a late fee has been applied to this invoice.",
    )
    late_fee_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total late fees applied to this invoice.",
    )
    late_fee_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when late fee was last applied.",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "invoice_number"],
                name="unique_invoice_number_per_institution",
            )
        ]
        indexes = [
            models.Index(
                fields=["student", "status"],
                name="invoice_student_status_idx",
            ),
            models.Index(
                fields=["institution", "status"],
                name="invoice_inst_status_idx",
            ),
            models.Index(
                fields=["due_date", "status"],
                name="invoice_due_status_idx",
            ),
            models.Index(
                fields=["academic_year", "status"],
                name="invoice_year_status_idx",
            ),
        ]

    @property
    def subtotal(self):
        return sum(
            (item.amount for item in self.items.all()),
            Decimal("0.00"),
        )

    @property
    def total_amount(self):
        concession_total = sum(
            (
                concession.amount
                for concession in self.concessions.all()
                if concession.status == "approved"
            ),
            Decimal("0.00"),
        )
        total = self.subtotal - self.discount - concession_total
        return max(total, Decimal("0.00"))

    @property
    def paid_amount(self):
        return sum(
            (
                payment.net_amount
                for payment in self.payments.all()
                if payment.status == "completed"
            ),
            Decimal("0.00"),
        )

    @property
    def balance(self):
        return max(
            self.total_amount - self.paid_amount,
            Decimal("0.00"),
        )

    @property
    def installment_amount(self):
        """Amount per installment (total / count)."""
        if self.installment_count > 1:
            return (self.total_amount / Decimal(str(self.installment_count))).quantize(Decimal("0.01"))
        return self.total_amount

    @property
    def installments_paid(self):
        """Number of installments fully paid."""
        if self.installment_count <= 1:
            return 1 if self.status == "paid" else 0
        paid = self.paid_amount
        return min(int(paid / self.installment_amount), self.installment_count)

    @property
    def installments_remaining(self):
        return max(self.installment_count - self.installments_paid, 0)

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

        if self.installment_count < 1:
            errors["installment_count"] = "Installment count must be at least 1."

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


class Payment(SoftDeleteMixin):
    objects = SoftDeleteManager()
    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True,
    )

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

    # Installment tracking
    installment_number = models.PositiveIntegerField(
        default=1,
        help_text="Which installment this payment is for (1-based).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "receipt_number"],
                name="unique_receipt_number_per_institution",
            ),
            models.UniqueConstraint(
                fields=["stripe_session_id"],
                name="unique_stripe_session_id",
                condition=~models.Q(stripe_session_id=""),
            ),
        ]
        indexes = [
            models.Index(
                fields=["invoice", "status"],
                name="payment_invoice_status_idx",
            ),
            models.Index(
                fields=["institution", "payment_date"],
                name="payment_inst_date_idx",
            ),
            models.Index(
                fields=["payment_method", "status"],
                name="payment_method_status_idx",
            ),
        ]

    def clean(self):
        errors = {}

        if self.amount <= Decimal("0"):
            errors["amount"] = "Payment amount must be greater than zero."

        if self.invoice_id and self.amount > self.invoice.balance:
            errors["amount"] = (
                "Payment cannot be greater than the invoice balance."
            )

        if self.installment_number < 1:
            errors["installment_number"] = "Installment number must be at least 1."

        if self.invoice_id and self.installment_number > self.invoice.installment_count:
            errors["installment_number"] = (
                f"Installment number cannot exceed invoice installment count "
                f"({self.invoice.installment_count})."
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
            (reversal.amount for reversal in self.reversals.all() if reversal.status == "completed"),
            Decimal("0.00"),
        )

    @property
    def net_amount(self):
        refunded = sum(
            (refund.amount for refund in self.refunds.all() if refund.status == "completed"),
            Decimal("0.00"),
        )
        return max(
            self.amount - self.reversed_amount - refunded,
            Decimal("0.00"),
        )

    def __str__(self):
        return (
            f"{self.receipt_number} - "
            f"{self.invoice.student.full_name} - "
            f"{self.amount}"
        )


class PaymentReversal(models.Model):
    """An auditable correction to a completed payment; payments are never deleted."""

    STATUS_CHOICES = [("completed", "Completed"), ("cancelled", "Cancelled")]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="payment_reversals",
        null=True,
        blank=True,
    )

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


class Account(SoftDeleteMixin):
    objects = SoftDeleteManager()
    ACCOUNT_TYPES = [
        ("asset", "Asset"),
        ("liability", "Liability"),
        ("equity", "Equity"),
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="finance_accounts",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_account_code_per_institution",
            )
        ]

    def clean(self):
        if self.parent_id and self.parent.institution_id != self.institution_id:
            raise ValidationError({"parent": "Parent account must belong to the same institution."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(SoftDeleteMixin):
    objects = SoftDeleteManager()
    STATUS_CHOICES = [("posted", "Posted"), ("void", "Void")]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="journal_entries",
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="journal_entries",
    )
    posting_date = models.DateField(default=date.today)
    description = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, blank=True)
    source_id = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="posted")
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_journal_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.campus_id and self.campus.school_id != self.institution_id:
            raise ValidationError({"campus": "Campus must belong to the institution."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def total_debit(self):
        return sum((line.debit for line in self.lines.all()), Decimal("0.00"))

    @property
    def total_credit(self):
        return sum((line.credit for line in self.lines.all()), Decimal("0.00"))

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit


class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="journal_lines")
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    memo = models.CharField(max_length=255, blank=True)

    def clean(self):
        errors = {}
        if self.account_id and self.entry_id and self.account.institution_id != self.entry.institution_id:
            errors["account"] = "Account must belong to the journal institution."
        if self.debit < 0 or self.credit < 0:
            errors["debit"] = "Amounts cannot be negative."
        if self.debit and self.credit:
            errors["debit"] = "A journal line cannot contain both debit and credit."
        if not self.debit and not self.credit:
            errors["debit"] = "A journal line must contain a debit or credit amount."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Expense(SoftDeleteMixin):
    objects = SoftDeleteManager()
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    institution = models.ForeignKey(School, on_delete=models.CASCADE, related_name="expenses")
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, null=True, blank=True, related_name="expenses")
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="expenses")
    payment_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="paid_expenses")
    vendor = models.CharField(max_length=200, blank=True)
    expense_date = models.DateField(default=date.today)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    journal_entry = models.OneToOneField(JournalEntry, on_delete=models.PROTECT, null=True, blank=True, related_name="expense")
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_expenses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}
        if self.campus_id and self.campus.school_id != self.institution_id:
            errors["campus"] = "Campus must belong to the institution."
        for field in ("expense_account", "payment_account"):
            account = getattr(self, f"{field}_id", None) and getattr(self, field, None)
            if account and account.institution_id != self.institution_id:
                errors[field] = "Account must belong to the institution."
        if self.amount <= 0:
            errors["amount"] = "Expense amount must be greater than zero."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Concession(SoftDeleteMixin):
    objects = SoftDeleteManager()
    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="concessions",
        null=True,
        blank=True,
    )

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="concessions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    approved_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_concessions")
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Concession amount must be greater than zero."})
        if self.invoice_id and self.amount > self.invoice.subtotal:
            raise ValidationError({"amount": "Concession cannot exceed the invoice subtotal."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class PaymentRefund(SoftDeleteMixin):
    objects = SoftDeleteManager()
    STATUS_CHOICES = [("completed", "Completed"), ("cancelled", "Cancelled")]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="payment_refunds",
        null=True,
        blank=True,
    )

    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    refund_date = models.DateField(default=date.today)
    refund_method = models.CharField(max_length=20, choices=Payment.PAYMENT_METHOD_CHOICES, default="cash")
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_refunds")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Refund amount must be greater than zero."})
        prior = sum((refund.amount for refund in self.payment.refunds.filter(status="completed")), Decimal("0.00"))
        if self.pk:
            prior -= self.amount
        available = self.payment.amount - self.payment.reversed_amount - prior
        if self.amount > available:
            raise ValidationError({"amount": "Refund cannot exceed the effective payment amount."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.payment.invoice.refresh_status()


class StudentFeeOverride(SoftDeleteMixin):
    """Per-student fee amount override for a specific fee structure."""
    objects = SoftDeleteManager()

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="student_fee_overrides",
        null=True,
        blank=True,
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="fee_overrides",
    )

    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.PROTECT,
        related_name="student_overrides",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Override amount. Overrides the fee structure amount for this student.",
    )

    reason = models.TextField(blank=True, help_text="Reason for the override (e.g., scholarship, sibling discount).")

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
        constraints = [
            models.UniqueConstraint(
                fields=["student", "fee_structure"],
                name="unique_student_fee_override",
            )
        ]
        ordering = ["student", "fee_structure"]

    def clean(self):
        errors = {}

        if self.amount < Decimal("0"):
            errors["amount"] = "Override amount cannot be negative."

        if self.fee_structure_id and self.student_id:
            enrollment = self.student.enrollments.filter(
                academic_year=self.fee_structure.academic_year,
                campus=self.fee_structure.campus,
                class_obj=self.fee_structure.class_obj,
                status="active",
            ).first()
            if not enrollment:
                errors["student"] = "Student must be enrolled in the fee structure's class/campus/year."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.fee_structure} - {self.amount}"

