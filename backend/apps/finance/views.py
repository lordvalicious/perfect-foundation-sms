from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope
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

from .models import (
    FeeCategory,
    FeeStructure,
    Invoice,
    Payment,
    PaymentReversal,
    Account,
    JournalEntry,
    JournalLine,
    Expense,
    Concession,
    PaymentRefund,
)
from .pdf import payment_receipt_pdf
from .serializers import (
    FeeCategorySerializer,
    FeeStructureSerializer,
    InvoiceCreateSerializer,
    InvoiceSerializer,
    PaymentCreateSerializer,
    PaymentReversalSerializer,
    PaymentSerializer,
    AccountSerializer,
    JournalEntrySerializer,
    ExpenseSerializer,
    ConcessionSerializer,
    PaymentRefundSerializer,
)


def institution_filter(queryset, request):
    return queryset.filter(institution=getattr(request, "institution", None))


def scoped_invoice_queryset(request):
    queryset = Invoice.objects.filter(
        academic_year__school=getattr(request, "institution", None),
    )
    return apply_campus_scope(queryset, request, "enrollment__campus_id")


class AccountListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAccountantRole]
    serializer_class = AccountSerializer

    def get_queryset(self):
        queryset = institution_filter(Account.objects.select_related("parent"), self.request)
        active = self.request.query_params.get("active")
        if active is not None:
            queryset = queryset.filter(is_active=active.lower() == "true")
        return queryset

    def perform_create(self, serializer):
        serializer.save(institution=self.request.institution)


class JournalEntryListView(generics.ListAPIView):
    permission_classes = [IsAccountantRole]
    serializer_class = JournalEntrySerializer

    def get_queryset(self):
        queryset = institution_filter(
            JournalEntry.objects.prefetch_related("lines__account").order_by("-posting_date", "-id"),
            self.request,
        )
        return apply_campus_scope(queryset, self.request, "campus_id")


class ExpenseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAccountantRole]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        queryset = institution_filter(
            Expense.objects.select_related("campus", "expense_account", "payment_account"),
            self.request,
        )
        return apply_campus_scope(queryset, self.request, "campus_id")

    def perform_create(self, serializer):
        campus = serializer.validated_data.get("campus")
        if campus:
            from apps.accounts.access import assert_campus_allowed
            assert_campus_allowed(self.request.user, campus.pk)
        serializer.save(institution=self.request.institution, created_by=self.request.user)


class ExpensePostView(APIView):
    permission_classes = [IsAccountantRole]

    @transaction.atomic
    def post(self, request, pk):
        expense = get_object_or_404(
            institution_filter(Expense.objects.select_related("campus", "expense_account", "payment_account"), request),
            pk=pk,
        )
        if expense.campus_id:
            from apps.accounts.access import assert_campus_allowed
            assert_campus_allowed(request.user, expense.campus_id)
        if expense.status == "cancelled":
            return Response({"detail": "Cancelled expenses cannot be posted."}, status=400)
        if expense.journal_entry_id:
            return Response(ExpenseSerializer(expense).data)
        entry = JournalEntry.objects.create(
            institution=expense.institution,
            campus=expense.campus,
            posting_date=expense.expense_date,
            description=f"Expense: {expense.vendor or expense.reference or expense.id}",
            source_type="expense",
            source_id=str(expense.pk),
            created_by=request.user,
        )
        JournalLine.objects.create(entry=entry, account=expense.expense_account, debit=expense.amount, memo=expense.notes)
        JournalLine.objects.create(entry=entry, account=expense.payment_account, credit=expense.amount, memo=expense.reference)
        expense.journal_entry = entry
        expense.status = "paid"
        expense.save(update_fields=["journal_entry", "status", "updated_at"])
        record_audit(request=request, action="expense_posted", model_name="Expense", object_id=str(expense.pk), object_repr=str(expense), details={"amount": str(expense.amount)})
        return Response(ExpenseSerializer(expense).data)


class ConcessionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAccountantRole]
    serializer_class = ConcessionSerializer

    def get_queryset(self):
        return Concession.objects.filter(
            invoice__in=scoped_invoice_queryset(self.request),
        ).select_related("invoice")

    def perform_create(self, serializer):
        invoice = serializer.validated_data["invoice"]
        if not scoped_invoice_queryset(self.request).filter(pk=invoice.pk).exists():
            raise PermissionDenied(
                "You cannot create a concession outside your institution or campus."
            )
        serializer.save()


class ConcessionApproveView(APIView):
    permission_classes = [IsAccountantRole]

    @transaction.atomic
    def post(self, request, pk):
        concession = get_object_or_404(
            Concession.objects.select_related("invoice__enrollment"),
            pk=pk,
            invoice__in=scoped_invoice_queryset(request),
        )
        if concession.status != "pending":
            return Response({"detail": "Only pending concessions can be approved."}, status=400)
        from django.utils import timezone
        concession.status = "approved"
        concession.approved_by = request.user
        concession.approved_at = timezone.now()
        concession.save(update_fields=["status", "approved_by", "approved_at"])
        concession.invoice.refresh_status()
        record_audit(request=request, action="concession_approved", model_name="Concession", object_id=str(pk), object_repr=str(concession), details={"amount": str(concession.amount)})
        return Response(ConcessionSerializer(concession).data)


class PaymentRefundCreateView(generics.CreateAPIView):
    permission_classes = [IsAccountantRole]
    serializer_class = PaymentRefundSerializer

    def perform_create(self, serializer):
        payment = serializer.validated_data["payment"]
        invoice = payment.invoice
        if not scoped_invoice_queryset(self.request).filter(pk=invoice.pk).exists():
            raise PermissionDenied("You cannot refund a payment outside your institution or campus.")
        refund = serializer.save(created_by=self.request.user)
        record_audit(request=self.request, action="payment_refund", model_name="PaymentRefund", object_id=str(refund.pk), object_repr=str(refund), details={"amount": str(refund.amount), "payment": payment.receipt_number})


