from datetime import date

from django.core.management.base import BaseCommand

from apps.schools.models import AcademicYear, Campus, Section
from apps.students.models import Enrollment, Guardian, Student


class Command(BaseCommand):
    help = (
        "Add N fictional students per campus, each enrolled in an "
        "active section of that campus."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of new students to create per campus.",
        )

    FIRST_NAMES_MALE = [
        "Ahmed", "Bilal", "Daniyal", "Fahad", "Hamza", "Imran",
        "Kamran", "Muneeb", "Noman", "Omar", "Raza", "Saad",
        "Taimur", "Usman", "Waleed", "Yasir", "Zain", "Arham",
        "Hassan", "Ibrahim", "Junaid", "Shahzaib", "Talha", "Umer",
    ]

    FIRST_NAMES_FEMALE = [
        "Ayesha", "Bushra", "Dua", "Fatima", "Hira", "Iqra",
        "Khadija", "Mahnoor", "Nadia", "Rabia", "Sana", "Areeba",
        "Maryam", "Zainab", "Hafsa", "Iman", "Laiba", "Mariam",
        "Noor", "Sadia", "Tahira", "Umme", "Yusra", "Zara",
    ]

    LAST_NAMES = [
        "Khan", "Malik", "Ahmed", "Butt", "Chaudhry", "Dar",
        "Gill", "Hashmi", "Iqbal", "Javed", "Kazmi", "Lodhi",
        "Mirza", "Nawaz", "Qureshi", "Rana", "Sheikh", "Tariq",
        "Virk", "Warsi", "Yousaf", "Zafar", "Abbas", "Baig",
    ]

    GENDER_OPTIONS = ["male", "female"]

    def handle(self, *args, **options):
        count = max(options["count"], 0)

        academic_year = (
            AcademicYear.objects.filter(status="active").first()
            or AcademicYear.objects.first()
        )

        if academic_year is None:
            self.stderr.write(
                self.style.ERROR(
                    "No academic year found. Create one first."
                )
            )
            return

        if count == 0:
            self.stdout.write("Count is 0, nothing to do.")
            return

        for campus in Campus.objects.filter(status="active").order_by("id"):
            self.stdout.write(f"\nProcessing {campus.name}...")

            sections = list(
                Section.objects.filter(
                    class_obj__unit__campus=campus,
                    status="active",
                ).select_related("class_obj")
            )

            if not sections:
                self.stderr.write(
                    self.style.WARNING(
                        f"No active sections on {campus.name}; skipping."
                    )
                )
                continue

            code = "".join(
                ch for ch in campus.name.upper() if ch.isalpha()
            )[:3] or f"CAMPUS{campus.id}"

            seq = 1
            created = 0

            for i in range(count):
                admission_number = f"PF-{code}-{seq:04d}"

                while Student.objects.filter(
                    admission_number=admission_number
                ).exists():
                    seq += 1
                    admission_number = f"PF-{code}-{seq:04d}"

                gender = self.GENDER_OPTIONS[i % 2]

                if "girls" in campus.name.lower():
                    gender = "female"
                elif "boys" in campus.name.lower():
                    gender = "male"

                first_names = (
                    self.FIRST_NAMES_FEMALE
                    if gender == "female"
                    else self.FIRST_NAMES_MALE
                )

                first_name = first_names[i % len(first_names)]
                last_name = self.LAST_NAMES[
                    (i + seq) % len(self.LAST_NAMES)
                ]

                guardian_name = (
                    f"{'Mrs.' if gender == 'female' else 'Mr.'} "
                    f"{last_name}"
                )

                guardian = Guardian.objects.create(
                    name=guardian_name,
                    relationship=(
                        "Mother" if gender == "female" else "Father"
                    ),
                    phone=f"0301-{seq:07d}",
                    alternate_phone="",
                    email="",
                    address=campus.city or "Sialkot",
                )

                year = 2026 - (4 + (i % 13))
                dob = date(year, ((i * 7) % 12) + 1, (i % 27) + 1)

                student = Student.objects.create(
                    admission_number=admission_number,
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=dob,
                    gender=gender,
                    guardian=guardian,
                    phone=f"0310-{seq:07d}",
                    address=campus.city or "Sialkot",
                    status="active",
                    admission_date=date(2026, 8, 1),
                )

                section = sections[i % len(sections)]

                Enrollment.objects.create(
                    student=student,
                    academic_year=academic_year,
                    campus=campus,
                    class_obj=section.class_obj,
                    section=section,
                    status="active",
                )

                seq += 1
                created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"{campus.name}: created {created} students."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Added up to {count} students per campus for "
                f"academic year {academic_year.name}."
            )
        )
