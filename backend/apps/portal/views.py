"""Role-portal aggregation endpoints.

A single, cheap endpoint per persona so the Teacher and Student portals
render from one request instead of many paginated list calls.
"""

from collections import OrderedDict

from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.accounts.scopes import (
    get_guardian_profile,
    get_student_profile,
    get_teacher_profile,
    teacher_student_ids,
)
from apps.attendance.models import Attendance
from apps.communication.models import Announcement
from apps.exams.models import StudentResult
from apps.finance.models import Payment
from apps.homework.models import Homework, Submission
from apps.hr.models import LeaveBalance, LeaveRequest
from apps.schools.models import AcademicYear
from apps.students.models import Enrollment, Student, StudentLeaveRequest
from apps.teachers.models import TeacherAssignment
from apps.timetable.models import TimetableEntry
from apps.transport.models import TransportAssignment


def _photo_url(request, obj, field="photo"):
    photo = getattr(obj, field, None)

    if not photo:
        return None

    try:
        return request.build_absolute_uri(photo.url)
    except Exception:  # noqa: BLE001 - media may be unavailable
        return None


def _active_year(institution):
    if institution is None:
        return None

    return (
        AcademicYear.objects.filter(school=institution, status="active")
        .order_by("-start_date")
        .first()
    )


def _portal_announcements(user, institution=None, limit=6):
    qs = Announcement.objects.filter(status="published")

    if institution is not None:
        qs = qs.filter(
            Q(institution=institution) | Q(institution__isnull=True)
        )

    qs = qs.order_by(
        "-published_at", "-created_at"
    )[:40]

    out = []
    user_id = user.id

    for ann in qs:
        if user_id in ann.target_user_ids():
            out.append(
                {
                    "id": ann.id,
                    "title": ann.title,
                    "message": ann.message,
                    "category": ann.category,
                    "published_at": ann.published_at,
                    "created_at": ann.created_at,
                }
            )

            if len(out) >= limit:
                break

    return out


def _attendance_summary(student):
    rows = (
        Attendance.objects.filter(student=student)
        .values("status")
        .annotate(count=Count("id"))
    )

    counts = {"present": 0, "absent": 0, "late": 0, "leave": 0}

    for row in rows:
        counts[row["status"]] = row["count"]

    recorded = sum(counts.values())
    present_total = counts["present"] + counts["late"]

    return {
        "attendance_rate": (
            round(present_total / recorded * 100) if recorded else None
        ),
        "recorded_days": recorded,
        "present": present_total,
        "absent": counts["absent"],
        "late": counts["late"],
        "leave": counts["leave"],
    }


def _recent_attendance(student, limit=10):
    return [
        {
            "id": record.id,
            "date": record.date,
            "status": record.status,
            "status_display": record.get_status_display(),
            "class_name": record.class_obj.name,
            "section_name": record.section.name,
        }
        for record in Attendance.objects.filter(student=student)
        .select_related("class_obj", "section")
        .order_by("-date")[:limit]
    ]


def _exam_marks_for_student(student, limit=3):
    results_by_exam = OrderedDict()
    result_rows = (
        StudentResult.objects.filter(student=student)
        .select_related("exam", "exam_subject", "exam_subject__subject")
        .order_by("exam__start_date", "exam_subject__subject__name")
    )

    for result in result_rows:
        key = result.exam_id
        bucket = results_by_exam.get(key)

        if bucket is None:
            bucket = {
                "id": key,
                "name": result.exam.name,
                "exam_type_display": result.exam.get_exam_type_display(),
                "start_date": result.exam.start_date.isoformat(),
                "subjects": [],
                "obtained": 0.0,
                "maximum": 0.0,
                "pass": True,
            }
            results_by_exam[key] = bucket

        subject = result.exam_subject.subject
        bucket["subjects"].append(
            {
                "subject": subject.name,
                "obtained": float(result.obtained_marks),
                "maximum": result.exam_subject.maximum_marks,
                "grade": result.grade or "\u2014",
                "is_pass": result.is_pass,
                "is_absent": result.is_absent,
            }
        )
        bucket["obtained"] += float(result.obtained_marks)
        bucket["maximum"] += float(result.exam_subject.maximum_marks)

        if result.is_absent or not result.is_pass:
            bucket["pass"] = False

    marks = []
    for bucket in results_by_exam.values():
        bucket["percentage"] = (
            round(bucket["obtained"] / bucket["maximum"] * 100, 1)
            if bucket["maximum"]
            else 0
        )
        marks.append(bucket)

    marks.sort(key=lambda item: item.get("start_date") or "", reverse=True)

    if limit is None:
        return marks

    return marks[:limit]


