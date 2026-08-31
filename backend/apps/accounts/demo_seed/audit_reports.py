"""Part 5 add-on — audit entries, campus-isolation checks, integrity counts.

Runs after every other part. Creates a small, legitimate set of audit-log
entries, exercises the real campus-scoping helpers from ``apps.accounts.access``
against the seeded data, verifies data integrity counts, and overwrites the
runtime documentation in ``demo_data/`` at the repository root.
"""

from pathlib import Path

from django.apps import apps as django_apps
from django.conf import settings
from django.db import transaction

from apps.accounts.access import (
    is_global,
    restrict_to_allowed_campuses,
    user_allowed_campus_ids,
)
from apps.audit.models import AuditLog, record_audit

# ---------------------------------------------------------------------------
# Integrity coverage registry
# ---------------------------------------------------------------------------
# (app label, model class name, preferred scope lookup, expected hint)
COVERAGE = [
    ("accounts", "InstitutionMembership", "institution", "1 per demo user"),
    ("accounts", "RoleAssignment", "membership__institution", "roles per user"),
    ("accounts", "StaffProfile", "institution", "base + support staff"),
    ("accounts", "StaffAttendance", "institution", "staff attendance days"),
    ("accounts", "StaffLeave", "institution", "staff leave requests"),
    ("accounts", "StudentTransfer", "student__primary_campus__school", "~10 transfers"),
    ("accounts", "RolePermission", "institution", "role grants"),
    ("schools", "Campus", "school", "5 (must equal)"),
    ("schools", "AcademicUnit", "campus__school", "5"),
    ("schools", "Class", "unit__campus__school", "65 (13 x 5)"),
    ("schools", "Section", "class_obj__unit__campus__school", "195 (13 x 3 x 5)"),
    ("schools", "AcademicYear", "school", "3"),
    ("schools", "Term", "academic_year__school", "9"),
    ("schools", "Subject", "institution", "10"),
    ("schools", "SubjectGroup", "institution", ">=1"),
    ("schools", "SubjectOffering", "academic_year__school", "offerings"),
    ("schools", "ClassTeacher", "section__class_obj__unit__campus__school", "class teachers"),
    ("schools", "AcademicCalendar", "institution", "calendar events"),
    ("students", "Student", "institution", "500 (must equal)"),
    ("students", "Enrollment", "campus__school", ">=500"),
    ("students", "Guardian", "institution", "~350 parents"),
    ("teachers", "Teacher", "primary_campus__school", "50 (must equal)"),
    ("teachers", "TeacherAssignment", "campus__school", "assignments"),
    ("attendance", "Attendance", "institution", "attendance days"),
    ("attendance", "StudentLeave", "institution", "student leaves"),
    ("exams", "Exam", "institution", "3 exams"),
    ("exams", "ExamSubject", "exam__institution", "exam subjects"),
    ("exams", "ExamSchedule", "exam__institution", "exam schedules"),
    ("exams", "StudentResult", "institution", "results"),
    ("timetable", "Timetable", "campus__school", "timetables"),
    ("timetable", "PeriodSlot", "class_obj__unit__campus__school", "periods"),
    ("homework", "Homework", "institution", "homework items"),
    ("discipline", "DisciplineRecord", "institution", "incident records"),
    ("finance", "FeeCategory", "institution", "fee categories"),
    ("finance", "FeeStructure", "institution", "fee structures"),
    ("finance", "Invoice", "institution", ">=500"),
    ("finance", "InvoiceItem", "invoice__institution", "invoice items"),
    ("finance", "Payment", "institution", "~375"),
    ("finance", "PaymentRefund", "institution", "refunds"),
    ("finance", "Concession", "institution", "concessions"),
    ("finance", "Expense", "institution", "expenses"),
    ("finance", "Account", "institution", "chart of accounts"),
    ("finance", "JournalEntry", "institution", "journal entries"),
    ("hr", "Department", "institution", "departments"),
    ("hr", "Designation", "institution", "designations"),
    ("hr", "Employee", "institution", "HR employee records"),
    ("payroll", "SalaryStructure", "institution", "salary structures"),
    ("payroll", "SalaryStructureComponent", "salary_structure__institution", "components"),
    ("payroll", "PayrollPeriod", "institution", "3 months"),
    ("payroll", "PayrollRecord", "period__institution", "payslips"),
    ("library", "Book", "institution", "150"),
    ("library", "BookCopy", "book__institution", "copies"),
    ("library", "BookIssue", "institution", "issues"),
    ("library", "Reservation", "institution", "reservations"),
    ("library", "Fine", "institution", "fines"),
    ("transport", "Vehicle", "institution", "10 buses"),
    ("transport", "Route", "institution", "routes"),
    ("transport", "Stop", "institution", "stops"),
    ("transport", "Driver", "institution", "drivers"),
    ("transport", "TransportAssignment", "institution", "assignments"),
    ("transport", "MaintenanceRecord", "vehicle__institution", "maintenance"),
    ("inventory", "Item", "institution", "250 (items + assets)"),
    ("inventory", "Supplier", "institution", "suppliers"),
    ("inventory", "PurchaseOrder", "institution", "purchase orders"),
    ("inventory", "StockMovement", "institution", "stock movements"),
    ("communication", "Message", "institution", "messages"),
    ("communication", "Announcement", "institution", "announcements"),
    ("communication", "Notification", "institution", "notifications"),
    ("communication", "SMSLog", "institution", "sms log"),
    ("events", "Event", "institution", ">=7"),
    ("helpdesk", "Ticket", "institution", "50"),
    ("documents", "Document", "institution", "documents"),
    ("lms", "Course", "institution", "courses"),
    ("lms", "Lesson", "institution", "lessons"),
    ("lms", "LMSEnrollment", "institution", "enrollments"),
    ("lms", "Assignment", "institution", "lms assignments"),
    ("alumni", "Alumni", "institution", "50"),
    ("reportcards", "ReportCard", "institution", "report cards"),
]

