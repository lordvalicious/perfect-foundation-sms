from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from apps.core.models import SoftDeleteMixin, SoftDeleteManager
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
    Base user account for the School Management System.

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

    twofa_secret = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    twofa_enabled = models.BooleanField(default=False)

    # Account security fields
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_failed_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_failed_login_at = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(auto_now_add=True)
    must_change_password = models.BooleanField(default=False)

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

    # =========================================================================
    # PERMISSION CHECKING METHODS
    # =========================================================================
    
    def get_permissions(self, institution=None):
        """
        Get all effective permissions for the user in an institution.
        
        Returns a set of permission codenames combining:
        - Role-based permissions (via RolePermission)
        - User-specific allow overrides (via UserPermission with effect=allow)
        - Excludes user-specific deny overrides (via UserPermission with effect=deny)
        """
        if institution is None:
            institution = self.primary_institution
        
        if institution is None:
            return set()
        
        # Get role-based permissions
        memberships = self.get_active_memberships().filter(institution=institution)
        role_names = RoleAssignment.objects.filter(
            membership__in=memberships
        ).values_list("role", flat=True).distinct()
        
        role_perms = set()
        if role_names:
            role_perms = set(RolePermission.objects.filter(
                role__in=role_names,
                institution=institution,
            ).values_list("permission__codename", flat=True))
        
        # Get user-specific allow permissions
        allow_perms = set(UserPermission.objects.filter(
            user=self,
            institution=institution,
            effect="allow",
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        ).values_list("permission__codename", flat=True))
        
        # Get user-specific deny permissions
        deny_perms = set(UserPermission.objects.filter(
            user=self,
            institution=institution,
            effect="deny",
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        ).values_list("permission__codename", flat=True))
        
        # Combine: role perms + allow perms - deny perms
        effective = (role_perms | allow_perms) - deny_perms
        
        # Superuser gets all permissions
        if self.is_superuser:
            return set(Permission.objects.values_list("codename", flat=True))
        
        return effective
    
    def has_permission(self, codename, institution=None):
        """Check if user has a specific permission."""
        return codename in self.get_permissions(institution)
    
    def has_any_permission(self, codenames, institution=None):
        """Check if user has any of the given permissions."""
        perms = self.get_permissions(institution)
        return any(c in perms for c in codenames)
    
    def has_all_permissions(self, codenames, institution=None):
        """Check if user has all of the given permissions."""
        perms = self.get_permissions(institution)
        return all(c in perms for c in codenames)


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


class StaffProfile(SoftDeleteMixin):
    objects = SoftDeleteManager()
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="staff_profiles",
        null=True,
        blank=True,
    )

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_profile",
    )

    membership = models.OneToOneField(InstitutionMembership, on_delete=models.SET_NULL, null=True, blank=True, related_name="staff_profile_membership")
    primary_campus = models.ForeignKey("schools.Campus", on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_staff")

    employee_number = models.CharField(
        max_length=50,
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
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "employee_number"],
                name="unique_staff_employee_number_per_institution",
            )
        ]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return (
            f"{self.employee_number} - "
            f"{self.full_name or self.user.get_full_name() or self.user.username}"
        )


class StaffAttendance(SoftDeleteMixin):
    objects = SoftDeleteManager()
    """Daily attendance record for a staff member / teacher."""

    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("half_day", "Half Day"),
        ("leave", "On Leave"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="staff_attendance",
        null=True,
        blank=True,
    )

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

    @property
    def working_hours(self):
        """Compute elapsed working time from check_in / check_out.

        Returns a ``timedelta``, or ``None`` when either timestamp is missing.
        """
        if self.check_in is None or self.check_out is None:
            return None

        from datetime import datetime

        start = datetime.combine(self.date, self.check_in)
        end = datetime.combine(self.date, self.check_out)
        if end < start:
            # Overnight shift: assume wrap-around to the next day.
            from datetime import timedelta

            end += timedelta(days=1)
        return end - start


