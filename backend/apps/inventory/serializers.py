from rest_framework import serializers

from .models import (
    Asset,
    AssetAssignment,
    AssetCategory,
    MaintenanceRecord,
    Supplier,
)


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = ["id", "name", "description"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "contact_person",
            "phone",
            "email",
            "address",
        ]


class AssetSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(
        source="campus.name",
        read_only=True,
        default="",
    )
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
        default="",
    )
    supplier_name = serializers.CharField(
        source="supplier.name",
        read_only=True,
        default="",
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    total_value = serializers.DecimalField(
        read_only=True,
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        model = Asset
        fields = [
            "id",
            "name",
            "campus",
            "campus_name",
            "code",
            "category",
            "category_name",
            "supplier",
            "supplier_name",
            "quantity",
            "unit_cost",
            "total_value",
            "purchase_date",
            "location",
            "status",
            "status_display",
            "notes",
        ]


class AssetAssignmentSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(
        source="asset.name",
        read_only=True,
    )
    assignee_type_display = serializers.CharField(
        source="get_assignee_type_display",
        read_only=True,
    )

    class Meta:
        model = AssetAssignment
        fields = [
            "id",
            "asset",
            "asset_name",
            "assignee_type",
            "assignee_type_display",
            "assignee_name",
            "assigned_to",
            "quantity",
            "assigned_date",
            "return_date",
            "notes",
        ]


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(
        source="asset.name",
        read_only=True,
    )

    class Meta:
        model = MaintenanceRecord
        fields = [
            "id",
            "asset",
            "asset_name",
            "date",
            "cost",
            "description",
            "performed_by",
            "status",
        ]