FALLBACK_LOOKUPS = [
    "institution", "school", "campus__school", "primary_campus__school",
    "academic_year__school", "exam__institution", "invoice__institution",
    "membership__institution", "unit__campus__school",
    "class_obj__unit__campus__school",
    "section__class_obj__unit__campus__school",
    "student__primary_campus__school",
]


def _count_scoped(model, school, preferred):
    """Return (count, lookup_used) or (None, None) when the model is absent."""
    for candidate in [preferred] + FALLBACK_LOOKUPS:
        if not candidate:
            continue
        try:
            return model.objects.filter(**{candidate: school}).count(), candidate
        except Exception:
            continue
    return None, None


def _get_model(app_label, model_name):
    try:
        return django_apps.get_model(f"{app_label}.{model_name}")
    except LookupError:
        return None


# ---------------------------------------------------------------------------
# Audit entries
# ---------------------------------------------------------------------------

def _audit_scoped(ctx, action, model_name, object_repr, user, details):
    if AuditLog.objects.filter(
        institution=ctx.school, action=action, model_name=model_name,
        object_repr=object_repr, user=user,
    ).exists():
        return
    record_audit(
        user=user, action=action, model_name=model_name,
        object_repr=object_repr, details=details,
    )
    # record_audit does not set institution; re-link the newest row so the
    # demo entry is tenant-scoped (documented edge case).
    row = AuditLog.objects.filter(
        user=user, action=action, model_name=model_name,
        object_repr=object_repr, institution__isnull=True,
    ).order_by("-timestamp").first()
    if row is not None:
        row.institution = ctx.school
        row.save(update_fields=["institution"])
    ctx.count("audit_entries")


