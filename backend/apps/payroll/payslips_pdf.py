"""Printable payslip PDF for a payroll record (ReportLab)."""

from io import BytesIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.access import assert_campus_allowed


class PayrollPayslipPdfView(APIView):
    """GET /api/payroll/records/<pk>/payslip.pdf"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from .models import PayrollRecord
        from .views import payroll_queryset

        record = get_object_or_404(
            payroll_queryset(
                PayrollRecord.objects.select_related(
                    "teacher",
                    "teacher__primary_campus",
                    "structure",
                ),
                request,
            ),
            pk=pk,
        )

        campus = (
            record.teacher.primary_campus.name
            if record.teacher.primary_campus_id
            else "-"
        )
        school_name = (
            record.teacher.primary_campus.school.name
            if record.teacher.primary_campus_id
            and record.teacher.primary_campus.school_id
            else "Perfect Foundation School"
        )

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A5,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            title=f"Payslip {record.year}-{record.month:02d}",
        )

        styles = getSampleStyleSheet()
        school_style = ParagraphStyle(
            "School",
            parent=styles["Normal"],
            fontSize=13,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        title_style = ParagraphStyle(
            "PayslipTitle",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=8,
        )

        rows = [
            ["Employee", record.teacher.full_name],
            ["Employee No", record.teacher.employee_number],
            ["Campus", campus],
            ["Period", f"{record.year}-{record.month:02d}"],
            ["Paid Days", f"{record.paid_days} / {record.working_days}"],
        ]

        info_table = Table(rows, colWidths=[32 * mm, 108 * mm])
        info_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

        earnings_rows = [["Earnings", "Amount (Rs)"]]
        earnings_rows.append(["Basic Salary", f"{record.basic_salary:,.2f}"])

        for name, value in sorted((record.allowances or {}).items()):
            earnings_rows.append([name.replace("_", " ").title(), f"{value:,.2f}"])

        earnings_rows.append(["Gross", f"{record.gross_salary:,.2f}"])

        deduction_rows = [["Deductions", "Amount (Rs)"]]

        if record.deductions:
            for name, value in sorted(record.deductions.items()):
                deduction_rows.append(
                    [name.replace("_", " ").title(), f"{value:,.2f}"]
                )
        else:
            deduction_rows.append(["-", "-"])

        deduction_rows.append(["Total", f"{record.total_deductions:,.2f}"])

        def money_table(data, highlight_last=True):
            table = Table(data, colWidths=[80 * mm, 60 * mm])
            style = [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]

            if highlight_last:
                style += [
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
                ]

            table.setStyle(TableStyle(style))
            return table

        net_table = Table(
            [["Net Salary", f"Rs {record.net_salary:,.2f}"]],
            colWidths=[140 * mm],
        )
        net_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ecfdf5")),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#22c55e")),
                ]
            )
        )

        story = [
            Paragraph(school_name.upper(), school_style),
            Paragraph(
                f"PAYSLP — {campus}".upper().replace("PAYSLP", "Payslip"),
                title_style,
            ),
            info_table,
            Spacer(1, 4 * mm),
            money_table(earnings_rows),
            Spacer(1, 3 * mm),
            money_table(deduction_rows),
            Spacer(1, 4 * mm),
            net_table,
            Spacer(1, 10 * mm),
            Paragraph(
                "System generated payslip — signature not required.",
                ParagraphStyle(
                    "FooterNote",
                    parent=styles["Normal"],
                    fontSize=7,
                    alignment=TA_CENTER,
                    textColor=colors.grey,
                ),
            ),
        ]

        document.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="payslip_{record.teacher.employee_number}'
            f'_{record.year}_{record.month:02d}.pdf"'
        )

        return response
