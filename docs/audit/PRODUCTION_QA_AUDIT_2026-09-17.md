# Production QA / Regression Audit — perfect-foundation-sms

- **Date:** 2026-09-17
- **Frontend:** https://perfect-foundation-sms.vercel.app/
- **Backend:** https://perfect-foundation-api.vercel.app/
- **Mode:** READ-ONLY. No code, database, user, role, permission or config changes. No deploy. No commit/push.
- **Method:** live production HTTP/API testing using real login sessions, plus full static source inspection. No browser engine was available, so rendering, browser console, visual/responsive and modal behaviour are source-inspected only and are explicitly marked as NOT runtime-verified.

## Accounts used (passwords redacted)

| Role | Identifier | Notes |
|---|---|---|
| Super Admin | `FrostFire` | `is_superuser:true`, `primary_role:super_admin`, `must_change_password:false` |
| Principal | `Flora` | actual primary role is `principal`, not admin |
| Teacher | `SA-EMP-0001`, `SA-EMP-0003`, `SA-EMP-0004` | `must_change_password:true` |
| Student | `SA-ST-0001`, `SA-ST-0002`, `SA-ST-0003`, `PF-20262027-0121` | `must_change_password:true` |
| Staff | `DI-EMP-0001` | `must_change_password:true` |
| Not tested | Institution Admin, Accountant, HR, Parent | no credentials provided |

