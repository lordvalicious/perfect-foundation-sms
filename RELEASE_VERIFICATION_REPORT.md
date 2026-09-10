=== OPENCODE — FINAL SCHOOL ERP RELEASE VERIFICATION ===
Date: Thu Sep 10 2026
Branch: master (== origin/master, working tree clean)
Purpose: Section 10 acceptance + RELEASE DECISION for the School ERP.

=== EXECUTIVE SUMMARY

Runtime API probe (release_qa.py, config.settings.test, SQLite in-memory with
full middleware chain): PASS=45 FAIL=6 N/A=1 (3.7s).

All tenant-isolation and school-switching checks PASS. Every business workflow
that was reachable passed EXCEPT endpoints that crash on 6 confirmed runtime
bugs (all reached through the public API, all 5xx/403, none covered by the
existing test suite). The Django suite additionally fails 28 tests
(2 failures + 26 errors: 21 broken via reports/tests.py setUp, 2 stale
assertions, 5 tests exercising the two NameError 500s).

VERDICT: NOT READY FOR RELEASE / BLOCKED — see Section 10.

=== 1. REPO & BUILD
1.1 Git: master == origin/master; working tree clean; HEAD d8d5fa4
1.2 Backend: makemigrations --check → no drift; manage.py check ok
1.3 Frontend: `npm run build` PASS (vite build), `npm run lint` PASS
     (no test script exists in package.json)
1.4 Live Postgres NOT running on this host → runtime verification used
     config.settings.test (SQLite memory, throttle disabled) with full
     middleware chain.

=== 2. TENANT ISOLATION ARCHITECTURE (verified by code + runtime)

2.1 SoftDeleteManager (apps/core/models.py:53) is NOT tenant-aware — it only
    filters deleted_at__isnull. Tenant isolation is NOT enforced by the ORM
    tier for core models; it is enforced at VIEW tier via apply_campus_scope,
    campus_scoped, institution_queryset and assert_campus_allowed.
    => Security-sensitive dependency on view-layer discipline.
2.2 Tenant key: session active_institution_id (accounts/middleware.py,
    ActiveInstitutionMiddleware), resolution order domain → session →
    first active membership. Membership status defaults "active".

=== 3. SECTION 3-5 ACCEPTANCE TABLE (runtime probe results)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Superuser@A lists only School-A students | PASS | 200, 1 result (StudA) |
| 2 | Switch active school to B → only B students | PASS | 200, only StudB |
| 3 | Switch back to A → A students only | PASS | 200, only StudA |
| 4 | admin_A lists only School-A students | PASS | 200, count=1 |
| 5 | admin_A fetches School-B student id | PASS | 404 (scoped) |
| 6 | admin_A requests campus B1 | PASS | 403 (campus scoped) |
| 7 | campus_admin_A1 requests campus B1 | PASS | 403 |
| 8 | teacher_A list (assigned A1) never leaks B | PASS | 200 count=0 |
| 9 | unauthenticated API access | PASS | 403 |
|10 | create student + enroll | PASS | 201 create, 201 enroll |
|11 | student detail + PATCH edit | PASS | 200, 200 |
|12 | lifecycle withdraw + activate | PASS | 201, 201 |
|13 | admission create + review/submit | PASS | 201, 200 |
|14 | admission ACCEPT | FAIL | 500 NameError (bug B1) |
|15 | create teacher / create staff | PASS | 201, 201 |
|16 | invoice 10000+2000, pay 1000+5000 | PASS | 201s; balance 6000 |
|17 | overpayment rejected | PASS | 400 |
|18 | mark attendance (single) | FAIL | 500 TypeError (bug B2) |
|19 | bulk mark attendance | PASS | 200 created=1 (note B2-lite) |
|20 | attendance summary | PASS | 200, 100% present |
|21 | dashboard attendance endpoint | FAIL | 500 NameError (bug B3) |
|22 | create exam | PASS | 201 |
|23 | salary structure → payroll record → process → approve → pay | PASS | 201/200/200/200; pay-before-approve correctly 400 |
|24 | section-transfers list | PASS | 200 |
|25 | transfer-certificates list | FAIL | 500 FieldError (bug B4) |
|26 | report-cards list | PASS | 200 |
|27 | library book create | FAIL | 403 Invalid campus (bug B5) |
|28 | graduate student → alumni | FAIL | 500 AttributeError (bug B6); standalone alumni create 201 |
|29 | 400/401/403/404 error paths | PASS | correct codes |
|30 | 429 rate-limit | N/A | throttle disabled in test settings (verified in code; middleware active in prod) |
|31 | S8 stability 25x repeated /api/students/ | PASS | 0 errors; RTT 32–56 ms |

