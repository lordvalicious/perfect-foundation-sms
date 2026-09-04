
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
    campus = models.ForeignKey(
        Campus,
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
    campus = models.ForeignKey(
        Campus,
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
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("posted", "Posted"),
        ("void", "Void"),
    ]

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
    reference = models.CharField(max_length=100, blank=True)
    source_type = models.CharField(max_length=50, blank=True)
    source_id = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_journal_entries",
    )
    posted_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posted_journal_entries",
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voided_journal_entries",
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.TextField(blank=True)
    reversed_entry = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reversal_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-posting_date", "-id"]
        indexes = [
            models.Index(fields=["institution", "status", "posting_date"]),
            models.Index(fields=["source_type", "source_id"]),
        ]

    def clean(self):
        errors = {}
        if self.campus_id and self.campus.school_id != self.institution_id:
            errors["campus"] = "Campus must belong to the institution."

        # Validate balance for posted entries
        if self.status == "posted" and self.pk:
            total_debit = sum((line.debit for line in self.lines.all()), Decimal("0.00"))
            total_credit = sum((line.credit for line in self.lines.all()), Decimal("0.00"))
            if total_debit != total_credit:
                errors["__all__"] = f"Journal entry unbalanced: debit={total_debit}, credit={total_credit}"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def post(self, user):
        """Post a draft journal entry."""
        if self.status != "draft":
            raise ValueError("Only draft entries can be posted.")
        
        total_debit = sum((line.debit for line in self.lines.all()), Decimal("0.00"))
        total_credit = sum((line.credit for line in self.lines.all()), Decimal("0.00"))
        if total_debit != total_credit:
            raise ValueError(f"Journal entry unbalanced: debit={total_debit}, credit={total_credit}")
        
        if not self.lines.exists():
            raise ValueError("Journal entry must have at least one line.")
        
        from django.utils import timezone
        self.status = "posted"
        self.posted_by = user
        self.posted_at = timezone.now()
        self.save(update_fields=["status", "posted_by", "posted_at", "updated_at"])
        
        record_audit(
            user=user,
            action="journal_posted",
            model_name="JournalEntry",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"total_debit": str(total_debit), "total_credit": str(total_credit)},
        )
        return self

    def void(self, user, reason):
        """Void a posted journal entry and create reversing entry."""
        if self.status != "posted":
            raise ValueError("Only posted entries can be voided.")
        if self.reversed_entry_id:
            raise ValueError("Entry already has a reversal.")

        from django.utils import timezone
        from .services import JournalService
        
        # Create reversing entry
        lines = []
        for line in self.lines.all():
            lines.append({
                "account_id": line.account_id,
                "debit": str(line.credit),
                "credit": str(line.debit),
                "memo": f"Reversal of {self.description}",
            })
        
        reversal = JournalService(self.institution).create_journal_entry(
            posting_date=date.today(),
            description=f"Reversal: {self.description}",
            lines=lines,
            campus=self.campus,
            source_type="journal_reversal",
            source_id=str(self.pk),
            user=user,
        )
        reversal.post(user)

        # Mark original as void
        self.status = "void"
        self.voided_by = user
        self.voided_at = timezone.now()
        self.void_reason = reason
        self.reversed_entry = reversal
        self.save(update_fields=["status", "voided_by", "voided_at", "void_reason", "reversed_entry", "updated_at"])

        record_audit(
            user=user,
            action="journal_voided",
            model_name="JournalEntry",
            object_id=str(self.pk),
            object_repr=str(self),
            details={"reversal_id": str(reversal.pk), "reason": reason},
        )
        return reversal

    @property
    def total_debit(self):
        return sum((line.debit for line in self.lines.all()), Decimal("0.00"))

    @property
    def total_credit(self):
        return sum((line.credit for line in self.lines.all()), Decimal("0.00"))

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit

def __str__(self):
        return f"{self.posting_date} - {self.description} ({self.status})"


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


class BankAccount(SoftDeleteMixin):
    """Bank account / cash book for recording bank transactions."""
    objects = SoftDeleteManager()

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="bank_accounts",
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="bank_accounts",
    )
    account = models.OneToOneField(
        Account,
        on_delete=models.PROTECT,
        related_name="bank_account",
        help_text="The GL account representing this bank account",
    )
    bank_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    account_holder = models.CharField(max_length=200, blank=True)
    branch = models.CharField(max_length=200, blank=True)
    swift_code = models.CharField(max_length=20, blank=True)
    iban = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=3, default="PKR")
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    opening_date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)
    last_reconciled_date = models.DateField(null=True, blank=True)
    last_reconciled_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_bank_accounts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["bank_name", "account_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "account_number"],
                name="unique_bank_account_per_institution",
            )
        ]

    def clean(self):
        errors = {}
        if self.campus_id and self.campus.school_id != self.institution_id:
            errors["campus"] = "Campus must belong to the institution."
        if self.account_id and self.account.institution_id != self.institution_id:
            errors["account"] = "GL account must belong to the same institution."
        if self.account_id and self.account.account_type != "asset":
            errors["account"] = "Bank account must be linked to an asset account."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

    @property
    def current_balance(self):
        """Calculate current balance from journal lines."""
        from django.db.models import Sum
        total_debit = self.account.journal_lines.filter(
            entry__status="posted"
        ).aggregate(total=Sum("debit"))["total"] or Decimal("0.00")
        total_credit = self.account.journal_lines.filter(
            entry__status="posted"
        ).aggregate(total=Sum("credit"))["total"] or Decimal("0.00")
        return self.opening_balance + total_debit - total_credit


