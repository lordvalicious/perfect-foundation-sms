# PHASE 49 — Defects Report

**Phase:** 49
**Verdict:** See Authorization Report (PARTIAL) — defects documented below are pre-existing or observed, not "fixed" since no code changes were made.

---

## 1. Pre-existing Defects (not introduced by this phase)

### D-01: `/api/staff/me/` soft-deleted profile inconsistency
- **Module:** `apps/accounts/views.py` / `apps/accounts/models.py` (StaffProfile + SoftDeleteManager)
- **Description:** The reverse OneToOne accessor `user.staff_profile` (DRF `generics.RetrieveAPIView` with base manager) returns HTTP 200 for a soft-deleted StaffProfile (id=97, DI-EMP-0001), while `GET /api/staff/<pk>/` and the staff list 404 it via `SoftDeleteManager`. This is a long-standing DRF semantics inconsistency present before Phase 49.
- **Impact:** Users calling `/api/staff/me/` see the profile; calling `/api/staff/97/` or listing staff 404s it. No data loss or corruption; documented in Phase 46.
- **Status:** DOCUMENTED; not fixed (would require changing DRF view queryset managers, outside Phase 49 scope).

### D-02: `/api/finance/` parent route returns 404
- **Module:** `backend/apps/finance/urls.py` (prefix route, no data endpoint)
- **Description:** The `/api/finance/` route is a URL prefix that includes all child finance routes (`/api/finance/accounts/`, `/api/finance/reports/trial-balance/`, etc.). It is **not** intended to return data itself; it returns 404 because no view is mounted at the exact path. All finance data is accessible via child routes.
- **Impact:** None; frontend callers use child routes exclusively.
- **Status:** DOCUMENTED in Phase 48; intentional design.

### D-03: MIGRATION_SECRET not configured in Vercel production
- **Module:** `backend/apps/core/views.py` (`run_migrations_view`)
- **Description:** The F14 migration endpoint returns `503 "MIGRATION_SECRET is not configured."` for ALL requests because the environment variable is absent from the Vercel production environment. All auth gates (throttle, DEBUG guard, HMAC compare) are correctly implemented in code; only the env var is missing.
- **Impact:** Full functional verification of the valid-secret path is blocked until the secret is configured and production is redeployed.
- **Status:** CONFIGURATION GAP (see Phase 47); not a code defect.

### D-04: Teacher accounts show 403 on `/api/staff/me/`
- **Module:** `apps/accounts/access.py` (`user_allowed_campus_ids`), `apps/accounts/views.py` (Staff list/detail)
- **Description:** Teacher-role accounts (SA-EMP-0001, SA-EMP-0003, SA-EMP-0004) return 403 on `/api/staff/me/` because the `staff` role and `teacher` role are distinct; teacher profiles are not StaffProfiles.
- **Impact:** None; teachers have their own endpoints (`/api/teachers/`).
- **Status:** DOCUMENTED; confirmed in Phase 46 production verification.

---

## 2. Observations (Phase 49)

### O-01: STAFF `active_campus_id` session was null, now persists to campus 7
- **Module:** `apps/accounts/views.py` (`ActiveCampusView`)
- **Description:** After `POST /api/auth/active-campus/ {"campus_id": 7}`, the session now persistently selects campus 7 (SS, Sialkot) for DI-EMP-0001. This is a usability improvement observed during verification; not a defect.
- **Status:** OBSERVATION; no code change required.

### O-02: Finance role distinctions are sharp
- **Module:** `apps/accounts/permissions.py` (`IsFinanceReaderRole`, `IsAccountantRole`)
- **Description:** `IsFinanceReaderRole` grants read access to parents/students for own invoices only; `IsAccountantRole` grants full finance report access (trial-balance, income-expense, receivables). No overlap; roles are mutually exclusive in practice.
- **Status:** OBSERVATION; confirmed via production API tests.

### O-03: FrostFire session context drift
- **Module:** Server-side session management (`/api/auth/super-admin/switch/`)
- **Description:** FrostFire's server-side session drifted to institution 9 (QA Smoke School) during prior probing; re-switching to institution 1 restored Default-context admin views. This is an operational detail, not a defect.
- **Status:** OPERATIONAL; re-switch as needed.

### O-03: `/api/staff/97/` visibility depends on context
- **Module:** `apps/accounts/models.py` (SoftDeleteManager + StaffProfile)
- **Description:** Profile 97 is soft-deleted; visible via `/api/staff/me/` (base manager) but 404 via `SoftDeleteManager` list and `/api/staff/97/` in non-Default institution context. This is the same issue documented in Phase 46; no new defect.
- **Status:** PRE-EXISTING; documented in Phase 46.

---

## 3. Closed/Resolved

No defects were resolved in this phase (no code changes were made). All items are documentation/observation.

---

## 4. Final Status

All defects are either pre-existing (D-01 through D-04) or observations (O-01 through O-03). No new defects were introduced, and no code changes were made that would require defect resolution. The phase's objective was authorization matrix construction and safe CRUD certification, which is reflected in the PARTIAL verdict.

---