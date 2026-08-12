from django.contrib import admin

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


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_type", "city", "status")
    search_fields = ("name", "city")
    list_filter = ("institution_type", "status")


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "city", "status")
    search_fields = ("name", "school__name", "city")
    list_filter = ("status",)


@admin.register(AcademicUnit)
class AcademicUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "campus", "unit_type", "status")
    search_fields = ("name", "campus__name")
    list_filter = ("unit_type", "status")


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "level", "status")
    search_fields = ("name", "unit__name")
    list_filter = ("status", "unit")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "class_obj", "capacity", "status")
    search_fields = ("name", "class_obj__name")
    list_filter = ("status",)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "start_date", "end_date", "status")
    search_fields = ("name", "school__name")
    list_filter = ("status",)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("name", "academic_year", "start_date", "end_date")
    search_fields = ("name", "academic_year__name")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "subject_type",
        "practical_required",
        "status",
    )
    search_fields = ("name", "code")
    list_filter = (
        "subject_type",
        "practical_required",
        "status",
    )

@admin.register(SubjectOffering)
class SubjectOfferingAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "class_obj",
        "academic_year",
    )
    search_fields = (
        "subject__name",
        "subject__code",
        "class_obj__name",
        "academic_year__name",
    )
    list_filter = (
        "academic_year",
        "subject",
    )
