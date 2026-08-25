from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import Campus, School
from apps.students.models import Student


class Hostel(models.Model):
    """A boarding house on a campus."""

    GENDER_CHOICES = [
        ("boys", "Boys"),
        ("girls", "Girls"),
        ("mixed", "Mixed"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="hostels",
        null=True,
        blank=True,
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="hostels",
    )

    name = models.CharField(max_length=150)
    warden = models.CharField(max_length=150, blank=True)
    gender = models.CharField(
        max_length=8,
        choices=GENDER_CHOICES,
        default="mixed",
    )
    address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def total_capacity(self):
        return sum(room.capacity for room in self.rooms.all())

    @property
    def occupied(self):
        return self.allocated_students.count()


class Room(models.Model):
    hostel = models.ForeignKey(
        Hostel,
        on_delete=models.CASCADE,
        related_name="rooms",
    )
    room_number = models.CharField(max_length=30)
    capacity = models.PositiveSmallIntegerField(default=4)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["room_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["hostel", "room_number"],
                name="unique_room_per_hostel",
            )
        ]

    def __str__(self):
        return f"{self.hostel.name} - {self.room_number}"

    @property
    def occupied(self):
        return self.allocations.filter(status="active").count()

    @property
    def is_full(self):
        return self.occupied >= self.capacity


class Allocation(models.Model):
    """A student living in a room for a period."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("vacated", "Vacated"),
    ]

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="hostel_allocations",
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def clean(self):
        if self.room_id and self.room.is_full and self.status == "active":
            active_count = (
                Allocation.objects.filter(
                    room=self.room, status="active"
                )
                .exclude(pk=self.pk or 0)
                .count()
            )

            if active_count >= self.room.capacity:
                raise ValidationError(
                    {"room": "This room is already full."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} in {self.room}"
