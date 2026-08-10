
from django.core.management.base import BaseCommand

from apps.schools.models import (
    AcademicYear,
    Campus,
    Section,
    Subject,
    SubjectOffering,
)
from apps.teachers.models import Teacher, TeacherAssignment


TEACHERS = {
    "Junior Campus": [
        ("Ayaan", "Raza", "male"),
        ("Hiba", "Khan", "female"),
        ("Rayyan", "Malik", "male"),
        ("Maira", "Ahmed", "female"),
    ],
    "Girls Campus": [
        ("Ayesha", "Khan", "female"),
        ("Mariam", "Raza", "female"),
        ("Sana", "Malik", "female"),
        ("Zoya", "Ahmed", "female"),
        ("Hina", "Sheikh", "female"),
        ("Iqra", "Farooq", "female"),
        ("Mehwish", "Ali", "female"),
        ("Anaya", "Hassan", "female"),
    ],
    "Boys Campus": [
        ("Hamza", "Khan", "male"),
        ("Usman", "Raza", "male"),
        ("Bilal", "Ahmed", "male"),
        ("Saad", "Malik", "male"),
        ("Daniyal", "Sheikh", "male"),
        ("Talha", "Farooq", "male"),
        ("Haris", "Ali", "male"),
        ("Zain", "Hassan", "male"),
    ],
    "Haripur Campus": [
        ("Areeba", "Khan", "female"),
        ("Mahnoor", "Raza", "female"),
        ("Fatima", "Ahmed", "female"),
        ("Laiba", "Malik", "female"),
        ("Arham", "Sheikh", "male"),
        ("Huzaifa", "Farooq", "male"),
        ("Maryam", "Ali", "female"),
        ("Ibrahim", "Hassan", "male"),
        ("Eman", "Qureshi", "female"),
        ("Abdullah", "Khan", "male"),
    ],
    "Paris Road Campus": [
        ("Noor", "Ahmed", "female"),
        ("Yusuf", "Khan", "male"),
        ("Amina", "Raza", "female"),
        ("Omar", "Malik", "male"),
        ("Sara", "Sheikh", "female"),
        ("Hamza", "Farooq", "male"),
        ("Zainab", "Ali", "female"),
        ("Dawood", "Hassan", "male"),
    ],
}


class Command(BaseCommand):
    help = "Create teachers and assign them according to existing subject offerings."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "\nSetting up teachers and teacher assignments...\n"
            )
        )

        academic_year = (
            AcademicYear.objects
            .select_related("school")
            .filter(name="2026-2027")
            .first()
        )

        if not academic_year:
            self.stdout.write(
                self.style.ERROR(
                    "Academic Year 2026-2027 was not found."
                )
            )
            return

        self.stdout.write(
            f"Academic Year: {academic_year.school.name} - "
            f"{academic_year.name}\n"
        )

        total_teachers_created = 0
        total_assignments_created = 0

        for campus_name, teacher_list in TEACHERS.items():
            campus = Campus.objects.filter(
                name=campus_name
            ).first()

            if not campus:
                self.stdout.write(
                    self.style.WARNING(
                        f"Campus not found: {campus_name}"
                    )
                )
                continue

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nProcessing {campus.name}"
                )
            )

            teachers = []

            for index, (first_name, last_name, gender) in enumerate(
                teacher_list,
                start=1,
            ):
                employee_number = (
                    f"{campus.name[:2].upper()}-T-{index:03d}"
                )

                teacher, created = Teacher.objects.get_or_create(
                    employee_number=employee_number,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "gender": gender,
                        "status": "active",
                    },
                )

                teachers.append(teacher)

                if created:
                    total_teachers_created += 1
                    self.stdout.write(
                        f"  Created teacher: {teacher.full_name}"
                    )

            offerings = (
                SubjectOffering.objects
                .filter(
                    academic_year=academic_year,
                    class_obj__unit__campus=campus,
                )
                .select_related(
                    "subject",
                    "class_obj",
                    "class_obj__unit",
                )
                .order_by(
                    "class_obj__level",
                    "class_obj__name",
                    "subject__name",
                )
            )

            assignment_count = 0

            for offering in offerings:
                class_obj = offering.class_obj
                subject = offering.subject

                sections = Section.objects.filter(
                    class_obj=class_obj
                ).order_by("name")

                if not sections.exists():
                    section = Section.objects.create(
                        class_obj=class_obj,
                        name="A",
                        capacity=30,
                        status="active",
                    )
                    sections = [section]

                    self.stdout.write(
                        f"  Created section A for {class_obj.name}"
                    )

                # Deterministically choose a teacher based on
                # class + subject so repeated runs remain stable.
                teacher_index = (
                    class_obj.pk + subject.pk
                ) % len(teachers)

                teacher = teachers[teacher_index]

                for section in sections:
                    _, created = TeacherAssignment.objects.get_or_create(
                        teacher=teacher,
                        campus=campus,
                        class_obj=class_obj,
                        section=section,
                        subject=subject,
                        academic_year=academic_year,
                        defaults={
                            "role": "subject_teacher",
                            "status": "active",
                        },
                    )

                    if created:
                        assignment_count += 1
                        total_assignments_created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"{campus.name}: "
                    f"{len(teachers)} teachers, "
                    f"{assignment_count} new assignments."
                )
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Teacher setup completed successfully."
            )
        )

        self.stdout.write(
            f"Teachers created: {total_teachers_created}"
        )

        self.stdout.write(
            f"Assignments created: {total_assignments_created}"
        )

