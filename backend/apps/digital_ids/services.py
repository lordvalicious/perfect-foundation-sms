from datetime import date

from .models import IdCard


def default_expiry_date():
    """Cards expire on March 31 of the next calendar year."""
    return date(date.today().year + 1, 3, 31)


def next_card_number(institution):
    """Next ID card number, e.g. PF-2026-0001."""
    prefix = f"PF-{date.today().year}-"
    count = IdCard.objects.filter(
        institution=institution,
        card_number__startswith=prefix,
    ).count()
    return f"{prefix}{count + 1:04d}"