from django.contrib import admin
from .models import WhiteLabelBranding, SchoolSettings, DomainMapping, WhiteLabelAuditLog


@admin.register(WhiteLabelBranding)
class WhiteLabelBrandingAdmin(admin.ModelAdmin):
    list_display = [
        "school",
        "subdomain",
        "primary_color",
        "secondary_color",
        "maintenance_mode",
        "allow_registration",
        "created_at",
        "updated_at",
    ]
    list_filter = [
        "maintenance_mode",
        "allow_registration",
        "login_show_powered_by",
        "receipt_show_qr",
        "created_at",
        "updated_at",
    ]
    search_fields = ["school__name", "subdomain", "login_title"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    fieldsets = (
        ("School", {"fields": ("school",)}),
        ("Colors", {
            "fields": (
                "primary_color", "secondary_color", "accent_color",
                "background_color", "surface_color", "text_primary",
                "text_secondary", "border_color", "error_color",
                "success_color", "warning_color",
            )
        }),
        ("Typography", {
            "fields": (
                "font_family", "font_family_mono",
                "font_size_base", "font_size_lg", "font_size_xl",
            )
        }),
        ("Border Radius & Spacing", {
            "fields": (
                "border_radius_sm", "border_radius_md", "border_radius_lg",
                "spacing_unit",
            )
        }),
        ("Logo & Favicon", {
            "fields": (
                "logo", "logo_dark", "favicon", "favicon_dark",
            )
        }),
        ("Login Page", {
            "fields": (
                "login_background_image", "login_background_color",
                "login_title", "login_subtitle", "login_show_powered_by",
                "login_custom_css",
            )
        }),
        ("Email Branding", {
            "fields": (
                "email_header_image", "email_footer_text", "email_from_name",
                "email_reply_to", "email_custom_css",
            )
        }),
        ("Document Branding", {
            "fields": (
                "document_header_text", "document_footer_text",
                "document_watermark", "certificate_border", "receipt_show_qr",
            )
        }),
        ("Domain & SEO", {
            "fields": (
                "subdomain", "meta_title", "meta_description", "og_image",
            )
        }),
        ("Maintenance", {
            "fields": (
                "maintenance_mode", "maintenance_message",
                "maintenance_allowed_ips", "allow_registration",
            )
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",),
        }),
    )


@admin.register(SchoolSettings)
class SchoolSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "school",
        "default_language",
        "default_timezone",
        "date_format",
        "time_format",
        "fee_grace_days",
        "fee_late_fee_percent",
        "created_at",
    ]
    list_filter = [
        "default_language",
        "time_format",
        "date_format",
        "created_at",
    ]
    search_fields = ["school__name"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    fieldsets = (
        ("School", {"fields": ("school",)}),
        ("Modules", {"fields": ("enabled_modules",)}),
        ("Localization", {
            "fields": (
                "default_language", "default_timezone", "date_format",
                "time_format", "first_day_of_week",
            )
        }),
        ("Attendance", {
            "fields": (
                "attendance_late_threshold_minutes",
                "attendance_half_day_threshold_minutes",
                "attendance_auto_mark_absent_after_minutes",
            )
        }),
        ("Fees", {
            "fields": (
                "fee_grace_days", "fee_late_fee_percent", "fee_late_fee_flat",
            )
        }),
        ("Communication", {
            "fields": ("default_notification_channels", "sms_sender_id"),
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",),
        }),
    )


@admin.register(DomainMapping)
class DomainMappingAdmin(admin.ModelAdmin):
    list_display = [
        "domain",
        "school",
        "is_primary",
        "is_verified",
        "ssl_enabled",
        "ssl_expires_at",
        "created_at",
    ]
    list_filter = ["is_primary", "is_verified", "ssl_enabled"]
    search_fields = ["domain", "school__name"]
    readonly_fields = ["created_at", "updated_at", "is_verified"]
    fieldsets = (
        ("Domain", {"fields": ("school", "domain", "is_primary")}),
        ("SSL", {
            "fields": (
                "is_verified", "ssl_enabled", "ssl_certificate",
                "ssl_private_key", "ssl_expires_at",
            )
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(WhiteLabelAuditLog)
class WhiteLabelAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "school",
        "user",
        "action",
        "model_name",
        "object_id",
        "created_at",
    ]
    list_filter = ["action", "model_name", "created_at"]
    search_fields = [
        "school__name", "user__username", "model_name",
        "object_id", "object_repr",
    ]
    readonly_fields = [
        "school", "user", "action", "model_name", "object_id",
        "object_repr", "changes", "ip_address", "user_agent", "created_at",
    ]
    ordering = ["-created_at"]