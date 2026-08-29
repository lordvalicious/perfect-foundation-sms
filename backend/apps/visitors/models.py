from django.db import models

from apps.schools.models import School


class Visitor(models.Model):
    """A visitor logged at the gate (check-in / check-out)."""

    STATUS_CHOICES = [
        ("checked_in", "Checked In"),
        ("checked_out", "Checked Out"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="visitors",
    )

    campus = models.ForeignKey(
        "schools.Campus",
        on_delete=models.PROTECT,
        related_name="visitors",
    )

    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    id_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="National ID / CNIC if provided at the gate.",
    )
    company = models.CharField(max_length=120, blank=True)
    vehicle_number = models.CharField(max_length=20, blank=True)

    purpose = models.CharField(max_length=200, blank=True)
    meeting_party = models.CharField(
        max_length=120,
        blank=True,
        help_text="Who they came to see, e.g. Principal - Mr. Khan.",
    )

    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)

    badge_number = models.CharField(max_length=40)

    photo = models.ImageField(
        upload_to="visitors/",
        blank=True,
        null=True,
    )

    notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="checked_in",
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visitor_logs",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-check_in"]
        indexes = [
            models.Index(fields=["institution", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "badge_number"],
                name="unique_visitor_badge_per_institution",
            )
        ]

    @property
    def is_active(self):
        return self.status == "checked_in" and self.check_out is None

    def __str__(self):
        return f"{self.full_name} ({self.badge_number})"