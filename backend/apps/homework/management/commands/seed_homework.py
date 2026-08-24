import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.homework.models import Homework, Submission
from apps.students.models import Enrollment
from apps.teachers.models import TeacherAssignment


TITLES = [
    "Chapter review questions",
    "Worksheet: practice problems",
    "Short essay",
    "Lab report write-up",
    "Reading comprehension exercise",
    "Math problem set",
]


class Command(BaseCommand):
    help = "Seed homework assignments and student submissions."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=12)

    def handle(self, *args, **options):
        count = options["count"]

        assignments = list(
            TeacherAssignment.objects.filter(status="active")
            .select_related("teacher", "campus", "class_obj", "section", "subject")
        )

        enrollments = list(Enrollment.objects.filter(status="active"))

        if not assignments or not enrollments:
            self.stderr.write(
                self.style.ERROR(
                    "Need active teacher assignments and enrollments first."
                )
            )
            return

        today = timezone.localdate()
        homework_created = 0
        submissions_created = 0

        for _ in range(count):
            assignment = random.choice(assignments)

            assigned = today - timedelta(days=random.randint(0, 14))
            due = assigned + timedelta(days=random.choice([2, 3, 5, 7]))

            homework = Homework.objects.create(
                institution=assignment.campus.school,
                teacher=assignment.teacher,
                campus=assignment.campus,
                class_obj=assignment.class_obj,
                section=assignment.section,
                subject=assignment.subject,
                title=random.choice(TITLES),
                description="Auto-generated demo homework.",
                assigned_date=assigned,
                due_date=due,
                max_marks=random.choice([10, 20]),
            )
            homework_created += 1

            class_enrollments = [
                e
                for e in enrollments
                if e.class_obj_id == homework.class_obj_id
                and e.campus_id == homework.campus_id
            ]

            for enrollment in random.sample(
                class_enrollments,
                min(len(class_enrollments), random.randint(2, 6)),
            ):
                graded = random.random() < 0.5

                submission = Submission.objects.create(
                    homework=homework,
                    student=enrollment.student,
                    content="Demo submission content.",
                    marks_obtained=(
                        random.randint(3, homework.max_marks)
                        if graded
                        else None
                    ),
                    feedback="Good effort." if graded else "",
                    status="graded" if graded else "submitted",
                )
                submissions_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Homework created: {homework_created}, "
                f"submissions created: {submissions_created}"
            )
        )
