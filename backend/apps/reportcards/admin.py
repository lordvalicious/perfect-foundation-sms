from django.contrib import admin

from .models import ReportCard, ReportCardSubject


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "exam",
        "position",
        "percentage_display",
        "grade_display",
        "result_display",
        "is_complete_display",
    )

    list_filter = (
        "exam",
        "exam__campus",
        "exam__class_obj",
    )

    search_fields = (
        "student__first_name",
        "student__middle_name",
        "student__last_name",
        "student__admission_number",
        "exam__name",
    )

    readonly_fields = (
        "position",
        "created_at",
        "updated_at",
    )

    def percentage_display(self, obj):
        return f"{obj.percentage}%"

    percentage_display.short_description = "Percentage"

    def grade_display(self, obj):
        return obj.grade

    grade_display.short_description = "Grade"

    def result_display(self, obj):
        return obj.overall_result

    result_display.short_description = "Result"

    def is_complete_display(self, obj):
        return obj.is_complete

    is_complete_display.short_description = "Complete"


@admin.register(ReportCardSubject)
class ReportCardSubjectAdmin(admin.ModelAdmin):
    list_display = (
        "report_card",
        "exam_subject",
        "obtained_marks",
        "maximum_marks",
        "percentage",
        "grade",
        "is_pass",
    )

    list_filter = (
        "is_pass",
        "grade",
    )

    search_fields = (
        "report_card__student__first_name",
        "report_card__student__last_name",
        "report_card__student__admission_number",
        "exam_subject__subject__name",
    )