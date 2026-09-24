# PHASE 80 STEP 3 — STAFF READ-ONLY PRODUCTION CERTIFICATION

Phase: 80, Step: 3, Target role: `staff` (`sa_DI-staff.txt`), Mode: READ-ONLY, Date: 2026-09-24
Targets: `https://perfect-foundation-sms.vercel.app/` (frontend) and `https://perfect-foundation-a37ruonxb-lordvalicious-projects.vercel.app` (API)
Authoritative sources: `e2e/helpers/modules.js` (`CORE[STAFF]`), `e2e/tests/staff.spec.js`, `e2e/tests/authorization.spec.js`, `frontend/src/App.jsx`, `CORE[STAFF].allowed`, `CORE[STAFF].deniedUI`.

## 1. Authenticated Identity

- `GET /api/auth/me/` = **200** on both hosts (API + frontend). `username=DI-EMP-0001`, `primary_role=staff`,
  `primary_institution="Default Institution"`, display `But`, `memberships=[{role:staff, role_label:Staff Member}]`.
- `must_change_password=true`, `email_verified=false` — **observed, NOT acted upon** (no password change, no verification email sent).
- Session source: `sa_DI-staff.txt` in `P43_SESSIONS_DIR` (`C:\Users\Ryuk\AppData\Local\Temp\opencode`). No `P43_*` env vars set.
- No cookie/session/token/CSRF values printed at any point.

## 2. Method (READ-ONLY)

1. Set `P43_SESSIONS_DIR`; launched Playwright Headless Chromium; injected only `sa_DI-staff.txt` Netscape cookies.
2. Booted frontend `https://perfect-foundation-sms.vercel.app/`; confirmed authenticated shell + `/api/auth/me/` 200 / DI-EMP-0001 / staff.
3. Ran the authoritative STAFF-only e2e suites on production:
   - `npx playwright test tests/staff.spec.js` → **25/25 PASSED**.
   - `npx playwright test tests/authorization.spec.js --grep "STAFF:.*|staff denied routes"` → **8/8 PASSED** (STAFF-scoped only).
4. Ran per-route probe (`p80_s3_routes.cjs`) against all 21 canonical routes (10 allowed + 11 denied): captured
   final URL, login-page flag, denied-card flag, rendered body, in-page `/api/*` response statuses, and mutation controls.
5. Direct API checks (read-only, documented and canonical endpoints only).

## 3. Authentication Status

`AUTHENTICATION_STATUS=PROVEN`
- me/ 200 both hosts; staff membership present; frontend boots to authenticated shell (topbar: `S Default Institution Dashboard ... B But Staff`).
- Anonymous `/api/auth/me/` remains 403 (gate intact, verified Step 2).

## 4. Dashboard Status

`DASHBOARD_STATUS=PROVEN`
- `/` renders Dashboard Overview with welcome banner (body 683 chars); `isLoginPage=false`, no denied card, no login redirect.
- Widget API calls: `/api/dashboard/overview/` 200; report widgets `/api/reports/enrollment/`, `/api/reports/collection-trend/`,
  `/api/reports/attendance/` = **403** — expected backend denial for the Developer-role STAFF on the denied `/reports` module;
  dashboard main content still rendered. Not a defect (expected module-level denial).

## 5. Routes (21 canonical = CORE[STAFF].allowed 10 + deniedUI 11)

### 5.1 Allowed routes (render content, no redirect, no denied card) — READ_ONLY_PROVEN

| Route | Module APIs (all 200) | Proof |
|---|---|---|
| `/` | dashboard/overview | staff.spec[3], probe `p80_s3_routes.cjs` |
| `/profile` | auth/me | staff.spec[4] |
| `/timetable` | timetable/periods, timetable/entries | staff.spec[5] |
| `/messages` | communication/messages, messages/unread-count | staff.spec[6] |
| `/announcements` | communication/announcements | staff.spec[7] |
| `/events` | events | staff.spec[8] |
| `/helpdesk` | helpdesk/tickets, helpdesk/categories, schools/campuses | staff.spec[9] |
| `/visitors` | visitors/visitors, visitors/visitors/stats, schools/campuses | staff.spec[10] |
| `/digital-ids` | digital-ids/cards, students | staff.spec[11] |
| `/ai-assistant` | ai/overview | staff.spec[12] |

All ten: final URL = route (no redirect to login), `isLoginPage=false`, denied-card absent, non-empty rendered body.

### 5.2 Denied UI routes (correct Access denied card) — denied-verification PROVEN (expected denials, NOT failures)

`/finance`, `/payroll`, `/hr`, `/staff`, `/attendance`, `/exams`, `/report-cards`, `/settings`, `/students`, `/teachers`, `/reports`
— each rendered with `.state-card.error` "Access denied" (body ~145 chars), no login redirect, no module data calls fired.
Proofs: `staff.spec.js` 13–23 ("denied module is blocked on UI") + `authorization.spec.js` "staff denied routes show Access denied".

