from django.contrib.auth import get_user_model
from django.db import models

from apps.schools.models import School


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("login", "Login"),
        ("login_failed", "Login Failed"),
        ("institution_switched", "Institution Switched"),
        ("logout", "Logout"),
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("export", "Export"),
        ("permission_change", "Permission Change"),
        ("settings_change", "Settings Change"),
        ("password_reset", "Password Reset"),
        ("grade_publish", "Grade Publish"),
        ("grade_amendment", "Grade Amendment"),
        ("payment", "Payment"),
        ("payment_reversal", "Payment Reversal"),
        ("payment_refund", "Payment Refund"),
        ("invoice", "Invoice"),
        ("expense_posted", "Expense Posted"),
        ("concession_approved", "Concession Approved"),
        ("staff_leave_approved", "Staff Leave Approved"),
        ("staff_leave_rejected", "Staff Leave Rejected"),
        ("other", "Other"),
        ("student_transfer_initiated", "Student Transfer Initiated"),
        ("student_transfer_approved", "Student Transfer Approved"),
        ("student_transfer_rejected", "Student Transfer Rejected"),
        ("subscription_changed", "Subscription Changed"),
        ("feature_flag_changed", "Feature Flag Changed"),
        ("role_change", "Role Changed"),
        ("brute_force_detected", "Brute Force Detected"),
        ("api_key_created", "API Key Created"),
        ("ai_ask", "AI Ask"),
        ("ai_search", "AI Search"),
        ("ai_insight", "AI Insight"),
        ("ai_anomaly", "AI Anomaly Scan"),
        ("ai_draft", "AI Communication Draft"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    model_name = models.CharField(
        max_length=100,
        blank=True,
    )

    object_id = models.CharField(
        max_length=50,
        blank=True,
    )

    object_repr = models.CharField(
        max_length=255,
        blank=True,
    )

    details = models.JSONField(
        default=dict,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(
                fields=["user", "timestamp"],
                name="audit_user_time_idx",
            ),
            models.Index(
                fields=["action", "timestamp"],
                name="audit_action_time_idx",
            ),
            models.Index(
                fields=["institution", "timestamp"],
                name="audit_inst_time_idx",
            ),
            models.Index(
                fields=["model_name", "object_id"],
                name="audit_model_obj_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.get_action_display()} "
            f"{self.model_name} @ {self.timestamp}"
        )


ACTION_CHOICES = AuditLog.ACTION_CHOICES


def get_client_ip(request):
    if request is None:
        return None

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def record_audit(
    *,
    request=None,
    user=None,
    action,
    model_name="",
    object_id="",
    object_repr="",
    details=None,
):
    """Create an audit entry. `user` falls back to request.user."""
    if user is None and request is not None:
        user = getattr(request, "user", None)

    if user is not None and not user.is_authenticated:
        user = None

    institution = None
    if request is not None:
        institution = getattr(request, "institution", None)
    if institution is None and user is not None:
        institution = getattr(user, "institution", None)

    user_agent = ""
    if request is not None:
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        details=details or {},
        ip_address=get_client_ip(request),
        institution=institution,
        user_agent=user_agent,
    )
