from django.db import models

from apps.schools.models import Campus


class AssetCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "asset categories"

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Asset(models.Model):
    STATUS_CHOICES = [
        ("in_stock", "In Stock"),
        ("in_use", "In Use"),
        ("maintenance", "Under Maintenance"),
        ("expired", "Expired"),
        ("retired", "Retired"),
    ]

    name = models.CharField(max_length=200)
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
    )
    code = models.CharField(max_length=50, unique=True, blank=True)
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    purchase_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="in_stock",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    @property
    def total_value(self):
        return self.quantity * self.unit_cost

    def save(self, *args, **kwargs):
        if not self.code:
            from django.utils import timezone

            self.code = (
                f"A{timezone.now().strftime('%Y%m%d')}-"
                f"{self.__class__.objects.count() + 1:03d}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AssetAssignment(models.Model):
    ASSIGNEE_CHOICES = [
        ("teacher", "Teacher"),
        ("staff", "Staff"),
        ("student", "Student"),
        ("department", "Department"),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    assignee_type = models.CharField(
        max_length=16,
        choices=ASSIGNEE_CHOICES,
        default="staff",
    )
    assignee_name = models.CharField(max_length=200)
    assigned_to = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_assignments",
    )
    quantity = models.PositiveIntegerField(default=1)
    assigned_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-assigned_date"]

    def __str__(self):
        return f"{self.asset.name} -> {self.assignee_name}"


class MaintenanceRecord(models.Model):
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="maintenance_records",
    )
    date = models.DateField()
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    description = models.TextField(blank=True)
    performed_by = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=16,
        choices=[
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
        ],
        default="scheduled",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.asset.name} - {self.date}"
