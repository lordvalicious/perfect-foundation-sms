# PHASE 96.6 — VERCEL ENTRYPOINT REMEDIATION — STAGE A PREFLIGHT

Phase: 96.6 | Date: 2026-09-25 | Stage: A (PREFLIGHT/PREPARATION — NO CHANGES)

## Preflight Status

- PREFLIGHT_STATUS: COMPLETE
- EXECUTION_AUTHORIZATION: WAITING_FOR_OWNER_APPROVAL
- Source modified during preflight: NONE
- Deployment performed during preflight: NONE

## 1. Canonical Deployment Identity (verified)

| Field | Value |
|---|---|
| CANONICAL_VERCEL_PROJECT | perfect-foundation-api |
| PROJECT_ID | prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9 |
| PROJECT_OWNER_TEAM | lordvalicious-projects (org team_tfsvfjmV8ob1tVBJEIsNIMVy) |
| REPOSITORY | github.com/lordvalicious/perfect-foundation-sms |
| BRANCH | master (local HEAD == origin/master) |
| ROOT_DIRECTORY | backend |
| PRODUCTION_URL | https://perfect-foundation-api.vercel.app |
| ALIASES | perfect-foundation-api.vercel.app (canonical); per-deploy URLs |
| FRAMEWORK | django |
| BUILD_COMMAND | python manage.py migrate --noinput && python manage.py collectstatic --noinput |

## 2. Current Deployment State (Vercel API)

| Deployment | Commit | State | Error |
|---|---|---|---|
| dpl_AhAN32CjrfvHjEE21cxkdzomJ75V | e59c180 | ERROR (production) | PYTHON_ENTRYPOINT_NOT_FOUND, buildStep |
| dpl_DN1AMdpHCjz1i1yDC2euSEhazrZo | 425a3d9 | ERROR | PYTHON_ENTRYPOINT_NOT_FOUND |
| dpl_9KfWCb9wewiEeymZ4BqmUQNzL4DU | dbb2d95 | READY (PROMOTED) | — (no backend/pyproject.toml present) |

BUILD_FAILURE = PYTHON_ENTRYPOINT_NOT_FOUND (buildStep), observed on commits e59c180 and
425a3d9. FAILURE_CLASSIFICATION = ENTRYPOINT.

## 3. Phase 96.5 Diagnosis Carried Forward — Re-verified Against Source

`backend/pyproject.toml` (current HEAD) still contains:

```toml
[tool.vercel]
entrypoint = "backend/config/wsgi.py"
```

Under Vercel project Root Directory `backend`, Vercel resolves
`backend/config/wsgi.py` → `backend/backend/config/wsgi.py`, which does not exist →
PYTHON_ENTRYPOINT_NOT_FOUND. Diagnosis confirmed reproducible with exact current source.

`backend/config/wsgi.py`: exists, sets BACKEND_DIR onto sys.path, selects
production settings when `VERCEL` env present, and exposes
`application = get_wsgi_application()` plus `handler = application`.

## 4. Remediation Options Evaluated

### Option A — Remove `[tool.vercel] entrypoint` override (automatic detection)

- Evidence: last READY production deployment (dbb2d95) was built from a commit that had
  NO `backend/pyproject.toml` at all (`git show dbb2d95:backend/pyproject.toml` → not in
  commit). Automatic entrypoint detection succeeded under framework=django.
- Vercel's own error message explicitly offers this: "or remove the setting to use
  automatic entrypoint detection."
- Supports: preferred approach in directive ("restoring automatic entrypoint detection").

### Option B — Replace with `config.wsgi:application`

- Evidence: `config.wsgi` imports cleanly from the backend project root and exposes
  `application` (verified: `application= WSGIHandler`). Root Directory = `backend`, so
  the module path is `config.wsgi`, object `application`.
- Valid module:object form; matches Vercel guidance.

Both options are locally validated to be syntactically/modulely correct. Option A is
preferred because it restores the exact configuration proven READY at dbb2d95 and is the
most minimal change (removing a single `[tool.vercel]` section). Option B is the
documented alternative if automatic detection is deemed unsafe. FINAL selection must be
RESERVED for the approved execution stage (proposed = Option A).

## 5. Scope Check — NO Non-Entrypoint Impact

The proposed change touches ONLY `backend/pyproject.toml` (a Vercel configuration table).
It does NOT modify:
- five-role implementation (Role, ROLE_RANK, DESIGNATION_ROLE_MAP),
- authorization architecture / permissions / role semantics / frontend guards,
- database schema or production data,
- authentication behavior,
- frontend application behavior.

Protected baseline commit 7357c18d is an ancestor of HEAD (verified, exit=0).
`git diff 7357c18d..HEAD` for the five-role protected set (models.py, services.py,
serializers.py, permissions.py, test_regressions.py) and frontend/src/App.jsx is EMPTY —
files byte-identical to baseline.

## 6. Frontend Backend Target

- frontend/vercel.json rewrites `/api/:path(.*)` →
  `https://perfect-foundation-api.vercel.app/api/:path` (canonical) and `/(.*)` →
  `/index.html`; CSP `connect-src` includes `https://perfect-foundation-api.vercel.app`.
