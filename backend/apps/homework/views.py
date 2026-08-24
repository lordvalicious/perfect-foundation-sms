from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope
from rest_framework.permissions import IsAuthenticated

from .models import Homework, Submission
from .serializers import HomeworkSerializer, SubmissionSerializer


def _user_teacher(request):
    return getattr(request.user, "teacher_profile", None)


def _user_student(request):
    return getattr(request.user, "student_profile", None)


class HomeworkListCreateView(generics.ListCreateAPIView):
    serializer_class = HomeworkSerializer

    def get_permissions(self):
        # Students may read; creating requires a teacher profile.
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Homework.objects.select_related(
            "teacher",
            "campus",
            "class_obj",
            "section",
            "subject",
        )

        queryset = apply_campus_scope(queryset, self.request)

        student = _user_student(self.request)

        if student is not None and not self.request.user.is_superuser:
            enrollments = student.enrollments.filter(status="active")

            from django.db.models import Q

            condition = Q()

            for enrollment in enrollments:
                condition |= Q(
                    campus=enrollment.campus,
                    class_obj=enrollment.class_obj,
                ) & (
                    Q(section__isnull=True)
                    | Q(section=enrollment.section)
                )

            if condition:
                queryset = queryset.filter(condition).distinct()
            else:
                queryset = queryset.none()

            return queryset

        class_obj = self.request.query_params.get("class_obj")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        teacher = self.request.query_params.get("teacher")

        if teacher:
            queryset = queryset.filter(teacher_id=teacher)

        return queryset

    def perform_create(self, serializer):
        teacher = _user_teacher(self.request)

        if teacher is None:
            raise PermissionDenied(
                "Only teachers can create homework."
            )

        serializer.save(teacher=teacher, created_by=self.request.user)


class HomeworkDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HomeworkSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Homework.objects.select_related(
            "teacher",
            "campus",
            "class_obj",
            "section",
            "subject",
        )

        return apply_campus_scope(queryset, self.request)

    def perform_update(self, serializer):
        teacher = _user_teacher(self.request)

        if (
            teacher is None
            or serializer.instance.teacher_id != teacher.id
        ) and not self.request.user.is_superuser:
            raise PermissionDenied(
                "Only the homework's teacher can edit it."
            )

        serializer.save()

    def perform_destroy(self, instance):
        teacher = _user_teacher(self.request)

        if (
            teacher is None
            or instance.teacher_id != teacher.id
        ) and not self.request.user.is_superuser:
            raise PermissionDenied(
                "Only the homework's teacher can delete it."
            )

        instance.delete()


class SubmissionListCreateView(generics.ListCreateAPIView):
    serializer_class = SubmissionSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_homework(self):
        return get_object_or_404(Homework, pk=self.kwargs["homework_id"])

    def get_queryset(self):
        homework = self.get_homework()
        queryset = Submission.objects.filter(homework=homework).select_related(
            "student",
            "graded_by",
        )

        student = _user_student(self.request)

        if student is not None and not self.request.user.is_superuser:
            return queryset.filter(student=student)

        return queryset

    def perform_create(self, serializer):
        homework = self.get_homework()
        student = _user_student(self.request)

        if student is None:
            raise PermissionDenied("Only students can submit homework.")

        active = student.enrollments.filter(
            campus=homework.campus,
            class_obj=homework.class_obj,
            status="active",
        ).exists()

        if not active:
            raise PermissionDenied(
                "You are not enrolled in this class."
            )

        serializer.save(student=student, homework=homework)


class GradeSubmissionView(APIView):
    """Teacher grades one submission: {marks_obtained, feedback}."""

    def post(self, request, pk):
        teacher = _user_teacher(request)

        if teacher is None and not request.user.is_superuser:
            raise PermissionDenied("Only teachers can grade submissions.")

        submission = get_object_or_404(
            Submission.objects.select_related("homework", "homework__teacher"),
            pk=pk,
        )

        if (
            teacher is not None
            and submission.homework.teacher_id != teacher.id
            and not request.user.is_superuser
        ):
            raise PermissionDenied(
                "Only the homework's teacher can grade it."
            )

        marks = request.data.get("marks_obtained")
        feedback = request.data.get("feedback", "")

        try:
            marks = int(marks) if marks is not None else None
        except (TypeError, ValueError):
            return Response(
                {"detail": "marks_obtained must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if marks is not None and marks > submission.homework.max_marks:
            return Response(
                {
                    "detail": (
                        f"Marks cannot exceed "
                        f"{submission.homework.max_marks}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission.marks_obtained = marks
        submission.feedback = feedback
        submission.status = "graded"
        submission.graded_by = request.user
        submission.save()

        return Response(SubmissionSerializer(submission).data)
