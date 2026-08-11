from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import NotFound

from apps.accounts.permissions import IsAdminOrReadOnly
from apps.accounts.scopes import get_teacher_profile, is_manager

from .models import Teacher, TeacherAssignment
from .serializers import (
    TeacherAssignmentSerializer,
    TeacherSerializer,
)


class TeacherListCreateView(generics.ListCreateAPIView):
    serializer_class = TeacherSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Teacher.objects.all().order_by(
            "first_name", "last_name"
        )

        user = self.request.user

        if not is_manager(user):
            profile = get_teacher_profile(user)

            if profile is None:
                return queryset.none()

            queryset = queryset.filter(pk=profile.pk)

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(employee_number__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
            )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        gender = self.request.query_params.get("gender")

        if gender:
            queryset = queryset.filter(gender=gender)

        campus = self.request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus__iexact=campus)

        return queryset


class TeacherDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = TeacherSerializer

    def get_queryset(self):
        queryset = Teacher.objects.all()

        user = self.request.user

        if not is_manager(user):
            profile = get_teacher_profile(user)

            if profile is None:
                return queryset.none()

            queryset = queryset.filter(pk=profile.pk)

        return queryset


class TeacherMyView(generics.RetrieveAPIView):
    """The logged-in teacher's own profile and assigned classes."""

    permission_classes = [IsAdminOrReadOnly]
    serializer_class = TeacherSerializer

    def get_object(self):
        profile = get_teacher_profile(self.request.user)

        if profile is None:
            raise NotFound(
                "No teacher profile is linked to this account."
            )

        return profile


class TeacherAssignmentListCreateView(generics.ListCreateAPIView):
    """Assign a teacher to a grade (class/section/subject)."""

    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = (
            TeacherAssignment.objects
            .select_related(
                "teacher",
                "campus",
                "class_obj",
                "section",
                "subject",
                "academic_year",
            )
            .order_by("class_obj__name", "section__name", "teacher__first_name")
        )

        teacher = self.request.query_params.get("teacher")

        if teacher:
            queryset = queryset.filter(teacher_id=teacher)

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        role = self.request.query_params.get("role")

        if role:
            queryset = queryset.filter(role=role)

        academic_year = self.request.query_params.get("year")

        if academic_year:
            queryset = queryset.filter(
                academic_year_id=academic_year
            )

        return queryset


class TeacherAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = TeacherAssignmentSerializer

    def get_queryset(self):
        return (
            TeacherAssignment.objects
            .select_related(
                "teacher",
                "campus",
                "class_obj",
                "section",
                "subject",
                "academic_year",
            )
        )
