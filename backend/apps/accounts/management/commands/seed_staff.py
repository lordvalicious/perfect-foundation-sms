from datetime import date
from random import choice, randint, sample

from django.core.management.base import BaseCommand

from apps.accounts.models import StaffProfile
from apps.schools.models import Campus


class Command(BaseCommand):
    help = (
        "Add fictional non-teaching staff (janitors, guards, nurses, "
        "etc.) to every active campus."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=15,
            help="Number of new staff members to create per campus.",
        )

    FIRST_NAMES_MALE = [
        "Adnan", "Aslam", "Bashir", "Dawood", "Faheem", "Ghulam",
        "Haider", "Ijaz", "Javed", "Kashif", "Latif", "Mansoor",
        "Nadeem", "Pervaiz", "Rasheed", "Saleem", "Tariq", "Umer",
        "Waseem", "Younis", "Zafar", "Abbas", "Bilal", "Faisal",
    ]

    FIRST_NAMES_FEMALE = [
        "Amina", "Asma", "Bushra", "Farzana", "Ghazala", "Hina",
        "Ishrat", "Jamila", "Kausar", "Lubna", "Mehwish", "Nazia",
        "Parveen", "Rukhsana", "Saima", "Tahira", "Uzma", "Yasmin",
        "Zahida", "Anila", "Bano", "Fozia", "Kanwal", "Shaista",
    ]

    LAST_NAMES = [
        "Awan", "Bajwa", "Chaudhry", "Dasti", "Gujjar", "Hameed",
        "Irshad", "Jatala", "Kaleem", "Lashari", "Mughal", "Nazir",
        "Ojha", "Qadir", "Rafiq", "Sial", "Toor", "Ullah",
        "Virk", "Wattoo", "Yaqub", "Zaman", "Bhatti", "Cheema",
    ]

    DESIGNATIONS = [
        {"designation": "Janitor", "department": "Maintenance", "gender": "male"},
        {"designation": "Security Guard", "department": "Security", "gender": "male"},
        {"designation": "Nurse", "department": "Health", "gender": "female"},
        {"designation": "Librarian", "department": "Library", "gender": "female"},
        {"designation": "Clerk", "department": "Administration", "gender": "male"},
        {"designation": "Accountant", "department": "Accounts", "gender": "male"},
        {"designation": "Driver", "department": "Transport", "gender": "male"},
        {"designation": "Cook", "department": "Kitchen", "gender": "female"},
        {"designation": "Gardener", "department": "Grounds", "gender": "male"},
        {"designation": "Counsellor", "department": "Student Services", "gender": "female"},
        {"designation": "Lab Assistant", "department": "Student Services", "gender": "male"},
        {"designation": "Administrative Officer", "department": "Administration", "gender": "female"},
        {"designation": "Cleaner", "department": "Maintenance", "gender": "female"},
        {"designation": "Technician", "department": "Maintenance", "gender": "male"},
        {"designation": "Gatekeeper", "department": "Security", "gender": "male"},
    ]

    def handle(self, *args, **options):
        count = max(options["count"], 0)

        campuses = list(
            Campus.objects.filter(status="active").order_by("id")
        )

        if not campuses:
            self.stderr.write(
                self.style.ERROR("No active campuses found.")
            )
            return

        if count == 0:
            self.stdout.write("Count is 0, nothing to do.")
            return

        total = 0

        for campus in campuses:
            self.stdout.write(f"\nProcessing {campus.name}...")

            code = "".join(
                ch for ch in campus.name.upper() if ch.isalpha()
            )[:3] or f"CAMPUS{campus.id}"

            seq = 1
            created = 0

            for i in range(count):
                employee_number = f"PF-{code}-{seq:04d}"

                while StaffProfile.objects.filter(
                    employee_number=employee_number
                ).exists():
                    seq += 1
                    employee_number = f"PF-{code}-{seq:04d}"

                spec = self.DESIGNATIONS[i % len(self.DESIGNATIONS)]

                if "girls" in campus.name.lower():
                    gender = "female"
                elif "boys" in campus.name.lower():
                    gender = "male"
                else:
                    gender = spec["gender"]

                first_names = (
                    self.FIRST_NAMES_FEMALE
                    if gender == "female"
                    else self.FIRST_NAMES_MALE
                )

                first_name = first_names[i % len(first_names)]
                last_name = self.LAST_NAMES[
                    (i + seq) % len(self.LAST_NAMES)
                ]

                year = randint(1975, 1998)
                dob = date(
                    year,
                    randint(1, 12),
                    randint(1, 28),
                )

                joining_year = randint(2015, 2025)
                joining_date = date(
                    joining_year,
                    randint(1, 12),
                    randint(1, 28),
                )

                department = spec["department"]

                if "girls" in campus.name.lower() and department == "Health":
                    designation = choice(
                        ["Nurse", "Lady Health Worker"]
                    )
                else:
                    designation = spec["designation"]

                StaffProfile.objects.create(
                    employee_number=employee_number,
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    date_of_birth=dob,
                    phone=f"03{randint(10,49)}-{seq:07d}",
                    email="",
                    campus=campus.name,
                    designation=designation,
                    department=department,
                    joining_date=joining_date,
                    status="active",
                )

                seq += 1
                created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"{campus.name}: created {created} staff members."
                )
            )

            total += created

        sample_staff = list(
            StaffProfile.objects.order_by("?")[:5]
        )

        for member in sample_staff:
            member.status = choice(["active", "active", "inactive"])
            member.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Added {total} staff members across "
                f"{len(campuses)} campuses."
            )
        )
