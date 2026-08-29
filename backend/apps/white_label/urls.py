from django.urls import path
from rest_framework import generics

from .views import (
    WhiteLabelBrandingView,
    ThemePreviewView,
    SchoolSettingsView,
    DomainMappingListCreateView,
    DomainMappingDetailView,
    SchoolBrandingPublicView,
    WhiteLabelAuditLogView,
    WhiteLabelAuditLogDetailView,
    branding_css_variables,
    school_branding_config,
)

urlpatterns = [
    # Branding
    path("branding/", WhiteLabelBrandingView.as_view(), name="white-label-branding"),
    path("branding/theme-preview/", ThemePreviewView.as_view(), name="white-label-theme-preview"),
    path("branding/css-variables/", branding_css_variables, name="white-label-css-variables"),
    path("branding/config/", school_branding_config, name="white-label-config"),

    # School Settings
    path("settings/", SchoolSettingsView.as_view(), name="white-label-settings"),

    # Domain Mapping
    path("domains/", DomainMappingListCreateView.as_view(), name="domain-mapping-list"),
    path("domains/<int:pk>/", DomainMappingDetailView.as_view(), name="domain-mapping-detail"),

    # Public Branding (for login page)
    path("public/<slug:subdomain>/", SchoolBrandingPublicView.as_view(), name="white-label-public"),

    # Audit Log
    path("audit/", WhiteLabelAuditLogView.as_view(), name="white-label-audit-list"),
    path("audit/<int:pk>/", WhiteLabelAuditLogDetailView.as_view(), name="white-label-audit-detail"),
]