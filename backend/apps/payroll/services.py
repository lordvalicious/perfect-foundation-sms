"""Service layer for payroll processing."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any

from django.db import transaction
from django.db.models import Sum, Q

from apps.schools.models import School
from apps.teachers.models import Teacher
from apps.hr.models import Employee

from .models import SalaryStructure, PayrollRecord, Payslip


class PayrollService:
    """Service for payroll processing and management."""

    def __init__(self, institution: School):
        self.institution = institution

    def get_active_salary_structure(self, teacher: Teacher, on_date: Optional[date] = None) -> Optional[SalaryStructure]:
        """Get the active salary structure for a teacher on a given date."""
        if on_date is None:
            on_date = date.today()

        return SalaryStructure.objects.filter(
            teacher=teacher,
            effective_date__lte=on_date,
            status="active",
        ).order_by("-effective_date").first()

    @transaction.atomic
    def generate_payroll_for_month(
        self,
        month: int,
        year: int,
        teacher_ids: Optional[List[int]] = None,
        processed_by=None,
    ) -> List[PayrollRecord]:
        """Generate payroll records for all active teachers for a given month."""
        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12.")

        teachers = Teacher.objects.filter(
            institution=self.institution,
            status="active",
        ).select_related("salary_structures")

        if teacher_ids:
            teachers = teachers.filter(id__in=teacher_ids)

        records = []
        for teacher in teachers:
            structure = self.get_active_salary_structure(teacher, date(year, month, 1))
            if not structure:
                continue

            # Check if payroll already exists
            existing = PayrollRecord.objects.filter(
                teacher=teacher,
                month=month,
                year=year,
            ).first()

            if existing:
                continue

            # Get working days for the month (simplified - should use calendar)
            working_days = self._calculate_working_days(month, year)
            paid_days = working_days  # Simplified - should account for leaves

            record = PayrollRecord.objects.create(
                teacher=teacher,
                structure=structure,
                month=month,
                year=year,
                working_days=working_days,
                paid_days=paid_days,
                status="draft",
                processed_by=processed_by,
            )
            # compute() is called in save()
            records.append(record)

        return records

    def _calculate_working_days(self, month: int, year: int) -> int:
        """Calculate working days in a month (simplified - excludes weekends)."""
        import calendar
        cal = calendar.monthcalendar(year, month)
        working_days = 0
        for week in cal:
            for day in week[:5]:  # Mon-Fri
                if day != 0:
                    working_days += 1
        return working_days

    @transaction.atomic
    def process_payroll(self, payroll_record: PayrollRecord, processed_by) -> PayrollRecord:
        """Process a draft payroll record."""
        if payroll_record.status != "draft":
            raise ValueError("Only draft payroll records can be processed.")

        payroll_record.status = "processed"
        payroll_record.processed_at = date.today()
        payroll_record.processed_by = processed_by
        payroll_record.save(update_fields=["status", "processed_at", "processed_by", "updated_at"])

        return payroll_record

    @transaction.atomic
    def mark_paid(self, payroll_record: PayrollRecord) -> PayrollRecord:
        """Mark a processed payroll record as paid."""
        if payroll_record.status != "processed":
            raise ValueError("Only processed payroll records can be marked as paid.")

        payroll_record.status = "paid"
        payroll_record.save(update_fields=["status", "updated_at"])

        # Generate payslip
        self.generate_payslip(payroll_record)

        return payroll_record

    def generate_payslip(self, payroll_record: PayrollRecord) -> Payslip:
        """Generate a payslip PDF for a payroll record."""
        from .payslips_pdf import generate_payslip_pdf

        payslip, created = Payslip.objects.get_or_create(
            record=payroll_record,
        )

        if created or not payslip.document:
            pdf_content = generate_payslip_pdf(payroll_record)
            # Save PDF to document field (implementation depends on storage backend)
            # This is a placeholder - actual implementation would save to media/payslips/

        return payslip

    def calculate_deductions(
        self,
        teacher: Teacher,
        gross_salary: Decimal,
        month: int,
        year: int,
    ) -> Dict[str, Decimal]:
        """Calculate deductions for a teacher (tax, insurance, etc.)."""
        from .tax import calculate_tax

        deductions = {}

        # Income tax
        annual_gross = gross_salary * 12
        tax = calculate_tax(annual_gross)
        monthly_tax = (tax / 12).quantize(Decimal("0.01"))
        if monthly_tax > 0:
            deductions["income_tax"] = monthly_tax

        # Add other deductions as needed (EOBI, SESSI, etc.)
        # These would be configurable per institution

        return deductions

    def get_payroll_summary(
        self,
        month: int,
        year: int,
        campus_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get payroll summary for a month."""
        queryset = PayrollRecord.objects.filter(
            teacher__institution=self.institution,
            month=month,
            year=year,
        ).select_related("teacher")

        if campus_id:
            queryset = queryset.filter(teacher__primary_campus_id=campus_id)

        stats = queryset.aggregate(
            total_records=Count("id"),
            total_gross=Sum("gross_salary"),
            total_deductions=Sum("total_deductions"),
            total_net=Sum("net_salary"),
            by_status=Count("status"),
        )

        return {
            "month": month,
            "year": year,
            "total_records": stats["total_records"] or 0,
            "total_gross": stats["total_gross"] or Decimal("0.00"),
            "total_deductions": stats["total_deductions"] or Decimal("0.00"),
            "total_net": stats["total_net"] or Decimal("0.00"),
        }

    def get_teacher_payroll_history(self, teacher: Teacher) -> List[PayrollRecord]:
        """Get payroll history for a teacher."""
        return PayrollRecord.objects.filter(
            teacher=teacher,
        ).order_by("-year", "-month")

    def get_yearly_tax_certificate_data(self, teacher: Teacher, year: int) -> Dict[str, Any]:
        """Get data needed for yearly tax certificate."""
        records = PayrollRecord.objects.filter(
            teacher=teacher,
            year=year,
            status__in=["processed", "paid"],
        ).order_by("month")

        total_gross = sum(r.gross_salary for r in records)
        total_tax = sum(
            r.deductions.get("income_tax", Decimal("0")) for r in records
        )

        return {
            "teacher": teacher,
            "year": year,
            "months_paid": records.count(),
            "total_gross": total_gross,
            "total_tax_deducted": total_tax,
            "records": records,
        }


