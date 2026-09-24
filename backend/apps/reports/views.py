"""Reports app views - consolidated exports for URL routing."""

from datetime import date
from decimal import Decimal

from django.db.models import Count, Prefetch, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole

from .utils import prefetch_reportcard_results, quantize, to_csv


# REPORT_VIEW_MAP maps report type strings to view classes for the weekly email cron
REPORT_VIEW_MAP = {
    "enrollment": "apps.reports.views.EnrollmentReportView",
    "attendance": "apps.reports.views.AttendanceReportView",
    "results": "apps.reports.views.ResultsReportView",
    "fees": "apps.reports.views.FeesReportView",
    "staff": "apps.reports.views.StaffReportView",
    "subjects": "apps.reports.views.SubjectPerformanceReportView",
    "payments": "apps.reports.views.PaymentMethodsReportView",
    "student_status": "apps.reports.views.StudentStatusReportView",
    "fee_categories": "apps.reports.views.FeeCategoryReportView",
    "fee_defaulters": "apps.reports.views.FeeDefaultersReportView",
    "teacher_workload": "apps.reports.views.TeacherWorkloadReportView",
    "class_performance": "apps.reports.views.ClassPerformanceReportView",
    "student_progress": "apps.reports.views.StudentProgressTrendReportView",
    "collection_trend": "apps.reports.extended_views.CollectionTrendReportView",
    "discounts": "apps.reports.extended_views.DiscountsReportView",
    "chronic_absentee": "apps.reports.extended_views.ChronicAbsenteeReportView",
    "payroll_summary": "apps.reports.extended_views.PayrollSummaryReportView",
    "library_overview": "apps.reports.extended_views.LibraryOverviewReportView",
    "route_utilization": "apps.reports.extended_views.RouteUtilizationReportView",
    "inventory_value": "apps.reports.extended_views.InventoryValueReportView",
    "maintenance_due": "apps.reports.extended_views.MaintenanceDueReportView",
    "event_participation": "apps.reports.extended_views.EventParticipationReportView",
    "sms_usage": "apps.reports.extended_views.SmsUsageReportView",
    "top_performers": "apps.reports.extended_views.TopPerformersReportView",
    "at_risk": "apps.reports.at_risk_views.AtRiskReportView",
}


class ReportsRootView(APIView):
    """Root endpoint for Reports API."""
    permission_classes = [IsAccountantRole]

    def get(self, request):
        return Response({
            "message": "Reports API",
            "endpoints": {
                "enrollment": "/api/reports/enrollment/",
                "attendance": "/api/reports/attendance/",
                "results": "/api/reports/results/",
                "fees": "/api/reports/fees/",
                "staff": "/api/reports/staff/",
                "subjects": "/api/reports/subjects/",
                "payments": "/api/reports/payments/",
                "student_status": "/api/reports/student-status/",
                "fee_categories": "/api/reports/fee-categories/",
                "fee_defaulters": "/api/reports/fee-defaulters/",
                "teacher_workload": "/api/reports/teacher-workload/",
                "class_performance": "/api/reports/class-performance/",
                "student_progress": "/api/reports/student-progress/",
                "library": {
                    "inventory": "/api/reports/library/inventory/",
                    "available": "/api/reports/library/available/",
                    "issued": "/api/reports/library/issued/",
                    "returned": "/api/reports/library/returned/",
                    "overdue": "/api/reports/library/overdue/",
                    "fines": "/api/reports/library/fines/",
                    "activity": "/api/reports/library/activity/",
                    "most_borrowed": "/api/reports/library/most-borrowed/",
                    "student_history": "/api/reports/library/student-history/",
                    "teacher_history": "/api/reports/library/teacher-history/",
                }
            }
        })


