from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.accounts.scopes import (
    get_student_profile,
    is_manager,
    is_student,
    is_teacher,
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
