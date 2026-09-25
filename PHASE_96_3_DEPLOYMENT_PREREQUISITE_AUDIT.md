# PHASE 96.3 — DEPLOYMENT PREREQUISITE & MIGRATION READINESS AUDIT

**Date:** 2026-09-25 06:55 PKT
**Method:** Evidence-based, read-only. NO deployment, NO migration
creation/application, NO production data changes, NO new accounts,
NO secrets read or printed. Where evidence is insufficient → **UNKNOWN**.

---

## 1. Source Readiness

| Check | Result | Evidence |
|---|---|---|
| Django system check | PASS | `manage.py check` → 0 errors, 1 pre-existing `auth.W004` warning |
| Reports imports | PASS | All 13 restored views importable |
| Reports URL routing | PASS | 171 patterns load |
| Collectstatic (dry-run) | PASS | 157 files, no collisions |
| Missing-views blocker | RESOLVED | 13 views restored in `e59c180` (v1.25 04:38 PKT) |
| Five-role protected files | UNCHANGED | 0/6 modified |
| Git state | CLEAN | `master == origin/master`, working tree clean |

**SOURCE READINESS GATE = READY** (no source changes made in this phase).

---

## 2. Migration 0028 — Facts & Classification (corrected precedence)

### What "Migration 0028" actually is
- **Accounts app:** NO `0028*` migration file exists in source — current or in
  any commit (`git log -S "0028_alter_roleassignment_role"` → no output).
  - Latest committed accounts migration: `0027_seed_ai_permissions.py`.
  - `python manage.py makemigrations --check` **FAILS**: Django wants to
    generate `0028_alter_roleassignment_role_alter_rolepermission_role.py`
    — an `AlterField` that would add the Phase 84 roles
    (`counsellor`, `administrative_officer`, `nurse`, etc.) to the `choices`
    of `roleassignment.role` and `rolepermission.role`.
  - The last committed migration touching these fields,
    `0016_alter_role_choices.py`, does **not** include these three roles.
- **Schools app:** `0028_schoolsettings_theme_color.py` **exists** — unrelated
  to the accounts role drift.

### What is established vs not established
`makemigrations --check` FAIL establishes **only**

```
MIGRATION_MODEL_DRIFT=PENDING_MODEL_CHANGES
```

It does **not** establish that a concrete migration file named `0028` is
expected, missing, or applied/unapplied anywhere. Model definitions, the
migration number, source containing role choices, or a migration Django
"would generate today" are each insufficient to set `EXPECTED=YES`. No
authoritative deployment/source lineage identifies an expected `0028` by
app + filename + history → `SOURCE_MIGRATION_IDENTITY=NOT_IDENTIFIED`.

### Classification (deterministic precedence:
GRAPH → IDENTITY → PRESENT → EXPECTED → TARGET → DRIFT)

| Field | Value | Basis |
|---|---|---|
| `MIGRATION_0028_SOURCE_IDENTITY` | NOT_IDENTIFIED | No authoritative app+filename+lineage for an expected 0028 |
| `MIGRATION_0028_SOURCE_PRESENT` | NO | No accounts `0028*` file in source/any commit |
| `MIGRATION_0028_EXPECTED` | UNKNOWN | Expectedness requires authoritative lineage; none found |
| `MIGRATION_0028_GRAPH_STATUS` | VALID | Migration graph loads; accounts leaf = `0027` |
| `MIGRATION_0028_LOCAL_STATUS` | UNKNOWN | No concrete identity to have an applied state for |
| `MIGRATION_0028_TARGET_STATUS` | UNKNOWN | No authorized target-DB inspection this phase |
| `MIGRATION_0028_MODEL_DRIFT` | PENDING_MODEL_CHANGES | `makemigrations --check` FAIL |
| `MIGRATION_0028_CLASSIFICATION` | **INSUFFICIENT_EVIDENCE** | Identity NOT_IDENTIFIED + drift PENDING_MODEL_CHANGES |
| `MIGRATION_GATE` | **UNKNOWN** | Insufficient evidence; no deterministic classification |

**MIGRATION GATE = UNKNOWN** (INSUFFICIENT_EVIDENCE)

> If separate authoritative lineage later shows the exact
> `0028_alter_roleassignment_role_alter_rolepermission_role` migration was
> required by the approved deployment plan, the classification may then
> become `SOURCE_MISSING` / `BLOCKED`. That is not established today.

---

## 3. Redis Dependency

| Field | Value | Evidence |
|---|---|---|
| Redis in requirements | YES | `redis==5.0.0` |
| Runtime requirement | **NO** | `base.py:290-315` uses Redis **only if** `REDIS_URL`/`UPSTASH_REDIS_URL` set; otherwise LocMemCache fallback |
| django-ratelimit | DISABLED | INSTALLED_APPS + middleware commented out |
| Production env | NOT PROVISIONED | No `REDIS_URL`/`UPSTASH_REDIS_URL` on Vercel production |
| Degradation | Graceful | LocMemCache per-process; fine for single-instance serverless |

**REDIS GATE = READY** (optional; no hard dependency).

---

## 4. Vercel Project & Quota

