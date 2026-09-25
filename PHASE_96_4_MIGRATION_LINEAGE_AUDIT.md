# PHASE 96.4 — MIGRATION LINEAGE AUDIT (READ-ONLY)

**Date:** 2026-09-25 (PKT / UTC+5)
**Mode:** READINESS INVESTIGATION — no deploy, no migration creation/application, no production DB write, no account creation, no secret access, no project creation, no ownership/billing changes.
**Canonical backend target:** Vercel project `perfect-foundation-api` -> `https://perfect-foundation-api.vercel.app`
**Repo:** https://github.com/lordvalicious/perfect-foundation-sms (branch `master`)

---

## 1. PREFLIGHT REPORT (STOP AND CONFIRM)

| Field | Value |
|---|---|
| CURRENT HEAD | `e59c180ad9ecca65d7a5a414649959fdd4637029` — "Restore missing report views and update imports in views.py ..." (2026-09-25 04:38:32 +0500) |
| CURRENT BRANCH | master (tracks origin/master; `## master...origin/master`) |
| WORKTREE STATUS | Clean vs HEAD; untracked only: PHASE_96_3_* and PHASE_96_4_* deliverables |
| PHASE 84 BASELINE | `7357c18d1e4352bdce41b7de23c36eead4b66681` (ancestor of HEAD) |
| PHASE 96.3 BASELINE | HEAD `e59c180` + corrected PHASE_96_3_* deliverables present in worktree |
| CANONICAL VERCEL PROJECT | perfect-foundation-api (ID `prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9`) |
| CANONICAL BACKEND URL | https://perfect-foundation-api.vercel.app |
| BACKEND ROOT DIRECTORY | `backend/` (Vercel rootDirectory = backend) |
| DEPLOYMENT BRANCH | master |
| PRODUCTION DATABASE TARGET | DATABASE_URL / DB_* (encrypted Vercel production env) — names read, values NOT read |
| PRODUCTION DATABASE MODIFIED | NO |
| PRODUCTION SECRETS ACCESSED | NO (env variable values are `Hidden`/encrypted and were not decoded) |
| VERCELL DEPLOYMENT PERFORMED | NO |

**Mode statement:** This phase performed a read-only, source-level deployment-readiness investigation only. Evidence above and in Sections 2-14 was gathered via git history, migration source, Django tooling (check/showmigrations/makemigrations --dry-run/collectstatic --dry-run), the Vercel CLI read-only commands (whoami/project ls/ls/inspect/env ls/usage/contract/teams), and a public HTTP GET to the live health endpoint. No write, no deploy, no account mutation.

---

## 2. MIGRATION 0028 — FACTS & CLASSIFICATION (corrected precedence matrix applied)

The only `0028*` migration file in the repository is `backend/apps/schools/migrations/0028_schoolsettings_theme_color.py` — an unrelated app (schools). There is **no accounts `0028`** file in source, in any commit, or in any branch.

| Field | Value |
|---|---|
| MIGRATION_0028_SOURCE_IDENTITY | NOT_IDENTIFIED |
| MIGRATION_0028_SOURCE_PRESENT | NO |
| MIGRATION_0028_EXPECTED | UNKNOWN |
| MIGRATION_0028_GRAPH_STATUS | VALID |
| MIGRATION_0028_LOCAL_STATUS | UNKNOWN |
| MIGRATION_0028_TARGET_STATUS | UNKNOWN |
| MIGRATION_0028_MODEL_DRIFT | PENDING_MODEL_CHANGES |
| MIGRATION_0028_CLASSIFICATION | **INSUFFICIENT_EVIDENCE** |
| MIGRATION_GATE | **UNKNOWN** |

**Why INSUFFICIENT_EVIDENCE (not SOURCE_MISSING):** per the corrected precedence matrix, `makemigrations --check` FAIL establishes ONLY `MODEL_MIGRATION_DRIFT=PENDING_MODEL_CHANGES`. SOURCE_MISSING requires all three of SOURCE_MIGRATION_IDENTITY=IDENTIFIED (app+filename+number+lineage), SOURCE_PRESENT=NO, EXPECTED=YES. Here identity is NOT_IDENTIFIED, so the classification is INSUFFICIENT_EVIDENCE and the gate is UNKNOWN. No UNKNOWN was collapsed to BLOCKED.

---

## 3. MIGRATION LINEAGE — FULL INVESTIGATION

