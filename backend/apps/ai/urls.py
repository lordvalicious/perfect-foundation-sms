from django.urls import path

from . import views


urlpatterns = [
    path("overview/", views.AiOverviewView.as_view(), name="ai-overview"),
    path("ask/", views.AiAskView.as_view(), name="ai-ask"),
    path("search/", views.AiSearchView.as_view(), name="ai-search"),
    path(
        "insights/students/",
        views.AiStudentInsightsView.as_view(),
        name="ai-insights-students",
    ),
    path(
        "insights/attendance/",
        views.AiAttendanceInsightsView.as_view(),
        name="ai-insights-attendance",
    ),
    path(
        "insights/academic/",
        views.AiAcademicInsightsView.as_view(),
        name="ai-insights-academic",
    ),
    path(
        "insights/finance/",
        views.AiFinanceInsightsView.as_view(),
        name="ai-insights-finance",
    ),
    path("anomalies/", views.AiAnomaliesView.as_view(), name="ai-anomalies"),
    path(
        "communication/draft/",
        views.AiCommunicationDraftView.as_view(),
        name="ai-communication-draft",
    ),
]