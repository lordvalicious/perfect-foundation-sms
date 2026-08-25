from django.urls import path

from .views import AlumniDetailView, AlumniListCreateView

urlpatterns = [
    path(
        "",
        AlumniListCreateView.as_view(),
        name="alumni-list",
    ),
    path(
        "<int:pk>/",
        AlumniDetailView.as_view(),
        name="alumni-detail",
    ),
]
