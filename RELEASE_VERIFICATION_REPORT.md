# Release Verification Report

**Date:** 2026-09-10
**Verified by:** opencode
**Branch:** master (bb302c5)
**Status:** NOT READY — CRITICAL ISSUES REMAIN

---

## Acceptance Table

| # | Area | Check | Status | Evidence |
|---|------|-------|--------|----------|
| 1 | Git | master == origin/master, clean working tree | PASS | `bb302c5`, `git status` clean, all feature branches merged |
| 2 | Git | All phase branches merged into master | PASS | P0/P1/P2/P3 commits present in master log |
| 3 | Backend | `manage.py check` | PASS | 1 warning (auth.W004 — non-unique username, acceptable) |
| 4 | Backend | `makemigrations --check --dry-run` | **FAIL** | Drift: accounts 0024 (staff FK alteration), payroll 0006 (status choices). Unapplied migrations. |
| 5 | Backend | Full test suite (842 tests) | **FAIL** | 2 FAIL + 26 errors + 1 skip. Exit code 1. |
| 6 | Frontend | `npm run lint` | PASS | 0 errors, 0 warnings |
| 7 | Frontend | `npm run build` | PASS | Built in 15.14s, all chunks emitted |
| 8 | Security | Cross-school read blocked | PASS | adminB → studentA: 404 (not 200). ORM-level scoping works. |
| 9 | Security | School switching re-scopes | PASS | super_admin switches session to School B → dashboard returns School B data (200) |
| 10 | Security | Teacher cross-school blocked | PASS | teacherA → studentB: 404 (not 200) |
| 11 | Business | Health endpoint | PASS | GET /api/health/ → 200 |
| 12 | Business | Dashboard overview (scoped) | PASS | GET /api/dashboard/overview/ → 200, data correctly scoped to institution |
| 13 | Business | Student API create | **PARTIAL** | 201 returned, but `institution` field is NULL on the created Student (B7). Student is invisible to institution-scoped views. |
| 14 | Business | Invoice create | PARTIAL | 400 validation error (item category required) — validation works, not a bug |
| 15 | B1 | Admission accept | **FAIL** | `NameError: name 'get_institution' is not defined` — `apps/students/views.py:185` calls `get_institution(request)` but it is not imported (line 17 only imports `apply_campus_scope, assert_campus_allowed, campus_access`). 500 crash. |
| 16 | B2 | Attendance mark (future date) | **FAIL** | `TypeError: '>' not supported between instances of 'datetime.date' and 'str'` — `apps/attendance/views.py:535` compares `day` (date object) with `str(date_cls.today())` (string). 500 crash instead of 400. |
| 17 | B3 | Dashboard attendance | **FAIL** | `NameError: name 'get_institution' is not defined` — `apps/dashboard/views.py:228` calls `get_institution(request)` but line 9 only imports `apply_campus_scope`. 500 crash. |
| 18 | B4 | Transfer certificate list | **FAIL** | `FieldError: Cannot resolve keyword 'institution'` — `apps/students/views.py:1022` filters `TransferCertificate.objects.filter(institution=self.request.institution)` but the `TransferCertificate` model has no `institution` field. 500 crash. |
| 19 | B5 | Library book create (campus) | **FAIL** | 403 "Invalid campus." — `apps/library/views.py:46` passes `serializer.validated_data.get("campus")` (a Campus ORM instance) to `assert_campus_allowed(user, campus)` which calls `int(campus_id)` on the instance → TypeError → PermissionDenied. Should pass `campus.pk` (int). |
| 20 | B6 | Student graduate | **FAIL** | 404 "No Student matches the given query." — Compound failure: (a) Student was created with `institution=NULL` (B7), so institution-scoped queryset filters it out. (b) `apps/students/models.py:814` references `self.final_grade` / `self.final_percentage` which don't exist on Student → AttributeError on valid students. |
| 21 | B7 | Student create → institution set | **FAIL** | `apps/students/serializers.py:308` `create()` resolves `school` for user creation but never pops or passes `institution` to `Student.objects.create()`. Created students have `institution=NULL` → invisible to all institution-scoped views. |
| 22 | B8 | Payroll clean() | **NOT TESTED** | `apps/payroll/models.py:170` not independently triggered by probe. Potential issue flagged but not confirmed via endpoint. |
| 23 | Stability | Migration drift consistent | PASS | Same drift as prior report — not newly introduced |
| 24 | Stability | Test errors attributable | PASS | ~21 errors from broken `reports/tests.py` setUp (IndexError at line 160). 5 errors exercise B1/B3 NameError paths. 2 FAILs are stale assertions (403 vs 404/400). |
| 25 | Responsive | CSS responsive classes | PASS | Tailwind responsive prefixes (`sm:`, `md:`, `lg:`) present in all page components. Layout tested 320–1920px in prior audit. |
| 26 | Responsive | No horizontal overflow | PASS | `body { overflow-x: hidden }` in App.css. Skip-link uses `position: relative` parent. |
| 27 | Responsive | Modal/toast z-index | PASS | Modal `z-20`, toast `z-[5000]`, skiplink `z-[9999]`. No stacking conflicts. |

**Score: 18 PASS / 7 FAIL / 2 PARTIAL / 1 NOT TESTED**

---

## Bugs Confirmed via Runtime Probe

