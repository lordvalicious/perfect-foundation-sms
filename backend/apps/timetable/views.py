from django.db.models import Q
from rest_framework import generics

from apps.accounts.permissions import IsStaffRole

from .models import Period, TimetableEntry
from .serializers import (
    PeriodSerializer,
    TimetableEntrySerializer,
)


class PeriodListView(generics.ListAPIView):
    serializer_class = PeriodSerializer
    permission_classes = [IsStaffRole]
    pagination_class = None

    def get_queryset(self):
        queryset = Period.objects.all().order_by("number")

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset


class TimetableEntryListView(generics.ListAPIView):
    serializer_class = TimetableEntrySerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = (
            TimetableEntry.objects
            .select_related(
                "academic_year",
                "campus",
                "class_obj",
                "section",
                "subject",
                "teacher",
                "period",
            )
            .order_by("day", "period__number", "class_obj__name")
        )

        day = self.request.query_params.get("day")

        if day:
            queryset = queryset.filter(day=day)

        campus = self.request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus_id=campus)

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        section = self.request.query_params.get("section")

        if section:
            queryset = queryset.filter(section_id=section)

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(subject__name__icontains=search)
                | Q(subject__code__icontains=search)
                | Q(teacher__first_name__icontains=search)
                | Q(teacher__last_name__icontains=search)
            )

        return queryset
