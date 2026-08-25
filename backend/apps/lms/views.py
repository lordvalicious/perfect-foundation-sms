from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope

from .models import Course, Lesson, LessonCompletion
from .serializers import CourseSerializer, LessonSerializer


def _user_teacher(request):
    return getattr(request.user, "teacher_profile", None)


def _user_student(request):
    return getattr(request.user, "student_profile", None)


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
        course = get_object_or_404(Course, pk=self.kwargs["course_id"])
        return course.lessons.all()

    def perform_create(self, serializer):
        course = get_object_or_404(Course, pk=self.kwargs["course_id"])
        teacher = _user_teacher(self.request)

        if (
            teacher is None
            or course.teacher_id != teacher.id
        ) and not self.request.user.is_superuser:
            raise PermissionDenied(
                "Only the course's teacher can add lessons."
            )

        next_order = (
            Lesson.objects.filter(course=course)
            .order_by("-order")
            .values_list("order", flat=True)
            .first()
            or 0
        ) + 1

        serializer.save(course=course, order=next_order)


class MarkLessonCompleteView(APIView):
    """POST toggle: students mark a lesson done / undo."""

    def post(self, request, lesson_id):
        student = _user_student(request)

        if student is None:
            raise PermissionDenied("Only students complete lessons.")

        lesson = get_object_or_404(Lesson, pk=lesson_id)

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

        total = lesson.course.lessons.count()
        done = LessonCompletion.objects.filter(
            student=student,
            lesson__course_id=lesson.course_id,
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
