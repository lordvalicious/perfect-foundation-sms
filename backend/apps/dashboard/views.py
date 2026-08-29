from decimal import Decimal

from django.db.models import Count, Sum, Subquery, OuterRef
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.accounts.scopes import (
    get_guardian_profile,
    get_student_profile,
    is_manager,
    is_parent,
    is_student,
    is_teacher,
    parent_student_ids,
    parent_student_class_ids,
    student_class_ids,
    teacher_class_ids,
    teacher_student_ids,
)
from apps.attendance.models import Attendance
from apps.finance.models import Invoice, Payment
from apps.exams.models import Exam, StudentResult
from apps.schools.models import Campus, Class, Section
from apps.students.models import Student, Enrollment
from apps.teachers.models import Teacher


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_overview(request):
    user = request.user

    if is_student(user):
        profile = get_student_profile(user)

        if profile is None:
            return JsonResponse(
                {
                    "students": {"total": 0, "active": 0},
                    "teachers": {"total": 0, "active": 0},
                    "campuses": 0,
                    "classes": 0,
                    "sections": 0,
                    "enrollments": 0,
                }
            )

        enrollments = profile.enrollments.filter(status="active")

        data = {
            "students": {"total": 1, "active": 1},
            "teachers": {
                "total": enrollments.values(
                    "class_obj"
                ).distinct().count(),
                "active": 0,
            },
            "campuses": enrollments.values("campus").distinct().count(),
            "classes": enrollments.values("class_obj").distinct().count(),
            "sections": enrollments.values("section").distinct().count(),
            "enrollments": enrollments.count(),
        }

        return JsonResponse(data)

    if is_parent(user):
        student_ids = parent_student_ids(user)
        enrollments = Enrollment.objects.filter(
            student_id__in=student_ids,
            status="active",
        )

        data = {
            "students": {
                "total": len(student_ids),
                "active": len(
                    Student.objects.filter(
                        pk__in=student_ids,
                        status="active",
                    )
                ),
            },
            "teachers": {
                "total": enrollments.values(
                    "class_obj"
                ).distinct().count(),
                "active": 0,
            },
            "campuses": enrollments.values("campus").distinct().count(),
            "classes": enrollments.values("class_obj").distinct().count(),
            "sections": enrollments.values("section").distinct().count(),
            "enrollments": enrollments.count(),
        }

        return JsonResponse(data)

    if is_teacher(user):
        student_ids = teacher_student_ids(user)
        class_ids = teacher_class_ids(user)

        data = {
            "students": {
                "total": len(student_ids),
                "active": len(student_ids),
            },
            "teachers": {"total": 1, "active": 1},
            "campuses": (
                Teacher.objects.filter(pk=getattr(user, "teacher_profile", None).pk)
                .values("campus")
                .distinct()
                .count()
                if getattr(user, "teacher_profile", None)
                else 0
            ),
            "classes": len(class_ids),
            "sections": (
                Enrollment.objects.filter(
                    class_obj_id__in=class_ids,
                    status="active",
                )
                .values("section")
                .distinct()
                .count()
            ),
            "enrollments": len(student_ids),
        }

        return JsonResponse(data)

    data = {
        "students": {
            "total": Student.objects.count(),
            "active": Student.objects.filter(status="active").count(),
        },
        "teachers": {
            "total": Teacher.objects.count(),
            "active": Teacher.objects.filter(status="active").count(),
        },
        "campuses": Campus.objects.count(),
        "classes": Class.objects.count(),
        "sections": Section.objects.count(),
        "enrollments": Enrollment.objects.filter(
            status="active"
        ).count(),
    }

    return JsonResponse(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_attendance(request):
    user = request.user
    queryset = Attendance.objects.all()

    if is_student(user):
        profile = get_student_profile(user)

        if profile is None:
            return JsonResponse(
                {"present": 0, "absent": 0, "late": 0, "leave": 0}
            )

        queryset = queryset.filter(student=profile)
    elif is_parent(user):
        student_ids = parent_student_ids(user)

        if not student_ids:
            return JsonResponse(
                {"present": 0, "absent": 0, "late": 0, "leave": 0}
            )

        queryset = queryset.filter(student_id__in=student_ids)
    elif is_teacher(user):
        student_ids = teacher_student_ids(user)

        if not student_ids:
            return JsonResponse(
                {"present": 0, "absent": 0, "late": 0, "leave": 0}
            )

        queryset = queryset.filter(student_id__in=student_ids)

    data = {
        "present": queryset.filter(status="present").count(),
        "absent": queryset.filter(status="absent").count(),
        "late": queryset.filter(status="late").count(),
        "leave": queryset.filter(status="leave").count(),
    }

    return JsonResponse(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_finance(request):
    from apps.finance.models import InvoiceItem

    item_totals = InvoiceItem.objects.filter(
        invoice=OuterRef("pk")
    ).values("invoice").annotate(
        total=Sum("amount")
    ).values("total")

    paid_totals = Payment.objects.filter(
        invoice=OuterRef("pk"),
        status="completed",
    ).values("invoice").annotate(
        total=Sum("amount")
    ).values("total")

    invoices = Invoice.objects.annotate(
        items_total=Coalesce(Subquery(item_totals), Decimal("0.00")),
        paid=Coalesce(Subquery(paid_totals), Decimal("0.00")),
    )

    payments_total = (
        Payment.objects.filter(
            status="completed"
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    counts = {}
    for row in invoices.values("status").annotate(c=Count("id")):
        counts[row["status"]] = row["c"]

    total_billed = Decimal("0.00")
    outstanding_total = Decimal("0.00")

    for inv in invoices:
        billed = max(inv.items_total - inv.discount, Decimal("0.00"))
        total_billed += billed
        outstanding_total += max(billed - inv.paid, Decimal("0.00"))

    data = {
        "invoices": invoices.count(),
        "paid": counts.get("paid", 0),
        "partial": counts.get("partial", 0),
        "issued": counts.get("issued", 0),
        "overdue": counts.get("overdue", 0),
        "cancelled": counts.get("cancelled", 0),
        "total_billed": str(total_billed),
        "payments_collected": str(payments_total),
        "outstanding": str(outstanding_total),
    }

    return JsonResponse(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_finance_breakdown(request):
    """Collection by campus / method, monthly collection and
    outstanding student balances. School-wide finance only."""
    user = request.user

    if is_parent(user) or is_student(user):
        return JsonResponse(
            {"detail": "Finance breakdown is not available."},
            status=403,
        )

    from apps.finance.models import InvoiceItem

    item_totals = InvoiceItem.objects.filter(
        invoice=OuterRef("pk")
    ).values("invoice").annotate(
        total=Sum("amount")
    ).values("total")

    paid_totals_sub = Payment.objects.filter(
        invoice=OuterRef("pk"),
        status="completed",
    ).values("invoice").annotate(
        total=Sum("amount")
    ).values("total")

    invoices = Invoice.objects.select_related(
        "enrollment__campus",
        "student",
    ).annotate(
        items_total=Coalesce(Subquery(item_totals), Decimal("0.00")),
        paid=Coalesce(Subquery(paid_totals_sub), Decimal("0.00")),
    )

    campus_totals = {}
    outstanding_rows = []

    for invoice in invoices:
        campus_name = invoice.enrollment.campus.name
        billed = max(invoice.items_total - invoice.discount, Decimal("0.00"))
        balance = max(billed - invoice.paid, Decimal("0.00"))

        entry = campus_totals.setdefault(
            campus_name,
            {"billed": Decimal("0.00"), "collected": Decimal("0.00")},
        )
        entry["billed"] += billed
        entry["collected"] += invoice.paid

        if balance > 0:
            outstanding_rows.append(
                {
                    "student_id": invoice.student_id,
                    "student_name": invoice.student.full_name,
                    "admission_number": invoice.student.admission_number,
                    "campus": campus_name,
                    "invoice_number": invoice.invoice_number,
                    "balance": str(balance),
                }
            )

    completed_payments = Payment.objects.filter(
        status="completed"
    ).select_related("invoice__enrollment__campus")

    method_totals = {}
    monthly_totals = {}

    for payment in completed_payments:
        method = payment.get_payment_method_display()
        method_totals[method] = (
            method_totals.get(method, Decimal("0.00"))
            + payment.amount
        )

        month_key = payment.payment_date.strftime("%Y-%m")
        monthly_totals[month_key] = (
            monthly_totals.get(month_key, Decimal("0.00"))
            + payment.amount
        )

    outstanding_rows.sort(
        key=lambda row: Decimal(row["balance"]),
        reverse=True,
    )

    data = {
        "by_campus": [
            {
                "campus": name,
                "billed": str(values["billed"]),
                "collected": str(values["collected"]),
                "outstanding": str(
                    values["billed"] - values["collected"]
                ),
            }
            for name, values in sorted(campus_totals.items())
        ],
        "by_method": [
            {"method": name, "total": str(total)}
            for name, total in sorted(
                method_totals.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ],
        "monthly": [
            {"month": name, "total": str(total)}
            for name, total in sorted(monthly_totals.items())
        ],
        "outstanding_students": outstanding_rows[:25],
    }

    return JsonResponse(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_exams(request):
    user = request.user
    exams_queryset = Exam.objects.all()
    results_queryset = StudentResult.objects.all()

    if is_student(user):
        profile = get_student_profile(user)

        if profile is None:
            return JsonResponse(
                {
                    "exams": 0,
                    "results": 0,
                    "passed": 0,
                    "failed": 0,
                }
            )

        class_ids = student_class_ids(user)

        if class_ids:
            exams_queryset = exams_queryset.filter(
                class_obj_id__in=class_ids
            )

        results_queryset = results_queryset.filter(student=profile)
    elif is_parent(user):
        student_ids = parent_student_ids(user)
        class_ids = parent_student_class_ids(user)

        if class_ids:
            exams_queryset = exams_queryset.filter(
                class_obj_id__in=class_ids
            )

        if student_ids:
            results_queryset = results_queryset.filter(
                student_id__in=student_ids
            )
        else:
            results_queryset = results_queryset.none()
    elif is_teacher(user):
        student_ids = teacher_student_ids(user)
        class_ids = teacher_class_ids(user)

        if class_ids:
            exams_queryset = exams_queryset.filter(
                class_obj_id__in=class_ids
            )

        if student_ids:
            results_queryset = results_queryset.filter(
                student_id__in=student_ids
            )
        else:
            results_queryset = results_queryset.none()

    data = {
        "exams": exams_queryset.count(),
        "results": results_queryset.count(),
        "passed": results_queryset.filter(is_pass=True).count(),
        "failed": results_queryset.filter(is_pass=False).count(),
    }

    return JsonResponse(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_executive(request):
    """Owner / principal / academic snapshot of the whole school.

    Institution- and campus-scoped to the caller: aggregates people,
    finance, attendance, academics, per-campus comparison, and alerts.
    Manager roles only — students/parents/teachers get 403.
    """
    if not is_manager(request.user):
        return JsonResponse(
            {
                "detail": (
                    "The executive dashboard requires a "
                    "manager role."
                )
            },
            status=403,
        )

    from .executive import executive_dashboard

    return JsonResponse(executive_dashboard(request))
