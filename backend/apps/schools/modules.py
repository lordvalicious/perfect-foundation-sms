"""Canonical ERP module registry for white-label module toggling.

``MODULE_PREFIXES`` maps URL prefixes under ``/api/`` to a module key.
When a school disables a module, every prefixed API becomes 403 for
that school's users (platform admins bypass). Unmapped prefixes are
core SIS and always available.
"""

MODULE_PREFIXES = {
    "payroll/": "payroll",
    "library/": "library",
    "transport/": "transport",
    "inventory/": "inventory",
    "hostel/": "hostel",
    "lms/": "lms",
    "homework/": "homework",
    "events/": "events",
    "discipline/": "discipline",
    "health-records/": "health",
    "alumni/": "alumni",
    "hr/": "hr",
    "communication/": "communication",
    "helpdesk/": "helpdesk",
    "visitors/": "visitors",
    "digital-ids/": "digital_ids",
}

ALL_MODULES = [
    "students",
    "attendance",
    "exams",
    "finance",
    "payroll",
    "hr",
    "library",
    "transport",
    "inventory",
    "hostel",
    "lms",
    "homework",
    "events",
    "discipline",
    "health",
    "alumni",
    "communication",
    "helpdesk",
    "visitors",
    "digital_ids",
    "reports",
]


def module_for_path(path_after_api):
    """Return the module key owning this path, or None (core/open)."""
    path = (path_after_api or "").lstrip("/")

    for prefix, module in MODULE_PREFIXES.items():
        if path.startswith(prefix):
            return module

    return None
