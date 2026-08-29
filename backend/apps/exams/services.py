"""Service layer for exam management and result processing."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any

from django.db import transaction
from django.db.models import Avg, Count, Q

from apps.schools.models import AcademicYear, Campus, Class, School, Section
from apps.students.models import Enrollment, Student

from .models import (
    Exam,
    ExamSchedule,
    ExamSubject,
    PracticalResult,
    StudentResult,
)


class ExamService:
    """Service for exam lifecycle management."""

    def __init__(self, institution: School):
        self.institution = institution

    def create_exam(
        self,
        name: str,
        exam_type: str,
        academic_year: AcademicYear,
        campus: Campus,
        class_obj: Class,
        start_date: date,
        end_date: date,
        subjects: List[Dict[str, Any]],
        status: str = "draft",
    ) -> Exam:
        """Create an exam with subjects."""
        if end_date < start_date:
            raise ValueError("Exam end date cannot be before start date.")

        with transaction.atomic():
            exam = Exam.objects.create(
                name=name,
                exam_type=exam_type,
                academic_year=academic_year,
                campus=campus,
                class_obj=class_obj,
                start_date=start_date,
                end_date=end_date,
                status=status,
            )

            for subject_data in subjects:
                ExamSubject.objects.create(
                    exam=exam,
                    subject=subject_data["subject"],
                    maximum_marks=subject_data.get("maximum_marks", 100),
                    passing_marks=subject_data.get("passing_marks", 40),
                )

            return exam

    def schedule_exam(self, exam: Exam) -> Exam:
        """Mark exam as scheduled."""
        if exam.status != "draft":
            raise ValueError("Only draft exams can be scheduled.")
        if not exam.exam_subjects.exists():
            raise ValueError("Cannot schedule exam without subjects.")

        exam.status = "scheduled"
        exam.save(update_fields=["status", "updated_at"])
        return exam

    def complete_exam(self, exam: Exam) -> Exam:
        """Mark exam as completed."""
        if exam.status not in ["draft", "scheduled"]:
            raise ValueError("Only draft/scheduled exams can be completed.")

        exam.status = "completed"
        exam.save(update_fields=["status", "updated_at"])
        return exam

    def get_exams_for_campus(
        self,
        campus: Campus,
        academic_year: Optional[AcademicYear] = None,
        status: Optional[str] = None,
    ):
        """Get exams for a campus with optional filters."""
        queryset = Exam.objects.filter(campus=campus).select_related(
            "academic_year", "class_obj"
        ).prefetch_related("exam_subjects__subject")

        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        if status:
            queryset = queryset.filter(status=status)

        return queryset


class ResultService:
    """Service for result entry and processing."""

    def __init__(self, institution: School):
        self.institution = institution

    @transaction.atomic
    def enter_result(
        self,
        exam: Exam,
        student: Student,
        exam_subject: ExamSubject,
        obtained_marks: Decimal,
        is_absent: bool = False,
        remarks: str = "",
    ) -> StudentResult:
        """Enter or update a student's result for an exam subject."""
        if obtained_marks < 0:
            raise ValueError("Obtained marks cannot be negative.")

        if is_absent:
            obtained_marks = Decimal("0.00")

        if not is_absent and obtained_marks > exam_subject.maximum_marks:
            raise ValueError("Obtained marks cannot exceed maximum marks.")

        # Verify student is enrolled in this exam's class/campus/year
        enrolled = Enrollment.objects.filter(
            student=student,
            academic_year=exam.academic_year,
            campus=exam.campus,
            class_obj=exam.class_obj,
            status="active",
        ).exists()

        if not enrolled:
            raise ValueError("Student is not actively enrolled in this exam's class.")

        result, created = StudentResult.objects.update_or_create(
            exam=exam,
            student=student,
            exam_subject=exam_subject,
            defaults={
                "obtained_marks": obtained_marks,
                "is_absent": is_absent,
                "remarks": remarks,
            },
        )

        # Auto-calculate grade and pass/fail
        result.save()  # Triggers grade calculation in model's save()
        return result

    @transaction.atomic
    def bulk_enter_results(
        self,
        exam: Exam,
        exam_subject: ExamSubject,
        results: List[Dict[str, Any]],
    ) -> List[StudentResult]:
        """Enter results for multiple students at once."""
        created_results = []

        for result_data in results:
            student = result_data["student"]
            obtained_marks = Decimal(str(result_data["obtained_marks"]))
            is_absent = result_data.get("is_absent", False)
            remarks = result_data.get("remarks", "")

            try:
                result = self.enter_result(
                    exam=exam,
                    student=student,
                    exam_subject=exam_subject,
                    obtained_marks=obtained_marks,
                    is_absent=is_absent,
                    remarks=remarks,
                )
                created_results.append(result)
            except ValueError as e:
                # Log error but continue with other results
                result_data["error"] = str(e)

        return created_results

    @transaction.atomic
    def enter_practical_result(
        self,
        exam: Exam,
        student: Student,
        exam_subject: ExamSubject,
        obtained_marks: Decimal,
        maximum_marks: int = 50,
        passing_marks: int = 20,
        is_absent: bool = False,
        remarks: str = "",
    ) -> PracticalResult:
        """Enter practical exam result."""
        if is_absent:
            obtained_marks = Decimal("0.00")

        if obtained_marks < 0:
            raise ValueError("Obtained marks cannot be negative.")
        if obtained_marks > maximum_marks:
            raise ValueError("Obtained marks cannot exceed maximum marks.")
        if passing_marks > maximum_marks:
            raise ValueError("Passing marks cannot exceed maximum marks.")

        result, created = PracticalResult.objects.update_or_create(
            exam=exam,
            student=student,
            exam_subject=exam_subject,
            defaults={
                "obtained_marks": obtained_marks,
                "maximum_marks": maximum_marks,
                "passing_marks": passing_marks,
                "is_absent": is_absent,
                "remarks": remarks,
            },
        )

        result.save()  # Triggers grade calculation
        return result

    def get_student_results(
        self,
        student: Student,
        exam: Optional[Exam] = None,
        academic_year: Optional[AcademicYear] = None,
    ):
        """Get all results for a student."""
        queryset = StudentResult.objects.filter(student=student).select_related(
            "exam", "exam_subject__subject", "exam__academic_year", "exam__campus", "exam__class_obj"
        )

        if exam:
            queryset = queryset.filter(exam=exam)
        elif academic_year:
            queryset = queryset.filter(exam__academic_year=academic_year)

        return queryset

    def get_class_results(
        self,
        exam: Exam,
        class_obj: Optional[Class] = None,
        section=None,
    ):
        """Get all results for an exam (optionally filtered by class/section)."""
        queryset = StudentResult.objects.filter(
            exam=exam,
        ).select_related("student", "exam_subject__subject")

        if class_obj:
            queryset = queryset.filter(student__enrollments__class_obj=class_obj)
        if section:
            queryset = queryset.filter(student__enrollments__section=section)

        return queryset.distinct()

    def get_exam_statistics(self, exam: Exam) -> Dict[str, Any]:
        """Calculate statistics for an exam."""
        results = StudentResult.objects.filter(exam=exam)

        stats = results.aggregate(
            total_students=Count("student", distinct=True),
            avg_percentage=Avg("obtained_marks"),
            total_passed=Count("id", filter=Q(is_pass=True)),
            total_failed=Count("id", filter=Q(is_pass=False)),
            total_absent=Count("id", filter=Q(is_absent=True)),
        )

        total = stats["total_students"] or 0
        passed = stats["total_passed"] or 0

        return {
            "exam_id": exam.id,
            "exam_name": exam.name,
            "total_students": total,
            "passed": passed,
            "failed": stats["total_failed"] or 0,
            "absent": stats["total_absent"] or 0,
            "pass_percentage": round((passed / total * 100) if total > 0 else 0, 2),
            "average_percentage": round(float(stats["avg_percentage"] or 0), 2),
        }

    def get_subject_statistics(self, exam: Exam) -> List[Dict[str, Any]]:
        """Calculate per-subject statistics for an exam."""
        subjects = ExamSubject.objects.filter(exam=exam).select_related("subject")
        stats = []

        for es in subjects:
            results = StudentResult.objects.filter(exam_subject=es)
            subj_stats = results.aggregate(
                count=Count("id"),
                avg_marks=Avg("obtained_marks"),
                passed=Count("id", filter=Q(is_pass=True)),
                failed=Count("id", filter=Q(is_pass=False)),
                absent=Count("id", filter=Q(is_absent=True)),
            )

            total = subj_stats["count"] or 0
            passed = subj_stats["passed"] or 0

            stats.append({
                "exam_subject_id": es.id,
                "subject_name": es.subject.name,
                "subject_code": es.subject.code,
                "maximum_marks": es.maximum_marks,
                "passing_marks": es.passing_marks,
                "total_students": total,
                "passed": passed,
                "failed": subj_stats["failed"] or 0,
                "absent": subj_stats["absent"] or 0,
                "pass_percentage": round((passed / total * 100) if total > 0 else 0, 2),
                "average_marks": round(float(subj_stats["avg_marks"] or 0), 2),
            })

        return stats


