from django.core.exceptions import ValidationError
from django.db import models


class Vehicle(models.Model):
    STATUS_CHOICES = [
        ("operational", "Operational"),
        ("maintenance", "In Maintenance"),
        ("out_of_service", "Out of Service"),
    ]

    plate_number = models.CharField(
        max_length=32,
        unique=True,
    )
    model = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=30)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="operational",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["plate_number"]

    def __str__(self):
        return self.plate_number


class Driver(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=64)
    phone = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.full_name


class Route(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="routes",
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="routes",
    )
    start_point = models.CharField(max_length=200, blank=True)
    end_point = models.CharField(max_length=200, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RouteStop(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="stops",
    )
    name = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    time = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ["route", "order"]

    def __str__(self):
        return f"{self.route.name} - {self.name}"


class TransportAssignment(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("ended", "Ended"),
    ]

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="transport_assignments",
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    stop = models.ForeignKey(
        RouteStop,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments",
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.stop_id and self.stop.route_id != self.route_id:
            raise ValidationError(
                {"stop": "The stop must belong to the selected route."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.route.name}"
