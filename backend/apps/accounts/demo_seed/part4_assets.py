"""Part 4 — Operations: HR, payroll, library, transport, inventory.

Creates (idempotently, scoped to DEMO-EDU / ctx.school / ctx.active_year):
- HR departments and designations
- Employee records linking teachers + staff
- PayrollPeriods (3 months)
- SalaryStructures + components
- PayrollRecords
- Library books (150), BookCopies, BookIssues
- Vehicles (10), Drivers, Routes, Stops, TransportAssignments
- AssetCategories, Suppliers, Assets, MaintenanceRecords
- StockLevels, StockMovements
"""

from __future__ import annotations

import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.db import transaction

import apps.accounts.demo_seed.base as base
from apps.accounts.demo_seed.base import getc

CAMPUS_CODES = ["GVC", "CSC", "BFC", "KHC", "EXC"]


# ---------------------------------------------------------------------------
# HR: DEPARTMENTS + DESIGNATIONS + EMPLOYEES
# ---------------------------------------------------------------------------

def _seed_hr(ctx):
    ctx.log("Creating HR departments, designations, employee records...")
    from apps.hr.models import Department, Designation, Employee
    from apps.teachers.models import Teacher
    from apps.accounts.models import StaffProfile

    depts_data = [
        ("ACAD", "Academics"),
        ("ADMN", "Administration"),
        ("FINC", "Finance"),
        ("TRAN", "Transport"),
        ("LIBR", "Library"),
        ("MNTN", "Maintenance"),
        ("HLTH", "Health"),
        ("ITDE", "IT Department"),
        ("PRCL", "Pre-Primary"),
        ("SCNC", "Science"),
    ]
    departments = {}
    for code, name in depts_data:
        dept, _ = getc(
            Department,
            institution=ctx.school,
            code=code,
            defaults={"name": name, "status": "active"},
        )
        departments[code] = dept
        ctx.count("departments")

    designations_data = [
        ("TCHR", "Teacher", "ACAD", 2),
        ("PRNC", "Principal", "ACAD", 5),
        ("VPNC", "Vice Principal", "ACAD", 4),
        ("ACCT", "Accountant", "FINC", 3),
        ("HROF", "HR Officer", "ADMN", 3),
        ("LBRA", "Librarian", "LIBR", 2),
        ("DRVR", "Driver", "TRAN", 1),
        ("MNTR", "Maintenance", "MNTN", 1),
        ("SCGR", "Security Guard", "ADMN", 1),
        ("NRS", "Nurse", "HLTH", 2),
        ("RCPN", "Receptionist", "ADMN", 2),
        ("TCHN", "Technician", "ITDE", 2),
    ]
    designations = {}
    for code, name, dept_code, level in designations_data:
        des, _ = getc(
            Designation,
            institution=ctx.school,
            code=code,
            defaults={
                "name": name,
                "department": departments.get(dept_code),
                "level": level,
                "status": "active",
            },
        )
        designations[code] = des
        ctx.count("designations")

    # Link teachers to Employee records
    emp_count = 0
    teachers = Teacher.objects.filter(institution=ctx.school, primary_campus__isnull=False)
    for t in teachers:
        emp, created = Employee.objects.get_or_create(
            institution=ctx.school,
            employee_number=t.employee_number,
            defaults={
                "teacher": t,
                "primary_campus": t.primary_campus,
                "department": departments.get("ACAD"),
                "designation": designations.get("TCHR"),
                "employment_type": "permanent",
                "joining_date": t.joining_date or date(2020, 8, 1),
                "status": "active",
            },
        )
        if created:
            emp_count += 1
            ctx.count("employees")

    # Link support staff to Employee records
    staff_profiles = StaffProfile.objects.filter(
        institution=ctx.school, status="active"
    )
    for sp in staff_profiles:
        emp, created = Employee.objects.get_or_create(
            institution=ctx.school,
            employee_number=sp.employee_number,
            defaults={
                "staff_profile": sp,
                "primary_campus": sp.primary_campus,
                "department": departments.get("ADMN"),
                "designation": designations.get("HROF"),
                "employment_type": "permanent",
                "joining_date": sp.joining_date or date(2020, 8, 1),
                "status": "active",
            },
        )
        if created:
            emp_count += 1
            ctx.count("employees")

    ctx.ok(f"Departments: {len(departments)}, Designations: {len(designations)}, Employees: {emp_count}")


