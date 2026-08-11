from django.urls import path

from .views import (
    StaffDetailView,
    StaffListCreateView,
    StaffMyView,
)


urlpatterns = [
    path(
        "",
        StaffListCreateView.as_view(),
        name="staff-list",
    ),
    path(
        "me/",
        StaffMyView.as_view(),
        name="staff-my",
    ),
    path(
        "<int:pk>/",
        StaffDetailView.as_view(),
        name="staff-detail",
    ),
]
