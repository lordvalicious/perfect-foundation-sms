# PHASE 42 — DEFECTS REPORT

Re-certification sweep of the deployed production API
(`https://perfect-foundation-api.vercel.app/`) using live sessions for
SUPER_ADMIN, ADMIN, TEACHER_01, STUDENT_01 and STAFF_01. All timings and
statuses below are **fresh evidence** captured during this phase.

Methodology:
- 138 role-endpoint probes across 88 unique endpoints / 40 modules.
- Sessions: SUPER_ADMIN (FrostFire), ADMIN (Flora), TEACHER_01
  (SA-EMP-0001), STUDENT_01 (SA-ST-0001), STAFF_01 (DI-EMP-0001).
- Raw evidence: `PHASE_42_RAW_SWEEP.csv`.
- Per-chain evidence (endpoint returns data scoped to the caller's role)
  was required before marking any row PASS.

## 1. Root Causes Fixed in This Phase

### R-001 (RESOLVED) — Payroll report endpoints returned HTTP 500
- **Endpoints:** `/api/reports/payroll/*` (8 children) and
  `/api/reports/payroll-summary/`.
- **Symptom observed at start of phase:** all endpoints returned HTTP 500.
- **Root cause:** report views referenced pre-refactor payroll fields. The
  payroll module had been migrated to `PayrollRecord.employee`
  (FK -> `hr.Employee`), `salary_structure`, `campus`,
  `payroll_period` and a JSON `component_details` (allowances/deductions)
  shape, while the report views still read `record.teacher`,
  `record.salary_structure_id`, `record.allowances_breakdown`, etc.
- **Fix:** `backend/apps/reports/hr_views.py` — all 8 payroll report views
  rewritten to the new employee schema using `apply_campus_scope`;
  `backend/apps/reports/extended_views.py::PayrollSummaryReportView`;
  dead methods in `backend/apps/payroll/services.py` aligned.
- **Regression tests:** `backend/apps/reports/test_payroll_report_views.py`
  (7 tests). Suites: payroll+reports = 46 OK; hr/teachers/finance = 85 OK.
- **Deployed:** commits `cb2041a`, then performance commits `2a41468`
  and `7740e02`.
- **Fresh verification (production):** all 8 payroll-report endpoints + the
  payroll-summary endpoint now return HTTP 200 in **4.9–6.6 s** with correct
  data (monthly/net-salary/paid each return 438 records).

### R-002 (RESOLVED during this phase) — Payroll monthly/net/paid reports ~103 s (N+1)
- **Symptom:** after R-001, monthly/net-salary/paid returned 200 but took
  ~103–105 s (cold/warm), far above the 15 s target.
- **Root cause:** `Employee.full_name` is a Python property that resolves
  reverse OneToOne relations (`staff_profile`, `teacher`) with one query
  per row; 438 payroll records -> ~900 extra queries.
- **Fix:** added `.prefetch_related("employee__staff_profile",
  "employee__teacher")` to the `get_base_queryset` of the monthly,
  employee-salary, net-salary, paid and pending report views.
- **Fresh verification (production):** monthly 6.6 s, net-salary 6.1 s,
  paid 6.1 s with 438 rows each.

## 2. Regressions Detected vs Phase 37

| ID | Module | Endpoint | Phase 37 | Phase 42 | Severity | Evidence |
|----|--------|----------|----------|----------|----------|----------|
| D42-01 | Finance | `/api/finance/reports/` | 200 | **404** | MEDIUM | Fresh probe (4.2s) |

**D42-01 detail:** Phase 37 recorded `/api/finance/reports/` as HTTP 200
(PASS). In Phase 42 the parent path returns 404, but the actual report
endpoints moved to children:
- `/api/finance/reports/trial-balance/` -> 200
- `/api/finance/reports/income-expense/` -> 200
- `/api/finance/reports/receivables/` -> 200

The finance URLs were refactored (latest commit touching
`backend/apps/finance/urls.py` is `7431495`). This is a **routing rename,
not a lost feature**, but any client pinned to the old parent path is broken.
Recommendation: add a parent view at `/api/finance/reports/` that aggregates
or documents the child routes, or confirm the frontend was updated.

## 3. Improvements vs Phase 37

| ID | Module | Endpoint | Phase 37 | Phase 42 |
|----|--------|----------|----------|----------|
| I42-01 | AI | `/api/ai/insights/students/` | 403 | **200** |
| I42-02 | AI | `/api/ai/insights/attendance/` | 403 | **200** |
| I42-03 | AI | `/api/ai/insights/academic/` | 403 | **200** |
| I42-04 | AI | `/api/ai/insights/finance/` | 403 | **200** |
| I42-05 | AI | `/api/ai/anomalies/` | 403 | **200** |

AI insights and anomalies endpoints now return HTTP 200 for SUPER_ADMIN
(fresh probes: 5.1–9.2 s), instead of Phase 37's 403.

## 4. Unresolved Defects

### Missing endpoints (404 for all tested) — UNIMPLEMENTED
22 unique routes return 404 and have no functional replacement:

| Module | Endpoint |
|--------|----------|
| Auth | `/api/accounts/me/` |
| Auth | `/api/accounts/roles/` |
| Finance parent | `/api/finance/` |
| Reports parent | `/api/reports/` |
| Timetable | `/api/timetable/` |
| LMS | `/api/lms/` |
| Library | `/api/library/` |
| Transport | `/api/transport/` |
| Inventory | `/api/inventory/` |
| Helpdesk | `/api/helpdesk/` |
| Visitors | `/api/visitors/` |
| Digital IDs | `/api/digital-ids/` |
| Workflow | `/api/workflow/` |
| Discipline | `/api/discipline/` |
| Health Records | `/api/health-records/` |
| Hostel | `/api/hostel/` |
| Portal | `/api/portal/` |
| SAAS | `/api/saas/` |
| Dashboard Summary | `/api/dashboard/summary/` |
| Settings | `/api/settings/` |
| Branding | `/api/branding/` |
| Audit Logs | `/api/audit-logs/` |

### 4xx that are by design (retained as expected)
- `/api/auth/login/`, `/api/auth/logout/`, `/api/ai/ask/`,
  `/api/ai/communication/draft/` -> 405 on GET (POST-only). Correct.
- `/api/reports/payroll/salary-slip/` without `employee` -> 404
  "No payroll records found". Correct; 200 path verified by regression test.

### Unresolved pre-existing issues (carried over, unchanged scope)
- **STAFF_01 profile/campus repair** (from earlier phase): blocked on DB/data
  repair; `unique_staff_employee_number_per_institution` includes soft-deleted
  rows -> IntegrityError. Needs DBA action.
- **F14 (MIGRATION_SECRET) hardening:** deployed but not fully verifiable
  because `MIGRATION_SECRET` is not configured in Vercel env.
- **Student endpoints latency:** `/api/students/` and classmates remain in
  the 10–16 s band for non-super roles; several are just above the 15 s
  target. UNRESOLVED-RISK.

## 5. Summary Statistics

- Unique endpoints checked: **88**
- Total role-endpoint probes: **138**
- PASS (HTTP 200 with expected scoped data): **101**
- FAIL (HTTP 404, no replacement): **22**
- Expected 403 (role denied): **9**
- Expected 405 (POST-only endpoint): **4**
- Expected 404 (salary-slip without param): **1**
- Deprecated/renamed (finance reports parent): **1**
- Parent 404 (children work): **1** (finance) + 1 (reports) counted above

## 6. Verdict Contributing Items
- Payroll report regression (HTTP 500) **fully resolved** and re-verified live.
- Payroll report performance (103 s -> ~6 s) **fully resolved**.
- AI insights/anomalies authorization **resolved**.
- One medium regression introduced since Phase 37: finance reports parent path
  (D42-01) — routing rename, children functional.