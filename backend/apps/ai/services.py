"""Offline, deterministic AI services for the school ERP.

Every function takes the request and returns data that is strictly scoped
to the active institution, the user's campuses, and the user's role. No
external model calls, network requests, or third-party libraries are used
- everything is computed from the ERP's own data.

All queries use the platform's standard multi-tenancy helpers:

- ``get_institution`` clamps everything to the active school.
- ``apply_campus_scope`` clamps each queryset to the campuses the user may
  access (uses the field mapping for that model).
- role helper gates (``is_manager`` / ``is_teacher`` / ``is_parent`` /
  ``is_student``) keep teachers, parents and students inside their own
  read set, mirroring the rest of the API.
"""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q
from django.utils import timezone

from apps.accounts.access import apply_campus_scope, get_institution
from apps.accounts.scopes import (
    get_student_profile,
    is_manager,
    is_parent,
    is_student,
    is_teacher,
    parent_student_ids,
    teacher_student_ids,
)

ATTENDANCE_STATUS_CHOICES = ["present", "late"]


def ai_institution(request):
    return get_institution(request)


def effective_deny(request, codename):
    """True when the user has an explicit, unexpired deny for a codename.

    Superusers bypass explicit denies, matching the platform's other
    permission logic.
    """
    from apps.accounts.models import UserPermission

    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return True

    if user.is_superuser:
        return False

    institution = get_institution(request)
    if institution is None:
        return False

    now = timezone.now()
    return UserPermission.objects.filter(
        user=user,
        institution=institution,
        permission__codename=codename,
        effect="deny",
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now),
    ).exists()


def _finance_allowed(user):
    return is_manager(user) or user.has_any_role(["accountant", "hr"])


def _student_serialize(student):
    full_name = getattr(student, "full_name", None) or (
        f"{student.first_name} {student.last_name}".strip()
    )
    return {
        "id": student.pk,
        "name": full_name,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "admission_number": student.admission_number,
        "status": student.status,
    }


def scoped_students_qs(request):
    """Students visible to the user (institution + campus + role)."""
    from apps.students.models import Student

    institution = get_institution(request)
    queryset = Student.objects.all()
    if institution is not None:
        queryset = queryset.filter(institution=institution)
    queryset = apply_campus_scope(
        queryset, request, "primary_campus_id", institution_field=None
    )

    user = request.user
    if is_manager(user):
        return queryset
    if is_teacher(user):
        return queryset.filter(pk__in=teacher_student_ids(user))
    if is_parent(user):
        return queryset.filter(pk__in=parent_student_ids(user))
    if is_student(user):
        profile = get_student_profile(user)
        if profile is not None:
            return queryset.filter(pk=profile.pk)
        return queryset.none()
    return queryset.none()


def _role_scoped_attendance(request, queryset):
    user = request.user
    if is_teacher(user) and not is_manager(user):
        return queryset.filter(student_id__in=teacher_student_ids(user))
    return queryset


def _attendance_stats(request, student_id, days=30):
    from apps.attendance.models import Attendance

    what_ = get_institution(request)
    since = timezone.localdate() - timedelta(days=days)
    queryset = Attendance.objects.filter(student_id=student_id, date__gte=since)
    if what_ is not None:
        queryset = queryset.filter(enrollment__academic_year__school=what_)
    queryset = apply_campus_scope(
        queryset, request, "campus_id", institution_field=None
    )

    total = queryset.count()
    present = queryset.filter(status__in=ATTENDANCE_STATUS_CHOICES).count()
    absent = queryset.filter(status="absent").count()
    rate = round(present / total * 100, 1) if total else None
    return {"days": total, "present": present, "absent": absent, "rate": rate}


