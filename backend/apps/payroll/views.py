from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.teachers.models import Teacher

from .models import PayrollRecord, Payslip, SalaryStructure
from .serializers import (
    PayrollRecordSerializer,
    PayslipSerializer,
    SalaryStructureSerializer,
)


def payroll_queryset(model, request, teacher_path="teacher"):
    queryset = model.objects.filter(
        **{
            f"{teacher_path}__membership__institution": request.institution,
        },
    )


def teacher_queryset(request):
    return apply_campus_scope(
        Teacher.objects.filter(
            membership__institution=request.institution,
        ),
        request,
        "primary_campus_id",
    )
    return apply_campus_scope(
        queryset,
        request,
        f"{teacher_path}__primary_campus_id",
    )


class SalaryStructureListView(generics.ListCreateAPIView):
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAccountantRole]

    def perform_create(self, serializer):
        teacher = serializer.validated_data["teacher"]
        if not teacher_queryset(self.request).filter(pk=teacher.pk).exists():
            raise PermissionDenied("The teacher is outside your campus scope.")
        serializer.save()

    def get_queryset(self):
        queryset = payroll_queryset(
            SalaryStructure.objects.select_related("teacher"),
            self.request,
        )

        teacher = self.request.query_params.get("teacher")

        if teacher:
            queryset = queryset.filter(teacher_id=teacher)

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
        teacher = serializer.validated_data["teacher"]
        structure = serializer.validated_data["structure"]
        if not teacher_queryset(self.request).filter(pk=teacher.pk).exists():
            raise PermissionDenied("The teacher is outside your campus scope.")
        if not payroll_queryset(
            SalaryStructure.objects.all(),
            self.request,
        ).filter(pk=structure.pk, teacher_id=teacher.pk).exists():
            raise PermissionDenied("The salary structure is outside your campus scope.")
        serializer.save()

    def get_queryset(self):
        queryset = payroll_queryset(
            PayrollRecord.objects.select_related(
                "teacher",
                "structure",
            ),
            self.request,
        )

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")
        teacher = self.request.query_params.get("teacher")

        if month:
            queryset = queryset.filter(month=month)

        if year:
            queryset = queryset.filter(year=year)

        if teacher:
            queryset = queryset.filter(teacher_id=teacher)

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

        record.status = "paid"
        record.processed_at = timezone.now()
        record.processed_by = request.user
        record.save()

        Payslip.objects.get_or_create(record=record)

        return Response(PayrollRecordSerializer(record).data)


class PayslipListView(generics.ListAPIView):
    serializer_class = PayslipSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = payroll_queryset(
            Payslip.objects.select_related(
                "record__teacher",
            ),
            self.request,
            teacher_path="record__teacher",
        )

        teacher = self.request.query_params.get("teacher")

        if teacher:
            queryset = queryset.filter(record__teacher_id=teacher)

        return queryset
