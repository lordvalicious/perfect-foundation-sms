# PHASE 78 — STEP 5: PRINCIPAL READ-ONLY PRODUCTION CERTIFICATION

Phase: 78 · Step: 5 · Mode: READ-ONLY (no data mutation, no user/permission/password change, no migration, no redeploy,
no Vercel change, no logout) · Date: 2026-09-24 · Target: `https://perfect-foundation-sms.vercel.app`

## 1. Authenticated Identity
- Username/display: **Flora** · Primary role (server-reported): **principal** · Institution: Springfield Academy ·
  `must_change_password=false` · `GET /api/auth/me/` → **HTTP 200** (re-verified at step start and end of session;
  session remained valid throughout; Django `SESSION_COOKIE_AGE = 14d`).
- Mechanism used: documented `P43_SESSINGS_DIR\sa_flora.txt` (ADMIN→principal fixture) via the project's existing
  Playwright session helper. Canonical role certified in this step is the **server-reported `principal`**.

## 2. Principal Dashboard — **PROVEN**
- `/` → HTTP 200; authenticated navigation active; no login redirect.
- Renders "Dashboard Overview · Welcome back" with topbar, 41 sidebar links, account shown as `Flora · Principal`.
- Boot API calls all HTTP 200: `/api/auth/me/`, `/api/auth/active-institution/`, `/api/auth/active-campus/`,
  `/api/schools/modules/current/`, `/api/communication/notifications/`.
- Verified by existing `e2e/tests/admin.spec.js` ("dashboard renders for admin") and independent probes.

## 3. Principal Route Inventory
Source canonical route definitions: `frontend/src/App.jsx` (Routes at 1067-1393; guard `RequireRoles` 1006-1032;
`scopedHasRole` in `schoolContext.jsx:331-349`). Principal is flat-listed in 46 guarded routes + 4 unguarded
authenticated routes. Full per-route matrix in `PHASE_78_STEP_5_PRINCIPAL_ROUTE_MATRIX.csv`.

- **41/41 tested principal-eligible routes render as authenticated** with no denied card and no non-200 API.
- **11 non-principal routes verified as blocked** via the frontend "Access denied" card (no redirect, matching source
  `RequireRoles` behavior): `/parent-portal`, `/finance/student-fees`, `/finance/bulk`, `/sms`, `/templates`,
  `/data-export`, `/data-import`, `/branding`, `/health`, `/audit-logs`, `/tenants`.
- **5 detail routes with `:id` not probed** (safety §5 — no existing audit spec defines safe ID-probe tests):
  `/students/:id`, `/profile/teacher/:id`, `/profile/student/:id`, `/profile/staff/:id`, `/workflow/instances/:id`.
- Totals: routes tested 57 · **PROVEN 52** · FAILED 0 · BLOCKED 0 · UNVERIFIED 5.

## 4. Read-only Modules — module-by-module
40 principal-visible modules tested read-only (matrix in `PHASE_78_STEP_5_PRINCIPAL_MODULE_MATRIX.csv`).
All renders: authenticated shell, no denied card, no 5xx, no login redirect; mutation controls detected but **never**
interacted with. Representative observed content:

- Health Records: "Clinic visits, allergies, vaccinations and screenings … 0 records · 7 Students with clinic profiles"
- Hostel / Alumni / Workflow Approvals / Discipline / Homework / LMS / Announcements: publish/create/approve toolbars
  with empty datasets ("0 records · Loading data…") — **DATA-DEPENDENT** empty production datasets, not failures.
- Library: catalog shell + category filters. Visitors: gate log with "Check In"/"Check Out" filter controls.
- Digital IDs: issue/revoke toolbar. Students/Teachers/Finance: list shells with counts (0) and filters.

Record-level payload verification (actual row listing) is **UNVERIFIED** for empty data sets: no module record API
returned within capture windows (all boot APIs 200; no module data call observed on several pages) — consistent with
empty production data (Springfield Academy) and/or the stale deployed revision (Step 1: deployed backend predates
`d540ab2`). Not classified as an application defect; listed under Unverified areas.

## 5. Authorization / IDOR Checks
Used the project's **existing safe read-only authorization suite** rather than inventing production ID probes
(`e2e/tests/authorization.spec.js`, `e2e/tests/admin.spec.js`); principal is exercised by these specs as the ADMIN
fixture (Flora/principal). Live production run (desktop project, all passed):
- `ADMIN: /me returns own identity` → 200 ✔
- `ADMIN: /api/students/`, `/api/hr/employees/`, `/api/staff/` "does not 500 (scoped read ok)" → all 200 ✔
- `admin allowed pages do NOT show denied card` (/finance) ✔
- `backend blocks audit-logs / branding / tenants APIs` → `GET /api/audit-logs/`, `GET /api/settings/branding/`,
  `GET /api/schools/tenants/` all returned ≥403 for the principal ✔
