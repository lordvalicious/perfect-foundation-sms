"""Bank transfer file export for a payroll period (CSV)."""

import csv
from decimal import Decimal

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .tax import monthly_withholding


class PayrollBankFileView(APIView):
    """GET /api/payroll/records/bank-file/?year=&month=

    CSV: Employee No, Name, Bank, Account/IBAN, Gross, WHT, Net Payable.
    Rows with no bank/account details are flagged so finance can chase them.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import PayrollRecord
        from .views import payroll_queryset

        year = request.query_params.get("year")
        month = request.query_params.get("month")

        queryset = payroll_queryset(
            PayrollRecord.objects.select_related(
                "teacher",
                "teacher__primary_campus",
            ),
            request,
        )

        if year:
            queryset = queryset.filter(year=year)

        if month:
            queryset = queryset.filter(month=month)

        if not year or not month:
            return HttpResponse(
                "Provide ?year= and ?month=.", status=400
            )

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="bank_transfer_{year}_{int(month):02d}.csv"'
        )

        response.write("\ufeff")

        writer = csv.writer(response)
        writer.writerow([
            "Employee No",
            "Employee Name",
            "Campus",
            "Bank",
            "Account / IBAN",
            "Gross Salary",
            "Income Tax WHT",
            "Net Payable",
            "Missing Bank Details",
        ])

        rows_written = 0
        total_payable = Decimal("0")

        for record in queryset.order_by(
            "teacher__primary_campus__name", "teacher__employee_number"
        ):
            withholding = monthly_withholding(record.gross_salary)
            payable = max(record.net_salary - withholding, Decimal("0"))
            total_payable += payable

            missing = "YES" if (
                not record.teacher.account_number
            ) else ""

            writer.writerow([
                record.teacher.employee_number,
                record.teacher.full_name,
                (
                    record.teacher.primary_campus.name
                    if record.teacher.primary_campus_id
                    else "-"
                ),
                record.teacher.bank_name or "-",
                record.teacher.account_number or "-",
                f"{record.gross_salary:.2f}",
                f"{withholding:.2f}",
                f"{payable:.2f}",
                missing,
            ])

            rows_written += 1

        writer.writerow([])
        writer.writerow(["", "", "", "", "", "", "TOTAL", f"{total_payable:.2f}", ""])

        if not rows_written:
            writer.writerow(["No payroll records for this period."])

        return response