class GradeService:
    """Grade calculation that delegates to the configurable grading engine.

    The authoritative grade bands live in the ``reportcards`` app
    (``GradeScale`` / ``GradeBand``). This service reuses that engine so
    institutions' configured boundaries and grade points are honoured
    instead of a competing hard-coded scale.
    """

    def __init__(self, institution: School = None):
        self.institution = institution
        self.settings = getattr(institution, "settings", None) if institution else None

    def _default_scale(self):
        """Resolve the institution's effective grade scale.

        Prefers the institution's own default scale, falling back to the
        platform default scale used for automated grade calculation.
        """
        from apps.reportcards.models import GradeScale

        if self.institution is not None:
            scale = (
                GradeScale.objects
                .filter(
                    institution=self.institution,
                    is_default=True,
                )
                .first()
            )

            if scale is not None:
                return scale

        return GradeScale.objects.filter(is_default=True).first()

    def get_grade_bands(self) -> List[Dict[str, Any]]:
        """Return the effective grade bands as sorted dicts."""
        from apps.reportcards.models import GradeBand

        scale = self._default_scale()

        if scale is None:
            return []

        bands = (
            GradeBand.objects
            .filter(scale=scale)
            .order_by("-minimum_percentage")
        )

        return [
            {
                "min_percentage": band.minimum_percentage,
                "max_percentage": band.maximum_percentage,
                "grade": band.letter_grade,
                "gpa": band.grade_point,
                "grade_point": band.grade_point,
            }
            for band in bands
        ]

    def calculate_grade(self, percentage: Decimal) -> Dict[str, Any]:
        """Calculate the grade band for a percentage."""
        from apps.reportcards.models import GradeBand

        scale = self._default_scale()
        band = GradeBand.band_for_percentage(percentage, scale=scale)

        if band is None:
            return {}

        return {
            "min_percentage": band.minimum_percentage,
            "max_percentage": band.maximum_percentage,
            "grade": band.letter_grade,
            "gpa": band.grade_point,
            "grade_point": band.grade_point,
        }

    def calculate_gpa(self, results: List[StudentResult]) -> Decimal:
        """Calculate GPA from a list of results using the configured scale.

        Absent subjects are excluded from the calculation.
        """
        if not results:
            return Decimal("0.00")

        from apps.reportcards.models import GradeBand

        scale = self._default_scale()

        total_points = Decimal("0.00")
        total_credits = 0

        for result in results:
            if result.is_absent:
                continue

            band = GradeBand.band_for_percentage(
                result.percentage,
                scale=scale,
            )

            if band is None:
                continue

            total_points += band.grade_point
            total_credits += 1

        if total_credits == 0:
            return Decimal("0.00")

        return (
            total_points / Decimal(str(total_credits))
        ).quantize(Decimal("0.01"))

    def is_promoted(self, results: List[StudentResult]) -> bool:
        """Determine if student should be promoted based on results."""
        if not self.settings:
            return all(r.is_pass for r in results if not r.is_absent)

        min_subjects = self.settings.exam_minimum_subjects_to_pass
        passed_count = sum(1 for r in results if r.is_pass and not r.is_absent)
        return passed_count >= min_subjects


