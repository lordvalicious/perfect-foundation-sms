from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAccountantRole

from .models import PayrollRecord, Payslip, SalaryStructure
from .serializers import (
    PayrollRecordSerializer,
    PayslipSerializer,
    SalaryStructureSerializer,
)


class SalaryStructureListView(generics.ListCreateAPIView):
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = SalaryStructure.objects.select_related("teacher")

        teacher = self.request.query_params.get("teacher")

        if teacher:
            queryset = queryset.filter(teacher_id=teacher)

        return queryset


class SalaryStructureDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAccountantRole]
    queryset = SalaryStructure.objects.all()


class PayrollRecordListView(generics.ListCreateAPIView):
    serializer_class = PayrollRecordSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = PayrollRecord.objects.select_related(
            "teacher",
            "structure",
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
    queryset = PayrollRecord.objects.all()


class PayrollProcessView(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request, pk):
        record = PayrollRecord.objects.filter(pk=pk).first()

        if record is None:
            return Response(
                {"detail": "Payroll record not found."},
                status=status.HTTP_404_NOT_FOUND,
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
        queryset = Payslip.objects.select_related(
            "record__teacher",
        )

        teacher = self.request.query_params.get("teacher")

        if teacher:
            queryset = queryset.filter(record__teacher_id=teacher)

        return queryset