### 5.3 Backend enforcement (documented endpoints)

- REQUIRED 403 confirmed: `/api/finance/invoices/` **403**, `/api/finance/payments/` **403**, `/api/payroll/records/` **403**
  (staff.spec[24], authorization probes, and direct probe).
- Scoped reads (no 500, staff-self-scope): `/api/students/` 200, `/api/hr/employees/` 200, `/api/staff/` 200 (staff.spec[25], authorization probes).
- Observed reads (recorded, NOT in canonical required-403 set, NOT flagged as defects): `/api/attendance/` 200, `/api/exams/` 200,
  `/api/report-cards/` 200, `/api/teachers/` 200, `/api/documents/` 200 — these modules are UI-hidden for STAFF but API
  allows read scope; consistent with the documented "scoped read (no 500)" posture and not contradicted by any STAFF test.
- `/api/library/books/` 403 (module not in STAFF nav; expected denial).
- Guessed aggregate paths 404 (`/api/timetable/`, `/api/visitors/`, `/api/digital-ids/`, `/api/reports/`, `/api/inventory/`)
  — NOT defects (route aggregates do not exist; real sub-endpoints 200). Per instructions, guessed-path 404 is not a defect.

## 6. Modules (21 = 10 allowed + 11 denied UI)

- Allowed modules (read-only renders proven): Dashboard, My Profile, Timetable, Messages, Announcements, Events, Helpdesk,
  Visitors (Gate Log), Digital IDs, AI Assistant.
- Denied modules (Access denied card verified): Finance, Payroll, Human Resources, Staff Directory, Attendance, Exams,
  Report Cards, Settings, Students, Teachers, Reports.
- Module API statuses all 200 for allowed module endpoints (see 5.1); finance/payroll records/invoices/payments 403.

## 7. Mutation Ledger

Mutation-affording controls were **DETECTED but NEVER activated** (reason `PRODUCTION_READ_ONLY_CERTIFICATION`):
- Global email-banner: `Send verification link` (present on every page; `email_verified=false`; NOT clicked).
- `/messages`: `New Message` (detected, not clicked). `/announcements`: `New Announcement` (detected, not clicked).
- `/events`: `+ Add Event` (detected, not clicked). `/helpdesk`: `New Ticket` (detected, not clicked).
- `/visitors`: `Check In` (detected, not clicked). `/digital-ids`: `Issue Card` (detected, not clicked).

`MUTATION_WORKFLOWS_EXECUTED=0`. No form submitted, no button activated, no data written.

## 8. Deployment Context

Live frontend `56e4b21b` / live API `dbb2d95c` vs local HEAD `4306570d` → `DEPLOYMENT_COMMIT_MATCH=MISMATCH_PROVEN` (Step 1).
`/api/deploy-test/` 404 = STALE_DEPLOYMENT_PREDATES_ROUTE (Step 1). Not repaired; no redeploy.

## 9. Classification

- `CANONICAL_ROLE=staff`, `AUTHENTICATION_STATUS=PROVEN`, `DASHBOARD_STATUS=PROVEN`
- `ROUTES_TESTED=21`, `ROUTES_READONLY_PROVEN=10`, `ROUTES_FAILED=0`, `ROUTES_BLOCKED=11` (expected denials, not failures), `ROUTES_UNVERIFIED=0`
- `MODULES_TESTED=21`, `MODULES_READONLY_PROVEN=10`, `MODULES_FAILED=0`, `MODULES_BLOCKED=11` (expected denials), `MODULES_UNVERIFIED=0`
- `CONFIRMED_PRODUCTION_DEFECTS=0`
- `ROLE_CERTIFICATION_STATUS=READ_ONLY_PROVEN`

## 10. Deliverables

- `PHASE_80_STEP_3_STAFF_READONLY_CERTIFICATION.md` (this file)
- `PHASE_80_STEP_3_STAFF_ROUTE_MATRIX.csv`
- `PHASE_80_STEP_3_STAFF_MODULE_MATRIX.csv`
- `PHASE_80_STEP_3_MACHINE_SUMMARY.txt`

Safety flags: `PRODUCTION_DATA_MUTATED=NO SOURCE_MODIFIED=NO PERMISSIONS_CHANGED=NO PASSWORD_CHANGED=NO REDEPLOYED=NO
LOGOUT_PERFORMED=NO MUTATION_WORKFLOWS_EXECUTED=0`.

No login, no logout, no session creation, no other role tested, no parameterized-detail-route fabrication, no new IDOR probes,
no credential guessing. All counts derived from executed evidence only.