# ---------------------------------------------------------------------------
# PAYROLL: PERIODS + STRUCTURES + RECORDS
# ---------------------------------------------------------------------------

def _seed_payroll(ctx):
    ctx.log("Creating payroll periods, salary structures, payroll records...")
    from apps.hr.models import PayrollPeriod, Employee
    from apps.payroll.models import SalaryStructure, SalaryStructureComponent, PayrollRecord

    periods_data = [
        ("October 2026", date(2026, 10, 1), date(2026, 10, 31), date(2026, 11, 5)),
        ("November 2026", date(2026, 11, 1), date(2026, 11, 30), date(2026, 12, 5)),
        ("December 2026", date(2026, 12, 1), date(2026, 12, 31), date(2027, 1, 5)),
    ]
    periods = {}
    for name, start, end, pay_date in periods_data:
        period, _ = getc(
            PayrollPeriod,
            institution=ctx.school,
            name=name,
            defaults={
                "start_date": start,
                "end_date": end,
                "payment_date": pay_date,
                "status": "closed",
            },
        )
        periods[name] = period
        ctx.count("payroll_periods")

    # Salary structures for each employee
    employees = list(Employee.objects.filter(institution=ctx.school, status="active")[:100])
    structures = {}
    emp_seq = 0
    for emp in employees:
        emp_seq += 1
        basic = Decimal(str(random.choice([40000, 50000, 60000, 75000, 90000])))
        ss, created = SalaryStructure.objects.get_or_create(
            institution=ctx.school,
            code=f"SAL-{emp_seq:04d}",
            defaults={
                "employee": emp,
                "name": f"Salary Structure {emp_seq:04d}",
                "basic_salary": basic,
                "effective_date": date(2026, 8, 1),
                "status": "active",
            },
        )
        if created:
            ctx.count("salary_structures")
            structures[emp.id] = ss

            # Allowances
            SalaryStructureComponent.objects.get_or_create(
                salary_structure=ss, code="HRA",
                defaults={"name": "House Rent Allowance", "component_type": "allowance",
                          "calculation_type": "percent_basic", "percentage": Decimal("30.00")},
            )
            SalaryStructureComponent.objects.get_or_create(
                salary_structure=ss, code="MA",
                defaults={"name": "Medical Allowance", "component_type": "allowance",
                          "calculation_type": "percent_basic", "percentage": Decimal("15.00")},
            )
            SalaryStructureComponent.objects.get_or_create(
                salary_structure=ss, code="TA",
                defaults={"name": "Transport Allowance", "component_type": "allowance",
                          "calculation_type": "fixed", "amount": Decimal("5000")},
            )
            # Deductions
            SalaryStructureComponent.objects.get_or_create(
                salary_structure=ss, code="EOBI",
                defaults={"name": "EOBI", "component_type": "deduction",
                          "calculation_type": "fixed", "amount": Decimal("380")},
            )
            SalaryStructureComponent.objects.get_or_create(
                salary_structure=ss, code="PF",
                defaults={"name": "Provident Fund", "component_type": "deduction",
                          "calculation_type": "percent_basic", "percentage": Decimal("8.33")},
            )

    # Payroll records (3 months per employee)
    pr_count = 0
    for period_name, period in periods.items():
        month_num = int(period.start_date.month)
        year_num = int(period.start_date.year)
        for emp in employees[:80]:
            ss = structures.get(emp.id)
            if not ss:
                continue
            basic = ss.basic_salary
            hra = (basic * Decimal("0.30")).quantize(Decimal("0.01"))
            ma = (basic * Decimal("0.15")).quantize(Decimal("0.01"))
            ta = Decimal("5000")
            eobi = Decimal("380")
            pf = (basic * Decimal("0.0833")).quantize(Decimal("0.01"))
            gross = basic + hra + ma + ta
            deductions = eobi + pf
            net = gross - deductions

            pr, created = PayrollRecord.objects.get_or_create(
                employee=emp,
                payroll_period=period,
                defaults={
                    "campus": emp.primary_campus,
                    "salary_structure": ss,
                    "month": month_num,
                    "year": year_num,
                    "working_days": 26,
                    "paid_days": 26,
                    "basic_salary": basic,
                    "gross_earnings": gross,
                    "total_allowances": hra + ma + ta,
                    "total_deductions": deductions,
                    "gross_salary": gross,
                    "net_salary": net,
                    "status": "paid",
                    "component_details": {
                        "allowances": {"HRA": str(hra), "MA": str(ma), "TA": str(ta)},
                        "deductions": {"EOBI": str(eobi), "PF": str(pf)},
                    },
                },
            )
            if created:
                pr_count += 1
                ctx.count("payroll_records")

    ctx.ok(f"PayrollPeriods: {len(periods)}, SalaryStructures: {len(structures)}, PayrollRecords: {pr_count}")


