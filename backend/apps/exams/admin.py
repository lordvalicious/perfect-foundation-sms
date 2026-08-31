from django.contrib import admin

from .models import (
    Exam,
    ExamSchedule,
    ExamSeating,
    ExamSubject,
    PracticalResult,
    StudentResult,
)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "exam_type",
        "academic_year",
        "term",
        "campus",
        "class_obj",
        "start_date",
        "end_date",
        "status",
    )
    list_filter = ("status", "exam_type", "campus", "class_obj")
    search_fields = ("name", "campus__name", "class_obj__name")
    autocomplete_fields = ("academic_year", "campus", "class_obj", "term")


@admin.register(ExamSubject)
class ExamSubjectAdmin(admin.ModelAdmin):
    list_display = (
        "exam",
        "subject",
        "maximum_marks",
        "passing_marks",
    )
    list_filter = ("exam", "subject")
    search_fields = ("exam__name", "subject__name")


@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "exam",
        "exam_subject",
        "obtained_marks",
        "is_absent",
        "grade",
        "is_pass",
    )
    list_filter = ("is_absent", "is_pass", "grade", "exam")
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__admission_number",
    )


@admin.register(PracticalResult)
class PracticalResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "exam",
        "exam_subject",
        "obtained_marks",
        "is_absent",
    )
    list_filter = ("is_absent", "exam")
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__admission_number",
    )


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "exam",
        "section",
        "exam_subject",
        "date",
        "start_time",
        "end_time",
        "room",
        "invigilator",
    )
    list_filter = ("exam", "section", "date")
    search_fields = ("exam__name", "section__name", "room")


@admin.register(ExamSeating)
class ExamSeatingAdmin(admin.ModelAdmin):
    list_display = (
        "exam",
        "section",
        "student",
        "seat_number",
        "room",
    )
    list_filter = ("exam", "section")
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__admission_number",
    )
    autocomplete_fields = ("student", "section")