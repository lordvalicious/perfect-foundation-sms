# PHASE 96.9 – STAGE A PREFLIGHT

**Production-Safe Five-Role Account Provisioning Design (READ-ONLY)**

- **Phase:** 96.9 – Stage A (preflight / design proof only)
- **Mode:** READ-ONLY. No accounts created. No seed executed. No source modified. No commit/push/deploy/migrations/secrets/Vercel changes.
- **Final gate:** `READY FOR OWNER PROVISIONING APPROVAL`

---

## 1. Current Blockers

| # | Blocker | Evidence |
|---|---|---|
| B1 | **0/5 valid production accounts.** | No valid session cookie exists for COUNSELLOR, GUARD, NURSE, ADMINISTRATIVE_OFFICER, LIBRARIAN. The repo's `sa_*.txt` files (incl. `sa_guard.txt`, `sa_librarian.txt`, `sa_admin_officer.txt`) are invalid 88-byte placeholder non-sessions. Stage A/B audits treated them as NOT credentials (correct). |
| B2 | **No dedicated provisioning path for 3 of 5 roles** (COUNSELLOR, NURSE, ADMINISTRATIVE_OFFICER). | No seed/fixture/command creates accounts for these roles. Only the admin-gated `POST /api/staff/` auto-provision path can create them (via `role_for_designation`), and a valid admin session is required. |
| B3 | **GUARD / LIBRARIAN only reachable via full demo seed.** | `demo_seed` `base_users()` creates `guard.{c}` and `librarian.{c}` per campus, but only as part of the full DEMO-EDU dataset. No targeted mechanism exists. |

## 2. Existing Provisioning Mechanisms (inventory summary)

Verified at file level. Full attribute matrix in `PHASE_96_9_STAGE_A_PROVISIONING_MATRIX.csv`.

| Mechanism | Creates users? | Five roles? | Notes |
|---|---|---|---|
| `demo_seed` package / `seed_demo_data` cmd | **~997 users** | LIBRARIAN + GUARD only (correct roles); support staff get STAFF | Creates whole DEMO-EDU school (5 campuses) + permission catalog + grants; blocked from non-DEBUG unless `--allow-prod` |
| `create_demo_users` cmd | 8 users | No (SUPER_ADMIN/ADMIN/ACADEMIC/ACCOUNTANT/TEACHER/STUDENT/STAFF/PARENT) | hardcoded dev passwords; `--reset` deletes those 8 |
| `ensure_superuser` cmd | 1 (superuser) | No | env-backed; demotes other super_admin holders |
| `seed_staff` cmd | No accounts | No (StaffProfile only) | designations include all five but no login linkage |
| `seed_all` cmd | 8 (via create_demo_users) | No | aggregator |
| **`POST /api/staff/` `StaffProfileCRUDSerializer` (`create_account` default True)** | **Yes** | **ALL FIVE** via `role_for_designation` | **Only sanctioned path for COUNSELLOR/NURSE/ADMIN_OFFICER/GUARD/LIBRARIAN**; admin-gated `IsAdminOrReadOnly`; secure temp password returned once |
| `create_user_with_username()` service | Yes (core primitive) | caller-decides | concurrency-safe; used by serializer path |
| `provision_school_with_admin` / `provision_campus_with_admin` | Yes (ADMIN/CAMPUS_ADMIN) | No | transactional, tested |
| Teacher/Student CRUD serializers | Yes (TEACHER/STUDENT) | No | `create_account` pattern reused |
| Django admin (User + `InstitutionMembershipAdmin` + `RoleAssignmentInline`) | Yes | Manual | staff-user ability; password set manually (no once-only guarantee) |
| Migration `0014_create_frostfire_superadmin` | 1 superuser | No | env-driven bootstrap only |
| Role-based auto-provision in `run_migrations` view etc. | – | – | not a user-creator |
| Fixtures (`*.json`/`*.yaml`) | **None in repo** | – | – |

## 3. Demo Seed Audit (read-only)

Scope & data:
- Creates a new school **"Demo Education Group" / DEMO-EDU** (never school id 1) + 5 campuses (GVC CSC BFC KHC EXC), academic years, terms, units, classes, sections, subjects.
- **Base users (47):** `demo_superadmin` (SUPER_ADMIN, Django superuser), `demo_orgadmin` (ORG_ADMIN), and per campus: `{c}.admin` (CAMPUS_ADMIN), `principal.{c}` (PRINCIPAL), `accountant.{c}` (ACCOUNTANT), `hr.{c}` (HR), `reception.{c}` (RECEPTIONIST), `librarian.{c}` (LIBRARIAN), `clerk.{c}` (STAFF), `guard.{c}` (GUARD), `academic.{c}` (ACADEMIC).
- **Part 2:** 50 teachers (TEACHER + Teacher records), 50 support staff (role hardcoded STAFF – "Security Guard"/"Nurse" designations do **not** map to GUARD/NURSE roles), 350 parents (PARENT + Guardian), 500 students (STUDENT + Enrollment).
- Parts 3–5: finance, payroll, HR, fees, library, transport, inventory, events, helpdesk, etc. (no users).

