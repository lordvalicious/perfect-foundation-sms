from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAccountantRole

from .utils import quantize, to_csv


class EnrollmentReportView(APIView):
    """Enrollment summary grouped by campus and class."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.students.models import Enrollment

        queryset = (
            Enrollment.objects
            .filter(status="active")
            .select_related("campus", "class_obj", "student")
        )

        academic_year = request.query_params.get("academic_year")

        if academic_year:
            queryset = queryset.filter(
                academic_year_id=academic_year,
            )

        campus = request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus_id=campus)

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

        campus = request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus_id=campus)

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
        from apps.finance.models import Invoice

        invoices = Invoice.objects.prefetch_related(
            "items",
            "payments",
        )

        campus = request.query_params.get("campus")

        if campus:
            invoices = invoices.filter(enrollment__campus_id=campus)

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

        for invoice in invoices:
            invoiced = invoice.total_amount
            collected = invoice.paid_amount
            balance = invoice.balance

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

            method = request.query_params.get("payment_method")

            for payment in invoice.payments.filter(
                status="completed",
            ):
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


class StaffReportView(APIView):
    """Staff summary grouped by campus and designation."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.teachers.models import Teacher

        queryset = (
            Teacher.objects
            .select_related("campus")
        )

        campus = request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus_id=campus)

        rows = {}

        for teacher in queryset:
            campus_name = (
                teacher.campus.name
                if teacher.campus_id
                else "-"
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
