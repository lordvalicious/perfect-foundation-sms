"""Parent Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class ParentMasterReportView(AggregateReportView):
    """Parent/Guardian master report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "parent_master"
    model = "apps.students.models.Guardian"

    def get_base_queryset(self, request):
        from apps.students.models import Guardian
        return Guardian.objects.select_related("user", "institution")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        campus = request.query_params.get("campus")
        if campus:
            queryset = queryset.filter(students__primary_campus_id=campus).distinct()

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        with_students = queryset.filter(students__isnull=False).distinct().count()
        without_students = total - with_students

        return {
            "total_guardians": total,
            "with_students": with_students,
            "without_students": without_students,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for guardian in queryset:
            students = guardian.students.all()
            rows.append({
                "name": guardian.name,
                "relationship": guardian.relationship,
                "phone": guardian.phone,
                "alternate_phone": guardian.alternate_phone,
                "email": guardian.email,
                "address": guardian.address,
                "students_count": students.count(),
                "students": ", ".join([s.full_name for s in students]),
                "user_email": guardian.user.email if guardian.user else "-",
            })
        return rows


class ParentStudentRelationshipReportView(AggregateReportView):
    """Parent-student relationship report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "parent_student_relationship"
    model = "apps.students.models.StudentGuardian"

    def get_base_queryset(self, request):
        from apps.students.models import StudentGuardian
        return StudentGuardian.objects.select_related(
            "student", "student__primary_campus", "guardian"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "student__primary_campus_id")

        relationship = request.query_params.get("relationship")
        if relationship:
            queryset = queryset.filter(relationship=relationship)

        is_primary = request.query_params.get("is_primary")
        if is_primary is not None:
            queryset = queryset.filter(is_primary=is_primary.lower() == "true")

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_relationship = queryset.values("relationship").annotate(count=Count("id"))
        primary_count = queryset.filter(is_primary=True).count()

        return {
            "total_relationships": total,
            "primary_guardians": primary_count,
            "by_relationship": list(by_relationship),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for link in queryset:
            rows.append({
                "student_admission": link.student.admission_number,
                "student_name": link.student.full_name,
                "student_class": link.student.enrollments.filter(status="active").first().class_obj.name
                if link.student.enrollments.filter(status="active").exists() else "-",
                "guardian_name": link.guardian.name,
                "relationship": link.relationship,
                "is_primary": "Yes" if link.is_primary else "No",
                "can_pick_up": "Yes" if link.can_pick_up else "No",
                "is_emergency": "Yes" if link.is_emergency_contact else "No",
                "guardian_phone": link.guardian.phone,
                "guardian_email": link.guardian.email,
            })
        return rows


class ParentContactReportView(AggregateReportView):
    """Parent contact information report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "parent_contact"
    model = "apps.students.models.Guardian"

    def get_base_queryset(self, request):
        from apps.students.models import Guardian
        return Guardian.objects.select_related("user", "institution").prefetch_related("students")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        campus = request.query_params.get("campus")
        if campus:
            queryset = queryset.filter(students__primary_campus_id=campus).distinct()

        has_email = request.query_params.get("has_email")
        if has_email == "true":
            queryset = queryset.exclude(Q(email="") | Q(email__isnull=True))
        elif has_email == "false":
            queryset = queryset.filter(Q(email="") | Q(email__isnull=True))

        has_phone = request.query_params.get("has_phone")
        if has_phone == "true":
            queryset = queryset.exclude(Q(phone="") | Q(phone__isnull=True))
        elif has_phone == "false":
            queryset = queryset.filter(Q(phone="") | Q(phone__isnull=True))

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        with_email = queryset.exclude(Q(email="") | Q(email__isnull=True)).count()
        with_phone = queryset.exclude(Q(phone="") | Q(phone__isnull=True)).count()

        return {
            "total_guardians": total,
            "with_email": with_email,
            "with_phone": with_phone,
            "without_email": total - with_email,
            "without_phone": total - with_phone,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for guardian in queryset:
            students = guardian.students.all()
            rows.append({
                "name": guardian.name,
                "phone": guardian.phone,
                "alternate_phone": guardian.alternate_phone,
                "email": guardian.email or "-",
                "address": guardian.address or "-",
                "students": ", ".join([f"{s.full_name} ({s.admission_number})" for s in students]),
            })
        return rows


class ParentWiseStudentsReportView(AggregateReportView):
    """Students grouped by parent."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "parent_wise_students"
    model = "apps.students.models.Student"

    def get_base_queryset(self, request):
        from apps.students.models import Student
        return Student.objects.filter(status="active").select_related(
            "guardian", "primary_campus"
        ).prefetch_related("guardian_links__guardian")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")

        guardian_id = request.query_params.get("guardian")
        if guardian_id:
            queryset = queryset.filter(guardian_id=guardian_id)

        return queryset

    def get_summary(self, queryset, request):
        total_students = queryset.count()
        guardians_with_multiple = 0

        guardian_counts = {}
        for student in queryset:
            gid = student.guardian_id
            if gid:
                guardian_counts[gid] = guardian_counts.get(gid, 0) + 1

        guardians_with_multiple = sum(1 for c in guardian_counts.values() if c > 1)

        return {
            "total_students": total_students,
            "unique_guardians": len(guardian_counts),
            "guardians_with_multiple_children": guardians_with_multiple,
        }

    def get_detail_rows(self, queryset, request):
        # Group by guardian
        guardian_students = {}
        for student in queryset:
            if student.guardian_id:
                gid = student.guardian_id
                if gid not in guardian_students:
                    guardian_students[gid] = {
                        "guardian": student.guardian,
                        "students": [],
                    }
                guardian_students[gid]["students"].append(student)

        rows = []
        for gid, data in guardian_students.items():
            g = data["guardian"]
            for student in data["students"]:
                enrollment = student.enrollments.filter(status="active").first()
                rows.append({
                    "guardian_name": g.name,
                    "guardian_phone": g.phone,
                    "guardian_email": g.email or "-",
                    "student_admission": student.admission_number,
                    "student_name": student.full_name,
                    "student_class": enrollment.class_obj.name if enrollment else "-",
                    "student_section": enrollment.section.name if enrollment and enrollment.section else "-",
                })
        return rows


class OutstandingFeesByParentReportView(AggregateReportView):
    """Outstanding fees grouped by parent."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "parent_outstanding_fees"
    model = "apps.finance.models.Invoice"

    def get_base_queryset(self, request):
        from apps.finance.models import Invoice
        return Invoice.objects.filter(
            status__in=["issued", "partial", "overdue"]
        ).prefetch_related(
            "items", "payments", "concessions"
        ).select_related(
            "student", "student__guardian", "enrollment__campus", "academic_year"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "enrollment__campus_id")

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        return queryset

    def get_summary(self, queryset, request):
        guardians = {}

        for invoice in queryset:
            balance = invoice.balance
            if balance <= 0:
                continue

            guardian = invoice.student.guardian
            if not guardian:
                continue

            gid = guardian.id
            if gid not in guardians:
                guardians[gid] = {
                    "guardian": guardian,
                    "total_invoiced": Decimal("0"),
                    "total_paid": Decimal("0"),
                    "total_outstanding": Decimal("0"),
                    "invoice_count": 0,
                    "students": set(),
                }

            g = guardians[gid]
            g["total_invoiced"] += invoice.total_amount
            g["total_paid"] += invoice.paid_amount
            g["total_outstanding"] += balance
            g["invoice_count"] += 1
            g["students"].add(invoice.student_id)

        total_outstanding = sum(g["total_outstanding"] for g in guardians.values())

        return {
            "total_guardians_with_dues": len(guardians),
            "total_outstanding": quantize(total_outstanding),
        }

    def get_detail_rows(self, queryset, request):
        guardians = {}

        for invoice in queryset:
            balance = invoice.balance
            if balance <= 0:
                continue

            guardian = invoice.student.guardian
            if not guardian:
                continue

            gid = guardian.id
            if gid not in guardians:
                guardians[gid] = {
                    "guardian": guardian,
                    "total_invoiced": Decimal("0"),
                    "total_paid": Decimal("0"),
                    "total_outstanding": Decimal("0"),
                    "invoice_count": 0,
                    "students": set(),
                }

            g = guardians[gid]
            g["total_invoiced"] += invoice.total_amount
            g["total_paid"] += invoice.paid_amount
            g["total_outstanding"] += balance
            g["invoice_count"] += 1
            g["students"].add(invoice.student_id)

        rows = []
        for g in guardians.values():
            rows.append({
                "guardian_name": g["guardian"].name,
                "guardian_phone": g["guardian"].phone,
                "guardian_email": g["guardian"].email or "-",
                "students_count": len(g["students"]),
                "invoices": g["invoice_count"],
                "total_invoiced": quantize(g["total_invoiced"]),
                "total_paid": quantize(g["total_paid"]),
                "total_outstanding": quantize(g["total_outstanding"]),
            })

        return sorted(rows, key=lambda x: x["total_outstanding"], reverse=True)


class AttendanceSummaryByParentReportView(AggregateReportView):
    """Attendance summary grouped by parent."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "parent_attendance_summary"
    model = "apps.attendance.models.Attendance"

    def get_base_queryset(self, request):
        from apps.attendance.models import Attendance
        return Attendance.objects.select_related(
            "student", "student__guardian", "campus", "class_obj"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        month = request.query_params.get("month")
        year = request.query_params.get("year", str(timezone.now().year))

        if month:
            queryset = queryset.filter(date__year=year, date__month=month)
        elif year:
            queryset = queryset.filter(date__year=year)

        return queryset

    def get_summary(self, queryset, request):
        guardians = {}

        for record in queryset:
            guardian = record.student.guardian
            if not guardian:
                continue

            gid = guardian.id
            if gid not in guardians:
                guardians[gid] = {
                    "guardian": guardian,
                    "total": 0, "present": 0, "absent": 0, "late": 0, "leave": 0,
                }

            g = guardians[gid]
            g["total"] += 1
            if record.status in g:
                g[record.status] += 1

        return {
            "total_guardians": len(guardians),
        }

    def get_detail_rows(self, queryset, request):
        guardians = {}

        for record in queryset:
            guardian = record.student.guardian
            if not guardian:
                continue

            gid = guardian.id
            if gid not in guardians:
                guardians[gid] = {
                    "guardian": guardian,
                    "total": 0, "present": 0, "absent": 0, "late": 0, "leave": 0,
                    "students": set(),
                }

            g = guardians[gid]
            g["total"] += 1
            g["students"].add(record.student_id)
            if record.status in g:
                g[record.status] += 1

        rows = []
        for g in guardians.values():
            total = g["total"]
            rate = round(g["present"] / total * 100, 2) if total else 0
            rows.append({
                "guardian_name": g["guardian"].name,
                "guardian_phone": g["guardian"].phone,
                "children_count": len(g["students"]),
                "total_days": total,
                "present": g["present"],
                "absent": g["absent"],
                "late": g["late"],
                "leave": g["leave"],
                "attendance_rate": rate,
            })

        return sorted(rows, key=lambda x: x["attendance_rate"])


class AcademicSummaryByParentReportView(AggregateReportView):
    """Academic summary grouped by parent."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "parent_academic_summary"
    model = "apps.reportcards.models.ReportCard"

    def get_base_queryset(self, request):
        from apps.reportcards.models import ReportCard
        return ReportCard.objects.select_related(
            "student", "student__guardian", "exam", "exam__campus", "exam__class_obj"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "exam__campus_id")

        exam = request.query_params.get("exam")
        if exam:
            queryset = queryset.filter(exam_id=exam)

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(exam__academic_year_id=academic_year)

        return queryset

    def get_summary(self, queryset, request):
        guardians = {}

        for rc in queryset:
            guardian = rc.student.guardian
            if not guardian:
                continue

            gid = guardian.id
            if gid not in guardians:
                guardians[gid] = {
                    "guardian": guardian,
                    "students": set(),
                    "exams": 0,
                    "passed": 0,
                    "total_pct": Decimal("0"),
                }

            g = guardians[gid]
            g["students"].add(rc.student_id)
            g["exams"] += 1
            if rc.is_pass:
                g["passed"] += 1
            g["total_pct"] += rc.percentage

        return {
            "total_guardians": len(guardians),
        }

    def get_detail_rows(self, queryset, request):
        guardians = {}

        for rc in queryset:
            guardian = rc.student.guardian
            if not guardian:
                continue

            gid = guardian.id
            if gid not in guardians:
                guardians[gid] = {
                    "guardian": guardian,
                    "students": set(),
                    "exams": 0,
                    "passed": 0,
                    "total_pct": Decimal("0"),
                }

            g = guardians[gid]
            g["students"].add(rc.student_id)
            g["exams"] += 1
            if rc.is_pass:
                g["passed"] += 1
            g["total_pct"] += rc.percentage

        rows = []
        for g in guardians.values():
            exams = g["exams"]
            passed = g["passed"]
            avg = float(g["total_pct"] / exams) if exams else 0
            pass_rate = round(passed / exams * 100, 2) if exams else 0
            rows.append({
                "guardian_name": g["guardian"].name,
                "guardian_phone": g["guardian"].phone,
                "children_count": len(g["students"]),
                "total_exams": exams,
                "passed": passed,
                "failed": exams - passed,
                "pass_rate": pass_rate,
                "average_percentage": round(avg, 2),
            })

        return sorted(rows, key=lambda x: x["average_percentage"], reverse=True)