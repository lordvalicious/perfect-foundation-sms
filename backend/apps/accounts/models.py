from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.schools.models import School


class Role(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Platform Super Admin"
    ADMIN = "admin", "Institution Admin"
    PRINCIPAL = "principal", "Principal"
    VICE_PRINCIPAL = "vice_principal", "Vice Principal"
    CAMPUS_ADMIN = "campus_admin", "Campus Administrator"
    ACADEMIC = "academic", "Academic Administrator"
    ACCOUNTANT = "accountant", "Accountant"
    HR = "hr", "HR / Staff Officer"
    RECEPTIONIST = "receptionist", "Receptionist"
    TEACHER = "teacher", "Teacher"
    PARENT = "parent", "Parent / Guardian"
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
            Role.VICE_PRINCIPAL,
            Role.CAMPUS_ADMIN,
            Role.ACADEMIC,
            Role.ACCOUNTANT,
            Role.HR,
            Role.RECEPTIONIST,
            Role.TEACHER,
            Role.PARENT,
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
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_profile",
    )

    employee_number = models.CharField(
        max_length=50,
        unique=True,
    )

    photo = models.ImageField(
        upload_to="profiles/staff/",
        blank=True,
        null=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
    )

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    campus = models.CharField(
        max_length=150,
        blank=True,
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

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return (
            f"{self.employee_number} - "
            f"{self.full_name or self.user.get_full_name() or self.user.username}"
        )


class StaffAttendance(models.Model):
    """Daily attendance record for a staff member / teacher."""

    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("half_day", "Half Day"),
        ("leave", "On Leave"),
    ]

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="present",
    )

    check_in = models.TimeField(
        null=True,
        blank=True,
    )

    check_out = models.TimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_staff_attendance",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "staff__first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["staff", "date"],
                name="unique_staff_attendance_per_day",
            )
        ]

    def __str__(self):
        return f"{self.staff} - {self.date} - {self.get_status_display()}"


class StaffLeave(models.Model):
    """Leave request raised by staff/teachers and approved by HR."""

    LEAVE_TYPE_CHOICES = [
        ("casual", "Casual Leave"),
        ("sick", "Sick Leave"),
        ("annual", "Annual Leave"),
        ("maternity", "Maternity Leave"),
        ("paternity", "Paternity Leave"),
        ("unpaid", "Unpaid Leave"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )

    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPE_CHOICES,
    )

    start_date = models.DateField()
    end_date = models.DateField()

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_staff_leave",
    )

    review_notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return (
            f"{self.staff} - {self.get_leave_type_display()} "
            f"({self.start_date} to {self.end_date})"
        )
