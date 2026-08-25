"""Auto-graded MCQ quizzes: teacher authoring, student attempts."""

from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope

from .models import Course, Question, Quiz, QuizAttempt
from .serializers import (
    QuestionPublicSerializer,
    QuestionSerializer,
    QuizAttemptSerializer,
    QuizListSerializer,
)
from .views import _user_student, _user_teacher


def _course_teacher_or_503(request, course):
    teacher = _user_teacher(request)

    if (
        teacher is None or course.teacher_id != teacher.id
    ) and not request.user.is_superuser:
        raise PermissionDenied(
            "Only the course's teacher can manage its quizzes."
        )

    return teacher


class QuizListCreateView(generics.ListCreateAPIView):
    serializer_class = QuizListSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Quiz.objects.select_related("course")

        student = _user_student(self.request)

        if student is not None and not self.request.user.is_superuser:
            return queryset.filter(
                is_published=True,
                course__is_published=True,
                course__class_obj__in=student.enrollments.filter(
                    status="active"
                ).values("class_obj"),
            ).distinct()

        course_id = self.request.query_params.get("course")

        if course_id:
            queryset = queryset.filter(course_id=course_id)

        return queryset

    def perform_create(self, serializer):
        teacher = _user_teacher(self.request)

        if teacher is None:
            raise PermissionDenied("Only teachers can create quizzes.")

        course = serializer.validated_data["course"]
        _course_teacher_or_503(self.request, course)

        serializer.save()


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    def get_permissions(self):
        return [IsAuthenticated()]

    def get_serializer_class(self):
        request = self.request

        if _user_student(request) is not None and not request.user.is_superuser:
            from .serializers import QuizListSerializer

            return QuizListSerializer

        return QuizListSerializer

    def get_queryset(self):
        queryset = Quiz.objects.select_related("course")

        student = _user_student(self.request)

        if student is not None and not self.request.user.is_superuser:
            return queryset.filter(is_published=True)

        return queryset

    def perform_update(self, serializer):
        _course_teacher_or_503(self.request, serializer.instance.course)
        serializer.save()

    def perform_destroy(self, instance):
        _course_teacher_or_503(self.request, instance.course)
        instance.delete()


class QuizQuestionListView(APIView):
    """GET questions for a quiz.

    Teachers (of the course) see correct_option; students get the
    sanitized version.
    """

    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        student = _user_student(request)

        if (
            student is not None and not request.user.is_superuser
        ) and not quiz.is_published:
            return Response({"detail": "Quiz not available."}, status=404)

        questions = quiz.questions.all()

        if student is not None and not request.user.is_superuser:
            serializer = QuestionPublicSerializer(questions, many=True)
        else:
            teacher = _user_teacher(request)

            if (
                teacher is None or quiz.course.teacher_id != teacher.id
            ) and not request.user.is_superuser:
                # other staff preview: sanitized as well
                serializer = QuestionPublicSerializer(questions, many=True)
            else:
                serializer = QuestionSerializer(questions, many=True)

        return Response(serializer.data)


class QuizQuestionCreateView(APIView):
    """POST one question (teacher of the course only)."""

    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        _course_teacher_or_503(request, quiz.course)

        data = dict(request.data)
        data["quiz"] = quiz.pk

        serializer = QuestionSerializer(data=data)

        serializer.is_valid(raise_exception=True)
        question = serializer.save(quiz=quiz)

        return Response(
            QuestionSerializer(question).data, status=201
        )


class QuizQuestionDeleteView(APIView):
    def delete(self, request, pk):
        question = get_object_or_404(
            Question.objects.select_related("quiz__course"), pk=pk
        )
        _course_teacher_or_503(request, question.quiz.course)
        question.delete()

        return Response({"detail": "Question deleted."})


class SubmitQuizAttemptView(APIView):
    """POST {answers: {"<question_id>": "a", ...}} -> auto-scored attempt."""

    def post(self, request, quiz_id):
        quiz = get_object_or_404(
            Quiz.objects.select_related("course"), pk=quiz_id
        )
        student = _user_student(request)

        if student is None:
            raise PermissionDenied("Only students can submit attempts.")

        if not quiz.is_published:
            raise PermissionDenied("This quiz is not open.")

        enrolled = student.enrollments.filter(
            status="active",
            class_obj=quiz.course.class_obj,
            campus=quiz.course.campus,
        ).exists()

        if not enrolled:
            raise PermissionDenied(
                "You are not enrolled in this course's class."
            )

        if QuizAttempt.objects.filter(quiz=quiz, student=student).exists():
            return Response(
                {"detail": "You have already submitted this quiz."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answers = request.data.get("answers") or {}

        score = Decimal("0")
        total = Decimal("0")
        breakdown = {}

        for question in quiz.questions.all():
            total += question.marks
            given = str(answers.get(str(question.pk), "")).strip().lower()
            correct = given == question.correct_option
            breakdown[str(question.pk)] = {
                "given": given,
                "correct": question.correct_option,
                "ok": correct,
            }

            if correct:
                score += question.marks

        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=student,
            answers={"raw": answers, "breakdown": breakdown},
            score=score,
            total_marks=int(total),
        )

        return Response(
            QuizAttemptSerializer(attempt).data, status=201
        )


class QuizAttemptListView(generics.ListAPIView):
    """Teacher: every attempt for a quiz."""

    serializer_class = QuizAttemptSerializer

    def get_queryset(self):
        quiz = get_object_or_404(
            Quiz.objects.select_related("course"), pk=self.kwargs["quiz_id"]
        )
        _course_teacher_or_503(self.request, quiz.course)

        return (
            QuizAttempt.objects
            .filter(quiz=quiz)
            .select_related("student")
            .order_by("-submitted_at")
        )


class MyQuizAttemptView(APIView):
    """GET the signed-in student's own attempt for a quiz."""

    def get(self, request, quiz_id):
        student = _user_student(request)

        if student is None:
            return Response(None, status=204)

        attempt = QuizAttempt.objects.filter(
            quiz_id=quiz_id, student=student
        ).first()

        if attempt is None:
            return Response(None, status=204)

        return Response(QuizAttemptSerializer(attempt).data)
