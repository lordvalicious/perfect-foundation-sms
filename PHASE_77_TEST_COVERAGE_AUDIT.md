# PHASE 77 - STEP 11: TEST COVERAGE AUDIT

Phase: 77
Date: 2026-09-24
Method: READ-ONLY audit of all automated test files across backend (Django test runner output in `pytest_*.txt` logs + `apps/*/tests.py` and `apps/*/tests/` directories). Frontend test presence checked via glob. No test execution performed this phase (environmental read-only; historical logs analyzed).

---

## 1. BACKEND TEST FILES SUMMARY (by app)

| App | Test files | Test coverage summary | Historical pytest log result |
|-----|-----------|----------------------|------------------------------|
| accounts | 14 | Login/session/2FA, access/permissions, auth hardening, campus isolation, SSO, lockout, performance, permission seeding, regressions, role security, school auth, provisioning, staff attendance, 2FA backup | pytest_accounts: 252 tests OK; pytest_access: 55 OK |
| ai | 4 | service auditing, role access, insights, tenant/campus isolation | (ai logs OK per phase suite) |
| alumni | 1 | write tenant isolation | - |
| attendance | 1 | model + correction | - |
| audit | 4 | CSV export, CSP cleanup/reporting, phase9 audit | - |
| communication | 3 | notifications queue/cron, announcement audience, phase7 isolation | - |
| core | 1 | run-migrations authz + throttle | - |
| dashboard | 2 | overview/executive, phase8 isolation | pytest_dashboard: 43 OK |
| digital_ids | 1 | card issue/reissue/revoke | pytest_digital_ids: 6 OK |
| discipline | 0 | **NO TESTS** | - |
| documents | 0 | **NO TESTS** | - |
| events | 1 | CRUD, audit, published-only | pytest_events: 4 OK |
| exams | 6 | model, cross-school, management, schedule, marks/grades, tenant isolation | pytest_exams: 74 (1 failure 403!=400) -> pytest_exams2: 74 OK |
| finance | 2 | model, late fee, fee assignment, outstanding, payment integrity, security, receipts, concessions, journal, expense, fine, adjustment, refund, accountant isolation, jazzcash security, receivables aging | pytest_finance: 64 OK |
| health | 0 | **NO TESTS** (cross-app HealthRecordCampusFromEnrollmentTests in accounts) | - |
| helpdesk | 1 | staff + self-service | pytest_helpdesk: 10 OK |
| homework | 0 | **NO TESTS** | - |
| hostel | 1 | room selector/security/e2e, allocation policy | pytest_hostel: 0 (historical, now resolved) |
| hr | 1 | HR models | pytest_hr: 4 OK |
| inventory | 2 | asset isolation, stock engine/level/movement/summary, stock tenant isolation | pytest_inventory: 20 OK |
| library | 1 | book campus isolation only | pytest_library: 1 OK |
| lms | 0 | **NO TESTS** | pytest_lms: 0 |
| payroll | 1 | salary structure, payroll record, lifecycle, export | - |
| portal | 1 | teacher/student/parent portals + announcements | pytest_portal: 16 OK |
| reportcards | 3 | model, list, pdf, grade scale, result lifecycle | pytest_reportcards: 21 OK |
| reports | 2 | core catalog, campus filter, scoped user, permission, payroll report views | - |
| saas | 1 | feature flags, subscriptions, plans, usage analytics, health checks, brute force audit, tenant provisioning, daily snapshots | pytest_saas: 76 OK |
| schools | 4 | academic structure, branding, section detail, media views, tenant isolation, module enforcement, public admission | pytest_schools: 14 OK |
| search | 0 | **NO TESTS** (isolation covered by dashboard SearchFilterPaginationTests) | - |
| students | 6 | lifecycle, 360, docs isolation, transfers, certificate verify, capabilities | pytest_students: 39 OK (1 skip) |
| teachers | 1 | teacher assignment model, API regressions | pytest_teacher: 1 ERROR (historical harness bug: wrong module name) |
| tests (shared harness) | 1 | cross-school/campus access, IDOR, scoping, super-admin switching | - |
| timetable | 2 | model, period/entry isolation, conflicts | pytest_timetable: 26 OK |
| transport | 0 | **NO TESTS** | - |
| visitors | 1 | gate check-in/checkout/stats/scoping/role denial | pytest_visitors: 5 OK |
| white_label | 1 | branding, settings, domain, API, audit | pytest_white_label: 24 OK |
| workflow | 1 | engine + api | pytest_workflow: 21 OK |

