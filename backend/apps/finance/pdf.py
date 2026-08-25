"""PDF generation for finance documents (payment receipts).

Uses reportlab's platypus to produce a clean, print-ready A5 receipt.
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def payment_receipt_pdf(payment):
    """Return the bytes of a printable receipt PDF for a payment."""
    from apps.schools.branding_context import (
        get_school_branding,
        school_logo_flowable,
    )

    invoice = payment.invoice
    student = invoice.student

    campus = invoice.enrollment.campus if invoice.enrollment_id else None
    school = getattr(campus, "school", None)

    branding = get_school_branding(school) if school else {
        "name": "School",
        "logo_bytes": None,
        "primary_color": "#1a73e8",
        "footer_text": "",
    }

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A5,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    title = ParagraphStyle(
        "title",
        fontName="Helvetica-Bold",
        fontSize=15,
        alignment=1,
        spaceAfter=2,
    )
    subtitle = ParagraphStyle(
        "subtitle",
        fontName="Helvetica",
        fontSize=9,
        alignment=1,
        textColor=colors.HexColor("#555555"),
        spaceAfter=10,
    )
    heading = ParagraphStyle(
        "heading",
        fontName="Helvetica-Bold",
        fontSize=12,
        alignment=1,
        spaceBefore=6,
        spaceAfter=8,
    )
    cell = ParagraphStyle(
        "cell",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
    )
    cell_bold = ParagraphStyle(
        "cell-bold",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
    )
    total = ParagraphStyle(
        "total",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
    )

    story = []

    logo = school_logo_flowable(branding, width=16 * mm, height=16 * mm)

    if logo:
        logo_table = Table(
            [[logo, Paragraph(branding["name"], title)]],
            colWidths=[20 * mm, 116 * mm],
        )
        logo_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
            ])
        )
        story.append(logo_table)
    else:
        story.append(Paragraph(branding["name"], title))

    story.append(Paragraph("Official Payment Receipt", subtitle))

    meta = Table(
        [
            [Paragraph("Receipt No.", cell_bold), Paragraph(payment.receipt_number, cell)],
            [Paragraph("Payment Date", cell_bold), Paragraph(str(payment.payment_date), cell)],
            [Paragraph("Invoice No.", cell_bold), Paragraph(invoice.invoice_number, cell)],
            [Paragraph("Payment Method", cell_bold), Paragraph(payment.get_payment_method_display(), cell)],
        ],
        colWidths=[34 * mm, 55 * mm],
    )
    meta.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    story.append(meta)
    story.append(Spacer(1, 6))

    student_meta = Table(
        [
            [Paragraph("Student", cell_bold), Paragraph(student.full_name, cell)],
            [Paragraph("Admission No.", cell_bold), Paragraph(student.admission_number, cell)],
            [Paragraph("Class", cell_bold), Paragraph(invoice.enrollment.class_obj.name, cell)],
            [Paragraph("Section", cell_bold), Paragraph(invoice.enrollment.section.name, cell)],
            [Paragraph("Academic Year", cell_bold), Paragraph(invoice.academic_year.name, cell)],
        ],
        colWidths=[34 * mm, 55 * mm],
    )
    student_meta.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    story.append(student_meta)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Payment Summary", heading))

    items = [[
        Paragraph("Description", cell_bold),
        Paragraph("Amount", cell_bold),
    ]]

    for item in invoice.items.select_related("category").all():
        items.append([
            Paragraph(item.description, cell),
            Paragraph(f"Rs. {item.amount:,.2f}", cell),
        ])

    if invoice.discount:
        items.append([
            Paragraph("Discount", cell),
            Paragraph(f"- Rs. {invoice.discount:,.2f}", cell),
        ])

    items.append([
        Paragraph("Invoice Total", cell_bold),
        Paragraph(f"Rs. {invoice.total_amount:,.2f}", cell_bold),
    ])
    items.append([
        Paragraph("Amount Paid", cell),
        Paragraph(f"Rs. {payment.amount:,.2f}", cell),
    ])
    items.append([
        Paragraph("Balance Due", cell),
        Paragraph(f"Rs. {invoice.balance:,.2f}", cell),
    ])

    if payment.reference:
        items.append([
            Paragraph("Reference", cell),
            Paragraph(payment.reference, cell),
        ])

    table = Table(
        items,
        colWidths=[66 * mm, 23 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f4f7")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )

    story.append(table)

    if payment.notes:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Notes: {payment.notes}", cell))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This is a computer-generated receipt.",
        subtitle,
    ))

    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()
