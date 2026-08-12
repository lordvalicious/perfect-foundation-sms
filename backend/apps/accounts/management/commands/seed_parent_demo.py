import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.attendance.models import Attendance
from apps.reportcards.models import ReportCard
from apps.students.models import Guardian, Student


class Command(BaseCommand):
    help = (
        "Wire up the demo parent account: link it to a guardian, "
        "attach a data-rich student, top up attendance and publish "
        "the student's report card."
    )

    DEMO_USERNAME = "parent"

    def handle(self, *args, **options):
        user = User.objects.filter(
            username=self.DEMO_USERNAME
        ).first()

        if user is None:
            self.stdout.write(
                self.style.ERROR(
                    "Demo parent user not found. Run "
                    "create_demo_users first."
                )
            )
            return

        # ---------------------------------------------------------
        # 1. Guardian linked to the parent account
        # ---------------------------------------------------------
        guardian, _ = Guardian.objects.get_or_create(
            user=user,
            defaults={
                "name": "Demo Parent",
                "relationship": "Parent",
                "phone": "0300-1234567",
                "email": "parent@perfectfoundation.edu",
                "address": "House 4, Street 12, Islamabad",
            },
        )

        if guardian.name != "Demo Parent":
            guardian.name = "Demo Parent"
            guardian.save(update_fields=["name"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Guardian ready: {guardian.name} "
                f"(linked to {user.username})"
            )
        )

        # ---------------------------------------------------------
        # 2. Reassign a data-rich student to this guardian
        # ---------------------------------------------------------
        student = (
            Student.objects
            .filter(
                enrollments__status="active",
                attendance_records__isnull=False,
            )
            .distinct()
            .first()
        )

        if student is None:
            self.stdout.write(
                self.style.WARNING(
                    "No eligible student found to attach."
                )
            )
            return

        student.guardian = guardian
        student.save(update_fields=["guardian"])

        enrollment = (
            student.enrollments
            .filter(status="active")
            .select_related(
                "academic_year",
                "campus",
                "class_obj",
                "section",
            )
            .first()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Student attached: {student.full_name} "
                f"({student.admission_number}) "
                f"-> {guardian.name}"
            )
        )

        if enrollment is None:
            self.stdout.write(
                self.style.WARNING(
                    "Student has no active enrollment; "
                    "skipping attendance top-up."
                )
            )
        else:
            self.top_up_attendance(student, enrollment)

        # ---------------------------------------------------------
        # 3. Publish the student's report card
        # ---------------------------------------------------------
        report_card = (
            ReportCard.objects
            .filter(
                student=student,
                status__in=["draft", "approved"],
            )
            .order_by("-created_at")
            .first()
        )

        if report_card is None:
            self.stdout.write(
                self.style.WARNING(
                    "No draft/approved report card to publish."
                )
            )
        else:
            if report_card.status == "draft":
                report_card.approve(user=user)

            report_card.publish(user=user)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Report card published: "
                    f"{report_card.exam.name} | "
                    f"{report_card.percentage}% | "
                    f"{report_card.grade}"
                )
            )

    def top_up_attendance(self, student, enrollment):
        created = 0

        for day_offset in range(1, 15):
            day = timezone.now().date() - timedelta(days=day_offset)

            if day.weekday() >= 5:
                continue

            roll = random.random()

            if roll < 0.55:
                status = "present"
            elif roll < 0.78:
                status = "late"
            elif roll < 0.92:
                status = "absent"
            else:
                status = "leave"

            record, was_created = (
                Attendance.objects.get_or_create(
                    student=student,
                    date=day,
                    defaults={
                        "enrollment": enrollment,
                        "academic_year": (
                            enrollment.academic_year
                        ),
                        "campus": enrollment.campus,
                        "class_obj": enrollment.class_obj,
                        "section": enrollment.section,
                        "status": status,
                        "notes": "",
                    },
                )
            )

            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Attendance topped up: {created} new records "
                f"for {student.full_name}."
            )
        )
