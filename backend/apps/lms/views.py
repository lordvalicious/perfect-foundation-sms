from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, get_institution

from .models import Course, Lesson, LessonCompletion
from .serializers import CourseSerializer, LessonSerializer


def _user_teacher(request):
    return getattr(request.user, "teacher_profile", None)


def _user_student(request):
    return getattr(request.user, "student_profile", None)


def _get_scoped_course(request, course_id):
    """Return a Course if it belongs to the caller's institution; 404 otherwise.

    This replaces the unsafe ``get_object_or_404(Course, pk=...)`` pattern that
    let any authenticated user reach any course by guessing the ID.
    """
    return get_object_or_404(
        apply_campus_scope(Course.objects.all(), request),
        pk=course_id,
    )


def _assert_lesson_ownership(user, course, *,
                            require_teacher=False, require_staff_write=False):
    """Raise PermissionDenied unless the caller owns the course.

    ``require_teacher``: POST/PUT/DELETE paths — only the course teacher or a
    superuser may write.

    ``require_staff_write``: if True, a non-teacher staff member with
    ``require_staff_write`` may write (used where course.teacher can be None
    for staff-created ad-hoc content). For now, only teacher ownership is
    enforced (same as CourseDetailView).
    """
    if user.is_superuser:
        return

    teacher = getattr(user, "teacher_profile", None)

    if teacher is not None:
        if course.teacher_id == teacher.id:
            return
        raise PermissionDenied("You are not the teacher for this course.")

    if require_teacher:
        raise PermissionDenied("Only the course teacher may perform this action.")


class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Course.objects.select_related(
            "teacher", "campus", "class_obj", "subject"
        )

        queryset = apply_campus_scope(queryset, self.request)

        student = _user_student(self.request)

        if student is not None and not self.request.user.is_superuser:
            return queryset.filter(
                is_published=True,
                class_obj__in=student.enrollments.filter(
                    status="active"
                ).values("class_obj"),
            ).distinct()

        if not self.request.user.is_superuser:
            teacher = _user_teacher(self.request)

            if teacher is not None:
                queryset = queryset.filter(teacher=teacher)

        published = self.request.query_params.get("published")

        if published == "1":
            queryset = queryset.filter(is_published=True)

        return queryset

    def perform_create(self, serializer):
        teacher = _user_teacher(self.request)

        if teacher is None:
            raise PermissionDenied("Only teachers can create courses.")

        serializer.save(teacher=teacher)


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Course.objects.select_related(
            "teacher", "campus", "class_obj", "subject"
        )

        return apply_campus_scope(queryset, self.request)

    def perform_update(self, serializer):
        teacher = _user_teacher(self.request)

        if (
            teacher is None
            or serializer.instance.teacher_id != teacher.id
        ) and not self.request.user.is_superuser:
            raise PermissionDenied(
                "Only the course's teacher can edit it."
            )

        serializer.save()

    def perform_destroy(self, instance):
        teacher = _user_teacher(self.request)

        if (
            teacher is None
            or instance.teacher_id != teacher.id
        ) and not self.request.user.is_superuser:
            raise PermissionDenied(
                "Only the course's teacher can delete it."
            )

        instance.delete()


class LessonListCreateView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        course_id = self.kwargs.get("course_id")
        if not course_id:
            return Lesson.objects.none()

        # Institution- + campus-scoped course lookup (prevents cross-tenant lesson read).
        course = _get_scoped_course(self.request, course_id)

        user = self.request.user

        if user.is_superuser:
            return course.lessons.all()

        teacher = _user_teacher(self.request)
        if teacher is not None:
            if course.teacher_id != teacher.id:
                raise PermissionDenied("You do not have access to this course.")
            return course.lessons.all()

        student = _user_student(self.request)
        if student is not None:
            enrolled_course_ids = student.enrollments.filter(
                status="active"
            ).values_list("class_obj_id", flat=True)
            if course.class_obj_id not in enrolled_course_ids:
                raise PermissionDenied("Course not available.")
            return course.lessons.all()

        # Staff with no teacher/student profile get the course (now institution-scoped),
        # which is acceptable for read-only course materials access.
        return course.lessons.all()

    def perform_create(self, serializer):
        course_id = self.kwargs.get("course_id")
        if not course_id:
            raise PermissionDenied("Course ID is required.")

        course = _get_scoped_course(self.request, course_id)
        _assert_lesson_ownership(self.request.user, course, require_teacher=True)
        serializer.save(course=course)


