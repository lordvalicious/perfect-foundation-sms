from django.urls import path

from .views import AuditLogActionChoicesView, AuditLogListView, CSPViolationReportView

urlpatterns = [
    path("", AuditLogListView.as_view(), name="audit-log-list"),
    path("actions/", AuditLogActionChoicesView.as_view(), name="audit-log-actions"),
    path("csp-report/", CSPViolationReportView.as_view(), name="csp-report"),
]
