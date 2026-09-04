from django.db.models import Count, Q
from rest_framework import generics, status, viewsets
from rest_framework.mixins import (
    DestroyModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers
from django.db import transaction
from django.shortcuts import get_object_or_404
from datetime import date

from apps.accounts.access import apply_campus_scope, assert_campus_allowed, institution_scope
from apps.accounts.permissions import HasActiveInstitution, IsAdminOrReadOnly, IsSuperAdmin
from apps.students.models import Student, Enrollment
from .models import (
    AcademicUnit,
    AcademicYear,
    AcademicCalendar,
    Campus,
    Class,
    School,
    Section,
    Subject,
    SubjectOffering,
    Term,
)
from .serializers import (
    AcademicCalendarSerializer,
    AcademicUnitSerializer,
    AcademicYearSerializer,
    CampusSerializer,
    ClassSerializer,
    SchoolSerializer,
    SectionSerializer,
    SubjectOfferingSerializer,
    SubjectSerializer,
    TermSerializer,
)


class NoPaginationMixin:
    pagination_class = None


def populate_campus_counts(queryset):
    class_counts = (
        Class.objects.filter(status="active")
        .values("unit__campus_id")
        .annotate(total=Count("id"))
    )
    class_map = {
        item["unit__campus_id"]: item["total"]
        for item in class_counts
    }

    section_counts = (
        Section.objects.filter(status="active")
        .values("class_obj__unit__campus_id")
        .annotate(total=Count("id"))
    )
    section_map = {
        item["class_obj__unit__campus_id"]: item["total"]
        for item in section_counts
    }

    student_counts = (
        Enrollment.objects.filter(status="active")
        .values("campus_id")
        .annotate(total=Count("student", distinct=True))
    )
    student_map = {
        item["campus_id"]: item["total"]
        for item in student_counts
    }

    for campus in queryset:
        campus.class_count = class_map.get(campus.id, 0)
        campus.section_count = section_map.get(campus.id, 0)
        campus.student_count = student_map.get(campus.id, 0)

    return queryset


class SchoolViewSet(NoPaginationMixin, viewsets.GenericViewSet, generics.ListAPIView):
    serializer_class = SchoolSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        return School.objects.filter(
            pk=self.request.institution.pk
        ).order_by("name")

    @action(detail=True, methods=["post"], permission_classes=[HasActiveInstitution, IsSuperAdmin])
    def pause(self, request, pk=None):
        """Pause the school - prevents login, attendance, fees, etc."""
        school = self.get_object()
        school.pause(request.user)
        return Response({"detail": "School paused successfully."})

    @action(detail=True, methods=["post"], permission_classes=[HasActiveInstitution, IsSuperAdmin])
    def activate(self, request, pk=None):
        """Activate the school - resume all operations."""
        school = self.get_object()
        school.activate()
        return Response({"detail": "School activated successfully."})

    @action(detail=True, methods=["post"], permission_classes=[HasActiveInstitution, IsSuperAdmin])
    def archive(self, request, pk=None):
        """Archive the school."""
        school = self.get_object()
        school.archive(request.user)
        return Response({"detail": "School archived successfully."})

    @action(detail=True, methods=["post"], permission_classes=[HasActiveInstitution, IsSuperAdmin])
    def unarchive(self, request, pk=None):
        """Unarchive the school."""
        school = self.get_object()
        school.unarchive()
        return Response({"detail": "School unarchived successfully."})


class CampusViewSet(
    NoPaginationMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    viewsets.GenericViewSet,
    generics.ListCreateAPIView,
):
    serializer_class = CampusSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def _is_platform_admin(self):
        user = self.request.user
        return bool(user.is_superuser or user.has_any_role(["super_admin"]))

    def get_queryset(self):
        if self._is_platform_admin():
            queryset = Campus.objects.all()
            school_param = self.request.query_params.get("school")

            if school_param:
                queryset = queryset.filter(school_id=school_param)
            else:
                # Platform admin without a school filter keeps the current
                # institution scope so other pages behave unchanged.
                queryset = queryset.filter(school=self.request.institution)
        else:
            queryset = Campus.objects.filter(
                school=self.request.institution
            )

        queryset = queryset.select_related("school").order_by("name")

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(city__icontains=search)
            )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return populate_campus_counts(queryset)

    def _resolve_school(self):
        """Pick the owning school: platform admins may choose any school,
        everyone else is locked to their active institution."""
        requested = self.request.data.get("school")

        if self._is_platform_admin() and requested:
            school = School.objects.filter(pk=requested).first()

            if school is None:
                raise serializers.ValidationError(
                    {"school": "School not found."}
                )

            return school

        return self.request.institution

    def perform_create(self, serializer):
        serializer.save(school=self._resolve_school())

    def update(self, request, *args, **kwargs):
        # Non-platform users must never move a campus across schools.
        if not self._is_platform_admin():
            data = request.data

            if isinstance(data, dict):
                data.pop("school", None)

        return super().update(request, *args, **kwargs)

    def retrieve(self, request, pk=None):
        campus = self.get_object()
        row = populate_campus_counts(
            Campus.objects.filter(pk=campus.pk)
        )[0]
        return Response(self.get_serializer(row).data)

    def destroy(self, request, pk=None):
        """Delete campus - Super Admin only."""
        if not self._is_platform_admin():
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        campus = self.get_object()
        campus.delete()
        return Response(
            {"detail": "Campus deleted successfully."},
            status=status.HTTP_200_OK,
        )


