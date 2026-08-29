from django.contrib import admin

from .models import (
    Announcement,
    Notification,
    QueuedNotification,
)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status", "published_at"]
    list_filter = ["category", "status"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "recipient", "notification_type", "is_read"]
    list_filter = ["notification_type", "is_read"]


@admin.register(QueuedNotification)
class QueuedNotificationAdmin(admin.ModelAdmin):
    list_display = [
        "channel",
        "to_address",
        "recipient",
        "kind",
        "status",
        "attempts",
        "next_attempt_at",
        "created_at",
    ]
    list_filter = ["status", "channel", "kind"]
    readonly_fields = [
        "channel",
        "recipient",
        "to_address",
        "kind",
        "reference",
        "subject",
        "body",
        "payload",
        "attempts",
        "max_attempts",
        "next_attempt_at",
        "processed_at",
        "last_error",
        "created_at",
        "updated_at",
    ]
    actions = ["requeue_failed"]

    @admin.action(description="Requeue selected failed notifications")
    def requeue_failed(self, request, queryset):
        from django.utils import timezone

        count = 0

        for item in queryset.filter(status="failed"):
            item.status = "queued"
            item.next_attempt_at = timezone.now()
            item.last_error = ""
            item.save(
                update_fields=[
                    "status",
                    "next_attempt_at",
                    "last_error",
                    "updated_at",
                ]
            )
            count += 1

        self.message_user(
            request,
            f"{count} failed notification(s) requeued.",
        )
