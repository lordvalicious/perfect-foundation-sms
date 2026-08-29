from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, assert_campus_allowed
from apps.accounts.permissions import IsStaffRole

from .models import Visitor
from .serializers import VisitorSerializer
from .services import next_badge_number


class NoPaginationMixin:
    pagination_class = None


def _visitor_queryset():
    return Visitor.objects.select_related("campus", "created_by")


class VisitorListCreateView(NoPaginationMixin, generics.ListCreateAPIView):
    """Gate log: list visitors and register a check-in."""

    permission_classes = [IsStaffRole]
    serializer_class = VisitorSerializer

    def get_queryset(self):
        qs = apply_campus_scope(_visitor_queryset(), self.request)

        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("from"):
            start = parse_date(params["from"])
            if start:
                qs = qs.filter(check_in__date__gte=start)
        if params.get("to"):
            end = parse_date(params["to"])
            if end:
                qs = qs.filter(check_in__date__lte=end)
        if params.get("q"):
            qs = qs.filter(
                Q(full_name__icontains=params["q"])
                | Q(phone__icontains=params["q"])
                | Q(meeting_party__icontains=params["q"])
            )
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        campus = serializer.validated_data["campus"]
        assert_campus_allowed(user, campus.pk)

        serializer.save(
            institution=campus.school,
            campus=campus,
            badge_number=next_badge_number(campus.school),
            check_in=timezone.now(),
            status="checked_in",
            created_by=user,
        )


class VisitorDetailView(NoPaginationMixin, generics.RetrieveUpdateDestroyAPIView):
    """View / correct / remove a visitor log entry."""

    permission_classes = [IsStaffRole]
    serializer_class = VisitorSerializer

    def get_queryset(self):
        return apply_campus_scope(_visitor_queryset(), self.request)


class VisitorCheckOutView(APIView):
    """Check a currently-checked-in visitor out of the building."""

    permission_classes = [IsStaffRole]

    def post(self, request, pk):
        visitor = get_object_or_404(
            apply_campus_scope(_visitor_queryset(), request),
            pk=pk,
        )
        if visitor.status != "checked_in":
            raise ValidationError({"detail": "Visitor is already checked out."})

        visitor.status = "checked_out"
        visitor.check_out = timezone.now()
        visitor.save(update_fields=["status", "check_out", "updated_at"])

        return Response(VisitorSerializer(visitor, context={"request": request}).data)


class VisitorStatsView(APIView):
    """Gate summary: currently inside, today's footfall."""

    permission_classes = [IsStaffRole]

    def get(self, request):
        qs = apply_campus_scope(_visitor_queryset(), request)
        today = timezone.localdate()

        active = qs.filter(status="checked_in")
        active_by_campus = list(
            active.values("campus_id", "campus__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return Response(
            {
                "checked_in_now": active.count(),
                "today": qs.filter(check_in__date=today).count(),
                "active_by_campus": active_by_campus,
            }
        )