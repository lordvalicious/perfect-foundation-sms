from django.db.models import Q
from rest_framework import generics

from apps.accounts.permissions import IsAcademicMemberRole
from apps.accounts.scopes import (
    get_student_profile,
    is_manager,
    is_parent,
    is_student,
    is_teacher,
    parent_student_class_ids,
    parent_student_ids,
    student_class_ids,
    teacher_class_ids,
    teacher_student_ids,
)

from .models import Exam, ExamSubject, StudentResult
from .serializers import (
    ExamSerializer,
    ExamSubjectSerializer,
    StudentResultSerializer,
)


class ExamListView(generics.ListAPIView):
    serializer_class = ExamSerializer
    permission_classes = [IsAcademicMemberRole]

    def get_queryset(self):
        queryset = (
            Exam.objects
            .select_related("academic_year", "campus", "class_obj")
            .prefetch_related("exam_subjects", "results")
            .order_by("-start_date")
        )

        user = self.request.user

        if not is_manager(user):
            if is_student(user):
                class_ids = student_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(class_obj_id__in=class_ids)
            elif is_parent(user):
                class_ids = parent_student_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(class_obj_id__in=class_ids)
            elif is_teacher(user):
                class_ids = teacher_class_ids(user)

                if not class_ids:
                    return queryset.none()

                queryset = queryset.filter(class_obj_id__in=class_ids)

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
            )

        campus = self.request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus_id=campus)

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset


class ExamSubjectListView(generics.ListAPIView):
    serializer_class = ExamSubjectSerializer
    permission_classes = [IsAcademicMemberRole]
    pagination_class = None

    def get_queryset(self):
        queryset = (
            ExamSubject.objects
            .select_related("exam", "subject")
            .order_by("exam", "subject__name")
        )

        exam = self.request.query_params.get("exam")

        if exam:
            queryset = queryset.filter(exam_id=exam)

        return queryset


class StudentResultListView(generics.ListAPIView):
    serializer_class = StudentResultSerializer
    permission_classes = [IsAcademicMemberRole]

    def get_queryset(self):
        queryset = (
            StudentResult.objects
            .select_related(
                "exam",
                "student",
                "exam_subject__subject",
            )
            .order_by("exam", "student__first_name", "exam_subject__subject__name")
        )

        user = self.request.user

        if not is_manager(user):
            if is_student(user):
                profile = get_student_profile(user)

                if profile is None:
                    return queryset.none()

                queryset = queryset.filter(student=profile)
            elif is_parent(user):
                student_ids = parent_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)
            elif is_teacher(user):
                student_ids = teacher_student_ids(user)

                if not student_ids:
                    return queryset.none()

                queryset = queryset.filter(student_id__in=student_ids)

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(student__first_name__icontains=search)
                | Q(student__middle_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(student__admission_number__icontains=search)
            )

        exam = self.request.query_params.get("exam")

        if exam:
            queryset = queryset.filter(exam_id=exam)

        grade = self.request.query_params.get("grade")

        if grade:
            queryset = queryset.filter(grade=grade)

        return queryset
