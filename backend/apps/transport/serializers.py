from rest_framework import serializers

from .models import Driver, Route, RouteStop, TransportAssignment, Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "plate_number",
            "campus",
            "model",
            "capacity",
            "status",
            "status_display",
            "notes",
        ]


class DriverSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Driver
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "license_number",
            "phone",
            "campus",
            "status",
        ]


class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = ["id", "name", "order", "time"]


class RouteSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)
    vehicle_plate = serializers.CharField(
        source="vehicle.plate_number",
        read_only=True,
        default="",
    )
    driver_name = serializers.CharField(
        source="driver.full_name",
        read_only=True,
        default="",
    )

    class Meta:
        model = Route
        fields = [
            "id",
            "name",
            "description",
            "campus",
            "vehicle",
            "vehicle_plate",
            "driver",
            "driver_name",
            "start_point",
            "end_point",
            "status",
            "stops",
        ]


class TransportAssignmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )
    admission_number = serializers.CharField(
        source="student.admission_number",
        read_only=True,
    )
    route_name = serializers.CharField(
        source="route.name",
        read_only=True,
    )
    stop_name = serializers.CharField(
        source="stop.name",
        read_only=True,
        default="",
    )

    class Meta:
        model = TransportAssignment
        fields = [
            "id",
            "student",
            "student_name",
            "admission_number",
            "route",
            "route_name",
            "stop",
            "stop_name",
            "status",
            "created_at",
        ]
