from rest_framework import serializers

from .models import (
    Employee,
    EmployeeDocument,
    EmploymentContract,
    EmploymentEvent,
    PerformanceReview,
    WorkloadAssignment,
    Department,
    Designation,
    LeaveType,
    LeavePolicy,
    LeaveBalance,
    LeaveRequest,
    Allowance,
    Deduction,
    Bonus,
    Overtime,
    Loan,
    Advance,
    SalaryRevision,
    PayrollPeriod,
    ExitClearance,
    ClearanceItem,
    JobPosition,
    Candidate,
    Application,
    Interview,
)


class DepartmentSerializer(serializers.ModelSerializer):
    head_name = serializers.CharField(source="head.full_name", read_only=True)
    sub_departments_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            "id", "institution", "campus", "name", "code", "description",
            "head", "head_name", "parent", "status", "sub_departments_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "created_at", "updated_at"]

    def get_sub_departments_count(self, obj):
        return obj.sub_departments.count()


class DesignationSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Designation
        fields = [
            "id", "institution", "department", "department_name", "name", "code",
            "description", "level", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "created_at", "updated_at"]


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    profile_type = serializers.SerializerMethodField()
    department_name = serializers.CharField(source="department.name", read_only=True)
    designation_name = serializers.CharField(source="designation.name", read_only=True)
    manager_name = serializers.CharField(source="manager.full_name", read_only=True)
    primary_campus_name = serializers.CharField(source="primary_campus.name", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id", "institution", "teacher", "staff_profile", "employee_number",
            "primary_campus", "primary_campus_name", "department", "department_name",
            "designation", "designation_name", "employment_type", "joining_date",
            "confirmation_date", "status", "manager", "manager_name",
            "full_name", "profile_type", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "full_name", "profile_type", "created_at", "updated_at"]

    def get_profile_type(self, obj):
        return "teacher" if obj.teacher_id else "staff"


class EmployeeDetailSerializer(EmployeeSerializer):
    """Extended employee serializer with related data."""

    contracts = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    leave_balances = serializers.SerializerMethodField()
    performance_reviews = serializers.SerializerMethodField()
    workload_assignments = serializers.SerializerMethodField()
    employment_events = serializers.SerializerMethodField()
    loans = serializers.SerializerMethodField()
    advances = serializers.SerializerMethodField()
    salary_revisions = serializers.SerializerMethodField()
    exit_clearances = serializers.SerializerMethodField()

    class Meta(EmployeeSerializer.Meta):
        fields = EmployeeSerializer.Meta.fields + [
            "contracts", "documents", "leave_balances", "performance_reviews",
            "workload_assignments", "employment_events", "loans", "advances",
            "salary_revisions", "exit_clearances",
        ]

    def get_contracts(self, obj):
        from .serializers import EmploymentContractSerializer
        return EmploymentContractSerializer(obj.contracts.all()[:5], many=True).data

    def get_documents(self, obj):
        return EmployeeDocumentSerializer(obj.documents.all()[:5], many=True).data

    def get_leave_balances(self, obj):
        from .serializers import LeaveBalanceSerializer
        return LeaveBalanceSerializer(obj.leave_balances.all(), many=True).data

    def get_performance_reviews(self, obj):
        return PerformanceReviewSerializer(obj.performance_reviews.all()[:5], many=True).data

    def get_workload_assignments(self, obj):
        return WorkloadAssignmentSerializer(obj.workload_assignments.all()[:5], many=True).data

    def get_employment_events(self, obj):
        return EmploymentEventSerializer(obj.employment_events.all()[:5], many=True).data

    def get_loans(self, obj):
        from .serializers import LoanSerializer
        return LoanSerializer(obj.loans.all()[:5], many=True).data

    def get_advances(self, obj):
        from .serializers import AdvanceSerializer
        return AdvanceSerializer(obj.advances.all()[:5], many=True).data

    def get_salary_revisions(self, obj):
        from .serializers import SalaryRevisionSerializer
        return SalaryRevisionSerializer(obj.salary_revisions.all()[:5], many=True).data

    def get_exit_clearances(self, obj):
        from .serializers import ExitClearanceSerializer
        return ExitClearanceSerializer(obj.exit_clearances.all()[:5], many=True).data


class EmploymentContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentContract
        fields = [
            "id", "employee", "contract_number", "contract_type", "start_date",
            "end_date", "salary", "terms", "document", "status", "created_at",
        ]
        read_only_fields = ["id", "employee", "created_at"]


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDocument
        fields = [
            "id", "employee", "document_type", "title", "file", "file_url",
            "expiry_date", "notes", "uploaded_by", "created_at",
        ]
        read_only_fields = ["id", "employee", "file_url", "uploaded_by", "created_at"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return None
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url


class WorkloadAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkloadAssignment
        fields = [
            "id", "employee", "academic_year", "title", "weekly_periods",
            "hours_per_week", "notes", "status", "created_at",
        ]
        read_only_fields = ["id", "employee", "created_at"]


class PerformanceReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.get_full_name", read_only=True)

    class Meta:
        model = PerformanceReview
        fields = [
            "id", "employee", "reviewer", "reviewer_name", "review_date", "period",
            "rating", "strengths", "improvements", "goals", "status", "created_at",
        ]
        read_only_fields = ["id", "employee", "reviewer", "reviewer_name", "created_at"]


class EmploymentEventSerializer(serializers.ModelSerializer):
    from_campus_name = serializers.CharField(source="from_campus.name", read_only=True)
    to_campus_name = serializers.CharField(source="to_campus.name", read_only=True)
    recorded_by_name = serializers.CharField(source="recorded_by.get_full_name", read_only=True)

    class Meta:
        model = EmploymentEvent
        fields = [
            "id", "employee", "event_type", "effective_date", "from_campus", "from_campus_name",
            "to_campus", "to_campus_name", "previous_designation", "new_designation",
            "reason", "recorded_by", "recorded_by_name", "created_at",
        ]
        read_only_fields = ["id", "employee", "recorded_by", "recorded_by_name", "created_at"]


# Leave Serializers
class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = [
            "id", "institution", "name", "code", "category", "description",
            "is_paid", "requires_approval", "requires_document",
            "max_days_per_year", "max_consecutive_days", "carry_forward",
            "max_carry_forward_days", "gender_specific", "min_service_months",
            "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "created_at", "updated_at"]


class LeavePolicySerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = LeavePolicy
        fields = [
            "id", "institution", "department", "department_name", "leave_type",
            "leave_type_name", "eligibility_months", "accrual_rate",
            "max_accumulation", "probation_leave_allowed", "notice_days",
            "approval_hierarchy", "effective_from", "effective_to", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "created_at", "updated_at"]


class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    leave_type_category = serializers.CharField(source="leave_type.category", read_only=True)
    available_balance = serializers.ReadOnlyField()

    class Meta:
        model = LeaveBalance
        fields = [
            "id", "employee", "leave_type", "leave_type_name", "leave_type_category",
            "academic_year", "opening_balance", "accrued", "used", "pending",
            "carried_forward", "adjusted", "available_balance",
            "last_accrual_date", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    leave_type_category = serializers.CharField(source="leave_type.category", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)
    department_name = serializers.CharField(source="employee.department.name", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.get_full_name", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True)
    rejected_by_name = serializers.CharField(source="rejected_by.get_full_name", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            "id", "employee", "employee_name", "employee_number", "department_name",
            "leave_type", "leave_type_name", "leave_type_category", "leave_policy",
            "start_date", "end_date", "half_day", "half_day_session", "total_days",
            "reason", "attachment", "status", "applied_on", "reviewed_by",
            "reviewed_by_name", "reviewed_on", "review_comments", "approved_by",
            "approved_by_name", "approved_on", "rejected_by", "rejected_by_name",
            "rejected_on", "rejection_reason", "cancelled_by", "cancelled_on",
            "cancellation_reason", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "employee", "applied_on", "reviewed_by", "reviewed_on",
            "approved_by", "approved_on", "rejected_by", "rejected_on",
            "cancelled_by", "cancelled_on", "created_at", "updated_at",
        ]


# Salary Component Serializers
class AllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allowance
        fields = [
            "id", "institution", "name", "code", "description", "calculation_type",
            "amount", "percentage", "is_taxable", "is_fixed", "is_active",
            "applicable_to", "effective_from", "effective_to", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "created_at", "updated_at"]


class DeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deduction
        fields = [
            "id", "institution", "name", "code", "description", "calculation_type",
            "amount", "percentage", "is_mandatory", "is_pre_tax", "is_active",
            "applicable_to", "effective_from", "effective_to", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "created_at", "updated_at"]


class BonusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bonus
        fields = [
            "id", "institution", "name", "code", "bonus_type", "description",
            "is_recurring", "frequency", "calculation_method", "amount", "percentage",
            "eligibility_criteria", "is_active", "effective_from", "effective_to",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "created_at", "updated_at"]


class OvertimeSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True)
    payroll_period_name = serializers.CharField(source="payroll_period.name", read_only=True)

    class Meta:
        model = Overtime
        fields = [
            "id", "employee", "employee_name", "employee_number", "date",
            "overtime_type", "hours", "rate_per_hour", "amount", "description",
            "approved_by", "approved_by_name", "approved_on", "status",
            "payroll_period", "payroll_period_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "amount", "created_at", "updated_at"]


# Financial Serializers
class LoanSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True)

    class Meta:
        model = Loan
        fields = [
            "id", "employee", "employee_name", "employee_number", "loan_type",
            "principal_amount", "interest_rate", "interest_type", "tenure_months",
            "installment_amount", "total_installments", "paid_installments",
            "remaining_balance", "status", "applied_on", "approved_on",
            "approved_by", "approved_by_name", "disbursed_on", "first_installment_date",
            "rejection_reason", "purpose", "documents", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "remaining_balance", "paid_installments", "created_at", "updated_at",
        ]


class AdvanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True)

    class Meta:
        model = Advance
        fields = [
            "id", "employee", "employee_name", "employee_number", "amount", "reason",
            "requested_on", "approved_on", "approved_by", "approved_by_name",
            "status", "repayment_method", "number_of_installments", "installment_amount",
            "paid_amount", "remaining_balance", "rejection_reason", "purpose",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "paid_amount", "remaining_balance", "installment_amount",
            "created_at", "updated_at",
        ]


class SalaryRevisionSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True)

    class Meta:
        model = SalaryRevision
        fields = [
            "id", "employee", "employee_name", "employee_number", "revision_type",
            "previous_basic", "new_basic", "previous_gross", "new_gross",
            "effective_date", "reason", "approved_by", "approved_by_name",
            "approved_on", "effective_from", "document", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PayrollPeriodSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    processed_by_name = serializers.CharField(source="processed_by.get_full_name", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True)
    closed_by_name = serializers.CharField(source="closed_by.get_full_name", read_only=True)

    class Meta:
        model = PayrollPeriod
        fields = [
            "id", "institution", "campus", "campus_name", "name", "start_date",
            "end_date", "payment_date", "status", "processed_by", "processed_by_name",
            "processed_on", "approved_by", "approved_by_name", "approved_on",
            "closed_by", "closed_by_name", "closed_on", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "created_at", "updated_at"]


# Exit Clearance Serializers
class ClearanceItemSerializer(serializers.ModelSerializer):
    responsible_person_name = serializers.CharField(source="responsible_person.full_name", read_only=True)
    cleared_by_name = serializers.CharField(source="cleared_by.get_full_name", read_only=True)

    class Meta:
        model = ClearanceItem
        fields = [
            "id", "clearance", "department", "department_name", "responsible_person",
            "responsible_person_name", "status", "outstanding_items", "remarks",
            "cleared_on", "cleared_by", "cleared_by_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ExitClearanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)
    items = ClearanceItemSerializer(many=True, read_only=True)
    initiated_by_name = serializers.CharField(source="initiated_by.get_full_name", read_only=True)
    completed_by_name = serializers.CharField(source="completed_by.get_full_name", read_only=True)

    class Meta:
        model = ExitClearance
        fields = [
            "id", "employee", "employee_name", "employee_number", "resignation",
            "initiated_on", "expected_completion", "completed_on", "status",
            "initiated_by", "initiated_by_name", "completed_by", "completed_by_name",
            "notes", "items", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# Recruitment Serializers
class JobPositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    designation_name = serializers.CharField(source="designation.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = JobPosition
        fields = [
            "id", "institution", "department", "department_name", "designation",
            "designation_name", "title", "code", "description", "requirements",
            "qualifications", "experience_required", "employment_type", "salary_min",
            "salary_max", "vacancies", "location", "is_remote", "posted_on", "closes_on",
            "status", "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "posted_on", "created_at", "updated_at"]


class CandidateSerializer(serializers.ModelSerializer):
    applied_position_title = serializers.CharField(source="applied_position.title", read_only=True)
    screened_by_name = serializers.CharField(source="screened_by.get_full_name", read_only=True)

    class Meta:
        model = Candidate
        fields = [
            "id", "institution", "first_name", "last_name", "email", "phone",
            "current_organization", "current_designation", "experience_years",
            "current_salary", "expected_salary", "notice_period_days", "resume",
            "source", "status", "applied_position", "applied_position_title",
            "applied_on", "screened_on", "screened_by", "screened_by_name",
            "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "applied_on", "created_at", "updated_at"]


class ApplicationSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    position_title = serializers.CharField(source="position.title", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.get_full_name", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "candidate", "candidate_name", "position", "position_title",
            "applied_on", "cover_letter", "status", "reviewed_by", "reviewed_by_name",
            "reviewed_on", "review_comments", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "applied_on", "created_at", "updated_at"]


class InterviewSerializer(serializers.ModelSerializer):
    interviewer_name = serializers.CharField(source="interviewer.full_name", read_only=True)
    scheduled_by_name = serializers.CharField(source="scheduled_by.get_full_name", read_only=True)
    candidate_name = serializers.CharField(source="application.candidate.full_name", read_only=True)
    position_title = serializers.CharField(source="application.position.title", read_only=True)

    class Meta:
        model = Interview
        fields = [
            "id", "application", "candidate_name", "position_title", "interview_type",
            "round_number", "scheduled_on", "duration_minutes", "interviewer",
            "interviewer_name", "location", "meeting_link", "status", "feedback",
            "rating", "recommendation", "conducted_on", "scheduled_by",
            "scheduled_by_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# Exit Clearance Serializers
class ExitClearanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)
    items = ClearanceItemSerializer(many=True, read_only=True)
    initiated_by_name = serializers.CharField(source="initiated_by.get_full_name", read_only=True)
    completed_by_name = serializers.CharField(source="completed_by.get_full_name", read_only=True)

    class Meta:
        model = ExitClearance
        fields = [
            "id", "employee", "employee_name", "employee_number", "resignation",
            "initiated_on", "expected_completion", "completed_on", "status",
            "initiated_by", "initiated_by_name", "completed_by", "completed_by_name",
            "notes", "items", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]