# Batch 2: Parents, Library, Transport, Inventory, Discipline, Certificates, Campus, Builder
from apps.reports.models import ReportCategory, ReportDefinition

# Parents & Guardians
cat_par = ReportCategory.objects.get(slug='parents')
reports_par = [
    ('parent-master', 'Parent Master', 'Guardian directory with contact details', 'parents/master/', 'Users'),
    ('parent-relationship', 'Parent-Student Relationships', 'Primary/emergency/pickup contacts per student', 'parents/relationship/', 'Users'),
    ('parent-contact', 'Parent Contact Report', 'Phone/email/address with missing contact flags', 'parents/contact/', 'Mail'),
    ('parent-students', 'Parent-wise Students', 'Students grouped by parent with class details', 'parents/students/', 'Users'),
    ('parent-outstanding-fees', 'Outstanding Fees by Parent', 'Total dues per guardian across all children', 'parents/outstanding-fees/', 'Wallet'),
    ('parent-attendance', 'Attendance Summary by Parent', "Children's attendance rates grouped by parent", 'parents/attendance/', 'ClipboardCheck'),
    ('parent-academic', 'Academic Summary by Parent', "Children's exam performance grouped by parent", 'parents/academic/', 'Trophy'),
]
for key, title, desc, endpoint, icon in reports_par:
    ReportDefinition.objects.get_or_create(
        key=key,
        defaults={
            'category': cat_par,
            'title': title,
            'description': desc,
            'report_type': key.replace('-', '_'),
            'endpoint_url': '/api/reports/' + endpoint,
            'supports_csv': True,
            'supports_pdf': True,
            'supports_print': True,
            'required_roles': ['super_admin', 'admin', 'principal', 'vice_principal', 'campus_admin', 'academic'],
        }
    )

# Library
cat_lib = ReportCategory.objects.get(slug='library')
reports_lib = [
    ('library-inventory', 'Book Inventory', 'Total books, copies, available/issued by category', 'library/inventory/', 'BookOpen'),
    ('library-available', 'Available Books', 'Currently available copies with locations', 'library/available/', 'CheckCircle'),
    ('library-issued', 'Issued Books', 'Currently issued/overdue books with borrower details', 'library/issued/', 'BookOpen'),
    ('library-returned', 'Returned Books', 'Returned books with late return analysis', 'library/returned/', 'BookOpen'),
    ('library-overdue', 'Overdue Books', 'Overdue books with days overdue and fines', 'library/overdue/', 'Siren'),
    ('library-fines', 'Library Fines', 'Fines outstanding/paid with borrower details', 'library/fines/', 'Wallet'),
    ('library-activity', 'Library Activity Summary', 'Total issues, returns, overdue, fines, most borrowed', 'library/activity/', 'BarChart3'),
    ('library-most-borrowed', 'Most Borrowed Books', 'Top borrowed titles with issue counts', 'library/most-borrowed/', 'Trophy'),
    ('library-student-history', 'Student Borrowing History', 'Complete issue/return history for a student', 'library/student-history/', 'FileText'),
    ('library-teacher-history', 'Teacher Borrowing History', 'Complete issue/return history for a teacher', 'library/teacher-history/', 'FileText'),
]
for key, title, desc, endpoint, icon in reports_lib:
    ReportDefinition.objects.get_or_create(
        key=key,
        defaults={
            'category': cat_lib,
            'title': title,
            'description': desc,
            'report_type': key.replace('-', '_'),
            'endpoint_url': '/api/reports/' + endpoint,
            'supports_csv': True,
            'supports_pdf': True,
            'supports_print': True,
            'required_roles': ['super_admin', 'admin', 'principal', 'vice_principal', 'campus_admin', 'academic', 'librarian'],
        }
    )

# Transport
cat_trans = ReportCategory.objects.get(slug='transport')
reports_trans = [
    ('transport-students', 'Student Transport List', 'Students with route, vehicle, driver, pickup/drop points', 'transport/students/', 'Users'),
    ('transport-routes', 'Route Report', 'Route details with vehicle, driver, stops, utilization', 'transport/routes/', 'Bus'),
    ('transport-vehicles', 'Vehicle Report', 'Vehicles with capacity, status, routes, insurance/fitness', 'transport/vehicles/', 'Truck'),
    ('transport-drivers', 'Driver Report', 'Drivers with license, vehicle, routes, assigned students', 'transport/drivers/', 'Users'),
    ('transport-pickup-dropoff', 'Pickup/Drop-off Points', 'All pickup and drop points with times', 'transport/pickup-dropoff/', 'MapPin'),
    ('transport-students-by-route', 'Students by Route', 'Student lists grouped by route', 'transport/students-by-route/', 'Users'),
    ('transport-students-by-vehicle', 'Students by Vehicle', 'Student lists grouped by vehicle', 'transport/students-by-vehicle/', 'Truck'),
    ('transport-fees', 'Transport Fees', 'Monthly transport fees by student/route', 'transport/fees/', 'Wallet'),
    ('transport-vehicle-capacity', 'Vehicle Capacity', 'Capacity utilization per vehicle', 'transport/vehicle-capacity/', 'BarChart3'),
    ('transport-route-occupancy', 'Route Occupancy', 'Route capacity vs assigned students, overloaded routes', 'transport/route-occupancy/', 'BarChart3'),
]
for key, title, desc, endpoint, icon in reports_trans:
    ReportDefinition.objects.get_or_create(
        key=key,
        defaults={
            'category': cat_trans,
            'title': title,
            'description': desc,
            'report_type': key.replace('-', '_'),
            'endpoint_url': '/api/reports/' + endpoint,
            'supports_csv': True,
            'supports_pdf': True,
            'supports_print': True,
            'required_roles': ['super_admin', 'admin', 'principal', 'vice_principal', 'campus_admin', 'accountant'],
        }
    )

