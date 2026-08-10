
from django.contrib import admin

from .models import (
    FeeCategory,
    FeeStructure,
    Invoice,
    InvoiceItem,
    Payment,
)


@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "frequency",
        "status",
    )

    search_fields = (
        "name",
        "description",
    )

    list_filter = (
        "frequency",
        "status",
    )


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = (
        "campus",
        "class_obj",
        "academic_year",
        "category",
        "amount",
        "due_day",
        "status",
    )

    search_fields = (
        "campus__name",
        "class_obj__name",
        "category__name",
    )

    list_filter = (
        "academic_year",
        "campus",
        "category",
        "status",
    )

    autocomplete_fields = (
        "academic_year",
        "campus",
        "class_obj",
        "category",
    )


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "student",
        "academic_year",
        "issue_date",
        "due_date",
        "total_amount_display",
        "paid_amount_display",
        "balance_display",
        "status",
    )

    search_fields = (
        "invoice_number",
        "student__first_name",
        "student__middle_name",
        "student__last_name",
        "student__admission_number",
    )

    list_filter = (
        "status",
        "academic_year",
        "issue_date",
        "due_date",
    )

    date_hierarchy = "issue_date"

    autocomplete_fields = (
        "student",
        "enrollment",
        "academic_year",
    )

    inlines = [
        InvoiceItemInline,
        PaymentInline,
    ]

    @admin.display(description="Total")
    def total_amount_display(self, obj):
        return obj.total_amount

    @admin.display(description="Paid")
    def paid_amount_display(self, obj):
        return obj.paid_amount

    @admin.display(description="Balance")
    def balance_display(self, obj):
        return obj.balance


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_number",
        "invoice",
        "amount",
        "payment_date",
        "payment_method",
        "status",
    )

    search_fields = (
        "receipt_number",
        "invoice__invoice_number",
        "invoice__student__first_name",
        "invoice__student__last_name",
        "invoice__student__admission_number",
    )

    list_filter = (
        "payment_method",
        "status",
        "payment_date",
    )

    date_hierarchy = "payment_date"

    autocomplete_fields = (
        "invoice",
    )

