"""Transport Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class StudentTransportListReportView(AggregateReportView):
    """Student transport assignment list."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "transport_students"
    model = "apps.transport.models.RouteAssignment"

    def get_base_queryset(self, request):
        from apps.transport.models import RouteAssignment
        return RouteAssignment.objects.filter(status="active").select_related(
            "student", "student__primary_campus", "route__vehicle", "route__driver", "route__campus"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "route__campus_id")

        route = request.query_params.get("route")
        if route:
            queryset = queryset.filter(route_id=route)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_route = queryset.values("route__name").annotate(count=Count("id"))
        by_vehicle = queryset.values("route__vehicle__plate_number").annotate(count=Count("id"))

        return {
            "total_students": total,
            "total_routes": by_route.count(),
            "by_route": list(by_route),
            "by_vehicle": list(by_vehicle),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for assignment in queryset:
            rows.append({
                "admission_number": assignment.student.admission_number,
                "student": assignment.student.full_name,
                "campus": assignment.route.campus.name if assignment.route.campus else "-",
                "route": assignment.route.name,
                "vehicle": assignment.route.vehicle.plate_number if assignment.route.vehicle else "-",
                "driver": assignment.route.driver.full_name if assignment.route.driver else "-",
                "pickup_point": assignment.pickup_point or "-",
                "drop_point": assignment.drop_point or "-",
                "monthly_fee": quantize(assignment.monthly_fee) if assignment.monthly_fee else "0.00",
            })
        return rows


class RouteReportView(AggregateReportView):
    """Route details report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "transport_routes"
    model = "apps.transport.models.Route"

    def get_base_queryset(self, request):
        from apps.transport.models import Route
        return Route.objects.filter(status=True).select_related("campus", "vehicle", "driver").prefetch_related("assignments")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")
        return queryset

    def get_summary(self, queryset, request):
        total_routes = queryset.count()
        total_students = sum(r.assignments.filter(status="active").count() for r in queryset)

        return {
            "total_routes": total_routes,
            "total_students": total_students,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for route in queryset:
            active_students = route.assignments.filter(status="active").count()
            capacity = route.vehicle.capacity if route.vehicle else 0
            utilization = round(active_students / capacity * 100, 2) if capacity else 0

            rows.append({
                "name": route.name,
                "campus": route.campus.name if route.campus else "-",
                "vehicle": route.vehicle.plate_number if route.vehicle else "-",
                "vehicle_capacity": capacity,
                "driver": route.driver.full_name if route.driver else "-",
                "driver_phone": route.driver.phone if route.driver else "-",
                "active_students": active_students,
                "utilization": utilization,
                "stops_count": route.stops.count(),
            })
        return rows


class VehicleReportView(AggregateReportView):
    """Vehicle details report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "transport_vehicles"
    model = "apps.transport.models.Vehicle"

    def get_base_queryset(self, request):
        from apps.transport.models import Vehicle
        return Vehicle.objects.select_related("campus").prefetch_related("routes")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        status = request.query_params.get("status")
        if status == "active":
            queryset = queryset.filter(status=True)
        elif status == "inactive":
            queryset = queryset.filter(status=False)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        active = queryset.filter(status=True).count()
        total_capacity = sum(v.capacity for v in queryset)

        return {
            "total_vehicles": total,
            "active": active,
            "inactive": total - active,
            "total_capacity": total_capacity,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for vehicle in queryset:
            routes = vehicle.routes.filter(status=True)
            total_students = sum(r.assignments.filter(status="active").count() for r in routes)

            rows.append({
                "plate_number": vehicle.plate_number,
                "campus": vehicle.campus.name if vehicle.campus else "-",
                "type": vehicle.get_vehicle_type_display() if hasattr(vehicle, 'vehicle_type') else "Bus",
                "capacity": vehicle.capacity,
                "status": "Active" if vehicle.status else "Inactive",
                "routes_count": routes.count(),
                "assigned_students": total_students,
                "insurance_expiry": vehicle.insurance_expiry,
                "fitness_expiry": vehicle.fitness_expiry,
            })
        return rows


class DriverReportView(AggregateReportView):
    """Driver details report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "transport_drivers"
    model = "apps.transport.models.Driver"

    def get_base_queryset(self, request):
        from apps.transport.models import Driver
        return Driver.objects.select_related("campus", "vehicle").prefetch_related("routes")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        status = request.query_params.get("status")
        if status == "active":
            queryset = queryset.filter(status=True)
        elif status == "inactive":
            queryset = queryset.filter(status=False)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        active = queryset.filter(status=True).count()

        return {
            "total_drivers": total,
            "active": active,
            "inactive": total - active,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for driver in queryset:
            routes = driver.routes.filter(status=True)
            total_students = sum(r.assignments.filter(status="active").count() for r in routes)

            rows.append({
                "name": driver.full_name,
                "employee_number": driver.employee_number,
                "campus": driver.campus.name if driver.campus else "-",
                "phone": driver.phone,
                "license_number": driver.license_number,
                "license_expiry": driver.license_expiry,
                "status": "Active" if driver.status else "Inactive",
                "vehicle": driver.vehicle.plate_number if driver.vehicle else "-",
                "routes": ", ".join([r.name for r in routes]),
                "total_students": total_students,
            })
        return rows


class PickupDropoffReportView(AggregateReportView):
    """Pickup/Drop-off points report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "transport_pickup_dropoff"
    model = "apps.transport.models.RouteAssignment"

    def get_base_queryset(self, request):
        from apps.transport.models import RouteAssignment
        return RouteAssignment.objects.filter(status="active").select_related(
            "student", "route", "route__campus"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "route__campus_id")

        route = request.query_params.get("route")
        if route:
            queryset = queryset.filter(route_id=route)

        return queryset

    def get_summary(self, queryset, request):
        pickup_points = queryset.exclude(pickup_point="").values("pickup_point").distinct().count()
        drop_points = queryset.exclude(drop_point="").values("drop_point").distinct().count()

        return {
            "total_assignments": queryset.count(),
            "unique_pickup_points": pickup_points,
            "unique_drop_points": drop_points,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for assignment in queryset:
            rows.append({
                "student": assignment.student.full_name,
                "admission_number": assignment.student.admission_number,
                "route": assignment.route.name,
                "pickup_point": assignment.pickup_point or "-",
                "drop_point": assignment.drop_point or "-",
                "pickup_time": assignment.pickup_time,
                "drop_time": assignment.drop_time,
            })
        return rows


class StudentsByRouteReportView(AggregateReportView):
    """Students grouped by route."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "transport_students_by_route"
    model = "apps.transport.models.Route"

    def get_base_queryset(self, request):
        from apps.transport.models import Route
        return Route.objects.filter(status=True).select_related("campus", "vehicle").prefetch_related("assignments__student")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")
        return queryset

    def get_summary(self, queryset, request):
        return {"total_routes": queryset.count()}

    def get_detail_rows(self, queryset, request):
        rows = []
        for route in queryset:
            assignments = route.assignments.filter(status="active")
            for assignment in assignments:
                rows.append({
                    "route": route.name,
                    "vehicle": route.vehicle.plate_number if route.vehicle else "-",
                    "driver": route.driver.full_name if route.driver else "-",
                    "admission_number": assignment.student.admission_number,
                    "student": assignment.student.full_name,
                    "pickup_point": assignment.pickup_point or "-",
                    "drop_point": assignment.drop_point or "-",
                })
        return rows


class StudentsByVehicleReportView(AggregateReportView):
    """Students grouped by vehicle."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "transport_students_by_vehicle"
    model = "apps.transport.models.Vehicle"

    def get_base_queryset(self, request):
        from apps.transport.models import Vehicle
        return Vehicle.objects.filter(status=True).select_related("campus").prefetch_related("routes__assignments__student")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")
        return queryset

    def get_summary(self, queryset, request):
        return {"total_vehicles": queryset.count()}

    def get_detail_rows(self, queryset, request):
        rows = []
        for vehicle in queryset:
            for route in vehicle.routes.filter(status=True):
                for assignment in route.assignments.filter(status="active"):
                    rows.append({
                        "vehicle": vehicle.plate_number,
                        "route": route.name,
                        "driver": route.driver.full_name if route.driver else "-",
                        "admission_number": assignment.student.admission_number,
                        "student": assignment.student.full_name,
                    })
        return rows


class TransportFeeReportView(AggregateReportView):
    """Transport fee collection report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "transport_fees"
    model = "apps.transport.models.RouteAssignment"

    def get_base_queryset(self, request):
        from apps.transport.models import RouteAssignment
        return RouteAssignment.objects.filter(status="active").select_related(
            "student", "student__primary_campus", "route__vehicle", "route__campus"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "route__campus_id")

        route = request.query_params.get("route")
        if route:
            queryset = queryset.filter(route_id=route)

        return queryset

    def get_summary(self, queryset, request):
        total_fee = sum(Decimal(str(a.monthly_fee)) for a in queryset if a.monthly_fee)
        paid_count = 0  # Would need payment tracking

        return {
            "total_students": queryset.count(),
            "total_monthly_fee": quantize(total_fee),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for assignment in queryset:
            rows.append({
                "admission_number": assignment.student.admission_number,
                "student": assignment.student.full_name,
                "campus": assignment.route.campus.name if assignment.route.campus else "-",
                "route": assignment.route.name,
                "vehicle": assignment.route.vehicle.plate_number if assignment.route.vehicle else "-",
                "monthly_fee": quantize(assignment.monthly_fee) if assignment.monthly_fee else "0.00",
            })
        return rows


class VehicleCapacityReportView(AggregateReportView):
    """Vehicle capacity utilization report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "transport_vehicle_capacity"
    model = "apps.transport.models.Vehicle"

    def get_base_queryset(self, request):
        from apps.transport.models import Vehicle
        return Vehicle.objects.filter(status=True).select_related("campus").prefetch_related("routes__assignments")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")
        return queryset

    def get_summary(self, queryset, request):
        total_capacity = sum(v.capacity for v in queryset)
        total_students = sum(
            sum(r.assignments.filter(status="active").count() for r in v.routes.filter(status=True))
            for v in queryset
        )

        return {
            "total_vehicles": queryset.count(),
            "total_capacity": total_capacity,
            "total_students": total_students,
            "average_utilization": round(total_students / total_capacity * 100, 2) if total_capacity else 0,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for vehicle in queryset:
            active_assignments = sum(
                r.assignments.filter(status="active").count()
                for r in vehicle.routes.filter(status=True)
            )
            utilization = round(active_assignments / vehicle.capacity * 100, 2) if vehicle.capacity else 0

            rows.append({
                "vehicle": vehicle.plate_number,
                "campus": vehicle.campus.name if vehicle.campus else "-",
                "capacity": vehicle.capacity,
                "assigned_students": active_assignments,
                "free_seats": vehicle.capacity - active_assignments,
                "utilization": utilization,
            })
        return rows


class RouteOccupancyReportView(AggregateReportView):
    """Route occupancy report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "transport_route_occupancy"
    model = "apps.transport.models.Route"

    def get_base_queryset(self, request):
        from apps.transport.models import Route
        return Route.objects.filter(status=True).select_related("campus", "vehicle").prefetch_related("assignments")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")
        return queryset

    def get_summary(self, queryset, request):
        total_routes = queryset.count()
        overloaded = 0
        for route in queryset:
            capacity = route.vehicle.capacity if route.vehicle else 0
            students = route.assignments.filter(status="active").count()
            if capacity > 0 and students > capacity:
                overloaded += 1

        return {
            "total_routes": total_routes,
            "overloaded_routes": overloaded,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for route in queryset:
            capacity = route.vehicle.capacity if route.vehicle else 0
            students = route.assignments.filter(status="active").count()
            utilization = round(students / capacity * 100, 2) if capacity else 0
            is_overloaded = capacity > 0 and students > capacity

            rows.append({
                "route": route.name,
                "campus": route.campus.name if route.campus else "-",
                "vehicle": route.vehicle.plate_number if route.vehicle else "-",
                "capacity": capacity,
                "students": students,
                "free_seats": max(capacity - students, 0),
                "utilization": utilization,
                "overloaded": "Yes" if is_overloaded else "No",
            })
        return rows