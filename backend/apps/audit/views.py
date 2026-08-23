import csv
import json

from django.db.models import Q
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole

from .models import AuditLog, ACTION_CHOICES
from .serializers import AuditLogSerializer


class AuditLogPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminRole]
    pagination_class = AuditLogPagination

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("user").all()

        action = self.request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action)

        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        model = self.request.query_params.get("model")
        if model:
            queryset = queryset.filter(model_name=model)

        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(object_repr__icontains=search)
                | Q(model_name__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(user__username__icontains=search)
            )

        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)

        object_id = self.request.query_params.get("object_id")
        if object_id:
            queryset = queryset.filter(object_id=object_id)

        return queryset

    def list(self, request, *args, **kwargs):
        fmt = request.query_params.get("format")

        if fmt == "csv":
            queryset = self.filter_queryset(self.get_queryset())[:5000]

            response = HttpResponse(content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'
            response.write("\ufeff")
            writer = csv.writer(response)
            writer.writerow([
                "Timestamp", "User", "Action", "Model", "Object",
                "Object ID", "IP Address", "Details",
            ])
            for log in queryset:
                writer.writerow([
                    log.timestamp.isoformat(),
                    str(log.user) if log.user else "Anonymous",
                    log.get_action_display(),
                    log.model_name,
                    log.object_repr,
                    log.object_id,
                    log.ip_address or "",
                    json.dumps(log.details, default=str) if log.details else "",
                ])
            return response

        return super().list(request, *args, **kwargs)


class AuditLogActionChoicesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        return Response([
            {"value": value, "label": label}
            for value, label in ACTION_CHOICES
        ])