class EnrollmentReportView(APIView):
    """Enrollment summary grouped by campus and class."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.students.models import Enrollment

        queryset = (
            Enrollment.objects
            .filter(status="active")
            .select_related(
                "campus",
                "class_obj",
                "section",
                "student",
            )
        )

        academic_year = request.query_params.get("academic_year")

        if academic_year:
            queryset = queryset.filter(
                academic_year_id=academic_year,
            )

        queryset = apply_campus_scope(queryset, request, "campus_id")

        records = []

        for record in queryset:
            gender = record.student.gender or ""
            records.append(
                {
                    "campus": record.campus.name,
                    "class": record.class_obj.name,
                    "section": record.section.name if record.section_id else "-",
                    "gender": gender,
                }
            )

        summary = {}

        for record in records:
            key = (
                record["campus"],
                record["class"],
            )

            entry = summary.setdefault(
                key,
                {
                    "campus": record["campus"],
                    "class": record["class"],
                    "total": 0,
                    "male": 0,
                    "female": 0,
                },
            )

            entry["total"] += 1

            if record["gender"].upper() == "M":
                entry["male"] += 1
            elif record["gender"].upper() == "F":
                entry["female"] += 1

        return sorted(
            summary.values(),
            key=lambda item: (
                item["campus"],
                item["class"],
            ),
        )

    def get(self, request):
        rows = self._data(request)

        total_students = sum(row["total"] for row in rows)
        classes = len(rows)

        return Response(
            {
                "total_students": total_students,
                "total_classes": classes,
                "average_class_size": (
                    round(total_students / classes, 2)
                    if classes
                    else 0
                ),
                "classes": rows,
            }
        )

    def _csv(self, request):
        rows = self._data(request)

        return to_csv(
            "enrollment_report.csv",
            ["Campus", "Class", "Total", "Male", "Female"],
            [
                [
                    row["campus"],
                    row["class"],
                    row["total"],
                    row["male"],
                    row["female"],
                ]
                for row in rows
            ],
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)

        return super().finalize_response(
            request,
            response,
            *args,
            **kwargs,
        )


class AttendanceReportView(APIView):
    """Attendance summary grouped by class."""

    permission_classes = [IsAccountantRole]

    def _build_queryset(self, request):
        from apps.attendance.models import Attendance

        queryset = (
            Attendance.objects
            .select_related("campus", "class_obj")
        )

        queryset = apply_campus_scope(queryset, request, "campus_id")

        class_obj = request.query_params.get("class_obj")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        month = request.query_params.get("month")
        year = request.query_params.get("year")

        if month and year:
            queryset = queryset.filter(
                date__year=year,
                date__month=month,
            )
        elif month:
            from django.utils import timezone

            queryset = queryset.filter(
                date__month=month,
                date__year=timezone.now().year,
            )
        elif year:
            queryset = queryset.filter(date__year=year)

        return queryset

    def _data(self, request):
        queryset = self._build_queryset(request)

        rows = {}

        for record in queryset:
            key = (
                record.campus.name,
                record.class_obj.name,
            )

            entry = rows.setdefault(
                key,
                {
                    "campus": record.campus.name,
                    "class": record.class_obj.name,
                    "total_records": 0,
                    "present": 0,
                    "absent": 0,
                    "late": 0,
                    "leave": 0,
                },
            )

            entry["total_records"] += 1

            status = record.status

            if status in entry:
                entry[status] += 1

        for entry in rows.values():
            total = entry["total_records"]

            entry["attendance_rate"] = (
                round(
                    (
                        (entry["present"] + entry["late"])
                        / total
                        * 100
                    ),
                    2,
                )
                if total
                else 0
            )

        return sorted(
            rows.values(),
            key=lambda item: (
                item["campus"],
                item["class"],
            ),
        )

    def get(self, request):
        rows = self._data(request)

        total_records = sum(
            row["total_records"] for row in rows
        )
        present = sum(row["present"] for row in rows)
        late = sum(row["late"] for row in rows)

        return Response(
            {
                "overall_attendance_rate": (
                    round(
                        (present + late) / total_records * 100,
                        2,
                    )
                    if total_records
                    else 0
                ),
                "classes": rows,
            }
        )

    def _csv(self, request):
        rows = self._data(request)

        return to_csv(
            "attendance_report.csv",
            [
                "Campus",
                "Class",
                "Total Records",
                "Present",
                "Absent",
                "Late",
                "Leave",
                "Attendance Rate (%)",
            ],
            [
                [
                    row["campus"],
                    row["class"],
                    row["total_records"],
                    row["present"],
                    row["absent"],
                    row["late"],
                    row["leave"],
                    row["attendance_rate"],
                ]
                for row in rows
            ],
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)

        return super().finalize_response(
            request,
            response,
            *args,
            **kwargs,
        )


class ResultsReportView(APIView):
    """Exam results summary for a class."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.reportcards.models import ReportCard

        queryset = (
            ReportCard.objects
            .select_related(
                "student",
                "exam",
                "exam__class_obj",
            )
        )

        exam = request.query_params.get("exam")

        if not exam:
            return []

        queryset = queryset.filter(exam_id=exam)
        queryset = apply_campus_scope(queryset, request, "exam__campus_id")

        prefetch_reportcard_results(queryset)

        rows = []

        for report_card in queryset:
            rows.append(
                {
                    "admission_number": (
                        report_card.student.admission_number
                    ),
                    "student": report_card.student.full_name,
                    "total_marks": float(report_card.total_marks),
                    "maximum_marks": float(report_card.maximum_marks),
                    "percentage": float(report_card.percentage),
                    "grade": report_card.grade,
                    "result": report_card.overall_result,
                    "position": report_card.position,
                }
            )

        return rows

    def _stats(self, rows):
        if not rows:
            return {
                "total_students": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0,
                "average_percentage": 0,
                "highest": 0,
                "lowest": 0,
            }

        passed = sum(
            1 for row in rows if row["result"] == "Pass"
        )
        percentages = [row["percentage"] for row in rows]

        return {
            "total_students": len(rows),
            "passed": passed,
            "failed": len(rows) - passed,
            "pass_rate": round(passed / len(rows) * 100, 2),
            "average_percentage": round(
                sum(percentages) / len(percentages),
                2,
            ),
            "highest": max(percentages),
            "lowest": min(percentages),
        }

    def get(self, request):
        rows = self._data(request)

        return Response(
            {
                "summary": self._stats(rows),
                "students": rows,
            }
        )

    def _csv(self, request):
        rows = self._data(request)

        return to_csv(
            "results_report.csv",
            [
                "Admission No",
                "Student",
                "Total Marks",
                "Maximum Marks",
                "Percentage",
                "Grade",
                "Result",
                "Position",
            ],
            [
                [
                    row["admission_number"],
                    row["student"],
                    row["total_marks"],
                    row["maximum_marks"],
                    row["percentage"],
                    row["grade"],
                    row["result"],
                    row["position"],
                ]
                for row in rows
            ],
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)

        return super().finalize_response(
            request,
            response,
            *args,
            **kwargs,
        )


