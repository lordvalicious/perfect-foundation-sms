from django.db.models import Q
from rest_framework import generics

from apps.accounts.permissions import IsTeacherRole

from .models import Attendance
from .serializers import AttendanceSerializer


class AttendanceListView(generics.ListAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsTeacherRole]

    def get_queryset(self):
        queryset = (
            Attendance.objects
            .select_related(
                "student",
                "campus",
                "class_obj",
                "section",
                "academic_year",
            )
            .order_by("-date", "student__first_name")
        )

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(student__first_name__icontains=search)
                | Q(student__middle_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(student__admission_number__icontains=search)
            )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        date = self.request.query_params.get("date")

        if date:
            queryset = queryset.filter(date=date)

        campus = self.request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus_id=campus)

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        return queryset
