from django.contrib import admin

from .models import IdCard


@admin.register(IdCard)
class IdCardAdmin(admin.ModelAdmin):
    list_display = [
        "card_number",
        "holder_type",
        "status",
        "campus",
        "issue_date",
        "expiry_date",
        "created_at",
    ]
    list_filter = ["holder_type", "status"]
    search_fields = [
        "card_number",
        "student__first_name",
        "teacher__first_name",
        "staff__first_name",
    ]