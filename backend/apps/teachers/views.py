from django.db.models import Q
from rest_framework import generics

from apps.accounts.permissions import IsAdminOrReadOnly

from .models import Teacher
from .serializers import TeacherSerializer


class TeacherListCreateView(generics.ListCreateAPIView):
    serializer_class = TeacherSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Teacher.objects.all().order_by(
            "first_name", "last_name"
        )

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
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
