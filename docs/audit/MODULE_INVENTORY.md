# MODULE_INVENTORY.md

**Date:** 2026-08-30
**Owner:** Developer 1

Live inventory of backend apps. Data from source scan (models = `^class` defs in models.py; urls = path entries; views = DRF CBVs/FBVs). `*` beside app = no tests.

## Core & Platform

| App | Models | URLs | Views | Purpose | Notes |
|---|---|---|---|---|---|
| accounts | 15 | ~33 | 36 | Auth, users, roles, perms, staff profiles/attendance | Large files (models 1036, views 1364). 3 test files. |
| schools | 14 | 19 | 10 (+2 ViewSets) | Tenant (School/Campus/AcademicUnit/Class/Section/Year/Term/Subject) + white-label media | 21 migrations. 2 test files (incl. tenant isolation). |
| core | 6 mixins | 0 | 1 FBV | SoftDelete/TimeStamped/Campus/Institution/Auditable mixins | Only SoftDelete used. No migrations. |
| audit | 1 | 2 | 3 | AuditLog + record_audit helper | 4 indexes. No tests.* |
| dashboard | 0 | 6 | 6 FBV | Aggregated dashboard endpoints | No models. 1 test. |
| search | 0 | 1 | 1 | Cross-module search | No tests.* |
| white_label | 4 | 10 | 8 | White-label branding + DomainMapping | Has its own SchoolSettings (dup). 1 test. |
| workflow | 4 | 11 | 11 | Approval/workflow state machine | Hand-rolled polymorphism. 1 test. |

## SIS & Academics

| App | Models | URLs | Views | Purpose | Notes |
|---|---|---|---|---|---|
| students | 16 | 56 | 51 | Students, guardians, admissions, enrollments, transfers, life-cycle | Large files (models 1682, serializers 1547, views 1306). 11 migrations. 1 test. Soft-delete used. |
| teachers | 2 | 6 | 5 | Teacher profiles + assignments | 9 migrations. 1 test. Soft-delete used. |
| attendance | 2 | 10 | 9 | Student attendance + corrections | 3 migrations. 1 test. |
| exams | 5 | 9 | 9 | Exams, results, schedules | 5 migrations. 3 test files. Empty admin.py (0 bytes). |
| reportcards | 5 | 7 | 7 | Report cards + grade scales | 5 migrations. 2 test files. |
| timetable | 2 | 4 | 3 | Periods + timetable entries | 2 migrations. 1 test. |
| events | 3 | 3 | 3 | School events/audience/RSVP | 2 migrations. 1 test. |
| discipline | 2 | 4 | 4 | Incidents + actions | No tests.* |
| health | 1 | 2 | 2 | Health records | No tests.* |
| homework | 2 | 4 | 4 | Homework + submissions | No tests.* |
| lms | 6 | 13 | 5 | Courses/lessons/quizzes | No tests.* |
| hostel | 3 | 5 | 5 | Hostel/rooms/allocation | No tests.* |
| library | 3 | 5 | 5 | Books/copies/issues | 4 migrations. 1 test. |
| transport | 6 | 10 | 8 | Fleet/routes/assignments/vehicle location | No tests.* |
| digital_ids | 1 | 4 | 5 | Student/staff ID cards | 1 test. |
| documents | 0 | 2 | 2 | Aggregated document listing (polymorphic) | No models. No migrations. No tests.* |

## Finance, HR, Payroll

| App | Models | URLs | Views | Purpose | Notes |
|---|---|---|---|---|---|
| finance | 19 | 64 | 57 | Fees, invoices, payments, accounting, budgets, concessions, adjustments | Large files (models 1441, views 1789, tests 1525). 9 migrations. Soft-delete used. 1 test. |
| hr | 26 | 60 | 54 | Departments, employees, leave, recruitment, performance, contracts | Large files (models 1710, views 1113). 4 migrations. 1 test. |
| payroll | 5 | 11 | 9 | Salary structures, pay records, payslips | 5 migrations. No tests.* |

## Communication & Engagement

| App | Models | URLs | Views | Purpose | Notes |
|---|---|---|---|---|---|
| communication | 9 | 20 | 10 | Messages, announcements, notifications, SMS/email logs | 10 migrations. 1 test. |
| portal | 0 | 3 | 12 FBV | Role-portal aggregation (teacher/student) | No models. 1 test. |
| alumni | 1 | 2 | 2 | Alumni tracking | No tests.* |
| helpdesk | 3 | 10 | 10 | Support tickets | 1 test. |
| visitors | 1 | 4 | 5 | Visitor management | 1 test. |

## Reporting

| App | Models | URLs | Views | Purpose | Notes |
|---|---|---|---|---|---|
| reports | 8 | **167** | 16+11 | Report engine (categories, definitions, templates, scheduled, custom data sources, 100+ report views) | Largest route table (392-line urls.py). views.py 1534, extended_views 1165. 4 migrations. **No tests.*** |

## Totals

- Apps: 33
- Models: 182 (declared)
- Migrations: 138
- URL routes (backend): ~528 `path()`/`re_path()` entries (167 in reports alone)
- Apps with **zero tests (12):** alumni, audit, discipline, documents, health, homework, hostel, lms, payroll, reports, search, transport

## Frontend Pages (src/pages, ~59 files)

Dashboard, Students, Finance (Fees, Invoices, Payments, Accounting), HR, Payroll, Attendance, Exams, Report Cards, Timetable, Events, Communication, Reports (with 15+ report types), Search, Library, Transport, Inventory, Documents, Discipline, Health, Hostel, LMS, Homework, Alumni, Workflow, White Label, Helpdesk, Visitors, Digital IDs, Portal pages (teacher/student/parent), Platform/Tenant admin, Admissions (apply), plus `ui.jsx`, `useApiList.js`, `format.js`.

## Notes for Developer 2 Contract

- `documents`, `portal`, `search`, `dashboard`, `core` are utility apps with **no tables** — freeze list so developer 2 does not expect tables.
- `reports` is the reserved read-only surface: Developer 2 may consume endpoints but must not add ad-hoc DB columns without a co-signed migration from Developer 1.
- `finance`/`hr`/`payroll` heavy modules: schema changes in these modules require Developer 1 review first.