def _fee_stats(request, student_id):
    from apps.finance.models import Invoice

    institution = get_institution(request)
    queryset = Invoice.objects.filter(
        student_id=student_id,
        status__in=["issued", "partial", "overdue"],
    )
    if institution is not None:
        queryset = queryset.filter(institution=institution)
    queryset = apply_campus_scope(
        queryset, request, "campus_id", institution_field=None
    )

    today = timezone.localdate()
    outstanding = Decimal("0.00")
    overdue_amount = Decimal("0.00")
    overdue_count = 0
    for invoice in queryset:
        balance = invoice.balance
        outstanding += balance
        if balance > 0 and invoice.due_date and invoice.due_date < today:
            overdue_count += 1
            overdue_amount += balance

    return {
        "invoice_count": len(list(queryset)),
        "outstanding": str(outstanding),
        "overdue_count": overdue_count,
        "overdue_amount": str(overdue_amount),
    }


def _latest_exam(request, exam_id=None):
    from apps.exams.models import Exam

    institution = get_institution(request)
    queryset = Exam.objects.all()
    if exam_id is not None:
        queryset = queryset.filter(pk=exam_id)
    if institution is not None:
        queryset = queryset.filter(academic_year__school=institution)
    queryset = apply_campus_scope(queryset, request, "campus_id", institution_field=None)
    return queryset.order_by("-end_date").first()


def _academic_stats(request, exam, student_id):
    if exam is None:
        return {}

    from apps.exams.models import StudentResult

    queryset = StudentResult.objects.filter(
        exam=exam,
        student_id=student_id,
        is_absent=False,
    )
    queryset = apply_campus_scope(
        queryset, request, "exam__campus_id", institution_field=None
    )
    results = list(queryset.select_related("exam_subject"))
    if not results:
        return {}

    percentages = []
    passed = 0
    for result in results:
        maximum = result.exam_subject.maximum_marks
        if maximum:
            percentages.append(float(result.obtained_marks) / float(maximum) * 100.0)
        if result.is_pass:
            passed += 1

    term_name = exam.term.name if exam.term_id else ""
    return {
        "exam": exam.name,
        "term": term_name,
        "subjects_count": len(results),
        "average_percent": round(sum(percentages) / len(percentages), 1)
        if percentages
        else None,
        "pass_rate": round(passed / len(results) * 100, 1),
    }


def student_insights(request, student_id=None):
    """Per-student attendance / fee / academic snapshot cards."""
    queryset = scoped_students_qs(request)
    if student_id is not None:
        queryset = queryset.filter(pk=student_id)

    exam = _latest_exam(request)
    rows = []
    for student in queryset[: (1 if student_id is not None else 20)]:
        rows.append(
            {
                **_student_serialize(student),
                "attendance": _attendance_stats(request, student.pk),
                "fees": _fee_stats(request, student.pk),
                "academic": _academic_stats(request, exam, student.pk),
            }
        )
    return rows


def attendance_insights(request, days=30):
    from apps.attendance.models import Attendance

    institution = get_institution(request)
    since = timezone.localdate() - timedelta(days=days)
    queryset = Attendance.objects.filter(date__gte=since)
    if institution is not None:
        queryset = queryset.filter(enrollment__academic_year__school=institution)
    queryset = apply_campus_scope(queryset, request, "campus_id", institution_field=None)
    queryset = _role_scoped_attendance(request, queryset)

    total = queryset.count()
    present = queryset.filter(status__in=ATTENDANCE_STATUS_CHOICES).count()
    rate = round(present / total * 100, 1) if total else None

    status_breakdown = {
        entry["status"]: entry["count"]
        for entry in (
            queryset.values("status").annotate(count=Count("id")).order_by("status")
        )
    }

    top_absentees = list(
        queryset.filter(status="absent")
        .values(
            "student__first_name",
            "student__last_name",
            "student__admission_number",
            "student_id",
        )
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )

    below_threshold = []
    per_student = queryset.values("student_id").annotate(
        total=Count("id"),
        present=Count("id", filter=Q(status__in=ATTENDANCE_STATUS_CHOICES)),
        absent=Count("id", filter=Q(status="absent")),
    )
    for row in per_student:
        student_rate = row["present"] / row["total"] * 100
        if student_rate < 75:
            below_threshold.append(
                {
                    "student_id": row["student_id"],
                    "rate": round(student_rate, 1),
                    "absent": row["absent"],
                }
            )
    below_threshold.sort(key=lambda entry: entry["rate"])
    below_threshold = below_threshold[:10]

    return {
        "days": days,
        "records": total,
        "present": present,
        "overall_rate": rate,
        "status_breakdown": status_breakdown,
        "top_absentees": top_absentees,
        "students_below_75": below_threshold,
    }


