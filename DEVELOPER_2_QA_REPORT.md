# Developer 2 QA Report — Production-Focused Frontend QA (Session Report)

Branch: `developer-2-frontend` (no merge into `master`)
Latest QA session commit: `caad046` — `fix(frontend): show teacher campus and let managers file leave for staff`
Environment: Windows shell, no live browser/E2E. Verification = `eslint` (0 errors) + `vite build` (passes) + API-contract reproduction against a fresh Django test DB built from migrations (exact frontend requests, `APIClient.force_login` + `active_institution_id` session).

---

## Summary

Three HIGH-priority known issues were root-caused by reproducing the EXACT requests the
frontend sends, against the real backend serializers/views on a fresh test DB:

1. **Teacher profile — campus never displays** (FRONTEND, FIXED) — the teacher detail
   endpoint returns `primary_campus_name`; `ProfileModal`/`ProfilePage` read
   `profile.campus_name` (undefined) for the "Campus" field.
2. **Staff/HR leave request creation fails** (FRONTEND, FIXED) — the leave form never
   sent a `staff` member id, so an HR/admin user without their own linked staff profile
   received backend 404 `"No staff profile is linked to this account, and no staff member was selected."`
3. **Parent portal** (BACKEND-only issues surfaced) — all 9 portal endpoints resolve for a
   scoped parent (guardian/me, students, students/leave, attendance, report-cards, invoices,
   payments, timetable all return 200/paginated), with two exceptions that are backend-owned:
   `/api/communication/announcements/` raises a **500 on SQLite** (`JSONField contains`
   lookup unsupported), and a cross-tenant teacher-detail read.

All other medium/low audit items were spot-verified in code (Health campus selector,
Hostel dropdown scoping, Attendance mark flow, Academics filtering, Audit Log CSV export,
school-switch remount) with no frontend defect found.

---

# APPLICATION-LEVEL QA FINDINGS (production)

**QA REF # (A) — HIGH: FRONTEND-OWNED, FIXED**

### A-1. Teacher profile — "Campus" field never displays
- Page: `TeachersPage` → `ProfileModal` (view profile) and `ProfilePage` (own profile).
- Frontend request reproduced: `GET /api/teachers/<id>/` (admin session, credentials included).
- Actual backend response: `200` with `primary_campus_name: "Main Campus"` — the payload
  has **no** `campus_name` key for teachers (`TeacherSerializer.fields` exposes
  `primary_campus_name`, `source="primary_campus.name"`).
- Frontend read `profile.campus_name` → `DetailRow` renders nothing (empty-value rows are
  hidden). Field was silently blank.
- Also verified: `/api/teachers/me/` own-profile path works (200) with the same field.
- Fix: `value={profile.primary_campus_name || profile.campus_name}` in
  `ProfileModal.jsx:357` and `ProfilePage.jsx:419`.
- Status: **RESOLVED** (`caad046`).

### A-2. Staff / HR unable to create a leave request
- Page: `StaffOperationsPage` (`BASE = "/api/staff/"`), "New Request" form.
- Frontend request reproduced: `POST /api/staff/leave/` with body
  `{ leave_type, start_date, end_date, reason }` (no `staff`).
- Reproduced on a fresh test DB:
  - Staff member without manager role → `201` (backend auto-derives own `staff_profile`).
  - **HR/admin user with no linked staff profile → `404`**
    `{"detail": "No staff profile is linked to this account, and no staff member was selected."}`
    (`StaffLeaveListCreateView.perform_create`).
  - HR/admin WITH `staff` id → `201`.
- Root cause: the leave form had no staff selector and never sent the `staff` field that
  the backend already supports for manager-filed requests.
- Fix: added a staff-member `<select>` shown only to manager roles (`canReview`); payload
  sends `staff` only when selected; non-managers omit `staff` so their own profile is used.
- Also verified in the same run: leave list `?status=` (200), leave review action
  `POST /api/staff/leave/<id>/action/` (200, status transitions), staff list
  `GET /api/staff/?page_size=500` (200), attendance list+create (200/201),
  `/api/teachers/me/`, `/api/staff/me/`, `/api/students/me/`, `/api/auth/me/` (all 200),
  `/api/auth/active-institution|active-campus/`, `/api/schools/modules/current/`,
  `/api/schools/branding/` (all 200).
- Status: **RESOLVED** (`caad046`).

---

**QA REF # (B) — HIGH: BACKEND-OWNED APP ISSUES (DOCUMENTED FOR DEVELOPER 1)**

### B-1. Teacher detail endpoint — cross-tenant unauthorized read (non-manager branch)
- Module/Page: Teachers — `TeacherDetailView` used by `ProfileModal`/`ProfilePage`.
- Frontend request reproduced: `GET /api/teachers/<id>/` as an authenticated NON-manager
  user (staff role) with **no linked teacher profile**.
