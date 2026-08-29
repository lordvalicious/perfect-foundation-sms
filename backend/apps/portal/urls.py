from django.urls import path

from .views import parent_portal, student_portal, teacher_portal

urlpatterns = [
    path("teacher/", teacher_portal, name="portal-teacher"),
    path("student/", student_portal, name="portal-student"),
    path("parent/", parent_portal, name="portal-parent"),
]