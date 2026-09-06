from rest_framework import generics

from apps.accounts.access import (
    apply_campus_scope,
    assert_campus_allowed,
)
from apps.accounts.permissions import IsStaffRole

from .models import HealthRecord
from .serializers import HealthRecordSerializer


class HealthRecordListCreateView(generics.ListCreateAPIView):
    serializer_class = HealthRecordSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = HealthRecord.objects.select_related(
            "student",
            "campus",
        )

        queryset = apply_campus_scope(queryset, self.request)

        student = self.request.query_params.get("student")

        if student:
            queryset = queryset.filter(student_id=student)

        record_type = self.request.query_params.get("type")

        if record_type:
            queryset = queryset.filter(record_type=record_type)

        return queryset

    def perform_create(self, serializer):
        campus = serializer.validated_data.get("campus")

        if campus is not None:
            assert_campus_allowed(self.request.user, campus.id)

        serializer.save(recorded_by=self.request.user)


class HealthRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HealthRecordSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = HealthRecord.objects.select_related(
            "student",
            "campus",
        )

        return apply_campus_scope(queryset, self.request)

    def perform_update(self, serializer):
        campus = serializer.validated_data.get("campus")

        if campus is not None:
            assert_campus_allowed(self.request.user, campus.id)

        serializer.save()
