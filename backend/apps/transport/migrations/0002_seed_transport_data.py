from django.db import migrations


def seed_transport(apps, schema_editor):
    Vehicle = apps.get_model("transport", "Vehicle")
    Driver = apps.get_model("transport", "Driver")
    Route = apps.get_model("transport", "Route")
    RouteStop = apps.get_model("transport", "RouteStop")

    if Vehicle.objects.exists():
        return

    drivers_data = [
        {"first_name": "Muhammad", "last_name": "Aslam", "license_number": "DL-2019-4455", "phone": "0321-4567890"},
        {"first_name": "Ali", "last_name": "Hassan", "license_number": "DL-2020-7812", "phone": "0333-1234567"},
        {"first_name": "Rashid", "last_name": "Ahmed", "license_number": "DL-2018-3321", "phone": "0300-9876543"},
    ]
    drivers = []
    for d in drivers_data:
        drivers.append(Driver.objects.create(**d))

    vehicles_data = [
        {"plate_number": "LEA-2021", "model": "Toyota Coaster", "capacity": 30, "status": "operational"},
        {"plate_number": "LER-2022", "model": "Hyundai County", "capacity": 25, "status": "operational"},
        {"plate_number": "LAG-2020", "model": "Toyota Hiace", "capacity": 14, "status": "operational"},
        {"plate_number": "LEB-2023", "model": "Master Daewoo", "capacity": 40, "status": "operational"},
        {"plate_number": "Lec-2019", "model": "Hino Poncho", "capacity": 20, "status": "maintenance"},
    ]
    vehicles = []
    for v in vehicles_data:
        vehicles.append(Vehicle.objects.create(**v))

    routes_data = [
        {
            "name": "Route A - Gulberg",
            "description": "Gulberg Model Town Liberty Market circuit",
            "vehicle": vehicles[0],
            "driver": drivers[0],
            "start_point": "School Gate",
            "end_point": "Liberty Market Gulberg",
            "stops": [
                {"name": "School Gate", "order": 1, "time": "07:00"},
                {"name": "Canal Road Stop", "order": 2, "time": "07:10"},
                {"name": "Model Town Chowk", "order": 3, "time": "07:20"},
                {"name": "Liberty Market", "order": 4, "time": "07:30"},
            ],
        },
        {
            "name": "Route B - DHA",
            "description": "Defence Housing Authority Phase 1-5",
            "vehicle": vehicles[1],
            "driver": drivers[1],
            "start_point": "School Gate",
            "end_point": "DHA Phase 5 Main Boulevard",
            "stops": [
                {"name": "School Gate", "order": 1, "time": "06:45"},
                {"name": "Canal Road Bridge", "order": 2, "time": "06:55"},
                {"name": "DHA Phase 2", "order": 3, "time": "07:05"},
                {"name": "DHA Phase 3", "order": 4, "time": "07:15"},
                {"name": "DHA Phase 5", "order": 5, "time": "07:25"},
            ],
        },
        {
            "name": "Route C - Johar Town",
            "description": "Johar Town and附近 areas",
            "vehicle": vehicles[2],
            "driver": drivers[2],
            "start_point": "School Gate",
            "end_point": "Johar Town Main Market",
            "stops": [
                {"name": "School Gate", "order": 1, "time": "06:50"},
                {"name": "Mall Road", "order": 2, "time": "07:00"},
                {"name": "Canal View Society", "order": 3, "time": "07:10"},
                {"name": "Johar Town Market", "order": 4, "time": "07:20"},
            ],
        },
    ]

    for rd in routes_data:
        stops_data = rd.pop("stops")
        route = Route.objects.create(**rd)
        for s in stops_data:
            RouteStop.objects.create(route=route, **s)


class Migration(migrations.Migration):
    dependencies = [
        ("transport", "0001_initial"),
        ("students", "0002_alter_enrollment_options"),
    ]
    operations = [
        migrations.RunPython(seed_transport, migrations.RunPython.noop),
    ]
