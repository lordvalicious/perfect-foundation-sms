from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import (
    apply_campus_scope,
    assert_campus_allowed,
    get_institution,
    institution_scope,
    user_allowed_campus_ids,
)
from apps.accounts.permissions import IsAcademicMemberRole, IsStaffRole

from .models import SupportTicket, TicketCategory, TicketMessage
from .serializers import (
    MyTicketSerializer,
    SupportTicketSerializer,
    TicketCategorySerializer,
    TicketMessageSerializer,
)


def _ticket_queryset():
    return SupportTicket.objects.select_related(
        "campus",
        "category",
        "created_by",
        "assignee",
    ).prefetch_related("messages")


def _default_campus(user):
    """Best-guess default campus when a reporter does not pick one."""
    campus_ids = user_allowed_campus_ids(user)
    return next(iter(campus_ids), None)


class TicketCategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = TicketCategorySerializer
    permission_classes = [IsStaffRole]
    pagination_class = None

    def get_queryset(self):
        return institution_scope(
            TicketCategory.objects.all(),
            self.request,
        )


class TicketListCreateView(generics.ListCreateAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsStaffRole]
    pagination_class = None

    def get_queryset(self):
        queryset = _ticket_queryset()
        params = self.request.query_params

        if params.get("status"):
            queryset = queryset.filter(status=params.get("status"))
        if params.get("priority"):
            queryset = queryset.filter(priority=params.get("priority"))
        if params.get("category"):
            queryset = queryset.filter(category_id=params.get("category"))
        if params.get("assigned") == "me":
            queryset = queryset.filter(assignee=self.request.user)
        if params.get("mine") == "true":
            queryset = queryset.filter(created_by=self.request.user)
        if params.get("search"):
            term = params.get("search")
            queryset = queryset.filter(
                subject__icontains=term
            ) | queryset.filter(description__icontains=term)

        return apply_campus_scope(queryset, self.request)

    def perform_create(self, serializer):
        data = self.request.data
        campus_id = data.get("campus") or _default_campus(
            self.request.user
        )

        if campus_id:
            assert_campus_allowed(self.request.user, campus_id)

        serializer.save(
            institution=get_institution(self.request)
            or (
                serializer.validated_data.get("campus").school
                if serializer.validated_data.get("campus")
                else None
            ),
            campus_id=campus_id,
            created_by=self.request.user,
        )


class TicketRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        return apply_campus_scope(_ticket_queryset(), self.request)


class TicketAssignView(APIView):
    permission_classes = [IsStaffRole]

    def post(self, request, pk):
        ticket = apply_campus_scope(
            _ticket_queryset(), request
        ).filter(pk=pk).first()

        if ticket is None:
            return Response(
                {"detail": "Ticket not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        assignee_id = request.data.get("assignee")
        if not assignee_id:
            return Response(
                {"detail": "Assignee required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.accounts.models import User

        assignee = User.objects.filter(
            pk=assignee_id,
            memberships__institution=request.institution,
            memberships__role_assignments__role__in=IsStaffRole.roles,
            memberships__status="active",
        ).distinct().first()

        if assignee is None:
            return Response(
                {"detail": "Assignee not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        ticket.assignee = assignee
        if ticket.status == "open":
            ticket.status = "in_progress"
        ticket.save(update_fields=["assignee", "status", "updated_at"])

        return Response(SupportTicketSerializer(ticket, context={"request": request}).data)


class TicketResolveView(APIView):
    permission_classes = [IsStaffRole]

    def post(self, request, pk):
        ticket = apply_campus_scope(_ticket_queryset(), request).filter(pk=pk).first()
        if ticket is None:
            return Response({"detail": "Ticket not found."}, status=404)

        resolution_notes = request.data.get("resolution_notes", "").strip()
        updates = {"status": "resolved", "resolved_at": timezone.now()}
        if resolution_notes:
            updates["resolution_notes"] = resolution_notes

        for field, value in updates.items():
            setattr(ticket, field, value)
        ticket.save()

        return Response(SupportTicketSerializer(ticket, context={"request": request}).data)


class TicketReopenView(APIView):
    permission_classes = [IsStaffRole]

    def post(self, request, pk):
        ticket = apply_campus_scope(_ticket_queryset(), request).filter(pk=pk).first()
        if ticket is None:
            return Response({"detail": "Ticket not found."}, status=404)

        ticket.status = "open"
        ticket.resolved_at = None
        ticket.save(update_fields=["status", "resolved_at", "updated_at"])

        return Response(SupportTicketSerializer(ticket, context={"request": request}).data)


class TicketMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = TicketMessageSerializer
    permission_classes = [IsStaffRole]
    pagination_class = None

    def get_queryset(self):
        return TicketMessage.objects.filter(
            ticket=apply_campus_scope(
                SupportTicket.objects.filter(pk=self.kwargs.get("pk")),
                self.request,
            )
        ).select_related("author")

    def perform_create(self, serializer):
        ticket = apply_campus_scope(
            SupportTicket.objects.filter(pk=self.kwargs.get("pk")),
            self.request,
        ).first()

        if ticket is None:
            raise NotFound("Ticket not found.")

        if ticket.status == "open":
            ticket.status = "in_progress"
            ticket.save(update_fields=["status", "updated_at"])

        serializer.save(
            ticket=ticket,
            author=self.request.user,
        )


class MyTicketCreateView(generics.CreateAPIView):
    """Self-service: staff, teachers, students and parents raise a ticket."""

    serializer_class = SupportTicketSerializer
    permission_classes = [IsAcademicMemberRole]

    def perform_create(self, serializer):
        serializer.save(
            institution=get_institution(self.request),
            campus_id=_default_campus(self.request.user),
            created_by=self.request.user,
            assignee=None,
        )


class MyTicketsView(generics.ListAPIView):
    serializer_class = MyTicketSerializer
    permission_classes = [IsAcademicMemberRole]
    pagination_class = None

    def get_queryset(self):
        queryset = _ticket_queryset().filter(
            created_by=self.request.user
        )
        if self.request.query_params.get("status"):
            queryset = queryset.filter(
                status=self.request.query_params.get("status")
            )
        return queryset


class MyTicketDetailView(generics.RetrieveAPIView):
    serializer_class = MyTicketSerializer
    permission_classes = [IsAcademicMemberRole]

    def get_queryset(self):
        return _ticket_queryset().filter(created_by=self.request.user)