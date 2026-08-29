from django.urls import path

from .views import (
    VisitorCheckOutView,
    VisitorDetailView,
    VisitorListCreateView,
    VisitorStatsView,
)

urlpatterns = [
    path("visitors/", VisitorListCreateView.as_view(), name="visitor-list"),
    path("visitors/<int:pk>/", VisitorDetailView.as_view(), name="visitor-detail"),
    path(
        "visitors/<int:pk>/checkout/",
        VisitorCheckOutView.as_view(),
        name="visitor-checkout",
    ),
    path("visitors/stats/", VisitorStatsView.as_view(), name="visitor-stats"),
]