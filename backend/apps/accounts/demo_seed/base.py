"""Shared helpers and constants for the demo-data seeder.

The whole seed is scoped to a single created school ("Demo Education Group",
code DEMO-EDU). Nothing here ever touches the pre-existing tenant (school id 1
"Default Institution") or any other school.
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from django.db import transaction
from django.contrib.auth.hashers import make_password

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffProfile,
    User,
)
from apps.schools.models import (
    AcademicCalendar,
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    School,
    Section,
    Subject,
    SubjectGroup,
    SubjectOffering,
    Term,
)

DEMO_SCHOOL_NAME = "Demo Education Group"
DEMO_SCHOOL_CODE = "DEMO-EDU"
# Demo-only development credential. Never used outside the seeder.
DEMO_PASSWORD = "DemoPassword!2026"

CAMPUS_INFO = [
    {
        "name": "Green Valley Campus",
        "code": "GVC",
        "city": "Sialkot",
        "address": "Green Valley Road, Sialkot",
    },
    {
        "name": "City Scholars Campus",
        "code": "CSC",
        "city": "Lahore",
        "address": "City Scholars Block, Lahore",
    },
    {
        "name": "Bright Future Campus",
        "code": "BFC",
        "city": "Islamabad",
        "address": "Bright Future Avenue, Islamabad",
    },
    {
        "name": "Knowledge Hub Campus",
        "code": "KHC",
        "city": "Gujranwala",
        "address": "Knowledge Hub Street, Gujranwala",
    },
    {
        "name": "Excellence Campus",
        "code": "EXC",
        "city": "Faisalabad",
        "address": "Excellence Boulevard, Faisalabad",
    },
]

ACADEMIC_YEARS = [
    {"name": "2024-2025", "start": date(2024, 8, 12), "end": date(2025, 6, 27), "status": "completed"},
    {"name": "2025-2026", "start": date(2025, 8, 11), "end": date(2026, 6, 26), "status": "completed"},
    {"name": "2026-2027", "start": date(2026, 8, 10), "end": date(2027, 6, 25), "status": "active"},
]

TERMS = [
    {"name": "First Term", "start": (8, 12), "end": (12, 20)},
    {"name": "Second Term", "start": (1, 4), "end": (4, 10)},
    {"name": "Third Term", "start": (4, 13), "end": (6, 25)},
]

# Global roles that can see every campus (matches accounts/access.py).
GLOBAL_ROLES = [
    "super_admin", "admin", "org_admin", "head_office", "academic",
]

ROLE_USER_SPECS = [
    # (username, email, first_name, last_name, role, designation)
    ("demo_superadmin", "superadmin.demo@example.test", "Demo", "Superadmin",
     Role.SUPER_ADMIN, None),
    ("demo_orgadmin", "orgadmin.demo@example.test", "Demo", "Org Admin",
     Role.ORG_ADMIN, "Organization Administrator"),
]


def _campus_role_users(campus):
    """Return per-campus staff user specs for ``campus`` (a CAMPUS_INFO dict)."""
    c = campus["code"].lower()
    return [
        (f"{c}.admin", f"{c}.admin@example.test", "Campus", "Administrator",
         Role.CAMPUS_ADMIN, "Campus Administrator"),
        (f"principal.{c}", f"principal.{c}@example.test", "Principal", "Lead",
         Role.PRINCIPAL, "Principal"),
        (f"accountant.{c}", f"accountant.{c}@example.test", "Accounts", "Officer",
         Role.ACCOUNTANT, "Accountant"),
        (f"hr.{c}", f"hr.{c}@example.test", "Human", "Resources",
         Role.HR, "HR Officer"),
        (f"reception.{c}", f"reception.{c}@example.test", "Front", "Desk",
         Role.RECEPTIONIST, "Receptionist"),
        (f"librarian.{c}", f"librarian.{c}@example.test", "Head", "Librarian",
         Role.LIBRARIAN, "Librarian"),
        (f"clerk.{c}", f"clerk.{c}@example.test", "Inventory", "Clerk",
         Role.STAFF, "Inventory & Transport Clerk"),
        (f"guard.{c}", f"guard.{c}@example.test", "Security", "Guard",
         Role.GUARD, "Security Guard"),
    ]


class SeedContext:
    """State shared by all seeding modules."""

    def __init__(self, stdout=None, style=None):
        self.stdout = stdout
        self.style = style
        self.school = None
        self.campuses = {}            # code -> Campus
        self.campuses_by_name = {}    # name -> Campus
        self.codes_by_name = {}       # name -> code
        self.years = {}               # name -> AcademicYear
        self.active_year = None
        self.terms = {}               # (year_name, term_name) -> Term
        self.classes = {}             # module-registered lookups
        self.sections = {}
        self.users = {}               # username -> User (cache)
        self.roles = {}               # (username, role) -> True
        self.counts = Counter()
        self.notes = []
        self._staff_seq = Counter()
        self._lazy = set()

    # -- logging --------------------------------------------------------------
    def log(self, msg):
        if self.stdout is not None:
            self.stdout.write(f"[seed_demo_data] {msg}")

    def ok(self, msg):
        if self.stdout is not None:
            self.stdout.write(self.style.SUCCESS(f"[seed_demo_data] {msg}"))

    def warn(self, msg):
        if self.stdout is not None:
            self.stdout.write(self.style.WARNING(f"[seed_demo_data] WARNING: {msg}"))

    def err(self, msg):
        if self.stdout is not None:
            self.stdout.write(self.style.ERROR(f"[seed_demo_data] ERROR: {msg}"))

    def count(self, name, n=1):
        self.counts[name] += n

    def note(self, msg):
        self.notes.append(msg)


# ---------------------------------------------------------------------------
# Model get-or-create helpers
# ---------------------------------------------------------------------------

def getc(model, defaults=None, **lookup):
    """Thin get_or_create wrapper returning (obj, created)."""
    return model.objects.get_or_create(defaults=defaults, **lookup)


def get_or_create_school():
    """Idempotent creation of the demo school."""
    school, _ = School.objects.get_or_create(
        code=DEMO_SCHOOL_CODE,
        defaults={
            "name": DEMO_SCHOOL_NAME,
            "institution_type": "school",
            "timezone": "Asia/Karachi",
            "currency": "PKR",
            "address": "Demo Education Group Headquarters, Lahore",
            "city": "Lahore",
            "status": "active",
            "is_paused": False,
        },
    )
    return school


# ---------------------------------------------------------------------------
# Users / memberships / roles
# ---------------------------------------------------------------------------

# NB: Changing this cached hash invalidates every stored demo password. Keep it
# in sync with DEMO_PASSWORD. It is PRODUCTION-SAFE because it only short-circuits
# hashing for the single known demo password (identical for all demo accounts);
# real users never match it and always retain their own password.
_CACHED_DEMO_HASH = None


def _cached_demo_hash():
    """Lazily compute one PBKDF2 hash for DEMO_PASSWORD and reuse it for all
    demo users, avoiding ~950 calls to the (expensive) password hasher."""
    global _CACHED_DEMO_HASH
    if _CACHED_DEMO_HASH is None:
        _CACHED_DEMO_HASH = make_password(DEMO_PASSWORD)
    return _CACHED_DEMO_HASH


def make_user(ctx, username, email, first_name, last_name,
              password=DEMO_PASSWORD, is_staff=False, is_superuser=False):
    """Idempotent user creation. Demo passwords are always reset so the
    credential documentation stays accurate across re-runs.

    Optimization: because every demo account shares the same dev password, we
    reuse a single pre-computed hash for new users and skip re-hashing when an
    existing user already carries that exact hash. This cuts the seeding time
    for Part 2 dramatically without touching production password settings."""
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_staff": is_staff,
            "is_superuser": is_superuser,
        },
    )
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    if is_staff:
        user.is_staff = True
    if is_superuser:
        user.is_superuser = True
    if user.password != _cached_demo_hash():
        # Bypass set_password() (which re-hashes via make_password, ~3s each)
        # and assign the pre-computed hash directly.  This keeps the seed fast
        # while preserving the same stored credential for every demo account.
        user.password = _cached_demo_hash()
    user.save()
    ctx.users[username] = user
    if created:
        ctx.count("users")
    return user, created


def membership(ctx, user, school=None):
    """Active institutional membership for ``user`` in the demo school."""
    school = school or ctx.school
    mem, created = InstitutionMembership.objects.get_or_create(
        user=user,
        institution=school,
        defaults={"status": "active"},
    )
    if created:
        ctx.count("memberships")
    return mem


def assign_roles(ctx, user, roles, school=None):
    """Assign roles to ``user`` in the demo school (idempotent)."""
    mem = membership(ctx, user, school=school)
    for role in roles:
        _, created = RoleAssignment.objects.get_or_create(
            membership=mem, role=role
        )
        if created:
            ctx.count(f"role:{role}")
            ctx.roles[(user.username, role)] = True


def role_user(ctx, username, email, first_name, last_name, role, *,
              designation=None, campus=None, department="", gender="female",
              joining_date=None):
    """Create a user with a single role, plus a staff profile when
    ``designation`` is supplied (staff-scoped roles need ``primary_campus``)."""
    user, created = make_user(ctx, username, email, first_name, last_name)
    assign_roles(ctx, user, [role])
    if designation:
        staff_profile(ctx, user, first_name, last_name, designation=designation,
                      campus=campus, department=department, gender=gender,
                      joining_date=joining_date)
    elif campus is not None:
        # Roles like academic head office may still want a campus anchor.
        staff_profile(ctx, user, first_name, last_name, designation=designation or "Staff",
                      campus=campus, department=department, gender=gender,
                      joining_date=joining_date)
    return user


def staff_profile(ctx, user, first_name, last_name, *, designation,
                  campus=None, department="", gender="female",
                  joining_date=None):
    """Create or fetch the StaffProfile for ``user``.

    ``campus`` may be a Campus instance or a campus code/name string.
    Employee numbers are unique per institution and stable across re-runs.
    """
    campus_obj = resolve_campus(ctx, campus) if campus else None
    seq = ctx._staff_seq[campus_obj.id if campus_obj else "none"] + 1
    ctx._staff_seq[campus_obj.id if campus_obj else "none"] = seq
    code = campus_code(ctx, campus_obj) if campus_obj else "HO"

    defaults = {
        "user": user,
        "primary_campus": campus_obj,
        "first_name": first_name,
        "last_name": last_name,
        "gender": gender,
        "phone": "",
        "email": user.email,
        "campus": campus_obj.name if campus_obj else "",
        "designation": designation,
        "department": department,
        "joining_date": joining_date or date(2019, 8, 1),
        "status": "active",
    }
    # Idempotency is keyed on (institution, user): user_id is UNIQUE, so
    # re-runs always reuse the existing profile. employee_number is NOT
    # stable (the seq counter is shared with role_user/base_users), so never
    # use it as a lookup key; only for new rows, and bump past any collision.
    profile = StaffProfile.objects.filter(
        institution=ctx.school, user=user
    ).first()
    if profile is not None:
        return profile
    num = seq
    while StaffProfile.objects.filter(
        institution=ctx.school, employee_number=f"{code}-{num:04d}"
    ).exists():
        num += 1
    employee_number = f"{code}-{num:04d}"
    profile = StaffProfile.objects.create(
        institution=ctx.school,
        employee_number=employee_number,
        **defaults,
    )
    profile.membership = membership(ctx, user)
    profile.save(update_fields=["membership"])
    ctx.count("staff_profiles")
    return profile


def resolve_campus(ctx, campus):
    """Return a Campus from a Campus instance, code, or name."""
    if isinstance(campus, Campus):
        return campus
    if isinstance(campus, str):
        if campus.upper() in ctx.campuses:
            return ctx.campuses[campus.upper()]
        if campus in ctx.campuses_by_name:
            return ctx.campuses_by_name[campus]
    return None


def campus_code(ctx, campus):
    return ctx.codes_by_name.get(campus.name)


# ---------------------------------------------------------------------------
# Base users (created by part1, lazily by later parts)
# ---------------------------------------------------------------------------

def base_users(ctx):
    """Ensure every foundation user exists (school admins + per campus staff)."""
    specs = list(ROLE_USER_SPECS)
    for info in CAMPUS_INFO:
        specs.extend(_campus_role_users(info))
        specs.append(_academic_lead(info))

    for idx, spec in enumerate(specs):
        username, email, first, last, role = spec[:5]
        designation = spec[5] if len(spec) > 5 else None
        user = role_user(
            ctx, username, email, first, last, role,
            designation=designation,
            campus=code_for_username(username),
        )
    ctx._base_users_done = True
    return True


def _academic_lead(info):
    c = info["code"].lower()
    return (f"academic.{c}", f"academic.{c}@example.test", "Academic", "Lead",
            Role.ACADEMIC, "Academic Coordinator")


def code_for_username(username):
    """Infer campus code from a per-campus username (``gvc.admin`` -> GVC)."""
    for info in CAMPUS_INFO:
        if username.startswith(info["code"].lower() + "."):
            return info["code"]
    return None


def lazy_actor(ctx, role):
    """Return a demo user able to perform ``role`` side effects.

    Used by parts that run standalone so a missing user never blocks the seed.
    """
    if role in {Role.SUPER_ADMIN, Role.ORG_ADMIN, Role.CAMPUS_ADMIN,
                Role.ACCOUNTANT, Role.HR, Role.LIBRARIAN, Role.RECEPTIONIST,
                Role.GUARD, Role.STAFF, Role.ACADEMIC}:
        base_users(ctx)
        hints = {
            Role.CAMPUS_ADMIN: ("gvc.admin",),
            Role.ACCOUNTANT: ("accountant.gvc",),
            Role.HR: ("hr.gvc",),
            Role.LIBRARIAN: ("librarian.gvc",),
            Role.RECEPTIONIST: ("reception.gvc",),
            Role.GUARD: ("guard.gvc",),
            Role.STAFF: ("clerk.gvc",),
        }
        for username in hints.get(role, ()) or ():
            if username in ctx.users:
                return ctx.users[username]
        return ctx.users.get("demo_superadmin")

    if role == Role.TEACHER:
        ctx.note("Teacher actor created lazily (part1/part2 missing).")
        user, _ = make_user(ctx, "teacher.demo", "teacher.demo@example.test",
                            "Demo", "Teacher")
        assign_roles(ctx, user, [Role.TEACHER])
        return user

    if role == Role.STUDENT:
        ctx.note("Student actor created lazily (part1/part2 missing).")
        user, _ = make_user(ctx, "student.demo", "student.demo@example.test",
                            "Demo", "Student")
        assign_roles(ctx, user, [Role.STUDENT])
        return user

    if role == Role.PARENT:
        ctx.note("Parent actor created lazily (part1/part2 missing).")
        user, _ = make_user(ctx, "parent.demo", "parent.demo@example.test",
                            "Demo", "Parent")
        assign_roles(ctx, user, [Role.PARENT])
        return user

    return ctx.users.get("demo_superadmin")


# ---------------------------------------------------------------------------
# Academic structure bootstrap
# ---------------------------------------------------------------------------

@transaction.atomic
def build_context(stdout=None, style=None):
    """Create the school, campuses, years and terms. Cheap and idempotent, so
    any part may be run standalone."""
    ctx = SeedContext(stdout=stdout, style=style)
    school = get_or_create_school()
    ctx.school = school
    ctx.counts["schools"] = 1

    for info in CAMPUS_INFO:
        campus, created = Campus.objects.get_or_create(
            school=school, name=info["name"],
            defaults={
                "address": info["address"],
                "city": info["city"],
                "status": "active",
            },
        )
        ctx.campuses[info["code"]] = campus
        ctx.campuses_by_name[info["name"]] = campus
        ctx.codes_by_name[info["name"]] = info["code"]
        ctx.counts["campuses"] = 1

    for year_info in ACADEMIC_YEARS:
        year, _ = AcademicYear.objects.get_or_create(
            school=school, name=year_info["name"],
            defaults={
                "start_date": year_info["start"],
                "end_date": year_info["end"],
                "status": year_info["status"],
            },
        )
        year.start_date = year_info["start"]
        year.end_date = year_info["end"]
        year.status = year_info["status"]
        year.save()
        ctx.years[year_info["name"]] = year
        if year_info["status"] == "active":
            ctx.active_year = year

        for term_info in TERMS:
            term, _ = Term.objects.get_or_create(
                academic_year=year, name=term_info["name"],
                defaults={
                    "start_date": year.start_date.replace(
                        month=term_info["start"][0], day=term_info["start"][1]),
                    "end_date": year.start_date.replace(
                        month=term_info["end"][0], day=term_info["end"][1]),
                    "status": "completed" if year_info["status"] == "completed" else "active",
                },
            )
            ctx.terms[(year_info["name"], term_info["name"])] = term

    for info in CAMPUS_INFO:
        unit, created = AcademicUnit.objects.get_or_create(
            campus=ctx.campuses[info["code"]], name=f"{info['name']} Unit",
            defaults={"status": "active"},
        )
        ctx.counts["academic_units"] = 0 if unit.id else 1

    # Load the academic structure (classes + sections) so that any part can be
    # run standalone. part2_academics populates these from the DB already, but
    # parts 3-5 rely on them and may be invoked without part 2 in the same run.
    _load_academic_structure(ctx)

    return ctx


def _load_academic_structure(ctx):
    """Populate ctx.classes (``code:ClassName`` -> Class) and
    ctx.sections (``code:ClassName:Section`` -> Section) from the DB,
    keyed the same way part2_academics keys them, so later parts can run
    standalone without re-running part 2."""
    from apps.schools.models import AcademicUnit, Class as SchClass, Section as SchSection

    ctx.classes = {}
    ctx.sections = {}
    for code, campus in ctx.campuses.items():
        unit = AcademicUnit.objects.filter(campus=campus).first()
        if not unit:
            continue
        for cls in SchClass.objects.filter(unit=unit):
            key = f"{code}:{cls.name}"
            ctx.classes[key] = cls
            for section in SchSection.objects.filter(class_obj=cls):
                ctx.sections[f"{key}:{section.name}"] = section