class TrialBalanceReportView(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        rows = []
        entries = JournalEntry.objects.filter(institution=request.institution, status="posted")
        entries = apply_campus_scope(entries, request, "campus_id")
        lines = JournalLine.objects.filter(entry__in=entries).values("account_id", "account__code", "account__name").annotate(debit=Sum("debit"), credit=Sum("credit")).order_by("account__code")
        for line in lines:
            rows.append({"account": line["account__name"], "code": line["account__code"], "debit": str(line["debit"] or Decimal("0.00")), "credit": str(line["credit"] or Decimal("0.00"))})
        return Response({"rows": rows})


class IncomeExpenseReportView(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        entries = apply_campus_scope(JournalEntry.objects.filter(institution=request.institution, status="posted"), request, "campus_id")
        lines = JournalLine.objects.filter(entry__in=entries).values("account__account_type").annotate(debit=Sum("debit"), credit=Sum("credit"))
        income = Decimal("0.00")
        expense = Decimal("0.00")
        for line in lines:
            if line["account__account_type"] == "income":
                income += (line["credit"] or 0) - (line["debit"] or 0)
            elif line["account__account_type"] == "expense":
                expense += (line["debit"] or 0) - (line["credit"] or 0)
        return Response({"income": str(income), "expense": str(expense), "net": str(income - expense)})


class ReceivablesReportView(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        invoices = scoped_invoice_queryset(request).select_related("student")
        rows = [{"invoice": invoice.invoice_number, "student": invoice.student.full_name, "balance": str(invoice.balance)} for invoice in invoices if invoice.balance > 0]
        return Response({"rows": rows, "total": str(sum((Decimal(row["balance"]) for row in rows), Decimal("0.00")))})


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
        queryset = queryset.filter(
            academic_year__school=self.request.institution
        )
        queryset = apply_campus_scope(queryset, self.request, "enrollment__campus_id")

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
        queryset = queryset.filter(
            invoice__academic_year__school=self.request.institution
        )
        queryset = apply_campus_scope(queryset, self.request, "invoice__enrollment__campus_id")

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


class FeeStructureListView(generics.ListCreateAPIView):
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAccountantRole]
    pagination_class = None

    def get_queryset(self):
        queryset = (
            FeeStructure.objects
            .select_related(
                "academic_year",
                "campus",
                "class_obj__unit__campus",
                "category",
            )
            .order_by("campus", "class_obj", "category")
        )

        params = self.request.query_params

        if params.get("academic_year"):
            queryset = queryset.filter(
                academic_year_id=params.get("academic_year")
            )

        queryset = apply_campus_scope(
            queryset,
            self.request,
            "campus_id",
        )

        if params.get("class_obj"):
            queryset = queryset.filter(class_obj_id=params.get("class_obj"))

        if params.get("category"):
            queryset = queryset.filter(category_id=params.get("category"))

        status = params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset


class FeeStructureDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = FeeStructure.objects.filter(
            academic_year__school=self.request.institution
        ).select_related(
            "academic_year",
            "campus",
            "class_obj__unit__campus",
            "category",
        )
        return apply_campus_scope(queryset, self.request, "campus_id")


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
        queryset = queryset.filter(
            academic_year__school=self.request.institution
        )
        queryset = apply_campus_scope(queryset, self.request, "enrollment__campus_id")

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
        enrollment = serializer.validated_data["enrollment"]
        if enrollment.academic_year.school_id != self.request.institution.id:
            raise PermissionDenied("Enrollment is outside the active institution.")
        from apps.accounts.access import assert_campus_allowed
        assert_campus_allowed(self.request.user, enrollment.campus_id)
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
        queryset = queryset.filter(
            invoice__academic_year__school=self.request.institution
        )
        queryset = apply_campus_scope(queryset, self.request, "invoice__enrollment__campus_id")

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
        invoice = serializer.validated_data["invoice"]
        if invoice.academic_year.school_id != self.request.institution.id:
            raise PermissionDenied("Invoice is outside the active institution.")
        from apps.accounts.access import assert_campus_allowed
        assert_campus_allowed(self.request.user, invoice.enrollment.campus_id)
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
        payment = serializer.validated_data["payment"]
        if not scoped_invoice_queryset(self.request).filter(
            pk=payment.invoice_id
        ).exists():
            raise PermissionDenied(
                "You cannot reverse a payment outside your institution or campus."
            )
        reversal = serializer.save(created_by=self.request.user)
        record_audit(request=self.request, action="payment_reversal", model_name="PaymentReversal", object_id=str(reversal.pk), object_repr=str(reversal.payment), details={"amount": str(reversal.amount), "payment": reversal.payment.receipt_number})


class PaymentReceiptHTMLView(APIView):
    """Printable HTML receipt for a single payment."""

    permission_classes = [IsFinanceReaderRole]

    def get_object(self):
        payment = (
            Payment.objects
            .filter(
                pk=self.kwargs["pk"],
                invoice__academic_year__school=self.request.institution,
            )
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
        from apps.accounts.access import assert_campus_allowed
        assert_campus_allowed(user, payment.invoice.enrollment.campus_id)

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
            .filter(
                pk=pk,
                invoice__academic_year__school=request.institution,
            )
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
        from apps.accounts.access import assert_campus_allowed
        assert_campus_allowed(user, payment.invoice.enrollment.campus_id)

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
