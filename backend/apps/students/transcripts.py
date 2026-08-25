"""Consolidated multi-year transcript PDF for a student (ReportLab)."""

from io import BytesIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.access import assert_campus_allowed
from apps.reports.utils import prefetch_reportcard_results


class StudentTranscriptPdfView(APIView):
    """GET /api/students/<id>/transcript.pdf"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from apps.reportcards.models import ReportCard
        from apps.students.models import Student

        student = get_object_or_404(
            Student.objects.select_related("guardian", "primary_campus"),
            pk=pk,
        )

        cards = (
            ReportCard.objects
            .filter(student=student)
            .select_related(
                "exam",
                "exam__campus",
                "exam__class_obj",
                "exam__academic_year",
            )
            .order_by("exam__start_date", "exam_id")
        )

        if not cards:
            return HttpResponse(
                "No exam results found for this student.", status=400
            )

        first = cards[0]
        exam_campus = first.exam.campus
        campus_name = (
            exam_campus.name
            if first.exam.campus_id
            else (
                student.primary_campus.name
                if student.primary_campus_id
                else "-"
            )
        )

        try:
            assert_campus_allowed(request.user, first.exam.campus_id)
        except Exception:
            return HttpResponse(
                "You do not have access to this student.", status=403
            )

        prefetch_reportcard_results(cards)

        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=18 * mm,
            bottomMargin=16 * mm,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            title=f"Transcript {student.admission_number}",
        )

        styles = getSampleStyleSheet()
        school_style = ParagraphStyle(
            "School",
            parent=styles["Normal"],
            fontSize=15,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        title_style = ParagraphStyle(
            "TitleX",
            parent=styles["Normal"],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=10,
            spaceBefore=4,
        )
        section_style = ParagraphStyle(
            "Section",
            parent=styles["Normal"],
            fontSize=11,
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=4,
        )

        info_rows = [
            ["Student", student.full_name],
            ["Admission No", student.admission_number],
            [
                "Parent / Guardian",
                getattr(student.guardian, "name", "-") or "-",
            ],
            ["Campus", campus_name],
        ]

        info_table = Table(info_rows, colWidths=[42 * mm, 128 * mm])
        info_table.setStyle(
            TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )

        story = [
            Paragraph(
                (
                    exam_campus.school.name.upper()
                    if first.exam.campus_id and exam_campus.school_id
                    else "SCHOOL"
                ),
                school_style,
            ),
            Paragraph("ACADEMIC TRANSCRIPT", title_style),
            info_table,
        ]

        # Group by academic year.
        years = {}
        for card in cards:
            year_name = (
                card.exam.academic_year.name
                if card.exam.academic_year_id
                else "Unspecified"
            )
            years.setdefault(year_name, []).append(card)

        overall_percentages = []
        total_pass = 0

        def result_table(rows):
            table = Table(
                rows,
                colWidths=[58 * mm, 24 * mm, 24 * mm, 20 * mm, 20 * mm, 24 * mm],
                repeatRows=1,
            )
            table.setStyle(
                TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ])
            )
            return table

        for year_name, year_cards in years.items():
            rows = [[
                "Examination", "Obtained", "Total", "%", "Grade", "Result",
            ]]

            year_percentages = []

            for card in year_cards:
                passed = card.is_pass

                if passed:
                    total_pass += 1

                pct = float(card.percentage)
                year_percentages.append(pct)
                overall_percentages.append(pct)

                rows.append([
                    card.exam.name[:38],
                    f"{float(card.total_marks):g}",
                    f"{float(card.maximum_marks):g}",
                    f"{pct:.1f}%",
                    card.grade or "-",
                    "Pass" if passed else "Fail",
                ])

            if year_percentages:
                avg = sum(year_percentages) / len(year_percentages)

                rows.append([
                    "Year average", "", "", f"{avg:.1f}%", "", "",
                ])

            story.append(Paragraph(year_name, section_style))
            story.append(result_table(rows))

            if year_name != list(years.keys())[-1]:
                story.append(PageBreak())

        if overall_percentages:
            summary_rows = [
                ["Exams taken", str(len(overall_percentages))],
                ["Passed", f"{total_pass} / {len(overall_percentages)}"],
                [
                    "Overall average",
                    f"{sum(overall_percentages) / len(overall_percentages):.1f}%",
                ],
                ["Best result", f"{max(overall_percentages):.1f}%"],
                ["Lowest result", f"{min(overall_percentages):.1f}%"],
            ]

            summary_table = Table(summary_rows, colWidths=[70 * mm, 100 * mm])
            summary_table.setStyle(
                TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ])
            )

            from django.utils import timezone

            story.append(Spacer(1, 6 * mm))
            story.append(Paragraph("Summary", section_style))
            story.append(summary_table)
            story.append(Spacer(1, 14 * mm))
            story.append(
                Paragraph(
                    f"Issued on {timezone.localdate().strftime('%d %B %Y')} | "
                    "______________________  Principal",
                    ParagraphStyle(
                        "Sig",
                        parent=styles["Normal"],
                        fontSize=9,
                        alignment=TA_CENTER,
                        textColor=colors.grey,
                    ),
                )
            )

        document.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="transcript_{student.admission_number}.pdf"'
        )

        return response
