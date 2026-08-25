from django.urls import path

from .views import (
    CourseDetailView,
    CourseListCreateView,
    LessonListCreateView,
    MarkLessonCompleteView,
    MyProgressView,
)

urlpatterns = [
    path(
        "courses/",
        CourseListCreateView.as_view(),
        name="course-list",
    ),
    path(
        "courses/<int:pk>/",
        CourseDetailView.as_view(),
        name="course-detail",
    ),
    path(
        "courses/<int:course_id>/lessons/",
        LessonListCreateView.as_view(),
        name="lesson-list",
    ),
    path(
        "lessons/<int:lesson_id>/complete/",
        MarkLessonCompleteView.as_view(),
        name="lesson-complete",
    ),
    path(
        "my-progress/",
        MyProgressView.as_view(),
        name="my-progress",
    ),
]