- Actual: **`200`** with full teacher record (`first_name`, `last_name`, `email`, `phone`,
  etc.). Reproduced on fresh test DB.
- Expected: teacher's own record only (or 403/404 for anyone else).
- Status: Confirmed bug.
- Frontend behavior: harmless to the UI (the UI only opens profiles for valid users), but an
  authorization/tenant leak.
- Likely cause: `backend/apps/teachers/views.py:127-134` — for a non-manager whose
  `get_teacher_profile(user)` is `None`, the queryset skips ALL filtering and stays
  `Teacher.objects.all()`. No institution filter is applied in that branch at all.
- Tenant impact: any logged-in student/staff/parent without a teacher profile can read the
  personal details of every teacher on the platform (cross-school too, since no school scope
  is applied).
- Recommended fix: in the non-manager branch, filter to the user's own profile when one
  exists; otherwise return an empty queryset (e.g. `filter(pk=-1)` or raise `NotFound`).
- Also: for managers, `institution_filter` uses `request.institution` with **no
  `get_current_institution()` fallback** (the list view at
  `backend/apps/teachers/views.py:27-40` HAS the fallback). When `request.institution` is
  `None` (fresh session, direct API), the filter becomes `Q(institution=None)` → 404 on all
  teacher details. Add the same fallback used by `TeacherListCreateView`.

### B-2. `/api/communication/announcements/` — 500 on SQLite (dev/test backend)
- Module/Page: Parent portal and Announcements — announcements fetch is one of the portal's
  data sources.
- Frontend request reproduced: `GET /api/communication/announcements/?page=1`.
- Actual: **500** `django.db.utils.NotSupportedError: contains lookup is not supported on
  this database backend` (SQLite). Works on Postgres (production).
- Likely cause: `backend/apps/communication/views.py:197`
  `Q(audience_roles=[]) | Q(audience_roles__contains=[role])` — JSONField `__contains`
  lookup is not supported on the SQLite backend in this setup. Consider splitting the filter
  so the `[]` case and Postgres path are handled without `__contains` on unsupported
  backends, or guard for SQLite (e.g. filter empty out separately).
- Frontend behavior: the Parent Portal shows its "couldn't load" section for announcements
  (graceful failure) — this is the only portal feed affected and only in sqlite dev.
- Impact: dev/test environments cannot load announcements; production (Postgres) unaffected.

---

**QA REF # (C) — MEDIUM: FRONTEND-OWNED** — No new medium frontend defects found this session.
Previously fixed frontend issues (AI page rebuild to `/api/ai/` contract, etc.) remain verified.

---

**QA REF # (D) — MEDIUM: BACKEND-OWNED** — See B-1/B-2. No additional medium backend findings
this session.

---

**QA REF # (E) — FRONTEND AUDITS (interface / auth / state per page-component)**

- **School switching stale data**: satisfied — `App.jsx:1057` keys `<Routes>` by
  `currentSchool?.id`, so every page fully remounts and refetches on switch.
  `schoolScopeVersion` is exposed but unused; pages do not depend on `activeCampus` from the
  shell (they own local campus/class filter state), so campus-switch does not leave stale
  data in any page. HELD.
- **HostelPage**: per-school `AbortController` (`scopeRef`) aborts all in-flight requests for
  the previous school; hostel/room/student selectors all gate on `schoolId` resolution.
  HELD.
- **Health (HealthRecordsPage)**: student selector is school-scoped
  (`GET /api/students/?page_size=1000`), campus shown per record from
  `row.campus_name`. No campus-selector defect. HELD.
- **AttendancePage**: roster → quick-set-all → per-student status → submit flow; loading
  flags disable double-submit (`saving`), Reset clears roster/existing. HELD.
- **AcademicsPage**: campus filter resets class; `visibleClasses` (by campus) and
  `visibleSections` (by class) are correct memos. HELD.
- **AuditLogsPage CSV export**: `GET /api/audit/?format=csv` (via `apiDownload`) — CSV
  includes Timestamp, User, Action, Model, Object, Object ID, IP Address, Details; respects
  all page filters; row cap 5000. No missing-fields defect. HELD.
- **Teacher own-vs-other isolation (read scope)**: teacher reading another teacher's detail
  → 404 (verified). Manager reads in-school teacher → 200. HELD (UI side); see B-1 for the
  non-manager backend gap.

---

**QA REF # (F) — BACKEND AUDITS (API contract / permission / isolation)**

- `GET /api/teachers/<id>/` — see B-1.
- `POST /api/staff/leave/` — contract verified (201 for staff, 201 for manager+staff field,
  404 documented message for manager no-profile/no-staff). HELD (frontend now sends `staff`).
