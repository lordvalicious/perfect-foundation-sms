"""PDF generation for report cards using ReportLab."""

from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _style():
    styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "TitleX",
            parent=styles["Title"],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleX",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=6,
        ),
        "normal": ParagraphStyle(
            "NormalX",
            parent=styles["Normal"],
            fontSize=10,
        ),
        "small": ParagraphStyle(
            "SmallX",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.grey,
        ),
        "table_head": ParagraphStyle(
            "TableHead",
            parent=styles["Normal"],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=9,
        ),
        "table_center": ParagraphStyle(
            "TableCenter",
            parent=styles["Normal"],
            fontSize=9,
            alignment=TA_CENTER,
        ),
        "right": ParagraphStyle(
            "RightX",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_RIGHT,
        ),
    }


def build_report_card_pdf(report_card):
    """Return the bytes of a formatted report card PDF."""
    s = _style()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Report Card - {report_card.student.full_name}",
        author="Perfect Foundation School",
    )

    enrollment = (
        report_card.student.enrollments
        .filter(
            academic_year=report_card.exam.academic_year,
            campus=report_card.exam.campus,
            class_obj=report_card.exam.class_obj,
            status="active",
        )
        .select_related("section")
        .first()
    )

    flow = []

    flow.append(Paragraph("PERFECT FOUNDATION SCHOOL", s["title"]))
    flow.append(Paragraph("Academic Progress Report", s["subtitle"]))

    info_data = [
        [
            f"Student: {report_card.student.full_name}",
            f"Admission No: {report_card.student.admission_number}",
        ],
        [
            f"Class: {report_card.exam.class_obj.name}",
            f"Section: {enrollment.section.name if enrollment and enrollment.section else '-'}",
        ],
        [
            f"Exam: {report_card.exam.name}",
            f"Academic Year: {report_card.exam.academic_year}",
        ],
        [
            f"Campus: {report_card.exam.campus.name}",
            f"Date: {report_card.exam.start_date} to {report_card.exam.end_date}",
        ],
    ]

    info_table = Table(info_data, colWidths=[90 * mm, 84 * mm])

    info_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    flow.append(info_table)
    flow.append(Spacer(1, 8 * mm))

    header = [
        Paragraph("Subject", s["table_head"]),
        Paragraph("Theory", s["table_head"]),
        Paragraph("Practical", s["table_head"]),
        Paragraph("Total", s["table_head"]),
        Paragraph("Maximum", s["table_head"]),
        Paragraph("Grade", s["table_head"]),
        Paragraph("Remarks", s["table_head"]),
    ]

    rows = [header]

    theory_map = {}
    practical_map = {}

    for theory in report_card.results:
        theory_map[theory.exam_subject_id] = theory

    from apps.exams.models import PracticalResult

    for practical in (
        PracticalResult.objects
        .filter(
            exam=report_card.exam,
            student=report_card.student,
        )
    ):
        practical_map[practical.exam_subject_id] = practical

    subject_ids = set(theory_map.keys()) | set(practical_map.keys())

    from apps.exams.models import ExamSubject

    subjects = (
        ExamSubject.objects
        .filter(id__in=subject_ids)
        .select_related("subject")
        .order_by("subject__name")
    )

    for exam_subject in subjects:
        theory = theory_map.get(exam_subject.id)
        practical = practical_map.get(exam_subject.id)

        total = Decimal("0.00")
        obtained = 0
        maximum = exam_subject.maximum_marks
        grade = ""
        passed = True
        remarks = "-"

        if practical is not None:
            maximum += practical.maximum_marks
            total += practical.obtained_marks
            passed = passed and practical.is_pass
            grade = practical.grade
            remarks = practical.remarks

        if theory is not None:
            total += theory.obtained_marks
            passed = passed and theory.is_pass
            grade = grade or theory.grade
            remarks = remarks or theory.remarks

        rows.append(
            [
                Paragraph(exam_subject.subject.name, s["table_cell"]),
                Paragraph(
                    str(theory.obtained_marks) if theory else "-",
                    s["table_center"],
                ),
                Paragraph(
                    str(practical.obtained_marks) if practical else "-",
                    s["table_center"],
                ),
                Paragraph(str(total), s["table_center"]),
                Paragraph(str(maximum), s["table_center"]),
                Paragraph(grade or "-", s["table_center"]),
                Paragraph(remarks, s["table_cell"]),
            ]
        )

    marks_table = Table(
        rows,
        colWidths=[52 * mm, 20 * mm, 20 * mm, 20 * mm, 22 * mm, 16 * mm, 24 * mm],
        repeatRows=1,
    )

    marks_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a5dab")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4fb")]),
            ]
        )
    )

    flow.append(marks_table)
    flow.append(Spacer(1, 6 * mm))

    summary = [
        [
            f"Total Marks: {report_card.total_marks}",
            f"Maximum: {report_card.maximum_marks}",
        ],
        [
            f"Percentage: {report_card.percentage}%",
            f"Grade: {report_card.grade}",
        ],
        [
            f"Position: {report_card.position if report_card.position else '-'}",
            f"Result: {report_card.overall_result}",
        ],
    ]

    summary_table = Table(
        [
            [Paragraph(summary[0][0], s["right"]), Paragraph(summary[0][1], s["right"])],
            [Paragraph(summary[1][0], s["right"]), Paragraph(summary[1][1], s["right"])],
            [Paragraph(summary[2][0], s["right"]), Paragraph(summary[2][1], s["right"])],
        ],
        colWidths=[87 * mm, 87 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    flow.append(summary_table)
    flow.append(Spacer(1, 8 * mm))

    remarks_rows = [
        [Paragraph("<b>Teacher Remarks</b>", s["normal"])],
        [Paragraph(report_card.teacher_remarks or "-", s["normal"])],
        [Spacer(1, 3 * mm)],
        [Paragraph("<b>Principal Remarks</b>", s["normal"])],
        [Paragraph(report_card.principal_remarks or "-", s["normal"])],
    ]

    remarks_table = Table(remarks_rows, colWidths=[174 * mm])

    remarks_table.setStyle(
        TableStyle(
            [
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    flow.append(remarks_table)
    flow.append(Spacer(1, 10 * mm))

    signatures = Table(
        [
            [Paragraph("Teacher Signature", s["small"]), Paragraph("Principal Signature", s["small"])],
        ],
        colWidths=[87 * mm, 87 * mm],
    )

    flow.append(signatures)

    doc.build(flow)

    return buffer.getvalue()
