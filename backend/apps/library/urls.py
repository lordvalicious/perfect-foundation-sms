from django.urls import path

from .views import (
    BookCopyDetailView,
    BookCopyListCreateView,
    BookDetailView,
    BookIssueDetailView,
    BookIssueListView,
    BookListView,
    BookReservationCancelView,
    BookReservationDetailView,
    BookReservationFulfillView,
    BookReservationListCreateView,
    BookReturnView,
)


urlpatterns = [
    path("books/", BookListView.as_view(), name="book-list"),
    path("books/<int:pk>/", BookDetailView.as_view(), name="book-detail"),
    path("books/<int:book_pk>/copies/", BookCopyListCreateView.as_view(), name="book-copy-list"),
    path("books/<int:book_pk>/copies/<int:pk>/", BookCopyDetailView.as_view(), name="book-copy-detail"),
    path("issues/", BookIssueListView.as_view(), name="book-issue-list"),
    path(
        "issues/<int:pk>/",
        BookIssueDetailView.as_view(),
        name="book-issue-detail",
    ),
    path(
        "issues/<int:pk>/return/",
        BookReturnView.as_view(),
        name="book-return",
    ),
    path("reservations/", BookReservationListCreateView.as_view(), name="book-reservation-list"),
    path("reservations/<int:pk>/", BookReservationDetailView.as_view(), name="book-reservation-detail"),
    path("reservations/<int:pk>/fulfill/", BookReservationFulfillView.as_view(), name="book-reservation-fulfill"),
    path("reservations/<int:pk>/cancel/", BookReservationCancelView.as_view(), name="book-reservation-cancel"),
]
