from django.urls import path

from .views import (
    dashboard_overview,
    dashboard_attendance,
    dashboard_finance,
    dashboard_exams,
)

urlpatterns = [
    path("overview/", dashboard_overview, name="dashboard-overview"),
    path("attendance/", dashboard_attendance, name="dashboard-attendance"),
    path("finance/", dashboard_finance, name="dashboard-finance"),
    path("exams/", dashboard_exams, name="dashboard-exams"),
]
