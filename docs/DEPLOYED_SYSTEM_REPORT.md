# Deployed System Report — Perfect Foundation SMS

Audit date: 2026-09-06 · Scope: production deployment (frontend + backend + database) · Companion tool: `tools/gap_analyzer.py` → `docs/AI_GAP_REPORT.md`

---

## 1. Executive summary

Perfect Foundation SMS is a **multi-tenant school management / ERP system** with a React SPA frontend and a Django REST backend, deployed as serverless functions on **Vercel** with a **PostgreSQL** database (Neon) and Vercel Blob storage for files.

- **Frontend:** React 19 + Vite, ~70 routed pages, ~120 distinct API endpoints consumed, i18n (English/Urdu), PWA service worker, dark/light theme.
- **Backend:** Django 6.1 + DRF 3.18, 30 app packages, **~184 model classes / 150+ migrations**, ~31 API namespaces, role-based access with 17 roles, campus + institutional tenant isolation, audit logging.
- **Database:** PostgreSQL; ~184 tables covering academics, finance, HR/payroll, operations, communication, and reporting.
- **Maturity:** The feature set is broad and production-shaped. The largest real gaps are **surface-level, not architectural**: orphaned UI for the (complete) workflow engine, an unreferenced reports hub, online payment limited to Stripe in the UI (JazzCash/EasyPaisa exist server-side but are not wired into the UI), and no AI-assisted features.

---

## 2. Architecture & deployment topology

```
Browser (React SPA) ── /api/* rewrites ──► Vercel (backed by perfect-foundation-api.vercel.app)
   │                                       │
   │ session cookie + CSRF                  ├─ Django WSGI (serverless)
   │                                       │    ├─ ActiveInstitutionMiddleware (domain → session → membership)
   │                                       │    ├─ CampusAccessMiddleware (campus isolation)
   │                                       │    ├─ ModuleAccessMiddleware (per-school feature toggles)
   │                                       │    └─ LoginAttemptAuditMiddleware (audit)
   │                                       ├─ PostgreSQL (Neon, psycopg 3)
   │                                       ├─ Vercel Blob (uploads, photos, documents)
   │                                       └─ External: Stripe, Twilio (SMS), SMTP (email), Google SSO,
   │                                          JazzCash/EasyPaisa (server-side), reportlab (PDF)
   └─ PWA (sw.js) + theme + i18n
```

