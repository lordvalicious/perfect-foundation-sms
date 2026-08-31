"""Part 2 — People.

Creates (idempotently, scoped to DEMO-EDU / ctx.school / ctx.active_year):
- Teachers (50: 10 per campus)
- Support staff (50: 10 per campus via StaffProfile)
- Students (500: 100 per campus) with Enrollment
- Guardians (350) + Parent users
- ClassTeacher assignments (one per section)
- HealthRecords for "special students" where Student model lacks a flag
"""

from __future__ import annotations

from datetime import date

from django.db import transaction

import apps.accounts.demo_seed.base as base
from apps.accounts.demo_seed.base import getc

CAMPUS_CODES = ["GVC", "CSC", "BFC", "KHC", "EXC"]
TEACHERS_PER_CAMPUS = 10
STAFF_PER_CAMPUS = 10
STUDENTS_PER_CAMPUS = 100
TOTAL_STUDENTS = 500
TOTAL_GUARDIANS = 350

DESIGNATIONS = [
    ("Janitor", "Maintenance"),
    ("Security Guard", "Security"),
    ("Nurse", "Health"),
    ("Cook", "Kitchen"),
    ("Gardener", "Grounds"),
    ("Lab Assistant", "Student Services"),
    ("Cleaner", "Maintenance"),
    ("Technician", "Maintenance"),
    ("Gatekeeper", "Security"),
    ("Driver", "Transport"),
]


def _subject_codes_for_class(class_name: str) -> list[str]:
    if class_name in ("Playgroup", "Nursery", "Kindergarten"):
        return ["ENG", "URD", "MAT", "GK"]
    if class_name.startswith("Class "):
        num = int(class_name.split()[1])
        if 1 <= num <= 8:
            return ["MAT", "ENG", "URD", "SCI", "ISL", "SST", "COM", "PHY", "BIO", "GK"]
        if 9 <= num <= 10:
            return ["MAT", "ENG", "URD", "SCI", "ISL", "PHY", "BIO", "COM", "SST"]
    return ["MAT", "ENG", "URD", "SCI", "ISL", "SST", "COM", "PHY", "BIO", "GK"]


def _dob_for_index(idx: int) -> date:
    year = 2000 + (idx % 18)
    month = (idx % 12) + 1
    day = (idx % 27) + 1
    return date(year, month, day)


@transaction.atomic
def seed_teachers(ctx):
    """Create 50 teachers (10 per campus) + TeacherAssignment. Idempotent."""
    from apps.accounts.models import Role
    from apps.teachers.models import Teacher as TeacherModel, TeacherAssignment

    ctx.log("Creating teachers...")
    teacher_count = 0
    teacher_registry = {}

    for ci, code in enumerate(CAMPUS_CODES):
        campus = ctx.campuses[code]
        for j in range(TEACHERS_PER_CAMPUS):
            n = ci * TEACHERS_PER_CAMPUS + j + 1
            username = f"teacher.{code}.{j+1:02d}"
            email = f"teacher.{code}.{j+1:02d}@example.test"
            first = "Teacher"
            last = f"{n:02d}"

            user, created = base.make_user(ctx, username, email, first, last)
            if created:
                base.membership(ctx, user)
            base.assign_roles(ctx, user, [Role.TEACHER])

            emp_no = f"{code}-T{n:02d}"
            teacher, t_created = TeacherModel.objects.get_or_create(
                institution=ctx.school,
                employee_number=emp_no,
                defaults={
                    "user": user,
                    "primary_campus": campus,
                    "first_name": first,
                    "last_name": last,
                    "gender": "female" if n % 2 == 0 else "male",
                    "date_of_birth": date(1985 + (n % 20), (n % 12) + 1, (n % 27) + 1),
                    "phone": f"0311{n:07d}",
                    "email": email,
                    "department": "Academics",
                    "designation": "Teacher",
                    "joining_date": date(2015 + (n % 10), 8, 1),
                    "status": "active",
                },
            )
            if t_created:
                teacher.membership = base.membership(ctx, user)
                teacher.save(update_fields=["membership"])
            teacher_count += 1 if t_created else 0
            teacher_registry[(code, j)] = teacher

            if t_created:
                from apps.schools.models import Subject, Section as SecModel
                campus_classes = list(
                    SecModel.objects.filter(
                        class_obj__unit__campus=campus
                    ).select_related("class_obj").order_by("id")
                )
                if campus_classes:
                    sec = campus_classes[j % len(campus_classes)]
                    subj = Subject.objects.filter(
                        institution=ctx.school
                    ).order_by("id")[j % 10]
                    ta, ta_created = TeacherAssignment.objects.get_or_create(
                        teacher=teacher,
                        class_obj=sec.class_obj,
                        section=sec,
                        subject=subj,
                        academic_year=ctx.active_year,
                        defaults={"campus": campus, "role": "subject_teacher", "status": "active"},
                    )
                    if ta_created:
                        ctx.count("teacher_assignments")

    ctx.teacher_registry = teacher_registry
    ctx.ok(f"Teachers: {teacher_count} created (registry size {len(teacher_registry)})")


