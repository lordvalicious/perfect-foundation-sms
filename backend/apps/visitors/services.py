from datetime import date

from .models import Visitor


def next_badge_number(institution):
    """Next visitor badge number, e.g. VST-2026-0001."""
    prefix = f"VST-{date.today().year}-"
    count = Visitor.objects.filter(
        institution=institution,
        badge_number__startswith=prefix,
    ).count()
    return f"{prefix}{count + 1:04d}"