=== 4. CONFIRMED RUNTIME BUGS (new findings, all API-reachable)

B1. Admission accept 500 — apps/students/views.py:185
    NameError: name 'get_institution' is not defined.
    Fix: import get_institution from apps.accounts.access in the view (or use
    request.institution).
B2. Mark attendance 500 — apps/attendance/views.py:535 (single) and
    :198 (bulk, latent) — TypeError: '>' not supported between
    datetime.date and str (day > str(date_cls.today())).
    Fix: compare date objects: day > parse_date(str(date_cls.today())) or
    the inverse str(day) > str(...). Single-mark always 500; bulk only when
    date is parsed to a date object.
B3. Dashboard attendance 500 — apps/dashboard/views.py:228 — same NameError
    get_institution not defined.
B4. Transfer certificates 500 — apps/students/views.py:1023 —
    FieldError: Cannot resolve keyword 'institution' (TransferCertificate has
    no institution field).
    Fix: drop the filter; scope via campus__school or academic_year.
B5. Library book create 403 — apps/library/views.py perform_create passes a
    Campus INSTANCE into assert_campus_allowed, which does int(campus) →
    TypeError → PermissionDenied "Invalid campus." Always 403 for book
    creation.
    Fix: pass campus.id.
B6. Graduate 500 — apps/students/models.py:814 —
    AttributeError: 'Student' object has no attribute 'final_grade'.
    Student.graduate() reads self.final_grade/self.final_percentage; these
    fields exist on Enrollment, not Student.
    Fix: read from the active enrollment or accept via kwargs only.
B7. (Data consistency) apps/students/serializers.py StudentSerializer.create
    never sets institution → API-created students have institution=NULL, so
    they are invisible to institution-scoped views (was observed pre-fix as
    graduate 404; direct cause of mis-scoping for new students).
B8. (Latent) apps/hr/models.py:1462 PayrollPeriod.clean crashes with
    TypeError if payment_date is None (ORM create without payment_date);
    API create supplies it so reachable through API. Low risk.

=== 5. EXISTING TEST-SUITE FAILURES (already reported, unchanged)

842 tests / 167.4s → 2 failures + 26 errors.
- 21 errors: apps/reports/tests.py:121 setUp calls
  School.objects.model.__class__.objects.create_user (attribute fixture bug).
- 2 stale assertions: exams/test_exam_management.py:202 (expects 400, actual
  403); accounts/tests.py:1054 (expects 404, actual 403).
- 5 failures = B1+B3 NameError 500s exercised by test code.
Left unfixed: verification duty only.

=== 6. SECTION 8 — LONG-RUNNING / STABILITY  → partial

No browser or long-running server run possible on this host (no Postgres, no
dev server). Proxy evidence: 25x repeated authenticated list requests —
0 errors, stable RTT (p95 ~36 ms), no drift. Marked PARTIAL; recommend a
sustained soak on the deployed VPS.

=== 7. SECTION 9 — RESPONSIVE / UI  → NOT TESTED (browser)

No browser automation available here. Layout (320–1920), console/network
checks, no-black-screen, no-infinite-loader: MUST be confirmed on a browser
against the deployed app. Frontend build/lint pass from Section 1.

=== 8. SECTION 10 — ACCEPTANCE & RELEASE DECISION

Critical / blocking (release cannot proceed):
  B1 (admissions), B2 (attendance mark), B3 (dashboard), B4 (transfer certs),
  B5 (library), B6 (graduation) — six API-reachable 5xx/403 crashes on core
  daily workflows, masked because the test suite never calls these HTTP
  endpoints.

High (fix soon, independently verifiable):
  B7 institution=NULL on API-created students; B8 PayrollPeriod.clean guard;
  21 broken reports tests; 2 stale assertions.

PASSING as verified:
  School A/B isolation by role (admin/campus-admin/teacher), school
  switching, CRUD + lifecycle for students, admissions create/review, finance
  (invoices, payments, balances, overpayment), exam create, full payroll
  approval→pay cycle, sections/report-cards lists, error-code hygiene,
  rate-limit wiring, stability proxy, frontend build+lint.

DECISION: NOT READY / BLOCKED.
  6 release-blocking runtime bugs (B1–B6) confirmed at runtime on core
  workflows + 28 failing backend tests. B1–B6 each have known one-line
  fixes (Section 4), no schema migration required. Recommended gate: fix
  B1–B6, add HTTP-level tests for the 6 endpoints, fix reports/tests.py:121
  and the 2 stale assertions, then re-run this probe (target PASS=51) and the
  full suite before a green release.