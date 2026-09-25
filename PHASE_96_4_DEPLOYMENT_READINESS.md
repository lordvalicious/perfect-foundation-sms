# PHASE 96.4 — DEPLOYMENT READINESS RESOLUTION (READ-ONLY)

**Date:** 2026-09-25 (PKT)
**Mode:** READINESS INVESTIGATION — no deploy, no migration creation/application, no production DB write, no account creation, no secret access, no project creation, no ownership/billing changes.
**Canonical backend:** Vercel project `perfect-foundation-api` -> `https://perfect-foundation-api.vercel.app` (repo `lordvalicious/perfect-foundation-sms`, branch `master`, root `backend`).

---

## 5. TARGET DATABASE STATE (READ-ONLY)

| Field | Value |
|---|---|
| TARGET_DATABASE_REACHABLE | YES (indirect, via live HTTP probe) |
| TARGET_DATABASE_IDENTITY | UNKNOWN — DATABASE_URL / DB_* exist as encrypted Vercel production env (names only); no direct connection string decoded or used |
| TARGET_MIGRATION_TABLE_PRESENT | UNKNOWN (no read/query performed) |
| TARGET_ACCOUNTS_MIGRATIONS | UNKNOWN |
| TARGET_RELEVANT_MIGRATION_STATUS | UNKNOWN |
| TARGET_SCHOOLS_MIGRATIONS | UNKNOWN |
| TARGET_ROLE_SCHEMA_STATE | UNKNOWN |
| TARGET_STATUS | **UNKNOWN** (no authorized read-only DB path established this phase) |

Evidence: `GET https://perfect-foundation-api.vercel.app/api/health/` → `200 {"status":"ok","database":{"ok":true,"error":null},...}` (2026-09-25 02:35 UTC). This proves DB connectivity only; it does NOT reveal migration state. The account for direct DB inspection was not available, so `TARGET_STATUS=UNKNOWN` is recorded — **not** treated as READY and **not** treated as BLOCKED.

Note: the live deployment is a 12h-old build (`perfect-foundation-1kllqrz3d`, created 2026-09-24 19:07 PKT) that predates the reports remediation commit `e59c180` (2026-09-25 04:38:32 PKT). Its migration state is not representative of current source.

---

## 6. VERCEL CANONICAL PROJECT CONFIGURATION (VERIFIED, READ-ONLY)

| Field | Value |
|---|---|
| CANONICAL_PROJECT_NAME | perfect-foundation-api |
| CANONICAL_PROJECT_ID | `prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9` |
| OWNER / SCOPE | lordvalicious-projects (team `team_tfsvfjmV8ob1tVBJEIsNIMVy`) |
| ROOT_DIRECTORY | backend |
| FRAMEWORK | Django |
| INSTALL_COMMAND | `pip install -r requirements.txt` |
| BUILD_COMMAND | `python manage.py migrate --noinput && python manage.py collectstatic --noinput` |
| NODE_VERSION | 24.x |
| PRODUCTION DEPLOYMENT | perfect-foundation-1kllqrz3d (`dpl_9KfWCb9wewiEeymZ4BqmUQNzL4DU`) |
| PRODUCTION DEPLOYMENT STATUS | **READY** |
| PRODUCTION DEPLOYMENT CREATED | Thu Sep 24 2026 19:07:18 GMT+0500 (12h old) |
| ALIASES | https://perfect-foundation-api.vercel.app (LIVE); *.lordvalicious-projects.vercel.app; git-master |
| HEALTH PROBE (LIVE ALIAS) | 200 `{"status":"ok","database":{"ok":true}}` |

### Env var names present (production; values NOT read — they are `Hidden`/encrypted `Config`/`Secret`):
DATABASE_URL, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_ENGINE, SECRET_KEY, DJANGO_SECRET_KEY, DJANGO_SETTINGS_MODULE, DEBUG, CORS_ALLOWED_ORIGINS, DJANGO_CSRF_TRUSTED_ORIGINS, DJANGO_ALLOWED_HOSTS, DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD, MIGRATION_SECRET, VITE_API_URL, DJANGO_SESSION_COOKIE_SECURE, DJANGO_CSRF_COOKIE_SECURE, DJANGO_SECURE_SSL_REDIRECT, DJANGO_EMAIL_HOST, DJANGO_EMAIL_PORT, DJANGO_EMAIL_USER, DJANGO_EMAIL_PASSWORD, DJANGO_EMAIL_USE_TLS, LATE_FEE_PERCENT, LATE_FEE_GRACE_DAYS, JAZZCASH_ENV, EASYPAISA_ENV, CRON_SECRET, ATTENDANCE_DEVICE_KEYS, GPS_DEVICE_KEYS.