| Field | Value | Evidence |
|---|---|---|
| Canonical backend project | `perfect-foundation-api` | exists in team listing |
| Canonical production | **READY + LIVE** | Read-only inspect → READY deployment 12h old; alias `https://perfect-foundation-api.vercel.app` returns 200; `/api/health/` → `{"status":"ok","database":{"ok":true}}` |
| Frontend project | `perfect-foundation-sms` | alias returns 200 ("School Management System") |
| `backend/.vercel` link | **MISMATCH** | points to project `backend` (`prj_mIvO…`), NOT canonical `prj_RP5I…` |
| Stray projects | `backend`, `frontend`, `perfect-foundation-backend` | backend/frontend builds Error; `perfect-foundation-backend` has no deployment |
| Quota | **UNKNOWN** | Cannot be verified without a deploy, which is forbidden this phase |

**VERCEL PROJECT GATE = READY** (canonical project is deployed and healthy).
**DEPLOYMENT GATE = NOT PERFORMED** (mandated; no `vercel` deploy run).

---

## 5. Production Environment (names only — no values read/printed)

Required deployment variables present on `perfect-foundation-api` (Production):
`DATABASE_URL`, `SECRET_KEY`, `DJANGO_SECRET_KEY`, `DJANGO_SETTINGS_MODULE`,
`CORS_ALLOWED_ORIGINS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_ALLOWED_HOSTS`,
`DJANGO_SUPERUSER_EMAIL/PASSWORD/USERNAME`, `MIGRATION_SECRET`, `DB_*`,
`DJANGO_EMAIL_*`, `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE`,
`DJANGO_SECURE_SSL_REDIRECT`.

Not present (non-blocking): `REDIS_URL`, `UPSTASH_REDIS_URL`,
`BLOB_READ_WRITE_TOKEN` (storage falls back to FileSystemStorage).

**PRODUCTION ENV GATE = READY**

---

## 6. Five-Role E2E Account Audit (no creation performed)

| Role | Safe provisioning path in source | Gate |
|---|---|---|
| COUNSELLOR | None (models/permissions/tests only) | BLOCKED |
| ADMINISTRATIVE_OFFICER | None | BLOCKED |
| NURSE | None | BLOCKED |
| LIBRARIAN | YES — `demo_seed/base.py` (`librarian.*@example.test`) | PROVISIONABLE |
| GUARD | YES — `demo_seed/base.py` (`guard.*@example.test`) | PROVISIONABLE |

No fixtures directory exists. No management command seeds
COUNSELLOR / ADMINISTRATIVE_OFFICER / NURSE.
**FIVE-ROLE ACCOUNTS GATE = BLOCKED** (3 of 5 roles lack a provisioning path).

---

## 7. Stale / Anomalous References (documented, not modified)

- `backend/config/settings/production.py:35` — `_VERCEL_DEFAULT_ORIGINS`
  still lists `https://perfect-foundation-backend.vercel.app`. The canonical
  origin is already present via `base.py` `CSRF_TRUSTED_ORIGINS`, so this is
  stale-but-harmless; flagged for cleanup in a future source-approved phase.
- `docs/deployment.md`, `render.yaml`, several `PHASE_*` docs reference
  `perfect-foundation-backend.(vercel|onrender)` — historical/stale.
- Live canonical alias serves the 12h-old READY build (created before the
  reports-remediation commit `e59c180`); deploying the fixed source is for a
  later phase.

---

## 8. Readiness Summary

| Gate | Status |
|---|---|
| SOURCE_READINESS | READY |
| MIGRATION_0028_CLASSIFICATION | INSUFFICIENT_EVIDENCE |
| MIGRATION_GATE | UNKNOWN (model drift pending; no concrete expected identity) |
| REDIS_GATE | READY (optional) |
| VERCEL_PROJECT_GATE | READY |
| VERCEL_QUOTA | UNKNOWN (not verifiable without deploy) |
| PRODUCTION_ENV_GATE | READY |
| FIVE_ROLE_ACCOUNTS_GATE | BLOCKED (3/5 no provisioning path) |
| E2E_GATE | BLOCKED (accounts unavailable) |
| DEPLOYMENT_GATE | NOT PERFORMED (forbidden this phase) |
| **OVERALL GATE** | **BLOCKED** (on other independently verified blockers) |

### Why OVERALL is blocked (NOT the migration state)
The OVERALL gate is BLOCKED for independently verified reasons only:
1. `FIVE_ROLE_ACCOUNTS_GATE=BLOCKED` — COUNSELLOR, ADMINISTRATIVE_OFFICER,
   NURSE have no safe provisioning path;
2. `VERCEL_QUOTA=UNKNOWN` and no deploy was run this phase (forbidden);
3. `VERCEL_LOCAL_LINK_MISMATCH` — `backend/.vercel` targets project `backend`;
4. unresolved `MODEL_MIGRATION_DRIFT=PENDING_MODEL_CHANGES`
   (`makemigrations --check` FAIL) — recorded as a source concern, **not** as
   proof that migration `0028` is missing.

Distinct states — never conflated:
- MIGRATION MODEL DRIFT = PENDING_MODEL_CHANGES (verified)
- MISSING EXPECTED MIGRATION = not established
- TARGET MIGRATION NOT APPLIED = not established
- DEPLOYMENT BLOCKED = other verified reasons

## 9. What Would Move the Gate (future phases — none performed here)

1. **Migration:** obtain authoritative lineage for the proposed accounts
   `0028` identity, or add a migration capturing the role-choices drift and
   re-run `makemigrations --check` to PASS.
2. **Accounts:** provide legitimate COUNSELLOR / ADMINISTRATIVE_OFFICER /
   NURSE test accounts (owner-provisioned) or an approved seed path.
3. **Vercel:** in a deploy-allowed phase, fix `backend/.vercel` to link to
   `perfect-foundation-api`, confirm deploy quota, then deploy the fixed
   source.