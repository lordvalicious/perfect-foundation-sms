import random

from django.core.management.base import BaseCommand

from apps.schools.models import Campus, School
from apps.students.models import Enrollment
from apps.transport.models import Driver, Route, RouteStop, TransportAssignment, Vehicle


class Command(BaseCommand):
    help = "Seed transport data: vehicles, drivers, routes, stops, and student assignments."

    VEHICLE_MODELS = [
        ("Toyota Coaster", 30),
        ("Honda MB100", 20),
        ("Master Coach", 40),
        ("Hino Rosa", 35),
        ("Yutong Bus", 45),
        ("Shehzore Pickup", 8),
        ("Suzuki Bolan", 8),
        ("HiAce Commuter", 14),
    ]

    FIRST_NAMES = [
        "Abdul", "Muhammad", "Ali", "Hassan", "Hussain", "Bilal",
        "Faisal", "Imran", "Javed", "Kamran", "Nadeem", "Rashid",
        "Saeed", "Tariq", "Younis", "Zubair", "Aslam", "Irfan",
    ]

    LAST_NAMES = [
        "Raza", "Khan", "Malik", "Ahmed", "Sheikh", "Chaudhry",
        "Qureshi", "Bajwa", "Gujjar", "Awan", "Mughal", "Nawaz",
        "Tariq", "Wattoo", "Yaqub", "Zaman", "Bhatti", "Cheema",
    ]

    STOP_NAMES = [
        "Main Bazaar", "Hospital Road", "College Chowk", "Masjid Road",
        "Railway Station", "City Park", "Shopping Mall", "Government Office",
        "Police Station", "Post Office", "Bank Road", "Library Chowk",
        "Graveyard Stop", "Bus Terminal", "University Gate", "市场街",
        "Satellite Town", "Gulberg", "DHA Phase 1", "Cantonment Area",
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\nSeeding transport data...\n"))

        if not School.objects.exists():
            self.stderr.write(self.style.ERROR("No school found. Run seed setup first."))
            return

        campuses = list(
            Campus.objects.filter(status="active").select_related("school")
        )
        if not campuses:
            self.stderr.write(self.style.ERROR("No active campuses found."))
            return

        vehicles_created = 0
        drivers_created = 0
        routes_created = 0
        stops_created = 0
        assignments_created = 0

        for campus in campuses:
            self.stdout.write(f"\nProcessing {campus.name}...")

            num_vehicles = random.randint(2, 4)
            vehicles = []

            for i in range(num_vehicles):
                model_name, capacity = random.choice(self.VEHICLE_MODELS)
                plate = f"LEA-{random.randint(10, 99)}-{random.randint(1000, 9999)}"

                vehicle, created = Vehicle.objects.get_or_create(
                    institution=campus.school,
                    plate_number=plate,
                    defaults={
                        "campus": campus,
                        "model": model_name,
                        "capacity": capacity,
                        "status": random.choice(["operational", "operational", "operational", "maintenance"]),
                        "notes": f"Vehicle for {campus.name} route.",
                    },
                )
                if created:
                    vehicles_created += 1
                vehicles.append(vehicle)

            num_drivers = random.randint(2, 3)
            drivers = []

            for i in range(num_drivers):
                fn = random.choice(self.FIRST_NAMES)
                ln = random.choice(self.LAST_NAMES)

                driver, created = Driver.objects.get_or_create(
                    institution=campus.school,
                    first_name=fn,
                    last_name=ln,
                    defaults={
                        "license_number": f"LIC-{random.randint(100000, 999999)}",
                        "phone": f"03{random.randint(10, 49)}-{random.randint(1000000, 9999999)}",
                        "campus": campus,
                        "status": True,
                    },
                )
                if created:
                    drivers_created += 1
                drivers.append(driver)

            num_routes = random.randint(2, 3)
            for i in range(num_routes):
                route_name = f"{campus.name} Route {chr(65 + i)}"

                vehicle = vehicles[i % len(vehicles)] if vehicles else None
                driver = drivers[i % len(drivers)] if drivers else None

                route, created = Route.objects.get_or_create(
                    institution=campus.school,
                    name=route_name,
                    defaults={
                        "campus": campus,
                        "vehicle": vehicle,
                        "driver": driver,
                        "description": f"Daily route for {campus.name} students.",
                        "start_point": random.choice(self.STOP_NAMES),
                        "end_point": random.choice(self.STOP_NAMES),
                        "status": True,
                    },
                )
                if created:
                    routes_created += 1

                    num_stops = random.randint(3, 6)
                    used_stops = set()

                    for j in range(num_stops):
                        stop_name = random.choice(self.STOP_NAMES)
                        while stop_name in used_stops:
                            stop_name = random.choice(self.STOP_NAMES)
                        used_stops.add(stop_name)

                        RouteStop.objects.create(
                            route=route,
                            name=stop_name,
                            order=j + 1,
                            time=None,
                        )
                        stops_created += 1

                    enrollments = list(
                        Enrollment.objects.filter(
                            campus=campus,
                            status="active",
                        ).select_related("student")[:random.randint(5, 15)]
                    )

                    for enrollment in enrollments:
                        route_stops = list(route.stops.all())
                        if route_stops:
                            stop = random.choice(route_stops)
                        else:
                            stop = None

                        _, assign_created = TransportAssignment.objects.get_or_create(
                            student=enrollment.student,
                            route=route,
                            defaults={
                                "stop": stop,
                                "status": "active",
                            },
                        )
                        if assign_created:
                            assignments_created += 1

        self.stdout.write(self.style.SUCCESS(f"\nVehicles created: {vehicles_created}"))
        self.stdout.write(self.style.SUCCESS(f"Drivers created: {drivers_created}"))
        self.stdout.write(self.style.SUCCESS(f"Routes created: {routes_created}"))
        self.stdout.write(self.style.SUCCESS(f"Route stops created: {stops_created}"))
        self.stdout.write(self.style.SUCCESS(f"Transport assignments created: {assignments_created}"))
        self.stdout.write(self.style.SUCCESS("\nTransport seeding completed.\n"))
