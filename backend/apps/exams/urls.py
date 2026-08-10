from django.urls import path

from .views import (
    ExamListView,
    ExamSubjectListView,
    StudentResultListView,
)


urlpatterns = [
    path("", ExamListView.as_view(), name="exam-list"),
    path("subjects/", ExamSubjectListView.as_view(), name="exam-subject-list"),
    path("results/", StudentResultListView.as_view(), name="student-result-list"),
]
