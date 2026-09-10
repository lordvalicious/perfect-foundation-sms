from django.contrib import admin

from .models import DailyUsageSnapshot, FeatureFlag, Plan, Subscription


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ["name", "label", "enabled", "institution", "updated_at"]
    list_filter = ["enabled", "institution"]
    search_fields = ["name", "label"]


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "monthly_price_cents", "is_active", "sort_order"]
    list_filter = ["is_active"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "school",
        "plan",
        "status",
        "trial_ends_at",
        "current_period_end",
        "seats_used",
    ]
    list_filter = ["status", "plan"]


@admin.register(DailyUsageSnapshot)
class DailyUsageSnapshotAdmin(admin.ModelAdmin):
    list_display = ["school", "date", "logins", "failed_logins", "api_requests"]
    list_filter = ["date"]