class MarksService:
    """Reliable, reusable calculation foundation for marks and results.

    All percentages, grades, grade points, GPAs and pass/fail decisions
    delegate to the canonical ``GradeScale``/``GradeBand`` engine so there
    is a single source of truth across the platform.
    """

    def __init__(self, institution: School = None, scale=None):
        self.scale = scale
        if scale is None and institution is not None:
            from apps.reportcards.models import GradeScale

            self.scale = (
                GradeScale.objects
                .filter(institution=institution, is_default=True)
                .first()
            ) or GradeScale.objects.filter(is_default=True).first()

    @staticmethod
    def percentage(obtained: Decimal, maximum: Decimal) -> Decimal:
        """Percentage of obtained marks out of maximum, rounded to 2dp."""
        from decimal import Decimal as D, ROUND_HALF_UP

        maximum = D(str(maximum))
        if maximum <= 0:
            return D("0.00")

        value = (D(str(obtained)) / maximum) * D("100")
        return value.quantize(D("0.01"), rounding=ROUND_HALF_UP)

    def grade_band(self, percentage: Decimal):
        """Canonical grade band for a percentage (``None`` if unscaled)."""
        from apps.reportcards.models import GradeBand

        return GradeBand.band_for_percentage(percentage, scale=self.scale)

    def grade(self, percentage: Decimal) -> str:
        band = self.grade_band(percentage)
        return band.letter_grade if band else ""

    def grade_point(self, percentage: Decimal) -> Decimal:
        band = self.grade_band(percentage)
        return band.grade_point if band else Decimal("0.00")

    def subject_result(self, result: StudentResult) -> Dict[str, Any]:
        """Calculated presentation of a single subject result."""
        from decimal import Decimal as D

        maximum = D(str(result.exam_subject.maximum_marks))
        obtained = result.obtained_marks

        return {
            "exam_subject": result.exam_subject_id,
            "subject": result.exam_subject.subject_id,
            "subject_name": result.exam_subject.subject.name,
            "maximum_marks": maximum,
            "obtained_marks": obtained,
            "absent": result.is_absent,
            "percentage": result.percentage,
            "grade": result.grade,
            "is_pass": result.is_pass
            if not result.is_absent
            else False,
        }

    def gpa(self, results: List[StudentResult]) -> Decimal:
        """GPA over results using the configured scale.

        Absent subjects are excluded. Fails on empty subject sets as
        ``0.00`` only when there are no measurable results.
        """
        if not results:
            return Decimal("0.00")

        from decimal import Decimal as D, ROUND_HALF_UP

        total_points = D("0.00")
        total_credits = 0

        for result in results:
            if result.is_absent:
                continue

            band = self.grade_band(result.percentage)

            if band is None:
                continue

            total_points += band.grade_point
            total_credits += 1

        if total_credits == 0:
            return D("0.00")

        return (
            total_points / D(str(total_credits))
        ).quantize(D("0.01"), rounding=ROUND_HALF_UP)

    def overall(
        self,
        results: List[StudentResult],
        total_marks=None,
        maximum_marks=None,
    ) -> Dict[str, Any]:
        """Aggregated overall result for a set of subject results.

        Passes only when every recorded result passes. Uses the provided
        totals (for example from a report card) or sums the marks.
        """
        from decimal import Decimal as D, ROUND_HALF_UP

        results = list(results)

        if total_marks is None:
            total_marks = sum(
                (r.obtained_marks for r in results),
                D("0.00"),
            )

        if maximum_marks is None:
            maximum_marks = sum(
                (
                    D(str(r.exam_subject.maximum_marks))
                    for r in results
                ),
                D("0.00"),
            )

        pct = self.percentage(total_marks, maximum_marks)
        is_pass = bool(results) and all(
            r.is_pass for r in results if not r.is_absent
        )

        return {
            "maximum_marks": maximum_marks,
            "total_marks": total_marks,
            "percentage": pct,
            "grade": self.grade(pct),
            "grade_point": self.grade_point(pct),
            "is_pass": is_pass,
            "overall_result": "Pass" if is_pass else "Fail",
            "subject_count": len(results),
        }