- No occurrence of `perfect-foundation-backend` anywhere in frontend/vercel.json
  (searched; none found).
- FRONTEND_BACKEND_TARGET = perfect-foundation-api.vercel.app (CANONICAL — no stale
  target, no correction needed).

## 7. Local Django Validation (Stage A)

| Check | Result |
|---|---|
| python manage.py check | PASS (exit 0; 1 pre-existing warning re non-unique username field) |
| config.wsgi:application import (from backend root) | PASS — application is WSGIHandler; handler present |
| from apps.reports import views | PASS — REPORTS_IMPORT_OK; REPORT_VIEW_MAP present |
| reports URL loading | PASS — 47 URL patterns resolve |
| collectstatic --noinput --dry-run | PASS — 157 static files, 0 new |
| showmigrations accounts | PASS — max applied/unapplied 0027 (0024-0027 unapplied locally) |
| makemigrations --check --dry-run | FAIL (exit 1) — drift: accounts 0028 alter roleassignment/rolepermission role |
| five-role regression suite (apps.accounts.test_regressions) | Ran 19 tests; FAILED failures=12, errors=11 — EXACTLY equal to Phase 96.4/96.5 baseline; pre-existing DesignationRoleMappingRegressionTests SQLite email-uniqueness infrastructure failures; NOT a source regression |

## 8. Migration Classification (carried forward, NOT reinterpreted)

```text
SOURCE_IDENTITY = NOT_IDENTIFIED
SOURCE_PRESENT  = NO
EXPECTED        = UNKNOWN
GRAPH_STATUS    = VALID
LOCAL_STATUS    = UNKNOWN
TARGET_STATUS   = UNKNOWN
MODEL_DRIFT     = PENDING_MODEL_CHANGES
CLASSIFICATION  = INSUFFICIENT_EVIDENCE
MIGRATION_GATE  = UNKNOWN
```

- makemigrations --check failure does NOT prove migration 0028 exists or is missing at
  the identity level.
- No migration 0028 created. No production migrations run. No migration-history edits.

## 9. Vercel Quota

VERCEL_QUOTA = UNKNOWN — no authoritative read-only quota evidence available; no
deployment attempted to test quota.

## 10. Production Safety

- No production migrations will be run as part of this remediation.
- No production data changes required.
- No secrets exposed (only env-var NAMES verified; values never printed).
- No environment-variable changes.
- No Vercel ownership/billing changes.
- No project creation/deletion/transfer.
- No Neon production configuration change.

## 11. Working Tree Review

- Starting/current HEAD: e59c180ad9ecca65d7a5a414649959fdd4637029 (master)
- Modified tracked files: NONE
- Untracked: only Phase 96.3/96.4/96.5 deliverable .md/.csv/.txt files (untracked by
  design; PHASE_96_6_* created in this phase are also untracked)
- No unrelated user changes present; nothing discarded.

## 12. Proposed Remediation (RESERVED for Stage B approval)

```text
FILE: backend/pyproject.toml
CHANGE: remove the [tool.vercel] section (entrypoint override)
```

Exact before → after:

```toml
# before
[tool.vercel]
entrypoint = "backend/config/wsgi.py"

# after (section removed entirely)
```

ALTERNATIVE_REMEDIATION (if owner/execution proof deems automatic detection unsafe):
`entrypoint = "config.wsgi:application"`.

## 13. Stage A Output

```text
PREFLIGHT_STATUS: COMPLETE
CANONICAL_VERCEL_PROJECT: perfect-foundation-api
PROJECT_ID: prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9
PROJECT_OWNER_TEAM: lordvalicious-projects
REPOSITORY: github.com/lordvalicious/perfect-foundation-sms
BRANCH: master
ROOT_DIRECTORY: backend
PRODUCTION_URL: https://perfect-foundation-api.vercel.app
CURRENT_DEPLOYMENT: dpl_AhAN32CjrfvHjEE21cxkdzomJ75V -> ERROR (PYTHON_ENTRYPOINT_NOT_FOUND)
BUILD_FAILURE: PYTHON_ENTRYPOINT_NOT_FOUND (buildStep)
FAILURE_CLASSIFICATION: ENTRYPOINT
PROPOSED_REMEDIATION: remove [tool.vercel] entrypoint override in backend/pyproject.toml
ALTERNATIVE_REMEDIATION: entrypoint = "config.wsgi:application"
MINIMAL_CHANGE: YES (single config section; proven READY precedent at dbb2d95)
FRONTEND_BACKEND_TARGET: perfect-foundation-api.vercel.app (canonical)
LOCAL_VALIDATION: PASS (check, wsgi import, reports imports/urls, collectstatic; regression matches baseline)
MIGRATION_CLASSIFICATION: INSUFFICIENT_EVIDENCE / GATE=UNKNOWN (unchanged)
VERCEL_QUOTA: UNKNOWN
PRODUCTION_SAFETY: CONFIRMED (no migrations, no data change, no secret exposure, no billing/project changes)
WORKTREE_STATUS: CLEAN (no tracked modifications; only untracked phase deliverables)
EXECUTION_AUTHORIZATION: WAITING_FOR_OWNER_APPROVAL
```

PHASE 96.6 PREFLIGHT: COMPLETE — STOPPING FOR OWNER APPROVAL