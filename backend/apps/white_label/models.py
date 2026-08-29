from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class WhiteLabelBranding(models.Model):
    """White-label branding configuration for a School/tenant."""

    school = models.OneToOneField(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="white_label_branding",
    )

    # Logo & Favicon
    logo = models.ImageField(
        upload_to="white_label/logos/",
        blank=True,
        null=True,
        help_text="Main logo (recommended: 200x60px, transparent background)",
    )
    logo_dark = models.ImageField(
        upload_to="white_label/logos/",
        blank=True,
        null=True,
        help_text="Dark mode logo variant",
    )
    favicon = models.ImageField(
        upload_to="white_label/favicons/",
        blank=True,
        null=True,
        help_text="Favicon (recommended: 32x32px, .ico or .png)",
    )

    # Color Palette
    primary_color = models.CharField(
        max_length=7,
        default="#2563EB",
        help_text="Primary brand color (hex, e.g., #2563EB)",
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#0F172A",
        help_text="Secondary brand color (hex)",
    )
    accent_color = models.CharField(
        max_length=7,
        default="#10B981",
        help_text="Accent color for CTAs and highlights (hex)",
    )
    background_color = models.CharField(
        max_length=7,
        default="#FFFFFF",
        help_text="Background color (hex)",
    )
    surface_color = models.CharField(
        max_length=7,
        default="#F8FAFC",
        help_text="Card/surface background color (hex)",
    )
    text_primary = models.CharField(
        max_length=7,
        default="#0F172A",
        help_text="Primary text color (hex)",
    )
    text_secondary = models.CharField(
        max_length=7,
        default="#64748B",
        help_text="Secondary text color (hex)",
    )
    border_color = models.CharField(
        max_length=7,
        default="#E2E8F0",
        help_text="Border color (hex)",
    )
    error_color = models.CharField(
        max_length=7,
        default="#EF4444",
        help_text="Error/danger color (hex)",
    )
    success_color = models.CharField(
        max_length=7,
        default="#10B981",
        help_text="Success color (hex)",
    )
    warning_color = models.CharField(
        max_length=7,
        default="#F59E0B",
        help_text="Warning color (hex)",
    )

    # Typography
    font_family = models.CharField(
        max_length=100,
        default="Inter, system-ui, sans-serif",
        help_text="CSS font-family string (e.g., 'Inter, system-ui, sans-serif')",
    )
    font_family_mono = models.CharField(
        max_length=100,
        default="JetBrains Mono, monospace",
        help_text="Monospace font for code/technical content",
    )
    font_size_base = models.PositiveSmallIntegerField(
        default=14,
        help_text="Base font size in pixels",
    )
    font_size_lg = models.PositiveSmallIntegerField(
        default=18,
        help_text="Large font size in pixels",
    )
    font_size_xl = models.PositiveSmallIntegerField(
        default=24,
        help_text="Extra large font size in pixels",
    )

    # Border Radius & Spacing
    border_radius_sm = models.PositiveSmallIntegerField(
        default=4,
        help_text="Small border radius in pixels",
    )
    border_radius_md = models.PositiveSmallIntegerField(
        default=8,
        help_text="Medium border radius in pixels",
    )
    border_radius_lg = models.PositiveSmallIntegerField(
        default=12,
        help_text="Large border radius in pixels",
    )
    spacing_unit = models.PositiveSmallIntegerField(
        default=4,
        help_text="Base spacing unit in pixels",
    )

    # Login Page Customization
    login_background_image = models.ImageField(
        upload_to="white_label/login/",
        blank=True,
        null=True,
        help_text="Custom background image for login page",
    )
    login_background_color = models.CharField(
        max_length=7,
        default="#F8FAFC",
        help_text="Login page background color (hex)",
    )
    login_title = models.CharField(
        max_length=200,
        blank=True,
        default="Welcome to Your School",
        help_text="Title shown on login page",
    )
    login_subtitle = models.TextField(
        blank=True,
        default="Sign in to access your account",
        help_text="Subtitle shown on login page",
    )
    login_show_powered_by = models.BooleanField(
        default=True,
        help_text="Show 'Powered by' footer on login page",
    )
    login_custom_css = models.TextField(
        blank=True,
        help_text="Custom CSS injected into login page",
    )

    # Email Branding
    email_header_image = models.ImageField(
        upload_to="white_label/email/",
        blank=True,
        null=True,
        help_text="Header image for emails (recommended: 600x150px)",
    )
    email_footer_text = models.TextField(
        blank=True,
        default="This email was sent by {school_name}. If you have any questions, please contact us.",
        help_text="Default footer text for emails. Use {school_name} placeholder.",
    )
    email_from_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="From name for emails (defaults to school name)",
    )
    email_reply_to = models.EmailField(
        blank=True,
        help_text="Reply-to email address",
    )
    email_custom_css = models.TextField(
        blank=True,
        help_text="Custom CSS for email templates",
    )

    # Document Branding (Certificates, Receipts, ID Cards)
    document_header_text = models.CharField(
        max_length=200,
        blank=True,
        default="Official Document",
        help_text="Header text for certificates/receipts/ID cards",
    )
    document_footer_text = models.TextField(
        blank=True,
        default="This document is generated electronically and is valid without a signature.",
        help_text="Footer text for documents",
    )
    document_watermark = models.ImageField(
        upload_to="white_label/watermarks/",
        blank=True,
        null=True,
        help_text="Watermark image for documents (transparent PNG recommended)",
    )
    certificate_border = models.ImageField(
        upload_to="white_label/certificates/",
        blank=True,
        null=True,
        help_text="Border image for certificates",
    )
    receipt_show_qr = models.BooleanField(
        default=True,
        help_text="Show QR code on receipts for verification",
    )

    # Domain & SEO
    subdomain = models.SlugField(
        max_length=63,
        unique=True,
        blank=True,
        null=True,
        help_text="Subdomain for this school (e.g., 'sunrise' for sunrise.example.com)",
    )
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Default meta title for SEO",
    )
    meta_description = models.TextField(
        blank=True,
        help_text="Default meta description for SEO",
    )
    og_image = models.ImageField(
        upload_to="white_label/og/",
        blank=True,
        null=True,
        help_text="Open Graph image for social sharing (1200x630px)",
    )
    favicon_dark = models.ImageField(
        upload_to="white_label/favicons/",
        blank=True,
        null=True,
        help_text="Dark mode favicon",
    )

    # Maintenance / Feature Flags
    maintenance_mode = models.BooleanField(
        default=False,
        help_text="Enable maintenance mode (shows maintenance page)",
    )
    maintenance_message = models.TextField(
        blank=True,
        default="We are performing scheduled maintenance. Please check back later.",
        help_text="Message shown during maintenance mode",
    )
    allow_registration = models.BooleanField(
        default=False,
        help_text="Allow self-registration for new users",
    )
    maintenance_allowed_ips = models.JSONField(
        default=list,
        blank=True,
        help_text="List of IP addresses allowed during maintenance",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_white_label_branding",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_white_label_branding",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Branding for {self.school.name}"

    def clean(self):
        errors = {}
        if self.primary_color and not self.primary_color.startswith("#"):
            errors["primary_color"] = "Color must be a valid hex code (e.g., #2563EB)"
        if self.subdomain and not self.subdomain.isalnum() and "-" not in self.subdomain:
            errors["subdomain"] = "Subdomain must be alphanumeric with hyphens only"
        if self.subdomain and len(self.subdomain) > 63:
            errors["subdomain"] = "Subdomain must be 63 characters or less"
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.subdomain and self.school_id:
            base = slugify(self.school.name)[:63] or "school"
            candidate = base
            suffix = 2
            while type(self).objects.filter(subdomain=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base[:63 - len(str(suffix)) - 1]}-{suffix}"
                suffix += 1
            self.subdomain = candidate
        super().save(*args, **kwargs)

    @property
    def css_variables(self):
        """Generate CSS custom properties for the theme."""
        return {
            "--color-primary": self.primary_color,
            "--color-secondary": self.secondary_color,
            "--color-accent": self.accent_color,
            "--color-background": self.background_color,
            "--color-surface": self.surface_color,
            "--color-text-primary": self.text_primary,
            "--color-text-secondary": self.text_secondary,
            "--color-border": self.border_color,
            "--color-error": self.error_color,
            "--color-success": self.success_color,
            "--color-warning": self.warning_color,
            "--font-family": self.font_family,
            "--font-family-mono": self.font_family_mono,
            "--font-size-base": f"{self.font_size_base}px",
            "--font-size-lg": f"{self.font_size_lg}px",
            "--font-size-xl": f"{self.font_size_xl}px",
            "--border-radius-sm": f"{self.border_radius_sm}px",
            "--border-radius-md": f"{self.border_radius_md}px",
            "--border-radius-lg": f"{self.border_radius_lg}px",
            "--spacing-unit": f"{self.spacing_unit}px",
        }

    def to_dict(self):
        """Serialize branding config for API response."""
        return {
            "id": self.id,
            "school_id": self.school_id,
            "colors": {
                "primary": self.primary_color,
                "secondary": self.secondary_color,
                "accent": self.accent_color,
                "background": self.background_color,
                "surface": self.surface_color,
                "text_primary": self.text_primary,
                "text_secondary": self.text_secondary,
                "border": self.border_color,
                "error": self.error_color,
                "success": self.success_color,
                "warning": self.warning_color,
            },
            "typography": {
                "font_family": self.font_family,
                "font_family_mono": self.font_family_mono,
                "font_size_base": self.font_size_base,
                "font_size_lg": self.font_size_lg,
                "font_size_xl": self.font_size_xl,
            },
            "border_radius": {
                "sm": self.border_radius_sm,
                "md": self.border_radius_md,
                "lg": self.border_radius_lg,
            },
            "spacing_unit": self.spacing_unit,
            "logo": self.logo.url if self.logo else None,
            "logo_dark": self.logo_dark.url if self.logo_dark else None,
            "favicon": self.favicon.url if self.favicon else None,
            "login": {
                "background_image": self.login_background_image.url if self.login_background_image else None,
                "background_color": self.login_background_color,
                "title": self.login_title,
                "subtitle": self.login_subtitle,
                "show_powered_by": self.login_show_powered_by,
                "custom_css": self.login_custom_css,
            },
            "email": {
                "header_image": self.email_header_image.url if self.email_header_image else None,
                "footer_text": self.email_footer_text,
                "from_name": self.email_from_name,
                "reply_to": self.email_reply_to,
                "custom_css": self.email_custom_css,
            },
            "document": {
                "header_text": self.document_header_text,
                "footer_text": self.document_footer_text,
                "watermark": self.document_watermark.url if self.document_watermark else None,
                "certificate_border": self.certificate_border.url if self.certificate_border else None,
                "receipt_show_qr": self.receipt_show_qr,
            },
            "subdomain": self.subdomain,
            "seo": {
                "meta_title": self.meta_title,
                "meta_description": self.meta_description,
                "og_image": self.og_image.url if self.og_image else None,
            },
            "maintenance": {
                "enabled": self.maintenance_mode,
                "message": self.maintenance_message,
                "allowed_ips": self.maintenance_allowed_ips,
            },
            "allow_registration": self.allow_registration,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SchoolSettings(models.Model):
    """Additional school settings for white-label configuration."""

    school = models.OneToOneField(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="white_label_settings",
    )

    # Module toggles (granular control over enabled modules)
    MODULES = [
        ("students", "Students"),
        ("teachers", "Teachers"),
        ("attendance", "Attendance"),
        ("exams", "Exams"),
        ("fees", "Fees & Finance"),
        ("attendance_staff", "Staff Attendance"),
        ("library", "Library"),
        ("transport", "Transport"),
        ("inventory", "Inventory"),
        ("hr", "HR"),
        ("payroll", "Payroll"),
        ("communication", "Communication"),
        ("library", "Library"),
        ("timetable", "Timetable"),
        ("lms", "LMS"),
        ("reports", "Reports"),
        ("documents", "Documents"),
        ("helpdesk", "Helpdesk"),
        ("visitors", "Visitors"),
        ("digital_ids", "Digital IDs"),
        ("workflow", "Workflow"),
        ("dashboard", "Dashboards"),
        ("portal_teacher", "Teacher Portal"),
        ("portal_student", "Student Portal"),
        ("portal_parent", "Parent Portal"),
    ]

    enabled_modules = models.JSONField(
        default=list,
        blank=True,
        help_text="List of enabled module keys. Empty = all modules enabled.",
    )

    # Default settings
    default_language = models.CharField(
        max_length=10,
        default="en",
        choices=[
            ("en", "English"),
            ("ur", "Urdu"),
            ("ar", "Arabic"),
            ("fr", "French"),
            ("es", "Spanish"),
        ],
    )
    default_timezone = models.CharField(
        max_length=64,
        default="UTC",
        help_text="IANA timezone (e.g., Asia/Karachi)",
    )
    date_format = models.CharField(
        max_length=20,
        default="DD/MM/YYYY",
        choices=[
            ("DD/MM/YYYY", "DD/MM/YYYY"),
            ("MM/DD/YYYY", "MM/DD/YYYY"),
            ("YYYY-MM-DD", "YYYY-MM-DD"),
        ],
    )
    time_format = models.CharField(
        max_length=10,
        default="12h",
        choices=[("12h", "12-hour"), ("24h", "24-hour")],
    )
    first_day_of_week = models.PositiveSmallIntegerField(
        default=0,
        help_text="0=Sunday, 1=Monday, ... 6=Saturday",
    )

    # Attendance settings
    attendance_late_threshold_minutes = models.PositiveSmallIntegerField(
        default=15,
        help_text="Minutes after class start to mark as late",
    )
    attendance_half_day_threshold_minutes = models.PositiveSmallIntegerField(
        default=120,
        help_text="Minutes present required for half-day (0 = disabled)",
    )
    attendance_auto_mark_absent_after_minutes = models.PositiveSmallIntegerField(
        default=60,
        help_text="Mark absent after this many minutes of no check-in",
    )

    # Fee settings
    fee_grace_days = models.PositiveSmallIntegerField(
        default=5,
        help_text="Grace days after due date before late fee applies",
    )
    fee_late_fee_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Late fee percentage (0 = flat fee only)",
    )
    fee_late_fee_flat = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Flat late fee amount",
    )

    # Communication defaults
    default_notification_channels = models.JSONField(
        default=list,
        blank=True,
        help_text="Default channels: ['in_app', 'email', 'sms', 'push']",
    )
    sms_sender_id = models.CharField(
        max_length=11,
        blank=True,
        help_text="SMS sender ID (max 11 chars)",
    )

    # Created/Updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_white_label_settings",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_white_label_settings",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Settings for {self.school.name}"