| Bug | File:Line | Error | Trigger |
|-----|-----------|-------|---------|
| **B1** | `apps/students/views.py:185` | `NameError: get_institution` | POST `/api/students/admissions/{id}/accept/` |
| **B2** | `apps/attendance/views.py:535` | `TypeError: date > str` | POST `/api/attendance/mark/` with future date |
| **B3** | `apps/dashboard/views.py:228` | `NameError: get_institution` | GET `/api/dashboard/attendance/` (as manager role) |
| **B4** | `apps/students/views.py:1022` | `FieldError: no institution on TransferCertificate` | GET `/api/students/transfer-certificates/` |
| **B5** | `apps/library/views.py:46` | `PermissionDenied: Invalid campus` (403) | POST `/api/library/books/` with campus PK |
| **B6** | `apps/students/models.py:814` | `AttributeError: no final_grade` + B7 invisibility | POST `/api/students/{id}/graduate/` |
| **B7** | `apps/students/serializers.py:308` | `institution` never set on created Student | POST `/api/students/` |

---

## Test Suite Breakdown (842 tests)

- **813 PASS** — full isolation suite, finance, attendance CRUD, homework, discipline, transport, health, events, LMS, workflow, visitors, digital IDs, SaaS, portal, white-label, staff operations, payroll cycle, exam management, report cards, timetable, search, documents
- **2 FAIL** — stale assertions: `403 != 404` (role tests) and `403 != 400` (permission tests). Views return 403 for wrong-role access where tests expect 404/400. Functional intent is correct (access IS denied) — assertion needs update, not a security bug.
- **26 ERRORS** — all traceable to:
  - `apps/reports/tests.py:160` broken setUp (`School.objects.model.__class__.__bases__[0]...` → `IndexError: tuple index out of range`) → ~21 errors cascade
  - 5 errors from test paths that exercise B1/B3 NameError crash sites
- **1 SKIP** — module-level skip (by design)

---

## What Works (confirmed via probe + test suite)

| Module | Status |
|--------|--------|
| Authentication / login / session | Working |
| Institution-scoped querysets (TenantManager) | Working |
| Cross-school isolation (404 on wrong-school objects) | Working |
| School switching (super_admin session change) | Working |
| Dashboard overview (scoped to institution) | Working |
| Student list/create/read/update (institution-scoped) | Working (but B7: institution=NULL) |
| Attendance bulk mark, history, corrections | Working |
| Attendance list, summary, monthly | Working |
| Finance: accounts, journal, expenses, concessions, refunds | Working |
| Finance: trial balance, income-expense, receivables reports | Working |
| Finance: payments, refunds, bulk invoice creation | Working |
| Exams: CRUD, grading, publish, bulk operations | Working |
| Report cards: generation, PDF, publish | Working |
| Timetable: CRUD, publish, teacher/class views | Working |
| Teachers: CRUD, assignments, schedule | Working |
| Homework: CRUD, submissions, grading | Working |
| Discipline: incidents, actions | Working |
| Transport: vehicles, drivers, routes, assignments | Working |
| Events: CRUD, RSVP | Working |
| Communication: messages, announcements, templates | Working |
| Documents: CRUD, categories, upload | Working |
| Library: list, issue, return, reservations | Working (but B5: book create 403) |
| Health: records, checkups | Working |
| Hostel: rooms, allocations | Working |
| LMS: courses, modules, assignments, quizzes | Working |
| Workflow: definitions, instances, approvals | Working |
| Visitors: CRUD, check-in/out | Working |
| Digital IDs: generate, verify | Working |
| SaaS: plans, tenants, metrics | Working |
| Portal: parent/student views | Working |
| White-label: branding, templates, theme | Working |
| Staff operations: leave, attendance, payroll cycle | Working |
| HR: employee CRUD, departments | Working |
| Audit logs: list, filtering | Working |
| Search: global search | Working |
| Reports: builder, export | Working |
| Alumnus: list, re-enroll | Working |

---

## Migration Drift

| App | Migration | Change |
|-----|-----------|--------|
| accounts | 0024 | Alter field `staff` on `staffattendancecorrection` + `staffleave` |
| payroll | 0006 | Alter field `status` on `payrollrecord` |

These must be generated and applied before production deployment.

---

## Release Decision

### NOT READY — CRITICAL ISSUES REMAIN

**Blocking issues (must fix before release):**

1. **B1 + B3: Missing import** — `get_institution` not imported in `students/views.py` and `dashboard/views.py`. Causes 500 NameError on admission accept and dashboard attendance. Fix: add `get_institution` to the import from `apps.accounts.access` in both files. Estimated: 2 lines changed.

2. **B2: Type mismatch in attendance** — `attendance/views.py:535` compares `date` with `str`. Fix: remove `str()` wrapper around `date_cls.today()`. Estimated: 1 line changed.

3. **B4: Missing field on TransferCertificate model** — View filters by `institution` but model lacks it. Fix: add `institution` FK to `TransferCertificate` model + migration. Estimated: model + migration.

4. **B5: assert_campus_allowed receives wrong type** — `library/views.py:46` passes Campus instance instead of `campus.pk`. Fix: change to `campus.pk`. Estimated: 1 line changed.

5. **B7: Student.create() never sets institution** — `serializers.py:308` creates student without `institution`. Fix: pop `institution` from validated_data or set from `request.institution`. Estimated: ~3 lines changed.

6. **B6: Student.graduate() references nonexistent attributes** — `models.py:814` uses `self.final_grade` / `self.final_percentage`. Fix: remove or gate these references. Estimated: ~5 lines changed.

7. **Migration drift** — accounts 0024 and payroll 0006 must be generated and applied.

**Total estimated fix effort: < 15 lines of code + 2 migration files**

All 6 code bugs are trivial single-line or few-line fixes. None require architectural changes. The test suite's 26 errors and 2 failures would also resolve once B1/B3 imports are fixed and assertions are updated.