### 3.1 Migration numbering & inventory (accounts)
Accounts migration directory, sorted, full chain `0001_initial` → `0027_seed_ai_permissions`:
`0001_initial, 0002_institutionmembership_roleassignment_staffprofile_and_more, 0003_staffprofile_photo_user_photo_and_more, 0004_staffprofile_fields, 0005_alter_roleassignment_role, 0006_staffleave_staffattendance, 0007_staffprofile_membership_primary_campus, 0008_add_institution_to_all_models, 0009_populate_institution_ids, 0010_user_twofa_enabled_user_twofa_secret, 0011_alter_roleassignment_role, 0011_remove_staffprofile_campus_charfield, 0011_staffattendancecorrection, 0012_staffattendance_deleted_at_and_more, 0013_merge_20260829_1001, 0014_create_frostfire_superadmin, 0015_twofabackupcode_salt, 0016_alter_role_choices, 0017_studenttransfer, 0018_merge_accounts_leaves, 0019_alter_user_options_user_institution_and_more, 0020_roleassignment_unique_super_admin, 0021_demote_duplicate_active_memberships, 0022_alter_staffattendance_staff, 0023_user_email_verified_and_emailverification, 0024_alter_staffattendancecorrection_staff_and_more, 0025_seed_permissions_catalog, 0026_alter_permission_action_alter_permission_category, 0027_seed_ai_permissions`

- Accounts leaf at HEAD = `0027_seed_ai_permissions`.
- Accounts leaf at Phase 84 baseline `7357c18` = also `0027_seed_ai_permissions` (verified via `git ls-tree`).
- **No accounts `0028*` file exists at HEAD, at baseline, or in any commit.**

### 3.2 Git history searches (authoritative lineage)
- `git log -S "0028_alter_roleassignment_role"` (all branches, accounts migrations) → **no output** (never committed).
- `git log --all -S "counsellor" -- backend/apps/accounts/migrations` → **no output**.
- `git log --all -S "administrative_officer" -- backend/apps/accounts/migrations` → **no output**.
- `git log --all --diff-filter=D --name-only -- backend/apps/accounts/migrations/*` → **no output** (no deleted/renamed accounts migration files in history).
- No merge/rebase artifacts: accounts migration history is linear through the leaf (0011/0018/0027 merges are normal graph merges; none removes a migration).

**Conclusion:** no numbered `accounts.0028` migration was ever authored, committed, renamed, or deleted. There is no authoritative app+filename+lineage for an accounts `0028`.

### 3.3 The role-choices migration history (the relevant lineage)
| Migration | Introduced | Touches `role` choices | Roles included |
|---|---|---|---|
| 0003_staffprofile_photo_user_photo_and_more | early | user role | 8 |
| 0005_alter_roleassignment_role | early | roleassignment.role | 13 |
| 0011_alter_roleassignment_role | 2026-08 | roleassignment.role | 14 (incl. guard) |
| **0016_alter_role_choices** | **2026-08-30 (07a4275)** | **roleassignment.role + rolepermission.role** | **17 (super_admin..staff)** |
| 0020_roleassignment_unique_super_admin | later | NO choices change — adds unique constraint only | — |
| 0026_alter_permission_action... | later | permission.category (not roles) | — |
| 0027_seed_ai_permissions | 2026-09-12 (c7e3e6b) | data migration (permissions), not role choices | — |

`0016_alter_role_choices.py` (dependency: 0015) is the **last migration that encoded the role choices**; it contains exactly 17 roles and does **not** include `counsellor`, `administrative_officer`, or `nurse` (source read in full, Section evidence).

### 3.4 When the three roles entered models.py (drift origin)
| Role | Commit | Date | Files changed (migration? ) |
|---|---|---|---|
| NURSE | `a5d254d` "feat: Add NURSE role to Role enum and permissions" | 2026-09-23 07:33 | models.py (+3), permissions.py (+28) — **NO migration file** |
| COUNSELLOR + ADMINISTRATIVE_OFFICER | `7357c18` "Add Phase 85 documentation ..." (Phase 84 baseline) | 2026-09-24 14:36 | models.py (+9), permissions.py (+4), serializers.py, services.py, test_regressions.py (+163) — **NO migration file** |

Both commits that grew the enum shipped **zero** migration files. After `a5d254d` + `7357c18`, `models.py` `Role.TextChoices` (lines 11-31) contains 20 roles; migration state still encodes 17.

### 3.5 Current model field definitions
- `RoleAssignment` (models.py:502): `role = models.CharField(max_length=30, choices=Role.choices)` (lines 509-511).
- `RolePermission` (models.py:1782): `role = models.CharField(max_length=30, choices=Role.choices)` (line 1788).

