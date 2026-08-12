from django.contrib import admin

from .models import (
    Driver,
    Route,
    RouteStop,
    TransportAssignment,
    Vehicle,
)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["plate_number", "model", "capacity", "status"]


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ["full_name", "license_number", "phone", "status"]


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ["name", "vehicle", "driver", "status"]


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ["route", "name", "order"]


@admin.register(TransportAssignment)
class TransportAssignmentAdmin(admin.ModelAdmin):
    list_display = ["student", "route", "stop", "status"]
    list_filter = ["status"]
