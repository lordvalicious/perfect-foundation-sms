"""Bank transfer file export for a payroll period (CSV)."""

import csv
from decimal import Decimal

from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAccountantRole

from .tax import monthly_withholding


class PayrollBankFileView(APIView):
    """GET /api/payroll/records/bank-file/?year=&month=

    CSV: Employee No, Name, Bank, Account/IBAN, Gross, WHT, Net Payable.
    Rows with no bank/account details are flagged so finance can chase them.
    """

    permission_classes = [IsAccountantRole]

    def get(self, request):
        from .models import PayrollRecord
        from .views import payroll_queryset

        year = request.query_params.get("year")
        month = request.query_params.get("month")

        queryset = payroll_queryset(
            PayrollRecord.objects.select_related(
                "employee",
                "employee__primary_campus",
                "employee__teacher",
            ),
            request,
        )

        if year:
            queryset = queryset.filter(year=year)

        if month:
            queryset = queryset.filter(month=month)

        if not year or not month:
            return Response(
                {"detail": "Provide ?year= and ?month=."}, status=400
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
            "employee__primary_campus__name", "employee__employee_number"
        ):
            withholding = monthly_withholding(record.gross_salary)
            payable = max(record.net_salary - withholding, Decimal("0"))
            total_payable += payable

            employee = record.employee
            bank_name = (
                employee.teacher.bank_name
                if employee.teacher and employee.teacher.bank_name
                else None
            )
            account_number = (
                employee.teacher.account_number
                if employee.teacher and employee.teacher.account_number
                else None
            )

            missing = "YES" if not account_number else ""

            writer.writerow([
                employee.employee_number,
                employee.full_name,
                (
                    employee.primary_campus.name
                    if employee.primary_campus_id
                    else "-"
                ),
                bank_name or "-",
                account_number or "-",
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
