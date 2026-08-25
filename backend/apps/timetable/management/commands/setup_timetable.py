
from datetime import time

from django.core.management.base import BaseCommand

from apps.schools.models import (
    AcademicYear,
    Campus,
    SubjectOffering,
)
from apps.teachers.models import Teacher
from apps.timetable.models import Period, TimetableEntry


class Command(BaseCommand):
    help = "Create realistic timetable periods and timetable entries."

    DAYS = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
    ]

    PERIOD_DATA = [
        ("Period 1", 1, time(8, 0), time(8, 40), False),
        ("Period 2", 2, time(8, 40), time(9, 20), False),
        ("Period 3", 3, time(9, 20), time(10, 0), False),
        ("Period 4", 4, time(10, 0), time(10, 40), False),
        ("Break", 5, time(10, 40), time(11, 0), True),
        ("Period 5", 6, time(11, 0), time(11, 40), False),
        ("Period 6", 7, time(11, 40), time(12, 20), False),
        ("Period 7", 8, time(12, 20), time(13, 0), False),
    ]

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "\nSetting up timetable data...\n"
            )
        )

        academic_year = (
            AcademicYear.objects
            .filter(name="2026-2027")
            .select_related("school")
            .first()
        )

        if not academic_year:
            academic_year = (
                AcademicYear.objects
                .select_related("school")
                .order_by("-start_date")
                .first()
            )

        if not academic_year:
            self.stdout.write(
                self.style.ERROR(
                    "No academic year found."
                )
            )
            return

        self.stdout.write(
            f"Academic Year: {academic_year.school.name} - "
            f"{academic_year.name}\n"
        )

        periods = self.create_periods()

        self.create_timetables(
            academic_year,
            periods,
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Timetable setup completed successfully."
            )
        )

    def create_periods(self):
        periods = {}

        created_count = 0
        existing_count = 0

        self.stdout.write("Creating timetable periods...\n")

        for (
            name,
            number,
            start_time,
            end_time,
            is_break,
        ) in self.PERIOD_DATA:

            period, created = Period.objects.get_or_create(
                number=number,
                defaults={
                    "name": name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "is_break": is_break,
                    "status": "active",
                },
            )

            periods[number] = period

            if created:
                created_count += 1
                self.stdout.write(
                    f"Created period: {name}"
                )
            else:
                existing_count += 1

        self.stdout.write(
            f"\nPeriods created: {created_count}"
        )

        self.stdout.write(
            f"Periods already existed: {existing_count}\n"
        )

        return periods

    def create_timetables(
        self,
        academic_year,
        periods,
    ):
        campuses = (
            Campus.objects
            .all()
            .order_by("name")
        )

        total_created = 0
        total_existing = 0
        total_skipped = 0

        for campus in campuses:
            self.stdout.write(
                f"\nProcessing campus: {campus.name}"
            )

            classes = []

            for unit in campus.academic_units.all():
                classes.extend(
                    unit.classes.all()
                )

            if not classes:
                self.stdout.write(
                    self.style.WARNING(
                        "  No classes found."
                    )
                )
                continue

            for class_obj in classes:
                self.stdout.write(
                    f"  Processing class: "
                    f"{class_obj.name}"
                )

                sections = class_obj.sections.all()

                if not sections.exists():
                    self.stdout.write(
                        self.style.WARNING(
                            "    No sections found."
                        )
                    )
                    continue

                for section in sections:
                    (
                        created,
                        existing,
                        skipped,
                    ) = self.create_section_timetable(
                        academic_year,
                        campus,
                        class_obj,
                        section,
                        periods,
                    )

                    total_created += created
                    total_existing += existing
                    total_skipped += skipped

        self.stdout.write(
            f"\nTimetable entries created: "
            f"{total_created}"
        )

        self.stdout.write(
            f"Timetable entries already existed: "
            f"{total_existing}"
        )

        self.stdout.write(
            f"Timetable entries skipped: "
            f"{total_skipped}"
        )

    def create_section_timetable(
        self,
        academic_year,
        campus,
        class_obj,
        section,
        periods,
    ):
        offerings = list(
            SubjectOffering.objects
            .filter(
                academic_year=academic_year,
                class_obj=class_obj,
            )
            .select_related("subject")
            .order_by("subject__name")
        )

        if not offerings:
            self.stdout.write(
                self.style.WARNING(
                    f"    No subjects offered for "
                    f"{class_obj.name}."
                )
            )
            return 0, 0, 0

        teachers = list(
            Teacher.objects
            .filter(
                status="active",
            )
            .prefetch_related("assignments")
            .order_by(
                "first_name",
                "last_name",
            )
        )

        if not teachers:
            self.stdout.write(
                self.style.WARNING(
                    f"    No active teachers found."
                )
            )
            return 0, 0, 0

        created_count = 0
        existing_count = 0
        skipped_count = 0

        # Build a teacher lookup based on subject,
        # campus and class assignments.
        subject_teachers = {}

        for offering in offerings:
            matching_teachers = [
                teacher
                for teacher in teachers
                if self.teacher_can_teach_subject(
                    teacher,
                    offering.subject,
                    campus,
                    class_obj,
                )
            ]

            if matching_teachers:
                subject_teachers[
                    offering.subject_id
                ] = matching_teachers
            else:
                # If no specific assignment is found,
                # use active teachers as a fallback.
                subject_teachers[
                    offering.subject_id
                ] = teachers

        # Seven teaching periods.
        teaching_period_numbers = [
            1,
            2,
            3,
            4,
            6,
            7,
            8,
        ]

        subject_ids = [
            offering.subject_id
            for offering in offerings
        ]

        for day_index, day in enumerate(self.DAYS):

            for slot_index, period_number in enumerate(
                teaching_period_numbers
            ):
                if not subject_ids:
                    continue

                subject_id = subject_ids[
                    (
                        day_index
                        * len(teaching_period_numbers)
                        + slot_index
                    )
                    % len(subject_ids)
                ]

                offering = next(
                    (
                        item
                        for item in offerings
                        if item.subject_id == subject_id
                    ),
                    None,
                )

                if not offering:
                    skipped_count += 1
                    continue

                teacher = self.find_available_teacher(
                    subject_teachers.get(
                        subject_id,
                        teachers,
                    ),
                    academic_year,
                    day,
                    periods[period_number],
                )

                if not teacher:
                    skipped_count += 1
                    continue

                existing = (
                    TimetableEntry.objects
                    .filter(
                        academic_year=academic_year,
                        section=section,
                        day=day,
                        period=periods[
                            period_number
                        ],
                    )
                    .first()
                )

                if existing:
                    existing_count += 1
                    continue

                try:
                    entry = TimetableEntry(
                        academic_year=academic_year,
                        campus=campus,
                        class_obj=class_obj,
                        section=section,
                        subject=offering.subject,
                        teacher=teacher,
                        period=periods[
                            period_number
                        ],
                        day=day,
                        room=self.get_room(
                            campus,
                            class_obj,
                            section,
                        ),
                        status="active",
                    )

                    entry.full_clean()
                    entry.save()

                    created_count += 1

                except Exception as exc:
                    skipped_count += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"    Skipped "
                            f"{day} / "
                            f"{periods[period_number].name}: "
                            f"{exc}"
                        )
                    )

        return (
            created_count,
            existing_count,
            skipped_count,
        )

    def teacher_can_teach_subject(
        self,
        teacher,
        subject,
        campus=None,
        class_obj=None,
    ):
        """
        Check whether a teacher has an assignment matching
        the subject, campus and class.

        The Teacher model does NOT have a 'campuses' field.
        Teacher assignments are accessed through:
            teacher.assignments
        """

        assignments = teacher.assignments.all()

        for assignment in assignments:

            assignment_subject_id = getattr(
                assignment,
                "subject_id",
                None,
            )

            assignment_campus_id = getattr(
                assignment,
                "campus_id",
                None,
            )

            assignment_class_id = getattr(
                assignment,
                "class_obj_id",
                None,
            )

            # Subject must match when assignment specifies one.
            if (
                assignment_subject_id is not None
                and assignment_subject_id != subject.id
            ):
                continue

            # Campus must match when assignment specifies one.
            if (
                campus is not None
                and assignment_campus_id is not None
                and assignment_campus_id != campus.id
            ):
                continue

            # Class must match when assignment specifies one.
            if (
                class_obj is not None
                and assignment_class_id is not None
                and assignment_class_id != class_obj.id
            ):
                continue

            return True

        return False

    def find_available_teacher(
        self,
        teachers,
        academic_year,
        day,
        period,
    ):
        for teacher in teachers:

            conflict = (
                TimetableEntry.objects
                .filter(
                    academic_year=academic_year,
                    teacher=teacher,
                    day=day,
                    period=period,
                )
                .exists()
            )

            if not conflict:
                return teacher

        return None

    def get_room(
        self,
        campus,
        class_obj,
        section,
    ):
        return (
            f"{campus.name} - "
            f"{class_obj.name} "
            f"{section.name}"
        )

