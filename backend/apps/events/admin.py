from django.contrib import admin

from .models import Event, EventAudience, EventRSVP


class EventAudienceInline(admin.TabularInline):
    model = EventAudience
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "school",
        "campus",
        "start_datetime",
        "end_datetime",
        "status",
        "created_by",
    ]

    list_filter = ["status", "school", "campus"]
    search_fields = ["title", "description"]
    inlines = [EventAudienceInline]


@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ["event", "user", "response", "created_at"]
    list_filter = ["response"]
    search_fields = ["event__title", "user__username"]