class ScheduleService:
    """Service for exam scheduling and conflict detection."""

    def __init__(self, institution: School):
        self.institution = institution

    def check_conflicts(
        self,
        exam: Exam,
        section: Section,
        date,
        start_time,
        end_time,
        room: str = "",
        exclude_schedule=None,
    ) -> List[str]:
        """Return a list of conflict messages for a proposed time slot.

        Ignores ``exclude_schedule`` when present (for updates).
        """
        conflicts = []

        if end_time <= start_time:
            conflicts.append("End time must be after start time.")

        if date < exam.start_date or date > exam.end_date:
            conflicts.append(
                "Exam date falls outside the exam period "
                f"({exam.start_date} to {exam.end_date})."
            )

        if section.class_obj_id != exam.class_obj_id:
            conflicts.append(
                "The section does not belong to the exam's class."
            )

        overlap = ExamSchedule.objects.filter(
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time,
        )
        if exclude_schedule is not None:
            overlap = overlap.exclude(pk=exclude_schedule.pk)

        if section_id := getattr(section, "id", None):
            if overlap.filter(section_id=section_id).exists():
                conflicts.append(
                    "This section already has an exam "
                    "overlapping this date and time."
                )

        if room:
            if overlap.filter(room=room).exists():
                conflicts.append(
                    "This room is already booked for an exam "
                    "overlapping this date and time."
                )

        return conflicts

    @transaction.atomic
    def create_schedule(
        self,
        exam: Exam,
        section: Section,
        exam_subject=None,
        date=None,
        start_time=None,
        end_time=None,
        room: str = "",
        notes: str = "",
    ) -> ExamSchedule:
        """Create a single exam schedule slot."""
        conflicts = self.check_conflicts(
            exam=exam,
            section=section,
            date=date,
            start_time=start_time,
            end_time=end_time,
            room=room,
        )

        if conflicts:
            raise ValueError("; ".join(conflicts))

        return ExamSchedule.objects.create(
            exam=exam,
            section=section,
            exam_subject=exam_subject,
            date=date,
            start_time=start_time,
            end_time=end_time,
            room=room,
            notes=notes,
        )

    @transaction.atomic
    def bulk_create_schedules(
        self,
        exam: Exam,
        slots: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Atomically create many schedule slots for an exam.

        Each item in ``slots`` may carry: section, exam_subject, date,
        start_time, end_time, room, notes. Returns a report with created
        ids and any per-slot errors (a failing slot does not roll back
        the whole batch).
        """
        created = []
        errors = []

        for slot in slots:
            section = slot.get("section")
            if section is None:
                errors.append({"error": "section is required"})
                continue

            try:
                schedule = self.create_schedule(
                    exam=exam,
                    section=section,
                    exam_subject=slot.get("exam_subject"),
                    date=slot.get("date"),
                    start_time=slot.get("start_time"),
                    end_time=slot.get("end_time"),
                    room=slot.get("room", ""),
                    notes=slot.get("notes", ""),
                )
                created.append(schedule.pk)
            except (ValueError, KeyError) as exc:
                errors.append(
                    {
                        "section": getattr(section, "id", None),
                        "exam_subject": getattr(
                            slot.get("exam_subject"), "id", None
                        ),
                        "error": str(exc),
                    }
                )

        return {"created": created, "errors": errors}