# Inventory
cat_inv = ReportCategory.objects.get(slug='inventory')
reports_inv = [
    ('inventory-master', 'Inventory Master', 'All assets with category, campus, quantity, value', 'inventory/master/', 'Package'),
    ('inventory-stock', 'Current Stock', 'Available stock by item/category/campus', 'inventory/stock/', 'Package'),
    ('inventory-low-stock', 'Low Stock', 'Items below reorder threshold', 'inventory/low-stock/', 'Siren'),
    ('inventory-out-of-stock', 'Out of Stock', 'Items with zero quantity', 'inventory/out-of-stock/', 'X'),
    ('inventory-movement', 'Stock Movement', 'Inward/outward/transfer movements by date range', 'inventory/movement/', 'ArrowRightLeft'),
    ('inventory-purchases', 'Purchases', 'Purchase orders with supplier, amount, status', 'inventory/purchases/', 'ShoppingCart'),
    ('inventory-issues', 'Issues', 'Assets issued to staff/students with return tracking', 'inventory/issues/', 'ArrowRight'),
    ('inventory-returns', 'Returns', 'Asset returns with condition assessment', 'inventory/returns/', 'ArrowLeft'),
    ('inventory-damaged', 'Damaged Items', 'Assets marked damaged with value', 'inventory/damaged/', 'AlertTriangle'),
    ('inventory-lost', 'Lost Items', 'Assets marked lost with value', 'inventory/lost/', 'AlertTriangle'),
    ('inventory-category', 'Category Report', 'Item counts and values by category', 'inventory/category/', 'BarChart3'),
    ('inventory-supplier', 'Supplier Report', 'Assets and purchase values by supplier', 'inventory/supplier/', 'Truck'),
    ('inventory-valuation', 'Inventory Valuation', 'Total asset value by category and campus', 'inventory/valuation/', 'Wallet'),
]
for key, title, desc, endpoint, icon in reports_inv:
    ReportDefinition.objects.get_or_create(
        key=key,
        defaults={
            'category': cat_inv,
            'title': title,
            'description': desc,
            'report_type': key.replace('-', '_'),
            'endpoint_url': '/api/reports/' + endpoint,
            'supports_csv': True,
            'supports_pdf': True,
            'supports_print': True,
            'required_roles': ['super_admin', 'admin', 'principal', 'vice_principal', 'campus_admin', 'accountant'],
        }
    )

# Discipline
cat_disc = ReportCategory.objects.get(slug='discipline')
reports_disc = [
    ('discipline-incidents', 'Discipline Incidents', 'All incidents with type, severity, action taken', 'discipline/incidents/', 'Siren'),
    ('discipline-student', 'Student Incidents', 'Incidents grouped by student with counts', 'discipline/student/', 'Users'),
    ('discipline-class', 'Class Incidents', 'Incident counts by class with type breakdown', 'discipline/class/', 'Users'),
    ('discipline-campus', 'Campus Incidents', 'Incident counts and severity by campus', 'discipline/campus/', 'MapPin'),
    ('discipline-type', 'Incident Type Breakdown', 'Counts by incident type and severity', 'discipline/type/', 'BarChart3'),
    ('discipline-date-range', 'Date Range Incidents', 'Incidents within a specific date range', 'discipline/date-range/', 'CalendarDays'),
    ('discipline-warnings', 'Warnings', 'All warning-level incidents', 'discipline/warnings/', 'AlertTriangle'),
    ('discipline-suspensions', 'Suspensions', 'All suspension incidents with action taken', 'discipline/suspensions/', 'UserX'),
    ('discipline-repeat', 'Repeat Offenders', 'Students with multiple incidents', 'discipline/repeat/', 'Siren'),
    ('discipline-history', 'Disciplinary History', 'Complete incident timeline for a student', 'discipline/history/', 'FileText'),
]
for key, title, desc, endpoint, icon in reports_disc:
    ReportDefinition.objects.get_or_create(
        key=key,
        defaults={
            'category': cat_disc,
            'title': title,
            'description': desc,
            'report_type': key.replace('-', '_'),
            'endpoint_url': '/api/reports/' + endpoint,
            'supports_csv': True,
            'supports_pdf': True,
            'supports_print': True,
            'required_roles': ['super_admin', 'admin', 'principal', 'vice_principal', 'campus_admin', 'academic'],
        }
    )