def _timetable_for_section(section):
    return [
        {
            "id": entry.id,
            "day": entry.day,
            "day_display": entry.get_day_display(),
            "period_name": entry.period.name,
            "start_time": entry.period.start_time.strftime("%H:%M"),
            "end_time": entry.period.end_time.strftime("%H:%M"),
            "subject_name": entry.subject.name,
            "teacher_name": entry.teacher.full_name if entry.teacher_id else "",
            "room": entry.room or "",
        }
        for entry in (
            TimetableEntry.objects.filter(
                section=section,
                status="active",
            )
            .select_related("period", "subject", "teacher")
            .order_by("period__number")
        )
    ]


def _homework_for_student(student, enrollment):
    homework_q = Q(class_obj=enrollment.class_obj)

    if enrollment.section_id:
        homework_q &= Q(section_id=None) | Q(section_id=enrollment.section_id)

    homework_rows = list(
        Homework.objects.filter(homework_q)
        .select_related("teacher", "subject", "section")
        .order_by("-due_date", "-id")[:10]
    )

    submission_statuses = dict(
        Submission.objects.filter(
            student=student,
            homework__in=homework_rows,
        ).values_list("homework_id", "status")
    )

    homework = []

    for hw in homework_rows:
        status = submission_statuses.get(hw.id)
        homework.append(
            {
                "id": hw.id,
                "title": hw.title,
                "description": hw.description,
                "subject_name": hw.subject.name if hw.subject_id else "General",
                "teacher_name": hw.teacher.full_name,
                "assigned_date": hw.assigned_date,
                "due_date": hw.due_date,
                "max_marks": hw.max_marks,
                "submission_status": status,
                "submission_status_display": status
                if status is None
                else status.capitalize(),
            }
        )

    return homework


