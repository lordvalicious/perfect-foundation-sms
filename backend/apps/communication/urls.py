from django.urls import path

from .views import (
    AnnouncementDetailView,
    AnnouncementListView,
    MessageDetailView,
    MessageListView,
    MessageRecipientsView,
    MessageThreadView,
    MessageUnreadCountView,
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
    path(
        "messages/",
        MessageListView.as_view(),
        name="message-list",
    ),
    path(
        "messages/recipients/",
        MessageRecipientsView.as_view(),
        name="message-recipients",
    ),
    path(
        "messages/unread-count/",
        MessageUnreadCountView.as_view(),
        name="message-unread-count",
    ),
    path(
        "messages/<int:pk>/",
        MessageDetailView.as_view(),
        name="message-detail",
    ),
    path(
        "messages/<int:pk>/thread/",
        MessageThreadView.as_view(),
        name="message-thread",
    ),
]
