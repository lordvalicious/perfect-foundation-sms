from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAccountantRole
from apps.accounts.scopes import (
    get_guardian_profile,
    get_teacher_profile,
    is_manager,
    is_parent,
    is_student,
    is_teacher,
    parent_student_class_ids,
    student_class_ids,
    teacher_class_ids,
)
from apps.audit.models import record_audit

from .models import Announcement, Notification
from .serializers import (
    AnnouncementSerializer,
    NotificationSerializer,
)


class AnnouncementListView(generics.ListAPIView):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = Announcement.objects.select_related(
            "campus",
            "class_obj",
            "section",
        )

        user = self.request.user

        if not is_manager(user):
            queryset = queryset.filter(status="published")

            q = Q()

            if is_teacher(user):
                class_ids = teacher_class_ids(user)

                if class_ids:
                    q |= Q(class_obj_id__in=class_ids)

                q |= Q(class_obj__isnull=True)
            elif is_parent(user):
                class_ids = parent_student_class_ids(user)

                if class_ids:
                    q |= Q(class_obj_id__in=class_ids)

                q |= Q(class_obj__isnull=True)
            elif is_student(user):
                class_ids = student_class_ids(user)

                if class_ids:
                    q |= Q(class_obj_id__in=class_ids)

                q |= Q(class_obj__isnull=True)
            else:
                q = Q()

            queryset = queryset.filter(q)

        status_filter = self.request.query_params.get("status")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(category=category)

        return queryset


class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        return Announcement.objects.all()

    def perform_update(self, serializer):
        instance = serializer.save()

        record_audit(
            request=self.request,
            action="update",
            model_name="Announcement",
            object_id=str(instance.pk),
            object_repr=str(instance),
            details={"status": instance.status},
        )

    def perform_destroy(self, instance):
        record_audit(
            request=self.request,
            action="delete",
            model_name="Announcement",
            object_id=str(instance.pk),
            object_repr=str(instance),
        )
        instance.delete()


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        queryset = Notification.objects.filter(
            recipient=self.request.user
        )

        unread_only = self.request.query_params.get("unread_only")

        if unread_only in ("1", "true", "True"):
            queryset = queryset.filter(is_read=False)

        return queryset[:50]


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = (
            Notification.objects
            .filter(pk=pk, recipient=request.user)
            .first()
        )

        if notification is None:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.is_read = True
        notification.save(update_fields=["is_read"])

        return Response(
            {"detail": "Notification marked as read."}
        )


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = (
            Notification.objects
            .filter(recipient=request.user, is_read=False)
            .update(is_read=True)
        )

        return Response(
            {"detail": f"{count} notifications marked as read."}
        )
