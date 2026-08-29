from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, assert_campus_allowed, get_institution
from apps.accounts.permissions import IsStaffRole

from .models import IdCard
from .serializers import IdCardSerializer
from .services import default_expiry_date, next_card_number


class NoPaginationMixin:
    pagination_class = None


def _card_queryset():
    return IdCard.objects.select_related(
        "campus",
        "student",
        "teacher",
        "staff",
        "created_by",
    )


def _holder_from(serializer):
    """Return (holder, campus) for the requested holder_type."""
    holder_type = serializer.validated_data["holder_type"]
    if holder_type == "student":
        holder = serializer.validated_data["student"]
    elif holder_type == "teacher":
        holder = serializer.validated_data["teacher"]
    else:
        holder = serializer.validated_data["staff"]
    return holder, holder.primary_campus


def _revoke_previous(institution, validated):
    holder_type = validated["holder_type"]
    lookup = {"institution": institution, "holder_type": holder_type, "status": "active"}
    if holder_type == "student":
        lookup["student_id"] = validated["student"].pk
    elif holder_type == "teacher":
        lookup["teacher_id"] = validated["teacher"].pk
    else:
        lookup["staff_id"] = validated["staff"].pk
    IdCard.objects.filter(**lookup).update(status="revoked")


class IdCardListCreateView(NoPaginationMixin, generics.ListCreateAPIView):
    """List / issue digital ID cards."""

    permission_classes = [IsStaffRole]
    serializer_class = IdCardSerializer

    def get_queryset(self):
        qs = apply_campus_scope(_card_queryset(), self.request)

        params = self.request.query_params
        if params.get("holder_type"):
            qs = qs.filter(holder_type=params["holder_type"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("q"):
            qs = qs.filter(
                Q(card_number__icontains=params["q"])
                | Q(student__first_name__icontains=params["q"])
                | Q(student__last_name__icontains=params["q"])
                | Q(teacher__first_name__icontains=params["q"])
                | Q(teacher__last_name__icontains=params["q"])
                | Q(staff__first_name__icontains=params["q"])
                | Q(staff__last_name__icontains=params["q"])
            )
        return qs

    def perform_create(self, serializer):
        holder, campus = _holder_from(serializer)
        if campus is not None:
            assert_campus_allowed(self.request.user, campus.pk)

        institution = get_institution(self.request)
        _revoke_previous(institution, serializer.validated_data)

        card_number = next_card_number(institution)
        serializer.save(
            institution=institution,
            campus=campus,
            card_number=card_number,
            barcode_data=card_number,
            issue_date=timezone.localdate(),
            expiry_date=default_expiry_date(),
            created_by=self.request.user,
        )


class IdCardDetailView(NoPaginationMixin, generics.RetrieveUpdateDestroyAPIView):
    """View / update / delete a card record."""

    permission_classes = [IsStaffRole]
    serializer_class = IdCardSerializer

    def get_queryset(self):
        return apply_campus_scope(_card_queryset(), self.request)


class IdCardRevokeView(APIView):
    """Revoke a card (e.g. lost / replaced / departed)."""

    permission_classes = [IsStaffRole]

    def post(self, request, pk):
        card = get_object_or_404(
            apply_campus_scope(_card_queryset(), request),
            pk=pk,
        )
        if card.status != "active":
            raise ValidationError({"detail": "Card is not active."})

        card.status = "revoked"
        card.save(update_fields=["status", "updated_at"])
        return Response(IdCardSerializer(card, context={"request": request}).data)


class IdCardPayloadView(APIView):
    """Structured payload for printing / digital wallet display."""

    permission_classes = [IsStaffRole]

    def get(self, request, pk):
        card = get_object_or_404(
            apply_campus_scope(_card_queryset(), request),
            pk=pk,
        )
        return Response(
            {
                "id": card.pk,
                "card_number": card.card_number,
                "barcode_data": card.barcode_data or card.card_number,
                "holder_type": card.holder_type,
                "holder_name": card.holder_name,
                "holder_code": card.holder_code,
                "holder_photo": card.holder_photo,
                "student_class": card.student_class_label,
                "institution_name": card.institution.name,
                "campus_name": card.campus.name if card.campus else None,
                "issue_date": card.issue_date.isoformat(),
                "expiry_date": card.expiry_date.isoformat(),
                "status": card.status,
            }
        )