@transaction.atomic
def seed_support_staff(ctx):
    """Create 50 support staff via StaffProfile. Idempotent."""
    from apps.accounts.models import Role

    ctx.log("Creating support staff...")
    staff_count = 0
    for ci, code in enumerate(CAMPUS_CODES):
        campus = ctx.campuses[code]
        for j in range(STAFF_PER_CAMPUS):
            n = ci * STAFF_PER_CAMPUS + j + 1
            username = f"staff.{code}.{j+1:02d}"
            email = f"staff.{code}.{j+1:02d}@example.test"
            first = "Staff"
            last = f"{n:02d}"
            designation, department = DESIGNATIONS[j]

            user, created = base.make_user(ctx, username, email, first, last)
            if created:
                base.membership(ctx, user)
            base.assign_roles(ctx, user, [Role.STAFF])

            gender = "female" if n % 2 == 0 else "male"
            base.staff_profile(
                ctx, user, first, last,
                designation=designation,
                campus=campus,
                department=department,
                gender=gender,
                joining_date=date(2016 + (n % 8), (n % 12) + 1, (n % 27) + 1),
            )
            staff_count += 1 if created else 0
    ctx.ok(f"Support staff: {staff_count}")


@transaction.atomic
def seed_guardians(ctx):
    """Create 350 guardian + parent user accounts. Idempotent."""
    from apps.accounts.models import Role
    from apps.students.models import Guardian

    ctx.log("Creating guardians and parent users...")
    guardian_created = 0
    guardian_registry = {}
    for g in range(1, TOTAL_GUARDIANS + 1):
        username = f"parent.{g:04d}"
        email = f"parent.{g:04d}@example.test"
        first = "Parent"
        last = f"{g:03d}"

        user, u_created = base.make_user(ctx, username, email, first, last)
        if u_created:
            base.membership(ctx, user)
        base.assign_roles(ctx, user, [Role.PARENT])

        name = f"Parent {g:03d}"
        relationship = "Father" if g % 2 == 0 else "Mother"
        contact = f"0300{g:07d}"

        guardian, g_created = Guardian.objects.get_or_create(
            institution=ctx.school,
            user=user,
            defaults={
                "name": name,
                "relationship": relationship,
                "phone": contact,
            },
        )
        if g_created:
            guardian_created += 1
            ctx.count("guardians")
        guardian_registry[g] = guardian
    ctx.guardian_registry = guardian_registry
    ctx.ok(f"Guardians: {guardian_created}")