Security / behavior:
- **Passwords:** single deterministic shared demo credential (`DEMO_PASSWORD`), precomputed PBKDF2 hash reused across all demo accounts; reset on each run so docs stay accurate. Demo-only dev credential.
- **Idempotency:** yes, `get_or_create` throughout; `employee_number` unique per institution keyed on `(institution, user)`.
- **Existing data:** never modified/deleted outside DEMO-EDU; no flush; full-isolation to the new school.
- **Dry-run:** none. **Transaction/rollback:** sub-steps `transaction.atomic()` + resumable commits, but **no whole-seed rollback / no simulate mode**.
- **Provisioning guard:** refuses to run when `DEBUG=False` unless `--allow-prod` is passed.
- **Target/narrow mode:** NO — it cannot create only five dedicated accounts; part 1 requires building the school + campus structure + permission catalog; part 2 requires the full classroom batch.

Covers exactly 2 of the 5 roles with correct roles (LIBRARIAN, GUARD); support staff never become GUARD/NURSE; COUNSELLOR/NURSE/ADMINISTRATIVE_OFFICER accounts are never seeded.

## 4. Per-Role Provisioning Status

| Role | Role enum | Dedicated path today | Production-safe reachable | Evidence |
|---|---|---|---|---|
| COUNSELLOR | `counsellor` (42) | None | **POST /api/staff/** with designation `"Counsellor"` (`role_for_designation` → counsellor) | services.py:368-389; serializers.py:317-357; needs admin session |
| GUARD | `guard` (30) | demo_seed `guard.{c}` (bundled) | POST /api/staff/ designation `"Security Guard"` → guard | demo_seed/base.py:120-121 |
| NURSE | `nurse` (28) | None | POST /api/staff/ designation `"Nurse"`/`"Lady Health Worker"` → nurse | services.py:368-389; seed_support_staff gives STAFF not NURSE |
| ADMINISTRATIVE_OFFICER | `administrative_officer` (38) | None | POST /api/staff/ designation `"Administrative Officer"` → administrative_officer | services.py:368-389 |
| LIBRARIAN | `librarian` (35) | demo_seed `librarian.{c}` (bundled) | POST /api/staff/ designation `"Librarian"` → librarian | demo_seed/base.py:116-117 |

The admin-gated `POST /api/staff/` star is the only untouched-architecture path that reaches **all five** roles with exactly one intended `RoleAssignment` each.

## 5. Production-Safety Assessment

| Option | Classification | Rationale |
|---|---|---|
| A. Existing narrowly scoped mechanism (`POST /api/staff/` with `create_account=True`, admin-gated) | **SAFE** | Creates 1 StaffProfile + 1 User + membership + 1 role; temp password returned once; no permission catalog changes; reversible; already exercised historically (accountant/guard/librarian repairs in Phase 57 narrative) |
| B. Existing seed with safe isolation (`demo_seed --allow-prod`) | **UNSAFE for five-role-only** | Over-provisions ~997 records + whole school + permission catalog/ROLE_GRANTS mutation; only librarian/guard; support staff get STAFF not GUARD/NURSE |
| C. New dedicated owner-authorized provisioning command using existing primitives | **INSUFFICIENT_EVIDENCE** (until designed; no source change permitted this phase) | Primitives (`create_user_with_username`, `role_for_designation`, `get_or_create`) already exist and are tested; would satisfy full contract |
| D. Existing admin workflow (Django admin manual, or SPA staff form with admin session) | **SAFE** | Manual; password handled by admin (no once-only temp guarantee); less auditable than API path |
| E. Other repo-supported mechanisms (Teacher/Student serializers, provision_school/campus, create_demo_users, ensure_superuser, migration 0014, fixtures=none) | **UNSAFE / NOT APPLICABLE for five roles** | Wrong role sets / superuser only / none |

No option is selected for the owner. Tradeoffs are presented above and in the matrix; decision is the owner's.

## 6. Data-Impact Assessment

- **POST /api/staff/ path:** inserts exactly `StaffProfile` + `User` + `InstitutionMembership` + `RoleAssignment` per call; no other tables touched; deterministic per call; idempotent by unique (institution, username) and StaffProfile (institution,user).
- **demo_seed:** ~997 users + full education-domain dataset + Permission catalog (when empty) + ROLE_GRANTS role-permission rows; mutates demo password hashes on re-run; zero impact to school id 1.
- **No mechanism deletes or rewrites real tenant data.** No migration drift (pure data commands; graph stays VALID).

## 7. Credential-Handling Assessment

- **Authorized path primitives** generate a secure random 14-char temporary password when none supplied, set `must_change_password=True`, return the plaintext **exactly once** via serializer `generated_password`, and never log it. This matches the provisioning contract.
- **demo_seed** uses a deterministic shared dev credential (reset each run) — acceptable for DEMO-EDU only, never for real accounts.
- **Repo-root scripts** (`create_staff_profile*.py`, `create_accountant.py`, `phase57_fix_provisioning.py`) embed production DB credentials / live session cookies in source. These are **secret hazards; never reproduced or re-used** (excluded from all provisioning paths).
- The invalid placeholder `sa_*.txt` files are not credentials and must never be treated as such.
- E2E session cookies for the five roles must be derived from real logins (or generated accounts) via `P43_<ROLE>_SESSIONID`, never committed.

## 8. Isolation Assessment

The repo supports (and demo_seed proves) school-scoped isolation:
- **Dedicated organization/school:** `DEMO-EDU` school id ≠ 1 isolates all rows; `InstitutionMembership` scopes by institution.
- **Dedicated campus:** staff/role assignments carry `primary_campus`; existing campuses available.
- **Dedicated usernames/emails:** per-institution unique username partial constraint + unique `email`; `fallback_email` derivation keeps addresses institution-deterministic.
- **Dedicated role assignments:** single `RoleAssignment` per account; `assign_role_safely` preserves the single-super-admin invariant.

No new tenancy code is needed. A future mechanism may host the five accounts in an existing campus of the existing institution, or in a DEMO-EDU scope, with fixed usernames.

## 9. Reversibility / Cleanup Assessment

- **POST /api/staff/ created accounts:** fully reversible — delete the `StaffProfile`, then the `User` (membership/role rows delete with the user or via admin). Deterministic identifiers make cleanup trivial.
- **demo_seed data:** reversible by deleting the entire DEMO-EDU school subtree, but no cleanup command exists.
- **Password rotation:** `ensure_superuser` and `set_password` support rotation; E2E cookies are refreshed by new logins.
- No mechanism requires manual DB surgery except the repo-root scripted paths (which are excluded).

## 10. Minimum Requirements for a Safe Mechanism (Provisioning Contract)

1. Creates only dedicated E2E accounts (fixed usernames) via `get_or_create` idempotency.
2. Assigns exactly the intended five-role role (via `role_for_designation` or explicit role argument).
3. Does not weaken authorization semantics or touch role-rank/permission logic.
4. Does not modify unrelated users or delete unrelated data.
5. Does not expose passwords: secure random temp password, returned exactly once, never logged.
6. Supports deterministic verification (re-run idempotent; `/api/auth/me/` confirms role).
7. Auditable (app audit logging where staff account creation is recorded).
8. Reversible or cleanup-capable (delete-created-accounts documented).
9. No migration drift (no schema/model changes).
10. Does not alter production configuration unnecessarily (no Permission catalog mutation, no settings changes).

## 11. Exact Owner Decisions Required

1. **Choose the mechanism:** (A) admin-gated `POST /api/staff/` (needs an admin/superuser session or an authorized admin action), or (C) a new dedicated provisioning command via a future source change.
2. **Choose target scope:** existing institution/campus vs `DEMO-EDU` scope for the five accounts.
3. **Authorize execution credentials:** owner-provided admin session (A/D) or owner-approved source change + run step (C).
4. **Authorize credential delivery:** how generated temp passwords are delivered/rotated and turned into E2E session cookies (never committed).
5. **Sign off on reversibility/cleanup** of the five accounts.

## 12. Actions NOT Authorized by This Phase

- Creating/running any provisioning, seed, or account mutation.
- Resetting passwords, creating users, touching the production database.
- Modifying source, committing, pushing, deploying.
- Creating or classifying migrations; altering migration status.
- Modifying secrets or Vercel projects/settings.
- Weakening authorization, adding bypasses, inventing a provisioning API.
- Ranking/selecting an option for the owner.

---

## Final Gate

```
PHASE 96.9 FINAL GATE: READY FOR OWNER PROVISIONING APPROVAL
```

Evidence is sufficient to design and prove the path; a legitimate production-safe mechanism already exists in the repository (the admin-gated `POST /api/staff/` auto-provision with `role_for_designation`), and a contract-compliant dedicated command is feasible without new architecture. No account was created; no provisioning executed; STOP after this report pending separate owner approval.