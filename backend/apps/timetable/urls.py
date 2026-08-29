from django.urls import path

from .generate_views import TimetableGenerateView
from .views import (
    PeriodListView,
    TimetableConflictsView,
    TimetableEntryListView,
)


urlpatterns = [
    path("periods/", PeriodListView.as_view(), name="period-list"),
    path("entries/", TimetableEntryListView.as_view(), name="timetable-entry-list"),
    path("conflicts/", TimetableConflictsView.as_view(), name="timetable-conflicts"),
    path(
        "generate/",
        TimetableGenerateView.as_view(),
        name="timetable-generate",
    ),
]
