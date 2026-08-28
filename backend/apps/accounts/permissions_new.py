"""Granular permission classes for Django REST Framework.

These replace the role-based permission classes with permission-based ones.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Permission


class HasPermission(BasePermission):
    """Require a specific permission codename."""
    
    permission_codename = None
    permission_codenames = None  # Alternative: list of codenames (any match)
    permission_all_required = False  # If True and multiple codenames, all required
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        institution = getattr(request, "institution", None)
        
        if self.permission_codenames:
            codenames = self.permission_codenames
            if self.permission_all_required:
                return request.user.has_all_permissions(codenames, institution)
            return request.user.has_any_permission(codenames, institution)
        
        if self.permission_codename:
            return request.user.has_permission(self.permission_codename, institution)
        
        # Try to get from view
        if hasattr(view, "permission_codename"):
            return request.user.has_permission(view.permission_codename, institution)
        if hasattr(view, "permission_codenames"):
            codenames = view.permission_codenames
            if getattr(view, "permission_all_required", False):
                return request.user.has_all_permissions(codenames, institution)
            return request.user.has_any_permission(codenames, institution)
        
        return False


class HasPermissionOrReadOnly(BasePermission):
    """Allow read access to authenticated users; write requires permission."""
    
    permission_codename = None
    permission_codenames = None
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.method in SAFE_METHODS:
            return True
        
        institution = getattr(request, "institution", None)
        
        if self.permission_codenames:
            return request.user.has_any_permission(self.permission_codenames, institution)
        
        if self.permission_codename:
            return request.user.has_permission(self.permission_codename, institution)
        
        if hasattr(view, "permission_codename"):
            return request.user.has_permission(view.permission_codename, institution)
        if hasattr(view, "permission_codenames"):
            return request.user.has_any_permission(view.permission_codenames, institution)
        
        return False


class HasModelPermission(BasePermission):
    """
    Permission class that maps HTTP methods to standard permissions.
    
    Mapping:
    - GET, HEAD, OPTIONS -> <model>.view
    - POST -> <model>.create
    - PUT, PATCH -> <model>.edit
    - DELETE -> <model>.delete
    
    The model name is derived from the queryset's model or can be specified.
    """
    
    model_name = None
    
    def __init__(self, model_name=None):
        self.model_name = model_name
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        institution = getattr(request, "institution", None)
        
        # Determine model name
        model_name = self.model_name
        if not model_name and hasattr(view, "queryset") and view.queryset is not None:
            model_name = view.queryset.model._meta.model_name
        if not model_name and hasattr(view, "model_name"):
            model_name = view.model_name
        
        if not model_name:
            return False
        
        # Map method to action
        method = request.method
        if method in ("GET", "HEAD", "OPTIONS"):
            action = "view"
        elif method == "POST":
            action = "create"
        elif method in ("PUT", "PATCH"):
            action = "edit"
        elif method == "DELETE":
            action = "delete"
        else:
            return False
        
        codename = f"{model_name}.{action}"
        return request.user.has_permission(codename, institution)


class IsSuperAdmin(BasePermission):
    """Require super_admin role (platform level)."""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return request.user.is_superuser or request.user.has_role("super_admin")


class IsInstitutionAdmin(BasePermission):
    """Require admin-level role in the current institution."""
    
    admin_roles = ["super_admin", "admin", "principal", "vice_principal"]
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        institution = getattr(request, "institution", None)
        return request.user.has_any_role(self.admin_roles, institution)


class IsCampusAdmin(BasePermission):
    """Require campus_admin or higher role."""
    
    campus_admin_roles = ["super_admin", "admin", "principal", "vice_principal", "campus_admin"]
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        institution = getattr(request, "institution", None)
        return request.user.has_any_role(self.campus_admin_roles, institution)


# Convenience permission classes for common resources
# These use the standard permission codenames

# Student permissions
class CanViewStudent(HasPermission):
    permission_codename = "student.view"

class CanCreateStudent(HasPermission):
    permission_codename = "student.create"

class CanEditStudent(HasPermission):
    permission_codename = "student.edit"

class CanDeleteStudent(HasPermission):
    permission_codename = "student.delete"

class CanApproveStudent(HasPermission):
    permission_codename = "student.approve"

class CanExportStudent(HasPermission):
    permission_codename = "student.export"

# Teacher permissions
class CanViewTeacher(HasPermission):
    permission_codename = "teacher.view"

class CanCreateTeacher(HasPermission):
    permission_codename = "teacher.create"

class CanEditTeacher(HasPermission):
    permission_codename = "teacher.edit"

class CanDeleteTeacher(HasPermission):
    permission_codename = "teacher.delete"

class CanAssignTeacher(HasPermission):
    permission_codename = "teacher.assign"

# Staff permissions
class CanViewStaff(HasPermission):
    permission_codename = "staff.view"

class CanCreateStaff(HasPermission):
    permission_codename = "staff.create"

class CanEditStaff(HasPermission):
    permission_codename = "staff.edit"

class CanDeleteStaff(HasPermission):
    permission_codename = "staff.delete"

# Admission permissions
class CanViewAdmission(HasPermission):
    permission_codename = "admission.view"

class CanCreateAdmission(HasPermission):
    permission_codename = "admission.create"

class CanEditAdmission(HasPermission):
    permission_codename = "admission.edit"

class CanApproveAdmission(HasPermission):
    permission_codename = "admission.approve"

class CanRejectAdmission(HasPermission):
    permission_codename = "admission.reject"

# Attendance permissions
class CanViewAttendance(HasPermission):
    permission_codename = "attendance.view"

class CanCreateAttendance(HasPermission):
    permission_codename = "attendance.create"

class CanEditAttendance(HasPermission):
    permission_codename = "attendance.edit"

class CanDeleteAttendance(HasPermission):
    permission_codename = "attendance.delete"

class CanExportAttendance(HasPermission):
    permission_codename = "attendance.export"

# Exam permissions
class CanViewExam(HasPermission):
    permission_codename = "exam.view"

class CanCreateExam(HasPermission):
    permission_codename = "exam.create"

class CanEditExam(HasPermission):
    permission_codename = "exam.edit"

class CanDeleteExam(HasPermission):
    permission_codename = "exam.delete"

class CanPublishExam(HasPermission):
    permission_codename = "exam.publish"

class CanEnterExamResult(HasPermission):
    permission_codename = "exam.result.create"

class CanEditExamResult(HasPermission):
    permission_codename = "exam.result.edit"

class CanApproveExamResult(HasPermission):
    permission_codename = "exam.result.approve"

# Finance permissions
class CanViewInvoice(HasPermission):
    permission_codename = "finance.invoice.view"

class CanCreateInvoice(HasPermission):
    permission_codename = "finance.invoice.create"

class CanEditInvoice(HasPermission):
    permission_codename = "finance.invoice.edit"

class CanDeleteInvoice(HasPermission):
    permission_codename = "finance.invoice.delete"

class CanApproveInvoice(HasPermission):
    permission_codename = "finance.invoice.approve"

class CanRecordPayment(HasPermission):
    permission_codename = "finance.payment.create"

class CanApprovePayment(HasPermission):
    permission_codename = "finance.payment.approve"

class CanRefundPayment(HasPermission):
    permission_codename = "finance.payment.refund"

class CanViewExpense(HasPermission):
    permission_codename = "finance.expense.view"

class CanCreateExpense(HasPermission):
    permission_codename = "finance.expense.create"

class CanApproveExpense(HasPermission):
    permission_codename = "finance.expense.approve"

class CanViewJournal(HasPermission):
    permission_codename = "finance.journal.view"

class CanCreateJournal(HasPermission):
    permission_codename = "finance.journal.create"

class CanApproveJournal(HasPermission):
    permission_codename = "finance.journal.approve"

# Payroll permissions
class CanViewPayroll(HasPermission):
    permission_codename = "payroll.view"

class CanCreatePayroll(HasPermission):
    permission_codename = "payroll.create"

class CanEditPayroll(HasPermission):
    permission_codename = "payroll.edit"

class CanProcessPayroll(HasPermission):
    permission_codename = "payroll.process"

class CanApprovePayroll(HasPermission):
    permission_codename = "payroll.approve"

class CanPrintPayslip(HasPermission):
    permission_codename = "payroll.print"

# HR permissions
class CanViewEmployee(HasPermission):
    permission_codename = "hr.employee.view"

class CanCreateEmployee(HasPermission):
    permission_codename = "hr.employee.create"

class CanEditEmployee(HasPermission):
    permission_codename = "hr.employee.edit"

class CanViewContract(HasPermission):
    permission_codename = "hr.contract.view"

class CanCreateContract(HasPermission):
    permission_codename = "hr.contract.create"

class CanApproveContract(HasPermission):
    permission_codename = "hr.contract.approve"

# Settings permissions
class CanViewSettings(HasPermission):
    permission_codename = "settings.view"

class CanEditSettings(HasPermission):
    permission_codename = "settings.edit"

class CanManageModules(HasPermission):
    permission_codename = "settings.module.edit"

# User/Role/Permission management
class CanManageUser(HasPermission):
    permission_codename = "user.manage"

class CanManageRole(HasPermission):
    permission_codename = "role.manage"

class CanAssignPermission(HasPermission):
    permission_codename = "permission.assign"

# Report permissions
class CanViewReport(HasPermission):
    permission_codename = "report.view"

class CanCreateReport(HasPermission):
    permission_codename = "report.create"

class CanExportReport(HasPermission):
    permission_codename = "report.export"

# System permissions
class CanViewAuditLog(HasPermission):
    permission_codename = "system.audit.view"