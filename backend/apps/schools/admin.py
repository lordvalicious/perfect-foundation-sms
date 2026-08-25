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
    list_display = ("name", "code", "institution_type", "city", "status")
    search_fields = ("name", "code", "city")
    list_filter = ("institution_type", "status")


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "city", "status")
    search_fields = ("name", "school__name", "city")
    list_filter = ("status",)


@admin.register(AcademicUnit)
class AcademicUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "campus", "status")
    search_fields = ("name", "campus__name")
    list_filter = ("status",)


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


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "institution", "status")
    search_fields = ("name", "code")
    list_filter = ("status",)


@admin.register(SubjectOffering)
class SubjectOfferingAdmin(admin.ModelAdmin):
    list_display = ("class_obj", "subject", "teacher", "status")
    search_fields = ("class_obj__name", "subject__name")
    list_filter = ("status", "academic_year")


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "start_date", "end_date", "status")
    search_fields = ("name", "school__name")
    list_filter = ("status", "school")


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("name", "academic_year", "start_date", "end_date", "status")
    search_fields = ("name", "academic_year__name")
    list_filter = ("status", "academic_year")