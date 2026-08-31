"""Part 1 — Foundation.

Creates (idempotently, scoped to DEMO-EDU):
    - the granular permission catalog (if empty)
    - role -> permission grants for every used role
    - the base users (super admin, org admin, and per-campus staff accounts)
    - school settings and a handful of foundation calendar events
"""

from datetime import date

from django.db import transaction

from apps.accounts.models import Permission, Role, RolePermission
from apps.schools.models import AcademicCalendar, SchoolSettings

import apps.accounts.demo_seed.base as base
from apps.accounts.demo_seed.base import GLOBAL_ROLES, base_users, getc

ALL = ["*"]

# role -> permission codename prefixes. A "*" entry grants everything.
ROLE_GRANTS = {
    "super_admin": ALL,
    "admin": ALL,
    "org_admin": ALL,
    "head_office": ALL,
    "academic": ALL,
    "campus_admin": ALL,
    "principal": [
        "student.", "teacher.", "staff.", "admission.", "attendance.",
        "exam.", "lms.", "communication.", "report.",
    ],
    "vice_principal": [
        "student.", "teacher.", "staff.", "admission.", "attendance.",
        "exam.", "lms.", "communication.", "report.",
    ],
    "accountant": [
        "student.view", "finance.", "payroll.", "report.",
    ],
    "hr": [
        "student.view", "staff.", "attendance.", "hr.", "payroll.",
        "communication.", "report.", "user.view",
    ],
    "receptionist": [
        "student.view", "admission.", "communication.", "attendance.view",
    ],
    "librarian": [
        "library.", "report.view", "student.view",
    ],
    "guard": [
        "attendance.view", "student.view",
    ],
    "teacher": [
        "student.view", "teacher.", "attendance.", "exam.result.",
        "exam.view", "lms.", "communication.", "report.view",
    ],
    "staff": [
        "student.view", "attendance.view", "report.view", "communication.",
    ],
    "parent": [
        "student.view", "communication.view", "report.view",
    ],
    "student": [
        "student.view", "lms.view", "communication.view", "report.view",
    ],
}


def _seed_permissions(ctx):
    """Create the granular permission catalog when missing. Idempotent."""
    catalog = list(Permission.get_default_permissions())
    for codename, name, category, action in catalog:
        _, created = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                "name": name,
                "description": "",
                "action": action,
                "category": category,
                "is_system": True,
            },
        )
        if created:
            ctx.count("permissions")


def _grant(ctx, role, prefixes):
    """Grant every catalog permission matching one of ``prefixes`` to ``role``."""
    all_perms = Permission.objects.all()
    if ALL in prefixes:
        selected = all_perms
    else:
        selected = [
            p for p in all_perms
            if any(p.codename.startswith(pre) for pre in prefixes)
        ]
    for permission in selected:
        _, created = RolePermission.objects.get_or_create(
            role=role,
            permission=permission,
            institution=ctx.school,
        )
        if created:
            ctx.count(f"grant:{role}")


def _seed_role_permissions(ctx):
    for role, prefixes in ROLE_GRANTS.items():
        _grant(ctx, role, prefixes)


def _seed_school_settings(ctx):
    settings, _ = getc(
        SchoolSettings,
        school=ctx.school,
        defaults={
            "short_name": "DEG",
            "motto": "Excellence, Integrity, Community",
            "contact_email": "info@demo.edu.pk",
            "contact_phone": "+92-42-111-000-111",
            "contact_website": "https://demo.edu.pk",
            "address_line": "Demo Education Group Headquarters, Lahore",
            "footer_text": "Demo Education Group — for development and testing only.",
            "sidebar_color": "#1a73e8",
            "header_color": "#1a73e8",
            "date_format": "dd-mm-yyyy",
            "language": "en",
            "working_days": ["mon", "tue", "wed", "thu", "fri", "sat"],
            "email_from_name": "Demo Education Group",
        },
    )
    if settings.id:
        ctx.count("school_settings")


def _seed_calendar(ctx):
    fallback_events = [
        ("holiday", "Summer Break (Second Year)", date(2025, 6, 27), date(2025, 8, 7)),
        ("holiday", "Winter Break", date(2025, 12, 21), date(2026, 1, 3)),
        ("event", "Independence Day Celebration", date(2026, 8, 14), date(2026, 8, 14)),
        ("holiday", "Eid Holidays", date(2026, 3, 30), date(2026, 4, 3)),
    ]
    year = ctx.active_year
    for event_type, title, start, end in fallback_events:
        _, created = AcademicCalendar.objects.get_or_create(
            institution=ctx.school,
            title=title,
            start_date=start,
            defaults={
                "campus": None,
                "academic_year": year,
                "event_type": event_type,
                "description": "Foundation calendar event seeded by part 1.",
                "end_date": end,
                "is_all_day": True,
                "is_for_all_campuses": True,
                "status": "published",
                "created_by": ctx.users.get("demo_superadmin"),
            },
        )
        if created:
            ctx.count("calendar_events")


@transaction.atomic
def run(ctx):
    ctx.log("Part 1: foundation (school, campuses, roles, users).")
    _seed_permissions(ctx)
    _seed_role_permissions(ctx)
    base_users(ctx)
    _seed_school_settings(ctx)
    _seed_calendar(ctx)
    ctx.ok(
        "Part 1 done. Log in with any demo credential in DEMO_CREDENTIALS.md "
        f"(password {base.DEMO_PASSWORD})."
    )