class SalaryStructureService:
    """Service for managing salary structures."""

    def __init__(self, institution: School):
        self.institution = institution

    def create_salary_structure(
        self,
        teacher: Teacher,
        basic_salary: Decimal,
        allowances: Dict[str, Decimal],
        effective_date: date,
    ) -> SalaryStructure:
        """Create a new salary structure for a teacher."""
        # Archive previous active structure
        SalaryStructure.objects.filter(
            teacher=teacher,
            status="active",
        ).update(status="archived")

        structure = SalaryStructure.objects.create(
            teacher=teacher,
            basic_salary=basic_salary,
            allowances={k: str(v) for k, v in allowances.items()},
            effective_date=effective_date,
            status="active",
        )

        return structure

    def update_allowances(self, structure: SalaryStructure, allowances: Dict[str, Decimal]) -> SalaryStructure:
        """Update allowances for a salary structure."""
        if structure.status != "active":
            raise ValueError("Can only update allowances for active structures.")

        structure.allowances = {k: str(v) for k, v in allowances.items()}
        structure.save(update_fields=["allowances", "updated_at"])

        # Update any draft payroll records using this structure
        PayrollRecord.objects.filter(
            structure=structure,
            status="draft",
        ).update(allowances=structure.allowances)

        return structure

    def get_salary_history(self, teacher: Teacher) -> List[SalaryStructure]:
        """Get all salary structures for a teacher."""
        return SalaryStructure.objects.filter(teacher=teacher).order_by("-effective_date")