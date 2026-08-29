"""Finance business services shared by management commands and API."""

from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from apps.finance.models import FeeCategory, Invoice, InvoiceItem


def apply_late_fees(percent=None, flat=None, grace_days=5, dry_run=False):
    """Charge a one-time late fee to invoices past their due date.

    Each invoice is charged at most once (a "Late Fee" item must not
    already exist). Returns a summary dict:

        {"charged": n, "total": Decimal, "rows": [...], "dry_run": bool}
    """
    if percent is None and flat is None:
        raise ValueError("Provide either percent or flat.")

    if percent is not None and not (Decimal("0") < Decimal(str(percent)) <= 100):
        raise ValueError("percent must be between 0 and 100.")

    if flat is not None and Decimal(str(flat)) <= 0:
        raise ValueError("flat must be greater than zero.")

    cutoff = timezone.localdate() - timezone.timedelta(days=grace_days)

    overdue = (
        Invoice.objects
        .filter(
            status__in=["issued", "partial", "overdue"],
            due_date__lt=cutoff,
            late_fee_applied=False,  # Also exclude invoices that already had late fee applied
        )
        .exclude(items__category__name__iexact="Late Fee")
        .distinct()
        .prefetch_related(
            "items",
            "payments",
            "payments__refunds",
            "payments__reversals",
            "concessions",
        )
        .select_related("student", "enrollment__campus")
    )

    fee_category = None
    rows = []
    total_fees = Decimal("0")

    for invoice in overdue:
        balance = invoice.balance

        if balance <= 0:
            continue

        if flat is not None:
            fee = Decimal(str(flat))
        else:
            fee = (
                balance * Decimal(str(percent)) / Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        fee = min(fee, balance)

        if fee <= 0:
            continue

        rows.append((invoice, fee))
        total_fees += fee

    if not dry_run:
        fee_category, _ = FeeCategory.objects.get_or_create(
            name="Late Fee",
            defaults={
                "description": "Automated late payment surcharge."
            },
        )

        with transaction.atomic():
            for invoice, fee in rows:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    category=fee_category,
                    amount=fee,
                    description="Late fee applied automatically.",
                )
                invoice.late_fee_applied = True
                invoice.late_fee_amount += fee
                invoice.late_fee_date = timezone.localdate()
                invoice.save(update_fields=["late_fee_applied", "late_fee_amount", "late_fee_date", "updated_at"])

    return {
        "charged": len(rows),
        "total": total_fees.quantize(Decimal("0.01")),
        "rows": [
            {
                "invoice": invoice.invoice_number,
                "student": invoice.student.full_name,
                "fee": str(fee),
            }
            for invoice, fee in rows[:50]
        ],
        "truncated_rows": max(len(rows) - 50, 0),
        "dry_run": dry_run,
    }
