from django.urls import path

from .views import (
    GradeSubmissionView,
    HomeworkDetailView,
    HomeworkListCreateView,
    SubmissionListCreateView,
)

urlpatterns = [
    path(
        "",
        HomeworkListCreateView.as_view(),
        name="homework-list",
    ),
    path(
        "<int:pk>/",
        HomeworkDetailView.as_view(),
        name="homework-detail",
    ),
    path(
        "<int:homework_id>/submissions/",
        SubmissionListCreateView.as_view(),
        name="submission-list",
    ),
    path(
        "submissions/<int:pk>/grade/",
        GradeSubmissionView.as_view(),
        name="submission-grade",
    ),
]
