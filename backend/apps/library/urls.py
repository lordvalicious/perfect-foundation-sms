from django.urls import path

from .views import (
    BookDetailView,
    BookIssueDetailView,
    BookIssueListView,
    BookListView,
    BookReturnView,
)


urlpatterns = [
    path("books/", BookListView.as_view(), name="book-list"),
    path("books/<int:pk>/", BookDetailView.as_view(), name="book-detail"),
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
]