def academic_insights(request, exam_id=None):
    from apps.exams.models import StudentResult

    exam = _latest_exam(request, exam_id=exam_id)
    if exam is None:
        return {"exam": None, "subjects": [], "overall_pass_rate": None}

    user = request.user
    result_qs = StudentResult.objects.filter(exam=exam, is_absent=False)
    result_qs = apply_campus_scope(
        result_qs, request, "exam__campus_id", institution_field=None
    )
    if is_teacher(user) and not is_manager(user):
        result_qs = result_qs.filter(student_id__in=teacher_student_ids(user))

    results = list(result_qs.select_related("exam_subject__subject"))
    if not results:
        return {"exam": exam.name, "subjects": [], "overall_pass_rate": None}

    subjects = {}
    total_passed = 0
    for result in results:
        key = result.exam_subject_id
        bucket = subjects.setdefault(key, {"name": result.exam_subject.subject.name, "entries": 0, "passed": 0, "percentages": []})
        bucket["entries"] += 1
        if result.is_pass:
            bucket["passed"] += 1
            total_passed += 1
        maximum = result.exam_subject.maximum_marks
        if maximum:
            bucket["percentages"].append(float(result.obtained_marks) / float(maximum) * 100.0)

    subject_rows = []
    for bucket in subjects.values():
        count = bucket["entries"]
        subject_rows.append(
            {
                "subject": bucket["name"],
                "entries": count,
                "pass_rate": round(bucket["passed"] / count * 100, 1),
                "average_percent": round(sum(bucket["percentages"]) / len(bucket["percentages"]), 1)
                if bucket["percentages"]
                else None,
            }
        )
    subject_rows.sort(key=lambda entry: entry["pass_rate"])

    term_name = exam.term.name if exam.term_id else ""
    return {
        "exam": exam.name,
        "term": term_name,
        "overall_pass_rate": round(total_passed / len(results) * 100, 1),
        "subjects": subject_rows,
    }


def finance_insights(request):
    from apps.finance.models import Invoice

    institution = get_institution(request)
    queryset = Invoice.objects.filter(
        status__in=["issued", "partial", "overdue"],
    )
    if institution is not None:
        queryset = queryset.filter(institution=institution)
    queryset = apply_campus_scope(queryset, request, "campus_id", institution_field=None)

    today = timezone.localdate()
    total_outstanding = Decimal("0.00")
    total_paid = Decimal("0.00")
    overdue_count = 0
    overdue_amount = Decimal("0.00")
    by_student = {}
    count = 0
    for invoice in queryset:
        count += 1
        balance = invoice.balance
        total_outstanding += balance
        total_paid += invoice.paid_amount
        if balance > 0 and invoice.due_date and invoice.due_date < today:
            overdue_count += 1
            overdue_amount += balance
        if balance > 0:
            student_key = invoice.student_id
            entry = by_student.setdefault(student_key, {"student_id": student_key, "outstanding": Decimal("0.00"), "name": _invoice_student_name(invoice)})
            entry["outstanding"] += balance

    top_outstanding = sorted(
        (entry for entry in by_student.values()),
        key=lambda entry: entry["outstanding"],
        reverse=True,
    )[:5]
    for entry in top_outstanding:
        entry["outstanding"] = str(entry["outstanding"])

    return {
        "invoice_count": count,
        "total_outstanding": str(total_outstanding),
        "total_paid": str(total_paid),
        "overdue_count": overdue_count,
        "overdue_amount": str(overdue_amount),
        "top_outstanding": top_outstanding,
    }


