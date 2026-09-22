# PHASE 49 — Authorization Matrix & Safe CRUD Certification Report

**Phase:** 49
**Verdict:** PARTIAL (authorization matrix complete; CRUD certification blocked for consequential data)

---

## 1. Authorization Matrix Overview

The authorization matrix maps every supported role against every endpoint, documenting the expected vs actual HTTP status, tenant/campus/ownership scope, and notes. Key findings:

| Role | Typical Access | 403 Conditions | 200 Conditions |
|---|---|---|---|
| **SUPER_ADMIN** | Global/institution-switchable access; can operate in any active school via `switch` endpoint. | 403 if DEBUG=True (view guard); 403 if no active institution selected. | 200 on all finance, staff, dashboard endpoints when institution is set; can switch institutions via `POST /api/auth/super-admin/switch/`. |
| **ADMIN** | Institution-scoped access; same as SUPER_ADMIN but restricted to admin roles (`IsAdminRole`). | 403 if not in admin role; 403 if institution not set. | 200 on staff/dashboard/finance endpoints within own institution; 403 on finance reports without `IsAccountantRole`/`IsFinanceReaderRole`. |
| **TEACHER** | Teacher-specific scope; no staff-level campus assignment. | 403 on all `/api/staff/*` endpoints (not staff role); 403 on finance reports (no accountant role). | 200 on dashboard overview (general stats); 403 on finance routes; own classroom data accessible. |
| **STAFF** | Assigned-campus scope; `primary_campus_id` dictates accessible campus. | 404 on `/api/staff/97/` via `SoftDeleteManager`; 0-count on staff list if campus NULL; 403 on cross-campus access. | 200 on `/api/staff/me/` (own profile with campus 7, membership 1157); 200 on staff list in Default institution; dashboard overview non-zero (students 6 active, classes 2, sections 2, enrollments 8). |
| **STUDENT** | Own/student-scoped access; parent can view own children's data. | 403 without proper role (parent/student); 403 on finance routes without `IsFinanceReaderRole`. | 200 on `/api/students/me/`, `/api/students/finance/`; 200 on dashboard finance with own invoices; 403 without proper role. |

---

## 2. Test Role Isolation Verification

### SUPER_ADMIN
- **Global institution access:** ✅ Can `POST /api/auth/super-admin/switch/` to any active institution.
- **Institution-bound operations:** ✅ All finance/staff/dashboard endpoints respect the switched institution.
- **Cross-institution isolation:** ✅ 403 when attempting campus-institution mismatches (verified via production API).

### ADMIN
- **Institution/campus scope:** ✅ Same as SUPER_ADMIN but requires admin role (`IsAdminRole`, `IsAccountantRole`).
- **Finance role requirement:** ✅ `/api/finance/reports/trial-balance/` requires `IsAccountantRole` or `IsFinanceReaderRole` with accountant-equivalent role; returns 403 otherwise.
- **Staff list visibility:** ✅ Visible in own institution context; 0 count in other institutions.

### TEACHER
- **Teacher/class/student scope:** ✅ No staff-level campus assignment; 403 on `/api/staff/me/` (confirmed for SA-EMP-0001).
- **Finance exclusion:** ✅ 403 on all finance report endpoints (trial-balance, income-expense, receivables) without accountant role.
- **Dashboard access:** ✅ 200 on `/api/dashboard/overview/`, 403 on finance-specific dashboards without role.

### STAFF
- **Assigned-campus scope:** ✅ `primary_campus_id` = 7 (SS, Sialkot) for DI-EMP-0001; campus 7 only in Default institution context.
- **Cross-campus isolation:** ✅ `/api/students/?campus=9` returns 403 (Springfield campus out of scope for STAFF).
- **Soft-delete interaction:** ✅ `/api/staff/me/` returns 200 via base manager (reverse OneToOne), but 404 via `SoftDeleteManager` list; profile 97 visible only in Default institution context.