## A. Production Health — PASS
- Frontend `/` 200 (text/html); assets 200 (JS 300 KB, CSS 99 KB, favicon, manifest).
- Backend `/api/health/` 200 `{"status":"ok","database":{"ok":true,...}}`.
- CSRF cookie + session login work; deep links return 200 SPA fallback.
- `/api/docs/`, `/api/schema/`, `/api/redoc/` are auth-gated (403 unauthenticated).
- Security headers present: HSTS, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`. No CSP / Permissions-Policy.
- Same-origin `/api/*` proxy via `frontend/vercel.json`; no CORS needed (P4 informational).

## B. Role Testing

| Role | Login | Dashboard | Functionality | Status |
|---|---|---|---|---|
| Super Admin | 200 | 200 (~6.9 s) | platform routes 200 | TESTED |
| Principal | 200 | 200 (~22 s) | campus-scope defects | TESTED (with issues) |
| Teacher | 200 | 200 | 403 on finance/reports (correct) | PARTIAL |
| Student | 200 | 200 | scoped | PARTIAL |
| Staff | 200 | 200 | 403 on finance/reports (correct) | PARTIAL |
| Admin / Accountant / HR / Parent | — | — | — | NOT TESTED |

## C. Route Audit
All ~60 `App.jsx` routes enumerated (single router; one global `ErrorBoundary` at `App.jsx:1065`; `Suspense` at `App.jsx:1066`). Every route's backing API was exercised with an authorized session where one was available. No route hard-failed for an authorized role except those in §D. Browser-level console/render/responsive per route: NOT TESTED.

## D. Confirmed Bugs

### D-1 (P1) — Systemic backend latency
Evidence (production, real sessions, repeat runs):
| Endpoint | Time |
|---|---|
| `/api/health/` (no DB) | 2.5–2.6 s |
| `/api/health/?probe=db` | 2.6–2.8 s |
| `/api/documents/` | 10.9 s |
| `/api/timetable/conflicts/` | 11.8 s |
| `/api/dashboard/finance/` | 11.5 s |
| `/api/dashboard/exams/` | 12.8 s |
| `/api/reports/health/` | 10.9 s |
| `/api/library/books/`, `/api/exams/`, `/api/exams/results/`, `/api/transport/drivers/`, `/api/helpdesk/tickets/`, `/api/students/admissions/`, `/api/reports/enrollment/`, `/api/communication/announcements/` | ~9.5–11 s |
| `/api/students/?page=1&page_size=2` | 8.7 s |
| `/api/dashboard/overview/` | ~22 s |
| `/api/ai/overview/` | 19–29 s |
| `/api/dashboard/executive/` | 33 s |

Expected < 1–2 s. The app is effectively unusable in production.

**Root cause (deep-dive):**
1. A fixed per-request overhead of ~2.5–3.3 s even for a no-DB health check, reproducible warm across repeats (not cold start). A single `SELECT 1` adds only ~0.2 s, so the per-query cost is small; the overhead is connection/invocation + middleware work.
2. Five custom middlewares run on every request (`backend/config/settings/base.py:90-106`): `ActiveInstitutionMiddleware`, `CampusAccessMiddleware`, `ModuleAccessMiddleware`, `UsageTrackingMiddleware`, `LoginAttemptAuditMiddleware`. `ActiveInstitutionMiddleware` performs host/school resolution (1–2 `School` queries) and membership lookups on every request; `CampusAccessMiddleware` calls `user_allowed_campus_ids()` on every authenticated request, which itself issues profile/assignment/enrollment queries (`backend/apps/accounts/access.py:102-187`).
3. `apply_campus_scope()` calls `campus_access()` → `user_allowed_campus_ids()` again for every scoped queryset (`access.py:356-411`), so the campus lookup is repeated per query.
4. List/dashboard/AI views then add many sequential queries/aggregations (e.g. `dashboard_overview`/`_institution_overview_counts` in `backend/apps/dashboard/views.py:31-87`; `AiOverviewView` in `backend/apps/ai/views.py:53-105`). Super Admin is faster (~3.3 s baseline, dashboard 6.9 s) because global users skip campus scoping — confirming campus scope is a major cost multiplier for non-global roles.
5. Suspected additional factor: remote database with no effective persistent connection on serverless (Django `conn_max_age=600` does not reliably persist across serverless invocations).

### D-2 (P2) — `GET /api/reports/campus/students/` returns 500
- 500 for principal (non-global); **200 for Super Admin (global)** — role-scope dependent.
- **Root cause:** `BaseReportView.get_queryset` hardcodes `apply_campus_scope(queryset, request, "campus_id")` (`backend/apps/reports/base_views.py:156`). `CampusStudentCountReportView` uses the **Student** model (`backend/apps/reports/campus_views.py:19-30`), which has `primary_campus`, not `campus`. `apply_campus_scope` guards `institution_field` with `_model_has_path` but does **not** guard `campus_field` (`access.py:384-411`), so for non-global users it executes `filter(campus__isnull=True)` → `FieldError` → 500. Global users return before that filter, so they never hit it.

### D-3 (P2) — `GET /api/schema/` returns 500 for every authenticated role
Reproduced for Super Admin, principal, teacher and student (unauthenticated → 403). The OpenAPI schema is broken in production.

### D-4 (P2/P3) — Principal campus scope is inconsistent and empties data
- `/api/students/?campus=9` and `?campus=15` → 403 `"You do not have access to this campus."`
- `/api/auth/active-campus/` → `{"campus":null,"campuses":[]}`
- `/api/schools/campuses/` → Bloom (5 students) and Newbreath listed.
- **Root cause:** `principal` is not in `GLOBAL_ROLES` (`access.py:32-38`), so it is campus-scoped. `user_allowed_campus_ids()` derives scope from staff/teacher/student/guardian profiles and assignments (`access.py:134-187`); a principal with no such profile yields an empty set, so `apply_campus_scope` keeps only null-campus records → principal sees 0 students/teachers/attendance. `/api/schools/campuses/` does not apply the same scope, hence the inconsistency. No UI indication explains the empty data.

### D-5 (P2) — Temporary passwords never force rotation
8 of 9 tested accounts return `must_change_password:true`, but `frontend/src` contains **zero** references to `must_change_password` (grep). The SPA ignores the flag; temporary passwords remain valid indefinitely.

### D-6 (P2) — Unreachable LMS endpoint
`backend/apps/lms/urls.py` registers `questions/<int:pk>/` twice (lines 74–78 → `QuestionDetailView`, 84–88 → `QuizQuestionDeleteView`) and `quizzes/<int:quiz_id>/questions/new/` twice (69–73, 79–83). First match wins, so `QuizQuestionDeleteView` can never be reached; deleting a quiz question fails.

## E. UI / Page-Break (source-level, NOT browser-verified)
- Single global `ErrorBoundary` (`App.jsx:1065`): one crashing page blanks the entire route tree (shell survives).
- `ApprovalCard.jsx:38,51` unguarded `instance.definition_name`.
- `HealthPage.jsx:158` `count.toLocaleString()` on a possibly-null value.
- `StudentsPage.jsx:1246` `data.count.toLocaleString()` safe only via fetch-layer normalisation.
- Nav vs route guard mismatches: `Hostel` nav includes `academic` but the route denies it; `Announcements`/`Messages` have nav `roles:[]` but routes require explicit role lists → roles such as receptionist/librarian/guard can see a nav item then get "Access denied".

## F. API Errors (unexpected)
| Endpoint | Status | Role | Note |
|---|---|---|---|
| `/api/reports/campus/students/` | 500 | principal | D-2; 200 for Super Admin |
| `/api/schema/` | 500 | all authenticated | D-3 |
| `/api/dashboard/executive/` | 200 / 33 s | principal | D-1 |
| `/api/ai/overview/` | 200 / 19–29 s | all | D-1 |
| `/api/teachers/?page=999` | 404 `Invalid page.` | student | standard DRF |
| unknown `/api/*` | 404 `text/html` | any | Django HTML, not JSON |

## G. Security / Permissions — PASS (no authorization defects found)
- Super Admin platform routes all 200: `/api/auth/super-admin/schools/`, `/api/schools/tenants/`, `/api/white-label/domains|audit|branding|settings/`, `/api/saas/*`, `/api/audit/`, `/api/reports/health/`, `/api/auth/permissions|role-permissions|user-permissions/`.
- Non-super roles correctly 403 on `/api/schools/tenants/`, `/api/auth/super-admin/schools/`, `/api/white-label/domains|audit/`, `/api/finance/*`, `/api/reports/*`.
- `/tenants` and `/super-admin/schools/` are properly gated; no privilege escalation found.
- P4 informational: `/admin/` reachable (302 → login) on the backend domain; no CSP / Permissions-Policy; unknown API paths return HTML instead of JSON.

## H. Untested
- Roles: Institution Admin, Accountant, HR, Parent (no credentials).
- All browser-runtime concerns: JS console errors, React errors, modal/drawer/dropdown behaviour, form validation, CRUD create/edit/delete, uploads, print/export, responsive layout at 1440/1024/768/390, overflow/clipping.
- All write operations (read-only mandate): NOT SAFELY TESTED IN PRODUCTION.

## I. Overall Status — INCOMPLETE (PASS WITH ISSUES)
Authentication, routing, RBAC and SPA delivery are solid. However there are two confirmed 500s (D-2, D-3), a dead endpoint (D-6), an ignored password-rotation policy (D-5), a campus-scope inconsistency (D-4), and above all a P1 systemic latency problem (D-1) making the deployment effectively unusable. Remaining gaps: four untested roles and all browser-rendered behaviour.

### Priority recommendations (not applied)
1. P1 — Reduce per-request overhead: cache/avoid repeated `user_allowed_campus_ids()`, streamline the middleware stack, and add query optimisation to dashboard/AI aggregates.
2. P2 — Guard `campus_field` in `apply_campus_scope` (or pass the correct field in `BaseReportView`), fixing D-2.
3. P2 — Fix OpenAPI schema generation (D-3).
4. P2 — De-duplicate LMS URL registrations so delete works (D-6).
5. P2 — Enforce `must_change_password` in the SPA (D-5).
6. P2/P3 — Assign campuses to campus-scoped principals or surface an explicit "no campus assigned" state (D-4).
7. P3 — Isolate per-route errors with a route-level error boundary; guard the noted format/access expressions; align nav and route role guards.

## FINAL SAFETY CONFIRMATION
```
CODE CHANGES: NONE
DATABASE CHANGES: NONE
USER/ROLE CHANGES: NONE
DEPLOYMENT: NONE
COMMIT/PUSH: NONE
```