### 3.6 What Django currently wants (dry-run, verbosity 3 — file NOT created)
`python manage.py makemigrations accounts --dry-run --verbosity=3`:
```
Migrations for 'accounts':
  apps\accounts\migrations\0028_alter_roleassignment_role_alter_rolepermission_role.py
    ~ Alter field role on roleassignment
    ~ Alter field role on rolepermission
    dependencies: [('accounts', '0027_seed_ai_permissions')]
```
- Both AlterField ops carry the full 20-element choices list (roleassignment and rolepermission).
- `python manage.py makemigrations --check` exits **1** (FAIL). Deterministic and reproducible.
- Verified the candidate file was NOT generated during this audit (`Test-Path` = False); loose `--dry-run --verbosity=3` output only.

### 3.7 Graph validity
`MigrationLoader.build_graph()` → **GRAPH_OK**; accounts leaf = `0027_seed_ai_permissions`. No broken dependencies, no missing leaves; model state loads cleanly for every app.

### 3.8 Documents referencing "0028"
Only PHASE_96_2_* and PHASE_96_3_* remediation/audit documents mention an accounts `0028`; all refer to it as a **pending-drift status** (from Phase 96.2 `makemigrations --check` output), not as an authoritative planned artifact. No plan, deployment checklist, or approved baseline references an expected accounts `0028` migration by identity.

---

## 4. MODEL DRIFT vs MIGRATION LINEAGE (distinction required)

Four different states — do not conflate:

| State | Is it present? | Evidence |
|---|---|---|
| **MIGRATION MODEL DRIFT** | **YES** (PENDING_MODEL_CHANGES) | `makemigrations --check` FAIL (exit 1); `--dry-run -v 3` lists 2 AlterField ops; deterministic |
| **MISSING EXPECTED MIGRATION** | NOT ESTABLISHED | Identity NOT_IDENTIFIED; no committed/planned accounts 0028 exists in git history |
| **TARGET MIGRATION NOT APPLIED** | NOT ESTABLISHED | No authorized target-DB read; target status UNKNOWN |
| **DEPLOYMENT BLOCKED** | Blocked on other, independently verified blockers | Vercel latest builds ● Error; live build 12h old (predates reports fix); see READINESS report |

### 4.1 Structured model-drift report
| Field | Value |
|---|---|
| MODEL_DRIFT_DETECTED | YES |
| APPS_WITH_DRIFT | accounts |
| MODELS_WITH_DRIFT | RoleAssignment, RolePermission |
| FIELDS/CHOICES AFFECTED | `role` CharField(max_length=30) on both; choices grew 17 → 20 |
| EXPECTED SCHEMA CHANGE | **CHOICES-METADATA ONLY** — for PostgreSQL this is NOT a DDL change: column type stays varchar(30), no constraint, no data migration; Django represents it as AlterField purely to reconcile migration-model state |
| EXISTING MIGRATION THAT ALREADY REPRESENTS CHANGE | NONE (0016 predates the three roles; no later migration adds them) |
| MISSING MIGRATION IDENTITY | A candidate would be named `0028_alter_roleassignment_role_alter_rolepermission_role`, but that is a Django-generated prospective name, not an authoritative historical identity |
| CONFIDENCE | Drift existence: HIGH (deterministic tooling). A numbered accounts 0028 ever intended/committed: UNKNOWN (no lineage evidence) |

**Read-only conclusion:** drift is real but scoped to `choices` metadata; there is no committed migration for it and no authoritative evidence the numbered migration was ever expected. Per the corrected matrix this is INSUFFICIENT_EVIDENCE -> UNKNOWN. No migration was created or applied this phase.

---

## 5-14. Other sections are in PHASE_96_4_DEPLOYMENT_READINESS.md

| Section | Delivered in |
|---|---|
| 5 Target DB read-only | READINESS report |
| 6 Vercel canonical verification | READINESS report |
| 7 .vercel link mismatch | READINESS report |
| 8 Local checks | READINESS report |
| 9 Redis | READINESS report |
| 10 Five-role account paths | READINESS report |
| 11 Authorization architecture | READINESS report |
| 12 Five-role protected files | READINESS report |
| 13 Vercel quota (read-only) | READINESS report |
| 14 No speculative fixes | READINESS report |
| 15 Final matrix | READINESS report |
| 17 Final gate | READINESS report |
| 18 Machine summary | PHASE_96_4_MACHINE_SUMMARY.txt |
| 16 Deliverables | listed at end of READINESS report |

---

## NET EFFECT ON PHASE 96.3 / PHASE 96.4 GATES
Phase 96.4 confirms Phase 96.3's corrected classification. The migration gate remains **UNKNOWN** (INSUFFICIENT_EVIDENCE). The overall deployment gate is **BLOCKED** on independently verified blockers (backend build Error on the latest, post-fix deploy attempt; live build predates the reports remediation; five-role provisioning path absent for 3 of 5 roles; stricter evidence needed before DEPLOYMENT-READY is claimed).