## 2. AGGREGATE BACKEND COUNTS

- Apps with tests: **30 of 37**
- Test files: **~71**
- Apps WITHOUT any test: **7** — `discipline`, `documents`, `health`, `homework`, `lms`, `search`, `transport` (TPR-009)
- Reported historical results (pytest logs): mostly `OK`; 2 anomalies:
  1. `pytest_exams.txt` — 1 failure `AssertionError: 403 != 400` in `test_exam_cross_institution_campus_rejected`; **re-ran green** in `pytest_exams2.txt` (74 OK) → no persistent defect; flag as flaky assertion to stabilize.
  2. `pytest_teacher.txt` — 1 error `ModuleNotFoundError: No module named 'apps.teacher'`; harness script bug (app is `teachers`), resolved since (TPR-012).

## 3. FRONTEND TEST COVERAGE

- **ZERO** test files found (`*.test.*`, `*.spec.*`) anywhere under `frontend/`.
- No Vitest/Jest config, no Playwright/Cypress setup, no UI harness.
- 58 pages + 13 components + route guards + `api.js`/`auth.jsx`/`schoolContext.jsx` have **no automated tests** (TPR-010).

## 4. COVERAGE GAP ANALYSIS

| Gap | Severity | Detail |
|-----|----------|--------|
| 7 apps with zero tests (TPR-009) | HIGH | Discipline, Documents, Health, Homework, LMS, Search, Transport — all user-facing modules |
| Zero frontend tests (TPR-010) | HIGH | No regression safety for UI, guards, or API client |
| Library mutation paths untested | MEDIUM | Issue/return/reservations have no direct app-level tests (isolation test only) |
| Finance bank reconciliation, budgets, finance reports | MEDIUM | No dedicated tests (models only) |
| HR leave/compensation/payroll-periods/recruitment/exit | MEDIUM | No dedicated tests beyond base HRModelTests |
| Report builder, export/backup, import | MEDIUM | No dedicated tests |
| AUTH-tested surface | HIGH | All 18 roles' production behavior untested (environment) |

## 5. STRENGTHS (POSTIVE EVIDENCE)

- **Auth/security suites are exceptional**: 14 files in accounts covering lockout, escalation, school auth, provisioning, 2FA backup, role security, isolation.
- **Tenant/campus isolation is well covered**: dedicated shared harness in `apps/tests/` + per-app isolation tests across ai, communication, dashboard, events, exams, inventory, students, timetable, schools, reportcards, saas, alumni.
- **Exams math heavily tested**: percentage, GPA, grade boundaries, pass/fail, invalid marks, seating conflicts, tenant isolation.
- **Finance integrity strong**: payment integrity, receipts, concessions, fines, adjustments, refunds, jazzcash security, receivables aging.
- Historically flaky exams assertion re-ran green — no persistent failure evidence.

## 6. VERDICT

Backend test infrastructure is robust where it exists (30/37 apps). The certification-critical blockers are (a) 7 zero-test apps, (b) zero frontend tests, and (c) the environmental blocker that prevents exercising ANY authenticated production path (all 120 code-complete features remain AUTH_TEST_BLOCKED regardless of unit coverage). No test output indicates a confirmed production defect beyond the deploy-test 404 (deployment artifact, TPR-001) and the LMS question-delete route override (TPR-008), both code-level findings independent of tests.

---

*This document is part of PHASE_77_COMPLETE_FUNCTIONAL_STATUS_REPORT deliverables. No files modified.*