- **Tenant model (3 layers):** `ActiveInstitutionMiddleware` resolves the school (white-label domain → session `active_institution_id` → user's first membership); `TenantManager` (ContextVar) auto-scopes ORM queries; `CampusAccessMiddleware` isolates campuses; `ModuleAccessMiddleware` gates modules per school.
- **Deployment caveat (from recent live testing):** the currently-deployed API binary is **stale relative to `master`** — e.g. the live `tenant-config/` endpoint 404s and `students` returns empty 400 bodies even though current master code passes tests. A redeploy of latest `master` is required before the live surface fully matches this report.

---

## 3. Backend inventory

### 3.1 Core platform

| System | Detail |
|---|---|
| Multi-tenancy | `ActiveInstitutionMiddleware`, `TenantManager`, `CampusAccessMiddleware`, `ModuleAccessMiddleware` |
| Auth | Custom `User`, 17 roles + `ROLE_RANK` elevation guards, `EmailOrUsernameBackend`, Google SSO, TOTP 2FA + backup codes, password history, account lockout, user sessions |
| Permissions | `HasRole`, `HasPermission` (+ per-role/user matrix), `IsSuperAdmin`, campus/institution guards (`access.py`) |
| Audit | `AuditLog` (26 action types), `record_audit()` |
| Workflow | Data-driven approval engine: `WorkflowDefinition`, `WorkflowInstance`, `WorkflowApproval`, `WorkflowTransition` |
| White-label | `WhiteLabelBranding`, `DomainMapping` (per-school custom domain + theme), `PublicBrandingMediaView` |
| Reporting | ~150 endpoints: master/student/attendance/exam/fee/HR/library/transport/inventory/discipline/certificates, report builder, scheduled + exported reports (CSV/JSON), import engine |
| Global search | `/api/search/` (people, classes, invoices, etc.) |

### 3.2 Module apps (30) and their domain models

| App | Headline entities |
|---|---|
| `schools` | School, Campus, AcademicUnit, Class, Section, AcademicYear, Term, Subject, ClassTeacher, AcademicCalendar, SubjectOffering, SchoolSettings |
| `students` | Student, Guardian, StudentGuardian, Inquiry, AdmissionApplication, Enrollment, AcademicHistory, StudentLifecycleEvent, StudentDocument, CampusTransfer, SectionTransfer, TransferCertificate, StudentLeaveRequest, StudentAlumni, ProgressionRecord |
| `teachers` | Teacher, TeacherAssignment |
| `attendance` | Attendance, AttendanceCorrection (+ biometric/RFID device sync) |
| `finance` | FeeCategory, FeeStructure, Invoice, InvoiceItem, InstallmentSchedule, Payment, PaymentReversal, PaymentRefund, Account, JournalEntry, JournalLine, BankAccount, BankReconciliation, Budget, BudgetLine, Expense, Concession, Fine, Adjustment, StudentFeeOverride |
| `payroll` | PayrollPeriod, SalaryStructure, SalaryRecord, Payslip, Allowance/Deduction support |
| `hr` | Employee, Department, Designation, EmploymentContract, LeaveType/Policy/Balance/Request, PerformanceReview, Allowance, Deduction, Bonus, Overtime, Loan, Advance, SalaryRevision, PayrollPeriod, ExitClearance, JobPosition, Candidate, Application, Interview (26 models) |
| `exams` | Exam, ExamSubject, StudentResult, PracticalResult, ExamSchedule, ExamSeating |
| `reportcards` | ReportCard, ReportCardSubject, GradeScale, GradeBand, GradeAmendment |
| `timetable` | Period, TimetableEntry (+ auto-generate) |
| `homework` | Homework, Submission |
| `lms` | Course, Lesson, LessonCompletion, Quiz, Question, QuizAttempt |
| `library` | Book, BookCopy, BookIssue |
| `transport` | Vehicle, Driver, Route, RouteStop, TransportAssignment, VehicleLocationLog |
| `inventory` | AssetCategory, Supplier, Asset, AssetAssignment, MaintenanceRecord, StockLevel, StockMovement |
| `hostel` | Hostel, Room, Allocation |
| `discipline` | Incident, DisciplinaryAction |
| `events` | Event, EventAudience, EventRSVP |
| `health` | HealthRecord |
| `alumni` | AlumniProfile |
| `visitors` | Visitor (+ badge numbering) |
| `digital_ids` | IdCard (+ card numbering, revoke) |
| `communication` | Message, Announcement, Notification, NotificationPreference, NotificationDispatch, QueuedNotification, SMSLog, EmailLog, MessageTemplate (+ notification queue with backoff + idempotency, cron fee-reminders/absence-alerts) |
| `helpdesk` | TicketCategory, SupportTicket, TicketMessage |
| `reports` | ReportDefinition, ReportTemplate, SavedReport, ScheduledReport, CustomReport, ReportDataSource, ReportCategory, ReportAuditLog |
| `audit` | AuditLog |
| `workflow` | WorkflowDefinition, WorkflowInstance, WorkflowApproval, WorkflowTransition |
| `white_label` | WhiteLabelBranding, SchoolSettings, DomainMapping, WhiteLabelAuditLog |
| `core` | SoftDelete/TimeStamped/Campus/Institution/Auditable mixins |
| `portal`, `dashboard`, `search`, `documents` | thin aggregator/serverless apps (no models) |

### 3.3 Integrations & services

| Integration | Status |
|---|---|
| **Payments — Stripe** | Wired end-to-end in UI + `stripe_views.py` checkout + `stripe_webhook` (PKR) |
| **Payments — JazzCash** | Server-side complete (secure hash, hosted checkout, callback) — **not exposed in the UI** |
| **Payments — EasyPaisa** | Server-side complete (request hash, transaction confirm, callback) — **not exposed in the UI** |
| **SMS — Twilio** | `communication/sms.py`; falls back to console when `TWILIO_*` env vars unset |
| **Email** | SMTP via Django; **requires `DJANGO_EMAIL_*` env vars**; UI warns when unconfigured |
| **Google SSO** | `/api/auth/google/config/` + `/api/auth/google/login/` (login page) |
| **2FA** | TOTP + backup codes (setup/activate/disable/status in UI) |
| **Receipts / certificates / transcripts** | ReportLab PDF generation (A5 receipts, bonafide/character/transfer/leaving/fee-clearance/enrollment certs) |
| **Cron jobs** | Bearer `CRON_SECRET` endpoints: fee reminders, absence alerts, notification processing, weekly email reports |
| **Device sync** | Attendance biometric/RFID push via `X-Device-Key` |
| **Files** | `vercel_blob` for uploads; `ProtectedMediaView` + public branding media |
| **API docs** | drf-spectacular Swagger (`/api/docs/`), Redoc (`/api/redoc/`) |

---

## 4. Frontend inventory

- **Stack:** React 19, Vite, react-router-dom 7, recharts, lucide-react; ESLint; hand-rolled i18n (en/ur); PWA.
- **Auth/session:** cookie + CSRF (`api.js`), `/api/auth/me/` watchdog, `sessionWatch.js` 401/403 expiry (`pf:unauthorized`), `schoolContext.jsx` (active school, roles, per-school module toggles, school switcher for platform admins).

### 4.1 Routed pages (from `frontend/src/App.jsx`)

| Feature area | Pages |
|---|---|
| Platform | Dashboard, ExecutiveDashboard, CampusDashboard, Tenants (platform admin), Settings (2FA, notifications), Branding, Health, Audit Logs |
| Admissions & students | Public `/apply`, Admissions, Students, Student 360 (academics, finance, discipline, certificates, lifecycle) |
| Academics | Academics, Teachers, Class Assignments, Timetable |
| Exams & results | Exams (marks entry, subjects, schedules, seating, practicals, gradebook, results), Report Cards |
| Finance | Finance (invoices, payments, fee structures, overrides, outstanding, income/expense, receivables, Stripe checkout), Student Fees, Bulk Finance |
| HR & payroll | HR, Staff, Payroll (structures, records, payslips PDF), Staff Operations |
| Communication | Announcements, Messages, SMS, Templates |
| Operations | Library, Transport, Inventory, Documents, Hostel, Visitors, Digital IDs, Health Records, Discipline, Events |
| Learning | Homework, LMS (courses, lessons, quizzes, progress) |
| Support & reporting | Helpdesk, Alumni, Reports, Report Builder, Data Export/Import, Search (global) |

### 4.2 Frontend-side gaps (verified by reading source)

1. **Workflow engine UI is orphaned** — `WorkflowDefinitionAdminPage`, `WorkflowInstanceDetailPage`, `PendingApprovalsPage` exist and are backed by a real API, but have **no route or nav entry** in `App.jsx`.
2. **`ReportsCenter.jsx` is unreferenced** — superseded by `ReportsPage`/`ReportBuilderPage` but still shipped (dead code / config catalog).
3. **No AI features anywhere** (zero references to GPT/Claude/etc. in frontend or backend code).
4. **Online payment in the UI is Stripe-only** — JazzCash/EasyPaisa appear only as method labels; their complete server-side implementations are unused client-side.
5. **Email delivery depends on server env vars** (`DJANGO_EMAIL_*`) — no guaranteed out-of-box email.
6. **Data import supports only students + teachers** in the UI (backend import catalog is broader).
7. **Timetable is view + auto-generate only** — no manual entry editing in the UI.
8. **ReportsCenter catalog** (`config/reports.ts`, 136-report catalog) describes far more report URIs than the routed Reports page surfaces.

---

## 5. Database inventory

- **Engine:** PostgreSQL (Neon) via `psycopg` / `dj-database-url`. Local dev can use SQLite (`DATABASE_URL=sqlite:///:memory:`).
- **Scale:** ~184 model classes across 30 apps; 150+ migration files (largest: `schools` 28, `accounts` 23, `students` 11, `communication` 11).
- **Domain tables cover:** tenants/schools & hierarchy, students + guardians + admissions + transfers + leave + alumni, teachers, attendance, finance (invoicing, payments, ledger, budgets, concessions/fines/adjustments), payroll, HR (contracts, leaves, loans, reviews, recruitment), exams, report cards, timetable, homework, LMS, library, transport, inventory, hostel, events, discipline, health, visitors, digital IDs, communication (messages, notifications, SMS/email logs), helpdesk, reports, audit log, workflow, white-label branding/domains.
- **Multi-tenancy is enforced in the ORM (TenantManager), not duplicated in the database** — every tenant-scoped model carries an institution FK.

---

## 6. Verified production gaps (things to fix / finish, not add)

Priority order:

1. **Redeploy backend from `master`** — live API is stale (tenant-config 404, empty student 400s, `demo_superadmin` drift). Highest impact.
2. **Start the workflow engine UX** — engine is complete; add routes + nav for definitions/approvals/pending-items. Otherwise it's dead value.
3. **Wire JazzCash/EasyPaisa into the UI** or remove the labels — server-side is done; the UI currently misleads users.
4. **Reconnect/remove `ReportsCenter`** — decide between the routed Reports page and the 136-report catalog hub; ship one.
5. **Configure email delivery** (`DJANGO_EMAIL_*`/SMTP or an email provider) or state clearly it's SMS-first.
6. **Import engine coverage** — extend DataImport UI beyond students/teachers to the backend's full import catalog.

---

## 7. Recommended additions (what to add)

High value, low risk — build next:

1. **AI assistance layer** (the biggest missing differentiator, ~all modules can use it):
   - AI report-card / result comments generator (from exam results + grade bands).
   - AI "smart search" / natural-language queries over `/api/search/` + reports.
   - AI fee-default prediction & concession recommendations (finance already has data models for this).
   - AI draft SMS/email templates from `MessageTemplate` + tone/audience.
   - AI attendance anomaly detection (absences per student/weekly).
2. **Online payment expansion**: JazzCash/EasyPaisa UI wiring (backend ready) + payment receipt email.
3. **Student/Parent mobile experience**: PWA offline mode, push notifications for fees/attendance/schedules (queue engine + `sw.js` are ready).
4. **Manual timetable editor** (today: view/generate only).
5. **Custom report builder UX** on top of the existing report-builder API (surfaced to each role).
6. **Fee reminders automation visible in UI** (cron exists; expose schedules + dry runs per school).
7. **WhatsApp/email notification channels** alongside SMS (the `notification_queue` is channel-agnostic).

## 8. What NOT to add (avoid / cut)

1. Do not build **another auth system** — SSO, 2FA, lockout, password history already exceed most school ERPs.
2. Do not build **another reporting platform** — ~150 endpoints + builder already exist; surface them better instead.
3. Do not build **new HR/payroll tables** — 26 HR models already cover contracts, recruitment, leaves, loans, reviews.
4. Do not add **another multi-tenancy scheme** — the 3-layer model (domain/session/ORM) is complete; changing it is a rewrite.
5. Do not add **PayPal/other payment providers** before finishing JazzCash/EasyPaisa (already half-built).
6. Do not add **bulk BI/ETL** or a separate analytics database at this scale — the reporting module covers it.

---

## 9. How the AI gap analyzer works (built into the repo)

`tools/gap_analyzer.py` (stdlib-only) scans both trees and emits a prioritized add/don't-add recommendation:

- **Inventory:** parses backend `apps/*/models.py` + `urls.py`, frontend `App.jsx` routes + `src/pages/*.jsx` API calls; counts integrations (stripe/twilio/jazzcash/easypaisa/openai/pdf).
- **Analysis modes:**
  - `--llm` (or auto when `OPENAI_API_KEY` is set): sends the inventory + heuristic findings + checklist to an OpenAI-compatible chat-completions endpoint and asks for a structured add/don't-add report.
  - heuristic (default, offline): rule-based scoring of module completeness (models ↔ API endpoints ↔ UI routes ↔ integrations) against a curated capability checklist.
- **Outputs:** `docs/AI_GAP_REPORT.md` (markdown) + `docs/AI_GAP_REPORT.json` + console summary.
- **Run:** `python tools/gap_analyzer.py` (from repo root), or `python manage.py system_audit` inside `backend/` (Django mode introspection).