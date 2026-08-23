from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from apps.accounts.access import apply_campus_scope, assert_campus_allowed
from apps.accounts.permissions import IsAccountantRole

from .models import Driver, Route, TransportAssignment, Vehicle
from .serializers import (
    DriverSerializer,
    RouteSerializer,
    TransportAssignmentSerializer,
    VehicleSerializer,
)


def transport_queryset(queryset, request, campus_field="campus_id"):
    queryset = queryset.filter(
        Q(campus__school=request.institution)
        | Q(campus__isnull=True)
    )
    return apply_campus_scope(queryset, request, campus_field)


def validate_campus(request, campus):
    if campus is None:
        if not request.user.is_superuser:
            raise PermissionDenied("A campus is required for this record.")
        return
    if campus.school_id != request.institution.pk:
        raise PermissionDenied("The campus is outside the active institution.")
    assert_campus_allowed(request.user, campus.pk)


class VehicleListView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return transport_queryset(Vehicle.objects.all(), self.request)

    def perform_create(self, serializer):
        campus = serializer.validated_data.get("campus")
        validate_campus(self.request, campus)
        serializer.save()


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return transport_queryset(Vehicle.objects.all(), self.request)


class DriverListView(generics.ListCreateAPIView):
    serializer_class = DriverSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return transport_queryset(Driver.objects.all(), self.request)

    def perform_create(self, serializer):
        campus = serializer.validated_data.get("campus")
        validate_campus(self.request, campus)
        serializer.save()


class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DriverSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return transport_queryset(Driver.objects.all(), self.request)


class RouteListView(generics.ListCreateAPIView):
    serializer_class = RouteSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        return transport_queryset(
            Route.objects.all().prefetch_related("stops"),
            self.request,
        )

    def perform_create(self, serializer):
        campus = serializer.validated_data.get("campus")
        validate_campus(self.request, campus)
        serializer.save()


class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RouteSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return transport_queryset(Route.objects.all(), self.request)


class TransportAssignmentListView(generics.ListCreateAPIView):
    serializer_class = TransportAssignmentSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = TransportAssignment.objects.filter(
            Q(route__campus__school=self.request.institution)
            | Q(
                route__campus__isnull=True,
                student__enrollments__academic_year__school=self.request.institution,
            )
        ).select_related(
            "student",
            "route",
            "stop",
        ).distinct()
        queryset = apply_campus_scope(queryset, self.request, "route__campus_id")

        route = self.request.query_params.get("route")

        if route:
            queryset = queryset.filter(route_id=route)

        status_filter = self.request.query_params.get("status")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        route = serializer.validated_data["route"]
        if not transport_queryset(Route.objects.all(), self.request).filter(pk=route.pk).exists():
            raise PermissionDenied("The route is outside the active campus scope.")
        student = serializer.validated_data["student"]
        if not student.enrollments.filter(
            academic_year__school=self.request.institution,
        ).exists():
            raise PermissionDenied("The student is outside the active institution.")
        serializer.save()


class TransportAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransportAssignmentSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        queryset = TransportAssignment.objects.filter(
            Q(route__campus__school=self.request.institution)
            | Q(
                route__campus__isnull=True,
                student__enrollments__academic_year__school=self.request.institution,
            )
        )
        return apply_campus_scope(
            queryset.distinct(),
            self.request,
            "route__campus_id",
        )