class DomainMapping(models.Model):
    """Maps custom domains/subdomains to schools for tenant resolution."""

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="domain_mappings",
    )
    domain = models.CharField(
        max_length=255,
        help_text="Full domain (e.g., school.example.com) or subdomain (e.g., sunrise)",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary domain for this school",
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Domain has been verified (DNS/SSL)",
    )
    ssl_enabled = models.BooleanField(
        default=False,
        help_text="SSL certificate is provisioned",
    )
    ssl_certificate = models.TextField(
        blank=True,
        help_text="SSL certificate (PEM format)",
    )
    ssl_private_key = models.TextField(
        blank=True,
        help_text="SSL private key (PEM format)",
    )
    ssl_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="SSL certificate expiry",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_primary", "domain"]
        constraints = [
            models.UniqueConstraint(
                fields=["domain"],
                name="unique_domain_mapping",
            ),
        ]

    def __str__(self):
        return f"{self.domain} -> {self.school.name}"


class WhiteLabelAuditLog(models.Model):
    """Audit log for white-label configuration changes."""

    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("activate", "Activate"),
        ("deactivate", "Deactivate"),
    ]

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="white_label_audit_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="white_label_audit_logs",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.TextField(blank=True)
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON diff of changes (old -> new)",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} {self.model_name} ({self.object_id}) by {self.user}"