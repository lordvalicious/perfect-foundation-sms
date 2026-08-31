# ERP_MODULE_AUDIT — Perfect Foundation SMS

Audit date: 2026-08-30 · Auditor: Developer 2 · Frontend-facing view of every ERP module. Backend pairing is Developer 1; this table captures what the UI exposes and its completeness.

## 1. Module registry (authoritative source: `backend/apps/schools/modules.py`)

`MODULE_PREFIXES` maps `/api/<prefix>/` → module key; disabled modules become 403 for that school. The frontend consumes keys via `Shell()` → `/api/schools/modules/current/` and hides nav entries whose module is disabled.

Module keys (21): `students, attendance, exams, finance, payroll, hr, library, transport, inventory, hostel, lms, homework, events, discipline, health, alumni, communication, helpdesk, visitors, digital_ids, reports`.

Special: `schools, accounts, audit, dashboard, documents, portal, reportcards, search, timetable, workflow, reports(center)`, `white_label` are core/unmapped and always available (frontend `Documents`, `Timetable`, `Reports`, `Tenants` pages rely on this).

## 2. Navigation & reachability

- **App routes** (~46) = every nav entry maps to a `<RequireRoles>` route in `App.jsx`, plus `profile/*` detail routes and `/apply` (public admissions form).
- **Routed entry points** (some pages embed): SettingsPage embeds `NotificationsPanel` + `TwoFASection`; ExamsPage embeds `MarksEntryPanel`; ReportsPage embeds `SingleDetailReports`.
- **NOT routed → unreachable**: `ReportsCenter.jsx` (config-driven 136-report catalog — the modern hub is dead), `PendingApprovalsPage`, `WorkflowDefinitionAdminPage`, `WorkflowInstanceDetailPage`, `PermissionGate`.
- **Module toggle integration**: all toggleable modules have a `module:` key on their nav entries except Teachers, Staff, Staff Leave & Attendance, HR (hr=yes), HRPage uses `hr`), Timetable, Campuses, Assignments, Announcements, Documents, LMS/Online Courses (no `lms` — `lms` is prefixed in API but the nav entry has no `module: "lms"`), profile. See open items below.

## 3. Per-module coverage matrix

Legend: R=read-only, CRUD=full create/read/update/delete where API allows; **Reach** = routed ✓ / embedded ⦿ / dead ✗.

| Module | Pages (frontend) | Reach | CRUD | Key endpoints used | Gap notes |
| --- | --- | --- | --- | --- | --- |
| students | StudentsPage, ProfileModal, AdmissionsPage, AdmissionsApplyPage | ✓ | R+create; modal | `/api/students/`, `/me/`, `admissions/`, `guardians/` | add/edit modal not i18n; accept=prompt; no delete; self-view limited |
| attendance | AttendancePage | ✓ | create/bulk-mark | `/api/attendance/`, `/bulk/` | roster loader unbounded; no edit/delete of records |
| exams | ExamsPage + MarksEntryPanel | ✓ | marks entry only | `/api/exams/`, `/subjects/`, `/results/`, `/practical/` | **no exam create/edit/schedule UI** — D1 has service; FE gap |
| reportcards | ReportCardsPage | ✓ | read-only | `/api/report-cards/` | no open/print/download of a single card |
| timetable | TimetablePage | ✓ | view + auto-generate | `/api/timetable/periods|entries|generate/` | generate replaces all campus entries (confirm only) |
| discipline | DisciplinePage | ✓ | create incident | `/api/discipline/incidents/,/summary/` | no status-change/delete; no success feedback |
| finance | FinancePage, BulkFinancePage | ✓ | invoices/payments/fees CRUD + modals | `/api/finance/*`, `/api/dashboard/finance*`, stripe checkout | strong coverage; partial i18n; bulk lists unpaginated |
| payroll | PayrollPage | ✓ | mark paid, payslip dl | `/api/payroll/salary-structures|records|payslips|process/` | no create/edit payroll records UI |
| hr | HRPage, StaffPage, StaffOperationsPage | ✓ | employee CRUD (staff), leave approve | `/api/hr/employees/,/employment-events/`, `/api/staff/`, `/api/staff/leave/,/attendance/` | HRPage read-only; approvals unconfirmed |
| library | LibraryPage | ✓ | issues + return | `/api/library/books/,/issues/,/issues/{id}/return/` | no book/copy add/delete; filters manual |
| transport | TransportPage | ✓ | read-only | `/api/transport/vehicles|drivers|routes|assignments/` | **no CRUD at all** |
| inventory | InventoryPage | ✓ | read-only | `/api/inventory/assets|categories|suppliers|maintenance/` | no CRUD, no pagination |
| documents | DocumentsPage | ✓ | upload | `/api/documents/,/upload/`, `/api/hr/employees/`, `/api/students/` | no delete; no success feedback |
| hostel | HostelPage | ✓ | create + vacate | `/api/hostel/hostels|rooms|allocations|.../vacate/` | room-form reads wrong tab rows (bug); vacate unconfirmed |
| lms | LMSPage | ✓ | courses/lessons/quiz | `api/lms/*` | nav entry missing `module:"lms"`; quiz delete unconfirmed |
| homework | HomeworkPage | ✓ | create/grade | `/api/homework/,/submissions|grade/` | no attachments; text only |
| communication | MessagesPage, AnnouncementsPage, NotificationsPanel | ✓ | CRUD msgs; create announcements | `/api/communication/*` | announcements no edit/revoke; 2 of 3 pages embedded |
| sms/templates | SMSPage, TemplatesPage | ✓ | send + template CRUD | `/api/communication/sms|email/*`, `/templates/` | SMSPage GETs the send URL as probe; template errors swallowed |
| events | EventsPage | ✓ | create + RSVP | `/api/events/,/rsvp/` | RSVP/errors silent; no success feedback |
| health | HealthRecordsPage, HealthPage(→system) | ✓ | create records | `/api/health-records/records/`, `/api/students/` | no edit/delete of health records |
| alumni | AlumniPage | ✓ | create | `/api/alumni/`, `/api/schools/campuses/` | no edit/delete |
| helpdesk | HelpdeskPage | ✓ | create/reply/resolve/reopen | `/api/helpdesk/*` | feature-complete UI; errors swallowed; no assign picker |
| visitors | VisitorsPage | ✓ | check-in/out | `/api/visitors/visitors|stats|checkout/` | no success confirmation; silent load errors |
| digital_ids | DigitalIdsPage | ✓ | issue/revoke | `/api/digital-ids/cards/*`, `/api/students|teachers|staff/` | revoke unconfirmed + silent |
| reports | ReportsPage, ReportBuilderPage, ExportPage, DataImportPage, ReportsCenter, SingleDetailReports | ✓ + ✗ | templates CRUD; import commit | `/api/reports/*`, `/api/reports/templates/`, `/generate/`, `/import/*` | **ReportsCenter dead**; 24 legacy tabs duplicate config; import commit unconfirmed |
| portal | ParentPortalPage | ✓ | view + leave requests | `/api/students/guardians/me/`, all child data | sequential full-dataset loads — heavy |
| workflow | WorkflowDefinitionAdminPage, WorkflowInstanceDetailPage, PendingApprovalsPage | ✗ | (defined) CRUD/decide | `/api/workflow/*` | **all 3 pages unrouted** |
| system | TenantsPage, SettingsPage, BrandingPage, AuditLogsPage, HealthPage | ✓ | tenants PATCH; branding PUT | `/api/schools/tenants/`, `/branding/`, `/api/audit/`, `/api/reports/health/` | Tenants deactivate unconfirmed; Settings read-only; Branding fixed grid (not responsive); no validation |
| dashboards | Dashboard, CampusDashboard, ExecutiveDashboard | ✓ | read-only | `/api/dashboard/*`, `/api/reports/*` | missing empty states; no auto-refresh; Dashboard raw fetch |

