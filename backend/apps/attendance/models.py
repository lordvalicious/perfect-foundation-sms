
from django.core.exceptions import ValidationError
from django.db import models

from apps.schools.models import AcademicYear, Campus, Class, Section
# Use string references to avoid circular imports
# from apps.students.models import Enrollment, Student


class Attendance(models.Model):
    
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    enrollment = models.ForeignKey(
        "students.Enrollment",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )

    date = models.DateField()

    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("leave", "Leave"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="present",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "student__first_name"]

        constraints = [
            models.UniqueConstraint(
                fields=["student", "date"],
                name="unique_student_attendance_per_day",
            )
        ]
        indexes = [
            models.Index(
                fields=["campus", "date", "status"],
                name="att_campus_date_status_idx",
            ),
            models.Index(
                fields=["class_obj", "section", "date"],
                name="att_class_section_date_idx",
            ),
            models.Index(
                fields=["academic_year", "date"],
                name="att_year_date_idx",
            ),
        ]

    def clean(self):
        errors = {}

        if self.enrollment_id:
            enrollment = self.enrollment

            if self.student_id != enrollment.student_id:
                errors["student"] = (
                    "Student must match the selected enrollment."
                )

            if self.academic_year_id != enrollment.academic_year_id:
                errors["academic_year"] = (
                    "Academic year must match the enrollment."
                )

            if self.campus_id != enrollment.campus_id:
                errors["campus"] = (
                    "Campus must match the enrollment."
                )

            if self.class_obj_id != enrollment.class_obj_id:
                errors["class_obj"] = (
                    "Class must match the enrollment."
                )

            if self.section_id != enrollment.section_id:
                errors["section"] = (
                    "Section must match the enrollment."
                )

        if self.section_id and self.class_obj_id:
            if self.section.class_obj_id != self.class_obj_id:
                errors["section"] = (
                    "Section must belong to the selected class."
                )

        if self.class_obj_id and self.campus_id:
            if self.class_obj.unit.campus_id != self.campus_id:
                errors["class_obj"] = (
                    "Class must belong to the selected campus."
                )

        if self.academic_year_id and self.campus_id:
            if (
                self.academic_year.school_id
                != self.campus.school_id
            ):
                errors["academic_year"] = (
                    "Academic year must belong to the same school "
                    "as the selected campus."
                )

        if errors:
            raise ValidationError(errors)
        
        # Run campus assignment validation
        # super().clean()  # Removed CampusAssignmentValidationMixin

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.student.full_name} - "
            f"{self.date} - "
            f"{self.get_status_display()}"
        )

