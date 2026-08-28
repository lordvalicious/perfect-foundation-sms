"""Service layer for attendance management."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from django.db import transaction
from django.db.models import Count, Q, Sum

from apps.schools.models import AcademicYear, Campus, Class, School, Section
from apps.students.models import Enrollment, Student

from .models import Attendance


class AttendanceService:
    """Service for attendance recording and reporting."""

    def __init__(self, institution: School):
        self.institution = institution
        self.settings = getattr(institution, "settings", None)

    def _get_late_threshold(self, campus: Optional[Campus] = None) -> int:
        """Get late threshold in minutes (campus override or school default)."""
        if campus and hasattr(campus, "settings") and campus.settings.attendance_late_threshold_minutes:
            return campus.settings.attendance_late_threshold_minutes
        return self.settings.attendance_late_threshold_minutes if self.settings else 15

    def _get_half_day_cutoff(self, campus: Optional[Campus] = None) -> time:
        """Get half-day cutoff time (campus override or school default)."""
        if campus and hasattr(campus, "settings") and campus.settings.attendance_half_day_cutoff:
            return campus.settings.attendance_half_day_cutoff
        return self.settings.attendance_half_day_cutoff if self.settings else time(12, 0)

    def _get_auto_absent_minutes(self, campus: Optional[Campus] = None) -> int:
        """Get auto-absent minutes (campus override or school default)."""
        if campus and hasattr(campus, "settings") and campus.settings.auto_mark_absent_after_minutes:
            return campus.settings.auto_mark_absent_after_minutes
        return self.settings.auto_mark_absent_after_minutes if self.settings else 30

    @transaction.atomic
    def mark_attendance(
        self,
        enrollment: Enrollment,
        attendance_date: date,
        status: str,
        check_in: Optional[time] = None,
        check_out: Optional[time] = None,
        notes: str = "",
        marked_by=None,
    ) -> Attendance:
        """Mark attendance for a student on a specific date."""
        # Validate enrollment is active and matches the date's academic year
        if enrollment.status != "active":
            raise ValueError("Cannot mark attendance for inactive enrollment.")

        # Check if attendance already exists
        existing = Attendance.objects.filter(
            student=enrollment.student,
            date=attendance_date,
        ).first()

        if existing:
            raise ValueError("Attendance already recorded for this student on this date.")

        # Determine status based on check-in time if provided
        final_status = status
        if check_in and status == "present":
            late_threshold = self._get_late_threshold(enrollment.campus)
            class_start = time(8, 0)  # Default class start - should be configurable
            # Simple comparison - in production, get actual class start time
            check_in_dt = datetime.combine(attendance_date, check_in)
            class_start_dt = datetime.combine(attendance_date, class_start)
            if (check_in_dt - class_start_dt).total_seconds() / 60 > late_threshold:
                final_status = "late"

        attendance = Attendance.objects.create(
            student=enrollment.student,
            enrollment=enrollment,
            academic_year=enrollment.academic_year,
            campus=enrollment.campus,
            class_obj=enrollment.class_obj,
            section=enrollment.section,
            date=attendance_date,
            status=final_status,
            notes=notes,
        )

        return attendance

    @transaction.atomic
    def bulk_mark_attendance(
        self,
        enrollments: List[Enrollment],
        attendance_date: date,
        attendance_data: Dict[int, Dict[str, Any]],
    ) -> List[Attendance]:
        """Mark attendance for multiple students at once.

        Args:
            enrollments: List of Enrollment objects
            attendance_date: Date for attendance
            attendance_data: Dict mapping enrollment_id to {status, check_in, check_out, notes}
        """
        created = []

        for enrollment in enrollments:
            data = attendance_data.get(enrollment.id, {})
            status = data.get("status", "present")

            try:
                attendance = self.mark_attendance(
                    enrollment=enrollment,
                    attendance_date=attendance_date,
                    status=status,
                    check_in=data.get("check_in"),
                    check_out=data.get("check_out"),
                    notes=data.get("notes", ""),
                    marked_by=data.get("marked_by"),
                )
                created.append(attendance)
            except ValueError:
                # Skip if already exists or invalid
                continue

        return created

    @transaction.atomic
    def auto_mark_absent(
        self,
        campus: Campus,
        attendance_date: date,
        class_obj: Optional[Class] = None,
        section=None,
    ) -> int:
        """Auto-mark absent for students who haven't been marked by cutoff time."""
        enrollments = Enrollment.objects.filter(
            academic_year__school=campus.school,
            campus=campus,
            status="active",
        ).select_related("student")

        if class_obj:
            enrollments = enrollments.filter(class_obj=class_obj)
        if section:
            enrollments = enrollments.filter(section=section)

        # Get students already marked today
        marked_student_ids = Attendance.objects.filter(
            date=attendance_date,
            student__in=enrollments.values_list("student_id", flat=True),
        ).values_list("student_id", flat=True)

        unmarked = enrollments.exclude(student_id__in=marked_student_ids)

        count = 0
        for enrollment in unmarked:
            Attendance.objects.create(
                student=enrollment.student,
                enrollment=enrollment,
                academic_year=enrollment.academic_year,
                campus=enrollment.campus,
                class_obj=enrollment.class_obj,
                section=enrollment.section,
                date=attendance_date,
                status="absent",
                notes="Auto-marked absent (no check-in)",
            )
            count += 1

        return count

    def get_student_attendance_summary(
        self,
        student: Student,
        academic_year: Optional[AcademicYear] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get attendance summary for a student."""
        queryset = Attendance.objects.filter(student=student)

        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        stats = queryset.values("status").annotate(count=Count("id"))
        status_counts = {item["status"]: item["count"] for item in stats}

        total = sum(status_counts.values())
        present = status_counts.get("present", 0)
        late = status_counts.get("late", 0)
        absent = status_counts.get("absent", 0)
        leave = status_counts.get("leave", 0)

        attendance_percentage = Decimal("0.00")
        if total > 0:
            attendance_percentage = Decimal(str(present + late)) / Decimal(str(total)) * Decimal("100")

        return {
            "student_id": student.id,
            "total_days": total,
            "present": present,
            "late": late,
            "absent": absent,
            "leave": leave,
            "attendance_percentage": round(attendance_percentage, 2),
            "is_below_threshold": attendance_percentage < self._get_minimum_percentage(),
        }

    def _get_minimum_percentage(self, campus: Optional[Campus] = None) -> int:
        """Get minimum attendance percentage (campus override or school default)."""
        if campus and hasattr(campus, "settings") and campus.settings.attendance_minimum_percentage:
            return campus.settings.attendance_minimum_percentage
        return self.settings.attendance_minimum_percentage if self.settings else 75

    def get_class_attendance_report(
        self,
        class_obj: Class,
        section,
        academic_year: AcademicYear,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get attendance report for a class/section."""
        enrollments = Enrollment.objects.filter(
            academic_year=academic_year,
            class_obj=class_obj,
            section=section,
            status="active",
        ).select_related("student")

        report = []
        for enrollment in enrollments:
            summary = self.get_student_attendance_summary(
                student=enrollment.student,
                academic_year=academic_year,
                start_date=start_date,
                end_date=end_date,
            )
            summary["student_name"] = enrollment.student.full_name
            summary["admission_number"] = enrollment.student.admission_number
            summary["roll_number"] = enrollment.roll_number
            report.append(summary)

        return report

    def get_campus_attendance_summary(
        self,
        campus: Campus,
        attendance_date: Optional[date] = None,
        academic_year: Optional[AcademicYear] = None,
    ) -> Dict[str, Any]:
        """Get campus-wide attendance summary for a date or period."""
        if attendance_date is None:
            attendance_date = date.today()

        queryset = Attendance.objects.filter(campus=campus, date=attendance_date)

        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)

        stats = queryset.values("status").annotate(count=Count("id"))
        status_counts = {item["status"]: item["count"] for item in stats}

        total = sum(status_counts.values())
        present = status_counts.get("present", 0) + status_counts.get("late", 0)
        absent = status_counts.get("absent", 0)
        leave = status_counts.get("leave", 0)

        attendance_rate = Decimal("0.00")
        if total > 0:
            attendance_rate = Decimal(str(present)) / Decimal(str(total)) * Decimal("100")

        return {
            "campus_id": campus.id,
            "campus_name": campus.name,
            "date": attendance_date,
            "total_students": total,
            "present": present,
            "absent": absent,
            "leave": leave,
            "attendance_rate": round(attendance_rate, 2),
        }

    def get_low_attendance_students(
        self,
        academic_year: AcademicYear,
        campus: Optional[Campus] = None,
        threshold_percentage: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get students with attendance below threshold."""
        if threshold_percentage is None:
            threshold_percentage = self._get_minimum_percentage(campus)

        enrollments = Enrollment.objects.filter(
            academic_year=academic_year,
            status="active",
        ).select_related("student", "campus")

        if campus:
            enrollments = enrollments.filter(campus=campus)

        low_attendance = []
        for enrollment in enrollments:
            summary = self.get_student_attendance_summary(
                student=enrollment.student,
                academic_year=academic_year,
            )
            if summary["attendance_percentage"] < threshold_percentage:
                summary["student_name"] = enrollment.student.full_name
                summary["admission_number"] = enrollment.student.admission_number
                summary["class_name"] = f"{enrollment.class_obj.name}-{enrollment.section.name}"
                summary["campus_name"] = enrollment.campus.name
                low_attendance.append(summary)

        return sorted(low_attendance, key=lambda x: x["attendance_percentage"])