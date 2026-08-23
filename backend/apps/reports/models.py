from django.conf import settings
from django.db import models


class ReportTemplate(models.Model):
    REPORT_TYPE_CHOICES = [
        ("enrollment", "Enrollment Report"),
        ("attendance", "Attendance Report"),
        ("results", "Results Report"),
        ("fees", "Fees Report"),
        ("staff", "Staff Report"),
        ("subjects", "Subject Performance"),
        ("payments", "Payment Methods"),
        ("student_status", "Student Status"),
        ("fee_categories", "Fee Categories"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)

    filters = models.JSONField(default=dict, blank=True)
    columns = models.JSONField(default=list, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_templates",
    )

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