class BankReconciliation(SoftDeleteMixin):
    """Bank reconciliation statement."""
    objects = SoftDeleteManager()

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("completed", "Completed"),
        ("approved", "Approved"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="bank_reconciliations",
    )
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="reconciliations",
    )
    statement_date = models.DateField()
    statement_balance = models.DecimalField(max_digits=14, decimal_places=2)
    book_balance = models.DecimalField(max_digits=14, decimal_places=2)
    difference = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    prepared_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prepared_reconciliations",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_reconciliations",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-statement_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["bank_account", "statement_date"],
                name="unique_reconciliation_per_account_date",
            )
        ]

    def clean(self):
        errors = {}
        self.difference = self.statement_balance - self.book_balance
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.difference = self.statement_balance - self.book_balance
        self.full_clean()
        return super().save(*args, **kwargs)

    def approve(self, user):
        if self.status != "completed":
            raise ValueError("Only completed reconciliations can be approved.")
        from django.utils import timezone
        self.status = "approved"
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    def __str__(self):
        return f"{self.bank_account} - {self.statement_date} ({self.status})"


class Budget(SoftDeleteMixin):
    """Budget for tracking planned vs actual income/expense."""
    objects = SoftDeleteManager()

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("closed", "Closed"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="budgets",
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="budgets",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="budgets",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    total_budgeted_income = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_budgeted_expense = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_budgets",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_budgets",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "academic_year", "name"],
                name="unique_budget_name_per_year_institution",
            )
        ]

    def clean(self):
        errors = {}
        if self.campus_id and self.campus.school_id != self.institution_id:
            errors["campus"] = "Campus must belong to the institution."
        if self.academic_year_id and self.academic_year.school_id != self.institution_id:
            errors["academic_year"] = "Academic year must belong to the institution."
        if self.start_date > self.end_date:
            errors["end_date"] = "End date must be after start date."
        if self.academic_year_id:
            if self.start_date < self.academic_year.start_date or self.end_date > self.academic_year.end_date:
                errors["academic_year"] = "Budget dates must be within the academic year."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def approve(self, user):
        if self.status != "draft":
            raise ValueError("Only draft budgets can be approved.")
        from django.utils import timezone
        self.status = "active"
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    def close(self, user):
        if self.status != "active":
            raise ValueError("Only active budgets can be closed.")
        from django.utils import timezone
        self.status = "closed"
        self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"{self.name} ({self.academic_year})"


class BudgetLine(SoftDeleteMixin):
    """Individual budget line items."""
    objects = SoftDeleteManager()

    TYPE_CHOICES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="budget_lines",
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    budgeted_amount = models.DecimalField(max_digits=14, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    period_start = models.DateField()
    period_end = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["period_start", "account__code"]

    def clean(self):
        errors = {}
        if self.account_id and self.account.institution_id != self.budget.institution_id:
            errors["account"] = "Account must belong to the budget institution."
        if self.period_start > self.period_end:
            errors["period_end"] = "Period end must be after period start."
        if self.budget_id:
            if self.period_start < self.budget.start_date or self.period_end > self.budget.end_date:
                errors["period"] = "Budget line period must be within budget period."
        if self.budgeted_amount < 0:
            errors["budgeted_amount"] = "Budgeted amount cannot be negative."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def variance(self):
        return self.actual_amount - self.budgeted_amount

    def __str__(self):
        return f"{self.budget.name} - {self.account.code} - {self.get_type_display()}"


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

    def __str__(self):
        return f"{self.vendor or self.reference or self.id} - {self.amount}"
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
    TYPE_CHOICES = [
        ("discount", "Discount"),
        ("scholarship", "Scholarship"),
        ("waiver", "Waiver"),
        ("fine", "Fine/Penalty"),
        ("adjustment", "Adjustment"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="concessions",
        null=True,
        blank=True,
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.CASCADE,
        related_name="concessions",
        null=True,
        blank=True,
    )

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="concessions")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="discount")
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

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} - {self.invoice.invoice_number}"


class Fine(SoftDeleteMixin):
    """Disciplinary fines and penalties separate from concessions."""
    objects = SoftDeleteManager()
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("paid", "Paid"),
        ("waived", "Waived"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="fines",
        null=True,
        blank=True,
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.CASCADE,
        related_name="fines",
        null=True,
        blank=True,
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="fines",
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="fines",
    )

    TYPE_CHOICES = [
        ("late_payment", "Late Payment"),
        ("disciplinary", "Disciplinary"),
        ("library", "Library Fine"),
        ("damage", "Property Damage"),
        ("attendance", "Attendance Penalty"),
        ("other", "Other"),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="disciplinary")

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    issued_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_fines",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_fines",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    waived_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waived_fines",
    )
    waived_at = models.DateTimeField(null=True, blank=True)
    waiver_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Fine amount must be greater than zero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} - {self.student.full_name} - {self.amount}"


class Adjustment(SoftDeleteMixin):
    """Financial adjustment for historical corrections (never rewrites history)."""
    objects = SoftDeleteManager()
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("applied", "Applied"),
    ]

    TYPE_CHOICES = [
        ("credit", "Credit Adjustment"),
        ("debit", "Debit Adjustment"),
        ("write_off", "Write Off"),
        ("correction", "Correction"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="adjustments",
        null=True,
        blank=True,
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.CASCADE,
        related_name="adjustments",
        null=True,
        blank=True,
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="adjustments",
        null=True,
        blank=True,
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="adjustments",
        null=True,
        blank=True,
    )

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="adjustments",
        null=True,
        blank=True,
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_adjustments",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_adjustments",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Adjustment amount must be greater than zero."})
        # Must be linked to at least one entity
        if not any([self.student_id, self.invoice_id, self.payment_id]):
            raise ValidationError({"__all__": "Adjustment must be linked to a student, invoice, or payment."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} - {self.status}"


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
    campus = models.ForeignKey(
        Campus,
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
    campus = models.ForeignKey(
        Campus,
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

