
from django import forms
from django.contrib import admin

from .models import Enrollment, Guardian, Student


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "relationship",
        "phone",
        "email",
    )

    search_fields = (
        "name",
        "phone",
        "email",
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "admission_number",
        "full_name",
        "gender",
        "guardian",
        "status",
    )

    search_fields = (
        "admission_number",
        "first_name",
        "middle_name",
        "last_name",
        "guardian__name",
    )

    list_filter = (
        "gender",
        "status",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Student Information",
            {
                "fields": (
                    "admission_number",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "date_of_birth",
                    "gender",
                )
            },
        ),
        (
            "Guardian / Parent",
            {
                "fields": (
                    "guardian",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "phone",
                    "address",
                )
            },
        ),
        (
            "Admission",
            {
                "fields": (
                    "admission_date",
                    "status",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


class EnrollmentAdminForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ---------------------------------------------------------
        # Limit Academic Years to the student's school's years
        # when possible.
        # ---------------------------------------------------------
        if self.instance.pk:
            if self.instance.campus_id:
                self.fields["academic_year"].queryset = (
                    self.fields["academic_year"]
                    .queryset
                    .filter(school_id=self.instance.campus.school_id)
                )

        # ---------------------------------------------------------
        # Limit classes according to selected campus.
        # ---------------------------------------------------------
        self.fields["class_obj"].queryset = (
            self.fields["class_obj"]
            .queryset
            .select_related("unit", "unit__campus")
        )

        # ---------------------------------------------------------
        # Limit sections according to selected class.
        # ---------------------------------------------------------
        self.fields["section"].queryset = (
            self.fields["section"]
            .queryset
            .select_related("class_obj")
        )

    def clean(self):
        cleaned_data = super().clean()

        campus = cleaned_data.get("campus")
        class_obj = cleaned_data.get("class_obj")
        section = cleaned_data.get("section")
        academic_year = cleaned_data.get("academic_year")

        errors = {}

        if campus and class_obj:
            if class_obj.unit.campus_id != campus.id:
                errors["class_obj"] = (
                    "This class does not belong to the selected campus."
                )

        if class_obj and section:
            if section.class_obj_id != class_obj.id:
                errors["section"] = (
                    "This section does not belong to the selected class."
                )

        if campus and academic_year:
            if academic_year.school_id != campus.school_id:
                errors["academic_year"] = (
                    "This academic year does not belong to the "
                    "selected campus's school."
                )

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    form = EnrollmentAdminForm

    list_display = (
        "student",
        "academic_year",
        "campus",
        "class_obj",
        "section",
        "status",
        "enrollment_date",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__middle_name",
        "student__last_name",
        "campus__name",
        "class_obj__name",
        "section__name",
    )

    list_filter = (
        "academic_year",
        "campus",
        "status",
    )

    autocomplete_fields = (
        "student",
        "academic_year",
        "campus",
        "class_obj",
        "section",
    )

    readonly_fields = (
        "enrollment_date",
        "created_at",
        "updated_at",
    )

