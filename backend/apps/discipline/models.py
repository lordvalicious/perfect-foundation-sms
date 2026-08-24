from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import Campus, School


class Incident(models.Model):
    """A behaviour incident recorded against a student."""

    SEVERITY_CHOICES = [
        ("minor", "Minor"),
        ("moderate", "Moderate"),
        ("major", "Major"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("action_taken", "Action Taken"),
        ("resolved", "Resolved"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="discipline_incidents",
        null=True,
        blank=True,
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="discipline_incidents",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="discipline_incidents",
    )

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_incidents",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    location = models.CharField(max_length=200, blank=True)

    incident_date = models.DateField()

    severity = models.CharField(
        max_length=12,
        choices=SEVERITY_CHOICES,
        default="minor",
    )

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="open",
    )

    action_taken = models.TextField(blank=True)

    points = models.PositiveSmallIntegerField(
        default=0,
        help_text="Discipline points. Higher = more serious.",
    )

    parent_notified = models.BooleanField(default=False)

    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-incident_date", "-id"]

    def clean(self):
        if self.student_id and self.campus_id:
            active = self.student.enrollments.filter(
                campus=self.campus,
                status="active",
            ).exists()

            if not active:
                raise ValidationError(
                    {
                        "campus": (
                            "The student has no active enrollment "
                            "on this campus."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        if self.pk is None and self.points == 0:
            self.points = {
                "minor": 1,
                "moderate": 3,
                "major": 5,
            }.get(self.severity, 1)

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.title} - {self.student.full_name} "
            f"({self.get_severity_display()})"
        )


class DisciplinaryAction(models.Model):
    """An action (warning, detention, suspension...) for an incident."""

    ACTION_TYPE_CHOICES = [
        ("verbal_warning", "Verbal Warning"),
        ("written_warning", "Written Warning"),
        ("detention", "Detention"),
        ("suspension", "Suspension"),
        ("parent_meeting", "Parent Meeting"),
        ("counselling", "Counselling Referral"),
        ("other", "Other"),
    ]

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="actions",
    )

    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        default="verbal_warning",
    )

    details = models.TextField(blank=True)

    action_date = models.DateField()

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_disciplinary_actions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-action_date", "-id"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.incident.status == "open":
            self.incident.status = "action_taken"
            self.incident.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.incident.title}"
