from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, get_institution
from apps.accounts.permissions import IsStaffRole
from apps.students.models import Student

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

        if institution is None:
            # Active-school failure policy: without a valid active school we
            # fail closed. Never list rooms across schools (which would leak
            # every institution's data to a user with no tenant context).
            return Room.objects.none()

        queryset = Room.objects.select_related("hostel")
        # Room management is institution-scoped; never expose rooms belonging
        # to another school.
        queryset = queryset.filter(hostel__campus__school=institution)

        hostel = self.request.query_params.get("hostel")

        if hostel:
            queryset = queryset.filter(hostel_id=hostel)

        return queryset

    def perform_create(self, serializer):
        hostel = serializer.validated_data.get("hostel")
        institution = get_institution(self.request)

        if institution is None:
            raise serializers.ValidationError(
                {"institution": "Select a school before adding a room."}
            )

        if (
            hostel is None
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
        institution = get_institution(self.request)

        if institution is None:
            # Active-school failure policy: fail closed — never return
            # allocations from all schools when the active school is missing.
            return Allocation.objects.none()

        queryset = Allocation.objects.select_related(
            "student",
            "room",
            "room__hostel",
        ).filter(room__hostel__campus__school=institution)

        room = self.request.query_params.get("room")

        if room:
            queryset = queryset.filter(room_id=room)

        allocation_status = self.request.query_params.get("status")

        if allocation_status:
            queryset = queryset.filter(status=allocation_status)

        return queryset

    def perform_create(self, serializer):
        institution = get_institution(self.request)

        if institution is None:
            raise serializers.ValidationError(
                {
                    "institution": (
                        "Select a school before allocating a student "
                        "to a room."
                    )
                }
            )

        room = serializer.validated_data.get("room")

        if (
            room is None
            or room.hostel.campus.school_id != institution.id
        ):
            raise serializers.ValidationError(
                {"room": "Selected room does not belong to your school."}
            )

        student = serializer.validated_data.get("student")

        if (
            student is None
            or student.institution_id != institution.id
        ):
            raise serializers.ValidationError(
                {"student": "Selected student does not belong to your school."}
            )

        serializer.save()


class VacateAllocationView(APIView):
    """POST /hostel/allocations/<pk>/vacate/"""

    permission_classes = [IsStaffRole]

    def post(self, request, pk):
        from django.utils import timezone

        institution = get_institution(request)

        # The vacate target is scoped to the active institution. With no
        # valid active school the queryset is empty, so the lookup 404s and
        # never touches another school's allocation.
        queryset = Allocation.objects.all()

        if institution is not None:
            queryset = queryset.filter(
                room__hostel__campus__school=institution
            )
        else:
            queryset = queryset.none()

        allocation = get_object_or_404(queryset, pk=pk)
        allocation.status = "vacated"
        allocation.end_date = timezone.localdate()
        allocation.save()

        return Response(
            AllocationSerializer(allocation).data,
            status=status.HTTP_200_OK,
        )
