from django.db.models import Count, Q
from rest_framework import generics

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import HasActiveInstitution, IsAdminOrReadOnly
from apps.students.models import Enrollment
from .models import (
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    School,
    Section,
    Subject,
    SubjectOffering,
    Term,
)
from .serializers import (
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


class SchoolListView(NoPaginationMixin, generics.ListAPIView):
    serializer_class = SchoolSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        return School.objects.filter(
            pk=self.request.institution.pk
        ).order_by("name")


class CampusListView(NoPaginationMixin, generics.ListCreateAPIView):
    serializer_class = CampusSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Campus.objects.filter(
            school=self.request.institution
        ).select_related("school").order_by("name")

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

    def perform_create(self, serializer):
        serializer.save(school=self.request.institution)


class AcademicUnitListView(NoPaginationMixin, generics.ListAPIView):
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


class ClassListView(NoPaginationMixin, generics.ListAPIView):
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


class SectionListView(NoPaginationMixin, generics.ListAPIView):
    serializer_class = SectionSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = (
            Section.objects.filter(
                class_obj__unit__campus__school=self.request.institution
            )
            .select_related("class_obj", "class_obj__unit__campus")
            .order_by("class_obj__name", "name")
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


class AcademicYearListView(NoPaginationMixin, generics.ListAPIView):
    serializer_class = AcademicYearSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        return AcademicYear.objects.filter(
            school=self.request.institution
        ).select_related("school").order_by("-start_date")


class TermListView(NoPaginationMixin, generics.ListAPIView):
    serializer_class = TermSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]

    def get_queryset(self):
        return Term.objects.filter(
            academic_year__school=self.request.institution
        ).select_related("academic_year").order_by(
            "academic_year", "start_date"
        )


class SubjectListView(NoPaginationMixin, generics.ListAPIView):
    queryset = Subject.objects.all().order_by("name")
    serializer_class = SubjectSerializer
    permission_classes = [HasActiveInstitution, IsAdminOrReadOnly]


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