- `GET /api/staff/leave/?status=`, `POST /api/staff/leave/<id>/action/`,
  `GET /api/staff/attendance/?date=`, `POST /api/staff/attendance/` — all verified 200/201.
- Parent portal chain (guardian/me, students list, students/leave list+create, attendance,
  report-cards, invoices, payments, timetable) — verified 200/201 for the scoped parent;
  foreign-child leave POST is still covered by existing backend portal tests.
  `communication/announcements` — see B-2.
- Own-profile chain (`/api/teachers/me/`, `/api/staff/me/`, `/api/students/me/`,
  `/api/auth/me/`) — verified 200.
- School/campus context endpoints (`active-institution`, `active-campus`,
  `modules/current`, `branding`) — verified 200.

---

**QA REF # (G) — SESSION-LEVEL / GLOBAL GUARDS**

- Route tree keyed by active school id → auth/context switch resets page state (see E).
- `scopedHasRole` evaluated against the ACTIVE school only; platform admins keep global
  access; UI fail-closed for unknown roles. HELD.
- Profile fetches are read-only (`GET`, `credentials: include`, no CSRF needed); mutations
  in teacher/staff CRUD use CSRF + `authHeaders`. HELD.

---

**QA REF # (H) — RECOMMENDATIONS / NEXT STEPS**

1. Developer 1: fix `TeacherDetailView` non-manager branch (B-1) and add the
   `get_current_institution()` fallback used by the list view.
2. Developer 1: make announcements audience filtering dialect-safe for SQLite dev (B-2).
3. Frontend follow-ups (nice-to-have, not blocking): row-level delete confirmations for
   staff leave and staff attendance; offline/targeted retry wording on the Parent Portal
   announcements section using the response status.
4. Live-session verification pass on a running Postgres instance for the parent portal
   announcements feed and teacher-profile rendering (reproduced here at API level only).

---

## Commit log (this session)
- `caad046` `fix(frontend): show teacher campus and let managers file leave for staff`
  — `ProfileModal.jsx`, `ProfilePage.jsx`, `StaffOperationsPage.jsx`. Lint 0 errors, build passes.
- (pending) `test(frontend): regression guards for teacher campus + staff leave selector`
  — adds `frontend/tests/staff-leave-manager-selector.test.mjs` and
  `frontend/tests/teacher-profile-campus.test.mjs` (zero-dependency Node source-inspection
  guards, same style as the existing hostel/branding guards) and wires them into
  `npm test`.

## Testing performed (this session)
- `npm test` — 22/22 pass (16 pre-existing + 6 new regression guards).
- `npm run lint` — 0 errors (10 pre-existing PayrollPage warnings).
- `npm run build` — passes.
- Backend Django suites for touched endpoints — `apps.accounts.test_regressions`,
  `apps.accounts.test_staff_attendance`, `apps.teachers.tests`, `apps.hr.tests`,
  `apps.portal.tests`: **42/42 OK**.
- Targeted API assertions on a fresh test DB simulating the FIXED UI payloads: 5/5
  (teacher detail 200 + `primary_campus_name` present; HR leave with `staff` → 201;
  staff own leave without `staff` → 201; HR without selection → 404 as designed).
---

# FINAL INTEGRATION QA (post-Developer-1-merge)

Baseline: `developer-2-frontend` synced with `master` via merge `2fa4f87`
(`Merge remote-tracking branch origin/master into developer-2-frontend`). Developer 1
fix `98db9d3` (`fix(backend): close teacher detail tenant leak and harden announcements filtering`)
and `d7a017b` (P0 tenant isolation) are present through the merge. Local `master` ref was stale
(local pointer at `eb7e2e9`; fixes came in through `origin/master`); branch HEAD verified clean.

## Baselines recorded
- Frontend tests: 22/22 pass; ESLint: 0 errors (10 pre-existing PayrollPage warnings); Vite build: passes.
- Backend suites run on the merged tree (fresh test DB, SQLite engine):
  - Targeted batches (261 tests, 0 failures): `accounts.test_regressions` 10/10;
    `teachers.tests` + `accounts.test_access` + `communication.tests` +
    `communication.test_phase7_isolation` 108/108; `students.tests` + `portal.tests` +
    `hr.tests` + `hostel.tests` 71/71; `finance.tests` + `attendance.tests` 72/72.
  - Account/event flows: 62/62 OK.
  - **Full suite (`DJANGO_SETTINGS_MODULE=config.settings.test`): 942 run, 0 failures,
    1 skipped, 21 partner-owned Reports errors - identical to the Developer 1 baseline.**
