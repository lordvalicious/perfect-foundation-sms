from django.urls import path

from .views import (
    MyTicketCreateView,
    MyTicketDetailView,
    MyTicketsView,
    TicketAssignView,
    TicketCategoryListCreateView,
    TicketListCreateView,
    TicketMessageListCreateView,
    TicketReopenView,
    TicketResolveView,
    TicketRetrieveUpdateView,
)

urlpatterns = [
    path("categories/", TicketCategoryListCreateView.as_view(), name="ticket-category-list"),
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list"),
    path("tickets/<int:pk>/", TicketRetrieveUpdateView.as_view(), name="ticket-detail"),
    path("tickets/<int:pk>/assign/", TicketAssignView.as_view(), name="ticket-assign"),
    path("tickets/<int:pk>/resolve/", TicketResolveView.as_view(), name="ticket-resolve"),
    path("tickets/<int:pk>/reopen/", TicketReopenView.as_view(), name="ticket-reopen"),
    path("tickets/<int:pk>/messages/", TicketMessageListCreateView.as_view(), name="ticket-messages"),
    path("my/tickets/", MyTicketsView.as_view(), name="my-tickets"),
    path("my/tickets/create/", MyTicketCreateView.as_view(), name="my-ticket-create"),
    path("my/tickets/<int:pk>/", MyTicketDetailView.as_view(), name="my-ticket-detail"),
]