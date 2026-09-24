# PHASE 83 — Contradiction Log

Repo: `C:\Users\Ryuk\Documents\perfect-foundation-sms` · branch `master` · HEAD `2df1989d11009380f0a818e0cd5ac9b1f049f325`
Phase: READ-ONLY diagnosis — no fixes applied.
Baseline: extend of CON-82 series (Phase 82) — see `PHASE_82_CONTRADICTION_LOG.md`.

---

## CON-83-01 — "Designations create specialized-role accounts" vs. "serializer hardcodes Role.STAFF"

**Claimed:** Creating a staff account for (e.g.) a Librarian, Security Guard,
Nurse produces an account with the specialized role (owner assertion in
Phase 80/82 narrative).
**Proven:** `backend/apps/accounts/serializers.py:349-352`
`_build_user_account` creates the RoleAssignment with `role=Role.STAFF`,
ignoring `designation` entirely. No designation→role mapping exists anywhere
in the account-creation path.
**Impact:** Every such account authenticates (LoginView is role-independent,
`views.py:237`), but is denied by every specialized route guard and many
backend permission classes.

## CON-83-02 — "Counsellor / Administrative Officer accounts exist and work" vs. "no such canonical role exists"

**Claimed:** Counsellor and Administrative Officer are legitimate
provisionable roles (owner narration; `demo_seed/part2_people.py:28-39`
lists "Counsellor" and "Admin Officer" designation strings).
**Proven:** `models.py:11-29` `Role` enum has **no** `counsellor` and **no**
`admin_officer`/`administrative_officer` choice. Even a corrected
designation→role mapper could not resolve these to a valid Role.
**Impact:** ROLE_RESOLUTION_FAILURE — a new canonical role must exist before
these designations can authenticate into a non-staff account. Secondary:
`_campus_role_users` in `demo_seed/base.py:102-122` demonstrates the intended
librarian→LIBRARIAN / guard→GUARD mapping the owner believes is universal,
but that path is only used for a handful of named demo users.

## CON-83-03 — "Seeded staff can log in" vs. "seed_staff creates no User/RoleAssignment"

**Claimed:** The five accounts were created/seedable via seed data such that
they can log in.
**Proven:** `backend/apps/accounts/management/commands/seed_staff.py` creates
**only StaffProfile rows** — no `User`, no `RoleAssignment`. Any login-capable
account must therefore have come from the **Staff module UI/serializer**
(`StaffListCreateView`, `views.py:1124` + `serializers.py`), which produces
`role=staff`. Meanwhile `demo_seed/part2_people.py` `seed_support_staff`
explicitly assigns `Role.STAFF` to all support staff including Nurse/Security
Guard — reproducing the same generic-staff misclassification in the demo seed.
**Impact:** Two independent provisioning paths both deposit these designations
into the `staff` role; neither was created with the canonical role.

## CON-83-04 — "5/5 can log in" vs. "no fixture/session evidence is obtainable"

**Claimed:** Live demonstration of login for all five accounts.
**Proven:** No credentials/session fixtures exist for these accounts
(`e2e/helpers/session.js:4-12` ROLE_FILES cover SUPER_ADMIN/ADMIN/TEACHER/
STUDENT/STAFF only). Read-only phase forbids session fabrication and login
POSTs. Login success is therefore **attested by the system owner + supported
by code** (`LoginView.permission_classes=[]`) — not live-verified.
**Impact:** 5/5 login PASS is attestation-grade, AUTHENTICATED_PROVEN=0.

## CON-83-05 — "DB can confirm stored roles" vs. "documented DATABASE_URL points at a DB with no SMS schema"

**Claimed:** The repo's read-only check scripts (`backend/check_nurse.py`,
`check_users.py`, `audit_users.py`) can inspect the real DB to confirm stored
roles.
**Proven:** Running the exact connection/query path used by `check_nurse.py`
fails with `psycopg.errors.UndefinedTable: relation "accounts_user" does not
exist` — meaning the documented endpoint does not contain this app's tables
(schema drift / stale endpoint). Local probe scripts
(`C:\Users\Ryuk\AppData\Local\Temp\opencode\p83_db_probe.py`, `p83_dbg*.py`)
confirmed connection but no schema; `.venv\Scripts\python.exe` is not a valid
interpreter on this OS (system python 3.14.7 + Django 6.1 used).
**Impact:** Stored-role confirmation from DB is **not possible** via the
documented endpoint. Recorded as environment evidence, not as proof of role.

## CON-83-06 — "Nurse should reach /health-records" vs. "both backend and frontend gate it on different things"

**Observed:** Backend `/api/health-records/*` uses `IsStaffRole`
(`permissions.py:190`) which **allows** `staff`/`nurse` — so a corrected
Nurse account would pass the API. But the frontend route guard
`App.jsx:1303` requires super_admin/admin/principal/vice_principal/
campus_admin/teacher and **omits both `nurse` and `staff`** — so even after
the role-mapping fix, the Nurse cannot reach the page that the backend
already permits.
**Impact:** FRONTEND_ROLE_GUARD_FAILURE as a *secondary/latent* defect for
Nurse; must be fixed together with the mapping defect, not later.

---

## Tally

| CON ID | Claimed | Proven | Class |
|---|---|---|---|
| CON-83-01 | designations → specialized roles | serializer hardcodes `staff` | ROLE_MAPPING_FAILURE |
| CON-83-02 | counsellor/officer accounts exist | no such roles in enum | ROLE_RESOLUTION_FAILURE |
| CON-83-03 | seeded staff can log in | seeds create no User accounts | PROVISIONING_MISMATCH |
| CON-83-04 | live login demonstrated | not live-verifiable (read-only) | EVIDENCE_GAP |
| CON-83-05 | DB confirms stored roles | documented endpoint lacks schema | ENVIRONMENT_DRIFT |
| CON-83-06 | nurse page reachable | frontend guard omits nurse+staff | FRONTEND_ROLE_GUARD_FAILURE (secondary) |