class StaffAttendanceCorrection(SoftDeleteMixin):
    """
    Immutable audit trail for every change made to a staff attendance record.

    Each correction preserves the old value and the new value (status and
    check-in/check-out), who performed it, when, and why. Corrections are
    never edited or deleted, so the full history is retained.
    """

    objects = SoftDeleteManager()

    attendance = models.ForeignKey(
        StaffAttendance,
        on_delete=models.CASCADE,
        related_name="corrections",
    )

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="attendance_corrections",
    )

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="staff_attendance_corrections",
        null=True,
        blank=True,
    )

    from_status = models.CharField(
        max_length=20,
        choices=StaffAttendance.STATUS_CHOICES,
    )
    to_status = models.CharField(
        max_length=20,
        choices=StaffAttendance.STATUS_CHOICES,
    )

    from_check_in = models.TimeField(null=True, blank=True)
    to_check_in = models.TimeField(null=True, blank=True)
    from_check_out = models.TimeField(null=True, blank=True)
    to_check_out = models.TimeField(null=True, blank=True)

    reason = models.TextField(blank=True)

    corrected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_attendance_corrections_made",
    )

    corrected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-corrected_at"]
        indexes = [
            models.Index(
                fields=["attendance", "-corrected_at"],
                name="staff_att_corr_att_idx",
            ),
            models.Index(
                fields=["staff", "corrected_by"],
                name="staff_att_corr_staff_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.staff} {self.attendance.date}: "
            f"{self.from_status} -> {self.to_status}"
        )


class StaffLeave(SoftDeleteMixin):
    objects = SoftDeleteManager()
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

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="staff_leaves",
        null=True,
        blank=True,
    )

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


class FailedLoginAttempt(models.Model):
    """Track failed login attempts for account lockout."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="failed_login_records",
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    username_or_email = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(
                fields=["user", "attempted_at"],
                name="failed_login_user_time_idx",
            ),
            models.Index(
                fields=["ip_address", "attempted_at"],
                name="failed_login_ip_time_idx",
            ),
        ]

    def __str__(self):
        return f"Failed login for {self.username_or_email} from {self.ip_address}"


class PasswordHistory(models.Model):
    """Store password history to prevent reuse."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_history",
    )
    password_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "created_at"],
                name="pwdhist_user_time_idx",
            ),
        ]

    def __str__(self):
        return f"Password history for {self.user.username}"


class UserSession(models.Model):
    """Track active user sessions for management and revocation."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_sessions",
    )
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-last_activity_at"]
        indexes = [
            models.Index(
                fields=["user", "is_current"],
                name="usersession_user_current_idx",
            ),
            models.Index(
                fields=["expires_at"],
                name="usersession_expires_idx",
            ),
        ]

    def __str__(self):
        return f"Session for {self.user.username} from {self.ip_address}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at


class TwoFABackupCode(models.Model):
    """Backup codes for TOTP 2FA recovery."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="twofa_backup_codes",
    )
    code_hash = models.CharField(max_length=128)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "used_at"],
                name="twofa_backup_user_used_idx",
            ),
        ]

    def __str__(self):
        status = "used" if self.used_at else "unused"
        return f"2FA backup code ({status}) for {self.user.username}"


# =============================================================================
# GRANULAR PERMISSIONS SYSTEM
# =============================================================================

