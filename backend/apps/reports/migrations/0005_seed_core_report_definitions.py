"""Seed the ReportCategory + ReportDefinition rows for the 25 core reports.

The PDF/Print exporters require an active ``ReportDefinition`` matching the
report key (``PDFExportView`` returns 404 otherwise).  The legacy top-level
reports served by ReportsPage were never registered, so this migration
creates them so ``pdf/<key>/`` and ``print/<key>/`` work out of the box.

``report_type`` values mirror ``ReportDefinition.REPORT_TYPE_CHOICES`` so a
default ``ReportTemplate`` per type can be looked up later.
"""

from django.db import migrations

CORE_KEYS = [
    "enrollment",
    "attendance",
    "chronic-absentee",
    "results",
    "top-performers",
    "class-performance",
    "student-progress",
    "subjects",
    "fees",
    "fee-defaulters",
    "collection-trend",
    "discounts",
    "payments",
    "fee-categories",
    "payroll-summary",
    "staff",
    "teacher-workload",
    "student-status",
    "library",
    "route-utilization",
    "inventory-value",
    "maintenance-due",
    "event-participation",
    "sms-usage",
    "at-risk",
]

# key -> (title, report_type, description)
DEFINITIONS = {
    "enrollment": ("Enrollment Report", "enrollment",
                   "Students, classes and average class size per campus."),
    "attendance": ("Attendance Report", "attendance",
                   "Attendance records grouped by campus and class."),
    "chronic-absentee": ("Chronic Absentees", "chronic_absentee",
                         "Students whose attendance rate falls below a threshold."),
    "results": ("Results Report", "results",
                "Exam results, pass rates and averages per student."),
    "top-performers": ("Top Performers", "top_performers",
                       "Highest scoring students across classes."),
    "class-performance": ("Class Performance", "class_performance",
                          "Performance snapshot per class."),
    "student-progress": ("Student Progress", "student_progress",
                         "Exam progress trend for an individual student."),
    "subjects": ("Subject Performance", "subjects",
                 "Result averages and pass rates per subject."),
    "fees": ("Fees Report", "fees",
             "Invoiced, collected and outstanding fees per campus."),
    "fee-defaulters": ("Fee Defaulters", "fee_defaulters",
                       "Students with outstanding invoice balances."),
    "collection-trend": ("Collection Trend", "collection_trend",
                         "Monthly invoiced vs collected fee amounts."),
    "discounts": ("Discounts & Concessions", "discounts",
                  "Invoice discounts and concessions applied."),
    "payments": ("Payment Methods", "payments",
                 "Payments grouped by method and campus."),
    "fee-categories": ("Fee Categories", "fee_categories",
                       "Invoiced totals per fee category."),
    "payroll-summary": ("Payroll Summary", "payroll_summary",
                        "Payroll totals per period and campus."),
    "staff": ("Staff Report", "staff",
              "Staff grouped by campus and designation."),
    "teacher-workload": ("Teacher Workload", "teacher_workload",
                         "Teaching assignments per teacher."),
    "student-status": ("Student Status", "student_status",
                       "Students grouped by enrolment status per campus."),
    "library": ("Library Overview", "library_overview",
                "Issue totals, overdue books and fines."),
    "route-utilization": ("Route Utilization", "route_utilization",
                          "Transport capacity and occupancy per route."),
    "inventory-value": ("Inventory Value", "inventory_value",
                        "Stock quantity and value per category/campus."),
    "maintenance-due": ("Maintenance Due", "maintenance_due",
                        "Asset maintenance records and costs."),
    "event-participation": ("Event Participation", "event_participation",
                            "Attendance responses per event."),
    "sms-usage": ("SMS Usage", "sms_usage",
                  "SMS send counts per month."),
    "at-risk": ("At-Risk Students", "at_risk",
                "Early-warning composite: attendance, fees and discipline."),
}


def seed_core_definitions(apps, schema_editor):
    ReportCategory = apps.get_model("reports", "ReportCategory")
    ReportDefinition = apps.get_model("reports", "ReportDefinition")

    category, _ = ReportCategory.objects.get_or_create(
        slug="core-reports",
        defaults={
            "name": "Core Reports",
            "description": "Standard school-wide reports.",
            "order": 0,
            "is_active": True,
        },
    )

    for order, key in enumerate(CORE_KEYS):
        title, report_type, description = DEFINITIONS[key]
        ReportDefinition.objects.update_or_create(
            key=key,
            defaults={
                "category": category,
                "title": title,
                "description": description,
                "report_type": report_type,
                "endpoint_url": f"/api/reports/{key}/",
                "supports_csv": True,
                "supports_pdf": True,
                "supports_print": True,
                "supports_excel": False,
                "supports_schedule": False,
                "is_active": True,
                "order": order,
            },
        )


def unseed_core_definitions(apps, schema_editor):
    ReportCategory = apps.get_model("reports", "ReportCategory")
    ReportDefinition = apps.get_model("reports", "ReportDefinition")

    ReportDefinition.objects.filter(key__in=CORE_KEYS).delete()

    category = ReportCategory.objects.filter(slug="core-reports").first()
    if category is not None and not category.report_definitions.exists():
        category.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0004_customreportdatasource_reportcategory_and_more"),
    ]

    operations = [
        migrations.RunPython(
            seed_core_definitions,
            unseed_core_definitions,
        ),
    ]