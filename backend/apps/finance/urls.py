from django.urls import path

from .views import (
    FeeCategoryListView,
    FeeStructureDetailView,
    FeeStructureListView,
    InvoiceCreateView,
    InvoiceDetailView,
    InvoiceListView,
    PaymentCreateView,
    PaymentDetailView,
    PaymentListView,
    PaymentReceiptHTMLView,
    PaymentReceiptPDFView,
    PaymentReversalCreateView,
    AccountListCreateView,
    JournalEntryListView,
    ExpenseListCreateView,
    ExpensePostView,
    ConcessionListCreateView,
    ConcessionApproveView,
    PaymentRefundCreateView,
    TrialBalanceReportView,
    IncomeExpenseReportView,
    ReceivablesReportView,
    BulkInvoiceCreateView,
    BulkPaymentCreateView,
)
from .stripe_views import StripeCheckoutView, stripe_webhook
from .jazzcash_views import (
    JazzCashCheckoutView,
    jazzcash_callback,
)
from .cron_views import LateFeeCronView


urlpatterns = [
    path("accounts/", AccountListCreateView.as_view(), name="account-list"),
    path("journal/", JournalEntryListView.as_view(), name="journal-list"),
    path("expenses/", ExpenseListCreateView.as_view(), name="expense-list"),
    path("expenses/<int:pk>/post/", ExpensePostView.as_view(), name="expense-post"),
    path("concessions/", ConcessionListCreateView.as_view(), name="concession-list"),
    path("concessions/<int:pk>/approve/", ConcessionApproveView.as_view(), name="concession-approve"),
    path("refunds/", PaymentRefundCreateView.as_view(), name="refund-create"),
    path("reports/trial-balance/", TrialBalanceReportView.as_view(), name="trial-balance"),
    path("reports/income-expense/", IncomeExpenseReportView.as_view(), name="income-expense"),
    path("reports/receivables/", ReceivablesReportView.as_view(), name="receivables"),
    path("invoices/", InvoiceListView.as_view(), name="invoice-list"),
    path(
        "invoices/create/",
        InvoiceCreateView.as_view(),
        name="invoice-create",
    ),
    path(
        "invoices/<int:pk>/",
        InvoiceDetailView.as_view(),
        name="invoice-detail",
    ),
    path("payments/", PaymentListView.as_view(), name="payment-list"),
    path(
        "payments/create/",
        PaymentCreateView.as_view(),
        name="payment-create",
    ),
    path(
        "payments/<int:pk>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),
    path(
        "payments/<int:pk>/receipt/",
        PaymentReceiptHTMLView.as_view(),
        name="payment-receipt",
    ),
    path(
        "payments/<int:pk>/receipt.pdf/",
        PaymentReceiptPDFView.as_view(),
        name="payment-receipt-pdf",
    ),
    path(
        "payments/reversals/",
        PaymentReversalCreateView.as_view(),
        name="payment-reversal-create",
    ),
    path(
        "stripe/checkout/",
        StripeCheckoutView.as_view(),
        name="stripe-checkout",
    ),
    path(
        "stripe/webhook/",
        stripe_webhook,
        name="stripe-webhook",
    ),
    path(
        "jazzcash/checkout/",
        JazzCashCheckoutView.as_view(),
        name="jazzcash-checkout",
    ),
    path(
        "jazzcash/callback/",
        jazzcash_callback,
        name="jazzcash-callback",
    ),
    path(
        "categories/",
        FeeCategoryListView.as_view(),
        name="fee-category-list",
    ),
    path(
        "fee-structures/",
        FeeStructureListView.as_view(),
        name="fee-structure-list",
    ),
    path(
        "fee-structures/<int:pk>/",
        FeeStructureDetailView.as_view(),
        name="fee-structure-detail",
    ),
    path(
        "invoices/bulk/",
        BulkInvoiceCreateView.as_view(),
        name="invoice-bulk-create",
    ),
    path(
        "payments/bulk/",
        BulkPaymentCreateView.as_view(),
        name="payment-bulk-create",
    ),
    path(
        "cron/late-fees/",
        LateFeeCronView.as_view(),
        name="late-fee-cron",
    ),
]
