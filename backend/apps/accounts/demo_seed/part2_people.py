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
def run(ctx):
    ctx.log("Part 2: people (teachers, staff, students, guardians, enrollments, class teachers).")

    from apps.accounts.models import InstitutionMembership, Role, StaffProfile, User
    from apps.schools.models import Class, Section
    from apps.teachers.models import Teacher, TeacherAssignment

    # ---------- 1. TEACHERS ----------
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

            # Teacher profile
            from apps.teachers.models import Teacher as TeacherModel
            emp_no = f"{code}-T{n:02d}"
            subject_codes = _subject_codes_for_class(f"Class {min(n, 10)}")
            # Note: Teacher.subjects is M2M to Subject; we'll link later
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
                    "employment_status": "active",
                    "contact": f"0311{n:07d}",
                },
            )
            if t_created:
                teacher.membership = base.membership(ctx, user)
                teacher.save(update_fields=["membership"])
            teacher_count += 1 if t_created else 0
            teacher_registry[(code, j)] = teacher

            # Link 3-4 subjects M2M
            from apps.schools.models import Subject
            subject_objs = Subject.objects.filter(
                institution=ctx.school, code__in=subject_codes[:4]
            )
            teacher.subjects.set(subject_objs)

            # TeacherAssignment for campus scope
            ta, ta_created = TeacherAssignment.objects.get_or_create(
                teacher=teacher,
                campus=campus,
                defaults={"status": "active"},
            )
            if ta_created:
                ctx.count("teacher_assignments")

    ctx.ok(f"Teachers: {teacher_count} created (registry size {len(teacher_registry)})")

    # ---------- 2. SUPPORT STAFF ----------
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

    # ---------- 3. STUDENTS + ENROLLMENTS ----------
    ctx.log("Creating students and enrollments...")
    from apps.students.models import Student, Enrollment

    student_created = 0
    enrollment_created = 0
    section_list = list(ctx.sections.values())
    # Map student index to section round-robin
    for i in range(1, TOTAL_STUDENTS + 1):
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

        adm_no = f"DEMO-{i:04d}"
        stu, s_created = Student.objects.get_or_create(
            institution=ctx.school,
            admission_number=adm_no,
            defaults={
                "user": user,
                "first_name": first,
                "last_name": last,
                "gender": "female" if i % 2 == 0 else "male",
                "date_of_birth": _dob_for_index(i),
                "admission_date": date(2026, 8, 10),
                "enrollment_status": "active",
                "primary_campus": campus,
                "academic_year": ctx.active_year,
            },
        )
        if s_created:
            student_created += 1
            ctx.count("students")
        # Link user if not linked
        if stu.user_id != user.id:
            stu.user = user
            stu.save(update_fields=["user"])

        # Assign to section (round-robin across sections of this campus)
        campus_sections = [s for s in section_list if s.class_obj.unit.campus_id == campus.id]
        if campus_sections:
            section = campus_sections[(seq - 1) % len(campus_sections)]
            stu.class_obj = section.class_obj
            stu.section = section
            stu.save(update_fields=["class_obj", "section"])

            # Enrollment
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

    ctx.ok(f"Students: {student_created}, Enrollments: {enrollment_created}")

    # ---------- 4. GUARDIANS + PARENT USERS ----------
    ctx.log("Creating guardians and parent users...")
    from apps.students.models import Guardian

    guardian_created = 0
    # deterministic mapping: 500 students -> 350 guardians (some guardians have 2-3 children)
    # guardian g covers students [g, g+350) with wraparound, but to keep it simple:
    # guardian i (1..350) gets students i, i+350 if <=500, and maybe i+700
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
                "contact": contact,
            },
        )
        if g_created:
            guardian_created += 1
            ctx.count("guardians")

        # Link children: students with index congruent to g mod 350 (so each guardian ~1-2 children)
        child_indices = []
        for offset in (0, 350, 700):
            idx = g + offset
            if 1 <= idx <= TOTAL_STUDENTS:
                child_indices.append(idx)
        for idx in child_indices:
            ci = (idx - 1) // STUDENTS_PER_CAMPUS
            code = CAMPUS_CODES[ci]
            seq = (idx - 1) % STUDENTS_PER_CAMPUS + 1
            adm_no = f"DEMO-{idx:04d}"
            try:
                stu = Student.objects.get(institution=ctx.school, admission_number=adm_no)
                if stu.guardian_id != guardian.id:
                    stu.guardian = guardian
                    stu.save(update_fields=["guardian"])
            except Student.DoesNotExist:
                pass

    ctx.ok(f"Guardians: {guardian_created}")

    # ---------- 5. CLASS TEACHERS ----------
    ctx.log("Creating class teacher assignments...")
    from apps.schools.models import ClassTeacher

    ct_created = 0
    for section_key, section in ctx.sections.items():
        campus_code = section_key.split(":")[0]
        # Assign round-robin among the 10 teachers of this campus
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

    # ---------- 6. SPECIAL STUDENTS (HealthRecord fallback) ----------
    ctx.log("Checking for special-student support...")
    from apps.health.models import HealthRecord
    special_created = 0
    for i in range(1, 21):  # first 20 students
        adm_no = f"DEMO-{i:04d}"
        try:
            stu = Student.objects.get(institution=ctx.school, admission_number=adm_no)
            # Check if Student has special needs flag
            if not hasattr(stu, "special_needs") and not hasattr(stu, "health_notes"):
                hr, created = HealthRecord.objects.get_or_create(
                    institution=ctx.school,
                    student=stu,
                    defaults={
                        "condition": "Special attention required",
                        "description": "Seeded as special-student placeholder (Student model lacks dedicated flag).",
                        "recorded_by": ctx.users.get("demo_superadmin"),
                        "status": "active",
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

    ctx.log("Part 2 done.")