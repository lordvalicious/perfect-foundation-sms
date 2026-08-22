from django.contrib import admin

from .models import (
    Employee,
    EmployeeDocument,
    EmploymentContract,
    EmploymentEvent,
    PerformanceReview,
    WorkloadAssignment,
)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_number", "full_name", "institution", "primary_campus", "designation", "status")
    list_filter = ("institution", "primary_campus", "status")
    search_fields = ("employee_number", "designation", "teacher__first_name", "staff_profile__first_name")


@admin.register(EmploymentContract)
class EmploymentContractAdmin(admin.ModelAdmin):
    list_display = ("contract_number", "employee", "contract_type", "start_date", "end_date", "salary", "status")
    list_filter = ("contract_type", "status", "start_date")
    search_fields = ("contract_number", "employee__employee_number")


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "employee", "document_type", "expiry_date", "created_at")
    list_filter = ("document_type", "expiry_date")
    search_fields = ("title", "employee__employee_number")


@admin.register(WorkloadAssignment)
class WorkloadAssignmentAdmin(admin.ModelAdmin):
    list_display = ("employee", "academic_year", "title", "weekly_periods", "hours_per_week", "status")
    list_filter = ("academic_year", "status")


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ("employee", "period", "review_date", "rating", "status", "reviewer")
    list_filter = ("status", "rating", "review_date")
    search_fields = ("employee__employee_number", "period")


@admin.register(EmploymentEvent)
class EmploymentEventAdmin(admin.ModelAdmin):
    list_display = ("employee", "event_type", "effective_date", "from_campus", "to_campus")
    list_filter = ("event_type", "effective_date")
    search_fields = ("employee__employee_number", "reason")
    readonly_fields = ("created_at",)