class MarkLessonCompleteView(APIView):
    """POST toggle: students mark a lesson done / undo."""

    def post(self, request, lesson_id):
        student = _user_student(request)

        if student is None:
            raise PermissionDenied("Only students complete lessons.")

        # Fetch the lesson first so we have the course object available.
        lesson = get_object_or_404(Lesson.objects.select_related("course"), pk=lesson_id)

        # Institution gate: reject if the course belongs to another tenant.
        course = lesson.course
        institution = get_institution(request)
        if institution is not None and course.institution_id != institution.id:
            raise PermissionDenied("You do not have access to this lesson.")

        # Enrollment gate: student must have an active enrolment in the course class.
        user = request.user
        if not user.is_superuser:
            student_profile = getattr(user, "student_profile", None)
            if student_profile is None:
                raise PermissionDenied("No student profile.")
            if not student_profile.enrollments.filter(
                status="active", class_obj_id=course.class_obj_id
            ).exists():
                raise PermissionDenied("You are not enrolled in this course.")

        completion = LessonCompletion.objects.filter(
            lesson=lesson, student=student
        ).first()

        if completion:
            completion.delete()
            completed = False
        else:
            LessonCompletion.objects.create(
                lesson=lesson, student=student
            )
            completed = True

        total = course.lessons.count()
        done = LessonCompletion.objects.filter(
            student=student,
            lesson__course_id=course.id,
        ).count()

        progress = round(done / total * 100) if total else 0

        return Response({
            "completed": completed,
            "progress": progress,
        })


class MyProgressView(APIView):
    """GET per-course progress for the signed-in student."""

    def get(self, request):
        student = _user_student(request)

        if student is None:
            return Response([])

        from django.db.models import Count, Q

        courses = Course.objects.filter(
            is_published=True,
            class_obj__in=student.enrollments.filter(status="active").values(
                "class_obj"
            ),
        ).distinct()

        data = []

        for course in courses:
            total = course.lessons.count()
            done = LessonCompletion.objects.filter(
                student=student, lesson__course=course
            ).count()

            data.append({
                "course": course.title,
                "course_id": course.id,
                "lessons_done": done,
                "lessons_total": total,
                "progress": round(done / total * 100) if total else 0,
            })

        return Response(data)


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        course_id = self.kwargs.get("course_id")
        if not course_id:
            return Lesson.objects.none()

        course = _get_scoped_course(self.request, course_id)
        user = self.request.user

        if user.is_superuser:
            return course.lessons.all()

        teacher = _user_teacher(self.request)
        if teacher is not None:
            if course.teacher_id != teacher.id:
                raise PermissionDenied("You do not have access to this course.")
            return course.lessons.all()

        student = _user_student(self.request)
        if student is not None:
            enrolled_course_ids = student.enrollments.filter(
                status="active"
            ).values_list("class_obj_id", flat=True)
            if course.class_obj_id not in enrolled_course_ids:
                raise PermissionDenied("Course not available.")
            return course.lessons.all()

        return course.lessons.all()

    def perform_update(self, serializer):
        course_id = self.kwargs.get("course_id")
        if not course_id:
            raise PermissionDenied("Course ID is required.")
        course = _get_scoped_course(self.request, course_id)
        _assert_lesson_ownership(self.request.user, course, require_teacher=True)
        serializer.save(course=course)

    def perform_destroy(self, instance):
        _assert_lesson_ownership(self.request.user, instance.course, require_teacher=True)
        instance.delete()
