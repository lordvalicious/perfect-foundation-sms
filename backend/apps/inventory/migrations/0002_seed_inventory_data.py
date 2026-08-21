from decimal import Decimal
from django.db import migrations


def seed_inventory(apps, schema_editor):
    AssetCategory = apps.get_model("inventory", "AssetCategory")
    Supplier = apps.get_model("inventory", "Supplier")
    Asset = apps.get_model("inventory", "Asset")
    MaintenanceRecord = apps.get_model("inventory", "MaintenanceRecord")

    if AssetCategory.objects.exists():
        return

    categories_data = [
        {"name": "Furniture", "description": "Desks, chairs, tables, cupboards"},
        {"name": "IT Equipment", "description": "Computers, printers, projectors, routers"},
        {"name": "Lab Equipment", "description": "Science lab apparatus and tools"},
        {"name": "Sports Equipment", "description": "Balls, nets, bats, cones, bibs"},
        {"name": "Office Supplies", "description": "Stationery, paper, ink cartridges"},
        {"name": "Audio Visual", "description": "Speakers, microphones, screens"},
        {"name": "Cleaning", "description": "Mops, buckets, cleaning chemicals"},
    ]
    categories = {}
    for c in categories_data:
        cat = AssetCategory.objects.create(**c)
        categories[c["name"]] = cat

    suppliers_data = [
        {"name": "TechZone Pakistan", "contact_person": "Ahmed Khan", "phone": "0321-1112233", "email": "sales@techzone.pk", "address": "Hall Road, Lahore"},
        {"name": "Office Stationers", "contact_person": "Faisal Malik", "phone": "0300-4445566", "email": "info@officestationers.pk", "address": "Shah Alam Market, Lahore"},
        {"name": "Scientific Supply Co.", "contact_person": "Dr. Nasir", "phone": "0333-7778899", "email": "orders@scisupply.pk", "address": "GT Road, Lahore"},
        {"name": "Sports World", "contact_person": "Tariq Hussain", "phone": "0312-6655443", "email": "contact@sportsworld.pk", "address": "Mall Road, Lahore"},
    ]
    suppliers = {}
    for s in suppliers_data:
        sup = Supplier.objects.create(**s)
        suppliers[s["name"]] = sup

    assets_data = [
        {"name": "Student Desk (Wood)", "category": categories["Furniture"], "supplier": suppliers["Office Stationers"], "quantity": 120, "unit_cost": Decimal("4500.00"), "location": "Building A - Classrooms", "status": "in_use"},
        {"name": "Student Chair (Wood)", "category": categories["Furniture"], "supplier": suppliers["Office Stationers"], "quantity": 120, "unit_cost": Decimal("2800.00"), "location": "Building A - Classrooms", "status": "in_use"},
        {"name": "Teacher Desk", "category": categories["Furniture"], "supplier": suppliers["Office Stationers"], "quantity": 20, "unit_cost": Decimal("8500.00"), "location": "Staff Room", "status": "in_use"},
        {"name": "Office Chair (Swivel)", "category": categories["Furniture"], "supplier": suppliers["Office Stationers"], "quantity": 15, "unit_cost": Decimal("12000.00"), "location": "Admin Office", "status": "in_use"},
        {"name": "Desktop Computer (Core i5)", "category": categories["IT Equipment"], "supplier": suppliers["TechZone Pakistan"], "quantity": 30, "unit_cost": Decimal("85000.00"), "location": "Computer Lab 1", "status": "in_use"},
        {"name": "Laptop (Dell Latitude)", "category": categories["IT Equipment"], "supplier": suppliers["TechZone Pakistan"], "quantity": 10, "unit_cost": Decimal("120000.00"), "location": "Staff Room", "status": "in_use"},
        {"name": "LCD Projector (Epson)", "category": categories["IT Equipment"], "supplier": suppliers["TechZone Pakistan"], "quantity": 8, "unit_cost": Decimal("65000.00"), "location": "Various Classrooms", "status": "in_use"},
        {"name": "WiFi Router (Ubiquiti)", "category": categories["IT Equipment"], "supplier": suppliers["TechZone Pakistan"], "quantity": 5, "unit_cost": Decimal("15000.00"), "location": "Server Room", "status": "in_use"},
        {"name": "Printer (HP LaserJet)", "category": categories["IT Equipment"], "supplier": suppliers["TechZone Pakistan"], "quantity": 4, "unit_cost": Decimal("35000.00"), "location": "Admin Office", "status": "in_use"},
        {"name": "Microscope (Binocular)", "category": categories["Lab Equipment"], "supplier": suppliers["Scientific Supply Co."], "quantity": 12, "unit_cost": Decimal("25000.00"), "location": "Science Lab", "status": "in_use"},
        {"name": "Chemical Glassware Set", "category": categories["Lab Equipment"], "supplier": suppliers["Scientific Supply Co."], "quantity": 10, "unit_cost": Decimal("8000.00"), "location": "Chemistry Lab", "status": "in_use"},
        {"name": "Physics Experiment Kit", "category": categories["Lab Equipment"], "supplier": suppliers["Scientific Supply Co."], "quantity": 8, "unit_cost": Decimal("15000.00"), "location": "Physics Lab", "status": "in_stock"},
        {"name": "Football (Size 5)", "category": categories["Sports Equipment"], "supplier": suppliers["Sports World"], "quantity": 15, "unit_cost": Decimal("2500.00"), "location": "Sports Room", "status": "in_use"},
        {"name": "Cricket Bat (SS)", "category": categories["Sports Equipment"], "supplier": suppliers["Sports World"], "quantity": 10, "unit_cost": Decimal("3500.00"), "location": "Sports Room", "status": "in_use"},
        {"name": "Basketball", "category": categories["Sports Equipment"], "supplier": suppliers["Sports World"], "quantity": 8, "unit_cost": Decimal("2000.00"), "location": "Sports Room", "status": "in_use"},
        {"name": "Badminton Racket Set", "category": categories["Sports Equipment"], "supplier": suppliers["Sports World"], "quantity": 6, "unit_cost": Decimal("1800.00"), "location": "Sports Room", "status": "in_stock"},
        {"name": "Whiteboard (4x6 ft)", "category": categories["Office Supplies"], "supplier": suppliers["Office Stationers"], "quantity": 20, "unit_cost": Decimal("5500.00"), "location": "Various Classrooms", "status": "in_use"},
        {"name": "Toner Cartridge (HP)", "category": categories["Office Supplies"], "supplier": suppliers["Office Stationers"], "quantity": 12, "unit_cost": Decimal("3500.00"), "location": "Store Room", "status": "in_stock"},
        {"name": "LED Screen 65 inch", "category": categories["Audio Visual"], "supplier": suppliers["TechZone Pakistan"], "quantity": 3, "unit_cost": Decimal("95000.00"), "location": "Auditorium", "status": "in_use"},
        {"name": "Vacuum Cleaner (Industrial)", "category": categories["Cleaning"], "supplier": suppliers["Office Stationers"], "quantity": 2, "unit_cost": Decimal("28000.00"), "location": "Store Room", "status": "in_use"},
    ]

    created_assets = []
    for a in assets_data:
        asset = Asset.objects.create(**a)
        created_assets.append(asset)

    MaintenanceRecord.objects.create(
        asset=created_assets[4],
        date="2025-06-15",
        cost=Decimal("5000.00"),
        description="Replaced faulty hard drive on workstation #7",
        performed_by="TechZone Pakistan",
        status="completed",
    )
    MaintenanceRecord.objects.create(
        asset=created_assets[6],
        date="2025-07-20",
        cost=Decimal("3000.00"),
        description="Lamp replacement and filter cleaning",
        performed_by="TechZone Pakistan",
        status="completed",
    )
    MaintenanceRecord.objects.create(
        asset=created_assets[19],
        date="2025-08-10",
        cost=Decimal("12000.00"),
        description="Full engine service and brake pad replacement",
        performed_by="N/A",
        status="in_progress",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(seed_inventory, migrations.RunPython.noop),
    ]
