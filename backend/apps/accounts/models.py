from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.schools.models import School


class Role(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Platform Super Admin"
    ADMIN = "admin", "Institution Admin"
    PRINCIPAL = "principal", "Principal"
    ACADEMIC = "academic", "Academic Administrator"
    ACCOUNTANT = "accountant", "Accountant"
    TEACHER = "teacher", "Teacher"
    STUDENT = "student", "Student"
    STAFF = "staff", "Staff Member"


class User(AbstractUser):
    """
    Base user account for the Perfect Foundation School Management System.

    Staff and students will be connected to this account through
    their respective profiles.
    """

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)

    photo = models.ImageField(
        upload_to="profiles/users/",
        blank=True,
        null=True,
    )

    def get_active_memberships(self):
        return self.memberships.filter(status="active").select_related(
            "institution"
        )

    def get_roles(self, institution=None):
        memberships = self.get_active_memberships()

        if institution is not None:
            memberships = memberships.filter(institution=institution)

        return list(
            RoleAssignment.objects.filter(
                membership__in=memberships
            ).values_list("role", flat=True)
        )

    def has_role(self, role, institution=None):
        return role in self.get_roles(institution)

    def has_any_role(self, roles, institution=None):
        if self.is_superuser:
            return True

        return any(
            self.has_role(role, institution)
            for role in roles
        )

    @property
    def primary_role(self):
        roles = self.get_roles()

        priority = [
            Role.SUPER_ADMIN,
            Role.ADMIN,
            Role.PRINCIPAL,
            Role.ACADEMIC,
            Role.ACCOUNTANT,
            Role.TEACHER,
            Role.STAFF,
            Role.STUDENT,
        ]

        for candidate in priority:
            if candidate in roles:
                return candidate

        return None

    @property
    def primary_institution(self):
        membership = self.get_active_memberships().first()
        return membership.institution if membership else None

    def __str__(self):
        return self.username


class InstitutionMembership(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("suspended", "Suspended"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    joined_at = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "institution"],
                name="unique_membership_per_user_institution",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} @ {self.institution.name}"
        )


class RoleAssignment(models.Model):
    membership = models.ForeignKey(
        InstitutionMembership,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["role"]
        constraints = [
            models.UniqueConstraint(
                fields=["membership", "role"],
                name="unique_role_per_membership",
            )
        ]

    def __str__(self):
        return f"{self.membership} - {self.get_role_display()}"


class StaffProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )

    employee_number = models.CharField(
        max_length=50,
        unique=True,
    )

    designation = models.CharField(
        max_length=100,
        default="Staff",
    )

    department = models.CharField(
        max_length=100,
        blank=True,
    )

    joining_date = models.DateField(
        null=True,
        blank=True,
    )

    photo = models.ImageField(
        upload_to="profiles/staff/",
        blank=True,
        null=True,
    )

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.employee_number} - "
            f"{self.user.get_full_name() or self.user.username}"
        )
