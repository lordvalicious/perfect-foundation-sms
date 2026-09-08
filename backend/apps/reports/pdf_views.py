"""PDF Export and Print System for Reports."""

import io
from decimal import Decimal
from django.http import HttpResponse, FileResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsAccountantRole
from apps.reports.models import ReportTemplate, SavedReport, ReportDefinition
from apps.reports.utils import normalize_report_payload, quantize


class PDFExportMixin:
    """Mixin to add PDF export capabilities."""

    def get_pdf_context(self, report_data, template_config, request):
        """Build context for PDF template rendering."""
        user = request.user
        institution = getattr(request, "institution", None)

        school_name = "Perfect Foundation School"
        school_address = ""
        school_phone = ""
        school_email = ""
        school_logo = None

        if institution:
            school_name = institution.name
            school_address = institution.address or ""

            school_settings = None
            try:
                school_settings = institution.settings
            except Exception:
                school_settings = None

            if school_settings is not None:
                school_phone = school_settings.contact_phone or ""
                school_email = school_settings.contact_email or ""
                if school_settings.logo:
                    school_logo = school_settings.logo.url

        campus = None
        if hasattr(self, "campus") and self.campus:
            campus = self.campus
        elif report_data.get("campus"):
            campus = report_data.get("campus")

        return {
            "report_data": report_data,
            "template_config": template_config,
            "school": {
                "name": school_name,
                "address": school_address,
                "phone": school_phone,
                "email": school_email,
                "logo": school_logo,
            },
            "campus": campus,
            "generated_by": user.get_full_name() or user.username,
            "generated_at": timezone.now(),
            "page_config": template_config.get("page_config", {
                "size": "A4",
                "orientation": "portrait",
                "margins": {"top": 20, "bottom": 20, "left": 15, "right": 15},
            }),
            "styling": template_config.get("styling", {
                "font_family": "Helvetica",
                "font_size": 10,
                "header_color": "#1a73e8",
                "alternate_row_color": "#f5f5f5",
            }),
            "header_config": template_config.get("header_config", {}),
            "footer_config": template_config.get("footer_config", {}),
            "watermark": template_config.get("watermark", ""),
        }

    def render_pdf_with_reportlab(self, context):
        """Render PDF using ReportLab."""
        try:
            from reportlab.lib.pagesizes import A4, letter, landscape, portrait
            from reportlab.lib.units import mm, cm, inch
            from reportlab.lib.colors import HexColor, white, black
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
            from reportlab.platypus import (
                SimpleDocTemplate, Table, TableStyle, Paragraph,
                Spacer, PageBreak, KeepTogether, Image, Frame, PageTemplate
            )
            from reportlab.platypus.flowables import HRFlowable
        except ImportError:
            return None, "reportlab not installed"

        # Page setup
        page_config = context.get("page_config", {})
        page_size_str = page_config.get("size", "A4")
        orientation = page_config.get("orientation", "portrait")
        margins = page_config.get("margins", {"top": 20, "bottom": 20, "left": 15, "right": 15})

        if page_size_str == "A4":
            pagesize = A4
        elif page_size_str == "Letter":
            pagesize = letter
        else:
            pagesize = A4

        if orientation == "landscape":
            pagesize = landscape(pagesize)
        else:
            pagesize = portrait(pagesize)

        # Create buffer
        buffer = io.BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            leftMargin=margins.get("left", 15) * mm,
            rightMargin=margins.get("right", 15) * mm,
            topMargin=margins.get("top", 20) * mm,
            bottomMargin=margins.get("bottom", 20) * mm,
        )

        # Styles
        styles = getSampleStyleSheet()
        styling = context.get("styling", {})

        header_color = HexColor(styling.get("header_color", "#1a73e8"))
        font_name = styling.get("font_family", "Helvetica")
        font_size = styling.get("font_size", 10)
        alt_row_color = HexColor(styling.get("alternate_row_color", "#f5f5f5"))

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=16,
            textColor=header_color,
            spaceAfter=6,
            alignment=TA_CENTER,
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            textColor=black,
            spaceAfter=4,
            alignment=TA_CENTER,
        )

        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=font_size,
            textColor=white,
            alignment=TA_CENTER,
        )

        cell_style = ParagraphStyle(
            'CustomCell',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=font_size - 1,
            textColor=black,
            alignment=TA_LEFT,
            leading=font_size + 2,
        )

        # Build story
        story = []

        # Header
        header_config = context.get("header_config", {})
        school = context.get("school", {})
        campus = context.get("campus")

        if school.get("logo"):
            try:
                img = Image(school["logo"], width=60, height=60)
                img.hAlign = 'CENTER'
                story.append(img)
            except:
                pass

        story.append(Paragraph(school.get("name", "School Name"), title_style))

        if school.get("address"):
            story.append(Paragraph(school["address"], subtitle_style))

        contact_parts = []
        if school.get("phone"):
            contact_parts.append(f"Phone: {school['phone']}")
        if school.get("email"):
            contact_parts.append(f"Email: {school['email']}")
        if contact_parts:
            story.append(Paragraph(" | ".join(contact_parts), subtitle_style))

        if campus:
            story.append(Paragraph(f"Campus: {campus.name if hasattr(campus, 'name') else campus}", subtitle_style))

        report_title = header_config.get("title", "Report")
        story.append(Paragraph(report_title, title_style))

        # Filter summary
        filters_applied = context.get("report_data", {}).get("filters_applied", {})
        if filters_applied:
            filter_text = "Filters: " + ", ".join([f"{k}: {v}" for k, v in filters_applied.items()])
            story.append(Paragraph(filter_text, ParagraphStyle(
                'FilterStyle', parent=styles['Normal'], fontName=font_name, fontSize=8, textColor=black, alignment=TA_CENTER
            )))

        story.append(Spacer(1, 10))

        # Summary cards
        summary = context.get("report_data", {}).get("summary", [])
        if summary:
            summary_data = []
            for item in summary:
                summary_data.append([Paragraph(str(item.get("label", "")), cell_style),
                                   Paragraph(str(item.get("value", "")), cell_style)])

            if summary_data:
                summary_table = Table(summary_data, colWidths=[doc.width * 0.4, doc.width * 0.6])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor("#f0f0f0")),
                    ('TEXTCOLOR', (0, 0), (-1, -1), black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), font_size - 1),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#ddd")),
                ]))
                story.append(summary_table)
                story.append(Spacer(1, 10))

        # Main table
        report_data = context.get("report_data", {})
        headers = report_data.get("headers", [])
        rows = report_data.get("rows", [])

        if headers and rows:
            # Prepare table data
            table_data = [headers]

            for row in rows:
                table_row = []
                for cell in row:
                    if isinstance(cell, (int, float, Decimal)):
                        table_row.append(Paragraph(str(cell), cell_style))
                    else:
                        table_row.append(Paragraph(str(cell), cell_style))
                table_data.append(table_row)

            # Calculate column widths
            available_width = doc.width
            col_width = available_width / len(headers) if headers else available_width

            table = Table(table_data, colWidths=[col_width] * len(headers), repeatRows=1)

            # Table style
            style_commands = [
                ('BACKGROUND', (0, 0), (-1, 0), header_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), font_size),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 1), (-1, -1), font_size - 1),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('TEXTCOLOR', (0, 1), (-1, -1), black),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#ddd")),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ('TOPPADDING', (0, 1), (-1, -1), 5),
            ]

            # Alternate row colors
            for i in range(1, len(table_data)):
                if i % 2 == 0:
                    style_commands.append(('BACKGROUND', (0, i), (-1, i), alt_row_color))

            table.setStyle(TableStyle(style_commands))
            story.append(table)

        # Footer
        story.append(Spacer(1, 20))
        footer_config = context.get("footer_config", {})
        generated_by = context.get("generated_by", "System")
        generated_at = context.get("generated_at", timezone.now())

        footer_text = footer_config.get("text", f"Generated by {generated_by} on {generated_at.strftime('%Y-%m-%d %H:%M')}")
        story.append(Paragraph(footer_text, ParagraphStyle(
            'FooterStyle', parent=styles['Normal'], fontName=font_name, fontSize=8, textColor=black, alignment=TA_CENTER
        )))

        # Page numbers
        def add_page_number(canvas, doc):
            page_num = canvas.getPageNumber()
            text = f"Page {page_num}"
            canvas.saveState()
            canvas.setFont(font_name, 8)
            canvas.drawCentredString(pagesize[0] / 2, 15 * mm, text)
            canvas.restoreState()

        # Build PDF
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

        buffer.seek(0)
        return buffer.getvalue(), None

    def export_pdf(self, request, report_key, report_data=None):
        """Export report as PDF."""
        # Get template
        template = None
        template_id = request.query_params.get("template_id")
        if template_id:
            try:
                template = ReportTemplate.objects.get(pk=template_id)
            except ReportTemplate.DoesNotExist:
                pass

        if not template:
            template = ReportTemplate.objects.filter(report_type="default", is_default=True).first()

        template_config = {}
        if template:
            template_config = {
                "header_config": template.header_config,
                "footer_config": template.footer_config,
                "page_config": template.page_config,
                "styling": template.styling,
                "watermark": template.watermark,
            }

        if not report_data:
            # Try to get report data from the report view
            # This would need to be called from the actual report view
            report_data = {"headers": [], "rows": [], "summary": []}

        context = self.get_pdf_context(report_data, template_config, request)
        pdf_bytes, error = self.render_pdf_with_reportlab(context)

        if error:
            return Response({"detail": error}, status=500)

        filename = request.query_params.get("filename", f"report_{report_key}_{timezone.now().strftime('%Y%m%d')}.pdf")
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class PDFExportView(APIView):
    """Export any report as PDF."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def get(self, request, report_key):
        """Export a report as PDF."""
        # Get report definition
        try:
            report_def = ReportDefinition.objects.get(key=report_key, is_active=True)
        except ReportDefinition.DoesNotExist:
            return Response({"detail": "Report not found"}, status=404)

        # Check if report supports PDF
        if not report_def.supports_pdf:
            return Response({"detail": "This report does not support PDF export"}, status=400)

        # Get report data by calling the report endpoint
        from django.test import RequestFactory
        from rest_framework.request import Request as DRFRequest
        factory = RequestFactory()
        raw_request = factory.get(report_def.endpoint_url, request.GET.dict())
        raw_request.user = request.user
        raw_request.institution = getattr(request, "institution", None)
        raw_request.institution_membership = getattr(request, "institution_membership", None)
        report_request = DRFRequest(raw_request)
        report_request._user = request.user

        # Import and call the view
        from django.urls import resolve
        try:
            match = resolve(report_def.endpoint_url)
            view_func = match.func
            view_class = view_func.cls if hasattr(view_func, 'cls') else None
        except:
            return Response({"detail": "Could not resolve report endpoint"}, status=500)

        if view_class:
            view = view_class()
            view.request = report_request
            view.format_kwarg = "json"
            response = view.get(report_request)
            report_data = normalize_report_payload(response.data)
        else:
            report_data = normalize_report_payload({})

        # Get template
        template = ReportTemplate.objects.filter(
            report_type=report_def.report_type, is_default=True
        ).first()

        template_config = {}
        if template:
            template_config = {
                "header_config": template.header_config,
                "footer_config": template.footer_config,
                "page_config": template.page_config,
                "styling": template.styling,
                "watermark": template.watermark,
            }

        # Generate PDF
        exporter = PDFExportMixin()
        context = exporter.get_pdf_context(report_data, template_config, request)
        pdf_bytes, error = exporter.render_pdf_with_reportlab(context)

        if error:
            return Response({"detail": error}, status=500)

        filename = f"{report_key}_{timezone.now().strftime('%Y%m%d')}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class PrintView(APIView):
    """Generate print-friendly HTML for reports."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def get(self, request, report_key):
        """Return print-friendly HTML."""
        try:
            report_def = ReportDefinition.objects.get(key=report_key, is_active=True)
        except ReportDefinition.DoesNotExist:
            return Response({"detail": "Report not found"}, status=404)

        if not report_def.supports_print:
            return Response({"detail": "This report does not support printing"}, status=400)

        # Get report data
        from django.test import RequestFactory
        from rest_framework.request import Request as DRFRequest
        factory = RequestFactory()
        raw_request = factory.get(report_def.endpoint_url, request.GET.dict())
        raw_request.user = request.user
        raw_request.institution = getattr(request, "institution", None)
        report_request = DRFRequest(raw_request)
        report_request._user = request.user

        from django.urls import resolve
        try:
            match = resolve(report_def.endpoint_url)
            view_func = match.func
            view_class = view_func.cls if hasattr(view_func, 'cls') else None
        except:
            return Response({"detail": "Could not resolve report endpoint"}, status=500)

        if view_class:
            view = view_class()
            view.request = report_request
            response = view.get(report_request)
            report_data = normalize_report_payload(response.data)
        else:
            report_data = normalize_report_payload({})

        # Get template
        template = ReportTemplate.objects.filter(
            report_type=report_def.report_type, is_default=True
        ).first()

        template_config = {}
        if template:
            template_config = {
                "header_config": template.header_config,
                "footer_config": template.footer_config,
                "page_config": template.page_config,
                "styling": template.styling,
            }

        # Build context
        user = request.user
        institution = getattr(request, "institution", None)

        school_logo = None
        if institution:
            try:
                school_logo = institution.settings.logo.url if institution.settings.logo else None
            except Exception:
                school_logo = None

        context = {
            "report_data": report_data,
            "template_config": template_config,
            "report_definition": report_def,
            "school": {
                "name": institution.name if institution else "Perfect Foundation School",
                "address": institution.address if institution else "",
                "logo": school_logo,
            },
            "generated_by": user.get_full_name() or user.username,
            "generated_at": timezone.now(),
            "request": request,
        }

        html = render_to_string("reports/print.html", context, request=request)
        return HttpResponse(html)


