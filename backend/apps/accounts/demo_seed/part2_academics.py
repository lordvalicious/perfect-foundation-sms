"""Part 2 — Academics.

Creates (idempotently, scoped to DEMO-EDU / ctx.school / ctx.active_year):
- Subjects (10)
- Classes (13 per campus) under each campus AcademicUnit
- Sections (3 per class: A, B, C)
- SubjectOfferings for active year per class level rules
- SubjectGroup "Core Subjects"
- AcademicCalendar events per campus
- Periods (shared timetable periods)
"""

from __future__ import annotations

from datetime import date, time

from django.db import transaction

import apps.accounts.demo_seed.base as base
from apps.accounts.demo_seed.base import getc


SUBJECT_SPECS = [
    ("MAT", "Mathematics", "theory"),
    ("ENG", "English Language", "theory"),
    ("URD", "Urdu", "theory"),
    ("SCI", "General Science", "theory"),
    ("ISL", "Islamiyat", "theory"),
    ("SST", "Social Studies", "theory"),
    ("COM", "Computer Studies", "theory"),
    ("PHY", "Physics", "theory"),
    ("BIO", "Biology", "theory"),
    ("GK", "General Knowledge", "theory"),
]

CLASS_SPECS = [
    ("Playgroup", 0),
    ("Nursery", 1),
    ("Kindergarten", 2),
    ("Class 1", 3),
    ("Class 2", 4),
    ("Class 3", 5),
    ("Class 4", 6),
    ("Class 5", 7),
    ("Class 6", 8),
    ("Class 7", 9),
    ("Class 8", 10),
    ("Class 9", 11),
    ("Class 10", 12),
]

SECTION_NAMES = ["A", "B", "C"]
SECTION_CAPACITY = 40

PRIMARY_MIDDLE_SUBJECT_CODES = ["MAT", "ENG", "URD", "SCI", "ISL", "SST", "COM", "PHY", "BIO", "GK"]
EARLY_YEARS_SUBJECT_CODES = ["ENG", "URD", "MAT", "GK"]
SECONDARY_SUBJECT_CODES = ["MAT", "ENG", "URD", "SCI", "ISL", "PHY", "BIO", "COM", "SST"]

CORE_SUBJECT_CODES = ["MAT", "ENG", "URD", "SCI"]

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

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
TEACHING_PERIOD_NUMBERS = [1, 2, 3, 4, 6, 7, 8]


def _subjects_for_class(class_name: str) -> list[str]:
    if class_name in ("Playgroup", "Nursery", "Kindergarten"):
        return EARLY_YEARS_SUBJECT_CODES
    if class_name.startswith("Class ") and class_name.split()[1].isdigit():
        num = int(class_name.split()[1])
        if 1 <= num <= 8:
            return PRIMARY_MIDDLE_SUBJECT_CODES
        if 9 <= num <= 10:
            return SECONDARY_SUBJECT_CODES
    return PRIMARY_MIDDLE_SUBJECT_CODES


def _periods_per_week(class_name: str, subject_code: str) -> int:
    is_core = subject_code in CORE_SUBJECT_CODES
    if class_name in ("Playgroup", "Nursery", "Kindergarten"):
        return 4 if is_core else 3
    if class_name.startswith("Class "):
        num = int(class_name.split()[1])
        if 1 <= num <= 5:
            return 4 if is_core else 3
        if 6 <= num <= 8:
            return 4 if is_core else 3
        if 9 <= num <= 10:
            return 5 if is_core else 4
    return 3


def _is_compulsory(subject_code: str) -> bool:
    return subject_code in CORE_SUBJECT_CODES


