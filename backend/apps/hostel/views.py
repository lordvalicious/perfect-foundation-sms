from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsStaffRole

from .models import Allocation, Hostel, Room
from .serializers import (
    AllocationSerializer,
    HostelSerializer,
    RoomSerializer,
)


class HostelListCreateView(generics.ListCreateAPIView):
    serializer_class = HostelSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = Hostel.objects.select_related("campus")

        return apply_campus_scope(queryset, self.request)


class HostelDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HostelSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        return Hostel.objects.select_related("campus")


class RoomListCreateView(generics.ListCreateAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = Room.objects.select_related("hostel")

        hostel = self.request.query_params.get("hostel")

        if hostel:
            queryset = queryset.filter(hostel_id=hostel)

        return queryset


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
