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
        from apps.schools.branding_context import (
            get_school_branding,
            school_logo_flowable,
        )

        record = get_object_or_404(
            payroll_queryset(
                PayrollRecord.objects.select_related(
                    "teacher",
                    "teacher__primary_campus",
                    "teacher__primary_campus__school",
                    "structure",
                ),
                request,
            ),
            pk=pk,
        )

        campus_obj = record.teacher.primary_campus
        campus = campus_obj.name if campus_obj else "-"
        school_name = (
            campus_obj.school.name
            if campus_obj and campus_obj.school_id
            else "School"
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

        from .tax import monthly_withholding

        withholding = monthly_withholding(record.gross_salary)

        if withholding > 0:
            deduction_rows.append(
                ["Income Tax (WHT)", f"{withholding:,.2f}"]
            )

        if len(deduction_rows) == 1:
            deduction_rows.append(["-", "-"])

        total_deductions = record.total_deductions + withholding

        deduction_rows.append(["Total", f"{total_deductions:,.2f}"])

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
            [["Net Salary", f"Rs {record.net_salary - withholding:,.2f}"]],
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

        logo_flowable = None

        if campus_obj and campus_obj.school_id:
            branding = get_school_branding(campus_obj.school)
            logo_flowable = school_logo_flowable(branding)

        header_row = []

        if logo_flowable is not None:
            header_row.append(logo_flowable)
            header_row.append(
                Paragraph(school_name.upper(), school_style)
            )
        else:
            header_row.append(Paragraph(school_name.upper(), school_style))

        header_table = Table(
            [header_row],
            colWidths=[18 * mm, 122 * mm] if logo_flowable else [140 * mm],
        )
        header_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ])
        )

        story = [
            header_table,
            Paragraph(
                f"Payslip — {campus}".title(),
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
