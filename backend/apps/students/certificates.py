"""Printable student certificates (ReportLab).

Supported types:
- bonafide    — certificate of enrolment / study
- character   — conduct certificate
- transfer    — school leaving / transfer certificate
"""

from datetime import date
from io import BytesIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
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
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.access import assert_campus_allowed

CERTIFICATE_TYPES = ("bonafide", "character", "transfer")


class StudentCertificatePdfView(APIView):
    """GET /api/students/<id>/certificate/<type>/?date=&remarks="""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk, cert_type):
        from apps.students.models import Student

        if cert_type not in CERTIFICATE_TYPES:
            return HttpResponse(
                "Unknown certificate type.", status=404
            )

        student = get_object_or_404(
            Student.objects.select_related(
                "guardian",
                "primary_campus",
            ),
            pk=pk,
        )

        enrollment = (
            student.enrollments.filter(status="active")
            .select_related(
                "campus",
                "class_obj",
                "section",
                "academic_year",
                "academic_year__school",
            )
            .order_by("-enrollment_date")
            .first()
        )

        if enrollment is None:
            return HttpResponse(
                "Student has no active enrollment.", status=400
            )

        campus = enrollment.campus

        try:
            assert_campus_allowed(request.user, campus.id)
        except Exception:
            return HttpResponse(
                "You do not have access to this student.",
                status=403,
            )

        issue_date_raw = request.query_params.get("date")
        remarks = request.query_params.get("remarks", "").strip()

        try:
            issue_date = (
                date.fromisoformat(issue_date_raw)
                if issue_date_raw
                else timezone.localdate()
            )
        except ValueError:
            issue_date = timezone.localdate()

        school_name = campus.school.name if campus.school_id else "School"
        son_daughter = "son" if (student.gender or "") == "male" else "daughter"

        details = [
            ["Name", student.full_name],
            ["Admission No", student.admission_number],
            [
                f"{son_daughter.title()} of",
                getattr(student.guardian, "name", "-") or "-",
            ],
            ["Date of Birth", str(student.date_of_birth or "-")],
            ["Class", f"{enrollment.class_obj.name} - {enrollment.section.name}" if enrollment.section_id else enrollment.class_obj.name],
            ["Campus", campus.name],
            ["Academic Year", enrollment.academic_year.name],
        ]

        if cert_type == "bonafide":
            title = "CERTIFICATE OF ENROLMENT"

            body = (
                f"This is to certify that <b>{student.full_name}</b>, "
                f"{son_daughter} of {getattr(student.guardian, 'name', '-')}, "
                f"bearing Admission No. <b>{student.admission_number}</b>, is a "
                f"bonafide and actively enrolled student of "
                f"<b>{school_name}</b>, {campus.name}. The student is currently "
                f"studying in <b>{enrollment.class_obj.name}</b>"
                + (
                    f" (Section {enrollment.section.name})"
                    if enrollment.section_id
                    else ""
                )
                + f" for the academic year {enrollment.academic_year.name}. "
                "This certificate is issued on the request of the guardian "
                "for official purposes."
            )
        elif cert_type == "character":
            title = "CHARACTER CERTIFICATE"

            body = (
                f"This is to certify that <b>{student.full_name}</b>, "
                f"{son_daughter} of {getattr(student.guardian, 'name', '-')}, "
                f"Admission No. <b>{student.admission_number}</b>, studied at "
                f"<b>{school_name}</b>, {campus.name}, in "
                f"<b>{enrollment.class_obj.name}</b> during the academic year "
                f"{enrollment.academic_year.name}. During the period of study "
                "the student's general conduct and behaviour remained "
                "<b>satisfactory</b>. We wish the student every success in "
                "future endeavours."
            )

            if remarks:
                body = body.replace(
                    "remained <b>satisfactory</b>",
                    f"remained <b>satisfactory</b>. {remarks}",
                )
        else:
            title = "TRANSFER CERTIFICATE"

            body = (
                f"This is to certify that <b>{student.full_name}</b>, "
                f"{son_daughter} of {getattr(student.guardian, 'name', '-')}, "
                f"Admission No. <b>{student.admission_number}</b>, studied at "
                f"<b>{school_name}</b>, {campus.name}. The student left the "
                "institution on the date shown below. All school dues have "
                "been cleared and the student may be admitted to another "
                "institution."
            )

        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=22 * mm,
            bottomMargin=20 * mm,
            leftMargin=24 * mm,
            rightMargin=24 * mm,
            title=title.title(),
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CertTitle",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=2,
        )
        school_style = ParagraphStyle(
            "SchoolName",
            parent=styles["Normal"],
            fontSize=14,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        tagline_style = ParagraphStyle(
            "Tagline",
            parent=styles["Normal"],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=10,
        )
        heading_style = ParagraphStyle(
            "CertHeading",
            parent=styles["Title"],
            fontSize=13,
            spaceBefore=8,
            spaceAfter=12,
        )
        body_style = ParagraphStyle(
            "CertBody",
            parent=styles["Normal"],
            fontSize=11,
            leading=18,
            alignment=TA_JUSTIFY,
            spaceAfter=16,
        )

        table = Table(details, colWidths=[45 * mm, 105 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )

        story = [
            Paragraph(school_name.upper(), school_style),
            Paragraph(campus.name, tagline_style),
            Paragraph(title, heading_style),
            Spacer(1, 6 * mm),
            Paragraph(body, body_style),
            table,
            Spacer(1, 18 * mm),
        ]

        signature = Table(
            [
                [
                    Paragraph(
                        f"Issued on: <b>{issue_date.strftime('%d %B %Y')}</b>",
                        ParagraphStyle(
                            "IssuedOn",
                            parent=styles["Normal"],
                            fontSize=10,
                            alignment=TA_LEFT,
                        ),
                    ),
                    Paragraph(
                        "______________________<br/>Principal",
                        ParagraphStyle(
                            "Signature",
                            parent=styles["Normal"],
                            fontSize=10,
                            alignment=TA_RIGHT,
                        ),
                    ),
                ]
            ],
            colWidths=[75 * mm, 75 * mm],
        )

        story.append(signature)

        document.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{cert_type}_certificate_'
            f'{student.admission_number}.pdf"'
        )

        return response
