"""Device integration endpoints: biometric attendance and GPS pings.

Both are authenticated with a shared device key sent as X-Device-Key.
Configure allowed keys with comma-separated env values:
ATTENDANCE_DEVICE_KEYS / GPS_DEVICE_KEYS.
"""

import os

from django.http import JsonResponse
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


def _device_key_valid(request, env_name):
    allowed = [
        key.strip()
        for key in os.environ.get(env_name, "").split(",")
        if key.strip()
    ]

    return request.META.get("HTTP_X_DEVICE_KEY", "") in allowed


class GpsPingView(APIView):
    """POST /api/transport/gps/ping/

    Body: { vehicle: <id or plate>, lat, lng, speed? }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        if not _device_key_valid(request, "GPS_DEVICE_KEYS"):
            return JsonResponse(
                {"detail": "Invalid device key."}, status=401
            )

        from .models import Vehicle, VehicleLocationLog

        vehicle_ref = request.data.get("vehicle")
        lat = request.data.get("lat")
        lng = request.data.get("lng")

        if not (vehicle_ref and lat and lng):
            return JsonResponse(
                {"detail": "vehicle, lat and lng are required."},
                status=400,
            )

        vehicle = None

        if str(vehicle_ref).isdigit():
            vehicle = Vehicle.objects.filter(pk=vehicle_ref).first()

        if vehicle is None:
            vehicle = Vehicle.objects.filter(
                plate_number__iexact=str(vehicle_ref)
            ).first()

        if vehicle is None:
            return JsonResponse(
                {"detail": "Unknown vehicle."}, status=404
            )

        log = VehicleLocationLog.objects.create(
            vehicle=vehicle,
            latitude=lat,
            longitude=lng,
            speed_kmh=request.data.get("speed"),
        )

        return JsonResponse({
            "id": log.id,
            "recorded_at": log.recorded_at.isoformat(),
        })


class GpsLiveView(APIView):
    """GET /api/transport/gps/live/ -> latest position per vehicle."""

    permission_classes = [AllowAny]

    def get(self, request):
        from django.db.models import OuterRef, Subquery

        from apps.accounts.access import apply_campus_scope
        from .models import Vehicle, VehicleLocationLog

        vehicles = apply_campus_scope(
            Vehicle.objects.all(),
            request,
        ).filter(status="operational")

        latest = VehicleLocationLog.objects.filter(
            vehicle=OuterRef("pk")
        ).order_by("-recorded_at")

        rows = []

        for vehicle in vehicles.annotate(
            last_lat=Subquery(
                latest.values("latitude")[:1]
            ),
            last_lng=Subquery(
                latest.values("longitude")[:1]
            ),
            last_seen=Subquery(
                latest.values("recorded_at")[:1]
            ),
            last_speed=Subquery(
                latest.values("speed_kmh")[:1]
            ),
        ):
            route = vehicle.routes.filter(status=True).first()

            rows.append({
                "vehicle": vehicle.plate_number,
                "route": route.name if route else "-",
                "campus": (
                    vehicle.campus.name if vehicle.campus_id else "-"
                ),
                "lat": (
                    float(vehicle.last_lat)
                    if vehicle.last_lat is not None
                    else None
                ),
                "lng": (
                    float(vehicle.last_lng)
                    if vehicle.last_lng is not None
                    else None
                ),
                "speed_kmh": vehicle.last_speed,
                "last_seen": (
                    vehicle.last_seen.isoformat()
                    if vehicle.last_seen
                    else None
                ),
            })

        return Response(rows)
