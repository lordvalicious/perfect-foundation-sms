from django.contrib import admin

from .models import SupportTicket, TicketCategory, TicketMessage


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "institution", "status", "sort_order")
    search_fields = ("name",)
    list_filter = ("status", "institution")
    ordering = ("institution", "sort_order")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "institution",
        "campus",
        "category",
        "priority",
        "status",
        "assignee",
        "created_by",
        "created_at",
    )
    search_fields = ("subject", "description")
    list_filter = ("status", "priority", "campus", "institution")
    autocomplete_fields = ("campus", "category", "created_by", "assignee")


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "is_internal", "created_at")
    search_fields = ("body",)
    list_filter = ("is_internal",)