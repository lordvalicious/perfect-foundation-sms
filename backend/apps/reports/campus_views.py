"""Campus Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class CampusStudentCountReportView(AggregateReportView):
    """Campus student count report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "campus_students"
    model = "apps.students.models.Student"

    def get_base_queryset(self, request):
        from apps.students.models import Student
        return Student.objects.filter(status="active").select_related("primary_campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Don't apply campus scope for campus comparison report
        # This is for super admins to compare campuses
        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_campus = queryset.values("primary_campus__name").annotate(
            count=Count("id"),
            male=Count(Case(When(gender="male", then=1))),
            female=Count(Case(When(gender="female", then=1))),
        )
        return {
            "total_students": total,
            "campuses_count": by_campus.count(),
        }

    def get_detail_rows(self, queryset, request):
        by_campus = queryset.values("primary_campus__name").annotate(
            total=Count("id"),
            male=Count(Case(When(gender="male", then=1))),
            female=Count(Case(When(gender="female", then=1))),
        )
        rows = []
        for c in by_campus:
            rows.append({
                "campus": c["primary_campus__name"] or "Unassigned",
                "total": c["total"],
                "male": c["male"],
                "female": c["female"],
            })
        return rows


class CampusAttendanceReportView(AggregateReportView):
    """Campus attendance comparison."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "campus_attendance"
    model = "apps.attendance.models.Attendance"

    def get_base_queryset(self, request):
        from apps.attendance.models import Attendance
        return Attendance.objects.select_related("campus", "class_obj", "section")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Don't apply campus scope for comparison
        return queryset

    def get_summary(self, queryset, request):
        campuses = queryset.values("campus__name").annotate(
            total=Count("id"),
            present=Count(Case(When(status="present", then=1))),
            absent=Count(Case(When(status="absent", then=1))),
            late=Count(Case(When(status="late", then=1))),
            leave=Count(Case(When(status="leave", then=1))),
        )
        return {
            "campuses": list(campuses),
        }

    def get_detail_rows(self, queryset, request):
        campuses = queryset.values("campus__name").annotate(
            total=Count("id"),
            present=Count(Case(When(status="present", then=1))),
            absent=Count(Case(When(status="absent", then=1))),
            late=Count(Case(When(status="late", then=1))),
            leave=Count(Case(When(status="leave", then=1))),
        )
        rows = []
        for c in campuses:
            total = c["total"]
            rate = round((c["present"] + c["late"]) / total * 100, 2) if total else 0
            rows.append({
                "campus": c["campus__name"] or "Unassigned",
                "total_records": total,
                "present": c["present"],
                "absent": c["absent"],
                "late": c["late"],
                "leave": c["leave"],
                "attendance_rate": rate,
            })
        return rows


class CampusAcademicPerformanceReportView(AggregateReportView):
    """Campus academic performance comparison."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "campus_performance"
    model = "apps.reportcards.models.ReportCard"

    def get_base_queryset(self, request):
        from apps.reportcards.models import ReportCard
        return ReportCard.objects.select_related("exam__campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Don't apply campus scope for comparison

        exam = request.query_params.get("exam")
        if exam:
            queryset = queryset.filter(exam_id=exam)

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(exam__academic_year_id=academic_year)

        return queryset

    def get_summary(self, queryset, request):
        campuses = queryset.values("exam__campus__name").annotate(
            students=Count("id"),
            passed=Count(Case(When(overall_result="Pass", then=1))),
            avg_pct=Avg("percentage"),
            max_pct=Max("percentage"),
            min_pct=Min("percentage"),
        )
        return {
            "campuses": list(campuses),
        }

    def get_detail_rows(self, queryset, request):
        campuses = queryset.values("exam__campus__name").annotate(
            students=Count("id"),
            passed=Count(Case(When(overall_result="Pass", then=1))),
            avg_pct=Avg("percentage"),
            max_pct=Max("percentage"),
            min_pct=Min("percentage"),
        )
        rows = []
        for c in campuses:
            students = c["students"]
            passed = c["passed"]
            rows.append({
                "campus": c["exam__campus__name"] or "Unassigned",
                "students": students,
                "passed": passed,
                "failed": students - passed,
                "pass_rate": round(passed / students * 100, 2) if students else 0,
                "avg_percentage": round(c["avg_pct"], 2) if c["avg_pct"] else 0,
                "max_percentage": round(c["max_pct"], 2) if c["max_pct"] else 0,
                "min_percentage": round(c["min_pct"], 2) if c["min_pct"] else 0,
            })
        return rows


class CampusFeeCollectionReportView(AggregateReportView):
    """Campus fee collection comparison."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "campus_fees"
    model = "apps.finance.models.Invoice"

    def get_base_queryset(self, request):
        from apps.finance.models import Invoice
        return Invoice.objects.select_related("enrollment__campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Don't apply campus scope for comparison

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        campuses = queryset.values("enrollment__campus__name").annotate(
            invoiced=Sum("total_amount"),
            collected=Sum("paid_amount"),
            outstanding=Sum("balance"),
        )
        return {
            "campuses": list(campuses),
        }

    def get_detail_rows(self, queryset, request):
        campuses = queryset.values("enrollment__campus__name").annotate(
            invoiced=Sum("total_amount"),
            collected=Sum("paid_amount"),
            outstanding=Sum("balance"),
        )
        rows = []
        for c in campuses:
            inv = c["invoiced"] or Decimal("0")
            coll = c["collected"] or Decimal("0")
            rows.append({
                "campus": c["enrollment__campus__name"] or "Unassigned",
                "invoiced": quantize(inv),
                "collected": quantize(coll),
                "outstanding": quantize(c["outstanding"] or Decimal("0")),
                "collection_rate": round(float(coll) / float(inv) * 100, 2) if inv else 0,
            })
        return rows


class CampusOutstandingFeesReportView(CampusFeeCollectionReportView):
    """Campus outstanding fees report."""
    report_definition_key = "campus_outstanding_fees"


class CampusStaffCountReportView(AggregateReportView):
    """Campus staff count report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "campus_staff"
    model = "apps.accounts.models.StaffProfile"

    def get_base_queryset(self, request):
        from apps.accounts.models import StaffProfile
        return StaffProfile.objects.filter(status="active").select_related("primary_campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_campus = queryset.values("primary_campus__name").annotate(count=Count("id"))
        return {
            "total_staff": total,
            "campuses": list(by_campus),
        }

    def get_detail_rows(self, queryset, request):
        by_campus = queryset.values("primary_campus__name").annotate(
            total=Count("id"),
            teaching=Count(Case(When(designation__icontains="teacher", then=1))),
            admin=Count(Case(When(designation__icontains="admin", then=1))),
        )
        rows = []
        for c in by_campus:
            rows.append({
                "campus": c["primary_campus__name"] or "Unassigned",
                "total": c["total"],
                "teaching": c["teaching"],
                "admin": c["admin"],
            })
        return rows


class CampusAdmissionsReportView(AggregateReportView):
    """Campus admissions comparison."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "campus_admissions"
    model = "apps.students.models.AdmissionApplication"

    def get_base_queryset(self, request):
        from apps.students.models import AdmissionApplication
        return AdmissionApplication.objects.select_related("campus", "class_obj")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_campus = queryset.values("campus__name").annotate(count=Count("id"))
        by_status = queryset.values("status").annotate(count=Count("id"))
        return {
            "total_admissions": total,
            "by_campus": list(by_campus),
            "by_status": list(by_status),
        }

    def get_detail_rows(self, queryset, request):
        by_campus = queryset.values("campus__name").annotate(
            total=Count("id"),
            accepted=Count(Case(When(status="accepted", then=1))),
            pending=Count(Case(When(status="under_review", then=1))),
            rejected=Count(Case(When(status="rejected", then=1))),
        )
        rows = []
        for c in by_campus:
            rows.append({
                "campus": c["campus__name"] or "Unassigned",
                "total": c["total"],
                "accepted": c["accepted"],
                "pending": c["pending"],
                "rejected": c["rejected"],
            })
        return rows


class CampusFinancialSummaryReportView(AggregateReportView):
    """Campus financial summary."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "campus_finance"
    model = "apps.finance.models.Invoice"

    def get_base_queryset(self, request):
        from apps.finance.models import Invoice, Payment
        return Invoice.objects.select_related("enrollment__campus").prefetch_related("payments")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        from apps.finance.models import Payment, Expense

        campuses = {}
        for inv in queryset:
            campus = inv.enrollment.campus.name if inv.enrollment.campus else "Unassigned"
            if campus not in campuses:
                campuses[campus] = {
                    "invoiced": Decimal("0"),
                    "collected": Decimal("0"),
                    "outstanding": Decimal("0"),
                    "discounts": Decimal("0"),
                }
            campuses[campus]["invoiced"] += inv.total_amount
            campuses[campus]["collected"] += inv.paid_amount
            campuses[campus]["outstanding"] += inv.balance
            campuses[campus]["discounts"] += inv.discount

        # Add expenses
        expenses = Expense.objects.filter(status__in=["approved", "paid"])
        if hasattr(request, 'campus_id'):
            expenses = expenses.filter(campus_id=request.campus_id)

        for exp in expenses:
            campus = exp.campus.name if exp.campus else "Unassigned"
            if campus not in campuses:
                campuses[campus] = {
                    "invoiced": Decimal("0"),
                    "collected": Decimal("0"),
                    "outstanding": Decimal("0"),
                    "discounts": Decimal("0"),
                    "expenses": Decimal("0"),
                }
            campuses[campus]["expenses"] = campuses[campus].get("expenses", Decimal("0")) + exp.amount

        return {
            "campuses": [
                {
                    "campus": k,
                    "invoiced": quantize(v["invoiced"]),
                    "collected": quantize(v["collected"]),
                    "outstanding": quantize(v["outstanding"]),
                    "discounts": quantize(v["discounts"]),
                    "expenses": quantize(v.get("expenses", Decimal("0"))),
                    "net": quantize(v["collected"] - v.get("expenses", Decimal("0"))),
                }
                for k, v in sorted(campuses.items())
            ],
        }

    def get_detail_rows(self, queryset, request):
        return []


class CampusComparisonReportView(AggregateReportView):
    """Comprehensive campus comparison report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "campus_comparison"
    model = "apps.schools.models.Campus"

    def get_base_queryset(self, request):
        from apps.schools.models import Campus
        return Campus.objects.filter(status="active")

    def get_queryset(self, request):
        return super().get_queryset(request)

    def get_summary(self, queryset, request):
        return {"total_campuses": queryset.count()}

    def get_detail_rows(self, queryset, request):
        from apps.students.models import Student, Enrollment
        from apps.accounts.models import StaffProfile
        from apps.attendance.models import Attendance
        from apps.finance.models import Invoice
        from apps.reportcards.models import ReportCard

        rows = []
        for campus in queryset:
            # Students
            students = Student.objects.filter(primary_campus=campus, status="active")
            total_students = students.count()

            # Staff
            staff = StaffProfile.objects.filter(primary_campus=campus, status="active")
            total_staff = staff.count()

            # Attendance (current month)
            month = timezone.now().month
            year = timezone.now().year
            attendance = Attendance.objects.filter(campus=campus, date__month=month, date__year=year)
            att_total = attendance.count()
            att_present = attendance.filter(status__in=["present", "late"]).count()
            att_rate = round(att_present / att_total * 100, 2) if att_total else 0

            # Fees (current month)
            invoices = Invoice.objects.filter(enrollment__campus=campus, issue_date__month=month, issue_date__year=year)
            inv_total = sum(inv.total_amount for inv in invoices)
            inv_collected = sum(inv.paid_amount for inv in invoices)
            fee_rate = round(float(inv_collected) / float(inv_total) * 100, 2) if inv_total else 0

            # Academic (latest exam)
            latest_exam = ReportCard.objects.filter(exam__campus=campus).order_by("-exam__start_date").first()
            exam_perf = None
            if latest_exam:
                rcs = ReportCard.objects.filter(exam=latest_exam.exam)
                passed = rcs.filter(overall_result="Pass").count()
                total = rcs.count()
                if total:
                    exam_perf = round(passed / total * 100, 2)

            rows.append({
                "campus": campus.name,
                "students": total_students,
                "staff": total_staff,
                "attendance_rate": att_rate,
                "fee_collection_rate": fee_rate,
                "exam_pass_rate": exam_perf,
            })
        return rows


class CampusDashboardReportView(AggregateReportView):
    """Campus dashboard summary for a single campus."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "campus_dashboard"
    model = "apps.schools.models.Campus"

    def get_base_queryset(self, request):
        from apps.schools.models import Campus
        return Campus.objects.filter(status="active")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        campus_id = request.query_params.get("campus")
        if campus_id:
            queryset = queryset.filter(id=campus_id)

        return queryset

    def get_summary(self, queryset, request):
        from apps.students.models import Student, Enrollment
        from apps.accounts.models import StaffProfile
        from apps.attendance.models import Attendance
        from apps.finance.models import Invoice, Payment
        from apps.reportcards.models import ReportCard
        from apps.library.models import BookIssue
        from apps.transport.models import TransportAssignment

        campus = queryset.first()
        if not campus:
            return {}

        # Students
        students = Student.objects.filter(primary_campus=campus, status="active")
        total_students = students.count()
        new_admissions = students.filter(admission_date__month=timezone.now().month).count()

        # Staff
        staff = StaffProfile.objects.filter(primary_campus=campus, status="active")
        total_staff = staff.count()

        # Attendance (current month)
        month = timezone.now().month
        year = timezone.now().year
        attendance = Attendance.objects.filter(campus=campus, date__month=month, date__year=year)
        att_total = attendance.count()
        att_present = attendance.filter(status__in=["present", "late"]).count()
        att_rate = round(att_present / att_total * 100, 2) if att_total else 0

        # Fees (current academic year)
        from apps.schools.models import AcademicYear
        current_year = AcademicYear.objects.filter(status="active").first()
        invoices = Invoice.objects.filter(enrollment__campus=campus)
        if current_year:
            invoices = invoices.filter(academic_year=current_year)
        inv_total = sum(inv.total_amount for inv in invoices)
        inv_collected = sum(inv.paid_amount for inv in invoices)
        inv_outstanding = sum(inv.balance for inv in invoices)
        fee_rate = round(float(inv_collected) / float(inv_total) * 100, 2) if inv_total else 0

        # Library
        library_issues = BookIssue.objects.filter(book_copy__book__campus=campus, status__in=["issued", "overdue"])
        overdue_books = library_issues.filter(
            Q(status="overdue") | Q(status="issued", due_date__lt=timezone.now().date())
        ).count()

        # Transport
        transport_students = TransportAssignment.objects.filter(route__campus=campus, status="active").count()

        return {
            "campus": campus.name,
            "students": {
                "total": total_students,
                "new_admissions": new_admissions,
            },
            "staff": {
                "total": total_staff,
            },
            "attendance": {
                "rate": att_rate,
                "total_records": att_total,
            },
            "fees": {
                "invoiced": quantize(inv_total),
                "collected": quantize(inv_collected),
                "outstanding": quantize(inv_outstanding),
                "collection_rate": fee_rate,
            },
            "library": {
                "active_issues": library_issues.count(),
                "overdue": overdue_books,
            },
            "transport": {
                "students": transport_students,
            },
        }

    def get_detail_rows(self, queryset, request):
        return []