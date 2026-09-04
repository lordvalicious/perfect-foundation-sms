"""Student and Admission Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class StudentMasterReportView(AggregateReportView):
    """Comprehensive student master report with all details."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "student_master"
    model = "apps.students.models.Student"

    def get_base_queryset(self, request):
        from apps.students.models import Student
        return Student.objects.select_related(
            "user", "guardian", "primary_campus", "membership"
        ).prefetch_related("enrollments__class_obj", "enrollments__section", "enrollments__campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")

        # Filter by enrollment campus if specified
        campus = request.query_params.get("campus")
        if campus:
            queryset = queryset.filter(enrollments__campus_id=campus)

        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(enrollments__academic_year_id=academic_year)

        class_obj = request.query_params.get("class")
        if class_obj:
            queryset = queryset.filter(enrollments__class_obj_id=class_obj)

        section = request.query_params.get("section")
        if section:
            queryset = queryset.filter(enrollments__section_id=section)

        gender = request.query_params.get("gender")
        if gender:
            queryset = queryset.filter(gender=gender)

        return queryset.distinct()

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_status = queryset.values("status").annotate(count=Count("id"))
        by_gender = queryset.values("gender").annotate(count=Count("id"))
        by_campus = queryset.values("primary_campus__name").annotate(count=Count("id"))

        return {
            "total_students": total,
            "by_status": list(by_status),
            "by_gender": list(by_gender),
            "by_campus": list(by_campus),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for student in queryset:
            enrollment = student.enrollments.filter(status="active").first()
            rows.append({
                "id": student.id,
                "admission_number": student.admission_number,
                "full_name": student.full_name,
                "photo": student.photo.url if student.photo else None,
                "gender": student.gender,
                "date_of_birth": student.date_of_birth,
                "age": self.calculate_age(student.date_of_birth),
                "status": student.status,
                "admission_date": student.admission_date,
                "primary_campus": student.primary_campus.name if student.primary_campus else "-",
                "current_class": enrollment.class_obj.name if enrollment else "-",
                "current_section": enrollment.section.name if enrollment and enrollment.section else "-",
                "academic_year": enrollment.academic_year.name if enrollment else "-",
                "guardian_name": student.guardian.name if student.guardian else "-",
                "guardian_phone": student.guardian.phone if student.guardian else "-",
                "guardian_email": student.guardian.email if student.guardian else "-",
                "phone": student.phone,
                "address": student.address,
                "user_email": student.user.email if student.user else "-",
                "user_phone": student.user.phone if student.user else "-",
            })
        return rows

    def calculate_age(self, dob):
        if not dob:
            return None
        today = timezone.now().date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def _csv(self, request):
        rows = self.get_detail_rows(self.get_queryset(request), request)
        return to_csv(
            "student_master_report.csv",
            [
                "Admission No", "Name", "Gender", "DOB", "Age", "Status",
                "Admission Date", "Campus", "Class", "Section", "Year",
                "Guardian", "Guardian Phone", "Guardian Email",
                "Phone", "Address", "Email"
            ],
            [
                [
                    r["admission_number"], r["full_name"], r["gender"],
                    r["date_of_birth"] or "-", r["age"] or "-", r["status"],
                    r["admission_date"] or "-", r["primary_campus"], r["current_class"],
                    r["current_section"], r["academic_year"], r["guardian_name"],
                    r["guardian_phone"], r["guardian_email"], r["phone"],
                    r["address"], r["user_email"]
                ] for r in rows
            ],
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            return self._csv(request)
        return super().finalize_response(request, response, *args, **kwargs)


class StudentListReportView(AggregateReportView):
    """Student list reports with various filters."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "student_list"
    model = "apps.students.models.Student"

    REPORT_TYPES = {
        "active": ("active", "Active Students"),
        "inactive": ("inactive", "Inactive Students"),
        "graduated": ("graduated", "Graduated Students"),
        "withdrawn": ("withdrawn", "Withdrawn Students"),
        "new_admissions": ("new_admissions", "New Admissions"),
        "by_campus": ("by_campus", "Students by Campus"),
        "by_class": ("by_class", "Students by Class"),
        "by_section": ("by_section", "Students by Section"),
        "by_gender": ("by_gender", "Students by Gender"),
    }

    def get_base_queryset(self, request):
        from apps.students.models import Student
        return Student.objects.select_related(
            "primary_campus", "guardian", "user"
        ).prefetch_related("enrollments__class_obj", "enrollments__section", "enrollments__campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")

        report_type = request.query_params.get("list_type", "active")

        if report_type == "active":
            queryset = queryset.filter(status="active")
        elif report_type == "inactive":
            queryset = queryset.filter(status="inactive")
        elif report_type == "graduated":
            queryset = queryset.filter(status="graduated")
        elif report_type == "withdrawn":
            queryset = queryset.filter(status="withdrawn")
        elif report_type == "new_admissions":
            days = int(request.query_params.get("days", 30))
            cutoff = timezone.now().date() - timezone.timedelta(days=days)
            queryset = queryset.filter(admission_date__gte=cutoff, status="active")
        elif report_type == "by_campus":
            campus = request.query_params.get("campus")
            if campus:
                queryset = queryset.filter(primary_campus_id=campus)
        elif report_type == "by_class":
            class_obj = request.query_params.get("class")
            if class_obj:
                queryset = queryset.filter(enrollments__class_obj_id=class_obj, enrollments__status="active")
        elif report_type == "by_section":
            section = request.query_params.get("section")
            if section:
                queryset = queryset.filter(enrollments__section_id=section, enrollments__status="active")
        elif report_type == "by_gender":
            gender = request.query_params.get("gender")
            if gender:
                queryset = queryset.filter(gender=gender)

        return queryset.distinct()

    def get_summary(self, queryset, request):
        report_type = request.query_params.get("list_type", "active")
        return {
            "total": queryset.count(),
            "report_type": self.REPORT_TYPES.get(report_type, ("", "Students"))[1],
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for student in queryset:
            enrollment = student.enrollments.filter(status="active").first()
            rows.append({
                "admission_number": student.admission_number,
                "full_name": student.full_name,
                "gender": student.gender,
                "date_of_birth": student.date_of_birth,
                "status": student.status,
                "admission_date": student.admission_date,
                "campus": student.primary_campus.name if student.primary_campus else "-",
                "class": enrollment.class_obj.name if enrollment else "-",
                "section": enrollment.section.name if enrollment and enrollment.section else "-",
                "guardian": student.guardian.name if student.guardian else "-",
                "contact": student.phone or (student.user.phone if student.user else "-"),
            })
        return rows


class AdmissionReportView(AggregateReportView):
    """Admission reports - register, new admissions, withdrawals, transfers."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "admission_register"
    model = "apps.students.models.AdmissionApplication"

    REPORT_TYPES = {
        "register": ("Admission Register", "All applications"),
        "new": ("New Admissions", "Accepted applications"),
        "pending": ("Pending Admissions", "Under review"),
        "rejected": ("Rejected Applications", "Rejected"),
        "withdrawn": ("Withdrawn Applications", "Withdrawn"),
        "cancelled": ("Cancelled Admissions", "Cancelled"),
        "transfers_in": ("Transfer In", "Transfer in students"),
        "transfers_out": ("Transfer Out", "Transfer out students"),
    }

    def get_base_queryset(self, request):
        from apps.students.models import AdmissionApplication
        return AdmissionApplication.objects.select_related(
            "campus", "academic_year", "class_obj", "section", "guardian",
            "reviewed_by", "student"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        report_type = request.query_params.get("report_type", "register")

        if report_type == "new":
            queryset = queryset.filter(status="accepted")
        elif report_type == "pending":
            queryset = queryset.filter(status="under_review")
        elif report_type == "rejected":
            queryset = queryset.filter(status="rejected")
        elif report_type == "withdrawn":
            queryset = queryset.filter(status="withdrawn")
        elif report_type == "cancelled":
            queryset = queryset.filter(status="cancelled")

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        campus = request.query_params.get("campus")
        if campus:
            queryset = queryset.filter(campus_id=campus)

        class_obj = request.query_params.get("class")
        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        gender = request.query_params.get("gender")
        if gender:
            queryset = queryset.filter(gender=gender)

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(submitted_at__date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(submitted_at__date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        report_type = request.query_params.get("report_type", "register")
        total = queryset.count()
        by_status = queryset.values("status").annotate(count=Count("id"))
        by_campus = queryset.values("campus__name").annotate(count=Count("id"))
        by_class = queryset.values("class_obj__name").annotate(count=Count("id"))
        by_gender = queryset.values("gender").annotate(count=Count("id"))

        return {
            "total": total,
            "report_type": self.REPORT_TYPES.get(report_type, ("", "Admissions"))[1],
            "by_status": list(by_status),
            "by_campus": list(by_campus),
            "by_class": list(by_class),
            "by_gender": list(by_gender),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for app in queryset:
            rows.append({
                "application_number": app.application_number,
                "name": app.applicant_name,
                "gender": app.gender,
                "date_of_birth": app.date_of_birth,
                "phone": app.phone,
                "address": app.address,
                "guardian": app.guardian.name if app.guardian else "-",
                "campus": app.campus.name,
                "academic_year": app.academic_year.name,
                "class": app.class_obj.name,
                "section": app.section.name if app.section else "-",
                "status": app.get_status_display(),
                "submitted_at": app.submitted_at,
                "reviewed_at": app.reviewed_at,
                "reviewed_by": app.reviewed_by.get_full_name() if app.reviewed_by else "-",
                "student_created": app.student.admission_number if app.student else "-",
            })
        return rows


class StudentProfileReportView(BaseReportView):
    """Detailed student profile report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "student_profile"
    model = "apps.students.models.Student"

    def get_base_queryset(self, request):
        from apps.students.models import Student
        return Student.objects.select_related(
            "user", "guardian", "primary_campus", "membership"
        ).prefetch_related(
            "enrollments__class_obj", "enrollments__section", "enrollments__campus",
            "enrollments__academic_year", "documents", "guardian_links__guardian",
            "leave_requests"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        student_id = request.query_params.get("student")
        if student_id:
            queryset = queryset.filter(id=student_id)
        return queryset

    def get(self, request):
        queryset = self.get_queryset(request)
        student = queryset.first()

        if not student:
            return Response({"detail": "Student not found"}, status=404)

        # Build comprehensive profile
        enrollment = student.enrollments.filter(status="active").first()
        all_enrollments = student.enrollments.all().select_related(
            "class_obj", "section", "campus", "academic_year"
        )

        # Attendance summary
        from apps.attendance.models import Attendance
        attendance_qs = Attendance.objects.filter(student=student)
        attendance_summary = self.get_attendance_summary(attendance_qs)

        # Exam results summary
        from apps.reportcards.models import ReportCard
        report_cards = ReportCard.objects.filter(student=student).select_related("exam")
        results_summary = self.get_results_summary(report_cards)

        # Fee summary
        from apps.finance.models import Invoice
        invoices = Invoice.objects.filter(student=student)
        fee_summary = self.get_fee_summary(invoices)

        # Discipline
        from apps.discipline.models import DisciplineIncident
        incidents = DisciplineIncident.objects.filter(student=student).select_related("campus", "reported_by")
        discipline = self.get_discipline_summary(incidents)

        # Transport
        from apps.transport.models import TransportAssignment
        transport = TransportAssignment.objects.filter(student=student, status="active").select_related(
            "route", "route__vehicle", "route__driver"
        ).first()

        # Library
        from apps.library.models import BookIssue
        library_issues = BookIssue.objects.filter(student=student).select_related(
            "book_copy__book"
        ).order_by("-issue_date")[:10]

        data = {
            "personal": {
                "admission_number": student.admission_number,
                "full_name": student.full_name,
                "photo": student.photo.url if student.photo else None,
                "gender": student.gender,
                "date_of_birth": student.date_of_birth,
                "age": self.calculate_age(student.date_of_birth),
                "phone": student.phone,
                "address": student.address,
                "status": student.status,
                "admission_date": student.admission_date,
                "primary_campus": student.primary_campus.name if student.primary_campus else "-",
            },
            "academic": {
                "current_enrollment": {
                    "class": enrollment.class_obj.name if enrollment else "-",
                    "section": enrollment.section.name if enrollment and enrollment.section else "-",
                    "campus": enrollment.campus.name if enrollment else "-",
                    "academic_year": enrollment.academic_year.name if enrollment else "-",
                    "roll_number": enrollment.roll_number,
                } if enrollment else None,
                "all_enrollments": [
                    {
                        "academic_year": e.academic_year.name,
                        "campus": e.campus.name,
                        "class": e.class_obj.name,
                        "section": e.section.name if e.section else "-",
                        "roll_number": e.roll_number,
                        "status": e.status,
                        "enrollment_date": e.enrollment_date,
                    } for e in all_enrollments
                ],
            },
            "guardians": [
                {
                    "name": link.guardian.name,
                    "relationship": link.relationship,
                    "phone": link.guardian.phone,
                    "email": link.guardian.email,
                    "is_primary": link.is_primary,
                    "can_pick_up": link.can_pick_up,
                    "is_emergency": link.is_emergency_contact,
                } for link in student.guardian_links.all()
            ],
            "attendance": attendance_summary,
            "results": results_summary,
            "fees": fee_summary,
            "discipline": discipline,
            "transport": {
                "route": transport.route.name if transport else "-",
                "vehicle": transport.route.vehicle.plate_number if transport and transport.route.vehicle else "-",
                "driver": transport.route.driver.full_name if transport and transport.route.driver else "-",
            } if transport else None,
            "library": [
                {
                    "book": issue.book_copy.book.title,
                    "issue_date": issue.issue_date,
                    "due_date": issue.due_date,
                    "status": issue.status,
                    "fine": str(issue.fine) if issue.fine else "0",
                } for issue in library_issues
            ],
            "documents": [
                {
                    "type": doc.get_document_type_display(),
                    "title": doc.title,
                    "file": doc.file.url,
                    "uploaded_by": doc.uploaded_by.get_full_name() if doc.uploaded_by else "-",
                    "created_at": doc.created_at,
                } for doc in student.documents.all()
            ],
        }

        return Response(data)

    def calculate_age(self, dob):
        if not dob:
            return None
        today = timezone.now().date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def get_attendance_summary(self, queryset):
        total = queryset.count()
        present = queryset.filter(status="present").count()
        absent = queryset.filter(status="absent").count()
        late = queryset.filter(status="late").count()
        leave = queryset.filter(status="leave").count()

        return {
            "total_days": total,
            "present": present,
            "absent": absent,
            "late": late,
            "leave": leave,
            "attendance_rate": round((present + late) / total * 100, 2) if total else 0,
        }

    def get_results_summary(self, queryset):
        if not queryset:
            return {"exams": 0, "passed": 0, "failed": 0, "pass_rate": 0, "average": 0}

        exams = queryset.count()
        passed = queryset.filter(overall_result="Pass").count()
        percentages = [float(rc.percentage) for rc in queryset if rc.percentage]
        avg = round(sum(percentages) / len(percentages), 2) if percentages else 0

        return {
            "exams": exams,
            "passed": passed,
            "failed": exams - passed,
            "pass_rate": round(passed / exams * 100, 2) if exams else 0,
            "average_percentage": avg,
        }

    def get_fee_summary(self, queryset):
        total_invoiced = sum(inv.total_amount for inv in queryset)
        total_paid = sum(inv.paid_amount for inv in queryset)
        total_outstanding = sum(inv.balance for inv in queryset)

        return {
            "total_invoices": queryset.count(),
            "total_invoiced": quantize(total_invoiced),
            "total_paid": quantize(total_paid),
            "total_outstanding": quantize(total_outstanding),
            "overdue_count": queryset.filter(status="overdue").count(),
        }

    def get_discipline_summary(self, queryset):
        total = queryset.count()
        by_type = queryset.values("incident_type").annotate(count=Count("id"))
        by_severity = queryset.values("severity").annotate(count=Count("id"))

        return {
            "total_incidents": total,
            "by_type": list(by_type),
            "by_severity": list(by_severity),
        }


class StudentStatisticsReportView(AggregateReportView):
    """Student statistics and analytics."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "student_statistics"
    model = "apps.students.models.Student"

    def get_base_queryset(self, request):
        from apps.students.models import Student
        return Student.objects.select_related("primary_campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")
        return queryset.filter(status="active")

    def get_summary(self, queryset, request):
        total = queryset.count()

        # Age distribution
        from datetime import date
        today = date.today()
        age_groups = {"<5": 0, "5-10": 0, "11-15": 0, "16-18": 0, "18+": 0}
        for student in queryset:
            if student.date_of_birth:
                age = today.year - student.date_of_birth.year - (
                    (today.month, today.day) < (student.date_of_birth.month, student.date_of_birth.day)
                )
                if age < 5:
                    age_groups["<5"] += 1
                elif age <= 10:
                    age_groups["5-10"] += 1
                elif age <= 15:
                    age_groups["11-15"] += 1
                elif age <= 18:
                    age_groups["16-18"] += 1
                else:
                    age_groups["18+"] += 1

        # Gender distribution
        gender_dist = queryset.values("gender").annotate(count=Count("id"))

        # Campus distribution
        campus_dist = queryset.values("primary_campus__name").annotate(count=Count("id"))

        # Admission trend (last 12 months)
        from django.db.models.functions import TruncMonth
        admissions = queryset.filter(admission_date__isnull=False).annotate(
            month=TruncMonth("admission_date")
        ).values("month").annotate(count=Count("id")).order_by("month")

        return {
            "total_students": total,
            "age_distribution": age_groups,
            "gender_distribution": list(gender_dist),
            "campus_distribution": list(campus_dist),
            "admission_trend": list(admissions),
        }

    def get_detail_rows(self, queryset, request):
        return []