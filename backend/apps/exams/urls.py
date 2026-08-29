from django.urls import path

from .gradebook import ClassGradebookView
from .views import (
    ExamListView,
    ExamScheduleDetailView,
    ExamScheduleListView,
    ExamSubjectListView,
    PracticalResultDetailView,
    PracticalResultListCreateView,
    StudentResultDetailView,
    StudentResultListView,
)


urlpatterns = [
    path("", ExamListView.as_view(), name="exam-list"),
    path("subjects/", ExamSubjectListView.as_view(), name="exam-subject-list"),
    path("schedules/", ExamScheduleListView.as_view(), name="exam-schedule-list"),
    path(
        "schedules/<int:pk>/",
        ExamScheduleDetailView.as_view(),
        name="exam-schedule-detail",
    ),
    path("results/", StudentResultListView.as_view(), name="student-result-list"),
    path(
        "results/<int:pk>/",
        StudentResultDetailView.as_view(),
        name="student-result-detail",
    ),
    path(
        "practical/",
        PracticalResultListCreateView.as_view(),
        name="practical-result-list",
    ),
    path(
        "practical/<int:pk>/",
        PracticalResultDetailView.as_view(),
        name="practical-result-detail",
    ),
    path(
        "gradebook/",
        ClassGradebookView.as_view(),
        name="class-gradebook",
    ),
]
