from django.contrib import admin

from .models import Visitor


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "badge_number",
        "campus",
        "purpose",
        "status",
        "check_in",
        "check_out",
    ]
    list_filter = ["status", "campus"]
    search_fields = ["full_name", "phone", "meeting_party"]