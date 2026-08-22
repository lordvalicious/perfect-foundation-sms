"""Role-based scoping helpers.

These decide which records a user may see:

- **Managers** (super admin / admin / principal / academic) see everything.
- **Teachers** see only their assigned class: the students in it, plus the
  attendance and marks of those students.
- **Students** see only their own records.

Used by the list/detail views across the API.
"""

from django.db.models import Q

MANAGER_ROLES = [
    "super_admin",
    "admin",
    "principal",
    "vice_principal",
    "campus_admin",
    "academic",
]
TEACHER_ROLE = "teacher"
STUDENT_ROLE = "student"
PARENT_ROLE = "parent"


def is_manager(user):
    if not (user and user.is_authenticated):
        return False

    return user.is_superuser or user.has_any_role(MANAGER_ROLES)


def is_teacher(user):
    if not (user and user.is_authenticated):
        return False

    return user.has_any_role([TEACHER_ROLE]) and not is_manager(user)


def is_student(user):
    if not (user and user.is_authenticated):
        return False

    return user.has_any_role([STUDENT_ROLE]) and not is_manager(user)


def is_parent(user):
    if not (user and user.is_authenticated):
        return False

    return user.has_any_role([PARENT_ROLE]) and not is_manager(user)


def get_teacher_profile(user):
    return getattr(user, "teacher_profile", None)


def get_student_profile(user):
    return getattr(user, "student_profile", None)


def get_guardian_profile(user):
    return getattr(user, "guardian_profile", None)


def teacher_class_ids(user):
    """Class ids the user is the assigned class teacher of (active year)."""
    profile = get_teacher_profile(user)

    if profile is None:
        return []

    from apps.teachers.models import TeacherAssignment

    return list(
        TeacherAssignment.objects.filter(
            teacher=profile,
            role="class_teacher",
            status="active",
        ).values_list("class_obj_id", flat=True)
    )


def teacher_can_access_section(user, class_id, section_id):
    """Whether the user is the class teacher of this exact class/section."""
    profile = get_teacher_profile(user)

    if profile is None:
        return False

    from apps.teachers.models import TeacherAssignment

    return (
        TeacherAssignment.objects.filter(
            teacher=profile,
            role="class_teacher",
            status="active",
            class_obj_id=class_id,
            section_id=section_id,
        ).exists()
    )


def teacher_section_pairs(user):
    """(class, section) pairs the user is the class teacher of (active year)."""
    profile = get_teacher_profile(user)

    if profile is None:
        return []

    from apps.teachers.models import TeacherAssignment

    return list(
        TeacherAssignment.objects.filter(
            teacher=profile,
            role="class_teacher",
            status="active",
        ).values_list("class_obj_id", "section_id")
    )


def teacher_student_ids(user):
    """Student ids enrolled (active) in the teacher's class(es)."""
    pairs = teacher_section_pairs(user)

    if not pairs:
        return []

    from apps.students.models import Enrollment

    q = Q()
    for class_id, section_id in pairs:
        q |= Q(class_obj_id=class_id, section_id=section_id)

    return list(
        Enrollment.objects.filter(
            q,
            status="active",
        ).values_list("student_id", flat=True)
    )


def student_class_ids(user):
    """Class ids the logged-in student is actively enrolled in."""
    profile = get_student_profile(user)

    if profile is None:
        return []

    from apps.students.models import Enrollment

    return list(
        Enrollment.objects.filter(
            student=profile,
            status="active",
        ).values_list("class_obj_id", flat=True)
    )


def teacher_scope_filter(user):
    """Q filter restricting a Student queryset to the teacher's class."""
    student_ids = teacher_student_ids(user)

    if not student_ids:
        return Q(pk__in=[])

    return Q(pk__in=student_ids)


def parent_student_ids(user):
    """Student ids linked to the logged-in parent's guardian profile."""
    profile = get_guardian_profile(user)

    if profile is None:
        return []

    from apps.students.models import Student, StudentGuardian

    linked_ids = StudentGuardian.objects.filter(
        guardian=profile,
    ).values_list("student_id", flat=True)
    return list(
        Student.objects.filter(
            Q(guardian=profile) | Q(id__in=linked_ids),
        ).values_list("id", flat=True)
    )


def parent_student_class_ids(user):
    """Class ids of the logged-in parent's children (active year)."""
    student_ids = parent_student_ids(user)

    if not student_ids:
        return []

    from apps.students.models import Enrollment

    return list(
        Enrollment.objects.filter(
            student_id__in=student_ids,
            status="active",
        ).values_list("class_obj_id", flat=True)
    )


def parent_scope_filter(user):
    """Q filter restricting a Student queryset to the parent's children."""
    student_ids = parent_student_ids(user)

    if not student_ids:
        return Q(pk__in=[])

    return Q(pk__in=student_ids)
