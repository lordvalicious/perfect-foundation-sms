
from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "student",
        "campus",
        "class_obj",
        "section",
        "academic_year",
        "status",
    )

    search_fields = (
        "student__first_name",
        "student__middle_name",
        "student__last_name",
        "student__admission_number",
    )

    list_filter = (
        "date",
        "status",
        "campus",
        "academic_year",
        "class_obj",
        "section",
    )

    date_hierarchy = "date"

    autocomplete_fields = (
        "student",
        "enrollment",
        "academic_year",
        "campus",
        "class_obj",
        "section",
    )