class BulkPDFExportView(APIView):
    """Bulk export multiple reports as a single PDF."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def post(self, request):
        report_keys = request.data.get("reports", [])
        if not report_keys:
            return Response({"detail": "No reports specified"}, status=400)

        # This would merge multiple reports into one PDF
        # For now, return a ZIP file with individual PDFs
        return Response({"detail": "Bulk PDF export not yet implemented"}, status=501)


class ReportTemplatePreviewView(APIView):
    """Preview a report template with sample data."""

    permission_classes = [IsAuthenticated, IsAccountantRole]

    def get(self, request, pk):
        try:
            template = ReportTemplate.objects.get(pk=pk)
        except ReportTemplate.DoesNotExist:
            return Response({"detail": "Template not found"}, status=404)

        # Generate sample data
        sample_data = self.generate_sample_data(template.report_type)

        exporter = PDFExportMixin()
        context = exporter.get_pdf_context(sample_data, {
            "header_config": template.header_config,
            "footer_config": template.footer_config,
            "page_config": template.page_config,
            "styling": template.styling,
            "watermark": template.watermark,
        }, request)

        pdf_bytes, error = exporter.render_pdf_with_reportlab(context)

        if error:
            return Response({"detail": error}, status=500)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="template_preview_{pk}.pdf"'
        return response

    def generate_sample_data(self, report_type):
        """Generate sample data for template preview."""
        return {
            "summary": [
                {"label": "Total Records", "value": "150"},
                {"label": "Total Amount", "value": "1,250,000"},
                {"label": "Average", "value": "8,333"},
            ],
            "headers": ["Column 1", "Column 2", "Column 3", "Column 4", "Column 5"],
            "rows": [
                ["Sample Data 1", "Value A", "100", "Active", "2024-01-15"],
                ["Sample Data 2", "Value B", "200", "Pending", "2024-01-16"],
                ["Sample Data 3", "Value C", "150", "Active", "2024-01-17"],
                ["Sample Data 4", "Value D", "300", "Completed", "2024-01-18"],
                ["Sample Data 5", "Value E", "250", "Active", "2024-01-19"],
            ],
            "filters_applied": {"Date Range": "Jan 2024", "Status": "All"},
        }


