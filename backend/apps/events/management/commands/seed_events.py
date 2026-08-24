import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.events.models import Event, EventAudience, EventRSVP
from apps.schools.models import Campus, School


class Command(BaseCommand):
    help = "Seed events, audiences, and RSVPs."

    EVENT_DATA = [
        ("Annual Sports Day", "Join us for a day of sports, competition, and team spirit!", "School Ground"),
        ("Science Exhibition", "Students showcase innovative science projects.", "Main Hall"),
        ("Cultural Night", "An evening of music, drama, and poetry performances.", "Auditorium"),
        ("Parents Orientation", "Welcome session for new parents and students.", "Conference Room"),
        ("Teachers Training Workshop", "Professional development session on modern teaching methods.", "Staff Room"),
        ("Art Competition", "Annual inter-class art and painting competition.", "Art Room"),
        ("Career Counselling Seminar", "Guidance session for senior students on career paths.", "Lecture Hall"),
        ("Independence Day Celebration", "Flag hoisting ceremony and national songs.", "School Ground"),
        ("Annual Day Ceremony", "Prize distribution and cultural performances.", "Auditorium"),
        ("Math Olympiad", "Inter-school mathematics competition.", "Math Lab"),
        ("Book Fair", "Browse and purchase books from local publishers.", "Library"),
        ("School Picnic", "Fun day out for all students and staff.", "Jinnah Park"),
        ("Coding Bootcamp", "Two-day coding workshop for students.", "Computer Lab"),
        ("Health & Hygiene Awareness", "Workshop on personal hygiene and health.", "Seminar Hall"),
        ("Ramadan Assembly", "Special assembly for the blessed month of Ramadan.", "Main Hall"),
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\nSeeding events data...\n"))

        school = School.objects.first()
        if not school:
            self.stderr.write(self.style.ERROR("No school found."))
            return

        campuses = list(
            Campus.objects.filter(
                school=school,
                status="active",
            )
        )
        users = list(User.objects.filter(memberships__status="active").distinct()[:30])

        if not users:
            self.stderr.write(self.style.ERROR("No active users found."))
            return

        events_created = 0
        audiences_created = 0
        rsvps_created = 0

        for i, (title, desc, location) in enumerate(self.EVENT_DATA):
            campus = random.choice(campuses) if campuses else None

            start = timezone.now() + timedelta(days=random.randint(-30, 60), hours=random.randint(8, 16))
            end = start + timedelta(hours=random.choice([2, 3, 4, 6, 8]))

            event, created = Event.objects.get_or_create(
                school=school,
                title=title,
                defaults={
                    "description": desc,
                    "location": location,
                    "campus": campus,
                    "start_datetime": start,
                    "end_datetime": end,
                    "status": random.choice(["published", "published", "draft", "cancelled"]),
                    "created_by": random.choice(users),
                },
            )
            if created:
                events_created += 1

                audience_types = random.sample(
                    ["everyone", "students", "teachers", "staff", "class", "role"],
                    k=random.randint(1, 3),
                )
                for aud_type in audience_types:
                    class_obj = None

                    if aud_type == "class" and campus:
                        from apps.schools.models import Class as SchoolClass

                        class_obj = (
                            SchoolClass.objects
                            .filter(unit__campus=campus)
                            .order_by("?")
                            .first()
                        )

                        if class_obj is None:
                            continue

                    EventAudience.objects.create(
                        event=event,
                        audience_type=aud_type,
                        role=random.choice(["teacher", "parent", "student"]) if aud_type == "role" else "",
                        class_obj=class_obj,
                    )
                    audiences_created += 1

                if event.status == "published":
                    num_rsvps = random.randint(5, min(15, len(users)))
                    rsvp_users = random.sample(users, num_rsvps)

                    for user in rsvp_users:
                        _, rsvp_created = EventRSVP.objects.get_or_create(
                            event=event,
                            user=user,
                            defaults={
                                "response": random.choice(["yes", "yes", "yes", "maybe", "no"]),
                            },
                        )
                        if rsvp_created:
                            rsvps_created += 1

        self.stdout.write(self.style.SUCCESS(f"Events created: {events_created}"))
        self.stdout.write(self.style.SUCCESS(f"Event audiences created: {audiences_created}"))
        self.stdout.write(self.style.SUCCESS(f"Event RSVPs created: {rsvps_created}"))
        self.stdout.write(self.style.SUCCESS("\nEvents seeding completed.\n"))