# Certificates
cat_cert = ReportCategory.objects.get(slug='certificates')
reports_cert = [
    ('certificate-bonafide', 'Bonafide Certificate', 'Proof of enrollment certificate', 'certificates/bonafide/', 'FileText'),
    ('certificate-character', 'Character Certificate', 'Good conduct certificate', 'certificates/character/', 'FileText'),
    ('certificate-leaving', 'Leaving Certificate', 'School leaving certificate', 'certificates/leaving/', 'FileText'),
    ('certificate-transfer', 'Transfer Certificate', 'Inter-school transfer certificate', 'certificates/transfer/', 'FileText'),
    ('certificate-enrollment', 'Enrollment Certificate', 'Current enrollment verification', 'certificates/enrollment/', 'FileText'),
    ('certificate-fee-clearance', 'Fee Clearance Certificate', 'No dues certificate', 'certificates/fee-clearance/', 'FileText'),
    ('certificate-student-id', 'Student ID Card', 'Photo ID card with barcode', 'certificates/student-id/', 'Badge'),
    ('certificate-staff-id', 'Staff ID Card', 'Staff photo ID card with barcode', 'certificates/staff-id/', 'Badge'),
    ('certificate-templates', 'Certificate Templates', 'Manage certificate templates', 'certificates/templates/', 'Settings'),
]
for key, title, desc, endpoint, icon in reports_cert:
    ReportDefinition.objects.get_or_create(
        key=key,
        defaults={
            'category': cat_cert,
            'title': title,
            'description': desc,
            'report_type': key.replace('-', '_'),
            'endpoint_url': '/api/reports/' + endpoint,
            'supports_csv': True,
            'supports_pdf': True,
            'supports_print': True,
            'required_roles': ['super_admin', 'admin', 'principal', 'vice_principal', 'campus_admin', 'academic'],
        }
    )

# Campus Reports
cat_camp = ReportCategory.objects.get(slug='campus')
reports_camp = [
    ('campus-students', 'Campus Student Count', 'Student totals with gender breakdown by campus', 'campus/students/', 'Users'),
    ('campus-attendance', 'Campus Attendance', 'Attendance rate comparison across campuses', 'campus/attendance/', 'ClipboardCheck'),
    ('campus-performance', 'Campus Academic Performance', 'Pass rates, averages, grade distribution by campus', 'campus/performance/', 'Trophy'),
    ('campus-fees', 'Campus Fee Collection', 'Invoiced, collected, outstanding by campus', 'campus/fees/', 'Wallet'),
    ('campus-outstanding', 'Campus Outstanding Fees', 'Outstanding fee totals by campus', 'campus/outstanding/', 'Siren'),
    ('campus-staff', 'Campus Staff Count', 'Staff totals with teaching/admin breakdown', 'campus/staff/', 'Users'),
    ('campus-admissions', 'Campus Admissions', 'Applications, accepted, pending by campus', 'campus/admissions/', 'GraduationCap'),
    ('campus-finance', 'Campus Financial Summary', 'Revenue, expenses, net by campus', 'campus/finance/', 'Wallet'),
    ('campus-comparison', 'Campus Comparison', 'Side-by-side KPI comparison', 'campus/comparison/', 'BarChart3'),
    ('campus-dashboard', 'Campus Dashboard', 'Single campus overview with all KPIs', 'campus/dashboard/', 'LayoutDashboard'),
]
for key, title, desc, endpoint, icon in reports_camp:
    ReportDefinition.objects.get_or_create(
        key=key,
        defaults={
            'category': cat_camp,
            'title': title,
            'description': desc,
            'report_type': key.replace('-', '_'),
            'endpoint_url': '/api/reports/' + endpoint,
            'supports_csv': True,
            'supports_pdf': True,
            'supports_print': True,
            'required_roles': ['super_admin', 'admin', 'principal', 'vice_principal', 'campus_admin', 'accountant'],
        }
    )

# Report Builder
cat_builder = ReportCategory.objects.get(slug='builder')
reports_builder = [
    ('builder-data-sources', 'Available Data Sources', 'Browse approved data sources with fields and filters', 'builder/data-sources/', 'Database'),
    ('builder-create', 'Create Custom Report', 'Select fields, add filters, grouping, sorting', 'builder/create/', 'Plus'),
    ('builder-saved', 'My Saved Reports', 'Manage and run saved custom reports', 'builder/saved/', 'Star'),
    ('builder-templates', 'Report Templates', 'Manage PDF/print templates', 'builder/templates/', 'FileText'),
]
for key, title, desc, endpoint, icon in reports_builder:
    ReportDefinition.objects.get_or_create(
        key=key,
        defaults={
            'category': cat_builder,
            'title': title,
            'description': desc,
            'report_type': key.replace('-', '_'),
            'endpoint_url': '/api/reports/' + endpoint,
            'supports_csv': True,
            'supports_pdf': True,
            'supports_print': True,
            'required_roles': ['super_admin', 'admin', 'principal', 'vice_principal', 'campus_admin', 'academic'],
        }
    )

print("Batch 2 completed!")
print(f"Total ReportDefinitions: {ReportDefinition.objects.count()}")