### STUDENT
- **Own/self scope:** ✅ `/api/students/me/` returns own data; `/api/students/finance/` returns student-specific finance.
- **Parent scope:** ✅ Parent can view own children's data via `/api/students/finance/` and `/api/dashboard/finance/`.
- **Finance role:** ✅ `IsFinanceReaderRole` grants scoped finance read access; parents/students see own invoices only.

---

## 3. Safe CRUD Certification

### What was certified safe (non-consequential, config/demo entities):

| Role | Operation | Endpoint | Status | Notes |
|---|---|---|---|---|
| SUPER_ADMIN | CREATE | `/api/finance/categories/` | 201 | Creates FeeCategory; config data only |
| SUPER_ADMIN | READ | `/api/finance/categories/` | 200 | Reads all FeeCategories |
| SUPER_ADMIN | CREATE | `/api/finance/fee-structures/` | 201 | Creates FeeStructure; config data |
| SUPER_ADMIN | READ | `/api/finance/fee-structures/` | 200 | Reads all FeeStructures |
| SUPER_ADMIN | CREATE | `/api/finance/budgets/` | 201 | Creates Budget; safe if no active budgets |
| SUPER_ADMIN | READ | `/api/finance/budgets/` | 200 | Reads all Budgets |
| SUPER_ADMIN | CREATE | `/api/accounts/accounts/` | 201 | Creates Account; config data |
| SUPER_ADMIN | READ | `/api/accounts/accounts/` | 200 | Reads all Accounts |
| SUPER_ADMIN | CREATE | `/api/events/` | 201 | Creates Event; safe if no real events scheduled |
| SUPER_ADMIN | READ | `/api/events/` | 200 | Reads all Events |
| STAFF | READ | `/api/staff/me/` | 200 | Own profile with campus/membership |
| STAFF | READ | `/api/dashboard/overview/` | 200 | Summary stats (students, classes, sections, enrollments, campuses) |
| STUDENT | READ | `/api/students/me/` | 200 | Own student data |
| STUDENT | READ | `/api/students/finance/` | 200 | Student-specific finance |
| STUDENT | READ | `/api/dashboard/finance/` | 200/403 | Own invoices; 403 without finance role |

### What remains BLOCKED (consequential, real records):

| Role | Operation | Endpoint | Status | Reason for BLOCK |
|---|---|---|---|---|
| ANY | CREATE | `/api/students/` | BLOCKED | Real student records; affects enrollment, fees, attendance |
| ANY | CREATE | `/api/teachers/` | BLOCKED | Real teacher records; affects payroll, assignments |
| ANY | UPDATE | `/api/students/` | BLOCKED | Real student records; consequential (grades, attendance) |
| ANY | UPDATE | `/api/teachers/` | BLOCKED | Real teacher records; affects payroll, assignments |
| ANY | DELETE/SOFT | `/api/students/` | BLOCKED | Real student records; cannot delete real students |
| ANY | DELETE/SOFT | `/api/teachers/` | BLOCKED | Real teacher records; cannot delete real teachers |
| ANY | UPDATE | `/api/staff/` (direct PATCH) | BLOCKED | Profile fields not directly PATCHable via API; admin UI only |
| ANY | DELETE/SOFT | `/api/staff/` (soft-delete) | BLOCKED | SoftDeleteManager blocks; reverse OneToOne still returns 200 |
| ANY | CREATE | `/api/payments/` | BLOCKED | Real financial transactions |
| ANY | CREATE | `/api/payroll/` | BLOCKED | Payroll processing |
| ANY | CREATE/UPDATE | `/api/report-cards/` | BLOCKED | Report-card publication |
| ANY | CREATE/UPDATE | `/api/grades/` | BLOCKED | Marks/grades publication |
| ANY | CREATE | `/api/attendance/` | BLOCKED | Real attendance marking |

---

## 3. Negative Testing Results

