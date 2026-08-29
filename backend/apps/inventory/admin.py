from django.contrib import admin

from .models import (
    Asset,
    AssetAssignment,
    AssetCategory,
    MaintenanceRecord,
    StockLevel,
    StockMovement,
    Supplier,
)


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_person", "phone"]


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "category", "quantity", "unit", "status"]
    list_filter = ["status", "category"]


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ["asset", "assignee_name", "assigned_date", "return_date"]


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ["asset", "date", "cost", "status"]
    list_filter = ["status"]


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ["asset", "campus", "quantity", "minimum_stock", "is_low", "is_out"]
    list_filter = ["campus"]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "asset",
        "campus",
        "movement_type",
        "quantity",
        "created_by",
        "created_at",
    ]
    list_filter = ["movement_type", "campus"]
    readonly_fields = ["created_at"]
