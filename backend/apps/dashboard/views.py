
from django.db.models import Sum
from django.http import JsonResponse

from apps.attendance.models import Attendance
from apps.finance.models import Invoice, Payment
from apps.exams.models import Exam, StudentResult
from apps.schools.models import Campus, Class, Section
from apps.students.models import Student, Enrollment
from apps.teachers.models import Teacher


def dashboard_overview(request):
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


def dashboard_attendance(request):
    data = {
        "present": Attendance.objects.filter(
            status="present"
        ).count(),
        "absent": Attendance.objects.filter(
            status="absent"
        ).count(),
        "late": Attendance.objects.filter(
            status="late"
        ).count(),
        "leave": Attendance.objects.filter(
            status="leave"
        ).count(),
    }

    return JsonResponse(data)


def dashboard_finance(request):
    payments_total = (
        Payment.objects.filter(
            status="completed"
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    data = {
        "invoices": Invoice.objects.count(),
        "paid": Invoice.objects.filter(
            status="paid"
        ).count(),
        "partial": Invoice.objects.filter(
            status="partial"
        ).count(),
        "issued": Invoice.objects.filter(
            status="issued"
        ).count(),
        "payments_collected": payments_total,
    }

    return JsonResponse(data)


def dashboard_exams(request):
    data = {
        "exams": Exam.objects.count(),
        "results": StudentResult.objects.count(),
        "passed": StudentResult.objects.filter(
            is_pass=True
        ).count(),
        "failed": StudentResult.objects.filter(
            is_pass=False
        ).count(),
    }

    return JsonResponse(data)