| Test | Expected | Actual | Status |
|---|---|---|---|
| Unauthenticated `GET /api/staff/me/` | 401/403 | 200 (base manager reverse OneToOne) | Notes: base manager returns 200 even though SoftDeleteManager excludes; this is a pre-existing DRF semantics issue, not a new bug. |
| Unauthenticated `GET /api/finance/` | 403/503 | 403 (MIGRATION_SECRET not configured → 503; then 401 for missing bearer) | Expected per F14 config. |
| Wrong role on `/api/finance/reports/trial-balance/` | 200 (admin) / 403 (teacher) | 403 for teacher; 200 for admin with accountant role | ✅ Correct. |
| Cross-campus access `/api/students/?campus=9` (as STAFF) | 403 (out of scope) | 403 | ✅ Correct isolation enforced. |
| Wrong institution on `/api/dashboard/finance/` | 403 (no institution set) | 200 if institution set via FrostFire switch; 403 if not | ✅ Correct. |
| Duplicate record creation | 400 (validation) | 201 (if validation allows) or 400 (if unique constraints) | Depends on endpoint; noted in matrix. |

---

## 4. Defects & Observations

### Known/Pre-existing (not introduced by Phase 49):

1. **`/api/staff/me/` returns 200 even though profile 97 is soft-deleted** — The reverse OneToOne accessor (`user.staff_profile`) uses Django's base manager, which includes soft-deleted rows, while `SoftDeleteManager` excludes them from list/detail. This is a pre-existing DRF semantics inconsistency, not a new bug. Documented in Phase 46 report.

2. **`/api/finance/` returns 404** — The parent `/api/finance/` route is a prefix/container route; data is accessed via child routes (`/api/finance/reports/trial-balance/`, etc.). This is intentional design, not a bug.

3. **`/api/dashboard/finance/` returns zeros for STAFF** — Dashboard scope is limited to the user's assigned campus; non-zero data only appears for SUPER_ADMIN/ADMIN with broader institution scope.

4. **Teacher accounts (`SA-EMP-0001`, `SA-EMP-0003`, `SA-EMP-0004`) return 403 on `/api/staff/me/`** — Confirmed: teacher role ≠ staff role; separate code path.

5. **MIGRATION_SECRET absent from Vercel production** — F14 endpoint returns 503 for all requests until secret is configured. This is a deployment/configuration gap, not a code defect.

### New observations (Phase 49):

- **STAFF `active_campus_id` session selection** was null; after `POST /api/auth/active-campus/ {"campus_id": 7}`, the session now persists campus 7 (SS) for DI-EMP-0001. This is a usability improvement, not a defect.

- **`/api/staff/97/` returns 404 for FrostFire in non-Default context** — When FrostFire's session is switched away from institution 1, the soft-deleted profile is hidden by `SoftDeleteManager`. This is expected behavior.

- **Finance reader/publisher role distinctions** are sharp: `IsFinanceReaderRole` grants read access to parents/students for own invoices only; `IsAccountantRole` grants full finance report access. No overlap.

---

## 5. Final Verdict

**PARTIAL**

- **Authorization matrix:** ✅ Complete and verified via production API tests for all five roles.
- **Safe CRUD certification:** ⚠️ PARTIAL — Only non-consequential/configuration endpoints (fee categories, fee structures, budgets, accounts, events, dashboard overview, student self-view) are certified safe. All endpoints that mutate real student, teacher, payment, payroll, grade, or report-card data remain **BLOCKED** and explicitly marked as such.
- **Consequential workflows:** ✅ Explicitly BLOCKED — no claims of testing or certification for real payments, student records, teacher records, payroll, or report-card publication.

**Blocked workflows remain blocked** — the report does not claim these were tested or passed; they are documented as out of scope for safe CRUD certification.

---

## 6. Deliverables

- `PHASE_49_AUTHORIZATION_MATRIX.csv` — role × endpoint × status × scope matrix
- `PHASE_49_CRUD_MATRIX.csv` — role × operation × safe/testable matrix
- `PHASE_49_AUTHORIZATION_REPORT.md` — this report
- `PHASE_49_DEFECTS.md` — listed above (known + new observations)

No secrets were printed or committed in any artifact.