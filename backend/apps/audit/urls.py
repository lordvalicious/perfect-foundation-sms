from django.urls import path

from .views import AuditLogActionChoicesView, AuditLogListView

urlpatterns = [
    path("", AuditLogListView.as_view(), name="audit-log-list"),
    path("actions/", AuditLogActionChoicesView.as_view(), name="audit-log-actions"),
]