def _invoice_student_name(invoice):
    try:
        return f"{invoice.student.first_name} {invoice.student.last_name}".strip()
    except Exception:
        return "Unknown Student"


def anomalies(request):
    """Rule-based anomaly scan across the user's scope."""
    items = []

    attendance = attendance_insights(request, days=21)
    for entry in attendance.get("students_below_75", []):
        items.append(
            {
                "category": "attendance",
                "severity": "high" if entry["rate"] < 60 else "medium",
                "title": "Low attendance",
                "detail": (
                    f"Student #{entry['student_id']} has {entry['rate']}% "
                    f"attendance over the last 21 days."
                ),
                "student_id": entry["student_id"],
            }
        )

    academic = academic_insights(request)
    for subject in academic.get("subjects", []):
        if subject["pass_rate"] is not None and subject["pass_rate"] < 60:
            items.append(
                {
                    "category": "academic",
                    "severity": "high" if subject["pass_rate"] < 50 else "medium",
                    "title": "Low pass rate",
                    "detail": (
                        f"{subject['subject']} in {academic['exam']} has a "
                        f"{subject['pass_rate']}% pass rate."
                    ),
                }
            )

    user = request.user
    if _finance_allowed(user):
        finance = finance_insights(request)
        if finance["overdue_count"]:
            items.append(
                {
                    "category": "finance",
                    "severity": "high" if finance["overdue_amount"] and Decimal(finance["overdue_amount"]) > 0 else "medium",
                    "title": "Overdue invoices",
                    "detail": (
                        f"{finance['overdue_count']} invoices are past due "
                        f"totalling {finance['overdue_amount']}."
                    ),
                }
            )

    items.sort(key=lambda item: item["severity"] == "high", reverse=True)
    return items


GREETING_TERMS = ["hi", "hello", "hey", "help", "what can you"]


def _intent_for(query):
    lowered = query.lower()
    if any(term in lowered for term in GREETING_TERMS):
        return "greeting"
    if any(word in lowered for word in ("fee", "balance", "outstanding", "arrears", "pay", "money", "invoice")):
        return "finance"
    if any(word in lowered for word in ("attend", "absent", "present", "attendance", "truan")):
        return "attendance"
    if any(word in lowered for word in ("mark", "grade", "exam", "result", "score", "gpa")):
        return "academic"
    if any(word in lowered for word in ("how many", "count", "total ", "headcount", "number of")):
        return "counts"
    return "general"


def answer_ask(request, query):
    """Turn a natural-language question into a scoped, deterministic answer."""
    text = (query or "").strip()
    user = request.user
    institution = get_institution(request)
    school_name = institution.name if institution is not None else "your school"
    intent = _intent_for(text)
    digest = {}
    answer = ""

    if intent == "greeting":
        answer = (
            f"Hello! I can answer questions about your school data - attendance, "
            f"fees, exam results, and student counts - always within your access "
            f"level at {school_name}. Try asking 'How is attendance this week?' "
            f"or 'Show overdue fees'."
        )
    elif intent == "finance":
        if not _finance_allowed(user):
            answer = (
                "Your role does not have permission to view finance figures. "
                "Ask an administrator to grant you finance access."
            )
        else:
            data = finance_insights(request)
            digest = data
            answer = (
                f"Outstanding fees at {school_name}: {data['total_outstanding']} "
                f"across {data['invoice_count']} open invoices. "
                f"{data['overdue_count']} are past their due date "
                f"totalling {data['overdue_amount']}."
            )
    elif intent == "attendance":
        data = attendance_insights(request)
        digest = data
        answer = (
            f"Attendance over the last {data['days']} days is "
            f"{data['overall_rate']}% ({data['present']} of "
            f"{data['records']} records present). "
            f"{len(data['students_below_75'])} students are below 75%."
        )
    elif intent == "academic":
        data = academic_insights(request)
        digest = data
        if data.get("exam"):
            answer = (
                f"Latest exam '{data['exam']}' has an overall pass rate of "
                f"{data['overall_pass_rate']}% across "
                f"{len(data['subjects'])} subjects."
            )
        else:
            answer = "No exam results are available yet for your scope."
    elif intent == "counts":
        student_count = scoped_students_qs(request).count()
        teacher_count = 0
        if is_manager(user):
            from apps.teachers.models import Teacher

            teacher_queryset = Teacher.objects.all()
            if institution is not None:
                teacher_queryset = teacher_queryset.filter(institution=institution)
            teacher_queryset = apply_campus_scope(
                teacher_queryset, request, "primary_campus_id", institution_field=None
            )
            teacher_count = teacher_queryset.count()
        digest = {"students": student_count, "teachers": teacher_count}
        answer = (
            f"There are {student_count} students in your scope at {school_name}"
            + (f" and {teacher_count} staff" if is_manager(user) else "")
            + "."
        )
    else:
        home = scoped_students_qs(request).values_list("pk", flat=True)[:1]
        if home:
            answer = (
                f"I understand you are asking about '{text}'. I can answer "
                f"questions about attendance, fees, exam results, and student "
                f"counts at {school_name}."
            )
        else:
            answer = (
                f"No matching data in your scope at {school_name}. Ask about "
                f"attendance, fees, exam results, or student counts."
            )

    return {
        "query": text,
        "intent": intent,
        "answer": answer,
        "digest": digest,
    }


