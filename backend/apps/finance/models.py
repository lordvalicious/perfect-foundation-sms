
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import AcademicYear, Campus, Class, School
from apps.students.models import Enrollment, Student


class FeeCategory(models.Model):
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
    institution = models.ForeignKey(
        School,
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
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "invoice_number"],
                name="unique_invoice_number_per_institution",
            )
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "receipt_number"],
                name="unique_receipt_number_per_institution",
            )
        ]

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


class Account(models.Model):
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


class JournalEntry(models.Model):
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


class Expense(models.Model):
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


class Concession(models.Model):
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


class PaymentRefund(models.Model):
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

