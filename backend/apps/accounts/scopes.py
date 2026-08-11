"""Role-based scoping helpers.

These decide which records a user may see:

- **Managers** (super admin / admin / principal / academic) see everything.
- **Teachers** see only their assigned class: the students in it, plus the
  attendance and marks of those students.
- **Students** see only their own records.

Used by the list/detail views across the API.
"""

from django.db.models import Q

MANAGER_ROLES = ["super_admin", "admin", "principal", "academic"]
TEACHER_ROLE = "teacher"
STUDENT_ROLE = "student"


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


def get_teacher_profile(user):
    return getattr(user, "teacher_profile", None)


def get_student_profile(user):
    return getattr(user, "student_profile", None)


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


def teacher_student_ids(user):
    """Student ids enrolled (active) in the teacher's class(es)."""
    class_ids = teacher_class_ids(user)

    if not class_ids:
        return []

    from apps.students.models import Enrollment

    return list(
        Enrollment.objects.filter(
            class_obj_id__in=class_ids,
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
