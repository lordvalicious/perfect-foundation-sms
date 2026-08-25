"""Centralized tenant branding for documents, emails and notifications.

Given a School, returns everything needed to brand output: name,
short name, logo (storage-agnostic bytes), colors, footer and contact
details. Replaces all hardcoded school identity throughout the app.
"""

from io import BytesIO

from reportlab.lib.units import mm

from apps.schools.models import SchoolSettings


def get_school_branding(school):
    """Return a branding dict for ``school`` (never None fields crash)."""
    settings_obj = getattr(school, "settings", None)

    if settings_obj is None:
        try:
            settings_obj = SchoolSettings.objects.get(school=school)
        except SchoolSettings.DoesNotExist:
            settings_obj = None

    logo_bytes = None

    if settings_obj and settings_obj.logo:
        try:
            settings_obj.logo.open("rb")
            logo_bytes = settings_obj.logo.read()
        except Exception:
            logo_bytes = None

    return {
        "name": school.name if school else "School",
        "short_name": (
            settings_obj.short_name if settings_obj else ""
        ) or (school.name if school else "School"),
        "logo_bytes": logo_bytes,
        "primary_color": settings_obj.primary_color if settings_obj else "#1a73e8",
        "secondary_color": settings_obj.secondary_color if settings_obj else "#34a853",
        "accent_color": settings_obj.accent_color if settings_obj else "#fbbc04",
        "footer_text": settings_obj.footer_text if settings_obj else "",
        "contact_email": settings_obj.contact_email if settings_obj else "",
        "contact_phone": settings_obj.contact_phone if settings_obj else "",
        "contact_website": settings_obj.contact_website if settings_obj else "",
        "email_from_name": (
            settings_obj.email_from_name if settings_obj else ""
        ),
        "email_from_address": (
            settings_obj.email_from_address if settings_obj else ""
        ),
    }


def school_logo_flowable(branding, width=22 * mm, height=22 * mm):
    """Return a reportlab Image flowable when a logo exists, else None."""
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image

    data = branding.get("logo_bytes")

    if not data:
        return None

    try:
        return Image(
            ImageReader(BytesIO(data)),
            width=width,
            height=height,
            preserveAspectRatio=True,
            mask="auto",
        )
    except Exception:
        return None


def school_logo_table_cell(branding, size=26):
    """Fallback cell content when there is no logo: initials box data."""
    short = branding.get("short_name") or branding.get("name") or "S"

    return "".join(word[0] for word in short.split()[:3]).upper()