class FeesReportView(APIView):
    """Fee collection summary."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.finance.models import Invoice, Payment

        invoices = (
            Invoice.objects
            .prefetch_related(
                "items",
                Prefetch(
                    "payments",
                    queryset=Payment.objects.filter(
                        status="completed",
                    ),
                ),
            )
            .select_related(
                "enrollment__campus",
                "academic_year",
            )
        )

        invoices = apply_campus_scope(
            invoices,
            request,
            "enrollment__campus_id",
        )

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date:
            invoices = invoices.filter(issue_date__gte=start_date)

        if end_date:
            invoices = invoices.filter(issue_date__lte=end_date)

        campus_totals = {}
        method_totals = {}

        total_invoiced = Decimal("0")
        total_discount = Decimal("0")
        total_collected = Decimal("0")
        total_outstanding = Decimal("0")

        method = request.query_params.get("payment_method")

        for invoice in invoices:
            items = invoice.items.all()
            payments = invoice.payments.all()

            invoiced = sum(
                (item.amount for item in items),
                Decimal("0"),
            ) - invoice.discount

            invoiced = max(invoiced, Decimal("0"))

            collected = sum(
                (payment.amount for payment in payments),
                Decimal("0"),
            )

            balance = max(
                invoiced - collected,
                Decimal("0"),
            )

            total_invoiced += invoiced
            total_discount += invoice.discount
            total_collected += collected
            total_outstanding += balance

            campus_name = invoice.enrollment.campus.name

            campus_entry = campus_totals.setdefault(
                campus_name,
                {
                    "campus": campus_name,
                    "invoiced": Decimal("0"),
                    "collected": Decimal("0"),
                    "outstanding": Decimal("0"),
                },
            )

            campus_entry["invoiced"] += invoiced
            campus_entry["collected"] += collected
            campus_entry["outstanding"] += balance

            for payment in payments:
                if method and payment.payment_method != method:
                    continue

                method_entry = method_totals.setdefault(
                    payment.payment_method,
                    {
                        "method": payment.payment_method,
                        "collected": Decimal("0"),
                    },
                )

                method_entry["collected"] += payment.amount

        campuses = [
            {
                "campus": entry["campus"],
                "invoiced": quantize(entry["invoiced"]),
                "collected": quantize(entry["collected"]),
                "outstanding": quantize(entry["outstanding"]),
            }
            for entry in sorted(
                campus_totals.values(),
                key=lambda item: item["campus"],
            )
        ]

        methods = [
            {
                "method": entry["method"],
                "collected": quantize(entry["collected"]),
            }
            for entry in sorted(
                method_totals.values(),
                key=lambda item: item["method"],
            )
        ]

        return {
            "summary": {
                "total_invoiced": quantize(total_invoiced),
                "total_discount": quantize(total_discount),
                "total_collected": quantize(total_collected),
                "total_outstanding": quantize(total_outstanding),
                "collection_rate": (
                    round(
                        float(total_collected)
                        / float(total_invoiced)
                        * 100,
                        2,
                    )
                    if total_invoiced
                    else 0
                ),
            },
            "by_campus": campuses,
            "by_payment_method": methods,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        rows = [
            [
                "Total Invoiced",
                data["summary"]["total_invoiced"],
            ],
            [
                "Total Collected",
                data["summary"]["total_collected"],
            ],
            [
                "Total Outstanding",
                data["summary"]["total_outstanding"],
            ],
            [
                "Collection Rate (%)",
                data["summary"]["collection_rate"],
            ],
        ]

        return to_csv(
            "fees_report.csv",
            ["Metric", "Value"],
            rows,
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)

        return super().finalize_response(
            request,
            response,
            *args,
            **kwargs,
        )


class PaymentMethodsReportView(APIView):
    """Fee collection totals grouped by payment method."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.finance.models import Payment

        queryset = (
            Payment.objects
            .filter(status="completed")
            .select_related(
                "invoice__enrollment__campus",
                "invoice__academic_year",
            )
        )

        queryset = apply_campus_scope(
            queryset, request, "invoice__enrollment__campus_id",
        )

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date:
            queryset = queryset.filter(
                payment_date__gte=start_date,
            )

        if end_date:
            queryset = queryset.filter(
                payment_date__lte=end_date,
            )

        method_totals = {}
        campus_totals = {}
        total_collected = Decimal("0")

        for payment in queryset:
            amount = payment.amount

            total_collected += amount

            method = payment.get_payment_method_display()

            method_entry = method_totals.setdefault(
                method,
                {
                    "method": method,
                    "collected": Decimal("0"),
                    "payments": 0,
                },
            )

            method_entry["collected"] += amount
            method_entry["payments"] += 1

            campus_name = (
                payment.invoice.enrollment.campus.name
                if payment.invoice.enrollment_id
                and payment.invoice.enrollment.campus_id
                else "-"
            )

            campus_entry = campus_totals.setdefault(
                campus_name,
                {
                    "campus": campus_name,
                    "collected": Decimal("0"),
                    "payments": 0,
                },
            )

            campus_entry["collected"] += amount
            campus_entry["payments"] += 1

        methods = [
            {
                "method": entry["method"],
                "collected": quantize(entry["collected"]),
                "payments": entry["payments"],
            }
            for entry in sorted(
                method_totals.values(),
                key=lambda item: item["collected"],
                reverse=True,
            )
        ]

        campuses = [
            {
                "campus": entry["campus"],
                "collected": quantize(entry["collected"]),
                "payments": entry["payments"],
            }
            for entry in sorted(
                campus_totals.values(),
                key=lambda item: item["campus"],
            )
        ]

        return {
            "summary": {
                "total_collected": quantize(total_collected),
                "methods": len(methods),
            },
            "by_method": methods,
            "by_campus": campuses,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        rows = []

        for entry in data["by_method"]:
            rows.append(
                [
                    "By Method",
                    entry["method"],
                    entry["payments"],
                    entry["collected"],
                ]
            )

        for entry in data["by_campus"]:
            rows.append(
                [
                    "By Campus",
                    entry["campus"],
                    entry["payments"],
                    entry["collected"],
                ]
            )

        return to_csv(
            "payment_methods_report.csv",
            ["Grouping", "Name", "Payments", "Collected"],
            rows,
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)

        return super().finalize_response(
            request,
            response,
            *args,
            **kwargs,
        )


class StudentStatusReportView(APIView):
    """Students grouped by campus and status."""

    permission_classes = [IsAccountantRole]

    STATUS_LABELS = {
        "active": "Active",
        "inactive": "Inactive",
        "graduated": "Graduated",
        "withdrawn": "Withdrawn",
    }

    def _data(self, request):
        from apps.students.models import Enrollment

        queryset = (
            Enrollment.objects
            .filter(status="active")
            .select_related("campus", "student")
        )

        queryset = apply_campus_scope(queryset, request, "campus_id")

        rows = {}
        status_counts = {}

        for enrollment in queryset:
            status = enrollment.student.status or "active"
            label = self.STATUS_LABELS.get(status, status)
            campus_name = enrollment.campus.name

            key = (campus_name, label)

            entry = rows.setdefault(
                key,
                {
                    "campus": campus_name,
                    "status": label,
                    "count": 0,
                },
            )

            entry["count"] += 1

            status_entry = status_counts.setdefault(
                label,
                {"status": label, "count": 0},
            )

            status_entry["count"] += 1

        return {
            "total_students": sum(
                entry["count"] for entry in status_counts.values()
            ),
            "statuses": sorted(
                status_counts.values(),
                key=lambda item: item["count"],
                reverse=True,
            ),
            "rows": sorted(
                rows.values(),
                key=lambda item: (
                    item["campus"],
                    item["status"],
                ),
            ),
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "student_status_report.csv",
            ["Campus", "Status", "Count"],
            [
                [
                    row["campus"],
                    row["status"],
                    row["count"],
                ]
                for row in data["rows"]
            ],
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)

        return super().finalize_response(
            request,
            response,
            *args,
            **kwargs,
        )


class FeeCategoryReportView(APIView):
    """Invoiced amounts grouped by fee category."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.finance.models import InvoiceItem

        queryset = (
            InvoiceItem.objects
            .filter(
                invoice__status__in=[
                    "issued",
                    "partial",
                    "paid",
                    "overdue",
                ],
            )
            .select_related(
                "category",
                "invoice__enrollment__campus",
            )
        )

        queryset = apply_campus_scope(
            queryset,
            request,
            "invoice__enrollment__campus_id",
        )

        category_totals = {}
        rows = {}
        total_invoiced = Decimal("0")

        for item in queryset:
            amount = item.amount

            total_invoiced += amount

            category_name = item.category.name

            category_entry = category_totals.setdefault(
                category_name,
                {
                    "category": category_name,
                    "invoiced": Decimal("0"),
                    "items": 0,
                },
            )

            category_entry["invoiced"] += amount
            category_entry["items"] += 1

            campus_name = (
                item.invoice.enrollment.campus.name
                if item.invoice.enrollment_id
                and item.invoice.enrollment.campus_id
                else "-"
            )

            key = (category_name, campus_name)

            entry = rows.setdefault(
                key,
                {
                    "category": category_name,
                    "campus": campus_name,
                    "invoiced": Decimal("0"),
                },
            )

            entry["invoiced"] += amount

        return {
            "summary": {
                "total_invoiced": quantize(total_invoiced),
                "categories": len(category_totals),
            },
            "by_category": [
                {
                    "category": entry["category"],
                    "invoiced": quantize(entry["invoiced"]),
                    "items": entry["items"],
                }
                for entry in sorted(
                    category_totals.values(),
                    key=lambda item: item["category"],
                )
            ],
            "by_campus_category": [
                {
                    "category": entry["category"],
                    "campus": entry["campus"],
                    "invoiced": quantize(entry["invoiced"]),
                }
                for entry in sorted(
                    rows.values(),
                    key=lambda item: (
                        item["category"],
                        item["campus"],
                    ),
                )
            ],
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "fee_categories_report.csv",
            ["Category", "Campus", "Invoiced"],
            [
                [
                    row["category"],
                    row["campus"],
                    row["invoiced"],
                ]
                for row in data["by_campus_category"]
            ],
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)

        return super().finalize_response(
            request,
            response,
            *args,
            **kwargs,
        )


class StaffReportView(APIView):
    """Staff summary grouped by campus and designation."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.teachers.models import Teacher

        queryset = (
            Teacher.objects
            .select_related("primary_campus")
        )

        queryset = apply_campus_scope(
            queryset,
            request,
            "primary_campus_id",
        )

        rows = {}

        for teacher in queryset:
            campus_name = (
                teacher.primary_campus.name
                if teacher.primary_campus_id
                else teacher.campus or "-"
            )
            designation = teacher.designation or "Teacher"

            key = (campus_name, designation)

            entry = rows.setdefault(
                key,
                {
                    "campus": campus_name,
                    "designation": designation,
                    "count": 0,
                },
            )

            entry["count"] += 1

        return sorted(
            rows.values(),
            key=lambda item: (
                item["campus"],
                item["designation"],
            ),
        )

    def get(self, request):
        rows = self._data(request)

        return Response(
            {
                "total_staff": sum(
                    row["count"] for row in rows
                ),
                "groups": rows,
            }
        )

    def _csv(self, request):
        rows = self._data(request)

        return to_csv(
            "staff_report.csv",
            ["Campus", "Designation", "Count"],
            [
                [
                    row["campus"],
                    row["designation"],
                    row["count"],
                ]
                for row in rows
            ],
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)

        return super().finalize_response(
            request,
            response,
            *args,
            **kwargs,
        )


class ClassPerformanceReportView(APIView):
    """Class-wise performance across all exams."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.reportcards.models import ReportCard

        queryset = (
            ReportCard.objects
            .select_related(
                "exam",
                "exam__campus",
                "exam__class_obj",
            )
        )

        queryset = apply_campus_scope(
            queryset, request, "exam__campus_id",
        )

        academic_year = request.query_params.get("academic_year")
        if academic_year:
            queryset = queryset.filter(exam__academic_year_id=academic_year)

        prefetch_reportcard_results(queryset)

        classes = {}

        for rc in queryset:
            campus_name = rc.exam.campus.name if rc.exam.campus_id else "-"
            class_name = rc.exam.class_obj.name if rc.exam.class_obj_id else "-"
            key = (campus_name, class_name)

            entry = classes.setdefault(key, {
                "campus": campus_name,
                "class": class_name,
                "total_students": 0,
                "total_exams": set(),
                "passed": 0,
                "total_percentage": Decimal("0"),
                "highest": Decimal("0"),
                "lowest": None,
            })

            entry["total_students"] += 1
            entry["total_exams"].add(rc.exam_id)

            if rc.is_pass:
                entry["passed"] += 1

            pct = rc.percentage
            entry["total_percentage"] += pct

            if pct > entry["highest"]:
                entry["highest"] = pct

            if entry["lowest"] is None or pct < entry["lowest"]:
                entry["lowest"] = pct

        rows = []
        for entry in classes.values():
            total = entry["total_students"]
            exams = len(entry["total_exams"])
            avg = entry["total_percentage"] / total if total else Decimal("0")
            rows.append({
                "campus": entry["campus"],
                "class": entry["class"],
                "total_students": total,
                "exams_covered": exams,
                "passed": entry["passed"],
                "failed": total - entry["passed"],
                "pass_rate": round(entry["passed"] / total * 100, 2) if total else 0,
                "average_percentage": round(float(avg), 2),
                "highest": round(float(entry["highest"]), 2),
                "lowest": round(float(entry["lowest"]), 2) if entry["lowest"] is not None else 0,
            })

        rows.sort(key=lambda item: (item["campus"], item["class"]))

        total = sum(r["total_students"] for r in rows)
        passed = sum(r["passed"] for r in rows)
        avg_pct = sum(r["average_percentage"] for r in rows) / len(rows) if rows else 0

        return {
            "summary": {
                "total_students": total,
                "overall_pass_rate": round(passed / total * 100, 2) if total else 0,
                "overall_average": round(avg_pct, 2),
            },
            "classes": rows,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)
        return to_csv(
            "class_performance_report.csv",
            ["Campus", "Class", "Students", "Exams", "Passed", "Failed", "Pass Rate %", "Average %", "Highest %", "Lowest %"],
            [
                [
                    row["campus"],
                    row["class"],
                    row["total_students"],
                    row["exams_covered"],
                    row["passed"],
                    row["failed"],
                    row["pass_rate"],
                    row["average_percentage"],
                    row["highest"],
                    row["lowest"],
                ]
                for row in data["classes"]
            ],
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)
        return super().finalize_response(request, response, *args, **kwargs)


class StudentProgressTrendReportView(APIView):
    """Student performance trend across multiple exams."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.reportcards.models import ReportCard

        student_id = request.query_params.get("student")
        if not student_id:
            return {"summary": {}, "exams": []}

        queryset = (
            ReportCard.objects
            .filter(student_id=student_id)
            .select_related(
                "exam",
                "exam__campus",
                "exam__class_obj",
            )
            .order_by("exam__start_date")
        )

        queryset = apply_campus_scope(queryset, request, "exam__campus_id")

        exams = []
        for rc in queryset:
            exams.append({
                "exam": rc.exam.name,
                "exam_type": rc.exam.exam_type,
                "campus": rc.exam.campus.name if rc.exam.campus_id else "-",
                "class": rc.exam.class_obj.name if rc.exam.class_obj_id else "-",
                "total_marks": float(rc.total_marks),
                "maximum_marks": float(rc.maximum_marks),
                "percentage": float(rc.percentage),
                "grade": rc.grade,
                "result": rc.overall_result,
                "position": rc.position,
            })

        if not exams:
            return {"summary": {}, "exams": []}

        percentages = [e["percentage"] for e in exams]
        passed = sum(1 for e in exams if e["result"] == "Pass")

        trend = "improving" if len(percentages) >= 2 and percentages[-1] > percentages[0] else (
            "declining" if len(percentages) >= 2 and percentages[-1] < percentages[0] else "stable"
        )

        return {
            "summary": {
                "total_exams": len(exams),
                "average_percentage": round(sum(percentages) / len(percentages), 2),
                "best_percentage": round(max(percentages), 2),
                "worst_percentage": round(min(percentages), 2),
                "pass_rate": round(passed / len(exams) * 100, 2),
                "trend": trend,
            },
            "exams": exams,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)
        return to_csv(
            "student_progress_report.csv",
            ["Exam", "Type", "Campus", "Class", "Total", "Max", "Percentage", "Grade", "Result", "Position"],
            [
                [
                    row["exam"],
                    row["exam_type"],
                    row["campus"],
                    row["class"],
                    row["total_marks"],
                    row["maximum_marks"],
                    row["percentage"],
                    row["grade"],
                    row["result"],
                    row["position"],
                ]
                for row in data["exams"]
            ],
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.query_params.get("format") == "csv":
            response = self._csv(request)
        return super().finalize_response(request, response, *args, **kwargs)


class ReportTemplateListView(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        from .models import ReportTemplate

        templates = ReportTemplate.objects.filter(created_by=request.user)
        data = []
        for t in templates:
            data.append({
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "report_type": t.report_type,
                "report_type_display": t.get_report_type_display(),
                "filters": t.filters,
                "columns": t.columns,
                "is_default": t.is_default,
                "created_at": t.created_at.isoformat(),
            })
        return Response(data)

    def post(self, request):
        from .models import ReportTemplate

        name = request.data.get("name", "").strip()
        report_type = request.data.get("report_type", "")

        if not name or not report_type:
            return Response(
                {"detail": "name and report_type are required."},
                status=400,
            )

        valid_types = [c[0] for c in ReportTemplate.REPORT_TYPE_CHOICES]
        if report_type not in valid_types:
            return Response(
                {"detail": f"Invalid report_type. Must be one of: {', '.join(valid_types)}"},
                status=400,
            )

        template = ReportTemplate.objects.create(
            name=name,
            description=request.data.get("description", ""),
            report_type=report_type,
            filters=request.data.get("filters", {}),
            columns=request.data.get("columns", []),
            created_by=request.user,
        )

        return Response({
            "id": template.id,
            "name": template.name,
            "report_type": template.report_type,
            "detail": "Template created.",
        }, status=201)


class ReportTemplateDetailView(APIView):
    permission_classes = [IsAccountantRole]

    def get_object(self, pk):
        from .models import ReportTemplate

        try:
            return ReportTemplate.objects.get(pk=pk, created_by=self.request.user)
        except ReportTemplate.DoesNotExist:
            return None

    def get(self, request, pk):
        template = self.get_object(pk)
        if not template:
            return Response({"detail": "Not found."}, status=404)

        return Response({
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "report_type": template.report_type,
            "report_type_display": template.get_report_type_display(),
            "filters": template.filters,
            "columns": template.columns,
            "is_default": template.is_default,
            "created_at": template.created_at.isoformat(),
        })

    def put(self, request, pk):
        template = self.get_object(pk)
        if not template:
            return Response({"detail": "Not found."}, status=404)

        template.name = request.data.get("name", template.name)
        template.description = request.data.get("description", template.description)
        template.filters = request.data.get("filters", template.filters)
        template.columns = request.data.get("columns", template.columns)
        template.is_default = request.data.get("is_default", template.is_default)
        template.save()

        return Response({"detail": "Template updated."})

    def delete(self, request, pk):
        template = self.get_object(pk)
        if not template:
            return Response({"detail": "Not found."}, status=404)

        template.delete()
        return Response({"detail": "Template deleted."})


class ReportGenerateView(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request):
        from django.utils.module_loading import import_string

        report_type = request.data.get("report_type")
        filters = request.data.get("filters", {})

        if report_type not in REPORT_VIEW_MAP:
            return Response(
                {"detail": f"Invalid report_type: {report_type}"},
                status=400,
            )

        view_class = import_string(REPORT_VIEW_MAP[report_type])
        view_instance = view_class()

        from django.test import RequestFactory
        from rest_framework.request import Request as DRFRequest

        query_string = "&".join(f"{k}={v}" for k, v in filters.items() if v)
        url = f"/api/reports/{report_type}/?{query_string}"

        factory = RequestFactory()
        raw_req = factory.get(url)
        req = DRFRequest(raw_req)
        req._user = request.user

        try:
            data = view_instance._data(req)
        except Exception as e:
            return Response(
                {"detail": f"Report generation failed: {str(e)}"},
                status=500,
            )

        return Response(data)


# Re-export all views from their respective modules
from .extended_views import (
    ChronicAbsenteeReportView,
    CollectionTrendReportView,
    DiscountsReportView,
    EventParticipationReportView,
    InventoryValueReportView,
    LibraryOverviewReportView,
    MaintenanceDueReportView,
    PayrollSummaryReportView,
    RouteUtilizationReportView,
    SmsUsageReportView,
    TopPerformersReportView,
)

from .export_views import (
    DataBackupView,
    DataExportListView,
    DataExportView,
)

from .pdf_views import (
    PDFExportView,
    PrintView,
    ReportTemplatePreviewView,
)

from .cron_views import WeeklyReportEmailCronView

from .at_risk_views import AtRiskReportView

from .import_views import (
    ImportCommitView,
    ImportPreviewView,
    ImportTemplateView,
)

from .health_views import SystemHealthView

from .student_views import (
    StudentMasterReportView,
    StudentListReportView,
    AdmissionReportView,
    StudentProfileReportView,
    StudentStatisticsReportView,
)

from .attendance_views import (
    DailyAttendanceReportView,
    MonthlyAttendanceReportView,
    StudentAttendanceReportView,
    ClassAttendanceReportView,
    AttendanceAnalyticsReportView,
    ChronicAbsenteeReportView,
    SubjectAttendanceReportView,
)

from .exam_views import (
    ExamScheduleReportView,
    ExamMarksReportView,
    SubjectPerformanceReportView,
    ClassMarksReportView,
    StudentResultReportView,
    ResultAnalyticsReportView,
    StudentRankingReportView,
    ReportCardGeneratorView,
)

from .fee_views import (
    FeeCollectionReportView,
    FeeStatusReportView,
    FeeAnalyticsReportView,
    FinanceReportView,
    FeeDefaultersReportView,
)

from .hr_views import (
    EmployeeMasterReportView,
    HRAttendanceReportView,
    HRLeaveReportView,
    PayrollMonthlyReportView,
    EmployeeSalaryReportView,
    PayrollSummaryReportView,
    AllowanceReportView,
    DeductionReportView,
    NetSalaryReportView,
    PaidSalaryReportView,
    PendingSalaryReportView,
)

from .staff_views import (
    StaffMasterReportView,
    TeacherMasterReportView,
    StaffAttendanceReportView,
    TeacherAttendanceReportView,
    StaffLeaveReportView,
    TeacherLeaveReportView,
    TeacherWorkloadReportView,
    DepartmentReportView,
    DesignationReportView,
    StaffJoiningReportView,
    StaffResignationReportView,
    TeacherWorkloadReportView,
    DepartmentReportView,
    DesignationReportView,
    StaffJoiningReportView,
    StaffResignationReportView,
)

from .academic_views import (
    ClassStrengthReportView,
    SectionStrengthReportView,
    ClassStudentListReportView,
    GenderDistributionReportView,
    AcademicPerformanceReportView,
    PromotionReportView,
    SubjectListReportView,
    SubjectAllocationReportView,
    SubjectPerformanceReportView,
    TeacherSubjectAllocationReportView,
    StudentTimetableReportView,
    ClassTimetableReportView,
    TeacherTimetableReportView,
    RoomTimetableReportView,
    FreePeriodReportView,
)

from .parent_views import (
    ParentMasterReportView,
    ParentStudentRelationshipReportView,
    ParentContactReportView,
    ParentWiseStudentsReportView,
    OutstandingFeesByParentReportView,
    AttendanceSummaryByParentReportView,
    AcademicSummaryByParentReportView,
)

from .library_views import (
    LibraryInventoryReportView,
    AvailableBooksReportView,
    IssuedBooksReportView,
    ReturnedBooksReportView,
    OverdueBooksReportView,
    LibraryFinesReportView,
    LibraryActivitySummaryReportView,
    MostBorrowedBooksReportView,
    StudentBorrowingHistoryReportView,
    TeacherBorrowingHistoryReportView,
)

from .transport_views import (
    StudentTransportListReportView,
    RouteReportView,
    VehicleReportView,
    DriverReportView,
    PickupDropoffReportView,
    StudentsByRouteReportView,
    StudentsByVehicleReportView,
    TransportFeeReportView,
    VehicleCapacityReportView,
    RouteOccupancyReportView,
)

from .inventory_views import (
    InventoryMasterReportView,
    StockReportView,
    LowStockReportView,
    OutOfStockReportView,
    StockMovementReportView,
    PurchaseReportView,
    IssueReportView,
    ReturnReportView,
    DamagedItemsReportView,
    LostItemsReportView,
    CategoryReportView,
    SupplierReportView,
    InventoryValuationReportView,
)

from .discipline_views import (
    DisciplineIncidentsReportView,
    StudentIncidentsReportView,
    ClassIncidentsReportView,
    CampusIncidentsReportView,
    IncidentTypeReportView,
    DateRangeIncidentsReportView,
    WarningReportView,
    SuspensionReportView,
    RepeatIncidentsReportView,
    DisciplinaryHistoryReportView,
)

from .certificate_views import (
    BonafideCertificateView,
    CharacterCertificateView,
    LeavingCertificateView,
    TransferCertificateView,
    EnrollmentCertificateView,
    FeeClearanceCertificateView,
    StudentIDCardView,
    StaffIDCardView,
    CertificateTemplateListView,
    CertificateReportView,
)

from .campus_views import (
    CampusStudentCountReportView,
    CampusAttendanceReportView,
    CampusAcademicPerformanceReportView,
    CampusFeeCollectionReportView,
    CampusOutstandingFeesReportView,
    CampusStaffCountReportView,
    CampusAdmissionsReportView,
    CampusFinancialSummaryReportView,
    CampusComparisonReportView,
    CampusDashboardReportView,
)



__all__ = [
    "ReportsRootView",
    "EnrollmentReportView",
    "AttendanceReportView",
    "ResultsReportView",
    "FeesReportView",
    "PaymentMethodsReportView",
    "StudentStatusReportView",
    "FeeCategoryReportView",
    "StaffReportView",
    "ClassPerformanceReportView",
    "StudentProgressTrendReportView",
    "ReportTemplateListView",
    "ReportTemplateDetailView",
    "ReportGenerateView",
    "ChronicAbsenteeReportView",
    "CollectionTrendReportView",
    "DiscountsReportView",
    "EventParticipationReportView",
    "InventoryValueReportView",
    "LibraryOverviewReportView",
    "MaintenanceDueReportView",
    "PayrollSummaryReportView",
    "RouteUtilizationReportView",
    "SmsUsageReportView",
    "TopPerformersReportView",
    "DataBackupView",
    "DataExportListView",
    "DataExportView",
    "PDFExportView",
    "PrintView",
    "ReportTemplatePreviewView",
    "WeeklyReportEmailCronView",
    "AtRiskReportView",
    "ImportCommitView",
    "ImportPreviewView",
    "ImportTemplateView",
    "SystemHealthView",
    "StudentMasterReportView",
    "StudentListReportView",
    "AdmissionReportView",
    "StudentProfileReportView",
    "StudentStatisticsReportView",
    "DailyAttendanceReportView",
    "MonthlyAttendanceReportView",
    "StudentAttendanceReportView",
    "ClassAttendanceReportView",
    "AttendanceAnalyticsReportView",
    "ChronicAbsenteeReportView",
    "SubjectAttendanceReportView",
    "ExamScheduleReportView",
    "ExamMarksReportView",
    "SubjectPerformanceReportView",
    "ClassMarksReportView",
    "StudentResultReportView",
    "ResultAnalyticsReportView",
    "StudentRankingReportView",
    "ReportCardGeneratorView",
    "FeeCollectionReportView",
    "FeeStatusReportView",
    "FeeAnalyticsReportView",
    "FinanceReportView",
    "FeeDefaultersReportView",
    "EmployeeMasterReportView",
    "HRAttendanceReportView",
    "HRLeaveReportView",
    "PayrollMonthlyReportView",
    "EmployeeSalaryReportView",
    "PayrollSummaryReportView",
    "AllowanceReportView",
    "DeductionReportView",
    "NetSalaryReportView",
    "PaidSalaryReportView",
    "PendingSalaryReportView",
    "StaffMasterReportView",
    "TeacherMasterReportView",
    "StaffAttendanceReportView",
    "TeacherAttendanceReportView",
    "StaffLeaveReportView",
    "TeacherLeaveReportView",
    "TeacherWorkloadReportView",
    "DepartmentReportView",
    "DesignationReportView",
    "StaffJoiningReportView",
    "StaffResignationReportView",
    "TeacherWorkloadReportView",
    "DepartmentReportView",
    "DesignationReportView",
    "StaffJoiningReportView",
    "StaffResignationReportView",
    "ClassStrengthReportView",
    "SectionStrengthReportView",
    "ClassStudentListReportView",
    "GenderDistributionReportView",
    "AcademicPerformanceReportView",
    "PromotionReportView",
    "SubjectListReportView",
    "SubjectAllocationReportView",
    "SubjectPerformanceReportView",
    "TeacherSubjectAllocationReportView",
    "StudentTimetableReportView",
    "ClassTimetableReportView",
    "TeacherTimetableReportView",
    "RoomTimetableReportView",
    "FreePeriodReportView",
    "ParentMasterReportView",
    "ParentStudentRelationshipReportView",
    "ParentContactReportView",
    "ParentWiseStudentsReportView",
    "OutstandingFeesByParentReportView",
    "AttendanceSummaryByParentReportView",
    "AcademicSummaryByParentReportView",
    "LibraryInventoryReportView",
    "AvailableBooksReportView",
    "IssuedBooksReportView",
    "ReturnedBooksReportView",
    "OverdueBooksReportView",
    "LibraryFinesReportView",
    "LibraryActivitySummaryReportView",
    "MostBorrowedBooksReportView",
    "StudentBorrowingHistoryReportView",
    "TeacherBorrowingHistoryReportView",
    "StudentTransportListReportView",
    "RouteReportView",
    "VehicleReportView",
    "DriverReportView",
    "PickupDropoffReportView",
    "StudentsByRouteReportView",
    "StudentsByVehicleReportView",
    "TransportFeeReportView",
    "VehicleCapacityReportView",
    "RouteOccupancyReportView",
    "InventoryMasterReportView",
    "StockReportView",
    "LowStockReportView",
    "OutOfStockReportView",
    "StockMovementReportView",
    "PurchaseReportView",
    "IssueReportView",
    "ReturnReportView",
    "DamagedItemsReportView",
    "LostItemsReportView",
    "CategoryReportView",
    "SupplierReportView",
    "InventoryValuationReportView",
    "DisciplineIncidentsReportView",
    "StudentIncidentsReportView",
    "ClassIncidentsReportView",
    "CampusIncidentsReportView",
    "IncidentTypeReportView",
    "DateRangeIncidentsReportView",
    "WarningReportView",
    "SuspensionReportView",
    "RepeatIncidentsReportView",
    "DisciplinaryHistoryReportView",
    "BonafideCertificateView",
    "CharacterCertificateView",
    "LeavingCertificateView",
    "TransferCertificateView",
    "EnrollmentCertificateView",
    "FeeClearanceCertificateView",
    "StudentIDCardView",
    "StaffIDCardView",
    "CertificateTemplateListView",
    "CertificateReportView",
    "CampusStudentCountReportView",
    "CampusAttendanceReportView",
    "CampusAcademicPerformanceReportView",
    "CampusFeeCollectionReportView",
    "CampusOutstandingFeesReportView",
    "CampusStaffCountReportView",
    "CampusAdmissionsReportView",
    "CampusFinancialSummaryReportView",
    "CampusComparisonReportView",
    "CampusDashboardReportView",
    "ReportsRootView",
]