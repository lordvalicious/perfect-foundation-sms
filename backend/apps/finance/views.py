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
  <h1>School</h1>
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


class BulkInvoiceCreateView(APIView):
    """Create invoices for all active enrollments matching the given filters.

    POST body:
        academic_year (int, required)
        campus (int, required)
        class_obj (int, required)
        category (int, required)  — fee category id
        due_date (str, optional)  — defaults to today
        notes (str, optional)
        skip_existing (bool, optional, default true) — skip enrollments that already
            have an issued/partial/paid invoice for this category in the same year
    """

    permission_classes = [IsAccountantRole]

    @transaction.atomic
    def post(self, request):
        from datetime import date as _date
        from django.core.exceptions import ValidationError as ModelValidationError
        from apps.students.models import Enrollment
        from apps.accounts.access import assert_campus_allowed
        from .services import next_invoice_number

        academic_year_id = request.data.get("academic_year")
        campus_id = request.data.get("campus")
        class_obj_id = request.data.get("class_obj")
        category_id = request.data.get("category")
        due_date_str = request.data.get("due_date")
        notes = request.data.get("notes", "")
        skip_existing = request.data.get("skip_existing", True)

        if not all([academic_year_id, campus_id, class_obj_id, category_id]):
            return Response(
                {"detail": "academic_year, campus, class_obj, and category are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assert_campus_allowed(request.user, campus_id)

        try:
            fee_structure = FeeStructure.objects.get(
                academic_year_id=academic_year_id,
                campus_id=campus_id,
                class_obj_id=class_obj_id,
                category_id=category_id,
                status="active",
            )
        except FeeStructure.DoesNotExist:
            return Response(
                {"detail": "No active fee structure found for the selected filters."},
                status=status.HTTP_404_NOT_FOUND,
            )

        due_date = _date.today()
        if due_date_str:
            from datetime import date as _parse_date
            try:
                due_date = _parse_date.fromisoformat(due_date_str)
            except ValueError:
                return Response(
                    {"detail": "Invalid due_date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        enrollments = Enrollment.objects.filter(
            academic_year_id=academic_year_id,
            campus_id=campus_id,
            class_obj_id=class_obj_id,
            status="active",
        ).select_related("student", "academic_year", "campus", "class_obj", "section")

        if skip_existing:
            enrolled_with_invoice = set(
                InvoiceItem.objects.filter(
                    category_id=category_id,
                    invoice__academic_year_id=academic_year_id,
                    invoice__status__in=("issued", "partial", "paid"),
                    invoice__enrollment__campus_id=campus_id,
                    invoice__enrollment__class_obj_id=class_obj_id,
                ).values_list("invoice__enrollment_id", flat=True)
            )
            enrollments = enrollments.exclude(pk__in=enrolled_with_invoice)

        created = []
        skipped = []

        for enrollment in enrollments:
            try:
                invoice = Invoice.objects.create(
                    invoice_number=next_invoice_number(),
                    enrollment=enrollment,
                    student=enrollment.student,
                    academic_year=enrollment.academic_year,
                    issue_date=_date.today(),
                    due_date=due_date,
                    status="issued",
                    notes=notes,
                )
                InvoiceItem.objects.create(
                    invoice=invoice,
                    category=fee_structure.category,
                    description=fee_structure.category.name,
                    amount=fee_structure.amount,
                )
                created.append(invoice.pk)
            except (ModelValidationError, Exception) as exc:
                skipped.append({
                    "enrollment": enrollment.pk,
                    "student": str(enrollment.student),
                    "reason": str(exc),
                })

        record_audit(
            request=request,
            action="create",
            model_name="Invoice",
            object_id="bulk",
            object_repr=f"Bulk invoice creation for class {class_obj_id}",
            details={
                "created": len(created),
                "skipped": len(skipped),
                "category": category_id,
            },
        )

        return Response(
            {
                "created": len(created),
                "skipped": len(skipped),
                "skipped_details": skipped,
                "invoice_ids": created,
            },
            status=status.HTTP_201_CREATED,
        )


class BulkPaymentCreateView(APIView):
    """Record payments for multiple invoices at once.

    POST body:
        payments: [
            { invoice (int), amount (decimal), payment_method (str), reference (str, optional), notes (str, optional) }
        ]
        payment_date (str, optional) — defaults to today, applied to all
    """

    permission_classes = [IsAccountantRole]

    @transaction.atomic
    def post(self, request):
        from datetime import date as _date
        from django.core.exceptions import ValidationError as ModelValidationError
        from apps.accounts.access import assert_campus_allowed
        from .services import next_receipt_number

        payments_data = request.data.get("payments", [])
        payment_date_str = request.data.get("payment_date")

        if not payments_data:
            return Response(
                {"detail": "A list of payments is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_date = _date.today()
        if payment_date_str:
            try:
                payment_date = _date.fromisoformat(payment_date_str)
            except ValueError:
                return Response(
                    {"detail": "Invalid payment_date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        created = []
        errors = []

        for idx, item in enumerate(payments_data):
            invoice_id = item.get("invoice")
            amount = item.get("amount")
            payment_method = item.get("payment_method", "cash")
            reference = item.get("reference", "")
            notes = item.get("notes", "")

            if not invoice_id or not amount:
                errors.append({"index": idx, "reason": "invoice and amount are required."})
                continue

            try:
                invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
            except Invoice.DoesNotExist:
                errors.append({"index": idx, "reason": f"Invoice {invoice_id} not found."})
                continue

            if invoice.academic_year.school_id != request.institution.id:
                errors.append({"index": idx, "reason": "Invoice belongs to a different institution."})
                continue

            assert_campus_allowed(request.user, invoice.enrollment.campus_id)

            if invoice.status in ("cancelled", "draft"):
                errors.append({"index": idx, "reason": f"Invoice {invoice.invoice_number} is {invoice.status}."})
                continue

            if amount <= 0:
                errors.append({"index": idx, "reason": "Amount must be greater than zero."})
                continue

            locked_invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
            if amount > locked_invoice.balance:
                errors.append({
                    "index": idx,
                    "reason": f"Amount {amount} exceeds balance {locked_invoice.balance} for {locked_invoice.invoice_number}.",
                })
                continue

            try:
                payment = Payment.objects.create(
                    receipt_number=next_receipt_number(),
                    invoice=locked_invoice,
                    amount=amount,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    status="completed",
                    reference=reference,
                    notes=notes,
                )
                created.append({
                    "payment_id": payment.pk,
                    "receipt_number": payment.receipt_number,
                    "invoice_number": locked_invoice.invoice_number,
                    "amount": str(payment.amount),
                })
            except (ModelValidationError, Exception) as exc:
                errors.append({"index": idx, "reason": str(exc)})

        record_audit(
            request=request,
            action="payment",
            model_name="Payment",
            object_id="bulk",
            object_repr=f"Bulk payment: {len(created)} payments",
            details={"created": len(created), "errors": len(errors)},
        )

        return Response(
            {
                "created": len(created),
                "errors": len(errors),
                "payments": created,
                "error_details": errors,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST,
        )
