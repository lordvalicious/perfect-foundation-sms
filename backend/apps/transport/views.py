from rest_framework import generics

from apps.accounts.permissions import IsAccountantRole

from .models import Driver, Route, TransportAssignment, Vehicle
from .serializers import (
    DriverSerializer,
    RouteSerializer,
    TransportAssignmentSerializer,
    VehicleSerializer,
)


class VehicleListView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAccountantRole]
    queryset = Vehicle.objects.all()


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAccountantRole]
    queryset = Vehicle.objects.all()


class DriverListView(generics.ListCreateAPIView):
    serializer_class = DriverSerializer
    permission_classes = [IsAccountantRole]
    queryset = Driver.objects.all()


class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DriverSerializer
    permission_classes = [IsAccountantRole]
    queryset = Driver.objects.all()


class RouteListView(generics.ListCreateAPIView):
    serializer_class = RouteSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        return Route.objects.all().prefetch_related("stops")


class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RouteSerializer
    permission_classes = [IsAccountantRole]
    queryset = Route.objects.all()


class TransportAssignmentListView(generics.ListCreateAPIView):
    serializer_class = TransportAssignmentSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = TransportAssignment.objects.select_related(
            "student",
            "route",
            "stop",
        )

        route = self.request.query_params.get("route")

        if route:
            queryset = queryset.filter(route_id=route)

        status_filter = self.request.query_params.get("status")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


class TransportAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransportAssignmentSerializer
    permission_classes = [IsAccountantRole]
    queryset = TransportAssignment.objects.all()
