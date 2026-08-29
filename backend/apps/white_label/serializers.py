from rest_framework import serializers
from apps.white_label.models import (
    WhiteLabelBranding,
    SchoolSettings,
    DomainMapping,
    WhiteLabelAuditLog,
)


class WhiteLabelBrandingSerializer(serializers.ModelSerializer):
    css_variables = serializers.SerializerMethodField()
    logo_url = serializers.ImageField(source="logo", read_only=True)
    logo_dark_url = serializers.ImageField(source="logo_dark", read_only=True)
    favicon_url = serializers.ImageField(source="favicon", read_only=True)
    login_background_image_url = serializers.ImageField(
        source="login_background_image", read_only=True
    )
    email_header_image_url = serializers.ImageField(
        source="email_header_image", read_only=True
    )
    document_watermark_url = serializers.ImageField(
        source="document_watermark", read_only=True
    )
    certificate_border_url = serializers.ImageField(
        source="certificate_border", read_only=True
    )
    og_image_url = serializers.ImageField(source="og_image", read_only=True)
    favicon_dark_url = serializers.ImageField(source="favicon_dark", read_only=True)

    class Meta:
        model = WhiteLabelBranding
        fields = [
            "id",
            "school_id",
            # Colors
            "primary_color",
            "secondary_color",
            "accent_color",
            "background_color",
            "surface_color",
            "text_primary",
            "text_secondary",
            "border_color",
            "error_color",
            "success_color",
            "warning_color",
            # Typography
            "font_family",
            "font_family_mono",
            "font_size_base",
            "font_size_lg",
            "font_size_xl",
            # Border Radius & Spacing
            "border_radius_sm",
            "border_radius_md",
            "border_radius_lg",
            "spacing_unit",
            # Logo & Favicon
            "logo",
            "logo_url",
            "logo_dark",
            "logo_dark_url",
            "favicon",
            "favicon_url",
            "favicon_dark",
            "favicon_dark_url",
            # Login Page
            "login_background_image",
            "login_background_image_url",
            "login_background_color",
            "login_title",
            "login_subtitle",
            "login_show_powered_by",
            "login_custom_css",
            # Email
            "email_header_image",
            "email_header_image_url",
            "email_footer_text",
            "email_from_name",
            "email_reply_to",
            "email_custom_css",
            # Document
            "document_header_text",
            "document_footer_text",
            "document_watermark",
            "document_watermark_url",
            "certificate_border",
            "certificate_border_url",
            "receipt_show_qr",
            # Domain & SEO
            "subdomain",
            "meta_title",
            "meta_description",
            "og_image",
            "og_image_url",
            "favicon_dark",
            "favicon_dark_url",
            # Maintenance
            "maintenance_mode",
            "maintenance_message",
            "maintenance_allowed_ips",
            "allow_registration",
            # Computed
            "css_variables",
            # Meta
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "school_id",
            "css_variables",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def get_css_variables(self, obj):
        return obj.css_variables


class WhiteLabelBrandingCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhiteLabelBranding
        fields = [
            "primary_color",
            "secondary_color",
            "accent_color",
            "background_color",
            "surface_color",
            "text_primary",
            "text_secondary",
            "border_color",
            "error_color",
            "success_color",
            "warning_color",
            "font_family",
            "font_family_mono",
            "font_size_base",
            "font_size_lg",
            "font_size_xl",
            "border_radius_sm",
            "border_radius_md",
            "border_radius_lg",
            "spacing_unit",
            "logo",
            "logo_dark",
            "favicon",
            "login_background_image",
            "login_background_color",
            "login_title",
            "login_subtitle",
            "login_show_powered_by",
            "login_custom_css",
            "email_header_image",
            "email_footer_text",
            "email_from_name",
            "email_reply_to",
            "email_custom_css",
            "document_header_text",
            "document_footer_text",
            "document_watermark",
            "certificate_border",
            "receipt_show_qr",
            "subdomain",
            "meta_title",
            "meta_description",
            "og_image",
            "favicon_dark",
            "maintenance_mode",
            "maintenance_message",
            "maintenance_allowed_ips",
            "allow_registration",
        ]

    def validate_primary_color(self, value):
        if value and not value.startswith("#"):
            raise serializers.ValidationError("Color must be a valid hex code (e.g., #2563EB)")
        return value

    def validate_subdomain(self, value):
        if value and not value.replace("-", "").isalnum():
            raise serializers.ValidationError("Subdomain must be alphanumeric with hyphens only")
        if value and len(value) > 63:
            raise serializers.ValidationError("Subdomain must be 63 characters or less")
        return value


class SchoolSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolSettings
        fields = [
            "id",
            "school_id",
            "enabled_modules",
            "default_language",
            "default_timezone",
            "date_format",
            "time_format",
            "first_day_of_week",
            "attendance_late_threshold_minutes",
            "attendance_half_day_threshold_minutes",
            "attendance_auto_mark_absent_after_minutes",
            "fee_grace_days",
            "fee_late_fee_percent",
            "fee_late_fee_flat",
            "default_notification_channels",
            "sms_sender_id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "school_id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]


class SchoolSettingsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolSettings
        fields = [
            "enabled_modules",
            "default_language",
            "default_timezone",
            "date_format",
            "time_format",
            "first_day_of_week",
            "attendance_late_threshold_minutes",
            "attendance_half_day_threshold_minutes",
            "attendance_auto_mark_absent_after_minutes",
            "fee_grace_days",
            "fee_late_fee_percent",
            "fee_late_fee_flat",
            "default_notification_channels",
            "sms_sender_id",
        ]


class DomainMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainMapping
        fields = [
            "id",
            "school_id",
            "domain",
            "is_primary",
            "is_verified",
            "ssl_enabled",
            "ssl_certificate",
            "ssl_private_key",
            "ssl_expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_id", "created_at", "updated_at", "is_verified"]


class DomainMappingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainMapping
        fields = ["id", "domain", "is_primary"]


class WhiteLabelAuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = WhiteLabelAuditLog
        fields = [
            "id",
            "school",
            "user",
            "user_name",
            "action",
            "model_name",
            "object_id",
            "object_repr",
            "changes",
            "ip_address",
            "user_agent",
            "created_at",
        ]
        read_only_fields = fields


class BrandingPreviewSerializer(serializers.Serializer):
    """Serializer for branding preview endpoint."""
    colors = serializers.DictField()
    typography = serializers.DictField()
    border_radius = serializers.DictField()
    spacing_unit = serializers.IntegerField()
    logo = serializers.URLField(allow_null=True)
    logo_dark = serializers.URLField(allow_null=True)
    favicon = serializers.URLField(allow_null=True)
    login = serializers.DictField()
    email = serializers.DictField()
    document = serializers.DictField()
    subdomain = serializers.CharField(allow_null=True)
    seo = serializers.DictField()
    maintenance = serializers.DictField()
    allow_registration = serializers.BooleanField()


class ThemePreviewSerializer(serializers.Serializer):
    """Lightweight theme preview for login page preview."""
    css_variables = serializers.DictField()
    logo_url = serializers.URLField(allow_null=True)
    favicon_url = serializers.URLField(allow_null=True)
    login_background_image_url = serializers.URLField(allow_null=True)
    login_title = serializers.CharField()
    login_subtitle = serializers.CharField()
    login_background_color = serializers.CharField()