### Absent (non-blocking):
REDIS_URL, UPSTASH_REDIS_URL, BLOB_READ_WRITE_TOKEN — none present; Redis not required (see Section 9).

### Backend deployment target verdict:
**VERCEL_PROJECT_GATE = READY** for configuration (project identity, root directory, framework, install/build commands, env set, alias LIVE). **BACKEND_DEPLOYMENT_TARGET_GATE = BLOCKED** because the newest deploy of current source failed at build (Section 6/8 below) and the LIVE build is older than the reports fix.

### Recent deployments of the canonical project (read-only listing):
- 3h ago: `perfect-foundation-b3bj08ycv` (`dpl_AhAN32CjrfvHjEE21cxkdzomJ75V`) ● **Error**, build `[0ms]`, created Fri Sep 25 2026 04:38:41 +0500 — i.e. ~9s after the reports-fix commit `e59c180` (04:38:32). Never reached READY.
- 4h: `perfect-foundation-n4qjl35i2` ● Error
- Earlier (9h/9h): additional ● Error deployments; the only READY deployment in the window is the 12h-old `1kllqrz3d`.
- `vercel logs` for ERROR deployments returns: "Logs are unavailable because deployment ... never reached READY and ended in ERROR." → build failure logs not retained/readable via CLI; cause not further diagnosable read-only.

**Consequence:** every attempt to deploy the current (reports-fix) source has errored; the live alias still serves the pre-remediation build. This is an independently verified backend build blocker.

---

## 7. .vercel LINK MISMATCH RESOLUTION (README / NO-OP)

| Field | Value |
|---|---|
| LOCAL_VERCEL_LINK (backend/) | `backend/.vercel/project.json` = project `backend` (`prj_mIvOEZuQUhVZuU9dtmQ3bdGDIpQC`) |
| LOCAL_VERCEL_LINK (root / frontend/) | root `.vercel/project.json` and `frontend/.vercel/project.json` = `perfect-foundation-sms` (`prj_01w0P0HcW9BnLS6ustNxn6b6qsE3`, framework vite) |
| CANONICAL_VERCEL_PROJECT | perfect-foundation-api (`prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9`) |
| LINK_MATCH | **NO** — backend local link points at the stray `backend` project, not the canonical `perfect-foundation-api` |
| TRACKED? | All three `.vercel/` dirs are gitignored (backend/.gitignore:1, frontend/.gitignore:25, root .gitignore:43) → generated locals, never committed |
| IMPACT | LOW (local-CLI only): `vercel` CLI invocations from `backend/` would target the stray `backend` project; git-push deploys are driven by the GitHub repo↔project mapping in the Vercel dashboard (which is canonical), not by local `.vercel`. Stray projects `backend`, `frontend`, `perfect-foundation-backend` exist as separate Vercel projects (all with Error deployments / empty). |
| RECOMMENDED_ACTION | NOT EXECUTED. If local CLI deploys are ever wanted, run from `backend/`: `vercel link --project perfect-foundation-api --yes` (optionally `--scope lordvalicious-projects`). No change is required for git-push production deploys. |

No relink was performed (prohibited as a change this phase; also unnecessary for the canonical git flow).

---

## 8. LOCAL VALIDATION (CLASSIFIED)

| Check | Result | Classification |
|---|---|---|
| `python manage.py check` | PASS, exit 0; 1 warning `accounts.User auth.W004` (username not unique) | PRE-EXISTING (config note, non-blocking) |
| `python manage.py showmigrations accounts` (local dev Postgres `perfect_foundation`, development settings) | all `[ ]` — zero accounts migrations applied locally | ENVIRONMENT (local dev DB is not authoritative / not target) |
| `python manage.py makemigrations --check` | FAIL, exit 1 (`0028_alter_roleassignment_role_alter_rolepermission_role`: 2 AlterField choices ops) | SOURCE (MODEL_MIGRATION_DRIFT) — deterministic, choices-metadata only |
| `python manage.py collectstatic --noinput --dry-run` | PASS, exit 0 ("0 copied, 157 unmodified") | SOURCE OK |
| Reports import validation (`from apps.reports import views`) | PASS — REPORT_VIEW_MAP has 25 entries; URLs load (root URL resolver OK, 47 top-level patterns incl. reports) | SOURCE OK |
| Regression suite `python -m django test apps.accounts.test_regressions` | Ran 19 tests; failures=12, errors=11; all in `DesignationRoleMappingRegressionTests`; observed `staff.user is None` in the StaffProfileSerializer auto-provision path under the SQLite test profile | **PRE-EXISTING TEST-INFRASTRUCTURE** (tests added at Phase 84 baseline `7357c18`; protected code unchanged; failures reproduce the same way at baseline; not a Phase 96.x source regression) |

