from django.contrib import admin  # type: ignore[import]

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "employee_number",
        "first_name",
        "last_name",
        "designation",
        "campus",
        "phone",
        "gender",
        "status",
    )

    list_filter = (
        "gender",
        "status",
        "designation",
        "campus",
    )

    search_fields = (
        "employee_number",
        "first_name",
        "last_name",
        "phone",
        "email",
    )