def resolve_entities(request, query, limit=5):
    """Role-scoped entity search used by the AI search endpoint."""
    from django.db.models import Q

    from apps.schools.models import Class as SchoolClass

    text = (query or "").strip()
    result = {"query": text, "entities": []}
    if len(text) < 2:
        return result

    user = request.user
    institution = get_institution(request)

    student_queryset = scoped_students_qs(request).filter(
        Q(first_name__icontains=text)
        | Q(last_name__icontains=text)
        | Q(middle_name__icontains=text)
        | Q(admission_number__icontains=text)
    )
    for student in student_queryset[:limit]:
        result["entities"].append(
            {
                "kind": "student",
                "id": student.pk,
                "name": _student_serialize(student)["name"],
                "admission_number": student.admission_number,
                "status": student.status,
            }
        )

    class_queryset = SchoolClass.objects.all()
    if institution is not None:
        class_queryset = class_queryset.filter(unit__campus__school=institution)
    class_queryset = apply_campus_scope(
        class_queryset, request, "unit__campus_id", institution_field=None
    ).filter(name__icontains=text)
    for school_class in class_queryset[:limit]:
        result["entities"].append(
            {
                "kind": "class",
                "id": school_class.pk,
                "name": school_class.name,
            }
        )

    if is_manager(user):
        from apps.teachers.models import Teacher

        teacher_queryset = Teacher.objects.all()
        if institution is not None:
            teacher_queryset = teacher_queryset.filter(institution=institution)
        teacher_queryset = apply_campus_scope(
            teacher_queryset, request, "primary_campus_id", institution_field=None
        ).filter(Q(first_name__icontains=text) | Q(last_name__icontains=text))
        for teacher in teacher_queryset[:limit]:
            result["entities"].append(
                {
                    "kind": "teacher",
                    "id": teacher.pk,
                    "name": f"{teacher.first_name} {teacher.last_name}".strip(),
                    "employee_number": teacher.employee_number,
                }
            )

    if _finance_allowed(user):
        from apps.finance.models import Invoice

        invoice_queryset = Invoice.objects.all()
        if institution is not None:
            invoice_queryset = invoice_queryset.filter(institution=institution)
        invoice_queryset = apply_campus_scope(
            invoice_queryset, request, "campus_id", institution_field=None
        ).filter(invoice_number__icontains=text)
        for invoice in invoice_queryset[:limit]:
            result["entities"].append(
                {
                    "kind": "invoice",
                    "id": invoice.pk,
                    "invoice_number": invoice.invoice_number,
                    "status": invoice.status,
                    "balance": str(invoice.balance),
                }
            )

    return result