def _raise_parent_not_in_school(label):
    raise serializers.ValidationError(
        {label: f"Selected {label} does not belong to your school."}
    )


class AcademicUnitListView(NoPaginationMixin, generics.ListCreateAPIView):
    serializer_class = AcademicUnitSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = (
            AcademicUnit.objects.filter(campus__school=self.request.institution)
            .select_related("campus")
            .order_by("campus__name", "name")
        )

        queryset = apply_campus_scope(
            queryset,
            self.request,
            "campus_id",
        )

        return queryset

    def perform_create(self, serializer):
        campus_id = serializer.validated_data.get("campus")
        ok = campus_id and Campus.objects.filter(
            pk=campus_id.pk,
            school=self.request.institution,
        ).exists()

        if not ok:
            _raise_parent_not_in_school("campus")

        serializer.save()


class ClassListView(NoPaginationMixin, generics.ListCreateAPIView):
    serializer_class = ClassSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = (
            Class.objects.filter(unit__campus__school=self.request.institution)
            .select_related("unit", "unit__campus")
            .order_by("level", "name")
        )

        queryset = apply_campus_scope(
            queryset,
            self.request,
            "unit__campus_id",
        )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def perform_create(self, serializer):
        unit = serializer.validated_data.get("unit")
        ok = unit and AcademicUnit.objects.filter(
            pk=unit.pk,
            campus__school=self.request.institution,
        ).exists()

        if not ok:
            _raise_parent_not_in_school("unit")

        serializer.save()


class SectionListView(NoPaginationMixin, generics.ListCreateAPIView):
    serializer_class = SectionSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = section_queryset(self.request)

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        return queryset

    def perform_create(self, serializer):
        class_obj = serializer.validated_data.get("class_obj")
        ok = class_obj and Class.objects.filter(
            pk=class_obj.pk,
            unit__campus__school=self.request.institution,
        ).exists()

        if not ok:
            _raise_parent_not_in_school("class_obj")

        serializer.save()


class SectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SectionSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]
    queryset = Section.objects.all()

    def get_queryset(self):
        return section_queryset(self.request)

    def perform_destroy(self, instance):
        assert_campus_allowed(self.request.user, instance.class_obj.unit.campus_id)
        instance.delete()

    def perform_update(self, serializer):
        instance = self.get_object()
        assert_campus_allowed(self.request.user, instance.class_obj.unit.campus_id)
        serializer.save()


def section_queryset(request):
    """Base queryset for Section views, scoped to the current institution
    and campus, with the class parent validated against the institution."""
    queryset = (
        Section.objects.filter(
            class_obj__unit__campus__school=request.institution
        )
        .select_related("class_obj", "class_obj__unit__campus")
        .order_by("class_obj__name", "name")
    )

    return apply_campus_scope(
        queryset,
        request,
        "class_obj__unit__campus_id",
    )


class AcademicYearListView(NoPaginationMixin, generics.ListCreateAPIView):
    serializer_class = AcademicYearSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        return AcademicYear.objects.filter(
            school=self.request.institution
        ).select_related("school").order_by("-start_date")

    def perform_create(self, serializer):
        serializer.save(school=self.request.institution)


class TermListView(NoPaginationMixin, generics.ListCreateAPIView):
    serializer_class = TermSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        return Term.objects.filter(
            academic_year__school=self.request.institution
        ).select_related("academic_year").order_by(
            "academic_year", "start_date"
        )

    def perform_create(self, serializer):
        academic_year = serializer.validated_data.get("academic_year")
        ok = academic_year and AcademicYear.objects.filter(
            pk=academic_year.pk,
            school=self.request.institution,
        ).exists()

        if not ok:
            _raise_parent_not_in_school("academic_year")

        serializer.save()


class SubjectListView(NoPaginationMixin, generics.ListAPIView):
    serializer_class = SubjectSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        return institution_scope(Subject.objects.all(), self.request).order_by("name")


class SubjectOfferingListView(NoPaginationMixin, generics.ListAPIView):
    serializer_class = SubjectOfferingSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = (
            SubjectOffering.objects.filter(
                class_obj__unit__campus__school=self.request.institution
            )
            .select_related(
                "subject",
                "class_obj",
                "class_obj__unit__campus",
                "academic_year",
            )
            .order_by("class_obj__name", "subject__name")
        )

        queryset = apply_campus_scope(
            queryset,
            self.request,
            "class_obj__unit__campus_id",
        )

        class_obj = self.request.query_params.get("class")

        if class_obj:
            queryset = queryset.filter(class_obj_id=class_obj)

        return queryset
