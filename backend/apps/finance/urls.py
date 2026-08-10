from django.urls import path

from .views import (
    FeeCategoryListView,
    InvoiceListView,
    PaymentListView,
)


urlpatterns = [
    path("invoices/", InvoiceListView.as_view(), name="invoice-list"),
    path("payments/", PaymentListView.as_view(), name="payment-list"),
    path("categories/", FeeCategoryListView.as_view(), name="fee-category-list"),
]
