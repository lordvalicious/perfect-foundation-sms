from django.conf import settings
from django.db import models

from apps.schools.models import Campus, School
from apps.students.models import Student


class HealthRecord(models.Model):
    """A clinic visit, screening, allergy note or vaccination entry."""

    TYPE_CHOICES = [
        ("checkup", "General Checkup"),
        ("illness", "Illness"),
        ("injury", "Injury / First Aid"),
        ("allergy", "Allergy Note"),
        ("vaccination", "Vaccination"),
        ("screening", "Screening (vision/hearing)"),
        ("other", "Other"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="health_records",
        null=True,
        blank=True,
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="health_records",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="health_records",
    )

    record_type = models.CharField(
        max_length=16,
        choices=TYPE_CHOICES,
        default="checkup",
    )

    record_date = models.DateField()

    notes = models.TextField(blank=True)

    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
    )
    temperature_c = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    treated_by = models.CharField(max_length=120, blank=True)

    follow_up_date = models.DateField(null=True, blank=True)

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_health_records",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-record_date", "-id"]

    def __str__(self):
        return (
            f"{self.student.full_name} - "
            f"{self.get_record_type_display()} {self.record_date}"
        )

    @property
    def bmi(self):
        if not self.height_cm or not self.weight_kg:
            return None

        height_m = float(self.height_cm) / 100

        if height_m <= 0:
            return None

        return round(float(self.weight_kg) / (height_m ** 2), 1)