@transaction.atomic
def run(ctx):
    ctx.log("Part 2: academics (subjects, classes, sections, offerings, calendar, periods).")

    from apps.schools.models import (
        AcademicCalendar,
        AcademicUnit,
        Class,
        Section,
        Subject,
        SubjectGroup,
        SubjectOffering,
    )
    from apps.timetable.models import Period

    year = ctx.active_year
    if not year:
        ctx.err("No active academic year in context.")
        return

    # -------------------------------------------------------------------------
    # 1. SUBJECTS
    # -------------------------------------------------------------------------
    ctx.log("Creating subjects...")
    subject_map = {}
    for code, name, subject_type in SUBJECT_SPECS:
        subj, created = Subject.objects.get_or_create(
            institution=ctx.school,
            code=code,
            defaults={
                "name": name,
                "subject_type": subject_type,
                "status": "active",
            },
        )
        subject_map[code] = subj
        if created:
            ctx.count("subjects")
    ctx.ok(f"Subjects: {len(subject_map)}")

    # -------------------------------------------------------------------------
    # 2. CLASSES (13 per campus, under campus AcademicUnit)
    # -------------------------------------------------------------------------
    ctx.log("Creating classes...")
    for campus_code, campus in ctx.campuses.items():
        unit = campus.academic_units.filter(name=f"{campus.name} Unit").first()
        if not unit:
            ctx.warn(f"No AcademicUnit found for {campus.name}; skipping classes.")
            continue

        for class_name, level in CLASS_SPECS:
            cls, created = Class.objects.get_or_create(
                unit=unit,
                name=class_name,
                defaults={
                    "level": level,
                    "status": "active",
                },
            )
            key = f"{campus_code}:{class_name}"
            ctx.classes[key] = cls
            if created:
                ctx.count("classes")
    ctx.ok(f"Classes: {len(ctx.classes)}")

    # -------------------------------------------------------------------------
    # 3. SECTIONS (3 per class)
    # -------------------------------------------------------------------------
    ctx.log("Creating sections...")
    for class_key, cls in ctx.classes.items():
        for sec_name in SECTION_NAMES:
            section, created = Section.objects.get_or_create(
                class_obj=cls,
                name=sec_name,
                defaults={
                    "capacity": SECTION_CAPACITY,
                    "status": "active",
                },
            )
            ctx.sections[f"{class_key}:{sec_name}"] = section
            if created:
                ctx.count("sections")
    ctx.ok(f"Sections: {len(ctx.sections)}")

    # -------------------------------------------------------------------------
    # 4. SUBJECT OFFERINGS (active year)
    # -------------------------------------------------------------------------
    ctx.log("Creating subject offerings for active year...")
    offering_count = 0
    for class_key, cls in ctx.classes.items():
        campus_code = class_key.split(":")[0]
        campus = ctx.campuses[campus_code]
        class_name = cls.name
        subject_codes = _subjects_for_class(class_name)

        for subj_code in subject_codes:
            subj = subject_map[subj_code]
            offering, created = SubjectOffering.objects.get_or_create(
                academic_year=year,
                class_obj=cls,
                subject=subj,
                defaults={
                    "status": "active",
                    "periods_per_week": _periods_per_week(class_name, subj_code),
                    "is_compulsory": _is_compulsory(subj_code),
                },
            )
            if created:
                offering_count += 1
                ctx.count("subject_offerings")
    ctx.ok(f"SubjectOfferings: {offering_count}")

    # -------------------------------------------------------------------------
    # 5. SUBJECT GROUP
    # -------------------------------------------------------------------------
    ctx.log("Creating subject group...")
    core_subjects = [subject_map[code] for code in CORE_SUBJECT_CODES if code in subject_map]
    group, created = SubjectGroup.objects.get_or_create(
        institution=ctx.school,
        code="CORE",
        defaults={
            "name": "Core Subjects",
            "description": "Core academic subjects offered across all levels.",
            "status": "active",
        },
    )
    if created:
        ctx.count("subject_groups")
    if core_subjects:
        group.subjects.set(core_subjects)
    ctx.ok("SubjectGroup: Core Subjects")

    # -------------------------------------------------------------------------
    # 6. ACADEMIC CALENDAR (per campus, active year)
    # -------------------------------------------------------------------------
    ctx.log("Creating academic calendar events...")
    calendar_events = [
        ("event", "Orientation Day", date(2026, 8, 17), date(2026, 8, 17), None, None, True),
        ("meeting", "Term One PTM", date(2026, 10, 23), date(2026, 10, 23), None, None, True),
        ("holiday_break", "Winter Break", date(2026, 12, 21), date(2027, 1, 3), None, None, True),
    ]
    cal_created = 0
    for campus in ctx.campuses.values():
        for event_type, title, start, end, start_time, end_time, is_all_day in calendar_events:
            _, created = AcademicCalendar.objects.get_or_create(
                institution=ctx.school,
                campus=campus,
                academic_year=year,
                title=title,
                start_date=start,
                defaults={
                    "event_type": event_type,
                    "description": f"Seeded by part2_academics for {campus.name}.",
                    "end_date": end,
                    "start_time": start_time,
                    "end_time": end_time,
                    "is_all_day": is_all_day,
                    "is_for_all_campuses": False,
                    "status": "published",
                    "created_by": ctx.users.get("demo_superadmin"),
                },
            )
            if created:
                cal_created += 1
                ctx.count("calendar_events")
    ctx.ok(f"AcademicCalendar events: {cal_created}")

    # -------------------------------------------------------------------------
    # 7. PERIODS (timetable periods, shared across school)
    # -------------------------------------------------------------------------
    ctx.log("Creating timetable periods...")
    period_created = 0
    for name, number, start_time, end_time, is_break in PERIOD_DATA:
        period, created = Period.objects.get_or_create(
            institution=ctx.school,
            number=number,
            defaults={
                "name": name,
                "start_time": start_time,
                "end_time": end_time,
                "is_break": is_break,
                "status": "active",
            },
        )
        if created:
            period_created += 1
            ctx.count("periods")
    ctx.ok(f"Periods: {period_created}")

    # -------------------------------------------------------------------------
    # 8. TIMETABLE ENTRIES
    # -------------------------------------------------------------------------
    # The generator (apps.timetable.generator.generate_timetable) requires
    # TeacherAssignment rows which are created in part2_people. It also iterates
    # all sections of a campus, so it is not safely scoped to our seed data.
    # We create Periods above; actual TimetableEntry rows (which require a
    # Teacher FK) will be created in part2_people after teachers exist.
    ctx.note("TimetableEntry creation deferred to part2_people (requires Teacher rows).")

    ctx.log("Part 2 done.")