from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.exams.models import Exam, ExamSubject, StudentResult
from apps.schools.models import AcademicYear, Campus, SubjectOffering
from apps.students.models import Enrollment


class Command(BaseCommand):
    help = "Create realistic sample exams, exam subjects and student results."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "\nSetting up Perfect Foundation exam data...\n"
            )
        )

        academic_year = (
            AcademicYear.objects
            .filter(name="2026-2027")
            .first()
        )

        if not academic_year:
            academic_year = (
                AcademicYear.objects
                .order_by("-start_date")
                .first()
            )

        if not academic_year:
            self.stdout.write(
                self.style.ERROR(
                    "No academic year found."
                )
            )
            return

        self.stdout.write(
            f"Academic Year: {academic_year.school.name} - "
            f"{academic_year.name}\n"
        )

        exams_created = 0
        exams_existing = 0
        exam_subjects_created = 0
        results_created = 0

        exam_definitions = [
            {
                "name": "First Monthly Test 2026",
                "exam_type": "monthly",
                "start_date": "2026-08-15",
                "end_date": "2026-08-20",
                "status": "completed",
            },
            {
                "name": "Mid-Term Examination 2026",
                "exam_type": "midterm",
                "start_date": "2026-10-15",
                "end_date": "2026-10-25",
                "status": "scheduled",
            },
            {
                "name": "Annual Examination 2026-2027",
                "exam_type": "annual",
                "start_date": "2027-03-01",
                "end_date": "2027-03-15",
                "status": "draft",
            },
        ]

        campuses = Campus.objects.all().order_by("id")

        for campus in campuses:
            self.stdout.write(
                f"\nProcessing campus: {campus.name}"
            )

            classes = []

            for unit in campus.academic_units.all():
                classes.extend(
                    unit.classes.all()
                )

            for class_obj in classes:
                offerings = (
                    SubjectOffering.objects
                    .filter(
                        class_obj=class_obj,
                        academic_year=academic_year,
                    )
                    .select_related("subject")
                    .order_by("subject__name")
                )

                if not offerings.exists():
                    self.stdout.write(
                        f"  {class_obj.name}: "
                        f"No subject offerings found."
                    )
                    continue

                for exam_data in exam_definitions:
                    exam, created = Exam.objects.get_or_create(
                        name=exam_data["name"],
                        academic_year=academic_year,
                        campus=campus,
                        class_obj=class_obj,
                        defaults={
                            "exam_type": exam_data["exam_type"],
                            "start_date": exam_data["start_date"],
                            "end_date": exam_data["end_date"],
                            "status": exam_data["status"],
                        },
                    )

                    if created:
                        exams_created += 1
                    else:
                        exams_existing += 1

                    exam_subject_objects = []

                    for offering in offerings:
                        exam_subject, subject_created = (
                            ExamSubject.objects.get_or_create(
                                exam=exam,
                                subject=offering.subject,
                                defaults={
                                    "maximum_marks": 100,
                                    "passing_marks": 40,
                                },
                            )
                        )

                        if subject_created:
                            exam_subjects_created += 1

                        exam_subject_objects.append(
                            exam_subject
                        )

                    if exam.status != "completed":
                        continue

                    enrollments = (
                        Enrollment.objects
                        .filter(
                            academic_year=academic_year,
                            campus=campus,
                            class_obj=class_obj,
                            status="active",
                        )
                        .select_related("student")
                        .order_by(
                            "student__admission_number"
                        )
                    )

                    for student_index, enrollment in enumerate(
                        enrollments
                    ):
                        for subject_index, exam_subject in enumerate(
                            exam_subject_objects
                        ):
                            marks = self.generate_marks(
                                student_index,
                                subject_index,
                            )

                            result, result_created = (
                                StudentResult.objects.get_or_create(
                                    exam=exam,
                                    student=enrollment.student,
                                    exam_subject=exam_subject,
                                    defaults={
                                        "obtained_marks": marks,
                                        "remarks": self.get_remarks(
                                            marks
                                        ),
                                    },
                                )
                            )

                            if result_created:
                                results_created += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Exams created: {exams_created}"
            )
        )

        self.stdout.write(
            f"Exams already existed: {exams_existing}"
        )

        self.stdout.write(
            f"Exam subjects created: {exam_subjects_created}"
        )

        self.stdout.write(
            f"Student results created: {results_created}"
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Exam setup completed successfully."
            )
        )

    def generate_marks(self, student_index, subject_index):
        patterns = [
            96,
            91,
            86,
            82,
            78,
            74,
            69,
            65,
            61,
            57,
            52,
            47,
            43,
            38,
            31,
        ]

        index = (
            student_index * 3
            + subject_index
        ) % len(patterns)

        return Decimal(str(patterns[index]))

    def get_remarks(self, marks):
        marks = Decimal(marks)

        if marks >= 90:
            return "Outstanding performance."
        elif marks >= 80:
            return "Excellent performance."
        elif marks >= 70:
            return "Very good performance."
        elif marks >= 60:
            return "Good performance."
        elif marks >= 50:
            return "Satisfactory performance."
        elif marks >= 40:
            return "Passed. Can improve further."
        else:
            return "Needs additional attention and support."