from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, assert_campus_allowed
from apps.accounts.permissions import IsAccountantRole, IsAdminOrReadOnly
from apps.accounts.scopes import is_manager

from .models import (
    Employee,
    EmployeeDocument,
    EmploymentContract,
    EmploymentEvent,
    PerformanceReview,
    WorkloadAssignment,
)
from .serializers import (
    EmployeeDocumentSerializer,
    EmployeeSerializer,
    EmploymentContractSerializer,
    EmploymentEventSerializer,
    PerformanceReviewSerializer,
    WorkloadAssignmentSerializer,
)


def employee_queryset(request):
    queryset = Employee.objects.select_related(
        "institution", "teacher", "staff_profile", "primary_campus"
    ).filter(institution=request.institution)
    return apply_campus_scope(queryset, request, "primary_campus_id")


def owned_queryset(model, request):
    return model.objects.filter(employee__in=employee_queryset(request))


class EmployeeListView(generics.ListAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        queryset = employee_queryset(self.request)
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                employee_number__icontains=search
            ) | queryset.filter(
                teacher__first_name__icontains=search
            ) | queryset.filter(
                staff_profile__first_name__icontains=search
            )
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset.distinct()


class EmployeeDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        return employee_queryset(self.request)


class EmployeeContractListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAccountantRole]
    serializer_class = EmploymentContractSerializer

    def get_queryset(self):
        return owned_queryset(EmploymentContract, self.request).order_by("-start_date")

    def perform_create(self, serializer):
        employee = get_object_or_404(employee_queryset(self.request), pk=self.kwargs["employee_id"])
        serializer.save(employee=employee)


class EmployeeDocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAccountantRole]
    serializer_class = EmployeeDocumentSerializer

    def get_queryset(self):
        return owned_queryset(EmployeeDocument, self.request).order_by("-created_at")

    def perform_create(self, serializer):
        employee = get_object_or_404(employee_queryset(self.request), pk=self.kwargs["employee_id"])
        serializer.save(employee=employee, uploaded_by=self.request.user)


class EmployeeWorkloadListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = WorkloadAssignmentSerializer

    def get_queryset(self):
        return owned_queryset(WorkloadAssignment, self.request).order_by("-created_at")

    def perform_create(self, serializer):
        employee = get_object_or_404(employee_queryset(self.request), pk=self.kwargs["employee_id"])
        serializer.save(employee=employee)


class EmployeeReviewListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = PerformanceReviewSerializer

    def get_queryset(self):
        return owned_queryset(PerformanceReview, self.request).order_by("-review_date")

    def perform_create(self, serializer):
        employee = get_object_or_404(employee_queryset(self.request), pk=self.kwargs["employee_id"])
        serializer.save(employee=employee, reviewer=self.request.user)


class EmploymentEventListView(generics.ListAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = EmploymentEventSerializer

    def get_queryset(self):
        return owned_queryset(EmploymentEvent, self.request).order_by("-effective_date")


class EmploymentEventCreateView(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request):
        employee = get_object_or_404(employee_queryset(request), pk=request.data.get("employee"))
        event_data = request.data.copy()
        event_data.pop("employee", None)
        serializer = EmploymentEventSerializer(data=event_data)
        serializer.is_valid(raise_exception=True)
        event_type = serializer.validated_data["event_type"]
        to_campus = serializer.validated_data.get("to_campus")
        if to_campus:
            assert_campus_allowed(request.user, to_campus.pk)
        old_status = employee.status
        old_campus = employee.primary_campus
        old_designation = employee.designation
        event = serializer.save(employee=employee, recorded_by=request.user, from_campus=old_campus, previous_designation=old_designation)
        updates = {"updated_at"}
        if to_campus:
            employee.primary_campus = to_campus
            updates.add("primary_campus")
        if event.new_designation:
            employee.designation = event.new_designation
            updates.add("designation")
        if event_type in ("resigned", "terminated"):
            employee.status = event_type
            updates.add("status")
        employee.save(update_fields=list(updates))
        return Response(EmploymentEventSerializer(event).data, status=201)