- TEST-MODE NOTE (important for anyone re-running): use `config.settings.test` for tests.
  `config.settings.development` applies real throttle rates (`login: 60/hour`); running the
  full/account/event suites under `development` blows the throttles inside one process and
  produces mass 429->403/404 cascades unrelated to code (verified: `apps.accounts.tests`
  + `apps.events.tests` = 40 failures under `development`, 62/62 OK under `test` settings
  in 11s). No merge or frontend regression involved.

## FINAL integration matrix (fresh test DB, exact frontend requests; 70/75 PASS)
- TEACHER AUTHORIZATION (16/16): own profile 200 + `primary_campus_name`; admin/manager 200;
  unauthorized staff / receptionist / student / parent all 404 (leak CLOSED, was 200 before 98db9d3);
  cross-school teacher 404 for teacher + admin; cross-campus teacher: non-manager 404, admin 200;
  invalid id 404; no-active-school non-manager-without-profile 404 (fail-closed via `get_current_institution`);
  teacher without active school still sees own 200.
- STAFF/HR (9/9): staff list/me, teacher me, HR-filed leave with `staff` as string id -> 201,
  staff own leave without `staff` -> 201, leave list 200, approve 2xx, employee create (HRPage contract) 201.
- STUDENTS (11/11): parent sees only own child (list + detail), cross-school student 404 for parent AND
  admin, admin CRUD (add -> enroll -> visible -> edit 200 -> delete 204), search 200, campus/class/section filters 200.
- ATTENDANCE (4/4): register list, summary, staff attendance, teacher register all 200 on live-data params.
- HEALTH (5/5): same-school record create/view/edit 201/200/200, cross-school student blocked,
  list school-scoped (admission number prefix check).
- HOSTEL (5/5): school-scoped hostel list, `room-hostels` selector contains the school's hostel
  (Add Room fix), room create 201, cross-school hostel room blocked, allocation 201.
  NOTE: room editing/deletion is NOT supported anywhere (no backend `/rooms/<pk>/` route and the
  HostelPage only POSTs) - documented, not a defect.
- PARENT PORTAL (10/11): guardian/me, children, attendance, timetable, report-cards, invoices, payments,
  notifications, teacher info 200 for a scoped parent; FAILS = announcements feed (see A/B below).
- CONTRACTS (6/6): auth/me, active-institution, active-campus, schools/modules/current, dashboard/overview 200.

## Surviving defect - handoff to Developer 1
### F-1 (P1, BACKEND, UNFIXED BY 98db9d3): announcements still 500 on SQLite for non-manager roles
- Reproduction (fresh test DB, SQLite): `GET /api/communication/announcements/?page=1` with a `parent`
  (also teacher/student) session ->
  `django.db.utils.NotSupportedError: contains lookup is not supported on this database backend` -> HTTP 500.
- Root cause: `backend/apps/communication/views.py` `scoped_announcement_queryset()` non-manager branch
  (lines ~196-213) wraps `queryset.filter(Q(audience_roles=[]) | Q(audience_roles__contains=[role]))`
  in try/except **but `filter()` is lazy** - the failing SQL is only generated at evaluation time
  (ListAPIView pagination `.count()`), outside the try block, so the exception is never caught.
- Manager roles are unaffected (verified 200) because `apply_campus_scope` is used without the role filter.
- Why tests missed it: `communication/test_phase7_isolation.py` only exercises manager/campus-admin
  roles for the list endpoint, never the parent/teacher/student branch.
- Suggested fix for Developer 1 (frontend cannot/should not work around a 500):
  - materialize the non-manager queryset and filter by `role in a.audience_roles` in Python for the
    SQLite fallback path (or check `connection.vendor`), or
  - add `audience_roles` filtering via `Q(audience_roles=[...])` exact-match per target role list
    built from role slugs, avoiding `__contains`.
- Impact: on SQLite dev/production the parent-portal "Announcements" section and the staff
  announcements page show the API error state (frontend already handles it - error banner + retry,
  no hang, no crash). Frontend requires no change.

## Frontend verdict after merged backend fixes
- No new frontend defects found. Teacher 404/403 handled by `ProfileModal`/`ProfilePage`
  (`profileErrorMessage`, error state, no infinite loading); announcements page renders
  loading/error/empty states (`StateArea`); school switching unaffected (routes keyed by
  `currentSchool.id` remount + scoped fetch guards already in place; regression guards 22/22 green).
- No frontend source changes were required on the merged tree.

## Ready to merge? 
- YES from Developer 2 for frontend: branch contains master via `2fa4f87`, working tree matches
  origin/developer-2-frontend, all frontend + targeted backend suites green. The ONE open item is
  backend F-1 (announcements SQLite 500) which is Developer 1-owned and does not block the frontend
  diff itself.
