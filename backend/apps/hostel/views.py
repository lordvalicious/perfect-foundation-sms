from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, get_institution
from apps.accounts.permissions import IsStaffRole

from .models import Allocation, Hostel, Room
from .serializers import (
    AllocationSerializer,
    HostelSerializer,
    RoomSerializer,
)


class NoPaginationMixin:
    pagination_class = None


class HostelListCreateView(generics.ListCreateAPIView):
    serializer_class = HostelSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = Hostel.objects.select_related("campus")

        return apply_campus_scope(queryset, self.request)


class HostelRoomSelectorView(NoPaginationMixin, generics.ListAPIView):
    """School-wide hostel selector consumed by the Add Room form.

    Room management is a school-wide staff function: an authorized user may
    create Rooms in any hostel of their institution. This endpoint returns
    every hostel in the active institution regardless of campus so the Add
    Room dropdown exposes exactly what Room creation authorizes — never a
    hostel of another school.

    The general ``/api/hostel/hostels/`` list stays campus-scoped for the
    Hostel management table; this endpoint is intentionally separate.
    """

    serializer_class = HostelSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        institution = get_institution(self.request)

        if institution is None:
            return Hostel.objects.none()

        return (
            Hostel.objects.select_related("campus")
            .filter(campus__school=institution)
            .order_by("name")
        )


class HostelDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HostelSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        return apply_campus_scope(
            Hostel.objects.select_related("campus"),
            self.request,
        )


class RoomListCreateView(generics.ListCreateAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        institution = get_institution(self.request)
        queryset = Room.objects.select_related("hostel")

        if institution is not None:
            # Room management is institution-scoped; never expose rooms
            # belonging to another school.
            queryset = queryset.filter(hostel__campus__school=institution)

        hostel = self.request.query_params.get("hostel")

        if hostel:
            queryset = queryset.filter(hostel_id=hostel)

        return queryset

    def perform_create(self, serializer):
        hostel = serializer.validated_data.get("hostel")
        institution = get_institution(self.request)

        if (
            hostel is None
            or institution is None
            or hostel.campus.school_id != institution.id
        ):
            raise serializers.ValidationError(
                {"hostel": "Selected hostel does not belong to your school."}
            )

        serializer.save()


class AllocationListCreateView(generics.ListCreateAPIView):
    serializer_class = AllocationSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = Allocation.objects.select_related(
            "student",
            "room",
            "room__hostel",
        )

        room = self.request.query_params.get("room")

        if room:
            queryset = queryset.filter(room_id=room)

        allocation_status = self.request.query_params.get("status")

        if allocation_status:
            queryset = queryset.filter(status=allocation_status)

        return queryset


class VacateAllocationView(APIView):
    """POST /hostel/allocations/<pk>/vacate/"""

    permission_classes = [IsStaffRole]

    def post(self, request, pk):
        from django.utils import timezone

        allocation = get_object_or_404(Allocation, pk=pk)
        allocation.status = "vacated"
        allocation.end_date = timezone.localdate()
        allocation.save()

        return Response(
            AllocationSerializer(allocation).data,
            status=status.HTTP_200_OK,
        )
