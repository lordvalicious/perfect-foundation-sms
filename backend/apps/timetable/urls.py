from django.urls import path

from .views import (
    PeriodListView,
    TimetableEntryListView,
)


urlpatterns = [
    path("periods/", PeriodListView.as_view(), name="period-list"),
    path("entries/", TimetableEntryListView.as_view(), name="timetable-entry-list"),
]
