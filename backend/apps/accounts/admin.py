from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    InstitutionMembership,
    RoleAssignment,
    StaffProfile,
    User,
)


class RoleAssignmentInline(admin.TabularInline):
    model = RoleAssignment
    extra = 1


@admin.register(InstitutionMembership)
class InstitutionMembershipAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "institution",
        "status",
        "joined_at",
    ]

    list_filter = ["status", "institution"]
    search_fields = [
        "user__username",
        "user__email",
        "institution__name",
    ]

    inlines = [RoleAssignmentInline]


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = [
        "employee_number",
        "user",
        "designation",
        "department",
        "status",
    ]

    list_filter = ["status", "department"]
    search_fields = [
        "employee_number",
        "user__username",
        "user__email",
    ]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    search_fields = ["username", "email"]

    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
    ]