class Permission(models.Model):
    """
    Granular permissions for the ERP system.
    
    Naming convention: <resource>.<action>
    Examples:
    - student.view, student.create, student.edit, student.delete
    - student.approve, student.reject, student.export, student.print
    - finance.invoice.view, finance.invoice.create, finance.invoice.edit
    - finance.payment.view, finance.payment.create, finance.payment.approve
    - exam.view, exam.create, exam.edit, exam.delete, exam.publish
    - attendance.view, attendance.create, attendance.edit
    - hr.employee.view, hr.employee.create, hr.employee.edit
    - payroll.view, payroll.create, payroll.approve, payroll.process
    - settings.view, settings.edit
    - report.view, report.export
    - user.manage, role.manage, permission.manage
    """
    
    ACTION_CHOICES = [
        ("view", "View"),
        ("create", "Create"),
        ("edit", "Edit"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("approve", "Approve"),
        ("reject", "Reject"),
        ("export", "Export"),
        ("print", "Print"),
        ("manage", "Manage"),
        ("publish", "Publish"),
        ("process", "Process"),
        ("assign", "Assign"),
        ("unassign", "Unassign"),
    ]
    
    # Resource categories for organization
    CATEGORY_CHOICES = [
        ("student", "Student Management"),
        ("teacher", "Teacher Management"),
        ("staff", "Staff Management"),
        ("admission", "Admissions"),
        ("attendance", "Attendance"),
        ("exam", "Examinations"),
        ("finance", "Finance & Fees"),
        ("payroll", "Payroll"),
        ("hr", "Human Resources"),
        ("library", "Library"),
        ("transport", "Transport"),
        ("inventory", "Inventory"),
        ("hostel", "Hostel"),
        ("lms", "Learning Management"),
        ("communication", "Communication"),
        ("settings", "Settings"),
        ("report", "Reports"),
        ("user", "User Management"),
        ("role", "Role Management"),
        ("permission", "Permission Management"),
        ("system", "System Administration"),
    ]
    
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    is_system = models.BooleanField(default=False, help_text="System permissions cannot be deleted")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["category", "action", "codename"]
        indexes = [
            models.Index(fields=["category", "action"], name="perm_cat_action_idx"),
        ]
    
    def __str__(self):
        return f"{self.codename} ({self.name})"
    
    @classmethod
    def get_default_permissions(cls):
        """Return the standard set of permissions for the ERP."""
        return [
            # Student permissions
            ("student.view", "View Students", "student", "view"),
            ("student.create", "Create Students", "student", "create"),
            ("student.edit", "Edit Students", "student", "edit"),
            ("student.delete", "Delete Students", "student", "delete"),
            ("student.export", "Export Students", "student", "export"),
            ("student.print", "Print Students", "student", "print"),
            ("student.approve", "Approve Student Status", "student", "approve"),
            ("student.assign", "Assign Student to Class", "student", "assign"),
            
            # Teacher permissions
            ("teacher.view", "View Teachers", "teacher", "view"),
            ("teacher.create", "Create Teachers", "teacher", "create"),
            ("teacher.edit", "Edit Teachers", "teacher", "edit"),
            ("teacher.delete", "Delete Teachers", "teacher", "delete"),
            ("teacher.export", "Export Teachers", "teacher", "export"),
            ("teacher.assign", "Assign Teacher to Class", "teacher", "assign"),
            
            # Staff permissions
            ("staff.view", "View Staff", "staff", "view"),
            ("staff.create", "Create Staff", "staff", "create"),
            ("staff.edit", "Edit Staff", "staff", "edit"),
            ("staff.delete", "Delete Staff", "staff", "delete"),
            ("staff.export", "Export Staff", "staff", "export"),
            ("staff.assign", "Assign Staff", "staff", "assign"),
            
            # Admission permissions
            ("admission.view", "View Admissions", "admission", "view"),
            ("admission.create", "Create Admissions", "admission", "create"),
            ("admission.edit", "Edit Admissions", "admission", "edit"),
            ("admission.delete", "Delete Admissions", "admission", "delete"),
            ("admission.approve", "Approve Admissions", "admission", "approve"),
            ("admission.reject", "Reject Admissions", "admission", "reject"),
            
            # Attendance permissions
            ("attendance.view", "View Attendance", "attendance", "view"),
            ("attendance.create", "Mark Attendance", "attendance", "create"),
            ("attendance.edit", "Edit Attendance", "attendance", "edit"),
            ("attendance.delete", "Delete Attendance", "attendance", "delete"),
            ("attendance.approve", "Approve Attendance", "attendance", "approve"),
            ("attendance.export", "Export Attendance", "attendance", "export"),
            ("attendance.print", "Print Attendance", "attendance", "print"),
            
            # Exam permissions
            ("exam.view", "View Exams", "exam", "view"),
            ("exam.create", "Create Exams", "exam", "create"),
            ("exam.edit", "Edit Exams", "exam", "edit"),
            ("exam.delete", "Delete Exams", "exam", "delete"),
            ("exam.publish", "Publish Exams", "exam", "publish"),
            ("exam.result.view", "View Exam Results", "exam", "view"),
            ("exam.result.create", "Enter Exam Results", "exam", "create"),
            ("exam.result.edit", "Edit Exam Results", "exam", "edit"),
            ("exam.result.approve", "Approve Exam Results", "exam", "approve"),
            ("exam.result.export", "Export Exam Results", "exam", "export"),
            ("exam.result.print", "Print Exam Results", "exam", "print"),
            
            # Finance permissions
            ("finance.fee_category.view", "View Fee Categories", "finance", "view"),
            ("finance.fee_category.create", "Create Fee Categories", "finance", "create"),
            ("finance.fee_category.edit", "Edit Fee Categories", "finance", "edit"),
            ("finance.fee_category.delete", "Delete Fee Categories", "finance", "delete"),
            ("finance.fee_structure.view", "View Fee Structures", "finance", "view"),
            ("finance.fee_structure.create", "Create Fee Structures", "finance", "create"),
            ("finance.fee_structure.edit", "Edit Fee Structures", "finance", "edit"),
            ("finance.fee_structure.delete", "Delete Fee Structures", "finance", "delete"),
            ("finance.invoice.view", "View Invoices", "finance", "view"),
            ("finance.invoice.create", "Create Invoices", "finance", "create"),
            ("finance.invoice.edit", "Edit Invoices", "finance", "edit"),
            ("finance.invoice.delete", "Delete Invoices", "finance", "delete"),
            ("finance.invoice.approve", "Approve Invoices", "finance", "approve"),
            ("finance.invoice.export", "Export Invoices", "finance", "export"),
            ("finance.invoice.print", "Print Invoices", "finance", "print"),
            ("finance.payment.view", "View Payments", "finance", "view"),
            ("finance.payment.create", "Record Payments", "finance", "create"),
            ("finance.payment.edit", "Edit Payments", "finance", "edit"),
            ("finance.payment.delete", "Delete Payments", "finance", "delete"),
            ("finance.payment.approve", "Approve Payments", "finance", "approve"),
            ("finance.payment.refund", "Refund Payments", "finance", "reject"),
            ("finance.concession.view", "View Concessions", "finance", "view"),
            ("finance.concession.create", "Create Concessions", "finance", "create"),
            ("finance.concession.approve", "Approve Concessions", "finance", "approve"),
            ("finance.concession.reject", "Reject Concessions", "finance", "reject"),
            ("finance.expense.view", "View Expenses", "finance", "view"),
            ("finance.expense.create", "Create Expenses", "finance", "create"),
            ("finance.expense.edit", "Edit Expenses", "finance", "edit"),
            ("finance.expense.approve", "Approve Expenses", "finance", "approve"),
            ("finance.journal.view", "View Journal Entries", "finance", "view"),
            ("finance.journal.create", "Create Journal Entries", "finance", "create"),
            ("finance.journal.edit", "Edit Journal Entries", "finance", "edit"),
            ("finance.journal.approve", "Approve Journal Entries", "finance", "approve"),
            ("finance.export", "Export Finance Data", "finance", "export"),
            ("finance.print", "Print Finance Reports", "finance", "print"),
            
            # Payroll permissions
            ("payroll.view", "View Payroll", "payroll", "view"),
            ("payroll.create", "Create Payroll", "payroll", "create"),
            ("payroll.edit", "Edit Payroll", "payroll", "edit"),
            ("payroll.process", "Process Payroll", "payroll", "process"),
            ("payroll.approve", "Approve Payroll", "payroll", "approve"),
            ("payroll.export", "Export Payroll", "payroll", "export"),
            ("payroll.print", "Print Payslips", "payroll", "print"),
            ("payroll.salary_structure.view", "View Salary Structures", "payroll", "view"),
            ("payroll.salary_structure.create", "Create Salary Structures", "payroll", "create"),
            ("payroll.salary_structure.edit", "Edit Salary Structures", "payroll", "edit"),
            
            # HR permissions
            ("hr.employee.view", "View Employees", "hr", "view"),
            ("hr.employee.create", "Create Employees", "hr", "create"),
            ("hr.employee.edit", "Edit Employees", "hr", "edit"),
            ("hr.employee.delete", "Delete Employees", "hr", "delete"),
            ("hr.contract.view", "View Contracts", "hr", "view"),
            ("hr.contract.create", "Create Contracts", "hr", "create"),
            ("hr.contract.edit", "Edit Contracts", "hr", "edit"),
            ("hr.contract.approve", "Approve Contracts", "hr", "approve"),
            ("hr.document.view", "View Documents", "hr", "view"),
            ("hr.document.create", "Upload Documents", "hr", "create"),
            ("hr.performance.view", "View Performance", "hr", "view"),
            ("hr.performance.create", "Create Performance Reviews", "hr", "create"),
            ("hr.performance.edit", "Edit Performance Reviews", "hr", "edit"),
            ("hr.workload.view", "View Workload", "hr", "view"),
            ("hr.workload.create", "Create Workload Assignments", "hr", "create"),
            ("hr.workload.edit", "Edit Workload Assignments", "hr", "edit"),
            ("hr.export", "Export HR Data", "hr", "export"),
            
            # Library permissions
            ("library.book.view", "View Books", "library", "view"),
            ("library.book.create", "Add Books", "library", "create"),
            ("library.book.edit", "Edit Books", "library", "edit"),
            ("library.book.delete", "Delete Books", "library", "delete"),
            ("library.issue.view", "View Book Issues", "library", "view"),
            ("library.issue.create", "Issue Books", "library", "create"),
            ("library.issue.return", "Return Books", "library", "update"),
            ("library.issue.overdue", "Manage Overdue", "library", "manage"),
            ("library.export", "Export Library Data", "library", "export"),
            
            # Transport permissions
            ("transport.vehicle.view", "View Vehicles", "transport", "view"),
            ("transport.vehicle.create", "Add Vehicles", "transport", "create"),
            ("transport.vehicle.edit", "Edit Vehicles", "transport", "edit"),
            ("transport.route.view", "View Routes", "transport", "view"),
            ("transport.route.create", "Create Routes", "transport", "create"),
            ("transport.route.edit", "Edit Routes", "transport", "edit"),
            ("transport.student.view", "View Student Transport", "transport", "view"),
            ("transport.student.assign", "Assign Student Transport", "transport", "assign"),
            ("transport.export", "Export Transport Data", "transport", "export"),
            
            # Inventory permissions
            ("inventory.item.view", "View Inventory Items", "inventory", "view"),
            ("inventory.item.create", "Add Inventory Items", "inventory", "create"),
            ("inventory.item.edit", "Edit Inventory Items", "inventory", "edit"),
            ("inventory.item.delete", "Delete Inventory Items", "inventory", "delete"),
            ("inventory.stock.view", "View Stock", "inventory", "view"),
            ("inventory.stock.adjust", "Adjust Stock", "inventory", "edit"),
            ("inventory.order.view", "View Purchase Orders", "inventory", "view"),
            ("inventory.order.create", "Create Purchase Orders", "inventory", "create"),
            ("inventory.order.approve", "Approve Purchase Orders", "inventory", "approve"),
            ("inventory.export", "Export Inventory Data", "inventory", "export"),
            
            # Hostel permissions
            ("hostel.room.view", "View Rooms", "hostel", "view"),
            ("hostel.room.create", "Create Rooms", "hostel", "create"),
            ("hostel.room.edit", "Edit Rooms", "hostel", "edit"),
            ("hostel.allocation.view", "View Allocations", "hostel", "view"),
            ("hostel.allocation.create", "Create Allocations", "hostel", "create"),
            ("hostel.allocation.edit", "Edit Allocations", "hostel", "edit"),
            ("hostel.fee.view", "View Hostel Fees", "hostel", "view"),
            ("hostel.fee.create", "Create Hostel Fees", "hostel", "create"),
            ("hostel.export", "Export Hostel Data", "hostel", "export"),
            
            # LMS permissions
            ("lms.course.view", "View Courses", "lms", "view"),
            ("lms.course.create", "Create Courses", "lms", "create"),
            ("lms.course.edit", "Edit Courses", "lms", "edit"),
            ("lms.course.delete", "Delete Courses", "lms", "delete"),
            ("lms.lesson.view", "View Lessons", "lms", "view"),
            ("lms.lesson.create", "Create Lessons", "lms", "create"),
            ("lms.lesson.edit", "Edit Lessons", "lms", "edit"),
            ("lms.enrollment.view", "View Enrollments", "lms", "view"),
            ("lms.enrollment.manage", "Manage Enrollments", "lms", "manage"),
            ("lms.assignment.view", "View Assignments", "lms", "view"),
            ("lms.assignment.create", "Create Assignments", "lms", "create"),
            ("lms.assignment.grade", "Grade Assignments", "lms", "approve"),
            ("lms.export", "Export LMS Data", "lms", "export"),
            
            # Communication permissions
            ("communication.announcement.view", "View Announcements", "communication", "view"),
            ("communication.announcement.create", "Create Announcements", "communication", "create"),
            ("communication.announcement.edit", "Edit Announcements", "communication", "edit"),
            ("communication.announcement.delete", "Delete Announcements", "communication", "delete"),
            ("communication.message.view", "View Messages", "communication", "view"),
            ("communication.message.send", "Send Messages", "communication", "create"),
            ("communication.sms.view", "View SMS", "communication", "view"),
            ("communication.sms.send", "Send SMS", "communication", "create"),
            ("communication.template.view", "View Templates", "communication", "view"),
            ("communication.template.create", "Create Templates", "communication", "create"),
            ("communication.template.edit", "Edit Templates", "communication", "edit"),
            
            # Settings permissions
            ("settings.view", "View Settings", "settings", "view"),
            ("settings.edit", "Edit Settings", "settings", "edit"),
            ("settings.branding.view", "View Branding", "settings", "view"),
            ("settings.branding.edit", "Edit Branding", "settings", "edit"),
            ("settings.module.view", "View Modules", "settings", "view"),
            ("settings.module.edit", "Edit Modules", "settings", "edit"),
            
            # Report permissions
            ("report.view", "View Reports", "report", "view"),
            ("report.create", "Create Reports", "report", "create"),
            ("report.edit", "Edit Reports", "report", "edit"),
            ("report.delete", "Delete Reports", "report", "delete"),
            ("report.export", "Export Reports", "report", "export"),
            ("report.print", "Print Reports", "report", "print"),
            ("report.builder.view", "View Report Builder", "report", "view"),
            ("report.builder.create", "Create Report Templates", "report", "create"),
            
            # User/Role/Permission management
            ("user.view", "View Users", "user", "view"),
            ("user.create", "Create Users", "user", "create"),
            ("user.edit", "Edit Users", "user", "edit"),
            ("user.delete", "Delete Users", "user", "delete"),
            ("user.manage", "Manage User Accounts", "user", "manage"),
            ("role.view", "View Roles", "role", "view"),
            ("role.create", "Create Roles", "role", "create"),
            ("role.edit", "Edit Roles", "role", "edit"),
            ("role.delete", "Delete Roles", "role", "delete"),
            ("role.manage", "Manage Roles", "role", "manage"),
            ("permission.view", "View Permissions", "permission", "view"),
            ("permission.assign", "Assign Permissions", "permission", "assign"),
            
            # System permissions
            ("system.audit.view", "View Audit Logs", "system", "view"),
            ("system.backup", "Manage Backups", "system", "manage"),
            ("system.maintenance", "System Maintenance", "system", "manage"),
        ]


class RolePermission(models.Model):
    """
    Assign permissions to roles within an institution.
    
    This allows customizing what each role can do per institution.
    """
    role = models.CharField(max_length=30, choices=Role.choices)
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_role_permissions",
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["role", "permission__category", "permission__action"]
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission", "institution"],
                name="unique_role_permission_per_institution",
            ),
        ]
        indexes = [
            models.Index(fields=["role", "institution"], name="roleperm_role_inst_idx"),
        ]
    
    def __str__(self):
        return f"{self.role} -> {self.permission.codename} @ {self.institution.name}"


class UserPermission(models.Model):
    """
    User-specific permission overrides.
    
    Allows granting or denying specific permissions to individual users
    beyond their role-based permissions.
    """
    EFFECT_CHOICES = [
        ("allow", "Allow"),
        ("deny", "Deny"),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="custom_user_permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="user_permissions",
    )
    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="user_permissions",
    )
    effect = models.CharField(max_length=10, choices=EFFECT_CHOICES, default="allow")
    reason = models.TextField(blank=True)
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_user_permissions",
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-granted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "permission", "institution"],
                name="unique_user_permission_per_institution",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "institution"], name="userperm_user_inst_idx"),
        ]
    
    def __str__(self):
        return f"{self.user.username} -> {self.permission.codename} ({self.effect}) @ {self.institution.name}"
    
    def is_active(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True
