"""Certificate Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class BonafideCertificateView(BaseReportView):
    """Bonafide certificate generation."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "certificate_bonafide"
    model = "apps.students.models.Student"

    def get_base_queryset(self, request):
        from apps.students.models import Student
        return Student.objects.select_related(
            "primary_campus", "guardian"
        ).prefetch_related("enrollments__class_obj", "enrollments__section", "enrollments__campus", "enrollments__academic_year")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")

        student_id = request.query_params.get("student")
        if student_id:
            queryset = queryset.filter(id=student_id)

        return queryset

    def get(self, request):
        queryset = self.get_queryset(request)

        # Check if bulk generation requested
        bulk = request.query_params.get("bulk") == "true"
        student_id = request.query_params.get("student")

        if bulk or student_id:
            students = list(queryset)
            certificates = []
            for student in students:
                certificates.append(self.build_bonafide_certificate(student))

            return Response({
                "count": len(certificates),
                "certificates": certificates,
            })

        return Response({"detail": "Student ID required"}, status=400)

    def build_bonafide_certificate(self, student):
        enrollment = student.enrollments.filter(status="active").first()

        school = enrollment.campus.school if enrollment and enrollment.campus else None
        campus = enrollment.campus if enrollment else student.primary_campus

        return {
            "certificate_type": "Bonafide Certificate",
            "certificate_number": f"BON-{student.admission_number}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            "issue_date": timezone.now().date(),
            "school": {
                "name": school.name if school else "Perfect Foundation School",
                "address": school.address if school else "",
                "phone": school.settings.contact_phone if school and school.settings else "",
            },
            "campus": {
                "name": campus.name if campus else "Main Campus",
                "address": campus.address if campus else "",
            },
            "student": {
                "admission_number": student.admission_number,
                "full_name": student.full_name,
                "gender": student.gender,
                "date_of_birth": student.date_of_birth,
                "class": enrollment.class_obj.name if enrollment else "-",
                "section": enrollment.section.name if enrollment and enrollment.section else "-",
                "academic_year": enrollment.academic_year.name if enrollment else "-",
                "admission_date": student.admission_date,
            },
            "guardian": {
                "name": student.guardian.name if student.guardian else "-",
                "relationship": student.guardian.relationship if student.guardian else "-",
            },
            "purpose": "This is to certify that the above student is a bonafide student of this institution.",
            "signature": {
                "principal": "Principal",
                "date": timezone.now().date(),
            },
        }


class CharacterCertificateView(BonafideCertificateView):
    """Character certificate generation."""
    report_definition_key = "certificate_character"

    def build_bonafide_certificate(self, student):
        cert = super().build_bonafide_certificate(student)
        cert["certificate_type"] = "Character Certificate"
        cert["certificate_number"] = f"CHR-{student.admission_number}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        cert["purpose"] = "This is to certify that the above student has maintained good character and conduct during their tenure at this institution."
        return cert


class LeavingCertificateView(BonafideCertificateView):
    """Leaving certificate generation."""
    report_definition_key = "certificate_leaving"

    def build_bonafide_certificate(self, student):
        cert = super().build_bonafide_certificate(student)
        cert["certificate_type"] = "Leaving Certificate"
        cert["certificate_number"] = f"LEV-{student.admission_number}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        cert["purpose"] = "This is to certify that the above student has left this institution on their own accord."
        
        # Add leaving details
        from apps.students.models import StudentLifecycleEvent
        leaving_event = StudentLifecycleEvent.objects.filter(
            student=student, event_type="withdrawn"
        ).first()
        
        if leaving_event:
            cert["leaving_date"] = leaving_event.effective_date
            cert["leaving_reason"] = leaving_event.reason
        
        return cert


class TransferCertificateView(BonafideCertificateView):
    """Transfer certificate generation."""
    report_definition_key = "certificate_transfer"

    def build_bonafide_certificate(self, student):
        cert = super().build_bonafide_certificate(student)
        cert["certificate_type"] = "Transfer Certificate"
        cert["certificate_number"] = f"TRF-{student.admission_number}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        cert["purpose"] = "This is to certify that the above student is transferring to another institution."
        
        from apps.students.models import StudentLifecycleEvent
        transfer_event = StudentLifecycleEvent.objects.filter(
            student=student, event_type="transferred"
        ).first()
        
        if transfer_event:
            cert["transfer_date"] = transfer_event.effective_date
            cert["to_campus"] = transfer_event.to_campus.name if transfer_event.to_campus else "-"
            cert["to_enrollment_class"] = transfer_event.to_enrollment.class_obj.name if transfer_event.to_enrollment else "-"
        
        return cert


class EnrollmentCertificateView(BonafideCertificateView):
    """Enrollment certificate generation."""
    report_definition_key = "certificate_enrollment"

    def build_bonafide_certificate(self, student):
        cert = super().build_bonafide_certificate(student)
        cert["certificate_type"] = "Enrollment Certificate"
        cert["certificate_number"] = f"ENR-{student.admission_number}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        cert["purpose"] = "This is to certify that the above student is currently enrolled in this institution."
        return cert


