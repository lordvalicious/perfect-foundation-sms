from rest_framework import serializers

from .models import FeeCategory, Invoice, InvoiceItem, Payment


class FeeCategorySerializer(serializers.ModelSerializer):
    frequency_display = serializers.CharField(
        source="get_frequency_display",
        read_only=True,
    )

    class Meta:
        model = FeeCategory
        fields = [
            "id",
            "name",
            "description",
            "frequency",
            "frequency_display",
            "status",
            "created_at",
            "updated_at",
        ]


class InvoiceItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = InvoiceItem
        fields = [
            "id",
            "category",
            "category_name",
            "description",
            "amount",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )
    admission_number = serializers.CharField(
        source="student.admission_number",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    campus_name = serializers.CharField(
        source="enrollment.campus.name",
        read_only=True,
    )
    class_name = serializers.CharField(
        source="enrollment.class_obj.name",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    items = InvoiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "student",
            "student_name",
            "admission_number",
            "enrollment",
            "academic_year",
            "academic_year_name",
            "campus_name",
            "class_name",
            "issue_date",
            "due_date",
            "discount",
            "subtotal",
            "total_amount",
            "paid_amount",
            "balance",
            "status",
            "status_display",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(
        source="invoice.invoice_number",
        read_only=True,
    )
    student_name = serializers.CharField(
        source="invoice.student.full_name",
        read_only=True,
    )
    admission_number = serializers.CharField(
        source="invoice.student.admission_number",
        read_only=True,
    )
    payment_method_display = serializers.CharField(
        source="get_payment_method_display",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "receipt_number",
            "invoice",
            "invoice_number",
            "student_name",
            "admission_number",
            "amount",
            "payment_date",
            "payment_method",
            "payment_method_display",
            "status",
            "status_display",
            "reference",
            "notes",
            "created_at",
            "updated_at",
        ]
