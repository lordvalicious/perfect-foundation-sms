from django.db.models import Q
from rest_framework import generics

from apps.accounts.permissions import IsAccountantRole

from .models import FeeCategory, Invoice, Payment
from .serializers import (
    FeeCategorySerializer,
    InvoiceSerializer,
    PaymentSerializer,
)


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = (
            Invoice.objects
            .select_related(
                "student",
                "enrollment__campus",
                "enrollment__class_obj",
                "academic_year",
            )
            .prefetch_related("items__category")
            .order_by("-issue_date", "-id")
        )

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search)
                | Q(student__first_name__icontains=search)
                | Q(student__middle_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(student__admission_number__icontains=search)
            )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = (
            Payment.objects
            .select_related(
                "invoice",
                "invoice__student",
            )
            .order_by("-payment_date", "-id")
        )

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(receipt_number__icontains=search)
                | Q(invoice__invoice_number__icontains=search)
                | Q(invoice__student__first_name__icontains=search)
                | Q(invoice__student__last_name__icontains=search)
                | Q(invoice__student__admission_number__icontains=search)
            )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        payment_method = self.request.query_params.get("payment_method")

        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        return queryset


class FeeCategoryListView(generics.ListAPIView):
    serializer_class = FeeCategorySerializer
    permission_classes = [IsAccountantRole]
    pagination_class = None

    def get_queryset(self):
        queryset = FeeCategory.objects.all().order_by("name")

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset
