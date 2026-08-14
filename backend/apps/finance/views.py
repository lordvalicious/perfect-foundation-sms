from django.db.models import Q
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    IsAccountantRole,
    IsFinanceReaderRole,
)
from apps.accounts.scopes import (
    get_student_profile,
    is_manager,
    is_parent,
    is_student,
    parent_student_ids,
)
from apps.audit.models import record_audit

from .models import FeeCategory, Invoice, Payment, PaymentReversal
from .pdf import payment_receipt_pdf
from .serializers import (
    FeeCategorySerializer,
    InvoiceCreateSerializer,
    InvoiceSerializer,
    PaymentCreateSerializer,
    PaymentReversalSerializer,
    PaymentSerializer,
)


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsFinanceReaderRole]

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

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)
            elif is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(student=profile)

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
    permission_classes = [IsFinanceReaderRole]

    def get_queryset(self):
        queryset = (
            Payment.objects
            .select_related(
                "invoice",
                "invoice__student",
            )
            .order_by("-payment_date", "-id")
        )

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(
                    invoice__student_id__in=student_ids
                )
            elif is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(invoice__student=profile)

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


class InvoiceDetailView(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsFinanceReaderRole]

    def get_queryset(self):
        queryset = Invoice.objects.select_related(
            "student",
            "enrollment__campus",
            "enrollment__class_obj",
            "enrollment__section",
            "academic_year",
        ).prefetch_related("items__category", "payments")

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(
                    student_id__in=student_ids
                )
            elif is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(student=profile)

        return queryset


class InvoiceCreateView(generics.CreateAPIView):
    serializer_class = InvoiceCreateSerializer
    permission_classes = [IsAccountantRole]

    def perform_create(self, serializer):
        invoice = serializer.save()

        record_audit(
            request=self.request,
            action="invoice",
            model_name="Invoice",
            object_id=str(invoice.pk),
            object_repr=str(invoice),
            details={
                "invoice_number": invoice.invoice_number,
                "total": str(invoice.total_amount),
            },
        )


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsFinanceReaderRole]

    def get_queryset(self):
        queryset = Payment.objects.select_related(
            "invoice",
            "invoice__student",
            "invoice__enrollment__class_obj",
            "invoice__enrollment__section",
            "invoice__academic_year",
        ).prefetch_related("invoice__items__category")

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(
                    invoice__student_id__in=student_ids
                )
            elif is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(invoice__student=profile)

        return queryset


class PaymentCreateView(generics.CreateAPIView):
    serializer_class = PaymentCreateSerializer
    permission_classes = [IsAccountantRole]

    def perform_create(self, serializer):
        payment = serializer.save()

        record_audit(
            request=self.request,
            action="payment",
            model_name="Payment",
            object_id=str(payment.pk),
            object_repr=str(payment),
            details={
                "receipt_number": payment.receipt_number,
                "invoice": payment.invoice.invoice_number,
                "amount": str(payment.amount),
            },
        )


class PaymentReversalCreateView(generics.CreateAPIView):
    serializer_class = PaymentReversalSerializer
    permission_classes = [IsAccountantRole]

    def perform_create(self, serializer):
        reversal = serializer.save(created_by=self.request.user)
        record_audit(request=self.request, action="payment_reversal", model_name="PaymentReversal", object_id=str(reversal.pk), object_repr=str(reversal.payment), details={"amount": str(reversal.amount), "payment": reversal.payment.receipt_number})


class PaymentReceiptHTMLView(APIView):
    """Printable HTML receipt for a single payment."""

    permission_classes = [IsFinanceReaderRole]

    def get_object(self):
        payment = (
            Payment.objects
            .filter(pk=self.kwargs["pk"])
            .select_related(
                "invoice",
                "invoice__student",
                "invoice__enrollment__class_obj",
                "invoice__enrollment__section",
                "invoice__academic_year",
            )
            .prefetch_related("invoice__items__category")
            .first()
        )

        if payment is None:
            return None

        user = self.request.user

        if not is_manager(user):
            if is_parent(user):
                student_ids = parent_student_ids(user)

                if payment.invoice.student_id not in student_ids:
                    raise PermissionDenied(
                        "You cannot view this receipt."
                    )
            elif is_student(user):
                profile = get_student_profile(user)

                if (
                    profile is None
                    or payment.invoice.student_id != profile.pk
                ):
                    raise PermissionDenied(
                        "You cannot view this receipt."
                    )

        return payment

    def get(self, request, pk):
        payment = self.get_object()

        if payment is None:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        invoice = payment.invoice
        items = "".join(
            f"""
            <tr>
              <td>{item.description}</td>
              <td class="right">Rs. {item.amount:,.2f}</td>
            </tr>
            """
            for item in invoice.items.all()
        )

        if invoice.discount:
            items += (
                f"""
                <tr>
                  <td>Discount</td>
                  <td class="right">- Rs. {invoice.discount:,.2f}</td>
                </tr>
                """
            )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Receipt {payment.receipt_number}</title>
<style>
  body {{ font-family: Arial, sans-serif; color: #111; margin: 24px; }}
  h1 {{ text-align: center; margin-bottom: 2px; }}
  h2 {{ text-align: center; font-size: 13px; color: #555; margin-top: 0; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
  td, th {{ padding: 6px 8px; border: 1px solid #ccc; font-size: 13px; }}
  th {{ background: #f2f4f7; text-align: left; }}
  .right {{ text-align: right; }}
  .meta td {{ border: none; padding: 2px 8px; }}
  .title-row td {{ font-weight: bold; }}
  @media print {{ body {{ margin: 0; }} }}
</style>
</head>
<body>
  <h1>Perfect Foundation School</h1>
  <h2>Official Payment Receipt</h2>

  <table class="meta">
    <tr>
      <td><strong>Receipt No.</strong> {payment.receipt_number}</td>
      <td class="right"><strong>Date</strong> {payment.payment_date}</td>
    </tr>
    <tr>
      <td><strong>Invoice No.</strong> {invoice.invoice_number}</td>
      <td class="right"><strong>Method</strong> {payment.get_payment_method_display()}</td>
    </tr>
    <tr>
      <td><strong>Student</strong> {invoice.student.full_name}</td>
      <td class="right"><strong>Admission No.</strong> {invoice.student.admission_number}</td>
    </tr>
    <tr>
      <td><strong>Class</strong> {invoice.enrollment.class_obj.name} - {invoice.enrollment.section.name}</td>
      <td class="right"><strong>Year</strong> {invoice.academic_year.name}</td>
    </tr>
  </table>

  <table>
    <tr><th>Description</th><th class="right">Amount</th></tr>
    {items}
    <tr class="title-row">
      <td>Invoice Total</td>
      <td class="right">Rs. {invoice.total_amount:,.2f}</td>
    </tr>
    <tr>
      <td>Amount Paid</td>
      <td class="right">Rs. {payment.amount:,.2f}</td>
    </tr>
    <tr class="title-row">
      <td>Balance Due</td>
      <td class="right">Rs. {invoice.balance:,.2f}</td>
    </tr>
  </table>

  <p style="font-size: 11px; color: #777; margin-top: 18px;">
    This is a computer-generated receipt. Reference: {payment.reference or "—"}
  </p>
</body>
</html>"""

        return HttpResponse(html)


class PaymentReceiptPDFView(APIView):
    """Download a PDF receipt for a single payment."""

    permission_classes = [IsFinanceReaderRole]

    def get(self, request, pk):
        payment = (
            Payment.objects
            .filter(pk=pk)
            .select_related(
                "invoice",
                "invoice__student",
                "invoice__enrollment__class_obj",
                "invoice__enrollment__section",
                "invoice__academic_year",
            )
            .prefetch_related("invoice__items__category")
            .first()
        )

        if payment is None:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        if not is_manager(user):
            if is_parent(user):
                student_ids = parent_student_ids(user)

                if payment.invoice.student_id not in student_ids:
                    raise PermissionDenied(
                        "You cannot view this receipt."
                    )
            elif is_student(user):
                profile = get_student_profile(user)

                if (
                    profile is None
                    or payment.invoice.student_id != profile.pk
                ):
                    raise PermissionDenied(
                        "You cannot view this receipt."
                    )

        record_audit(
            request=request,
            action="export",
            model_name="Payment",
            object_id=str(payment.pk),
            object_repr=str(payment),
            details={"format": "pdf"},
        )

        response = HttpResponse(
            payment_receipt_pdf(payment),
            content_type="application/pdf",
        )

        response[
            "Content-Disposition"
        ] = f'attachment; filename="receipt-{payment.receipt_number}.pdf"'

        return response
