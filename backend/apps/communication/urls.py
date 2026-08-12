from django.urls import path

from .views import (
    AnnouncementDetailView,
    AnnouncementListView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
)


urlpatterns = [
    path(
        "announcements/",
        AnnouncementListView.as_view(),
        name="announcement-list",
    ),
    path(
        "announcements/<int:pk>/",
        AnnouncementDetailView.as_view(),
        name="announcement-detail",
    ),
    path(
        "notifications/",
        NotificationListView.as_view(),
        name="notification-list",
    ),
    path(
        "notifications/read-all/",
        NotificationMarkAllReadView.as_view(),
        name="notification-read-all",
    ),
    path(
        "notifications/<int:pk>/read/",
        NotificationMarkReadView.as_view(),
        name="notification-read",
    ),
]
