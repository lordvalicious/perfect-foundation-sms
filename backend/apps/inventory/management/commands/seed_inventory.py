import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.accounts.models import StaffProfile
from apps.inventory.models import Asset, AssetAssignment, AssetCategory, MaintenanceRecord, Supplier
from apps.schools.models import Campus, School


class Command(BaseCommand):
    help = "Seed inventory with categories, suppliers, assets, assignments, and maintenance records."

    CATEGORIES = [
        ("Furniture", "Desks, chairs, tables, cabinets"),
        ("Electronics", "Computers, printers, projectors, screens"),
        ("Lab Equipment", "Microscopes, chemicals, lab tools"),
        ("Sports Equipment", "Cricket bats, footballs, nets, goals"),
        ("Stationery", "Pens, paper, files, markers"),
        ("Audio Visual", "Speakers, mics, cameras, TVs"),
        ("IT Infrastructure", "Routers, switches, cables, UPS"),
        ("Kitchen Equipment", "Stoves, utensils, refrigerators"),
    ]

    SUPPLIERS = [
        ("Al-Faisal Trading Co.", "Ahmed Raza", "0321-1234567", "supplier1@example.com"),
        ("National Stationery House", "Bilal Khan", "0300-9876543", "supplier2@example.com"),
        ("Pak IT Solutions", "Daniyal Malik", "0311-5551234", "supplier3@example.com"),
        ("Sports World Pakistan", "Faisal Ahmed", "0322-7778899", "supplier4@example.com"),
        ("Sialkot Scientific Supplies", "Hamza Sheikh", "0333-4445566", "supplier5@example.com"),
        ("Master Electronics", "Imran Chaudhry", "0345-2223344", "supplier6@example.com"),
    ]

    ASSET_NAMES = {
        "Furniture": [
            ("Student Desk", 4500), ("Teacher Chair", 8000),
            ("Staff Table", 12000), ("Filing Cabinet", 15000),
            ("Bookshelf", 18000), ("Office Sofa", 25000),
            ("Staff Room Table", 20000), ("Classroom Board Stand", 6000),
        ],
        "Electronics": [
            ("Desktop Computer", 65000), ("Laptop", 95000),
            ("Printer", 35000), ("Projector", 85000),
            ("Smart Board", 120000), ("UPS 1500VA", 28000),
            ("Monitor 24 inch", 42000), ("Keyboard & Mouse Set", 3000),
        ],
        "Lab Equipment": [
            ("Microscope", 35000), ("Chemical Set", 15000),
            ("Lab Table", 22000), ("Test Tubes Set", 5000),
            ("Beakers Set", 3500), ("Bunsen Burner", 8000),
        ],
        "Sports Equipment": [
            ("Cricket Bat", 3500), ("Football", 2500),
            ("Badminton Net", 4000), ("Volleyball Set", 6000),
            ("Table Tennis Table", 25000), ("Basketball Hoop", 30000),
        ],
        "Stationery": [
            ("Ream of Paper", 1200), ("Marker Set", 800),
            ("File Folder Pack", 600), ("Pen Holder", 350),
            ("Stapler", 500), ("Tape Dispenser", 300),
        ],
        "Audio Visual": [
            ("Speaker Set", 18000), ("Wireless Microphone", 12000),
            ("LED TV 55 inch", 110000), ("Camera", 85000),
            ("Projector Screen", 15000),
        ],
        "IT Infrastructure": [
            ("WiFi Router", 8000), ("Network Switch", 15000),
            ("Ethernet Cable Roll", 3000), ("Server Rack", 45000),
            ("CCTV Camera", 12000),
        ],
        "Kitchen Equipment": [
            ("Gas Stove", 25000), ("Refrigerator", 85000),
            ("Water Dispenser", 18000), ("Microwave Oven", 32000),
        ],
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\nSeeding inventory data...\n"))

        school = School.objects.first()
        if not school:
            self.stderr.write(self.style.ERROR("No school found."))
            return

        campuses = list(Campus.objects.filter(status="active"))
        if not campuses:
            self.stderr.write(self.style.ERROR("No active campuses found."))
            return

        cat_created = 0
        supplier_created = 0
        asset_created = 0
        assignment_created = 0
        maintenance_created = 0

        categories = {}
        for name, desc in self.CATEGORIES:
            cat, created = AssetCategory.objects.get_or_create(
                institution=school,
                name=name,
                defaults={"description": desc},
            )
            categories[name] = cat
            if created:
                cat_created += 1

        suppliers = []
        for name, contact, phone, email in self.SUPPLIERS:
            supplier, created = Supplier.objects.get_or_create(
                institution=school,
                name=name,
                defaults={
                    "contact_person": contact,
                    "phone": phone,
                    "email": email,
                    "address": f"Sialkot, Punjab, Pakistan",
                },
            )
            suppliers.append(supplier)
            if created:
                supplier_created += 1

        staff_profiles = list(StaffProfile.objects.filter(status="active")[:15])

        for campus in campuses:
            self.stdout.write(f"\nProcessing {campus.name}...")

            for cat_name, assets_list in self.ASSET_NAMES.items():
                for asset_name, unit_cost in assets_list:
                    qty = random.randint(1, 20)
                    status = random.choice(["in_stock", "in_use", "in_use", "in_stock", "maintenance"])

                    asset, created = Asset.objects.get_or_create(
                        institution=school,
                        name=asset_name,
                        campus=campus,
                        defaults={
                            "category": categories.get(cat_name),
                            "supplier": random.choice(suppliers) if suppliers else None,
                            "quantity": qty,
                            "unit_cost": Decimal(str(unit_cost)),
                            "purchase_date": date.today() - timedelta(days=random.randint(30, 365)),
                            "location": f"{campus.name} - Room {random.randint(1, 20)}",
                            "status": status,
                            "notes": "",
                        },
                    )
                    if created:
                        asset_created += 1

                        if status == "in_use" and staff_profiles:
                            assignee = random.choice(staff_profiles)
                            AssetAssignment.objects.create(
                                asset=asset,
                                assignee_type="staff",
                                assignee_name=f"{assignee.first_name} {assignee.last_name}",
                                quantity=min(qty, random.randint(1, 3)),
                                notes=f"Assigned to {assignee.designation}.",
                            )
                            assignment_created += 1

                        if random.random() < 0.15:
                            MaintenanceRecord.objects.create(
                                asset=asset,
                                date=date.today() - timedelta(days=random.randint(1, 90)),
                                cost=Decimal(str(random.randint(500, 15000))),
                                description=random.choice([
                                    "Routine maintenance check.",
                                    "Repaired broken part.",
                                    "Software update.",
                                    "Cleaned and serviced.",
                                    "Replaced worn components.",
                                ]),
                                performed_by=random.choice([
                                    "Internal IT Team",
                                    "External Vendor",
                                    "Campus Maintenance Staff",
                                ]),
                                status=random.choice(["completed", "completed", "scheduled"]),
                            )
                            maintenance_created += 1

        self.stdout.write(self.style.SUCCESS(f"\nCategories created: {cat_created}"))
        self.stdout.write(self.style.SUCCESS(f"Suppliers created: {supplier_created}"))
        self.stdout.write(self.style.SUCCESS(f"Assets created: {asset_created}"))
        self.stdout.write(self.style.SUCCESS(f"Asset assignments created: {assignment_created}"))
        self.stdout.write(self.style.SUCCESS(f"Maintenance records created: {maintenance_created}"))
        self.stdout.write(self.style.SUCCESS("\nInventory seeding completed.\n"))
