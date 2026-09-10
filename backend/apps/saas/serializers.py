"""DRF serializers for SaaS/platform surfaces."""

from rest_framework import serializers

from .models import DailyUsageSnapshot, FeatureFlag, Plan, Subscription


class FeatureFlagSerializer(serializers.ModelSerializer):
    scope = serializers.SerializerMethodField()
    institution_name = serializers.CharField(
        source="institution.name", read_only=True, default=None
    )

    class Meta:
        model = FeatureFlag
        fields = [
            "id",
            "name",
            "label",
            "description",
            "enabled",
            "scope",
            "institution_id",
            "institution_name",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def get_scope(self, obj):
        return "global" if obj.institution_id is None else "institution"


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "id",
            "code",
            "name",
            "description",
            "max_students",
            "max_staff",
            "max_storage_mb",
            "max_api_requests_per_day",
            "monthly_price_cents",
            "features",
            "is_active",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_code = serializers.CharField(source="plan.code", read_only=True)
    display_status = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "plan_code",
            "status",
            "display_status",
            "trial_ends_at",
            "current_period_start",
            "current_period_end",
            "seats_used",
            "metadata",
            "is_active_subscription",
        ]
        read_only_fields = fields


class DailyUsageSnapshotSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = DailyUsageSnapshot
        fields = [
            "id",
            "school_id",
            "school_name",
            "date",
            "logins",
            "failed_logins",
            "api_requests",
            "students",
            "staff",
            "payments",
        ]