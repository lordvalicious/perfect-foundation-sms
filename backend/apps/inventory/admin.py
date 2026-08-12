from django.contrib import admin

from .models import (
    Asset,
    AssetAssignment,
    AssetCategory,
    MaintenanceRecord,
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
    list_display = ["name", "code", "category", "quantity", "status"]
    list_filter = ["status", "category"]


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ["asset", "assignee_name", "assigned_date", "return_date"]


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ["asset", "date", "cost", "status"]
    list_filter = ["status"]
