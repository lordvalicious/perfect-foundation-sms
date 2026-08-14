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
)


urlpatterns = [
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
]
