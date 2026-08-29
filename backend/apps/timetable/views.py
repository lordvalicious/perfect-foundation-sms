from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAcademicMemberRole
from apps.accounts.scopes import (
    get_teacher_profile,
    is_manager,
    is_parent,
    is_student,
    is_teacher,
    parent_student_class_ids,
    student_class_ids,
)

from .models import Period, TimetableEntry
from .serializers import (
    PeriodSerializer,
    TimetableEntrySerializer,
)


class PeriodListView(generics.ListAPIView):
    serializer_class = PeriodSerializer
    permission_classes = [IsAcademicMemberRole]
    pagination_class = None

    def get_queryset(self):
        queryset = Period.objects.all().order_by("number")

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset


class TimetableEntryListView(generics.ListAPIView):
    serializer_class = TimetableEntrySerializer
    permission_classes = [IsAcademicMemberRole]

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
                teacher_profile = get_teacher_profile(user)

                if teacher_profile is None:
                    return queryset.none()

                queryset = queryset.filter(
                    teacher=teacher_profile
                )

        day = self.request.query_params.get("day")

        if day:
            queryset = queryset.filter(day=day)

        queryset = apply_campus_scope(queryset, self.request, "campus_id")

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        section = self.request.query_params.get("section")

        if section:
            queryset = queryset.filter(section_id=section)

        teacher = self.request.query_params.get("teacher")

        if teacher:
            queryset = queryset.filter(teacher_id=teacher)

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(subject__name__icontains=search)
                | Q(subject__code__icontains=search)
                | Q(teacher__first_name__icontains=search)
                | Q(teacher__last_name__icontains=search)
            )

        return queryset


class TimetableConflictsView(APIView):
    """GET /api/timetable/conflicts/[?year=&campus=]

    Audits the timetable for double-bookings that the database unique
    constraints cannot see: overlapping-period teacher/section clashes
    and room double-bookings. Returns the matching conflict records.
    """

    permission_classes = [IsAcademicMemberRole]

    def get(self, request):
        from django.shortcuts import get_object_or_404

        from apps.accounts.access import (
            apply_campus_scope,
            assert_campus_allowed,
        )
        from apps.schools.models import AcademicYear, Campus
        from .conflicts import find_conflicts

        filters = {}

        year_id = request.query_params.get("year")

        if year_id:
            if not str(year_id).isdigit():
                return Response(
                    {"detail": "Invalid academic year id."}, status=400
                )
            year = get_object_or_404(AcademicYear, pk=year_id)
            filters["academic_year"] = year

        campus_id = request.query_params.get("campus")

        if campus_id:
            if not str(campus_id).isdigit():
                return Response(
                    {"detail": "Invalid campus id."}, status=400
                )
            campus = get_object_or_404(Campus, pk=campus_id)
            assert_campus_allowed(request.user, campus.pk)
            filters["campus"] = campus

        conflicts = find_conflicts(**filters)

        return Response(
            {
                "count": len(conflicts),
                "conflicts": conflicts,
            }
        )
