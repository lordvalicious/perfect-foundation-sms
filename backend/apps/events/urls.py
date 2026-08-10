from django.urls import path

from .views import (
    EventDetailView,
    EventListCreateView,
    EventRSVPView,
)

urlpatterns = [
    path("", EventListCreateView.as_view(), name="event-list"),
    path(
        "<int:pk>/",
        EventDetailView.as_view(),
        name="event-detail",
    ),
    path(
        "<int:pk>/rsvp/",
        EventRSVPView.as_view(),
        name="event-rsvp",
    ),
]
