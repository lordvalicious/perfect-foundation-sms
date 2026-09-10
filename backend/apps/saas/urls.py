from django.urls import path

from .views import (
    CurrentFlagsView,
    FeatureFlagAdminView,
    FeatureFlagDeleteView,
    PlansListView,
    PlatformOverviewView,
    PlatformStatusView,
    SecurityOverviewView,
    SubscriptionSummaryView,
    TenantSubscriptionView,
    UsageAnalyticsView,
)

app_name = "saas"

urlpatterns = [
    path("flags/", FeatureFlagAdminView.as_view(), name="feature-flags"),
    path("flags/<int:pk>/", FeatureFlagDeleteView.as_view(), name="feature-flag-detail"),
    path("flags/current/", CurrentFlagsView.as_view(), name="current-flags"),
    path("plans/", PlansListView.as_view(), name="plans-list"),
    path("subscription/", SubscriptionSummaryView.as_view(), name="subscription-summary"),
    path(
        "tenants/<int:school_id>/subscription/",
        TenantSubscriptionView.as_view(),
        name="tenant-subscription",
    ),
    path("analytics/usage/", UsageAnalyticsView.as_view(), name="usage-analytics"),
    path("platform/overview/", PlatformOverviewView.as_view(), name="platform-overview"),
    path("platform/status/", PlatformStatusView.as_view(), name="platform-status"),
    path("security/", SecurityOverviewView.as_view(), name="security-overview"),
]