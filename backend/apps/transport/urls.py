from django.urls import path

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
]
