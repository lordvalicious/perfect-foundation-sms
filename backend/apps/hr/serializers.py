from rest_framework import serializers

from .models import (
    Employee,
    EmployeeDocument,
    EmploymentContract,
    EmploymentEvent,
    PerformanceReview,
    WorkloadAssignment,
)


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    profile_type = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            "id", "institution", "teacher", "staff_profile", "employee_number",
            "primary_campus", "designation", "department", "joining_date", "status",
            "full_name", "profile_type", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "institution", "full_name", "profile_type", "created_at", "updated_at"]

    def get_profile_type(self, obj):
        return "teacher" if obj.teacher_id else "staff"


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
    class Meta:
        model = EmploymentEvent
        fields = [
            "id", "employee", "event_type", "effective_date", "from_campus", "to_campus",
            "previous_designation", "new_designation", "reason", "recorded_by", "created_at",
        ]
        read_only_fields = ["id", "employee", "recorded_by", "created_at"]