# ---------------------------------------------------------------------------
# LIBRARY
# ---------------------------------------------------------------------------

def _seed_library(ctx):
    ctx.log("Creating library books, copies, issues...")
    from apps.library.models import Book, BookCopy, BookIssue
    from apps.students.models import Student
    from apps.teachers.models import Teacher

    categories = ["fiction", "science", "math", "textbook", "reference", "literature", "history", "non_fiction"]
    book_data = [
        ("Mathematics for Class {n}", "Author Math", "science"),
        ("English Grammar {n}", "Author Eng", "textbook"),
        ("General Science {n}", "Author Sci", "science"),
        ("Urdu Literature {n}", "Author Urdu", "literature"),
        ("Pakistan Studies {n}", "Author Pak", "history"),
        ("Computer Basics {n}", "Author CS", "reference"),
        ("Islamic Studies {n}", "Author Isl", "non_fiction"),
        ("Story Collection {n}", "Author Story", "fiction"),
    ]

    book_count = 0
    copy_count = 0
    issue_count = 0
    books_list = []

    for campus_code in CAMPUS_CODES:
        campus = ctx.campuses[campus_code]
        for i, (title_tpl, author, cat) in enumerate(book_data):
            for edition in range(1, 3):
                title = title_tpl.format(n=i + 1)
                book, created = Book.objects.get_or_create(
                    institution=ctx.school,
                    campus=campus,
                    title=f"{title} Ed.{edition}",
                    defaults={
                        "author": author,
                        "isbn": f"978-{hash(title) % 9999999:07d}",
                        "category": cat,
                        "publisher": "Demo Publisher",
                        "publication_year": 2024,
                        "total_copies": 3,
                    },
                )
                if created:
                    book_count += 1
                    ctx.count("library_books")
                    books_list.append(book)

                    for copy_idx in range(3):
                        bc = BookCopy.objects.create(
                            book=book,
                            status="available",
                        )
                        copy_count += 1

    # Book issues
    students = list(Student.objects.filter(institution=ctx.school, status="active")[:60])
    teachers_list = list(Teacher.objects.filter(institution=ctx.school)[:20])

    for i, stu in enumerate(students):
        if i >= len(books_list):
            break
        book = books_list[i % len(books_list)]
        copy = book.copies.filter(status="available").first()
        if copy:
            copy.status = "issued"
            copy.save(update_fields=["status"])
            BookIssue.objects.get_or_create(
                book_copy=copy,
                student=stu,
                defaults={
                    "due_date": date(2026, 11, 15),
                    "status": "issued" if random.random() > 0.3 else "returned",
                    "return_date": date(2026, 11, 10) if random.random() > 0.5 else None,
                },
            )
            issue_count += 1

    for i, tch in enumerate(teachers_list):
        if i >= len(books_list):
            break
        book = books_list[(i + 30) % len(books_list)]
        copy = book.copies.filter(status="available").first()
        if copy:
            copy.status = "issued"
            copy.save(update_fields=["status"])
            BookIssue.objects.get_or_create(
                book_copy=copy,
                teacher=tch,
                defaults={
                    "due_date": date(2026, 12, 1),
                    "status": "issued",
                },
            )
            issue_count += 1

    ctx.ok(f"Books: {book_count}, Copies: {copy_count}, Issues: {issue_count}")


# ---------------------------------------------------------------------------
# TRANSPORT
# ---------------------------------------------------------------------------

