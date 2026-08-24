import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.discipline.models import DisciplinaryAction, Incident
from apps.schools.models import Campus
from apps.students.models import Enrollment


TITLES = [
    "Disrupting class",
    "Not completing homework repeatedly",
    "Fighting during break",
    "Using mobile phone in class",
    "Late to school (repeated)",
    "Disrespectful to staff member",
    "Littering the playground",
    "Skipping assembly",
    "Damaging school property",
    "Bullying report",
    "Cheating in class test",
    "Improper uniform",
]

LOCATIONS = ["Classroom", "Playground", "Corridor", "Cafeteria", "Library", "Bus"]

ACTIONS = [
    ("verbal_warning", "Spoke to the student about the behaviour."),
    ("written_warning", "Written warning issued and filed."),
    ("detention", "One-day after-school detention."),
    ("parent_meeting", "Meeting scheduled with guardians."),
]


class Command(BaseCommand):
    help = "Seed discipline incidents and actions."

    def add_arguments(self, parser):
        parser.add_argument("--per-campus", type=int, default=6)

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\nSeeding discipline data...\n"))

        per_campus = options["per_campus"]

        campuses = list(Campus.objects.all())
        enrollments = list(
            Enrollment.objects.filter(status="active").select_related("student")
        )

        if not enrollments:
            self.stderr.write(
                self.style.ERROR(
                    "No active enrollments found. Run student seeders first."
                )
            )
            return

        from apps.accounts.models import User

        staff_user = (
            User.objects.filter(is_superuser=True).first()
            or User.objects.first()
        )

        incidents_created = 0
        actions_created = 0

        for campus in campuses:
            campus_enrollments = [
                e for e in enrollments if e.campus_id == campus.id
            ] or enrollments

            for i in range(per_campus):
                enrollment = random.choice(campus_enrollments)
                severity = random.choice(
                    ["minor", "minor", "moderate", "moderate", "major"]
                )

                incident_date = timezone.localdate() - timedelta(
                    days=random.randint(1, 90)
                )

                incident = Incident.objects.create(
                    institution=campus.school,
                    student=enrollment.student,
                    campus=campus,
                    reported_by=staff_user,
                    title=random.choice(TITLES),
                    description="Auto-generated demo incident.",
                    location=random.choice(LOCATIONS),
                    incident_date=incident_date,
                    severity=severity,
                    status="open",
                )
                incidents_created += 1

                roll = random.random()

                if roll < 0.55:
                    action_type, details = random.choice(ACTIONS)
                    DisciplinaryAction.objects.create(
                        incident=incident,
                        action_type=action_type,
                        details=details,
                        action_date=incident_date + timedelta(days=1),
                        recorded_by=staff_user,
                    )
                    actions_created += 1

                    if severity != "major" or roll < 0.3:
                        incident.status = "resolved"
                        incident.resolved_at = timezone.now()
                        incident.save(update_fields=["status", "resolved_at"])

        self.stdout.write(
            self.style.SUCCESS(f"Incidents created: {incidents_created}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Actions created: {actions_created}")
        )
        self.stdout.write(self.style.SUCCESS("\nDiscipline seeding completed.\n"))