DRAFT_TEMPLATES = {
    "fee_reminder": {
        "subject": "Fee Reminder",
        "body": (
            "Dear Parent/Guardian,\n\n"
            "This is a reminder that there is an outstanding fee balance "
            "of {amount} for {student}. "
            "Kindly settle this before the due date to avoid disruption.\n\n"
            "Regards,\n{school}"
        ),
    },
    "attendance_warning": {
        "subject": "Attendance Notice",
        "body": (
            "Dear Parent/Guardian,\n\n"
            "{student} has recorded several absences recently "
            "({absent} days, {rate}% attendance). "
            "Please ensure regular attendance.\n\n"
            "Regards,\n{school}"
        ),
    },
    "exam_notice": {
        "subject": "Exam Schedule Notice",
        "body": (
            "Dear Parents/Guardians,\n\n"
            "Please note that the upcoming exam '{exam}' "
            "is scheduled from {start} to {end}. "
            "Students are expected to attend all papers.\n\n"
            "Regards,\n{school}"
        ),
    },
    "welcome": {
        "subject": "Welcome to {school}",
        "body": (
            "Dear {student},\n\n"
            "Welcome to {school}! Your admission number is {admission_number}. "
            "We look forward to a great year together.\n\n"
            "Regards,\n{school}"
        ),
    },
    "custom": {
        "subject": "{subject}",
        "body": "{body}",
    },
}


def _safe_format(text, context):
    try:
        return text.format(**context)
    except (KeyError, IndexError, ValueError):
        return text


def draft_communication(request, payload):
    """Draft (never send) a communication for an allowed audience."""
    from apps.students.models import Student

    ctype = (payload.get("type") or "custom").strip().lower()
    if ctype not in DRAFT_TEMPLATES:
        raise ValueError(f"Unknown draft type: {ctype}")

    visible_ids = set(
        scoped_students_qs(request).values_list("pk", flat=True)
    )
    student_ids = payload.get("student_ids") or []
    student_ids = [int(entry) for entry in student_ids if str(entry).strip().isdigit()]

    if student_ids and not set(student_ids).issubset(visible_ids):
        raise PermissionError(
            "One or more students are outside your access scope."
        )

    students = list(
        Student.objects.filter(pk__in=student_ids, id__in=list(visible_ids))
        if student_ids
        else Student.objects.filter(id__in=list(visible_ids))[:3]
    )

    institution = get_institution(request)
    school_name = institution.name if institution is not None else "School"

    context = {
        "school": school_name,
        "subject": (payload.get("subject") or "").strip(),
        "body": (payload.get("body") or "").strip(),
    }
    if students:
        first = students[0]
        snapshot = _student_serialize(first)
        context["student"] = snapshot["name"]
        context["admission_number"] = first.admission_number
        stats = _attendance_stats(request, first.pk)
        context["absent"] = str(stats["absent"])
        context["rate"] = f"{stats['rate']}%" if stats["rate"] is not None else "n/a"
        fees = _fee_stats(request, first.pk)
        context["amount"] = fees["outstanding"]

    if ctype == "custom":
        subject = _safe_format(context["subject"] or "Communication", context)
        body = _safe_format(context["body"] or "(Provide message body)", context)
    else:
        template = DRAFT_TEMPLATES[ctype]
        subject = _safe_format(template["subject"], context)
        body = _safe_format(template["body"], context)

    if ctype == "exam_notice":
        exam = _latest_exam(request)
        if exam is not None:
            context["exam"] = exam.name
            context["start"] = str(exam.start_date)
            context["end"] = str(exam.end_date)
            subject = _safe_format(DRAFT_TEMPLATES[ctype]["subject"], context)
            body = _safe_format(DRAFT_TEMPLATES[ctype]["body"], context)

    return {
        "type": ctype,
        "subject": subject,
        "body": body,
        "recipient_count": len(students),
        "recipient_preview": [_student_serialize(s) for s in students[:5]],
        "draft_only": True,
    }