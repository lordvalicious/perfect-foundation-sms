from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand

from apps.exams.models import Exam, ExamSubject, StudentResult
from apps.reportcards.models import ReportCard, ReportCardSubject


class Command(BaseCommand):
    help = "Create report cards from existing exam results."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "\nSetting up report cards...\n"
            )
        )

        exams = (
            Exam.objects
            .all()
            .select_related(
                "academic_year",
                "campus",
                "class_obj",
            )
            .order_by("start_date", "id")
        )

        if not exams.exists():
            self.stdout.write(
                self.style.WARNING(
                    "No exams found."
                )
            )
            return

        report_cards_created = 0
        report_cards_existing = 0
        subject_entries_created = 0
        subject_entries_existing = 0

        for exam in exams:
            self.stdout.write(
                f"\nProcessing exam: {exam.name} | "
                f"{exam.campus.name} | "
                f"{exam.class_obj.name}"
            )

            results = (
                StudentResult.objects
                .filter(exam=exam)
                .select_related(
                    "student",
                    "exam_subject",
                    "exam_subject__subject",
                )
                .order_by(
                    "student__admission_number",
                )
            )

            student_ids = (
                results
                .values_list(
                    "student_id",
                    flat=True,
                )
                .distinct()
            )

            for student_id in student_ids:
                student_results = list(
                    results.filter(
                        student_id=student_id
                    )
                )

                if not student_results:
                    continue

                student = student_results[0].student

                report_card, created = (
                    ReportCard.objects.get_or_create(
                        student=student,
                        exam=exam,
                        defaults={
                            "teacher_remarks": "",
                            "principal_remarks": "",
                        },
                    )
                )

                if created:
                    report_cards_created += 1
                else:
                    report_cards_existing += 1

                for result in student_results:
                    percentage = self.calculate_percentage(
                        result.obtained_marks,
                        result.exam_subject.maximum_marks,
                    )

                    entry, entry_created = (
                        ReportCardSubject.objects.get_or_create(
                            report_card=report_card,
                            exam_subject=result.exam_subject,
                            defaults={
                                "obtained_marks": (
                                    result.obtained_marks
                                ),
                                "maximum_marks": (
                                    result.exam_subject.maximum_marks
                                ),
                                "percentage": percentage,
                                "grade": result.grade,
                                "is_pass": result.is_pass,
                                "remarks": result.remarks,
                            },
                        )
                    )

                    if entry_created:
                        subject_entries_created += 1
                    else:
                        subject_entries_existing += 1

                if not report_card.teacher_remarks:
                    report_card.teacher_remarks = (
                        report_card.generate_teacher_remarks()
                    )

                report_card.save(
                    update_fields=[
                        "teacher_remarks",
                        "updated_at",
                    ]
                )

            self.update_positions(exam)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Report cards created: "
                f"{report_cards_created}"
            )
        )

        self.stdout.write(
            f"Report cards already existed: "
            f"{report_cards_existing}"
        )

        self.stdout.write(
            f"Subject entries created: "
            f"{subject_entries_created}"
        )

        self.stdout.write(
            f"Subject entries already existed: "
            f"{subject_entries_existing}"
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Report card setup completed successfully."
            )
        )

    def calculate_percentage(
        self,
        obtained_marks,
        maximum_marks,
    ):
        if not maximum_marks:
            return Decimal("0.00")

        percentage = (
            Decimal(str(obtained_marks))
            / Decimal(str(maximum_marks))
        ) * Decimal("100")

        return percentage.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def update_positions(self, exam):
        report_cards = list(
            ReportCard.objects
            .filter(exam=exam)
            .select_related("student")
        )

        if not report_cards:
            return

        report_cards.sort(
            key=lambda card: card.total_marks,
            reverse=True,
        )

        previous_marks = None
        current_position = 0

        for index, report_card in enumerate(
            report_cards,
            start=1,
        ):
            total = report_card.total_marks

            if total != previous_marks:
                current_position = index

            if report_card.position != current_position:
                ReportCard.objects.filter(
                    pk=report_card.pk
                ).update(
                    position=current_position
                )

            previous_marks = total

        self.stdout.write(
            f"Positions updated: "
            f"{len(report_cards)} report cards"
        )