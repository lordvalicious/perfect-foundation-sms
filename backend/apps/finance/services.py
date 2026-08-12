"""Helpers for the finance module.

- Sequential, human-readable invoice / receipt numbering.
- Printable receipt PDFs (via reportlab).
"""

from datetime import date

from .models import Invoice, Payment


def _year_suffix():
    return str(date.today().year)


def next_invoice_number():
    """Generate the next unique invoice number, e.g. INV-2026-0001."""
    prefix = f"INV-{_year_suffix()}-"
    count = Invoice.objects.filter(
        invoice_number__startswith=prefix
    ).count()
    return f"{prefix}{count + 1:04d}"


def next_receipt_number():
    """Generate the next unique receipt number, e.g. RCPT-2026-0001."""
    prefix = f"RCPT-{_year_suffix()}-"
    count = Payment.objects.filter(
        receipt_number__startswith=prefix
    ).count()
    return f"{prefix}{count + 1:04d}"
