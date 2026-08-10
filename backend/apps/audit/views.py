from rest_framework import generics

from apps.accounts.permissions import IsAdminRole

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminRole]
    pagination_class = None

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

        return queryset[:200]
