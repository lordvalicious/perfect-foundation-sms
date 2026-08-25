from django.urls import path

from .views import (
    AllocationListCreateView,
    HostelDetailView,
    HostelListCreateView,
    RoomListCreateView,
    VacateAllocationView,
)

urlpatterns = [
    path("hostels/", HostelListCreateView.as_view(), name="hostel-list"),
    path(
        "hostels/<int:pk>/",
        HostelDetailView.as_view(),
        name="hostel-detail",
    ),
    path("rooms/", RoomListCreateView.as_view(), name="room-list"),
    path(
        "allocations/",
        AllocationListCreateView.as_view(),
        name="allocation-list",
    ),
    path(
        "allocations/<int:pk>/vacate/",
        VacateAllocationView.as_view(),
        name="allocation-vacate",
    ),
]
