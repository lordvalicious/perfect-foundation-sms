from django.urls import path

from .device_views import GpsLiveView, GpsPingView
from .views import (
    DriverDetailView,
    DriverListView,
    RouteDetailView,
    RouteListView,
    TransportAssignmentDetailView,
    TransportAssignmentListView,
    VehicleDetailView,
    VehicleListView,
)


urlpatterns = [
    path("vehicles/", VehicleListView.as_view(), name="vehicle-list"),
    path(
        "vehicles/<int:pk>/",
        VehicleDetailView.as_view(),
        name="vehicle-detail",
    ),
    path("drivers/", DriverListView.as_view(), name="driver-list"),
    path(
        "drivers/<int:pk>/",
        DriverDetailView.as_view(),
        name="driver-detail",
    ),
    path("routes/", RouteListView.as_view(), name="route-list"),
    path(
        "routes/<int:pk>/",
        RouteDetailView.as_view(),
        name="route-detail",
    ),
    path(
        "assignments/",
        TransportAssignmentListView.as_view(),
        name="transport-assignment-list",
    ),
    path(
        "assignments/<int:pk>/",
        TransportAssignmentDetailView.as_view(),
        name="transport-assignment-detail",
    ),
    path(
        "gps/ping/",
        GpsPingView.as_view(),
        name="gps-ping",
    ),
    path(
        "gps/live/",
        GpsLiveView.as_view(),
        name="gps-live",
    ),
]
