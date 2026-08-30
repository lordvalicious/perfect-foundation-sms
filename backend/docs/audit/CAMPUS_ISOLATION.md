# Campus Isolation Documentation

## Overview

Campus- and institution-isolation ensures that users at one campus can only access records belonging to their own campus, while global administrators (SUPER_ADMIN) can see all records within the active institution. This is enforced through the middleware chain and queryset filtering.

## Middleware Chain

The request processing middleware chain enforces isolation:

1. `AuthenticationMiddleware` - Establishes `request.user`
2. `ActiveInstitutionMiddleware` - Sets `request.institution` from the active institution context
3. `CampusAccessMiddleware` - Filters querysets by `campus_id` based on the authenticated user's campus assignment
4. `ModuleAccessMiddleware` - Further restricts access for academic roles to only their assigned modules

## Exempt Paths

`CAMPUS_VALIDATION_EXEMPT_PATHS` defines URL patterns that bypass campus validation (typically authentication/public endpoints).

## Authorization Enforcement

- **Quadrant 1 - Campus Admin**: Can read/manage only their own campus records. `404` returned for foreign campus records.
- **Quadrant 2 - Super Admin**: Can see all records within the active institution across all campuses.
- **Quadrant 3 - Other roles**: Access restricted based on `StaffProfile.primary_campus` or `StaffProfile.institution`.
- **Quadrant 4 - Student/Parent**: Self-service access to own records only.

## Testing

The isolation test suite (`test_campus_isolation.py`) contains 22 green tests under SQLite, verifying:

- Campus admin can read own campus students/subjects/invoices/docs
- Campus admin cannot read other campus records (returns 404)
- Super admin can read any campus records
- Search endpoints respect campus isolation
- Dashboard/finance/exams results are campus-scoped
- Document upload/download is campus-scoped

## Database Note

Local development uses SQLite in-memory (`DATABASE_URL=$null; DB_ENGINE='django.db.backends.sqlite3'`). Full 137-account suite has environment-dependent throttle-lockout state issues that are isolated to the production Neon Postgres environment.

## APIs Affected

- `/api/students/` - List and detail scoped to campus
- `/api/exams/results/` - Results scoped via `enrollment__campus_id`
- `/api/finance/invoices/` - Invoices scoped to enrollment campus
- `/api/documents/` - Upload/list scoped to campus
- `/api/search/` - Subject/staff/student search isolated by campus
- `/api/dashboard/overview/`, `/finance/`, `/exams/` - All campus-scoped