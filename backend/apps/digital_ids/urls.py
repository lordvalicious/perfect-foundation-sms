from django.urls import path

from .views import (
    IdCardDetailView,
    IdCardListCreateView,
    IdCardPayloadView,
    IdCardRevokeView,
)

urlpatterns = [
    path("cards/", IdCardListCreateView.as_view(), name="digital-id-list"),
    path("cards/<int:pk>/", IdCardDetailView.as_view(), name="digital-id-detail"),
    path("cards/<int:pk>/revoke/", IdCardRevokeView.as_view(), name="digital-id-revoke"),
    path(
        "cards/<int:pk>/payload/",
        IdCardPayloadView.as_view(),
        name="digital-id-payload",
    ),
]