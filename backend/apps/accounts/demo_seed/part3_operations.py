"""Part 3 — Operations: attendance, leaves, exams, results, finance.

Creates (idempotently, scoped to DEMO-EDU / ctx.school / ctx.active_year):
- Student attendance (30 working days for all 500 students)
- Student leave requests
- Staff leave requests
- Exams (3 per campus: First Term, Mid Term, Final Term)
- ExamSubjects, ExamSchedules
- StudentResults (realistic marks)
- ReportCards
- FeeCategories, FeeStructures, Invoices, InvoiceItems
- Payments, Concessions, Fines
- Expenses
- Chart of Accounts, JournalEntries
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

import apps.accounts.demo_seed.base as base
from apps.accounts.demo_seed.base import getc

CAMPUS_CODES = ["GVC", "CSC", "BFC", "KHC", "EXC"]
STUDENTS_PER_CAMPUS = 100
ATTENDANCE_DAYS = 30
INV_SEQ = 0
TXN_SEQ = 0


def _working_days(start: date, count: int) -> list[date]:
    """Return ``count`` weekday (Mon-Sat) dates starting from ``start``."""
    days = []
    current = start
    while len(days) < count:
        if current.weekday() < 6:
            days.append(current)
        current += timedelta(days=1)
    return days


def _rand_marks(pct_good=0.4, pct_avg=0.35, pct_weak=0.15, pct_fail=0.10):
    """Return a realistic obtained_marks value out of 100."""
    r = random.random()
    if r < pct_good:
        return random.randint(70, 98)
    elif r < pct_good + pct_avg:
        return random.randint(50, 69)
    elif r < pct_good + pct_avg + pct_weak:
        return random.randint(35, 49)
    else:
        return random.randint(10, 39)


# ---------------------------------------------------------------------------
# ATTENDANCE
# ---------------------------------------------------------------------------

def _seed_attendance(ctx):
    ctx.log("Creating student attendance records...")
    from apps.attendance.models import Attendance
    from apps.students.models import Student, Enrollment

    statuses = ["present"] * 70 + ["absent"] * 10 + ["late"] * 8 + ["half_day"] * 5 + ["excused"] * 7
    start_date = date(2026, 9, 1)
    days = _working_days(start_date, ATTENDANCE_DAYS)

    # Fetch all students grouped by campus
    students = list(
        Student.objects.filter(
            institution=ctx.school, status="active"
        ).select_related("primary_campus").order_by("id")
    )

    created = 0
    for day in days:
        for stu in students:
            if day.weekday() == 5:
                status = "present" if random.random() < 0.5 else "absent"
            else:
                status = random.choice(statuses)

            enrollment = stu.enrollments.filter(
                academic_year=ctx.active_year
            ).first()
            if enrollment is None:
                continue
            _, c = Attendance.objects.get_or_create(
                student=stu,
                date=day,
                defaults={
                    "enrollment": enrollment,
                    "academic_year": ctx.active_year,
                    "campus": stu.primary_campus,
                    "class_obj": enrollment.class_obj if enrollment else None,
                    "section": enrollment.section if enrollment else None,
                    "status": status,
                    "marked_by": ctx.users.get("demo_superadmin"),
                },
            )
            if c:
                created += 1
    ctx.ok(f"Attendance records: {created}")
    ctx.count("attendance", created)


# ---------------------------------------------------------------------------
# STUDENT LEAVE
# ---------------------------------------------------------------------------

def _seed_student_leave(ctx):
    ctx.log("Creating student leave requests...")
    from apps.students.models import StudentLeaveRequest as StudentLeave
    from apps.students.models import Student

    leave_statuses = ["approved", "pending", "rejected", "cancelled"]
    students = list(
        Student.objects.filter(
            institution=ctx.school, status="active"
        )[:50]
    )
    created = 0
    for i, stu in enumerate(students):
        start = date(2026, 9 + (i % 4), 1 + (i % 20))
        end = start + timedelta(days=random.randint(1, 3))
        status = leave_statuses[i % len(leave_statuses)]
        _, c = StudentLeave.objects.get_or_create(
            student=stu,
            start_date=start,
            defaults={
                "end_date": end,
                "reason": f"Personal leave for student {i + 1}",
                "status": status,
                "requested_by": ctx.users.get("demo_superadmin"),
            },
        )
        if c:
            created += 1
    ctx.ok(f"Student leaves: {created}")
    ctx.count("student_leaves", created)


# ---------------------------------------------------------------------------
# STAFF LEAVE
# ---------------------------------------------------------------------------

def _seed_staff_leave(ctx):
    ctx.log("Creating staff leave requests...")
    from apps.accounts.models import StaffLeave

    staff_profiles = list(
        base.StaffProfile.objects.filter(
            institution=ctx.school, status="active"
        )[:30]
    )
    leave_types = ["casual", "sick", "annual", "maternity", "other"]
    statuses = ["approved", "pending", "rejected"]
    created = 0
    for i, sp in enumerate(staff_profiles):
        lt = leave_types[i % len(leave_types)]
        start = date(2026, 9 + (i % 4), 5 + (i % 20))
        end = start + timedelta(days=random.randint(1, 5))
        status = statuses[i % len(statuses)]
        _, c = StaffLeave.objects.get_or_create(
            institution=ctx.school,
            staff=sp,
            start_date=start,
            defaults={
                "end_date": end,
                "leave_type": lt,
                "reason": f"Staff leave request {i + 1}",
                "status": status,
            },
        )
        if c:
            created += 1
    ctx.ok(f"Staff leaves: {created}")
    ctx.count("staff_leaves", created)


# ---------------------------------------------------------------------------
# EXAMS + EXAM SUBJECTS + SCHEDULES + RESULTS
# ---------------------------------------------------------------------------

def _seed_exams(ctx):
    ctx.log("Creating exams, schedules, marks, results...")
    from apps.exams.models import Exam, ExamSubject, ExamSchedule, StudentResult
    from apps.schools.models import Class, Section, Subject, SubjectOffering
    from apps.students.models import Student, Enrollment
    from apps.teachers.models import Teacher

    year = ctx.active_year
    terms = list(
        base.Term.objects.filter(academic_year=year).order_by("id")
    )
    if len(terms) < 3:
        ctx.warn("Need 3 terms for exam seed; using first available term.")
        terms = [terms[0]] * 3 if terms else []

    exam_specs = [
        ("First Term Examination", "midterm", 0, date(2026, 10, 15), date(2026, 10, 25)),
        ("Mid Term Examination", "midterm", 1, date(2027, 1, 10), date(2027, 1, 20)),
        ("Final Term Examination", "annual", 2, date(2027, 4, 5), date(2027, 4, 15)),
    ]

    teachers = list(Teacher.objects.filter(institution=ctx.school, primary_campus__isnull=False))
    subjects = list(Subject.objects.filter(institution=ctx.school))
    subj_map = {s.code: s for s in subjects}

    all_results = 0
    all_schedules = 0

    for campus_code in CAMPUS_CODES:
        campus = ctx.campuses[campus_code]
        campus_classes = [
            (k, v) for k, v in ctx.classes.items()
            if k.startswith(f"{campus_code}:")
        ]
        campus_teachers = [t for t in teachers if t.primary_campus_id == campus.id]

        for exam_name, exam_type, term_idx, start, end in exam_specs:
            term = terms[term_idx] if term_idx < len(terms) else terms[0] if terms else None

            for cls_key, cls in campus_classes:
                if cls.name in ("Playgroup", "Nursery", "Kindergarten"):
                    continue

                exam, created = Exam.objects.get_or_create(
                    name=exam_name,
                    class_obj=cls,
                    academic_year=year,
                    campus=campus,
                    defaults={
                        "exam_type": exam_type,
                        "term": term,
                        "start_date": start,
                        "end_date": end,
                        "status": "completed",
                    },
                )
                if not created:
                    continue
                ctx.count("exams")

                # Exam subjects
                offering_codes = []
                try:
                    offerings = SubjectOffering.objects.filter(
                        academic_year=year, class_obj=cls
                    )
                    offering_codes = [o.subject.code for o in offerings]
                except Exception:
                    pass

                exam_subjects = []
                for code in offering_codes:
                    subj = subj_map.get(code)
                    if subj:
                        es, _ = ExamSubject.objects.get_or_create(
                            exam=exam,
                            subject=subj,
                            defaults={"maximum_marks": 100, "passing_marks": 40},
                        )
                        exam_subjects.append(es)
                        ctx.count("exam_subjects")

                # Exam schedules
                sections = [
                    v for k, v in ctx.sections.items()
                    if k.startswith(f"{campus_code}:") and k.endswith(f":{cls.name.split()[-1]}")
                ][:3]
                if not sections:
                    sections = list(Section.objects.filter(class_obj=cls))[:3]

                for es_idx, es in enumerate(exam_subjects[:3]):
                    sched_date = start + timedelta(days=es_idx)
                    invigilator = campus_teachers[es_idx % len(campus_teachers)] if campus_teachers else None
                    for sec in sections:
                        ExamSchedule.objects.get_or_create(
                            exam=exam,
                            section=sec,
                            exam_subject=es,
                            defaults={
                                "date": sched_date,
                                "start_time": time(9, 0),
                                "end_time": time(11, 0),
                                "room": f"Room E{exam.id}-{campus_code}-{es_idx + 1}-{sec.name}",
                                "invigilator": invigilator,
                            },
                        )
                        all_schedules += 1

                # Student results
                from apps.schools.models import Section as SecModel
                all_sections = list(SecModel.objects.filter(class_obj=cls))
                students = list(
                    Student.objects.filter(
                        institution=ctx.school,
                        primary_campus=campus,
                        enrollments__class_obj=cls,
                        enrollments__academic_year=year,
                        status="active",
                    ).distinct()
                )

                for stu in students:
                    for es in exam_subjects:
                        is_absent = random.random() < 0.02
                        if is_absent:
                            obt = Decimal("0.00")
                        else:
                            obt = Decimal(str(_rand_marks()))

                        sr, res_created = StudentResult.objects.get_or_create(
                            exam=exam,
                            student=stu,
                            exam_subject=es,
                            defaults={
                                "obtained_marks": obt,
                                "is_absent": is_absent,
                            },
                        )
                        if res_created:
                            all_results += 1

    ctx.ok(f"Exams: {ctx.counts.get('exams', 0)}, ExamSubjects: {ctx.counts.get('exam_subjects', 0)}, "
           f"Schedules: {all_schedules}, Results: {all_results}")
    ctx.count("exam_schedules", all_schedules)
    ctx.count("results", all_results)


# ---------------------------------------------------------------------------
# REPORT CARDS
# ---------------------------------------------------------------------------

def _seed_report_cards(ctx):
    ctx.log("Creating report cards...")
    from apps.exams.models import Exam, StudentResult
    from apps.reportcards.models import ReportCard, ReportCardSubject
    from apps.students.models import Student

    exams = Exam.objects.filter(
        campus__in=list(ctx.campuses.values()),
        academic_year=ctx.active_year,
        status="completed",
    )
    created = 0
    for exam in exams:
        students = Student.objects.filter(
            institution=ctx.school,
            primary_campus=exam.campus,
            enrollments__academic_year=ctx.active_year,
            enrollments__class_obj=exam.class_obj,
            status="active",
        ).distinct()
        for stu in students[:15]:
            rc, rc_created = ReportCard.objects.get_or_create(
                student=stu,
                exam=exam,
                defaults={
                    "status": "published",
                    "published_at": timezone.now(),
                    "teacher_remarks": f"Demo report card for {stu.first_name} {stu.last_name}",
                },
            )
            if rc_created:
                created += 1
                ctx.count("report_cards")

                results = StudentResult.objects.filter(
                    exam=exam, student=stu
                )
                for res in results:
                    es = res.exam_subject
                    max_m = es.maximum_marks
                    pct = (res.obtained_marks / Decimal(str(max_m)) * 100) if max_m else Decimal("0")
                    ReportCardSubject.objects.get_or_create(
                        report_card=rc,
                        exam_subject=es,
                        defaults={
                            "obtained_marks": res.obtained_marks,
                            "maximum_marks": max_m,
                            "percentage": pct.quantize(Decimal("0.01")),
                            "grade": res.grade,
                            "is_pass": res.is_pass,
                        },
                    )

    ctx.ok(f"Report cards: {created}")


# ---------------------------------------------------------------------------
# FEE CATEGORIES + STRUCTURES + INVOICES + PAYMENTS
# ---------------------------------------------------------------------------

def _seed_finance(ctx):
    global INV_SEQ, TXN_SEQ
    ctx.log("Creating fee categories, structures, invoices, payments...")
    from apps.finance.models import (
        FeeCategory, FeeStructure, Invoice, InvoiceItem,
        Payment, Concession, Fine, Expense, Account, JournalEntry, JournalLine,
    )
    from apps.students.models import Student, Enrollment

    year = ctx.active_year

    # --- Fee Categories ---
    fee_cats_data = [
        ("Admission Fee", "one_time", 5000),
        ("Tuition Fee", "monthly", 8000),
        ("Examination Fee", "term", 3000),
        ("Transport Fee", "monthly", 4000),
        ("Library Fee", "annual", 2000),
        ("Activity Fee", "term", 1500),
        ("Miscellaneous", "one_time", 1000),
    ]
    fee_cats = {}
    for name, freq, _ in fee_cats_data:
        fc, _ = getc(
            FeeCategory,
            institution=ctx.school,
            name=name,
            defaults={"frequency": freq, "status": "active"},
        )
        fee_cats[name] = fc
        ctx.count("fee_categories")

    # --- Fee Structures ---
    for campus_code in CAMPUS_CODES:
        campus = ctx.campuses[campus_code]
        campus_classes = [
            v for k, v in ctx.classes.items()
            if k.startswith(f"{campus_code}:") and not k.split(":")[1] in ("Playgroup", "Nursery", "Kindergarten")
        ]
        for cls in campus_classes[:8]:
            for name, _, amount in fee_cats_data:
                getc(
                    FeeStructure,
                    academic_year=year,
                    campus=campus,
                    class_obj=cls,
                    category=fee_cats[name],
                    defaults={"amount": Decimal(str(amount))},
                )
                ctx.count("fee_structures")

    # --- Invoices + Items + Payments ---
    students = list(
        Student.objects.filter(
            institution=ctx.school,
            status="active",
        ).select_related("primary_campus")
    )
    invoice_count = 0
    payment_count = 0
    concession_count = 0
    fine_count = 0

    for i, stu in enumerate(students):
        enrollment = Enrollment.objects.filter(
            student=stu, academic_year=year
        ).first()
        if not enrollment:
            continue

        INV_SEQ += 1
        inv_num = f"DEMO-INV-{INV_SEQ:06d}"
        issue = date(2026, 9, 1)
        due = date(2026, 10, 10)

        inv, inv_created = Invoice.objects.get_or_create(
            institution=ctx.school,
            invoice_number=inv_num,
            defaults={
                "student": stu,
                "enrollment": enrollment,
                "academic_year": year,
                "issue_date": issue,
                "due_date": due,
                "status": "issued",
            },
        )
        if not inv_created:
            continue
        invoice_count += 1
        ctx.count("invoices")

        # Invoice items
        tuition = fee_cats.get("Tuition Fee")
        if tuition:
            InvoiceItem.objects.get_or_create(
                invoice=inv,
                category=tuition,
                defaults={"description": "Monthly Tuition Fee", "amount": Decimal("8000")},
            )
        exam_fee = fee_cats.get("Examination Fee")
        if exam_fee:
            InvoiceItem.objects.get_or_create(
                invoice=inv,
                category=exam_fee,
                defaults={"description": "Examination Fee", "amount": Decimal("3000")},
            )

        total = Decimal("11000")

        # Payment statuses: 75% paid, 15% partial, 10% unpaid
        r = random.random()
        if r < 0.75:
            TXN_SEQ += 1
            rec_num = f"DEMO-REC-{TXN_SEQ:06d}"
            Payment.objects.get_or_create(
                institution=ctx.school,
                receipt_number=rec_num,
                defaults={
                    "invoice": inv,
                    "amount": total,
                    "payment_date": due,
                    "payment_method": "cash",
                    "status": "completed",
                },
            )
            payment_count += 1
            ctx.count("payments")
            inv.status = "paid"
            inv.save(update_fields=["status"])
        elif r < 0.90:
            TXN_SEQ += 1
            rec_num = f"DEMO-REC-{TXN_SEQ:06d}"
            partial = total * Decimal(str(random.uniform(0.3, 0.7))).quantize(Decimal("0.01"))
            Payment.objects.get_or_create(
                institution=ctx.school,
                receipt_number=rec_num,
                defaults={
                    "invoice": inv,
                    "amount": partial,
                    "payment_date": due,
                    "payment_method": "bank",
                    "status": "completed",
                },
            )
            payment_count += 1
            ctx.count("payments")
            inv.status = "partial"
            inv.save(update_fields=["status"])
        else:
            inv.status = "overdue"
            inv.save(update_fields=["status"])

        # Concessions (every 20th student)
        if i % 20 == 0 and i > 0:
            Concession.objects.get_or_create(
                institution=ctx.school,
                invoice=inv,
                defaults={
                    "type": "scholarship",
                    "amount": Decimal("2000"),
                    "reason": "Merit scholarship for demo student",
                    "status": "approved",
                },
            )
            concession_count += 1
            ctx.count("concessions")

        # Fines (every 30th student)
        if i % 30 == 0 and i > 0:
            Fine.objects.get_or_create(
                institution=ctx.school,
                student=stu,
                academic_year=year,
                defaults={
                    "type": "late_payment",
                    "amount": Decimal("500"),
                    "reason": "Late fee submission",
                    "status": "approved",
                },
            )
            fine_count += 1
            ctx.count("fines")

    ctx.ok(f"Invoices: {invoice_count}, Payments: {payment_count}, "
           f"Concessions: {concession_count}, Fines: {fine_count}")


# ---------------------------------------------------------------------------
# EXPENSES
# ---------------------------------------------------------------------------

def _seed_expenses(ctx):
    ctx.log("Creating expenses and chart of accounts...")
    from apps.finance.models import Expense, Account, JournalEntry, JournalLine

    # Chart of Accounts
    accounts_data = [
        ("1000", "Cash", "asset"),
        ("1100", "Bank Account", "asset"),
        ("1200", "Accounts Receivable", "asset"),
        ("2000", "Accounts Payable", "liability"),
        ("3000", "Equity", "equity"),
        ("4000", "Tuition Income", "income"),
        ("4100", "Exam Fee Income", "income"),
        ("4200", "Transport Income", "income"),
        ("5000", "Salary Expense", "expense"),
        ("5100", "Utility Expense", "expense"),
        ("5200", "Maintenance Expense", "expense"),
        ("5300", "Stationery Expense", "expense"),
        ("5400", "Transport Expense", "expense"),
    ]
    accounts = {}
    for code, name, atype in accounts_data:
        acc, _ = getc(
            Account,
            institution=ctx.school,
            code=code,
            defaults={"name": name, "account_type": atype, "is_active": True},
        )
        accounts[code] = acc
        ctx.count("finance_accounts")

    # Expenses
    expense_specs = [
        ("Utility Bill", "5100", 45000),
        ("Staff Salaries", "5000", 500000),
        ("Maintenance", "5200", 25000),
        ("Stationery Purchase", "5300", 15000),
        ("Transport Fuel", "5400", 30000),
        ("Event Expense", "5200", 20000),
        ("Repair Work", "5200", 18000),
        ("Cleaning Supplies", "5300", 8000),
    ]
    expense_account = accounts.get("5000")
    payment_account = accounts.get("1000")
    superuser = ctx.users.get("demo_superadmin")
    je_count = 0

    for campus_code in CAMPUS_CODES:
        campus = ctx.campuses[campus_code]
        for name, acc_code, amount in expense_specs:
            exp, created = Expense.objects.get_or_create(
                institution=ctx.school,
                campus=campus,
                expense_account=expense_account,
                payment_account=payment_account,
                defaults={
                    "vendor": f"Demo Vendor - {name}",
                    "expense_date": date(2026, 9 + ((hash(name) % 4)), 1 + (abs(hash(name)) % 27)),
                    "amount": Decimal(str(amount)),
                    "status": "approved",
                    "reference": f"DEMO-EXP-{campus_code}-{name[:4].upper()}",
                    "notes": f"Demo expense: {name} for {campus.name}",
                    "created_by": superuser,
                },
            )
            if created:
                ctx.count("expenses")

                # Journal entry for each expense
                JE_code = accounts.get("1000")
                je, _ = JournalEntry.objects.get_or_create(
                    institution=ctx.school,
                    campus=campus,
                    source_type="expense",
                    source_id=str(exp.id),
                    defaults={
                        "posting_date": exp.expense_date,
                        "description": f"Expense: {name} - {campus.name}",
                        "status": "posted",
                        "created_by": superuser,
                        "posted_by": superuser,
                        "posted_at": timezone.now(),
                    },
                )
                if je:
                    je_count += 1
                    JournalLine.objects.get_or_create(
                        entry=je, account=expense_account,
                        defaults={"debit": Decimal(str(amount)), "memo": name},
                    )
                    JournalLine.objects.get_or_create(
                        entry=je, account=payment_account,
                        defaults={"credit": Decimal(str(amount)), "memo": f"Payment for {name}"},
                    )

    ctx.ok(f"Accounts: {len(accounts)}, Expenses: {ctx.counts.get('expenses', 0)}, JournalEntries: {je_count}")
    ctx.count("journal_entries", je_count)


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------

@transaction.atomic
def run(ctx):
    ctx.log("Part 3: operations (attendance, exams, results, finance).")

    # Standalone part: ensure the foundation/base users exist so that
    # non-null actor FKs (e.g. StudentLeaveRequest.requested_by) resolve.
    base.base_users(ctx)

    # Re-seed student list for this part
    _seed_attendance(ctx)
    _seed_student_leave(ctx)
    _seed_staff_leave(ctx)
    _seed_exams(ctx)
    _seed_report_cards(ctx)
    _seed_finance(ctx)
    _seed_expenses(ctx)

    ctx.ok("Part 3 done.")
