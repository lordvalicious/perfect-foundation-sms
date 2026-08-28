
from django import forms
from django.contrib import admin

from .models import (
    AdmissionApplication,
    AcademicHistory,
    Enrollment,
    Guardian,
    Inquiry,
    Student,
    StudentGuardian,
    StudentLifecycleEvent,
    TransferCertificate,
)


@admin.register(AdmissionApplication)
class AdmissionApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "application_number",
        "applicant_name",
        "campus",
        "academic_year",
        "status",
        "created_at",
    )
    list_filter = ("status", "campus", "academic_year")
    search_fields = ("application_number", "first_name", "last_name", "phone")


@admin.register(StudentGuardian)
class StudentGuardianAdmin(admin.ModelAdmin):
    list_display = ("student", "guardian", "relationship", "is_primary", "can_pick_up")
    list_filter = ("is_primary", "can_pick_up", "is_emergency_contact")
    search_fields = ("student__admission_number", "student__first_name", "guardian__name")


@admin.register(StudentLifecycleEvent)
class StudentLifecycleEventAdmin(admin.ModelAdmin):
    list_display = ("student", "event_type", "effective_date", "recorded_by")
    list_filter = ("event_type", "effective_date")
    search_fields = ("student__admission_number", "student__first_name", "reason")
    readonly_fields = ("created_at",)


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


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = (
        "inquiry_number",
        "applicant_name",
        "campus",
        "academic_year",
        "class_obj",
        "status",
        "source",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "source", "campus", "academic_year")
    search_fields = ("inquiry_number", "first_name", "last_name", "phone", "email")
    readonly_fields = ("inquiry_number", "created_at", "updated_at", "converted_at", "converted_by")


@admin.register(AcademicHistory)
class AcademicHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "academic_year",
        "campus",
        "class_obj",
        "section",
        "final_status",
        "promotion_status",
        "final_grade",
        "final_percentage",
    )
    list_filter = ("final_status", "promotion_status", "campus", "academic_year")
    search_fields = ("student__admission_number", "student__first_name", "student__last_name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TransferCertificate)
class TransferCertificateAdmin(admin.ModelAdmin):
    list_display = (
        "certificate_number",
        "student",
        "full_name",
        "campus",
        "academic_year",
        "class_obj",
        "status",
        "reason",
        "issued_at",
    )
    list_filter = ("status", "reason", "campus", "academic_year")
    search_fields = ("certificate_number", "student__admission_number", "full_name")
    readonly_fields = (
        "certificate_number",
        "verification_code",
        "issued_by",
        "issued_at",
        "created_at",
        "updated_at",
    )
    actions = ["issue_certificates", "cancel_certificates"]

    def issue_certificates(self, request, queryset):
        for cert in queryset.filter(status="draft"):
            cert.issue(request.user)
        self.message_user(request, f"Issued {queryset.filter(status='issued').count()} certificates.")

    def cancel_certificates(self, request, queryset):
        for cert in queryset.filter(status="issued"):
            cert.cancel(request.user)
        self.message_user(request, f"Cancelled {queryset.filter(status='cancelled').count()} certificates.")

    issue_certificates.short_description = "Issue selected certificates"
    cancel_certificates.short_description = "Cancel selected certificates"