Notes: tests run under `config.settings.test` (SQLite in-memory) — a separate profile not used by production (production uses the Vercel DB_* / DATABASE_URL Postgres config). The `DesignationRoleMappingRegressionTests` failures reflect the test profile's serializer/account-provision behavior, not the reports fix.

---

## 9. REDIS (NO NEW DEPENDENCY — NOT A BLOCKER)

| Field | Value |
|---|---|
| REDIS_REQUIRED | NO |
| REDIS_OPTIONAL | YES |
| REDIS_URL_PRESENT (prod env) | NO |
| UPSTASH_REDIS_URL_PRESENT (prod env) | NO |
| LOC_MEM_FALLBACK_PRESENT | YES (`base.py:308-313` LocMemCache `default`/`ratelimit` when no Redis URL) |
| CACHE_CONFIGURATION_VALID | YES — `base.py:292-313`: `redis_url = REDIS_URL or UPSTASH_REDIS_URL`; Redis only when set, else LocMemCache |
| RATE_LIMIT_DEPENDENCY | NONE — `django_ratelimit` INSTALLED_APPS (`base.py:76`) and `RatelimitMiddleware` (`base.py:95`) are commented out |
| PRODUCTION_IMPACT | NONE — graceful fallback; no Redis required for boot or requests; live build served OK at 12h |
| CACHE_GATE | **READY** |

Per directive, Redis was NOT turned into a blocker (no actual requirement exists) and no Redis provisioning was performed.

---

## 10. FIVE-ROLE ACCOUNT PROVISIONING PATH (NO ACCOUNTS CREATED)

| Role | ROLE_DEFINED (models) | ROLE_PERSISTED (migration choices) | ROLE_ASSIGNMENT_SUPPORTED | ACCOUNT_CREATION_WORKFLOW | SCOPE | SAFE_TEST_ACCOUNT_PATH | Status |
|---|---|---|---|---|---|---|---|
| LIBRARIAN | YES (models.py:25) | YES (0016) | YES (RoleAssignment) | YES — `demo_seed/base.py:116` `librarian.{c}@example.test` | campus | YES | ACCOUNT_PROVISIONING_PATH_EXISTS |
| GUARD | YES (models.py:26) | YES (0016) | YES | YES — `demo_seed/base.py:120` `guard.{c}@example.test` | campus | YES | ACCOUNT_PROVISIONING_PATH_EXISTS |
| COUNSELLOR | YES (models.py:20) | NO (no migration lists it) | YES (model accepts any Role value) | NO — no demo_seed entry, no manager/command creates it | campus | NO | ACCOUNT_PROVISIONING_NOT_AVAILABLE |
| ADMINISTRATIVE_OFFICER | YES (models.py:24) | NO | YES | NO | campus | NO | ACCOUNT_PROVISIONING_NOT_AVAILABLE |
| NURSE | YES (models.py:27) | NO | YES | NO | campus | NO | ACCOUNT_PROVISIONING_NOT_AVAILABLE |

- ACCOUNT_EXISTS: NO evidence of any of the five roles having provisioned accounts (no fixtures found anywhere; no seed/command path for 3 of 5 roles). No accounts were created or enumerated this phase.
- REQUIRED_FIELDS for a safe test account (from existing seed pattern): username, email, first/last name, designation, department, campus, joining_date, status=active, create_account=True, password — i.e. the StaffProfileSerializer auto-provision path (`demo_seed/base.py`, `serializers.py:360-427`).
- REQUIRED_SCOPE_ASSIGNMENT: InstitutionMembership (institution/school) + campus scoping on StaffProfile/primary campus; roles via RoleAssignment (accounts/models.py:502).
- ADMIN_PERMISSION_REQUIRED: YES for managing these roles/accounts (per permission model; not provisioned this phase).
- ROLE_ASSIGNMENT_WORKFLOW: YES via RoleAssignment + `accounts.services`/serializers (used by demo_seed covers librarian/guard only).
- FIVE_ROLE_ACCOUNT_GATE = **BLOCKED** (3 of 5 roles lack any provisioning path; no accounts exist).

---

## 11. AUTHORIZATION ARCHITECTURE (AUDIT ONLY — NO REDESIGN)