def _seed_transport(ctx):
    ctx.log("Creating vehicles, drivers, routes, stops, assignments...")
    from apps.transport.models import Vehicle, Driver, Route, RouteStop, TransportAssignment
    from apps.students.models import Student

    vehicles = []
    for i in range(10):
        campus_code = CAMPUS_CODES[i % 5]
        campus = ctx.campuses[campus_code]
        v, created = Vehicle.objects.get_or_create(
            institution=ctx.school,
            plate_number=f"BUS-{i + 1:03d}",
            defaults={
                "campus": campus,
                "model": f"Demo Bus Model {(i % 3) + 1}",
                "capacity": 40,
                "status": "operational" if i < 9 else "maintenance",
            },
        )
        if created:
            ctx.count("vehicles")
            vehicles.append(v)

    drivers = []
    for i in range(10):
        campus_code = CAMPUS_CODES[i % 5]
        campus = ctx.campuses[campus_code]
        d, created = Driver.objects.get_or_create(
            institution=ctx.school,
            license_number=f"DL-{1000 + i:06d}",
            defaults={
                "first_name": f"Driver",
                "last_name": f"{i + 1:02d}",
                "phone": f"0321{i:07d}",
                "campus": campus,
                "status": True,
            },
        )
        if created:
            ctx.count("drivers")
            drivers.append(d)

    routes = []
    route_stops_data = [
        ["Main Gate", "City Center", "Hospital Chowk", "School Road"],
        ["Station Road", "Market Area", "Park Lane", "Campus Gate"],
        ["Highway Stop", "Town Square", "Library Road", "School Gate"],
    ]
    for i, v in enumerate(vehicles):
        campus_code = CAMPUS_CODES[i % 5]
        campus = ctx.campuses[campus_code]
        driver = drivers[i] if i < len(drivers) else None
        route, created = Route.objects.get_or_create(
            institution=ctx.school,
            name=f"Route {i + 1:03d} - {campus_code}",
            defaults={
                "campus": campus,
                "vehicle": v,
                "driver": driver,
                "start_point": f"Start Point {campus_code}",
                "end_point": f"{campus.name}",
                "status": True,
            },
        )
        if created:
            ctx.count("routes")
            routes.append(route)
            stops = route_stops_data[i % len(route_stops_data)]
            for j, stop_name in enumerate(stops):
                RouteStop.objects.get_or_create(
                    route=route,
                    name=stop_name,
                    defaults={"order": j + 1, "time": time(7 + j // 2, (j % 2) * 30)},
                )

    # Transport assignments
    ta_count = 0
    students = list(Student.objects.filter(institution=ctx.school, status="active")[:100])
    for i, stu in enumerate(students):
        if not routes:
            break
        route = routes[i % len(routes)]
        stops = list(route.stops.all())
        stop = stops[i % len(stops)] if stops else None
        ta, created = TransportAssignment.objects.get_or_create(
            student=stu,
            route=route,
            defaults={"stop": stop, "status": "active"},
        )
        if created:
            ta_count += 1
            ctx.count("transport_assignments")

    ctx.ok(f"Vehicles: {len(vehicles)}, Drivers: {len(drivers)}, Routes: {len(routes)}, Assignments: {ta_count}")


# ---------------------------------------------------------------------------
# INVENTORY / ASSETS
# ---------------------------------------------------------------------------

def _seed_inventory(ctx):
    ctx.log("Creating asset categories, suppliers, assets, maintenance...")
    from apps.inventory.models import (
        AssetCategory, Supplier, Asset, AssetAssignment, MaintenanceRecord, StockLevel, StockMovement,
    )
    from apps.teachers.models import Teacher

    categories_data = [
        ("IT-EQ", "IT Equipment"),
        ("FURN", "Furniture"),
        ("SCIF", "Science Lab Equipment"),
        ("SPRT", "Sports Equipment"),
        ("ELEC", "Electrical Equipment"),
        ("PRNT", "Printing Equipment"),
        ("LNCH", "Laboratory"),
    ]
    categories = {}
    for code, name in categories_data:
        cat, _ = getc(
            AssetCategory,
            institution=ctx.school,
            name=name,
            defaults={"description": f"Category: {name}"},
        )
        categories[code] = cat
        ctx.count("asset_categories")

    suppliers_data = [
        ("SUP-001", "Tech Solutions Ltd."),
        ("SUP-002", "Furniture House"),
        ("SUP-003", "Science Equipment Co."),
        ("SUP-004", "Sports World"),
        ("SUP-005", "Office Supplies Inc."),
    ]
    suppliers = {}
    for code, name in suppliers_data:
        sup, _ = getc(
            Supplier,
            institution=ctx.school,
            name=name,
            defaults={
                "contact_person": f"Contact {name}",
                "phone": f"0300{hash(name) % 9999999:07d}",
                "email": f"info@{name.lower().replace(' ', '')}.test",
                "status": "active",
            },
        )
        suppliers[code] = sup
        ctx.count("suppliers")

    # Assets (100 total, spread across campuses)
    asset_data = [
        "Desktop Computer", "Laptop", "Projector", "Printer", "Whiteboard",
        "Desk", "Chair", "Bookshelf", "Lab Microscope", "Sports Kit",
    ]
    asset_count = 0
    teachers = list(Teacher.objects.filter(institution=ctx.school, primary_campus__isnull=False)[:50])
    for i in range(100):
        campus_code = CAMPUS_CODES[i % 5]
        campus = ctx.campuses[campus_code]
        cat_code = list(categories.keys())[i % len(categories)]
        asset_name = f"{asset_data[i % len(asset_data)]} #{i + 1:03d}"
        teacher = teachers[i % len(teachers)] if teachers else None

        asset, created = Asset.objects.get_or_create(
            institution=ctx.school,
            asset_id=f"ASSET-{i + 1:04d}",
            defaults={
                "name": asset_name,
                "category": categories[cat_code],
                "campus": campus,
                "description": f"Demo asset: {asset_name}",
                "purchase_date": date(2024 + (i % 3), (i % 12) + 1, 1),
                "purchase_cost": Decimal(str(random.choice([15000, 25000, 50000, 75000, 120000]))),
                "current_value": Decimal(str(random.choice([10000, 20000, 40000, 60000, 100000]))),
                "status": "active" if i < 90 else "maintenance",
            },
        )
        if created:
            asset_count += 1
            ctx.count("assets")

            if teacher and i < 40:
                AssetAssignment.objects.get_or_create(
                    asset=asset,
                    defaults={
                        "assigned_to_user": teacher.user,
                        "assigned_date": date(2026, 9, 1),
                        "status": "active",
                    },
                )

    # Maintenance records
    mr_count = 0
    vehicles = list(
        __import__("apps.transport.models", fromlist=["Vehicle"]).Vehicle.objects.filter(
            institution=ctx.school
        )[:10]
    )
    maint_types = ["Oil change", "Tire replacement", "Engine service", "General inspection", "Repair work"]
    for i, v in enumerate(vehicles):
        for j in range(2):
            MaintenanceRecord.objects.get_or_create(
                vehicle=v,
                defaults={
                    "maintenance_type": maint_types[(i + j) % len(maint_types)],
                    "description": f"Maintenance record {j + 1} for {v.plate_number}",
                    "cost": Decimal(str(random.choice([5000, 10000, 25000, 40000]))),
                    "status": "completed",
                    "maintenance_date": date(2026, 9 + (i % 4), 5 + j * 10),
                },
            )
            mr_count += 1
            ctx.count("maintenance_records")

    # Stock levels
    stock_items = ["Chalk", "Markers", "Paper Ream", "Pens", "Notebooks", "Cleaning Spray", "Bulbs", "Cables"]
    for item_name in stock_items:
        campus_code = CAMPUS_CODES[hash(item_name) % 5]
        campus = ctx.campuses[campus_code]
        sl, created = StockLevel.objects.get_or_create(
            institution=ctx.school,
            item_name=item_name,
            campus=campus,
            defaults={
                "quantity": random.randint(10, 200),
                "minimum_level": 20,
                "unit": "pcs",
            },
        )
        if created:
            ctx.count("stock_levels")

    ctx.ok(f"Assets: {asset_count}, Maintenance: {mr_count}, StockLevels: {ctx.counts.get('stock_levels', 0)}")


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------

@transaction.atomic
def run(ctx):
    ctx.log("Part 4: assets (HR, payroll, library, transport, inventory).")
    _seed_hr(ctx)
    _seed_payroll(ctx)
    _seed_library(ctx)
    _seed_transport(ctx)
    _seed_inventory(ctx)
    ctx.ok("Part 4 done.")