def _invoice_rows_for_student(student):
    invoices = list(
        student.invoices.select_related().order_by("-issue_date")[:10]
    )

    invoice_rows = []
    total_balance = 0.0

    for inv in invoices:
        balance = float(inv.balance)
        total_balance += balance
        invoice_rows.append(
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "issue_date": inv.issue_date,
                "due_date": inv.due_date,
                "total_amount": float(inv.total_amount),
                "paid_amount": float(inv.paid_amount),
                "balance": balance,
                "status": inv.status,
                "status_display": inv.get_status_display(),
            }
        )

    invoice_rows.sort(key=lambda row: row["balance"], reverse=True)
    return invoice_rows, total_balance


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_portal(request):
    user = request.user
    teacher = get_teacher_profile(user)

    if teacher is None:
        return JsonResponse(
            {"detail": "No teacher profile is linked to your account."},
            status=403,
        )

    institution = teacher.institution or user.primary_institution
    year = _active_year(institution)

    assignment_qs = TeacherAssignment.objects.filter(
        teacher=teacher,
        status="active",
    ).select_related("class_obj", "section", "subject", "campus", "academic_year")

    if year is not None:
        assignment_qs = assignment_qs.filter(academic_year=year)

    assignments = list(
        assignment_qs.order_by("class_obj__name", "section__name", "subject__name")
    )

    today_key = timezone.localdate().strftime("%A").lower()

    tt_qs = TimetableEntry.objects.filter(
        teacher=teacher,
        status="active",
        day=today_key,
    ).select_related("period", "class_obj", "section", "subject", "campus")

    if year is not None:
        tt_qs = tt_qs.filter(academic_year=year)

    timetable = [
        {
            "period_name": entry.period.name,
            "start_time": entry.period.start_time.strftime("%H:%M"),
            "end_time": entry.period.end_time.strftime("%H:%M"),
            "class_name": entry.class_obj.name,
            "section_name": entry.section.name,
            "subject_name": entry.subject.name,
            "room": entry.room or "",
            "campus_name": entry.campus.name if entry.campus_id else "",
        }
        for entry in tt_qs.order_by("period__number", "class_obj__name")
    ]

    homework_qs = (
        Homework.objects.filter(teacher=teacher)
        .select_related("class_obj", "section", "subject")
        .order_by("-assigned_date", "-id")[:10]
    )

    homework = []
    for hw in homework_qs:
        counts = hw.submissions.aggregate(
            total=Count("id"),
            graded=Count("id", filter=Q(status="graded")),
        )
        homework.append(
            {
                "id": hw.id,
                "title": hw.title,
                "description": hw.description,
                "class_name": hw.class_obj.name,
                "section_name": hw.section.name if hw.section_id else "Whole class",
                "subject_name": hw.subject.name if hw.subject_id else "General",
                "assigned_date": hw.assigned_date,
                "due_date": hw.due_date,
                "max_marks": hw.max_marks,
                "submissions": counts["total"],
                "graded": counts["graded"],
            }
        )

    leave = {"balances": [], "requests": []}
    employee = getattr(teacher, "employee_record", None)

    if employee is not None:
        leave["balances"] = [
            {
                "id": balance.id,
                "leave_type": balance.leave_type.name,
                "available": float(balance.available_balance),
                "used": float(balance.used),
                "pending": float(balance.pending),
            }
            for balance in LeaveBalance.objects.select_related("leave_type").filter(
                employee=employee
            )
        ]

        leave["requests"] = [
            {
                "id": req.id,
                "leave_type": req.leave_type.name,
                "start_date": req.start_date,
                "end_date": req.end_date,
                "total_days": float(req.total_days or 0),
                "status": req.status,
                "status_display": req.get_status_display(),
                "reason": req.reason,
            }
            for req in LeaveRequest.objects.select_related("leave_type").filter(
                employee=employee
            )[:6]
        ]

    stats = {
        "sections": len({a.section_id for a in assignments}),
        "subjects": len({a.subject_id for a in assignments}),
        "classes": len({a.class_obj_id for a in assignments}),
        "students": len(teacher_student_ids(user)),
        "pending_leaves": sum(
            1
            for req in leave["requests"]
            if req["status"] in ("pending", "submitted")
        ),
    }

    profile = {
        "id": teacher.id,
        "full_name": teacher.full_name,
        "employee_number": teacher.employee_number,
        "designation": teacher.designation,
        "department": teacher.department,
        "phone": teacher.phone,
        "email": teacher.email,
        "photo_url": _photo_url(request, teacher),
        "campus": (
            teacher.primary_campus.name
            if teacher.primary_campus_id
            else (teacher.campus or "")
        ),
        "joining_date": teacher.joining_date,
        "status": teacher.status,
    }

    return JsonResponse(
        {
            "portal": "teacher",
            "academic_year": year.name if year else None,
            "today": today_key,
            "profile": profile,
            "stats": stats,
            "assignments": [
                {
                    "id": a.id,
                    "role": a.role,
                    "role_display": a.get_role_display(),
                    "class_name": a.class_obj.name,
                    "section_name": a.section.name,
                    "subject_name": a.subject.name,
                    "campus_name": a.campus.name,
                    "year_name": a.academic_year.name,
                }
                for a in assignments
            ],
            "timetable": timetable,
            "homework": homework,
            "leave": leave,
            "announcements": _portal_announcements(user, institution=request.institution),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_portal(request):
    user = request.user
    student = get_student_profile(user)

    if student is None:
        return JsonResponse(
            {"detail": "No student profile is linked to your account."},
            status=403,
        )

    enrollment = (
        Enrollment.objects.filter(student=student, status="active")
        .select_related("academic_year", "campus", "class_obj", "section")
        .order_by("-academic_year__start_date")
        .first()
    )

    enrollment_info = None

    if enrollment is not None:
        enrollment_info = {
            "class_name": enrollment.class_obj.name,
            "section_name": enrollment.section.name,
            "campus_name": enrollment.campus.name,
            "roll_number": enrollment.roll_number,
            "academic_year": enrollment.academic_year.name,
        }

    attendance = _attendance_summary(student)

    all_marks = _exam_marks_for_student(student, limit=None)
    marks = all_marks[:3]

    timetable = (
        _timetable_for_section(enrollment.section)
        if enrollment is not None
        else []
    )

    homework = (
        _homework_for_student(student, enrollment)
        if enrollment is not None
        else []
    )

    recent_attendance = _recent_attendance(student)

    invoice_rows, total_balance = _invoice_rows_for_student(student)

    leave_requests = [
        {
            "id": req.id,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "reason": req.reason,
            "status": req.status,
            "status_display": req.get_status_display(),
        }
        for req in StudentLeaveRequest.objects.filter(student=student)[:6]
    ]

    stats = {
        "attendance_rate": attendance["attendance_rate"],
        "recorded_days": attendance["recorded_days"],
        "present": attendance["present"],
        "absent": attendance["absent"],
        "results": len(all_marks),
        "fee_balance": round(total_balance, 2),
        "due_homework": sum(
            1 for hw in homework if hw["submission_status"] is None
        ),
    }

    profile = {
        "id": student.id,
        "full_name": student.full_name,
        "admission_number": student.admission_number,
        "gender": student.get_gender_display(),
        "status": student.status,
        "photo_url": _photo_url(request, student),
        "enrollment": enrollment_info,
    }

    return JsonResponse(
        {
            "portal": "student",
            "profile": profile,
            "stats": stats,
            "marks": marks,
            "timetable": timetable,
            "homework": homework,
            "attendance": recent_attendance,
            "invoices": invoice_rows,
            "leave": leave_requests,
            "announcements": _portal_announcements(user, institution=request.institution),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def parent_portal(request):
    user = request.user
    guardian = get_guardian_profile(user)

    if guardian is None:
        return JsonResponse(
            {"detail": "No guardian profile is linked to your account."},
            status=403,
        )

    children = list(
        Student.objects.filter(guardian=guardian).order_by(
            "first_name", "last_name", "admission_number"
        )
    )

    active_enrollments = {
        enrollment.student_id: enrollment
        for enrollment in Enrollment.objects.filter(
            student__in=children,
            status="active",
        )
        .select_related("academic_year", "campus", "class_obj", "section")
        .order_by("student_id", "-academic_year__start_date")
    }

    children_data = []

    for child in children:
        enrollment = active_enrollments.get(child.id)

        attendance = _attendance_summary(child)

        all_marks = _exam_marks_for_student(child, limit=None)
        marks = all_marks[:3]

        homework = (
            _homework_for_student(child, enrollment)
            if enrollment is not None
            else []
        )

        timetable = (
            _timetable_for_section(enrollment.section)
            if enrollment is not None
            else []
        )

        invoice_rows, fee_balance = _invoice_rows_for_student(child)

        receipts = [
            {
                "id": payment.id,
                "receipt_number": payment.receipt_number,
                "invoice_number": payment.invoice.invoice_number,
                "amount": float(payment.amount),
                "payment_date": payment.payment_date,
                "payment_method": payment.payment_method,
                "payment_method_display": (
                    payment.get_payment_method_display()
                ),
                "reference": payment.reference,
            }
            for payment in Payment.objects.select_related("invoice")
            .filter(invoice__student=child, status="completed")
            .order_by("-payment_date")[:10]
        ]

        leave_requests = [
            {
                "id": req.id,
                "start_date": req.start_date,
                "end_date": req.end_date,
                "reason": req.reason,
                "status": req.status,
                "status_display": req.get_status_display(),
            }
            for req in StudentLeaveRequest.objects.filter(student=child)[:6]
        ]

        transport = [
            {
                "id": assignment.id,
                "route": assignment.route.name,
                "stop": assignment.stop.name if assignment.stop_id else "",
                "status": assignment.status,
            }
            for assignment in TransportAssignment.objects.select_related(
                "route", "stop"
            ).filter(student=child, status="active")
        ]

        teachers = []

        if enrollment is not None:
            teachers = [
                {
                    "id": assignment.id,
                    "role": assignment.role,
                    "role_display": assignment.get_role_display(),
                    "subject_name": assignment.subject.name,
                    "class_name": assignment.class_obj.name,
                    "section_name": assignment.section.name,
                    "teacher_name": assignment.teacher.full_name,
                    "designation": assignment.teacher.designation,
                    "phone": assignment.teacher.phone,
                    "email": assignment.teacher.email,
                }
                for assignment in TeacherAssignment.objects.select_related(
                    "class_obj", "section", "subject", "teacher"
                )
                .filter(
                    class_obj=enrollment.class_obj_id,
                    section=enrollment.section_id,
                    academic_year=enrollment.academic_year_id,
                    status="active",
                )
                .order_by("role", "subject__name")
            ]

        enrollment_info = None

        if enrollment is not None:
            enrollment_info = {
                "class_name": enrollment.class_obj.name,
                "section_name": enrollment.section.name,
                "campus_name": enrollment.campus.name,
                "roll_number": enrollment.roll_number,
                "academic_year": enrollment.academic_year.name,
            }

        children_data.append(
            {
                "id": child.id,
                "full_name": child.full_name,
                "admission_number": child.admission_number,
                "gender": child.get_gender_display(),
                "status": child.status,
                "photo_url": _photo_url(request, child),
                "enrollment": enrollment_info,
                "attendance_rate": attendance["attendance_rate"],
                "recorded_days": attendance["recorded_days"],
                "present": attendance["present"],
                "absent": attendance["absent"],
                "late": attendance["late"],
                "leave": attendance["leave"],
                "fee_balance": round(fee_balance, 2),
                "marks_count": len(all_marks),
                "due_homework": sum(
                    1
                    for hw in homework
                    if hw["submission_status"] is None
                ),
                "marks": marks,
                "homework": homework,
                "timetable": timetable,
                "attendance_records": _recent_attendance(child),
                "invoices": invoice_rows,
                "receipts": receipts,
                "leave": leave_requests,
                "transport": transport,
                "teachers": teachers,
            }
        )

    profile = {
        "id": guardian.id,
        "name": guardian.name,
        "relationship": guardian.relationship,
        "phone": guardian.phone,
        "email": guardian.email,
        "children_count": len(children),
    }

    return JsonResponse(
        {
            "portal": "parent",
            "profile": profile,
            "children": children_data,
            "announcements": _portal_announcements(user, institution=request.institution),
        }
    )