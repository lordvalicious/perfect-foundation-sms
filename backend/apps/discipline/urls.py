from django.urls import path

from .views import (
    DisciplineSummaryView,
    IncidentActionListCreateView,
    IncidentDetailView,
    IncidentListCreateView,
)

urlpatterns = [
    path(
        "incidents/",
        IncidentListCreateView.as_view(),
        name="incident-list",
    ),
    path(
        "incidents/<int:pk>/",
        IncidentDetailView.as_view(),
        name="incident-detail",
    ),
    path(
        "incidents/<int:incident_id>/actions/",
        IncidentActionListCreateView.as_view(),
        name="incident-action-list",
    ),
    path(
        "summary/",
        DisciplineSummaryView.as_view(),
        name="discipline-summary",
    ),
]
