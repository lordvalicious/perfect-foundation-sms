import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.accounts.models import StaffProfile
from apps.hr.models import Employee, EmploymentContract, PerformanceReview, EmploymentEvent
from apps.schools.models import Campus, School
from apps.teachers.models import Teacher


class Command(BaseCommand):
    help = "Seed HR data: employees, contracts, performance reviews, employment events."

    DESIGNATIONS = [
        "Senior Teacher", "Junior Teacher", "Head of Department",
        "Vice Principal", "Lab Incharge", "Sports Coordinator",
        "Librarian", "Admin Officer", "Accounts Manager",
        "IT Support", "Counsellor", "Coordinator",
    ]

    DEPARTMENTS = [
        "Academic", "Administration", "Accounts", "IT",
        "Student Services", "Library", "Sports", "Maintenance",
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\nSeeding HR data...\n"))

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
        teachers = list(Teacher.objects.filter(status="active"))
        staff_profiles = list(StaffProfile.objects.filter(status="active"))

        if not teachers and not staff_profiles:
            self.stderr.write(self.style.ERROR("No teachers or staff found. Run teacher/staff seeders first."))
            return

        admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

        emp_created = 0
        contracts_created = 0
        reviews_created = 0
        events_created = 0

        employee_list = []

        for i, teacher in enumerate(teachers):
            campus = campuses[i % len(campuses)] if campuses else None
            designation = random.choice(self.DESIGNATIONS)
            dept = random.choice(self.DEPARTMENTS)
            joining = date.today() - timedelta(days=random.randint(365, 3650))

            emp, created = Employee.objects.get_or_create(
                institution=school,
                teacher=teacher,
                defaults={
                    "employee_number": f"EMP-T-{teacher.pk:04d}",
                    "primary_campus": campus,
                    "designation": designation,
                    "department": dept,
                    "joining_date": joining,
                    "status": "active",
                },
            )
            if created:
                emp_created += 1
            employee_list.append(emp)

        for i, staff in enumerate(staff_profiles):
            campus = campuses[i % len(campuses)] if campuses else None
            designation = staff.designation or random.choice(self.DESIGNATIONS)
            dept = staff.department or random.choice(self.DEPARTMENTS)
            joining = staff.joining_date or (date.today() - timedelta(days=random.randint(365, 3650)))

            emp, created = Employee.objects.get_or_create(
                institution=school,
                staff_profile=staff,
                defaults={
                    "employee_number": f"EMP-S-{staff.pk:04d}",
                    "primary_campus": campus,
                    "designation": designation,
                    "department": dept,
                    "joining_date": joining,
                    "status": "active",
                },
            )
            if created:
                emp_created += 1
            employee_list.append(emp)

        for i, emp in enumerate(employee_list):
            contract_num = f"CON-{emp.employee_number}-01"

            salary = Decimal(str(random.randint(30000, 120000)))

            contract, created = EmploymentContract.objects.get_or_create(
                employee=emp,
                contract_number=contract_num,
                defaults={
                    "contract_type": random.choice(["Permanent", "Contract", "Probation"]),
                    "start_date": emp.joining_date or date.today() - timedelta(days=365),
                    "end_date": (emp.joining_date or date.today()) + timedelta(days=random.choice([365, 730, 1095])) if random.random() < 0.3 else None,
                    "salary": salary,
                    "terms": "Standard employment terms as per school policy.",
                    "status": "active",
                },
            )
            if created:
                contracts_created += 1

            if random.random() < 0.4 and admin_user:
                rating = random.randint(1, 5)
                review, created = PerformanceReview.objects.get_or_create(
                    employee=emp,
                    reviewer=admin_user,
                    period=random.choice(["Q1 2026", "Q2 2026", "H1 2026", "Annual 2025-26"]),
                    defaults={
                        "review_date": date.today() - timedelta(days=random.randint(30, 180)),
                        "rating": rating,
                        "strengths": random.choice([
                            "Excellent classroom management and student engagement.",
                            "Strong subject knowledge and effective teaching methods.",
                            "Great at collaborating with other staff members.",
                            "Very dedicated and punctual.",
                            "Innovative approach to curriculum delivery.",
                        ]),
                        "improvements": random.choice([
                            "Could improve use of technology in lessons.",
                            "Should participate more in school events.",
                            "Needs to improve documentation and record keeping.",
                            "Could take more initiative in department meetings.",
                            "Better time management during assessments.",
                        ]),
                        "goals": random.choice([
                            "Complete professional development course.",
                            "Lead a school project next term.",
                            "Improve student pass rate by 10%.",
                            "Mentor junior teachers.",
                            "Organize an inter-school event.",
                        ]),
                        "status": random.choice(["draft", "final"]),
                    },
                )
                if created:
                    reviews_created += 1

            if random.random() < 0.2:
                campus_from = random.choice(campuses) if campuses else None
                campus_to = random.choice(campuses) if campuses else None

                event, created = EmploymentEvent.objects.get_or_create(
                    employee=emp,
                    event_type=random.choice(["joined", "promoted", "transferred", "status_changed"]),
                    defaults={
                        "effective_date": emp.joining_date or date.today() - timedelta(days=random.randint(30, 365)),
                        "from_campus": campus_from,
                        "to_campus": campus_to,
                        "previous_designation": "Junior Teacher" if random.random() < 0.5 else "",
                        "new_designation": emp.designation,
                        "reason": random.choice([
                            "Promoted based on performance review.",
                            "Transferred to meet campus staffing needs.",
                            "Initial joining record.",
                            "Role change per departmental requirements.",
                        ]),
                        "recorded_by": admin_user,
                    },
                )
                if created:
                    events_created += 1

        self.stdout.write(self.style.SUCCESS(f"\nEmployees created: {emp_created}"))
        self.stdout.write(self.style.SUCCESS(f"Employment contracts created: {contracts_created}"))
        self.stdout.write(self.style.SUCCESS(f"Performance reviews created: {reviews_created}"))
        self.stdout.write(self.style.SUCCESS(f"Employment events created: {events_created}"))
        self.stdout.write(self.style.SUCCESS("\nHR seeding completed.\n"))
