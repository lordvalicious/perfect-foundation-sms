from django.db.models import Q
from rest_framework import generics

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
