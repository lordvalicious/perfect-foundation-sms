from django.urls import path

from .views import (
    HealthRecordDetailView,
    HealthRecordListCreateView,
)

urlpatterns = [
    path(
        "records/",
        HealthRecordListCreateView.as_view(),
        name="health-record-list",
    ),
    path(
        "records/<int:pk>/",
        HealthRecordDetailView.as_view(),
        name="health-record-detail",
    ),
]
