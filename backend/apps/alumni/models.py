from django.db import models

from apps.schools.models import Campus, School
from apps.students.models import Student


class AlumniProfile(models.Model):
    """A former student kept in the school's alumni network."""

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="alumni",
        null=True,
        blank=True,
    )

    student = models.OneToOneField(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alumni_profile",
        help_text="Linked when the record was converted from a withdrawn/graduated student.",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alumni",
    )

    full_name = models.CharField(max_length=200)

    batch_year = models.PositiveIntegerField(
        help_text="Year of graduation / leaving.",
    )

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    occupation = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=200, blank=True)

    city = models.CharField(max_length=120, blank=True)

    notes = models.TextField(blank=True)

    is_active_member = models.BooleanField(
        default=True,
        help_text="Willing to be contacted for alumni events.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-batch_year", "full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.batch_year})"
