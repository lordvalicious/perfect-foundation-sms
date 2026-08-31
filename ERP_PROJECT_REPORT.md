# Perfect Foundation SMS — Whole-Project Technical Report

> Branch audited: **master** (`7ae416b`, "Merge branch 'master'...") — read-only audit. Companion documents: `ERP_AUDIT_GAP_MATRIX.md`, `ERP_MODULE_SCORECARD.md`, `ERP_SECURITY_AUDIT.md`, `ERP_DATABASE_AUDIT.md`, `ERP_REMAINING_WORK.md`, `DEVELOPER_1_PROMPT.md`, `DEVELOPER_2_PROMPT.md`.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Repository & Tech Stack](#2-repository--tech-stack)
3. [Directory Map](#3-directory-map)
4. [Backend Architecture](#4-backend-architecture)
   - 4.1 Settings & Configuration
   - 4.2 URL / API Map
   - 4.3 Apps & Responsibility Matrix
   - 4.4 Cross-Cutting Mechanisms (Auth, RBAC, Multi-Tenancy)
   - 4.5 Data Model Highlights
5. [Frontend Architecture](#5-frontend-architecture)
   - 5.1 Stack, Routing & Pages
   - 5.2 Auth & API Client Flow
6. [How the System Works (End-to-End)](#6-how-the-system-works-end-to-end)
7. [Master Branch Test Run — Results](#7-master-branch-test-run--results)
   - 7.1 Environment & Method
   - 7.2 Numbers
   - 7.3 Failures Caused by Test Files (not code)
   - 7.4 Real Code Bugs Found by the Test Run
8. [What Works vs. What Is Broken](#8-what-works-vs-what-is-broken)
9. [Key Risks & Known Issues](#9-key-risks--known-issues)
10. [Recommendations](#10-recommendations)

---

## 1. Executive Summary

`perfect-foundation-sms` is a **multi-tenant School Management System (ERP)** for a franchise model: a holding company runs many schools; each school has multiple campuses; users belong to a school and are scoped to one or more campuses. Identity, RBAC, multi-tenancy, and campus isolation are the most mature areas of the codebase. The **finance, HR/payroll, operations, and reporting modules are partially built**; the **foundation (auth + isolation + data model)** is genuinely strong.

- **Overall maturity:** "Basic ERP". Average module score ≈ **56%** (see `ERP_MODULE_SCORECARD.md`).
- **Frontend completeness:** ≈ **35%** of the UI surface is functional; many pages are admin CRUD shells, real feature screens (marks entry, report cards, finance ops) are still partial.
- **Production readiness estimate:** ≈ **23 weeks / 505 person-days / 5.5 FTE**, roughly split: Dev1 = backend core/security/infra; Dev2 = per-module backend logic; Frontend1/Frontend2 = UI; Partner = reports/tests consumption.

The branch boots cleanly, the stored code is coherent and the codebase compiles: `manage.py check` passes (test & production settings), and the **frontend production build succeeds (2441 modules)**. However, a **test run (276 tests across 5 apps) yields ~54 failures + ~19 errors**, dominated by (a) rate-limit throttles firing inside tests, (b) test-file bugs (missing imports), and (c) a set of **real, reproducible code bugs** listed in §7.4.

---

## 2. Repository & Tech Stack

| Layer      | Technology |
|------------|-----------|
| Backend    | Django 6.1, Django REST Framework 3.18, psycopg 3 |
| Database   | PostgreSQL (default `perfect_foundation`, `school_admin`/`school_password` fallback); `config/settings/test.py` uses SQLite in-memory |
| Frontend   | React 19, React-Router 7, Vite 8, Axios, plain CSS |
| Auth       | Custom `EmailOrUsernameBackend`, pyotp TOTP 2FA, PyJWT, session tracking |
| Integrations| Twilio (SMS), Stripe (payments), ReportLab (PDF), Pillow |
| Deployment | Vercel (frontend), run-migrations bootstrap endpoint |

`backend/requirements.txt` (17 packages) installs cleanly into `.venv` at repo root.

---

## 3. Directory Map

```
backend/
  manage.py                 # defaults to config.settings.development
  config/
    settings/base.py        # everything; hardcoded SECRET_KEY fallback (~L22), DB via DATABASE_URL else Postgres
    settings/development.py # DEBUG=True, CORS for localhost:5173
    settings/test.py        # [untracked] SQLite in-memory, throttling disabled at DEFAULT level, MD5 hasher
    urls.py                 # full API route table (~203 lines) + protected media serving
  apps/
    <34 apps>, each with models|serializers|views|urls|permissions|tests (see §4.3)
  scripts/, data/           # fixtures, seed data migrations
frontend/
  index.html, vite.config.*
  src/
    App.jsx, main.jsx       # router setup
    api/client.js           # axios instance + token handling
    components/             # shared UI (Sidebar, Layout, etc.)
    context/                # AuthContext, SchoolContext (active school/campus)
    pages/                  # 60+ page components (see §5.2)
    styles/
*.md at root               # audit reports + developer prompts + this report
```

---

## 4. Backend Architecture

### 4.1 Settings & Configuration

- **`config.settings.base`** holds everything: installed apps (18+ Django/DRF/cors libs + 34 local apps), middleware chain, DRF settings (JWT + session auth, default throttles, custom exception handling), template/media settings, and a **hardcoded `SECRET_KEY` fallback** (P0 risk — flagged in `ERP_SECURITY_AUDIT.md`).
- **DB selection:** `DATABASE_URL` env → parse; else Postgres env (`DB_ENGINE/DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT`) with baked-in dev defaults.
- **`test.py` (new, untracked, created for this test run):** SQLite in-memory, `DEFAULT_THROTTLE_CLASSES = []`, `MD5PasswordHasher`, `USE_TZ` aware. Note it only clears the *default* throttle classes — **views that set explicit `throttle_classes` still throttle**, which is why tests show 429s.
- Root `run_tests.py` invokes `manage.py test --settings=config.settings.production` (needs Postgres) — that is why default test discovery differed from app-labeled runs.

### 4.2 URL / API Map (from `config/urls.py`)

`/api/auth/`, `/api/staff/`, `/api/dashboard/`, `/api/students/`, `/api/teachers/`, `/api/attendance/`, `/api/schools/`, `/api/finance/`, `/api/exams/`, `/api/report-cards/`, `/api/timetable/`, `/api/events/`, `/api/communication/`, `/api/audit/`, `/api/library/`, `/api/transport/`, `/api/inventory/`, `/api/payroll/`, `/api/hr/`, `/api/reports/`, `/api/search/`, `/api/documents/`, `/api/discipline/`, `/api/homework/`, `/api/health-records/`, `/api/alumni/`, `/api/hostel/`, `/api/lms/`, `/api/portal/`, `/api/white-label/`, `/api/workflow/`, `/api/helpdesk/`, `/api/visitors/`, `/api/digital-ids/`, `/api/health/`, `/api/admin/run-migrations/`, plus `/admin/` and protected media endpoints. **No DRF API root router** (so `/api/` → 404).

### 4.3 Apps & Responsibility Matrix

| App | Purpose | Maturity (from `ERP_MODULE_SCORECARD.md`) |
|-----|---------|------|
| `accounts` | Users, roles (15), RBAC, 2FA, sessions, staff mgmt, access helpers, tests | Strong / core |
| `schools` | Tenant model (`School`), `Campus`, `AcademicUnit`, `Class`, `Section`, `SubjectOffering`, branding, modules, media | Strong core, **P0 duplicate model** |
| `students` | Student profile, guardians, admission, lifecycle, Student360 view | Core OK, broken serializer |
| `teachers` | Teacher profiles, assignments | Partial |
| `attendance` | Daily attendance | Partial |
| `finance` | Invoices, payments, expenses, receipts (PDF), audit trails | Partial — several failing flows |
| `exams` | Exam setup, marks entry, results | Partial |
| `reportcards` | Grade scales, report cards | Partial/broken |
| `timetable` | Scheduling, seating | Partial |
| `events` / `communication` / `announcements` | School events, messages | Partial (isolation leaks) |
| `audit` | Audit log records | Partial |
| `library`, `transport`, `inventory` | Operations modules | Stub-level (seed scripts exist) |
| `payroll`, `hr` | Salary structures, records | Stub-level + **migration drift** |
| `reports`, `search`, `documents`, `dashboard` | Reporting/search/document/dashboards | Consumer level (mostly frontend) |
| `discipline`, `health`, `homework`, `alumni`, `hostel`, `lms`, `portal`, `workflow`, `white_label`, `helpdesk`, `visitors`, `digital_ids` | Feature portals | Stub/skeleton scope |

Each app follows the same layout: `models.py`, `serializers.py`, `views.py` (DRF APIViews/viewsets+CBD patterns), `urls.py`, `permissions.py` where needed, and `tests.py`/`test_*.py` for accounts/schools/students/finance/exams.

### 4.4 Cross-Cutting Mechanisms

- **Authentication:** custom `EmailOrUsernameBackend`; DRF authentication classes = JWT + Session. Password hardening: bcrypt/Argon hashing, password history, account lockout, TOTP 2FA (`apps/accounts/twofa_views.py`, frontend `TwoFASection.jsx`).
- **RBAC:** 15 roles in `apps/accounts/models.Role` (super_admin, admin, org_admin, head_office, academic, teacher, staff, accountant, librarian, hostel_admin, transport_admin, hr_admin, payroll_admin, student, guardian, parent). Granular permissions use **3-part codenames** (`<app>.<model>.<action>` — a test still expects the old 2-part format).
- **Multi-tenancy & campus isolation:**
  - `ActiveInstitutionMiddleware` (`apps/accounts/middleware.py`) — binds request to the authenticated user's school.
  - `CampusAccessMiddleware` (`apps/accounts/campus_middleware.py`) — scopes to allowed campuses (super_admin/org_admin/head_office/academic see all — `GLOBAL_ROLES` in `apps/accounts/access.py`).
  - `TenantManager` / `CampusScopedManager` (`apps/accounts/managers.py`) — auto-`filter(school=...)` default managers on tenant models.
  - `apply_campus_scope` / `restrict_to_allowed_campuses` helpers in `apps/accounts/access.py`.
  - `ModuleAccessMiddleware` (`apps/schools/middleware.py`) — 403s requests to modules disabled in `School.enabled_modules` (empty list = all modules enabled). This is new on master and the cause of many 403 test failures.
- **Middleware order (base.py):** security → session → institution → campus-scope → module-gating → auth → DRF.

### 4.5 Data Model Highlights

- **Tenant spine:** `School` → `Campus` → `AcademicUnit` → `Class` → `Section`. `SubjectOffering` links subject+class+year (defined **twice** — see §7.4 #1).
- **Finance:** `Invoice`, `Payment`, `Expense` (+ journal concept), `FeeStructure`/`FeeCategory`, receipt PDF generation.
- **People:** `User` (custom), `Student` + `StudentGuardianLink` (self-referential related_names, both `models.py:199/204`), `Teacher`, `Staff`/`Employee`.
- **ID system:** `DigitalId` + `digital_ids` module.
- **Seed reality:** several apps have "Populating …" seed/migration scripts (library, inventory, transport, reportcards) that populate 0 rows when run against an empty/mock DB — fixtures are placeholders.

---

## 5. Frontend Architecture

### 5.1 Stack, Routing & Pages

- React 19 + React-Router 7, Vite 8. Single `dist` bundle ≈ **1.23 MB (gzip 307 kB)** — above the 500 kB chunk warning; code-splitting needed.
- Router in `src/App.jsx`; API layer `src/api/client.js` (axios, tokens, error interceptor).
- Auth/session state in `src/context/` (`AuthContext`, `SchoolContext`).
- **60+ pages** under `src/pages/`: Login, Dashboard (`Dashboard.jsx`, `CampusDashboardPage.jsx`, `ExecutiveDashboardPage.jsx`), Students (`StudentsPage.jsx`, `Student360Page.jsx`, `StudentLifecyclePanel.jsx`), Admissions, Attendance, Exams (`ExamsPage.jsx`, `MarksEntryPanel.jsx`, `ExamFormModal.jsx`), Timetable (`ManageSchedulePanel.jsx`, `ManageSubjectsPanel.jsx`, `ManageSeatingPanel.jsx`), Finance (`FinancePage.jsx`, `BulkFinancePage.jsx`), HR/Payroll, Reports (`ReportsCenter.jsx`, `ReportBuilderPage.jsx`, `SingleDetailReports.jsx`), SMS (`SMSPage.jsx`), plus `ui.jsx` (design tokens). Pages are admin-CRUD heavy; deep workflows (marks entry, report-card generation, payment approval) remain partial.

### 5.2 Auth & API Client Flow

1. Login → POST `/api/auth/login/` (rate limited) → JWT + session cookie; 2FA challenge if enabled.
2. Client stores token; `AuthContext` loads user + memberships/roles from `/api/auth/me/`.
3. `SchoolContext` picks active school/campus; subsequent requests carry `X-School-ID` (institution binding) and campus scoping headers that the backend middlewares enforce.

---

## 6. How the System Works (End-to-End)

1. **Onboarding:** Super admin creates a `School` (tenant). Branding/media via `/api/schools/`; `PublicBrandingMediaView` serves logo.
2. **Provisioning:** School → campuses → academic units → classes → sections; subjects + `SubjectOffering` per class/year. Modules toggled via `enabled_modules`.
3. **Users & access:** accounts create; roles assigned; staff/teacher/student linking; granular permissions granted (3-part codenames). Login enforces lockout/2FA/history; campus middleware scopes every query.
4. **Academic workflow:** timetable/scheduling → attendance → exams (`ExamSubject`, marks entry) → results → report cards (grade scales).
5. **Finance workflow:** fee structures → invoices → payments/refunds/reversals → receipts (PDF via ReportLab) → expense journal → audit trail.
6. **Operations:** events, communication/SMS (Twilio), library/inventory/transport records, HR/payroll records.
7. **Reporting:** `reports` + `search` + `dashboard` consume via read-only endpoints; export data import/export.

---

## 7. Master Branch Test Run — Results

### 7.1 Environment & Method

- Ran on **master** with the new SQLite `config/settings/test.py`: `manage.py check` pass; `manage.py test <app labels>`.
- Default discovery (`manage.py test`) reports **0 tests**; app-labeled runs are required.
- Frontend: `npm run build` (Vite) → **success**, 2441 modules, only chunk-size warning.
- Live boot: `runserver` starts clean; `/admin/login/` → 200; `/api/` → 404 (no root router, not a bug).

### 7.2 Numbers

| Run | Tests | Failures | Errors |
|-----|-------|----------|--------|
| `apps.accounts` | 137 | 45 | 4 |
| `apps.schools + apps.finance + apps.students + apps.exams` | 139 | 9 | 15 |
| **Total (sampled 5 of 34 apps)** | **276** | **54** | **19** |

### 7.3 Failures Caused by Test Files (not product code)

1. **Rate limiting fires inside tests → `429` floods** (majority of accounts failures; `BrandingIsolationTests`/`ModuleEnforcementTests`/`TenantIsolationTests` setUpClass fail with "Request was throttled. Expected available in 2707 sec"). `test.py` cleared only `DEFAULT_THROTTLE_CLASSES`, but views set explicit `throttle_classes` (login/password-reset scopes). Fix in test config (raise scoped rates to huge numbers), not production code.
2. **Missing imports in test files:** `APIClient` (6× in `apps/students/tests.py`, `Student360APITests`) and `APIRequestFactory` (`apps/finance/tests.py`, `SecurityAccessTests`) are used but never imported.
3. **Permission codename format test expects 2-part** (`resource.action`), code now generates **3-part** (`app.resource.action`) → `test_access.py` FAIL.
4. **`test_superuser_has_all_permissions` FAIL:** superuser permission set derives from `Permission` table, which is **empty in the test DB** (granular permissions not seeded) → superuser returns `False` for `student.view` in a fresh DB.
5. **`run_tests.py` points at `config.settings.production`** (needs Postgres) — should target test settings so CI can run on SQLite.

### 7.4 Real Code Bugs Found by the Test Run

| # | Severity | Bug | Location |
|---|----------|-----|----------|
| 1 | **P0** | Duplicate `class SubjectOffering` (defined twice) → Django RuntimeWarning "Model 'schools.subjectoffering' was already registered", risk of broken relations/indices | `backend/apps/schools/models.py:401` and `:736` |
| 2 | **P0** | `Student360Serializer.guardian_links` declares `source="guardian_links"` (redundant) → DRF `AssertionError` at instantiation → **Student360 endpoint crashes** | `backend/apps/students/serializers.py:962` |
| 3 | **P1** | `Student` has **no `age` property** yet tests depend on it (`AttributeError: 'Student' object has no attribute 'age'`) | `backend/apps/students/models.py` |
| 4 | **P1** | Expense posting does **not create a journal entry** (`test_expense_posting_creates_journal` ERROR) | `apps/finance` |
| 5 | **P1** | Outstanding-invoice queryset returns **0** and `invoice_summary` balance = 0 where 3000 expected (`0 != 2`, `0 != 3000.00`) | `apps/finance` |
| 6 | **P1** | Payment **audit trail is `None`** for create/refund/reversal (`test_payment_audit_trail`, `_refund_`, `_reversal_` all fail) | `apps/finance` |
| 7 | **P1** | Receipt endpoint now returns a **ReportLab PDF**, tests still expect HTML snippet `RCPT-...` (behavior change not propagated) | `apps/finance` (receipt gen) |
| 8 | **P1** | **Tenant/campus isolation leaks:** seeded events (annual sports day, etc.) visible to a campus admin; fee-structure isolation broken across institutions (`2 != 1`) | `apps/events`, `apps/schools` |
| 9 | **P1** | **Payroll migration drift:** models changed from `teacher`→`employee`, but `makemigrations --check` still generates an unmade migration (`0005_remove_payrollrecord_payroll_teacher_ym_idx_and_more`) | `backend/apps/payroll/models.py` vs `migrations/` |
| 10 | **P2** | Missing uniqueness validation: duplicate `Section` names within a class not rejected (`ValidationError not raised`) | `apps/schools/models.py:260` |
| 11 | **P2** | Refund validation blocks refunds: `Payment cannot be greater than the invoice balance` | `apps/finance` validation |
| 12 | **P2** | `test_subject_offering_is_unique_for_class_and_year` broken (missing uniqueness enforcement + test-scope `attribute` error) | `apps/schools/models.py:401/736` |

---

## 8. What Works vs. What Is Broken

**Works today (verified or high-quality code):**
- Auth: login/lockout/2FA/password history/session tracking, `/api/auth/me/`, JWT+session.
- Core tenant model & RBAC helpers: `GLOBAL_ROLES`, campus scoping functions and managers.
- Django admin at `/admin/` (pure Django, works).
- Compilation/boot: `manage.py check` passes on test & production settings; server starts cleanly.
- Frontend **production build** passes; most administrative CRUD pages render.

**Broken / incomplete today (from §7.4 + audit):**
- Student360 API (serializer crash) and Search consolidated risk.
- Finance outstanding/invoice summary, expense→journal, payment audit trails, receipts (behavior mismatch), refund handling.
- Isolation leaks for events & fee structures; module-gating 403s against unseeded permissions.
- Payroll schema/migration mismatch; report-cards + exam results flow partially implemented.
- Frontend feature depth (marks entry, report cards, finance ops, full portals) ≈ 35%.

---

## 9. Key Risks & Known Issues

- **Duplicate model definition (P0-07)** is the most dangerous structural defect — it corrupts model registry meta and relates to many downstream problems.
- **Hardcoded `SECRET_KEY` fallback** and embedded DB credentials in `base.py` (P0 security findings — `ERP_SECURITY_AUDIT.md`).
- **CASCADE deletes** on financial records (`Invoice.student`, `Payment.invoice`) + missing unique constraints (`ERP_DATABASE_AUDIT.md`).
- **No real payment gateway wiring, no refund workflow, no bank reconciliation** in finance.
- **Unverified campus isolation** for most modules (events confirmed leaking; others unverified).
- **Test debt:** 0-test default discovery, test file import bugs, throttle-vs-test conflict, permissions not seeded in test DB.
- **Frontend bundle** 1.2 MB — needs code-splitting.

---

## 10. Recommendations

1. **P0 first (Dev1):** remove duplicate `SubjectOffering`; fix `Student360Serializer.source` redundancy; generate `payroll` migration; add login/2FA scoped-rate override to test settings; seed granular permissions (data migration) so superuser/RBAC behave in fresh DBs.
2. **P1 (Dev1/Dev2):** fix test-file imports (`APIClient`/`APIRequestFactory`), align permission-codename tests to 3-part format, enforce tenant/campus isolation on `events` + `fee_structure`, restore finance flows (outstanding, journal, audit trails, receipt contract), add `Student.age`.
3. **Deliverables for the two developers** are in `DEVELOPER_1_PROMPT.md` / `DEVELOPER_2_PROMPT.md` with non-overlapping scope and "don't duplicate existing code" rules. Recommended order: Dev1 Phase 0 (core/security/infra) → Dev2 per-module backend → Frontend1/Frontend2 UI alongside.
4. **CI:** point test runner at `config.settings.test`, expand app coverage to all 34 apps, then run the whole suite to capture the remaining modules' baseline.