Chain observed (model-backed, read-only): `User` → `InstitutionMembership(institution=Institution/School, status)` (accounts/models.py:373) → `RoleAssignment(role)` (models.py:502) → `RolePermission(role, permission)` (models.py:1782) with `Permission` catalog seeded by migrations 0025/0027; campus scoping via `StaffProfile.membership_primary_campus` (0007) and `Campus` (schools/models.py:181); role priority via `ROLE_RANK`; permission checks via `accounts/permissions.py`. Org→School→Campus→User hierarchy with roles/permissions/scope is present and coherent. **AUTHORIZATION_ARCHITECTURE_GATE = READY (audit pass; no changes).**

---

## 12. FIVE-ROLE PROTECTION

`git diff --stat HEAD -- backend/apps/accounts/models.py backend/apps/accounts/services.py backend/apps/accounts/serializers.py backend/apps/accounts/permissions.py backend/apps/accounts/test_regressions.py frontend/src/App.jsx` → **empty** (no output). **PROTECTED ROLE FILE CHANGES = 0.**

---

## 13. VERCEL QUOTA (READ-ONLY ATTEMPT)

| Field | Value |
|---|---|
| VERCEL_QUOTA_STATUS | UNKNOWN |
| QUOTA_LIMIT | UNKNOWN (account on Hobby/Free per contract result; public Hobby limit ≈ 100 deployments/day, but not confirmed from account data) |
| QUOTA_CURRENT_STATUS | UNKNOWN — `vercel usage` → "Error: Costs not found (404)"; `vercel contract` → "No contract commitments found" (Hobby, no billing meter exposed) |
| RESET_AVAILABLE | UNKNOWN |
| DEPLOYMENT_ALLOWED_NOW | UNKNOWN |

No deploy was performed to test quota (prohibited). Read-only CLI verification was attempted and is documented. VERCEL_QUOTA_GATE = **UNKNOWN** (not collapsed to READY or BLOCKED).

---

## 14. NO SPECULATIVE FIXES

The following changes were considered and PROHIBITED / NOT PERFORMED this phase:
- Creating or applying an accounts `0028` migration (incl. the choices AlterField candidate).
- Any production database write or schema change.
- Creating any user/account (five-role or otherwise).
- Any Vercel deployment (build/deploy) or project/alias creation.
- Any ownership/billing/team change.
- Reading, rotating, or altering any secret/env value.
- Redis/Upstash/Neon provisioning or replacing cache backends.
- Any auth redesign or five-role/model change (protected files untouched).

| REQUIRED_CHANGE (if approved later) | RATIONALE | EVIDENCE | RISK | PROPOSED_PHASE |
|---|---|---|---|---|
| Generate + commit accounts `0028_alter_roleassignment_role_alter_rolepermission_role` (or otherwise reconcile drift) | Migration-model state has 17 roles vs 20 in source; deterministic drift | `makemigrations --check` exit 1; `--dry-run -v3` output | Pure choices-metadata change; no DB DDL impact on Postgres; low | 96.5 (owner approval) |
| Add NON-seed provisioning path (management command) for COUNSELLOR / ADMINISTRATIVE_OFFICER / NURSE | No workflow exists for 3 of 5 roles | demo_seed/base.py has only librarian/guard | Would create accounts — requires explicit owner go-ahead | 96.5+ (owner decision) |
| (Optional) Relink `backend/.vercel` to canonical project | Local CLI would hit stray `backend` project | backend/.vercel/project.json prj_mIvOEZ... | No production impact; git-push flow unaffected | 96.5 (optional) |
| Fix stale origin `https://perfect-foundation-backend.vercel.app` in production.py:35 and docs | Code-default CSRF origin points at a dead back-end project name | production.py:34-37; docs/deployment.md; render.yaml | Low; canonical origins already present via env | 96.5 (doc/code) |

---

## 15. FINAL GATE MATRIX (PHASE 96.4)

Rules applied: no UNKNOWN collapsed to BLOCKED; MODEL_MIGRATION_DRIFT kept distinct from SOURCE_MISSING; source-checks-pass does not imply overall READY.

