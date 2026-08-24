"""Extended module-level reports (library, transport, inventory, HR,
payroll, events, communication) plus finance trends and attendance
risk reports. Each view follows the same contract as the core views:
``_data`` builds the payload, ``?format=csv`` downloads it.
"""

from datetime import date
from decimal import Decimal

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, institution_scope
from apps.accounts.permissions import IsAccountantRole

from .utils import prefetch_reportcard_results, quantize, to_csv


def _month_label(year, month):
    return f"{year}-{month:02d}"


class CollectionTrendReportView(APIView):
    """Monthly invoiced vs collected totals over a rolling window."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.finance.models import Invoice, Payment

        try:
            months = int(request.query_params.get("months", 12))
        except (TypeError, ValueError):
            months = 12

        months = max(1, min(months, 36))

        today = timezone.localdate()

        buckets = {}
        month_keys = []

        year, month = today.year, today.month

        for _ in range(months):
            key = _month_label(year, month)
            month_keys.append(key)
            buckets[key] = {
                "month": key,
                "invoiced": Decimal("0"),
                "collected": Decimal("0"),
            }

            month -= 1

            if month == 0:
                month = 12
                year -= 1

        invoices = (
            Invoice.objects
            .filter(status__in=["issued", "partial", "paid", "overdue"])
            .prefetch_related(
                "items",
                "concessions",
                "payments",
                "payments__refunds",
                "payments__reversals",
            )
        )
        invoices = apply_campus_scope(
            invoices,
            request,
            "enrollment__campus_id",
        )

        start_key = month_keys[-1]

        for invoice in invoices:
            key = _month_label(invoice.issue_date.year, invoice.issue_date.month)

            if key < start_key:
                continue

            if key not in buckets:
                continue

            total = invoice.total_amount
            buckets[key]["invoiced"] += max(total, Decimal("0"))

        payments = (
            Payment.objects
            .filter(status="completed")
            .select_related("invoice__enrollment__campus")
            .prefetch_related("refunds", "reversals")
        )
        payments = apply_campus_scope(
            payments,
            request,
            "invoice__enrollment__campus_id",
        )

        for payment in payments:
            paid_on = payment.payment_date or payment.created_at.date()
            key = _month_label(paid_on.year, paid_on.month)

            if key not in buckets:
                continue

            buckets[key]["collected"] += payment.net_amount

        rows = [
            {
                "month": buckets[key]["month"],
                "invoiced": quantize(buckets[key]["invoiced"]),
                "collected": quantize(buckets[key]["collected"]),
                "gap": quantize(
                    buckets[key]["invoiced"] - buckets[key]["collected"]
                ),
            }
            for key in reversed(month_keys)
        ]

        total_invoiced = sum(row["invoiced"] for row in rows)
        total_collected = sum(row["collected"] for row in rows)

        return {
            "summary": {
                "total_invoiced": quantize(total_invoiced),
                "total_collected": quantize(total_collected),
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
                "months": len(rows),
            },
            "months_data": rows,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "collection_trend_report.csv",
            ["Month", "Invoiced", "Collected", "Gap"],
            [
                [
                    row["month"],
                    row["invoiced"],
                    row["collected"],
                    row["gap"],
                ]
                for row in data["months_data"]
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


class DiscountsReportView(APIView):
    """Invoices reduced by discounts and approved concessions."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.finance.models import Invoice

        queryset = (
            Invoice.objects
            .filter(status__in=["issued", "partial", "paid", "overdue"])
            .prefetch_related("items", "concessions")
            .select_related(
                "student",
                "enrollment__campus",
                "academic_year",
            )
        )

        queryset = apply_campus_scope(
            queryset,
            request,
            "enrollment__campus_id",
        )

        campus_totals = {}
        rows = []
        total_discount = Decimal("0")
        total_concession = Decimal("0")

        for invoice in queryset:
            discount = invoice.discount or Decimal("0")
            concession_total = sum(
                (
                    concession.amount
                    for concession in invoice.concessions.all()
                    if concession.status == "approved"
                ),
                Decimal("0"),
            )

            if discount <= 0 and concession_total <= 0:
                continue

            subtotal = sum(
                (item.amount for item in invoice.items.all()),
                Decimal("0"),
            )
            campus_name = (
                invoice.enrollment.campus.name
                if invoice.enrollment.campus_id
                else "-"
            )

            total_discount += discount
            total_concession += concession_total

            entry = campus_totals.setdefault(
                campus_name,
                {
                    "campus": campus_name,
                    "discounts": Decimal("0"),
                    "concessions": Decimal("0"),
                    "invoices": 0,
                },
            )

            entry["discounts"] += discount
            entry["concessions"] += concession_total
            entry["invoices"] += 1

            rows.append(
                {
                    "invoice_number": invoice.invoice_number,
                    "student": invoice.student.full_name,
                    "campus": campus_name,
                    "subtotal": quantize(subtotal),
                    "discount": quantize(discount),
                    "concession": quantize(concession_total),
                    "total_reduction": quantize(discount + concession_total),
                }
            )

        rows.sort(key=lambda item: item["invoice_number"])

        return {
            "summary": {
                "invoices_affected": len(rows),
                "total_discount": quantize(total_discount),
                "total_concession": quantize(total_concession),
                "total_reduction": quantize(total_discount + total_concession),
            },
            "invoices": rows,
            "by_campus": [
                {
                    "campus": entry["campus"],
                    "discounts": quantize(entry["discounts"]),
                    "concessions": quantize(entry["concessions"]),
                    "invoices": entry["invoices"],
                }
                for entry in sorted(
                    campus_totals.values(),
                    key=lambda item: item["campus"],
                )
            ],
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "discounts_report.csv",
            ["Invoice", "Student", "Campus", "Subtotal", "Discount", "Concession", "Total Reduction"],
            [
                [
                    row["invoice_number"],
                    row["student"],
                    row["campus"],
                    row["subtotal"],
                    row["discount"],
                    row["concession"],
                    row["total_reduction"],
                ]
                for row in data["invoices"]
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


class ChronicAbsenteeReportView(APIView):
    """Students whose attendance rate falls below a threshold."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.attendance.models import Attendance

        try:
            threshold = float(request.query_params.get("threshold", 75))
        except (TypeError, ValueError):
            threshold = 75.0

        queryset = (
            Attendance.objects
            .select_related(
                "student",
                "campus",
                "class_obj",
                "section",
            )
        )

        queryset = apply_campus_scope(queryset, request, "campus_id")

        class_obj = request.query_params.get("class_obj")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        month = request.query_params.get("month")
        year = request.query_params.get("year") or str(timezone.localdate().year)

        if month:
            queryset = queryset.filter(date__year=year, date__month=month)
        else:
            queryset = queryset.filter(date__year=year)

        students = {}

        for record in queryset:
            entry = students.setdefault(
                record.student_id,
                {
                    "admission_number": record.student.admission_number,
                    "student": record.student.full_name,
                    "campus": record.campus.name,
                    "class": record.class_obj.name,
                    "section": record.section.name if record.section_id else "-",
                    "total_days": 0,
                    "present": 0,
                    "absent": 0,
                    "late": 0,
                    "leave": 0,
                },
            )

            entry["total_days"] += 1

            if record.status in ("present", "late"):
                entry["present"] += 1

            if record.status == "absent":
                entry["absent"] += 1

            if record.status == "late":
                entry["late"] += 1

            if record.status == "leave":
                entry["leave"] += 1

        flagged = []

        for entry in students.values():
            rate = (
                round(entry["present"] / entry["total_days"] * 100, 2)
                if entry["total_days"]
                else 100.0
            )

            entry["attendance_rate"] = rate

            if rate < threshold:
                flagged.append(entry)

        flagged.sort(key=lambda item: item["attendance_rate"])

        return {
            "summary": {
                "threshold": threshold,
                "students_tracked": len(students),
                "students_flagged": len(flagged),
            },
            "students": flagged,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "chronic_absentee_report.csv",
            ["Admission No", "Student", "Campus", "Class", "Section", "Days", "Present+Late", "Absent", "Leave", "Rate %"],
            [
                [
                    row["admission_number"],
                    row["student"],
                    row["campus"],
                    row["class"],
                    row["section"],
                    row["total_days"],
                    row["present"],
                    row["absent"],
                    row["leave"],
                    row["attendance_rate"],
                ]
                for row in data["students"]
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


class PayrollSummaryReportView(APIView):
    """Payroll totals grouped by pay period and campus."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.payroll.models import PayrollRecord

        queryset = (
            PayrollRecord.objects
            .select_related(
                "teacher",
                "teacher__primary_campus",
                "structure",
            )
        )

        queryset = apply_campus_scope(
            queryset,
            request,
            "teacher__primary_campus_id",
            institution_field=None,
        )

        year = request.query_params.get("year")
        month = request.query_params.get("month")

        if year:
            queryset = queryset.filter(year=year)

        if month:
            queryset = queryset.filter(month=month)

        periods = {}
        campuses = {}
        total_gross = Decimal("0")
        total_deductions = Decimal("0")
        total_net = Decimal("0")

        for record in queryset:
            period_key = _month_label(record.year, record.month)
            campus_name = (
                record.teacher.primary_campus.name
                if record.teacher.primary_campus_id
                else "-"
            )

            total_gross += record.gross_salary
            total_deductions += record.total_deductions
            total_net += record.net_salary

            period_entry = periods.setdefault(
                period_key,
                {
                    "period": period_key,
                    "employees": 0,
                    "gross": Decimal("0"),
                    "deductions": Decimal("0"),
                    "net": Decimal("0"),
                },
            )

            period_entry["employees"] += 1
            period_entry["gross"] += record.gross_salary
            period_entry["deductions"] += record.total_deductions
            period_entry["net"] += record.net_salary

            campus_entry = campuses.setdefault(
                campus_name,
                {
                    "campus": campus_name,
                    "employees": 0,
                    "gross": Decimal("0"),
                    "net": Decimal("0"),
                },
            )

            campus_entry["employees"] += 1
            campus_entry["gross"] += record.gross_salary
            campus_entry["net"] += record.net_salary

        period_rows = sorted(
            periods.values(),
            key=lambda item: item["period"],
            reverse=True,
        )

        return {
            "summary": {
                "records": sum(row["employees"] for row in period_rows),
                "total_gross": quantize(total_gross),
                "total_deductions": quantize(total_deductions),
                "total_net": quantize(total_net),
            },
            "by_period": [
                {
                    **row,
                    "gross": quantize(row["gross"]),
                    "deductions": quantize(row["deductions"]),
                    "net": quantize(row["net"]),
                }
                for row in period_rows
            ],
            "by_campus": [
                {
                    **row,
                    "gross": quantize(row["gross"]),
                    "net": quantize(row["net"]),
                }
                for row in sorted(
                    campuses.values(),
                    key=lambda item: item["campus"],
                )
            ],
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "payroll_summary_report.csv",
            ["Period", "Employees", "Gross", "Deductions", "Net"],
            [
                [
                    row["period"],
                    row["employees"],
                    row["gross"],
                    row["deductions"],
                    row["net"],
                ]
                for row in data["by_period"]
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


class LibraryOverviewReportView(APIView):
    """Library circulation overview: most borrowed books and overdue issues."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.library.models import BookIssue

        queryset = (
            BookIssue.objects
            .select_related(
                "book_copy",
                "book_copy__book",
                "book_copy__book__campus",
                "student",
                "teacher",
            )
        )

        queryset = apply_campus_scope(
            queryset,
            request,
            "book_copy__book__campus_id",
            institution_field="book_copy__book__institution_id",
        )

        today = timezone.localdate()

        borrowed = {}
        overdue_rows = []
        status_counts = {"issued": 0, "returned": 0, "overdue": 0}
        fines_outstanding = Decimal("0")
        fines_collected = Decimal("0")

        for issue in queryset:
            status_counts[issue.status] = (
                status_counts.get(issue.status, 0) + 1
            )

            book_title = issue.book_copy.book.title

            entry = borrowed.setdefault(
                book_title,
                {
                    "title": book_title,
                    "category": issue.book_copy.book.category,
                    "issues": 0,
                    "currently_out": 0,
                },
            )

            entry["issues"] += 1

            if issue.status != "returned":
                entry["currently_out"] += 1

            is_overdue = (
                issue.status == "overdue"
                or (
                    issue.status == "issued"
                    and issue.due_date < today
                )
            )

            if is_overdue:
                fines_outstanding += issue.fine or Decimal("0")

                if len(overdue_rows) < 100:
                    overdue_rows.append(
                        {
                            "title": book_title,
                            "borrower": issue.borrower or "-",
                            "issue_date": issue.issue_date,
                            "due_date": issue.due_date,
                            "days_overdue": (today - issue.due_date).days,
                            "fine": quantize(issue.fine or Decimal("0")),
                        }
                    )

            if issue.status == "returned":
                fines_collected += issue.fine or Decimal("0")

        most_borrowed = sorted(
            borrowed.values(),
            key=lambda item: item["issues"],
            reverse=True,
        )[:15]

        overdue_rows.sort(key=lambda item: item["days_overdue"], reverse=True)

        return {
            "summary": {
                "total_issues": sum(status_counts.values()),
                "returned": status_counts.get("returned", 0),
                "active_issues": status_counts.get("issued", 0),
                "marked_overdue": status_counts.get("overdue", 0),
                "fines_outstanding": quantize(fines_outstanding),
                "fines_collected": quantize(fines_collected),
            },
            "most_borrowed": most_borrowed,
            "overdue": [
                {
                    **row,
                    "issue_date": row["issue_date"].isoformat(),
                    "due_date": row["due_date"].isoformat(),
                }
                for row in overdue_rows[:50]
            ],
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "library_report.csv",
            ["Title", "Issues", "Currently Out"],
            [
                [row["title"], row["issues"], row["currently_out"]]
                for row in data["most_borrowed"]
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


class RouteUtilizationReportView(APIView):
    """Transport route capacity versus active student assignments."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.transport.models import Route

        queryset = (
            Route.objects
            .filter(status=True)
            .select_related("campus", "vehicle", "driver")
            .prefetch_related("assignments")
        )

        queryset = apply_campus_scope(queryset, request, "campus_id")

        rows = []
        total_capacity = 0
        total_students = 0

        for route in queryset:
            active_students = sum(
                1
                for assignment in route.assignments.all()
                if assignment.status == "active"
            )

            capacity = route.vehicle.capacity if route.vehicle_id else 0

            utilization = (
                round(active_students / capacity * 100, 2)
                if capacity
                else 0
            )

            total_capacity += capacity
            total_students += active_students

            rows.append(
                {
                    "route": route.name,
                    "campus": route.campus.name if route.campus_id else "-",
                    "vehicle": (
                        route.vehicle.plate_number
                        if route.vehicle_id
                        else "-"
                    ),
                    "driver": route.driver.full_name if route.driver_id else "-",
                    "capacity": capacity,
                    "students": active_students,
                    "seats_free": max(capacity - active_students, 0),
                    "utilization": utilization,
                }
            )

        rows.sort(key=lambda item: (item["campus"], item["route"]))

        overloaded = sum(1 for row in rows if row["utilization"] > 100)

        return {
            "summary": {
                "routes": len(rows),
                "total_capacity": total_capacity,
                "total_students": total_students,
                "average_utilization": (
                    round(total_students / total_capacity * 100, 2)
                    if total_capacity
                    else 0
                ),
                "overloaded_routes": overloaded,
            },
            "routes": rows,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "route_utilization_report.csv",
            ["Route", "Campus", "Vehicle", "Driver", "Capacity", "Students", "Seats Free", "Utilization %"],
            [
                [
                    row["route"],
                    row["campus"],
                    row["vehicle"],
                    row["driver"],
                    row["capacity"],
                    row["students"],
                    row["seats_free"],
                    row["utilization"],
                ]
                for row in data["routes"]
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


class InventoryValueReportView(APIView):
    """Asset counts and value grouped by category and campus."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.inventory.models import Asset

        queryset = Asset.objects.select_related("category", "campus")

        queryset = apply_campus_scope(queryset, request, "campus_id")

        category_param = request.query_params.get("category")

        if category_param:
            queryset = queryset.filter(category_id=category_param)

        categories = {}
        campuses = {}
        statuses = {}
        total_value = Decimal("0")
        total_items = 0
        total_quantity = 0

        for asset in queryset:
            value = asset.unit_cost * asset.quantity

            total_value += value
            total_items += 1
            total_quantity += asset.quantity

            statuses[asset.status] = statuses.get(asset.status, 0) + 1

            category_name = asset.category.name if asset.category_id else "Uncategorized"
            campus_name = asset.campus.name if asset.campus_id else "-"

            category_entry = categories.setdefault(
                category_name,
                {
                    "category": category_name,
                    "items": 0,
                    "quantity": 0,
                    "value": Decimal("0"),
                },
            )

            category_entry["items"] += 1
            category_entry["quantity"] += asset.quantity
            category_entry["value"] += value

            campus_entry = campuses.setdefault(
                campus_name,
                {
                    "campus": campus_name,
                    "items": 0,
                    "quantity": 0,
                    "value": Decimal("0"),
                },
            )

            campus_entry["items"] += 1
            campus_entry["quantity"] += asset.quantity
            campus_entry["value"] += value

        return {
            "summary": {
                "items": total_items,
                "quantity": total_quantity,
                "total_value": quantize(total_value),
                "statuses": [
                    {"status": name.title(), "count": count}
                    for name, count in sorted(statuses.items())
                ],
            },
            "by_category": [
                {
                    **row,
                    "value": quantize(row["value"]),
                }
                for row in sorted(
                    categories.values(),
                    key=lambda item: item["value"],
                    reverse=True,
                )
            ],
            "by_campus": [
                {
                    **row,
                    "value": quantize(row["value"]),
                }
                for row in sorted(
                    campuses.values(),
                    key=lambda item: item["campus"],
                )
            ],
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "inventory_value_report.csv",
            ["Grouping", "Name", "Items", "Quantity", "Value"],
            [
                ["Category", row["category"], row["items"], row["quantity"], row["value"]]
                for row in data["by_category"]
            ]
            + [
                ["Campus", row["campus"], row["items"], row["quantity"], row["value"]]
                for row in data["by_campus"]
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


class MaintenanceDueReportView(APIView):
    """Open maintenance work and assets currently under maintenance."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.inventory.models import Asset, MaintenanceRecord

        records = (
            MaintenanceRecord.objects
            .filter(status__in=["scheduled", "in_progress"])
            .select_related("asset", "asset__campus", "asset__category")
        )

        records = apply_campus_scope(records, request, "asset__campus_id")

        rows = []
        scheduled_cost = Decimal("0")
        in_progress_cost = Decimal("0")

        for record in records:
            cost = record.cost or Decimal("0")

            if record.status == "scheduled":
                scheduled_cost += cost
            else:
                in_progress_cost += cost

            rows.append(
                {
                    "asset": record.asset.name,
                    "code": record.asset.code or "-",
                    "campus": (
                        record.asset.campus.name
                        if record.asset.campus_id
                        else "-"
                    ),
                    "status": record.status,
                    "date": record.date.isoformat(),
                    "cost": quantize(cost),
                    "description": (
                        record.description[:120] if record.description else "-"
                    ),
                    "performed_by": record.performed_by or "-",
                }
            )

        rows.sort(key=lambda item: item["date"])

        assets_in_maintenance = (
            Asset.objects
            .filter(status="maintenance")
        )
        assets_in_maintenance = apply_campus_scope(
            assets_in_maintenance,
            request,
            "campus_id",
        )

        return {
            "summary": {
                "open_records": len(rows),
                "scheduled_cost": quantize(scheduled_cost),
                "in_progress_cost": quantize(in_progress_cost),
                "assets_in_maintenance": assets_in_maintenance.count(),
            },
            "records": rows,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "maintenance_due_report.csv",
            ["Asset", "Code", "Campus", "Status", "Date", "Cost", "Performed By", "Description"],
            [
                [
                    row["asset"],
                    row["code"],
                    row["campus"],
                    row["status"],
                    row["date"],
                    row["cost"],
                    row["performed_by"],
                    row["description"],
                ]
                for row in data["records"]
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


class EventParticipationReportView(APIView):
    """RSVP responses per event with attendance rates."""

    permission_classes = [IsAccountantRole]

    STATUS_FILTERS = {
        "published": "published",
        "draft": "draft",
        "cancelled": "cancelled",
        "all": None,
    }

    def _data(self, request):
        from apps.events.models import Event

        queryset = Event.objects.prefetch_related("rsvps").select_related("campus")

        queryset = apply_campus_scope(
            queryset,
            request,
            "campus_id",
            institution_field="school_id",
        )

        status_param = request.query_params.get("status", "published")

        if status_param in self.STATUS_FILTERS and self.STATUS_FILTERS[status_param]:
            queryset = queryset.filter(status=self.STATUS_FILTERS[status_param])

        rows = []
        totals = {"yes": 0, "no": 0, "maybe": 0}

        for event in queryset:
            counts = {"yes": 0, "no": 0, "maybe": 0}

            for rsvp in event.rsvps.all():
                if rsvp.response in counts:
                    counts[rsvp.response] += 1

                    totals[rsvp.response] += 1

            responded = sum(counts.values())

            rows.append(
                {
                    "event": event.title,
                    "campus": event.campus.name if event.campus_id else "-",
                    "start": timezone.localtime(event.start_datetime).strftime("%Y-%m-%d %H:%M"),
                    "attending": counts["yes"],
                    "not_attending": counts["no"],
                    "maybe": counts["maybe"],
                    "responses": responded,
                    "participation_rate": (
                        round(counts["yes"] / responded * 100, 2)
                        if responded
                        else 0
                    ),
                }
            )

        rows.sort(key=lambda item: item["start"], reverse=True)

        total_responses = sum(totals.values())

        return {
            "summary": {
                "events": len(rows),
                "total_responses": total_responses,
                "attending": totals["yes"],
                "participation_rate": (
                    round(totals["yes"] / total_responses * 100, 2)
                    if total_responses
                    else 0
                ),
            },
            "events": rows,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "event_participation_report.csv",
            ["Event", "Campus", "Start", "Attending", "Not Attending", "Maybe", "Responses", "Participation %"],
            [
                [
                    row["event"],
                    row["campus"],
                    row["start"],
                    row["attending"],
                    row["not_attending"],
                    row["maybe"],
                    row["responses"],
                    row["participation_rate"],
                ]
                for row in data["events"]
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


class SmsUsageReportView(APIView):
    """SMS delivery volumes grouped by month."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.communication.models import SMSLog

        queryset = SMSLog.objects.all()

        institution = getattr(request, "institution", None)

        if institution is not None:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(institution=institution) | Q(institution__isnull=True)
            )

        year = request.query_params.get("year") or str(timezone.localdate().year)
        queryset = queryset.filter(created_at__year=year)

        months = {}

        for sms in queryset.iterator():
            key = _month_label(sms.created_at.year, sms.created_at.month)

            entry = months.setdefault(
                key,
                {
                    "month": key,
                    "sent": 0,
                    "failed": 0,
                    "queued": 0,
                    "total": 0,
                },
            )

            entry[sms.status] = entry.get(sms.status, 0) + 1
            entry["total"] += 1

        rows = sorted(
            months.values(),
            key=lambda item: item["month"],
        )

        for row in rows:
            delivered = row["sent"]

            row["success_rate"] = (
                round(delivered / row["total"] * 100, 2)
                if row["total"]
                else 0
            )

        total = sum(row["total"] for row in rows)
        sent = sum(row["sent"] for row in rows)
        failed = sum(row["failed"] for row in rows)

        return {
            "summary": {
                "year": int(year),
                "total_messages": total,
                "sent": sent,
                "failed": failed,
                "success_rate": round(sent / total * 100, 2) if total else 0,
            },
            "months_data": rows,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "sms_usage_report.csv",
            ["Month", "Sent", "Failed", "Queued", "Total", "Success Rate %"],
            [
                [
                    row["month"],
                    row["sent"],
                    row["failed"],
                    row["queued"],
                    row["total"],
                    row["success_rate"],
                ]
                for row in data["months_data"]
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


class TopPerformersReportView(APIView):
    """Top N students per class for an exam."""

    permission_classes = [IsAccountantRole]

    def _data(self, request):
        from apps.reportcards.models import ReportCard

        exam = request.query_params.get("exam")

        if not exam:
            return {
                "summary": {"classes": 0, "students": 0},
                "performers": [],
            }

        try:
            top_n = max(1, min(int(request.query_params.get("top", 3)), 10))
        except (TypeError, ValueError):
            top_n = 3

        queryset = (
            ReportCard.objects
            .filter(exam_id=exam)
            .select_related(
                "student",
                "exam",
                "exam__campus",
                "exam__class_obj",
            )
        )

        classes = {}

        cards = sorted(
            prefetch_reportcard_results(queryset),
            key=lambda card: card.percentage,
            reverse=True,
        )

        for card in cards:
            class_name = (
                card.exam.class_obj.name
                if card.exam.class_obj_id
                else "-"
            )
            campus_name = (
                card.exam.campus.name
                if card.exam.campus_id
                else "-"
            )

            entry = classes.setdefault(
                (campus_name, class_name),
                [],
            )

            if len(entry) >= top_n:
                continue

            entry.append(card)

        performers = []

        for (campus_name, class_name), cards in classes.items():
            for index, card in enumerate(cards, 1):
                performers.append(
                    {
                        "position": index,
                        "class": class_name,
                        "campus": campus_name,
                        "admission_number": card.student.admission_number,
                        "student": card.student.full_name,
                        "percentage": float(card.percentage),
                        "grade": card.grade,
                        "marks_obtained": float(card.total_marks),
                        "marks_total": float(card.maximum_marks),
                    }
                )

        performers.sort(
            key=lambda item: (item["campus"], item["class"], item["position"]),
        )

        return {
            "summary": {
                "classes": len(classes),
                "students": len(performers),
                "top_n": top_n,
            },
            "performers": performers,
        }

    def get(self, request):
        return Response(self._data(request))

    def _csv(self, request):
        data = self._data(request)

        return to_csv(
            "top_performers_report.csv",
            ["Position", "Campus", "Class", "Admission No", "Student", "Percentage", "Grade", "Marks"],
            [
                [
                    row["position"],
                    row["campus"],
                    row["class"],
                    row["admission_number"],
                    row["student"],
                    row["percentage"],
                    row["grade"],
                    f"{row['marks_obtained']}/{row['marks_total']}",
                ]
                for row in data["performers"]
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