class FeeClearanceCertificateView(BonafideCertificateView):
    """Fee clearance certificate generation."""
    report_definition_key = "certificate_fee_clearance"

    def build_bonafide_certificate(self, student):
        cert = super().build_bonafide_certificate(student)
        cert["certificate_type"] = "Fee Clearance Certificate"
        cert["certificate_number"] = f"FEE-{student.admission_number}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        from apps.finance.models import Invoice
        invoices = Invoice.objects.filter(student=student, status__in=["issued", "partial", "overdue"])
        has_dues = any(inv.balance > 0 for inv in invoices)
        
        if has_dues:
            cert["purpose"] = "This is to certify that the above student has outstanding fees."
            cert["status"] = "NOT CLEARED"
        else:
            cert["purpose"] = "This is to certify that the above student has cleared all fees."
            cert["status"] = "CLEARED"
        
        return cert


class StudentIDCardView(BonafideCertificateView):
    """Student ID card generation."""
    report_definition_key = "certificate_student_id"

    def build_bonafide_certificate(self, student):
        cert = super().build_bonafide_certificate(student)
        cert["certificate_type"] = "Student ID Card"
        cert["certificate_number"] = f"ID-{student.admission_number}"
        cert["purpose"] = "Student Identification Card"
        cert["valid_upto"] = f"{timezone.now().year + 1}-03-31"
        
        # Add barcode/QR code data
        cert["barcode_data"] = student.admission_number
        
        return cert


class StaffIDCardView(BaseReportView):
    """Staff ID card generation."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "certificate_staff_id"
    model = "apps.accounts.models.StaffProfile"

    def get_base_queryset(self, request):
        from apps.accounts.models import StaffProfile
        return StaffProfile.objects.select_related("user", "primary_campus", "institution")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "primary_campus_id")

        staff_id = request.query_params.get("staff")
        if staff_id:
            queryset = queryset.filter(id=staff_id)

        return queryset

    def get(self, request):
        queryset = self.get_queryset(request)

        bulk = request.query_params.get("bulk") == "true"
        staff_id = request.query_params.get("staff")

        if bulk or staff_id:
            staff_list = list(queryset)
            certificates = []
            for staff in staff_list:
                certificates.append(self.build_staff_id_card(staff))

            return Response({
                "count": len(certificates),
                "certificates": certificates,
            })

        return Response({"detail": "Staff ID required"}, status=400)

    def build_staff_id_card(self, staff):
        school = staff.institution if staff.institution else None
        campus = staff.primary_campus

        return {
            "certificate_type": "Staff ID Card",
            "certificate_number": f"STF-{staff.employee_number}",
            "issue_date": timezone.now().date(),
            "valid_upto": f"{timezone.now().year + 1}-03-31",
            "school": {
                "name": school.name if school else "Perfect Foundation School",
                "address": school.address if school else "",
            },
            "campus": {
                "name": campus.name if campus else "Main Campus",
            },
            "staff": {
                "employee_number": staff.employee_number,
                "full_name": staff.full_name,
                "designation": staff.designation,
                "department": staff.department,
                "photo": staff.photo.url if staff.photo else None,
            },
            "barcode_data": staff.employee_number,
        }


class CertificateTemplateListView(AggregateReportView):
    """List available certificate templates."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "certificate_templates"
    model = "apps.reports.models.ReportTemplate"

    def get_base_queryset(self, request):
        from apps.reports.models import ReportTemplate
        return ReportTemplate.objects.filter(
            report_type="certificate"
        ).order_by("-is_default", "name")

    def get_queryset(self, request):
        return super().get_queryset(request)

    def get_summary(self, queryset, request):
        return {"total_templates": queryset.count()}

    def get_detail_rows(self, queryset, request):
        rows = []
        for template in queryset:
            rows.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "report_type": template.report_type,
                "is_default": template.is_default,
                "is_system": template.is_system,
            })
        return rows


class CertificateReportView(AggregateReportView):
    """General certificate report listing."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "certificate_report"
    model = "apps.reports.models.ReportTemplate"

    CERTIFICATE_TYPES = [
        ("bonafide", "Bonafide Certificate"),
        ("character", "Character Certificate"),
        ("leaving", "Leaving Certificate"),
        ("transfer", "Transfer Certificate"),
        ("enrollment", "Enrollment Certificate"),
        ("fee_clearance", "Fee Clearance Certificate"),
        ("student_id", "Student ID Card"),
        ("staff_id", "Staff ID Card"),
    ]

    def get_base_queryset(self, request):
        return None

    def get_queryset(self, request):
        return None

    def get_summary(self, queryset, request):
        return {"certificate_types": len(self.CERTIFICATE_TYPES)}

    def get_detail_rows(self, queryset, request):
        return [{"key": k, "name": v} for k, v in self.CERTIFICATE_TYPES]