| # | Gate | Status | Basis |
|---|---|---|---|
| 1 | SOURCE_BASELINE | READY | HEAD e59c180 committed; clean worktree (only deliverables untracked); Phase 84 baseline ancestor |
| 2 | MIGRATION_IDENTITY | UNKNOWN | accounts 0028 identity NOT_IDENTIFIED (git history exhaustive, never existed) |
| 3 | MODEL_MIGRATION_DRIFT | BLOCKED | PENDING_MODEL_CHANGES (makemigrations --check exit 1; deterministic; choices-metadata only) |
| 4 | TARGET_MIGRATION_STATE | UNKNOWN | no authorized target-DB read |
| 5 | DATABASE_CONNECTIVITY | READY | live health 200, database.ok true |
| 6 | VERCEL_PROJECT | READY | canonical project verified (ID, root backend, framework, build) |
| 7 | VERCEL_CONFIGURATION | READY | env present (names only), settings production, canonical origins, no stale blockers |
| 8 | VERCEL_QUOTA | UNKNOWN | not verifiable read-only; no deploy performed |
| 9 | BACKEND_BUILD | BLOCKED | newest deploy of fixed source (b3bj08ycv, 9s after e59c180) ● Error; all recent ● Error; only 12h-old pre-fix build READY |
| 10 | REPORTS_IMPORT | READY | reports views import; REPORT_VIEW_MAP=25; URLs load; check PASS |
| 11 | CACHE | READY | no Redis required; LocMem scripted fallback; ratelimit disabled |
| 12 | FIVE_ROLE_DEFINITIONS | READY | all 5 roles defined + protected files untouched (0 changes) |
| 13 | FIVE_ROLE_ACCOUNT_PATH | BLOCKED | only librarian/guard provisionable; 3 roles have no path; no accounts exist |
| 14 | AUTHORIZATION_ARCHITECTURE | READY | audit pass; model-backed role/permission/scope chain intact |
| 15 | PRODUCTION_SAFETY | BLOCKED | no deploy executed; live build predates reports fix; target-state + quota UNKNOWN → cannot certify READY |

Overall = **BLOCKED** (UNKNOWN gates 2,4,8 do not manufacture readiness; verified blockers stand at 3,9,13,15).

---

## 16. DELIVERABLES (PHASE 96.4)

- PHASE_96_4_MIGRATION_LINEAGE_AUDIT.md (this file's sibling)
- PHASE_96_4_DEPLOYMENT_READINESS.md (this file — includes Sections 5-15, 17)
- PHASE_96_4_READINESS_MATRIX.csv
- PHASE_96_4_MACHINE_SUMMARY.txt

---

## 17. FINAL GATE

**PHASE 96.4 FINAL GATE: BLOCKED**

| BLOCKER | EVIDENCE | OWNER | REQUIRED ACTION | NEXT SAFE PHASE |
|---|---|---|---|---|
| BACKEND_BUILD (Vercel) | `b3bj08ycv` (dpl_AhAN32CjrfvHjEE21cxkdzomJ75V), created 04:38:41 PKT (9s after e59c180 commit) → ● Error, build 0ms, never READY; all recent deploys ● Error; only pre-fix `1kllqrz3d` READY | lordvalicious | Diagnose build failure (CLI logs unavailable for ERROR deploys; use Vercel dashboard), fix root cause, redeploy when authorized | 96.5 |
| FIVE_ROLE_ACCOUNT_PATH | No provisioning workflow for COUNSELLOR / ADMINISTRATIVE_OFFICER / NURSE; no accounts exist | lordvalicious | Decide on and implement a scoped provisioning path (management command / seed) with approval | 96.5+ (owner decision) |
| MODEL_MIGRATION_DRIFT | makemigrations --check FAIL (exit 1); 2 AlterField choices ops; no committed migration; identity NOT_IDENTIFIED | lordvalicious | Owner decision: generate+commit the choices migration, or explicitly accept drift (metadata-only; no DDL impact) | 96.5 |
| PRODUCTION_SAFETY | No deploy executed; live build predates reports fix; TARGET_MIGRATION_STATE=UNKNOWN; VERCEL_QUOTA=UNKNOWN | lordvalicious | After build fix + drift decision: authorized deploy with pre/post verification | 96.5 |

---

## 18. MACHINE SUMMARY

See **PHASE_96_4_MACHINE_SUMMARY.txt** (companion file, exact fields, pipe-delimited).

---

## 19. SAFETY RULES (RESTATED)

1. Evidence first; changes second; deployment last.
2. No deploy, migration create/apply, prod-DB write, account creation, project creation, ownership/billing change, secret change, Redis/Neon replacement, auth redesign, five-role change, or revert — this phase.
3. Migration-graph-drift ≠ missing-expected-migration ≠ target-not-applied ≠ deployment-blocked.
4. makemigrations --check FAIL establishes ONLY MODEL_MIGRATION_DRIFT=PENDING_MODEL_CHANGES.
5. SOURCE_MISSING requires identity identified + source absent + expected yes.
6. UNKNOWN stays UNKNOWN; never collapsed to READY or BLOCKED.
7. Protected five-role files: 0 changes this phase (verified via git diff).