## 4. Reports catalog (`frontend/src/config/reports.ts`)

**136 report definitions** across 16 categories: Dashboard, Students & Admissions, Attendance, Academics & Examinations, Fees & Finance, HR & Payroll, Staff & Teachers, Academic Operations, Parents & Guardians, Library, Transport, Inventory & Assets, Discipline, Certificates & ID Cards, Campus Reports, Report Builder. Consumed by the config-driven `ReportsCenter` — **which is not routed**. `ReportsPage.jsx` instead hardcodes ~24 legacy tabs (duplicated vocabulary, drift risk).

## 5. Portals

- **Public admissions** (`/apply`): campus→class→section cascade, application receipt, success + validation, but options-fetch failure leaves selects empty (no retry), no phone-format validation.
- **Parent portal** (`/parent-portal`, `parent` role): children attendance, report cards, fees + receipts, timetable, announcements, leave requests. Single page, per-child convention, but pulls full paginated datasets sequentially.
- **Self-profile views**: `ProfilePage` per `profile/:kind/:id` + `ProfileModal` (near-duplicate markup).

## 6. Cross-cutting issues (verify each is non-blocker before start)

1. **Dead/unrouted**: ReportsCenter, Workflow x3, PermissionGate — decide route-in or delete.
2. **Nav `module` gaps**: `lms` (Online Courses) and `assignments`, `announcements`, `documents`, `timetable`, `campuses`, `teachers`, `staff`, HR(documents via `hr` only) lack a module key → module-disable doesn't hide them (unless key intentionally absent for core).
3. **Client-side role arrays duplicated** in nav entries, routes, and pages — single source (D1's RBAC) vs page-level duplication drift risk.
4. **i18n**: only ~4/58 pages use the dictionary.
5. **Destructive-flight confirmations**: found on <10% of applicable pages.
6. **Bulk/sequential fetches**: attendance roster, parent portal, marks entry, pending approvals (N+1).

## 7. Module-level UX grading

| Grade | Modules |
| --- | --- |
| Strong | finance (modals, validation, charts), students/admissions, helpdesk, timetable (validate+confirm), digital_ids |
| Adequate (read-only or basic CRUD, gaps in confirmations/feedback) | attendance, exams(read), library, homework, hr, communication, alumni, visitors, lms |
| Thin (read-only, no actions) | transportation, inventory, reportcards, discipline, reports, payroll |
| Broken/Dead | hostel (room-form bug), ReportsCenter + workflow pages (unrouted) |