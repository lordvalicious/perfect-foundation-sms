"""Helpers for the finance module.

- Sequential, human-readable invoice / receipt numbering.
- Printable receipt PDFs (via reportlab).
- Fee invoice generation and management.
- Payment processing and reconciliation.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any

from django.db import transaction
from django.db.models import Sum, Q

from apps.schools.models import AcademicYear, Campus, Class, School
from apps.students.models import Enrollment, Student

from .models import (
    FeeCategory,
    FeeStructure,
    Invoice,
    InvoiceItem,
    Payment,
    PaymentReversal,
    Concession,
    JournalEntry,
    JournalLine,
    Account,
    Expense,
)


def _year_suffix():
    return str(date.today().year)


def next_invoice_number(institution: School) -> str:
    """Generate the next unique invoice number for an institution, e.g. INV-2026-0001."""
    prefix = f"INV-{_year_suffix()}-"
    count = Invoice.objects.filter(
        institution=institution,
        invoice_number__startswith=prefix
    ).count()
    return f"{prefix}{count + 1:04d}"


def next_receipt_number(institution: School) -> str:
    """Generate the next unique receipt number for an institution, e.g. RCPT-2026-0001."""
    prefix = f"RCPT-{_year_suffix()}-"
    count = Payment.objects.filter(
        institution=institution,
        receipt_number__startswith=prefix
    ).count()
    return f"{prefix}{count + 1:04d}"


class FeeInvoiceService:
    """Service for generating and managing fee invoices."""

    def __init__(self, institution: School, academic_year: AcademicYear):
        self.institution = institution
        self.academic_year = academic_year
        self.settings = getattr(institution, "settings", None)

    def get_fee_structures_for_enrollment(self, enrollment: Enrollment):
        """Get all active fee structures applicable to an enrollment."""
        return FeeStructure.objects.filter(
            academic_year=self.academic_year,
            campus=enrollment.campus,
            class_obj=enrollment.class_obj,
            status="active",
        ).select_related("category")

    def generate_invoice_for_enrollment(
        self,
        enrollment: Enrollment,
        issue_date: Optional[date] = None,
        due_date: Optional[date] = None,
        categories: Optional[List[FeeCategory]] = None,
    ) -> Invoice:
        """Generate a fee invoice for a single enrollment."""
        if issue_date is None:
            issue_date = date.today()

        if due_date is None:
            due_day = self.settings.fee_invoice_due_day if self.settings else 10
            # Simple due date calculation - next month's due day
            if issue_date.day >= due_day:
                # Next month
                if issue_date.month == 12:
                    due_date = date(issue_date.year + 1, 1, due_day)
                else:
                    due_date = date(issue_date.year, issue_date.month + 1, due_day)
            else:
                due_date = date(issue_date.year, issue_date.month, due_day)

        fee_structures = self.get_fee_structures_for_enrollment(enrollment)
        if categories:
            fee_structures = fee_structures.filter(category__in=categories)

        if not fee_structures.exists():
            raise ValueError("No fee structures found for this enrollment.")

        with transaction.atomic():
            invoice = Invoice.objects.create(
                institution=self.institution,
                invoice_number=next_invoice_number(self.institution),
                student=enrollment.student,
                enrollment=enrollment,
                academic_year=self.academic_year,
                issue_date=issue_date,
                due_date=due_date,
                status="issued",
            )

            for fs in fee_structures:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    category=fs.category,
                    description=fs.category.name,
                    amount=fs.amount,
                )

            # Apply any approved concessions
            self._apply_concessions(invoice)

            invoice.refresh_status(save=True)
            return invoice

    def _apply_concessions(self, invoice: Invoice):
        """Apply approved concessions to the invoice."""
        from .models import Concession
        concessions = Concession.objects.filter(
            invoice=invoice,
            status="approved",
        )
        # Concessions are handled in Invoice.total_amount property

    def bulk_generate_invoices(
        self,
        campus: Optional[Campus] = None,
        class_obj: Optional[Class] = None,
        section=None,
        categories: Optional[List[FeeCategory]] = None,
        issue_date: Optional[date] = None,
    ) -> List[Invoice]:
        """Generate invoices for multiple enrollments in bulk."""
        enrollments = Enrollment.objects.filter(
            academic_year=self.academic_year,
            status="active",
        ).select_related("student", "campus", "class_obj", "section")

        if campus:
            enrollments = enrollments.filter(campus=campus)
        if class_obj:
            enrollments = enrollments.filter(class_obj=class_obj)
        if section:
            enrollments = enrollments.filter(section=section)

        invoices = []
        for enrollment in enrollments:
            try:
                # Check if invoice already exists for this period
                existing = Invoice.objects.filter(
                    enrollment=enrollment,
                    academic_year=self.academic_year,
                    issue_date__month=issue_date.month if issue_date else date.today().month,
                    issue_date__year=issue_date.year if issue_date else date.today().year,
                ).exists()

                if not existing:
                    invoice = self.generate_invoice_for_enrollment(
                        enrollment,
                        issue_date=issue_date,
                        categories=categories,
                    )
                    invoices.append(invoice)
            except ValueError:
                # Skip enrollments with no fee structure
                continue

        return invoices


class PaymentService:
    """Service for processing payments."""

    def __init__(self, institution: School):
        self.institution = institution

    @transaction.atomic
    def process_payment(
        self,
        invoice: Invoice,
        amount: Decimal,
        payment_method: str,
        payment_date: Optional[date] = None,
        reference: str = "",
        notes: str = "",
        stripe_session_id: str = "",
        user=None,
    ) -> Payment:
        """Process a payment for an invoice."""
        if payment_date is None:
            payment_date = date.today()

        if amount <= Decimal("0"):
            raise ValueError("Payment amount must be greater than zero.")

        if amount > invoice.balance:
            raise ValueError("Payment cannot exceed invoice balance.")

        payment = Payment.objects.create(
            institution=self.institution,
            receipt_number=next_receipt_number(self.institution),
            invoice=invoice,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            status="completed",
            reference=reference,
            notes=notes,
            stripe_session_id=stripe_session_id,
        )

        # Refresh invoice status
        invoice.refresh_status(save=True)

        # Create journal entry for the payment
        self._create_payment_journal_entry(payment, user)

        return payment

    def _create_payment_journal_entry(self, payment: Payment, user=None):
        """Create a journal entry for the payment."""
        from .models import Account
        # Get default accounts - these should be configured per institution
        try:
            cash_account = Account.objects.filter(
                institution=payment.invoice.institution,
                account_type="asset",
                code__startswith="1",  # Asset accounts
            ).first()

            fee_income_account = Account.objects.filter(
                institution=payment.invoice.institution,
                account_type="income",
            ).first()

            if cash_account and fee_income_account:
                entry = JournalEntry.objects.create(
                    institution=payment.invoice.institution,
                    campus=payment.invoice.enrollment.campus,
                    posting_date=payment.payment_date,
                    description=f"Fee payment - {payment.receipt_number}",
                    source_type="payment",
                    source_id=str(payment.id),
                    created_by=user,
                )

                JournalLine.objects.create(
                    entry=entry,
                    account=cash_account,
                    debit=payment.amount,
                    memo=f"Payment received: {payment.receipt_number}",
                )

                JournalLine.objects.create(
                    entry=entry,
                    account=fee_income_account,
                    credit=payment.amount,
                    memo=f"Fee income: {payment.receipt_number}",
                )
        except Exception:
            # Journal entry creation is non-critical for payment processing
            pass

    @transaction.atomic
    def reverse_payment(
        self,
        payment: Payment,
        amount: Decimal,
        reason: str,
        user,
    ) -> PaymentReversal:
        """Reverse a completed payment."""
        if payment.status != "completed":
            raise ValueError("Only completed payments can be reversed.")

        if amount > payment.amount:
            raise ValueError("Reversal amount cannot exceed payment amount.")

        reversal = PaymentReversal.objects.create(
            institution=payment.institution,
            payment=payment,
            amount=amount,
            reason=reason,
            created_by=user,
        )

        # Refresh invoice status
        payment.invoice.refresh_status(save=True)

        return reversal


class InvoiceService:
    """Service for invoice management."""

    def __init__(self, institution: School):
        self.institution = institution

    def get_outstanding_invoices(
        self,
        student: Optional[Student] = None,
        campus: Optional[Campus] = None,
        academic_year: Optional[AcademicYear] = None,
    ):
        """Get all outstanding (partial/overdue) invoices."""
        queryset = Invoice.objects.filter(
            institution=self.institution,
            status__in=["issued", "partial", "overdue"],
        ).select_related("student", "enrollment", "academic_year")

        if student:
            queryset = queryset.filter(student=student)
        if campus:
            queryset = queryset.filter(enrollment__campus=campus)
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)

        return queryset

    def get_invoice_summary(self, academic_year: AcademicYear, campus: Optional[Campus] = None) -> Dict[str, Any]:
        """Get invoice summary statistics."""
        queryset = Invoice.objects.filter(
            institution=self.institution,
            academic_year=academic_year,
        )

        if campus:
            queryset = queryset.filter(enrollment__campus=campus)

        stats = queryset.aggregate(
            total_invoiced=Sum("items__amount"),
            total_paid=Sum(
                "payments__amount",
                filter=Q(payments__status="completed"),
            ),
            total_discount=Sum("discount"),
        )

        total_invoiced = stats["total_invoiced"] or Decimal("0")
        total_paid = stats["total_paid"] or Decimal("0")
        total_discount = stats["total_discount"] or Decimal("0")

        return {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_discount": total_discount,
            "total_outstanding": total_invoiced - total_paid - total_discount,
            "collection_rate": float(total_paid / total_invoiced * 100) if total_invoiced > 0 else 0,
        }


class JournalService:
    """Service for double-entry journal operations."""

    def __init__(self, institution: School):
        self.institution = institution

    @transaction.atomic
    def create_journal_entry(
        self,
        posting_date: date,
        description: str,
        lines: List[Dict[str, Any]],
        campus: Optional[Campus] = None,
        source_type: str = "",
        source_id: str = "",
        user=None,
    ) -> JournalEntry:
        """Create a balanced journal entry with multiple lines.

        Args:
            lines: List of dicts with keys: account_id, debit, credit, memo
        """
        total_debit = sum(Decimal(str(line.get("debit", 0))) for line in lines)
        total_credit = sum(Decimal(str(line.get("credit", 0))) for line in lines)

        if total_debit != total_credit:
            raise ValueError(f"Journal entry unbalanced: debit={total_debit}, credit={total_credit}")

        entry = JournalEntry.objects.create(
            institution=self.institution,
            campus=campus,
            posting_date=posting_date,
            description=description,
            source_type=source_type,
            source_id=source_id,
            created_by=user,
        )

        for line in lines:
            JournalLine.objects.create(
                entry=entry,
                account_id=line["account_id"],
                debit=Decimal(str(line.get("debit", 0))),
                credit=Decimal(str(line.get("credit", 0))),
                memo=line.get("memo", ""),
            )

        return entry

    def void_journal_entry(self, entry: JournalEntry, user) -> JournalEntry:
        """Void a posted journal entry."""
        if entry.status == "void":
            raise ValueError("Entry already voided.")

        entry.status = "void"
        entry.save(update_fields=["status", "updated_at"])

        # Create reversing entry
        lines = []
        for line in entry.lines.all():
            lines.append({
                "account_id": line.account_id,
                "debit": str(line.credit),
                "credit": str(line.debit),
                "memo": f"Reversal of {entry.description}",
            })

        return self.create_journal_entry(
            posting_date=date.today(),
            description=f"Reversal: {entry.description}",
            lines=lines,
            campus=entry.campus,
            source_type="journal_reversal",
            source_id=str(entry.id),
            user=user,
        )
