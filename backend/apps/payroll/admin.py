from django.contrib import admin

from .models import PayrollRecord, Payslip, SalaryStructure


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ["employee", "basic_salary", "effective_date", "status"]
    list_filter = ["status"]


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = [
        "employee",
        "month",
        "year",
        "gross_salary",
        "net_salary",
        "status",
    ]
    list_filter = ["status", "year", "month"]


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ["record", "issued_at"]