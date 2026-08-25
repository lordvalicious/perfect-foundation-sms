import random

from django.core.management.base import BaseCommand

from apps.alumni.models import AlumniProfile
from apps.schools.models import Campus


FIRST = ["Ali", "Sara", "Usman", "Ayesha", "Bilal", "Hina", "Omar", "Zara", "Hamza", "Iqra"]
LAST = ["Khan", "Malik", "Butt", "Sheikh", "Raza", "Chaudhry", "Hashmi", "Qureshi"]
JOBS = ["Software Engineer", "Doctor", "Teacher", "Accountant", "Civil Servant", "Entrepreneur"]
ORGANIZATIONS = ["Systems Ltd", "Shaukat Khanum", "City School", "FBR", "Self-employed", "Pak Army"]
CITIES = ["Lahore", "Islamabad", "Karachi", "Rawalpindi", "Haripur"]


class Command(BaseCommand):
    help = "Seed demo alumni records."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=25)

    def handle(self, *args, **options):
        count = options["count"]

        campuses = list(Campus.objects.all())

        created = 0

        for _ in range(count):
            name = f"{random.choice(FIRST)} {random.choice(LAST)}"

            AlumniProfile.objects.get_or_create(
                full_name=name,
                batch_year=random.randint(2005, 2025),
                defaults={
                    "campus": random.choice(campuses) if campuses else None,
                    "email": (
                        f"{name.lower().replace(' ', '.')}@example.com"
                    ),
                    "phone": f"03{random.randint(10, 49)}-{random.randint(1000000, 9999999)}",
                    "occupation": random.choice(JOBS),
                    "organization": random.choice(ORGANIZATIONS),
                    "city": random.choice(CITIES),
                },
            )

            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Alumni processed: {created}")
        )