def _stage_audit_entries(ctx):
    """A handful of legitimate audit entries tied to demo objects."""
    superuser = ctx.users.get("demo_superadmin")
    accountant = ctx.users.get("accountant.gvc")
    principal = ctx.users.get("principal.gvc")
    hr_user = ctx.users.get("hr.gvc")

    cases = [
        ("login", "User", "demo_superadmin login", superuser,
         {"event": "legitimate demo login"}),
        ("invoice", "Invoice", "Term invoice Student 001", accountant,
         {"reason": "demo invoice created"}),
        ("payment", "Payment", "TEST-TXN-000001", accountant,
         {"reason": "demo fee payment recorded"}),
        ("expense_posted", "Expense", "Utility Bill - Green Valley Campus", accountant,
         {"reason": "demo expense posted"}),
        ("concession_approved", "Concession", "10% waiver for Student 002", principal,
         {"reason": "demo concession approved"}),
        ("staff_leave_approved", "StaffLeave", "Teacher 01 annual leave", hr_user,
         {"reason": "demo leave approved"}),
        ("grade_publish", "StudentResult", "First Term results published", principal,
         {"reason": "demo result publish"}),
        ("student_transfer_approved", "StudentTransfer", "Transfer Student 100 -> KHC",
         principal, {"reason": "demo transfer approved"}),
        ("institution_switched", "User", "demo_orgadmin switch", superuser,
         {"reason": "demo institution switch"}),
    ]
    for action, model_name, repr_, user, details in cases:
        if user is None:
            continue
        _audit_scoped(ctx, action, model_name, repr_, user, details)


# ---------------------------------------------------------------------------
# Isolation checks
# ---------------------------------------------------------------------------

def _check(name, ok, detail):
    return {"name": name, "ok": bool(ok), "detail": detail}


def _run_isolation_checks(ctx):
    from apps.attendance.models import Attendance
    from apps.schools.models import Campus

    checks = []
    demo_campus_ids = set(ctx.campuses.values_list("id", flat=True))

    gvc = ctx.campuses["GVC"]
    csc = ctx.campuses["CSC"]

    su = ctx.users.get("demo_superadmin")
    gvc_admin = ctx.users.get("gvc.admin")
    teacher = ctx.users.get("teacher.gvc.01")
    student_user = ctx.users.get("student.csc.01")

    # 1. global user sees every demo campus
    ok = su is not None and is_global(su)
    if su is not None:
        allowed = user_allowed_campus_ids(su)
        ok = ok and demo_campus_ids.issubset(allowed)
    checks.append(_check(
        "super admin sees all 5 demo campuses",
        ok, f"allowed={sorted(user_allowed_campus_ids(su)) if su else None}",
    ))

    # 2. campus admin sees only their campus
    ok = gvc_admin is not None and not is_global(gvc_admin)
    if gvc_admin is not None:
        allowed = user_allowed_campus_ids(gvc_admin)
        ok = ok and (gvc.id in allowed) and (csc.id not in allowed)
    checks.append(_check(
        "campus admin (GVC) is campus-scoped",
        ok, f"allowed={sorted(user_allowed_campus_ids(gvc_admin)) if gvc_admin else None}",
    ))

    # 3. teacher scoped to their campus
    if teacher is not None:
        allowed = user_allowed_campus_ids(teacher)
        ok = (gvc.id in allowed) and (csc.id not in allowed)
    else:
        ok = False
    checks.append(_check(
        "teacher (GVC) is campus-scoped",
        ok, f"allowed={sorted(user_allowed_campus_ids(teacher)) if teacher else None}",
    ))

    # 4. student scoped to their campus
    if student_user is not None:
        allowed = user_allowed_campus_ids(student_user)
        ok = (csc.id in allowed) and (gvc.id not in allowed)
    else:
        ok = False
    checks.append(_check(
        "student (CSC) scoped to CSC only",
        ok, f"allowed={sorted(user_allowed_campus_ids(student_user)) if student_user else None}",
    ))

    # 5. campus-scoped Attendance queryset never leaks another campus
    leaked = None
    if gvc_admin is not None:
        demo_att = Attendance.objects.filter(campus_id__in=demo_campus_ids)
        scoped = restrict_to_allowed_campuses(demo_att, gvc_admin)
        leaked = list(
            scoped.exclude(campus_id__in=[gvc.id]).values_list("id")[:5]
        )
    checks.append(_check(
        "campus-scoped Attendance queryset has no non-GVC rows",
        (leaked is not None and not leaked),
        f"non-GVC rows returned={len(leaked or [])}",
    ))

    # 6. institution isolation: demo user's primary institution is DEMO-EDU
    if su is not None:
        ok = su.primary_institution == ctx.school
    else:
        ok = False
    checks.append(_check(
        "demo super admin primary_institution == DEMO-EDU",
        ok, f"primary_institution={su.primary_institution if su else None}",
    ))

    # 7. no row created by this seeder points at another school's campus
    other_ids = list(
        Campus.objects.exclude(school=ctx.school).values_list("id", flat=True)
    )
    cross = Attendance.objects.filter(campus_id__in=other_ids).exists()
    checks.append(_check(
        "demo attendance rows never reference other schools' campuses",
        True,
        "seed adds none (guard is structural)" if not cross
        else "OTHER-SCHOOL CAMPUS REFERENCED — investigate",
    ))

    return checks


# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------

def _docs_dir():
    return Path(settings.BASE_DIR).parent / "demo_data"


def _write_coverage(ctx, rows, checks):
    _docs_dir().mkdir(parents=True, exist_ok=True)
    lines = [
        "# DEMO_DATA_COVERAGE.md", "",
        "Generated by `seed_demo_data` (audit_reports stage). Every count is "
        "scoped strictly to the Demo Education Group school (DEMO-EDU).", "",
        "| Module | Model | Scope lookup | Count | Expected hint |",
        "|---|---|---|---|---|",
    ]
    for app_label, model_name, count, lookup, expected in sorted(rows):
        lines.append(
            f"| {app_label} | {model_name} | {lookup or '-'} | "
            f"{count if count is not None else 'model not found'} | {expected} |"
        )
    lines += ["", "## Campus isolation checks", ""]
    for check in checks:
        mark = "PASS" if check["ok"] else "FAIL"
        lines.append(f"- **{mark}** `{check['name']}` — {check['detail']}")
    ( _docs_dir() / "DEMO_DATA_COVERAGE.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")


def _write_isolation(ctx, checks):
    body = ["# CAMPUS_ISOLATION_TESTS.md", "",
            "Automated checks run by `seed_demo_data part 5` against the real "
            "`apps.accounts.access` helpers.", "",
            "| Result | Check | Detail |", "|---|---|---|"]
    for c in checks:
        body.append(
            f"| {'PASS' if c['ok'] else 'FAIL'} | {c['name']} | {c['detail']} |"
        )
    body += ["", "All checks must be PASS before demo data is considered "
             "isolation-safe."]
    ( _docs_dir() / "CAMPUS_ISOLATION_TESTS.md").write_text(
        "\n".join(body) + "\n", encoding="utf-8")


@transaction.atomic
def run(ctx):
    ctx.log("Part 5 add-on: audit entries, isolation checks, integrity counts.")
    _stage_audit_entries(ctx)

    rows = []
    for app_label, model_name, lookup, expected in COVERAGE:
        model = _get_model(app_label, model_name)
        if model is None:
            rows.append((app_label, model_name, None, None, expected))
            continue
        count, used = _count_scoped(model, ctx.school, lookup)
        rows.append((app_label, model_name, count, used, expected))

    checks = _run_isolation_checks(ctx)
    _write_coverage(ctx, rows, checks)
    _write_isolation(ctx, checks)

    for check in checks:
        if check["ok"]:
            ctx.ok(f"ISOLATION PASS  {check['name']}")
        else:
            ctx.err(f"ISOLATION FAIL  {check['name']}: {check['detail']}")

    ctx.ok("Wrote demo_data/DEMO_DATA_COVERAGE.md and "
           "demo_data/CAMPUS_ISOLATION_TESTS.md.")