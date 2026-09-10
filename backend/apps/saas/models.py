"""Enterprise infrastructure models: feature flags, subscription, usage.

This app holds the lightweight SaaS "platform wiring" for the ERP:

  * ``FeatureFlag``        — kill-switches / staged rollouts, global or per
                            institution.
  * ``Plan`` / ``Subscription`` — the subscription *foundation* (no billing
                            provider integration yet, only the data + state
                            machine the billing layer will attach to).
  * ``DailyUsageSnapshot`` — daily per-institution usage counters filled by
                            ``collect_usage`` (a cron/management command) from
                            the in-cache event buffer.
"""

from django.db import models

from apps.schools.models import School


class FeatureFlag(models.Model):
    """A named, toggleable capability.

    A flag with ``institution=None`` is global; a row carrying an institution
    is an *override* for that tenant. ``feature_enabled()`` (see
    ``apps.saas.services``) resolves: per-institution override wins, then the
    global default, then ``False``.

    The ``name`` is namespaced (e.g. ``lms.grading_v2``) and new flags are
    *off* by default so a regression can never silently ship wide.
    """

    name = models.CharField(max_length=100, db_index=True)
    label = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    # None == global flag; set == per-institution override.
    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="feature_flags",
        null=True,
        blank=True,
    )

    enabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "institution_id"]
        verbose_name = "Feature flag"
        constraints = [
            # One global row per name.
            models.UniqueConstraint(
                fields=["name"],
                name="unique_feature_flag_global",
                condition=models.Q(institution__isnull=True),
            ),
            # One override row per (name, institution).
            models.UniqueConstraint(
                fields=["name", "institution"],
                name="unique_feature_flag_per_institution",
            ),
        ]

    def __str__(self):
        scope = "global" if self.institution_id is None else f"inst:{self.institution_id}"
        state = "ON" if self.enabled else "off"
        return f"{self.name} [{scope}] {state}"


class Plan(models.Model):
    """A purchasable subscription tier (foundation only, no billing link yet)."""

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # 0 / NULL means "unlimited" for that dimension.
    max_students = models.PositiveIntegerField(null=True, blank=True)
    max_staff = models.PositiveIntegerField(null=True, blank=True)
    max_storage_mb = models.PositiveIntegerField(null=True, blank=True)
    max_api_requests_per_day = models.PositiveIntegerField(null=True, blank=True)

    # Integer cents so no float money handling is ever needed.
    monthly_price_cents = models.PositiveIntegerField(default=0)

    features = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "code"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """The tenant's current subscription state.

    ``status`` lifecycle (foundation): ``trial`` -> ``active`` ->
    ``past_due`` / ``canceled``.
    """

    STATUS_CHOICES = [
        ("trial", "Trial"),
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
    ]

    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="trial",
    )

    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    seats_used = models.PositiveIntegerField(default=0)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.school.name} -> {self.plan.code} "
            f"({self.get_status_display()})"
        )

    @property
    def is_active_subscription(self):
        return self.status in ("trial", "active")


class DailyUsageSnapshot(models.Model):
    """Daily per-institution usage counters.

    Written by the ``collect_usage`` management command (single row per
    school/day, upserted), read by the platform analytics endpoints.
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="usage_snapshots",
    )
    date = models.DateField(db_index=True)

    logins = models.PositiveIntegerField(default=0)
    failed_logins = models.PositiveIntegerField(default=0)
    api_requests = models.PositiveIntegerField(default=0)

    students = models.PositiveIntegerField(default=0)
    staff = models.PositiveIntegerField(default=0)
    payments = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "school__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "date"],
                name="unique_daily_usage_per_school_date",
            )
        ]

    def __str__(self):
        return f"{self.school.name} {self.date} ({self.api_requests} req)"