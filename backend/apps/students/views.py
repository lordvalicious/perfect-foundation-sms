from django.db.models import Q
from rest_framework import generics

from apps.accounts.permissions import IsAdminOrReadOnly

from .models import Student
from .serializers import StudentSerializer


class StudentListCreateView(generics.ListCreateAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = (
            Student.objects
            .select_related("guardian")
            .prefetch_related(
                "enrollments__academic_year",
                "enrollments__campus",
                "enrollments__class_obj",
                "enrollments__section",
            )
            .order_by("first_name", "last_name")
        )

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(admission_number__icontains=search)
                | Q(first_name__icontains=search)
                | Q(middle_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
            )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        gender = self.request.query_params.get("gender")

        if gender:
            queryset = queryset.filter(gender=gender)

        return queryset


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    queryset = (
        Student.objects
        .select_related("guardian")
        .prefetch_related(
            "enrollments__academic_year",
            "enrollments__campus",
            "enrollments__class_obj",
            "enrollments__section",
        )
    )
    serializer_class = StudentSerializer