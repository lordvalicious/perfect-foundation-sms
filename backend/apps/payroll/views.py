from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.hr.models import Employee

from .models import PayrollRecord, Payslip, SalaryStructure
from .serializers import (
    PayrollRecordSerializer,
    PayslipSerializer,
    SalaryStructureSerializer,
)


def payroll_queryset(queryset, request, employee_path="employee"):
    """Scope a payroll-related queryset to the active institution and the user's campus access."""
    institution = getattr(request, "institution", None)

    if institution is None:
        from apps.accounts.access import get_institution
        institution = get_institution(request)

    if institution is not None:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(**{f"{employee_path}__institution": institution})
            | Q(**{f"{employee_path}__primary_campus__school": institution})
        )

    return apply_campus_scope(
        queryset,
        request,
        f"{employee_path}__primary_campus_id",
        institution_field=None,
    )


def employee_queryset(request):
    return apply_campus_scope(
        Employee.objects.filter(
            institution=request.institution,
        ),
        request,
        "primary_campus_id",
    )


class SalaryStructureListView(generics.ListCreateAPIView):
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAccountantRole]

    def perform_create(self, serializer):
        employee = serializer.validated_data["employee"]
        if not employee_queryset(self.request).filter(pk=employee.pk).exists():
            raise PermissionDenied("The employee is outside your campus scope.")
        serializer.save()

    def get_queryset(self):
        queryset = payroll_queryset(
            SalaryStructure.objects.select_related("employee"),
            self.request,
        )

        employee = self.request.query_params.get("employee")

        if employee:
            queryset = queryset.filter(employee_id=employee)

        return queryset


class SalaryStructureDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        return payroll_queryset(SalaryStructure.objects.all(), self.request)


class PayrollRecordListView(generics.ListCreateAPIView):
    serializer_class = PayrollRecordSerializer
    permission_classes = [IsAccountantRole]

    def perform_create(self, serializer):
        employee = serializer.validated_data["employee"]
        structure = serializer.validated_data["salary_structure"]
        if not employee_queryset(self.request).filter(pk=employee.pk).exists():
            raise PermissionDenied("The employee is outside your campus scope.")
        if not payroll_queryset(
            SalaryStructure.objects.all(),
            self.request,
        ).filter(pk=structure.pk, employee_id=employee.pk).exists():
            raise PermissionDenied("The salary structure is outside your campus scope.")
        serializer.save()

    def get_queryset(self):
        queryset = payroll_queryset(
            PayrollRecord.objects.select_related(
                "employee",
                "salary_structure",
                "payroll_period",
            ),
            self.request,
        )

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")
        employee = self.request.query_params.get("employee")
        period = self.request.query_params.get("period")

        if month:
            queryset = queryset.filter(month=month)

        if year:
            queryset = queryset.filter(year=year)

        if employee:
            queryset = queryset.filter(employee_id=employee)

        if period:
            queryset = queryset.filter(payroll_period_id=period)

        return queryset


class PayrollRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PayrollRecordSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        return payroll_queryset(PayrollRecord.objects.all(), self.request)


class PayrollProcessView(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request, pk):
        record = get_object_or_404(
            payroll_queryset(PayrollRecord.objects.all(), request),
            pk=pk,
        )

        if record.status == "paid":
            return Response(
                {"detail": "This payroll record has already been paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record.compute()
        record.status = "processed"
        record.processed_at = timezone.now()
        record.processed_by = request.user
        record.save()

        Payslip.objects.get_or_create(record=record)

        return Response(PayrollRecordSerializer(record).data)


class PayrollApproveView(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request, pk):
        record = get_object_or_404(
            payroll_queryset(PayrollRecord.objects.all(), request),
            pk=pk,
        )

        if record.status != "processed":
            return Response(
                {"detail": "Payroll must be processed before approval."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record.status = "approved"
        record.approved_at = timezone.now()
        record.approved_by = request.user
        record.save(update_fields=["status", "approved_at", "approved_by"])

        return Response(PayrollRecordSerializer(record).data)


class PayrollPayView(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request, pk):
        record = get_object_or_404(
            payroll_queryset(PayrollRecord.objects.all(), request),
            pk=pk,
        )

        if record.status != "approved":
            return Response(
                {"detail": "Payroll must be approved before payment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record.status = "paid"
        record.paid_at = timezone.now()
        record.paid_by = request.user
        record.save(update_fields=["status", "paid_at", "paid_by"])

        return Response(PayrollRecordSerializer(record).data)


class PayslipListView(generics.ListAPIView):
    serializer_class = PayslipSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = payroll_queryset(
            Payslip.objects.select_related(
                "record__employee",
            ),
            self.request,
            teacher_path="record__employee",
        )

        employee = self.request.query_params.get("employee")

        if employee:
            queryset = queryset.filter(record__employee_id=employee)

        return queryset


class PayslipGenerateView(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request, pk):
        record = get_object_or_404(
            payroll_queryset(PayrollRecord.objects.all(), request),
            pk=pk,
        )

        if record.status != "paid":
            return Response(
                {"detail": "Payslip can only be generated for paid payroll records."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate PDF payslip
        from .pdf_views import PayrollPayslipPdfView
        pdf_view = PayrollPayslipPdfView()
        pdf_view.request = request
        return pdf_view.get(request, pk=record.pk)