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

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        details=details or {},
        ip_address=get_client_ip(request),
    )
