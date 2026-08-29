"""Zero-code workflow & approval engine.

Models
------

- :class:`WorkflowDefinition` — configuration for one business object:
  its allowed states, the transitions between them and, optionally, an
  ordered queue of roles that must approve before the object moves on.
- :class:`WorkflowInstance` — a live workflow applied to one object
  (``object_type`` + ``object_id``).
- :class:`WorkflowApproval` — one step in an approval queue.
- :class:`WorkflowTransition` — an append-only audit log of every action
  (actor, timestamps, previous/new state, comment).

State machines and approval queues are data, not code: definitions are
seeded by ``manage.py seed_workflow_definitions`` and any new workflow is
just a new definition row.
"""

from django.conf import settings
from django.db import models


class WorkflowDefinition(models.Model):
    """Reusable workflow configuration for a business object type."""

    name = models.CharField(max_length=150)
    slug = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Stable key used by the engine and API, e.g. 'hr.leave.request'.",
    )
    object_type = models.CharField(
        max_length=120,
        db_index=True,
        help_text="Dot path of the business object, e.g. 'hr.leaverequest'.",
    )
    states = models.JSONField(
        default=list,
        help_text="Valid states, e.g. ['draft', 'pending_approval', 'approved', 'rejected'].",
    )
    initial_state = models.CharField(max_length=50)
    approval_steps = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Ordered role slugs. Each step must approve in sequence before "
            "'approve' moves the object to its target state."
        ),
    )
    transitions = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Map action -> {'from': [...], 'to': ..., 'roles': [...]}. "
            "'approve'/'reject' walk the approval_steps queue; every other "
            "action is a plain state hop."
        ),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("object_type", "slug")
        verbose_name = "Workflow definition"
        constraints = [
            models.UniqueConstraint(
                fields=("object_type", "slug"),
                name="uniq_workflow_definition_object_slug",
            ),
        ]

    def __str__(self):
        return self.name

    def is_terminal(self, state):
        """A state is terminal when no transition leaves it."""
        return not any(
            state in (transition.get("from") or [])
            for transition in self.transitions.values()
        )


class WorkflowInstance(models.Model):
    """A running workflow attached to one business object."""

    definition = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.PROTECT,
        related_name="instances",
    )
    institution = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="workflow_instances",
        null=True,
        blank=True,
    )
    campus = models.ForeignKey(
        "schools.Campus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_instances",
    )
    object_type = models.CharField(max_length=120, db_index=True)
    object_id = models.PositiveBigIntegerField(db_index=True)
    current_state = models.CharField(max_length=50)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_workflows",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Workflow instance"
        indexes = [
            models.Index(fields=("object_type", "object_id")),
        ]

    def __str__(self):
        return f"{self.definition.slug} #{self.object_id} [{self.current_state}]"

    @property
    def is_terminal(self):
        return self.definition.is_terminal(self.current_state)


class WorkflowApproval(models.Model):
    """One step of an approval queue, keyed to a role."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SKIPPED = "skipped", "Skipped"

    instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name="approvals",
    )
    sequence = models.PositiveIntegerField(default=0)
    role = models.CharField(max_length=50)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_approvals",
    )
    comment = models.TextField(blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sequence",)
        verbose_name = "Workflow approval"

    def __str__(self):
        return f"{self.instance_id} step {self.sequence} ({self.role})"


class WorkflowTransition(models.Model):
    """Append-only history of actions performed on a workflow instance."""

    instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name="transitions",
    )
    action = models.CharField(max_length=50)
    from_state = models.CharField(max_length=50, blank=True, default="")
    to_state = models.CharField(max_length=50)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_actions",
    )
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Workflow transition"

    def __str__(self):
        return f"{self.instance_id}: {self.action} -> {self.to_state}"