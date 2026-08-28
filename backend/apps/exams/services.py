"""Service layer for exam management and result processing."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any

from django.db import transaction
from django.db.models import Avg, Count, Q

from apps.schools.models import AcademicYear, Campus, Class, School
from apps.students.models import Enrollment, Student

from .models import Exam, ExamSubject, StudentResult, PracticalResult


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
    """Service for grade calculation and management."""

    def __init__(self, institution: School):
        self.institution = institution
        self.settings = getattr(institution, "settings", None)

    def get_grade_bands(self) -> List[Dict[str, Any]]:
        """Get grade bands based on institution settings."""
        if self.settings and self.settings.grading_scale == "custom" and self.settings.custom_grade_bands:
            return self.settings.custom_grade_bands

        # Default standard grading scale
        return [
            {"min_percentage": 90, "max_percentage": 100, "grade": "A+", "label": "Excellent", "gpa": 4.0},
            {"min_percentage": 80, "max_percentage": 89, "grade": "A", "label": "Very Good", "gpa": 3.7},
            {"min_percentage": 70, "max_percentage": 79, "grade": "B+", "label": "Good", "gpa": 3.3},
            {"min_percentage": 60, "max_percentage": 69, "grade": "B", "label": "Above Average", "gpa": 3.0},
            {"min_percentage": 50, "max_percentage": 59, "grade": "C+", "label": "Average", "gpa": 2.5},
            {"min_percentage": 40, "max_percentage": 49, "grade": "C", "label": "Below Average", "gpa": 2.0},
            {"min_percentage": 33, "max_percentage": 39, "grade": "D", "label": "Pass", "gpa": 1.0},
            {"min_percentage": 0, "max_percentage": 32, "grade": "F", "label": "Fail", "gpa": 0.0},
        ]

    def calculate_grade(self, percentage: Decimal) -> Dict[str, Any]:
        """Calculate grade for a given percentage."""
        bands = self.get_grade_bands()
        for band in bands:
            if band["min_percentage"] <= percentage <= band["max_percentage"]:
                return band
        # Fallback
        return bands[-1]

    def calculate_gpa(self, results: List[StudentResult]) -> Decimal:
        """Calculate GPA from a list of results."""
        if not results:
            return Decimal("0.00")

        total_points = Decimal("0.00")
        total_credits = 0

        for result in results:
            if result.is_absent:
                continue
            percentage = result.percentage
            band = self.calculate_grade(percentage)
            total_points += Decimal(str(band.get("gpa", 0)))
            total_credits += 1

        if total_credits == 0:
            return Decimal("0.00")

        return (total_points / total_credits).quantize(Decimal("0.01"))

    def is_promoted(self, results: List[StudentResult]) -> bool:
        """Determine if student should be promoted based on results."""
        if not self.settings:
            return all(r.is_pass for r in results if not r.is_absent)

        min_subjects = self.settings.exam_minimum_subjects_to_pass
        passed_count = sum(1 for r in results if r.is_pass and not r.is_absent)
        return passed_count >= min_subjects