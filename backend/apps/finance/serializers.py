from decimal import Decimal

from rest_framework import serializers

from .models import FeeCategory, Invoice, InvoiceItem, Payment, PaymentReversal
from .services import next_invoice_number, next_receipt_number


class InvoiceItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ["category", "description", "amount"]


class InvoiceCreateSerializer(serializers.ModelSerializer):
    items = InvoiceItemWriteSerializer(many=True, write_only=True)
    invoice_number = serializers.CharField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "student",
            "enrollment",
            "academic_year",
            "issue_date",
            "due_date",
            "discount",
            "notes",
            "items",
        ]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError(
                "At least one invoice item is required."
            )

        for item in items:
            if item["amount"] <= 0:
                raise serializers.ValidationError(
                    "Invoice item amounts must be greater than zero."
                )

        return items

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        items = validated_data.pop("items")

        validated_data["invoice_number"] = next_invoice_number()
        validated_data["status"] = "issued"

        try:
            invoice = Invoice.objects.create(**validated_data)
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        for item in items:
            InvoiceItem.objects.create(invoice=invoice, **item)

        return invoice


class PaymentCreateSerializer(serializers.ModelSerializer):
    receipt_number = serializers.CharField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "receipt_number",
            "invoice",
            "amount",
            "payment_date",
            "payment_method",
            "status",
            "reference",
            "notes",
        ]

    def validate(self, attrs):
        invoice = attrs.get("invoice")
        amount = attrs.get("amount")

        if invoice and amount is not None:
            if amount <= 0:
                raise serializers.ValidationError(
                    {"amount": "Payment amount must be greater than zero."}
                )

            if amount > invoice.balance:
                raise serializers.ValidationError(
                    {
                        "amount": (
                            "Payment cannot be greater than the "
                            f"invoice balance (Rs. {invoice.balance:,.2f})."
                        )
                    }
                )

        return attrs

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        validated_data["receipt_number"] = next_receipt_number()

        try:
            return Payment.objects.create(**validated_data)
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)


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
            "net_amount",
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


class PaymentReversalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReversal
        fields = ["id", "payment", "amount", "reversal_date", "reason", "status", "created_by", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]
