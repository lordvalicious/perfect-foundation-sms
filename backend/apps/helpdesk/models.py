from django.db import models

from apps.schools.models import School


class TicketCategory(models.Model):
    """Helpdesk ticket categories (IT, Fees, Transport, Facilities...)."""

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="ticket_categories",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    sort_order = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "ticket categories"
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="unique_ticket_category_per_institution",
            )
        ]

    def __str__(self):
        return self.name


class SupportTicket(models.Model):
    """A support / complaint ticket raised by a member of the school."""

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="helpdesk_tickets",
    )

    campus = models.ForeignKey(
        "schools.Campus",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="helpdesk_tickets",
    )

    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )

    subject = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="helpdesk_tickets",
    )

    assignee = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )

    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["institution", "status"]),
            models.Index(fields=["institution", "priority"]),
        ]

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"


class TicketMessage(models.Model):
    """A message in a ticket thread (staff-to-staff or member-facing)."""

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_messages",
    )

    body = models.TextField()

    # Internal notes are visible to staff only, never to the reporter.
    is_internal = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message on {self.ticket_id} by {self.author_id}"