def seed_students(ctx):
    """Create 500 students (100 per campus) + Enrollments. Idempotent.
    Rebuilds the guardian registry from the DB if not present in-memory."""
    from apps.accounts.models import Role
    from apps.students.models import Student, Enrollment, Guardian

    ctx.log("Creating students and enrollments...")
    if not getattr(ctx, "guardian_registry", None):
        ctx.guardian_registry = {
            g.id: g
            for g in Guardian.objects.filter(institution=ctx.school)
        }
    guardian_registry = ctx.guardian_registry

    student_created = 0
    enrollment_created = 0
    section_list = list(ctx.sections.values())
    BATCH = 100
    for batch_start in range(1, TOTAL_STUDENTS + 1, BATCH):
        batch_end = min(batch_start + BATCH, TOTAL_STUDENTS + 1)
        with transaction.atomic():
            for i in range(batch_start, batch_end):
                ci = (i - 1) // STUDENTS_PER_CAMPUS
                code = CAMPUS_CODES[ci]
                campus = ctx.campuses[code]
                seq = (i - 1) % STUDENTS_PER_CAMPUS + 1

                username = f"student.{code}.{seq:02d}"
                email = f"student.{code}.{seq:02d}@example.test"
                first = "Student"
                last = f"{i:03d}"

                user, u_created = base.make_user(ctx, username, email, first, last)
                if u_created:
                    base.membership(ctx, user)
                base.assign_roles(ctx, user, [Role.STUDENT])

                guardian = guardian_registry[i if i <= TOTAL_GUARDIANS else i - TOTAL_GUARDIANS]

                adm_no = f"DEMO-{i:04d}"
                stu, s_created = Student.objects.get_or_create(
                    institution=ctx.school,
                    admission_number=adm_no,
                    defaults={
                        "guardian": guardian,
                        "user": user,
                        "first_name": first,
                        "last_name": last,
                        "gender": "female" if i % 2 == 0 else "male",
                        "date_of_birth": _dob_for_index(i),
                        "admission_date": date(2026, 8, 10),
                        "status": "active",
                        "primary_campus": campus,
                    },
                )
                if s_created:
                    student_created += 1
                    ctx.count("students")
                if stu.user_id != user.id:
                    stu.user = user
                    stu.save(update_fields=["user"])
                if stu.guardian_id != guardian.id:
                    stu.guardian = guardian
                    stu.save(update_fields=["guardian"])

                campus_sections = [s for s in section_list if s.class_obj.unit.campus_id == campus.id]
                if campus_sections:
                    section = campus_sections[(seq - 1) % len(campus_sections)]
                    enr, e_created = Enrollment.objects.get_or_create(
                        student=stu,
                        academic_year=ctx.active_year,
                        defaults={
                            "campus": campus,
                            "class_obj": section.class_obj,
                            "section": section,
                            "roll_number": seq,
                            "status": "active",
                        },
                    )
                    if e_created:
                        enrollment_created += 1
                        ctx.count("enrollments")

        ctx.log(f"... students seeded so far: {batch_end - 1} (committed)")

    ctx.ok(f"Students: {student_created}, Enrollments: {enrollment_created}")


@transaction.atomic
def seed_class_teachers(ctx):
    """Assign a class teacher to every section. Idempotent."""
    from apps.schools.models import ClassTeacher

    ctx.log("Creating class teacher assignments...")
    teacher_registry = getattr(ctx, "teacher_registry", None)
    if not teacher_registry:
        raise RuntimeError(
            "Part 2 class-teacher seeding needs the in-memory teacher registry. "
            "Run seed_demo_data --part=2 (teachers step) first."
        )

    ct_created = 0
    for section_key, section in ctx.sections.items():
        campus_code = section_key.split(":")[0]
        teacher_idx = hash(section_key) % TEACHERS_PER_CAMPUS
        teacher = teacher_registry.get((campus_code, teacher_idx))
        if teacher:
            ct, created = ClassTeacher.objects.get_or_create(
                section=section,
                academic_year=ctx.active_year,
                defaults={"teacher": teacher, "status": "active"},
            )
            if created:
                ct_created += 1
                ctx.count("class_teachers")
    ctx.ok(f"ClassTeachers: {ct_created}")


@transaction.atomic
def seed_special_students(ctx):
    """Create HealthRecord placeholders for 20 'special' students. Idempotent."""
    from apps.students.models import Student
    from apps.health.models import HealthRecord

    ctx.log("Checking for special-student support...")
    special_created = 0
    for i in range(1, 21):
        adm_no = f"DEMO-{i:04d}"
        try:
            stu = Student.objects.get(institution=ctx.school, admission_number=adm_no)
            if not hasattr(stu, "special_needs") and not hasattr(stu, "health_notes"):
                hr, created = HealthRecord.objects.get_or_create(
                    institution=ctx.school,
                    student=stu,
                    defaults={
                        "campus": stu.primary_campus,
                        "record_type": "general_checkup",
                        "record_date": date(2026, 9, 15),
                        "notes": "Special attention required (seeded placeholder; Student model lacks dedicated flag).",
                        "recorded_by": ctx.users.get("demo_superadmin"),
                    },
                )
                if created:
                    special_created += 1
                    ctx.count("health_records")
        except Student.DoesNotExist:
            pass
    if special_created:
        ctx.warn("Student model lacks special_needs flag; created HealthRecord entries for 20 students.")
    ctx.ok(f"Special student records (HealthRecord): {special_created}")


@transaction.atomic
def run(ctx):
    ctx.log("Part 2: people (teachers, staff, students, guardians, enrollments, class teachers).")
    seed_teachers(ctx)
    seed_support_staff(ctx)
    seed_guardians(ctx)
    seed_students(ctx)
    seed_class_teachers(ctx)
    seed_special_students(ctx)
    ctx.log("Part 2 done.")