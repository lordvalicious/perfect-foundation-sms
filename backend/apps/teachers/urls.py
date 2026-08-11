from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie

from .views import (
    TeacherListCreateView,
    TeacherDetailView,
    TeacherMyView,
    TeacherAssignmentListCreateView,
    TeacherAssignmentDetailView,
)


@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"detail": "CSRF cookie set."})


urlpatterns = [
    path("csrf/", csrf_token, name="csrf-token"),
    path(
        "",
        TeacherListCreateView.as_view(),
        name="teacher-list",
    ),
    path(
        "me/",
        TeacherMyView.as_view(),
        name="teacher-my",
    ),
    path(
        "assignments/",
        TeacherAssignmentListCreateView.as_view(),
        name="teacher-assignment-list",
    ),
    path(
        "assignments/<int:pk>/",
        TeacherAssignmentDetailView.as_view(),
        name="teacher-assignment-detail",
    ),
    path(
        "<int:pk>/",
        TeacherDetailView.as_view(),
        name="teacher-detail",
    ),
]
