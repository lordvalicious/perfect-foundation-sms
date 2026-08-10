from django.urls import path

from .views import (
    GradeAmendmentListCreateView,
    GradeScaleListView,
    ReportCardDetailView,
    ReportCardListView,
    ReportCardStatusView,
)


urlpatterns = [
    path("", ReportCardListView.as_view(), name="report-card-list"),
    path(
        "<int:pk>/",
        ReportCardDetailView.as_view(),
        name="report-card-detail",
    ),
    path(
        "<int:pk>/status/",
        ReportCardStatusView.as_view(),
        name="report-card-status",
    ),
    path(
        "grade-scales/",
        GradeScaleListView.as_view(),
        name="grade-scale-list",
    ),
    path(
        "amendments/",
        GradeAmendmentListCreateView.as_view(),
        name="grade-amendment-list",
    ),
]