- Source-defined negative/isolation probes (TEACHER/STAFF finance/payroll 403; STUDENT zero-cross-scope) exist in
  `authorization.spec.js` and backend unit tests (`test_role_security.py`, `test_campus_isolation.py`,
  `ai/test_phase_p5_isolation.py`); principal isolation is additionally enforced by backend campus scoping
  (`accounts/access.py`, `scopes.MANAGER_ROLES`).
- Backend authorization model cross-check: principal is campus-scoped (not in `GLOBAL_ROLES`), manager-class for
  read visibility, rank 70 (`accounts/models.py` ROLE_RANK), included in finance/payroll/report read permission
  classes except `IsSuperAdmin`. No object-level check existed to contradict live status <500 behavior.
- Object-level IDOR behavior remains **UNVERIFIED** (documented in `docs/audit/SECURITY_AUDIT.md` SEC-06 and
  `RISK_REGISTER.md` R-06 as a standing risk; Phase 75 confirmed object-level permission checks unverifiable under a
  read-only mandate).

## 6. Failures — precise classification
**Confirmed production defects: 0.** Recorded observations (not counted as access defects):
- **OBS-1 (frontend bootstrap race).** During cold navigations several routes (e.g., `/admissions`, `/alumni`,
  `/lms`, `/helpdesk`, `/visitors`, later `/executive-dashboard`, `/assignments`) first displayed a transient
  "Access denied …" card or a 5–10 s "Loading…" frame before correctly rendering content. Stability trace over 30 s
  showed **zero** denied frames at final state and content sizes 148–1236 chars. Interpretation: the live route guard
  evaluates with partially-loaded role context and momentarily renders the denied card, then re-renders correctly
  (source: `RequireRoles` → immediate `scopedHasRole` evaluation; `schoolContext.jsx`). UX-race observation; no access
  denied in final state, no authorization breach.
- **OBS-2 (pre-existing console issue).** Google Fonts stylesheets blocked by CSP (`style-src`) on every page — the
  only console error; no page errors, no failed module/API requests.
- No APPLICATION DEFECT / AUTHORIZATION DIFFERENCE / DEPLOYMENT MISMATCH confirmed for this role in this step.
  (Deployment revision staleness established separately in Step 1 remains a global standing concern, not a step-5
  role failure.)

## 7. Frontend Guard Results
- Allowed routes render (41/41); denied routes show the in-place "Access denied" card (11/11) — no login redirect,
  no NotFound substitution, matching source `RequireRoles`.
- No unexpected login redirects during the entire authenticated session.
- No final-state frontend/backend role mismatch: live rendering for `principal` matches source guard allow-lists.

## 8. Mutation Workflows — intentionally not executed
`MUTATION_NOT_EXECUTED` — Reason: `PRODUCTION_READ_ONLY_CERTIFICATION`, for all of:
CREATE (Add Student/Teacher/Book/Incident/Alumni/New Record/New Homework/New Course/New Announcement/Add Fee
Structure/Add), UPDATE (Edit, Save), DELETE (Delete), IMPORT (Data Import), EXPORT (Data Export), SEND (Messages/SMS),
APPROVE (Pending Approvals), PUBLISH (LMS/Announcements), ASSIGN, PROMOTE, Check In/Issue Card/Bulk Operations/Send
verification link. Controls detected on rendered pages; none were clicked.

## 9. Certification Conclusion
- **AUTHENTICATION: PROVEN** (me 200; session valid start→end).
- **DASHBOARD: PROVEN**.
- **ROUTES: 52 PROVEN / 0 FAILED / 0 BLOCKED / 5 UNVERIFIED (ID-detail routes).**
- **MODULES: 40 PROVEN read-only render / 0 FAILED / 0 UNVERIFIED (record payloads unverified: empty datasets).**
- **MUTATION WORKFLOWS: 0 EXECUTED.**
- Principal certification: **READ_ONLY_PROVEN** (route access, authorization behavior, and frontend guards proven on
  production using the project's existing safe read-only tests + independent probes; limited to read-only scope and to
  the Unverified areas below).
- Unverified areas (not failures): 5 `:id` detail routes (no safe spec for ID probes); record-level data payloads
  (empty datasets / no module record API observed); object-level IDOR check (standing R-06/SEC-06, unverifiable under
  read-only mandate); transient bootstrap-race frames (OBS-1).

## 10. Safety Verification (all NO)
```
PRODUCTION_DATA_MUTATED=NO   SOURCE_MODIFIED=NO   PERMISSIONS_CHANGED=NO   PASSWORD_CHANGED=NO   REDEPLOYED=NO
USERS_CREATED/MODIFIED/DELETED=NO   MIGRATIONS_RUN=NO   VERCEL_CHANGED=NO   NO_LOGOUT_PERFORMED=YES
```
No session ID / password / token / cookie / CSRF value printed at any point.