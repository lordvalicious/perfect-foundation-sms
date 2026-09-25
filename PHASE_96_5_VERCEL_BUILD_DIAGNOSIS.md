# PHASE 96.5 — VERCEL BUILD DIAGNOSIS

Phase: 96.5 | Date: 2026-09-25 | Mode: READ-ONLY

## 0. STOP-AND-CONFIRM PREFLIGHT — VERIFIED

```text
CANONICAL BACKEND: perfect-foundation-api
PROJECT ID: prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9
PRODUCTION URL: https://perfect-foundation-api.vercel.app
REPOSITORY: https://github.com/lordvalicious/perfect-foundation-sms
BRANCH: master

PHASE: 96.5
MODE: READ-ONLY
DEPLOYMENT: FORBIDDEN
VERCEL PROJECT CREATION: FORBIDDEN
PROJECT TRANSFER/OWNERSHIP CHANGE: FORBIDDEN
TEAM/BILLING CHANGE: FORBIDDEN
PRODUCTION DB MIGRATION: FORBIDDEN
PRODUCTION SECRET EXPOSURE: FORBIDDEN
ACCOUNT PROVISIONING: FORBIDDEN
SOURCE MODIFICATION: FORBIDDEN UNLESS EXPLICITLY AUTHORIZED LATER
```

Project identity verified against Vercel API and the local CLI project link:
canonical project `perfect-foundation-api`, `prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9`,
`rootDirectory=backend`, framework `django`, production branch `master`. No discrepancy.

## 1. BUILD FAILURE DIAGNOSIS — READY (conclusively diagnosed)

| Field | Value |
|---|---|
| BUILD_DIAGNOSIS | READY |
| BUILD_FAILURE_CLASS | ENTRYPOINT |
| OBSERVED_ERROR | Vercel API `errorCode = PYTHON_ENTRYPOINT_NOT_FOUND`, `errorStep = buildStep` |
| AUTHORITATIVE SOURCE | Vercel REST API `v13/deployments/{id}` build error fields (CLI could not expose ERROR build logs) |

### Exact verbatim error message (from Vercel API, not guessed)

```text
"tool.vercel.entrypoint" in "backend/pyproject.toml" is "backend/config/wsgi.py"
but no matching module file was found. Use "module:object" format (e.g. "main:app")
and ensure the module file exists, or remove the setting to use automatic entrypoint detection.
errorLink: https://vercel.com/docs/functions/runtimes/python#python-entrypoints
```

### Failing deployment details

| Field | Value |
|---|---|
| FAILED_DEPLOYMENT_ID | dpl_AhAN32CjrfvHjEE21cxkdzomJ75V |
| FAILED_DEPLOYMENT_URL | perfect-foundation-b3bj08ycv-lordvalicious-projects.vercel.app |
| FAILED_DEPLOYMENT_COMMIT | e59c180 |
| CURRENT_HEAD | e59c180ad9ecca65d7a5a414649959fdd4637029 |
| DEPLOYMENT_COMMIT_IS_HEAD | YES |
| DEPLOYMENT_ERROR_CODE | PYTHON_ENTRYPOINT_NOT_FOUND |
| DEPLOYMENT_STATE | ERROR |

## 2. CLASSIFICATION ANALYSIS

- Failure phase: **ENTRYPOINT** (Vercel Python-runtime entrypoint resolution) — this is the
  *observed* Vercel error, not an inference.
- The failing setting: `backend/pyproject.toml` contains

  ```toml
  [tool.vercel]
  entrypoint = "backend/config/wsgi.py"
  ```

  The canonical project's **root directory is `backend`**. Vercel therefore resolves the
  Python entrypoint **relative to the project root** (i.e., `backend/`). The configured
  value `backend/config/wsgi.py` maps to `backend/backend/config/wsgi.py`, which does not
  exist. This is the exact contract Vercel reports: "no matching module file was found."
- Additionally, Vercel expects the entrypoint in `module:object` form (e.g. `main:app`)
  or a project-root-relative path. `backend/config/wsgi.py` satisfies neither form under
  `rootDirectory=backend`.
- The correct module that was intended exists and imports cleanly:
  `backend/config/wsgi.py` (repo-root-relative) defines `application = get_wsgi_application()`;
  `backend/config/asgi.py` is also present.
- Proven READY precedent: the last READY production deployment (`dbb2d95`) was built from
  a commit that had **no `backend/pyproject.toml` at all**
  (`git show dbb2d95:backend/pyproject.toml` → "not in commit"), so Vercel used automatic
  entrypoint detection. Prior deployments in the failing window (`425a3d9`, `e59c180`) carry
  the bad entrypoint and all fail deterministically at this exact step.

### Proven vs inferred

```text
OBSERVED_ERROR = PYTHON_ENTRYPOINT_NOT_FOUND (Vercel API build error field, verbatim)
INFERENCE     = entrypoint mis-resolution under rootDirectory=backend (supported by:
               error message wording, project rootDirectory=backend in API, and path check —
               backend/backend/config/wsgi.py does not exist). Classified as INFERENCE.
```

## 3. MINIMAL CORRECTIVE ACTION (documented; NOT implemented — Phase 96.5 is read-only)

Required to make the build reach READY (top candidate, matches proven-READY config):

1. **Primary (recommended, restores proven behavior):** remove the `[tool.vercel]`
   section from `backend/pyproject.toml` so Vercel uses automatic entrypoint detection —
   the exact behavior of READY build `dbb2d95`, and one of the two remedies explicitly
   named in Vercel's own error message.
2. **Alternative:** set the entrypoint to a valid root-relative module:object form, e.g.
   `config.wsgi:application` (project root is `backend`, so the module is `config.wsgi`).

These are recommendations only. No source change was made in Phase 96.5.

## 4. SUPPORTING EVIDENCE (all gathered this phase)

| Item | Result |
|---|---|
| Vercel API deploy metadata (e59c180) | ERROR, PYTHON_ENTRYPOINT_NOT_FOUND, buildStep |
| Vercel API project settings | name=perfect-foundation-api, rootDirectory=backend, framework=django, buildCommand=`python manage.py migrate --noinput && python manage.py collectstatic --noinput`, linked repo perfect-foundation-sms |
| backend/pyproject.toml | `[tool.vercel] entrypoint = "backend/config/wsgi.py"` present in HEAD |
| backend/config/wsgi.py | exists; `application` defined |
| git show dbb2d95:backend/pyproject.toml | not in commit (proven READY precedent) |
| python manage.py check | exit 0 (warnings only) |
| python manage.py collectstatic --noinput --dry-run | exit 0, 157 files |
| python manage.py migrate --plan | resolves OK (reference) |
| reports imports | REPORTS_IMPORT_OK; APIView/Response/IsAccountantRole/REPORT_VIEW_MAP all present |
| URL loading | 47 URL patterns resolve |

## 5. NOT THE CAUSE (explicitly ruled out)

- Not a dependency/install failure: `requirements.txt` pins `dj-database-url==2.3.0`,
  `redis==5.0.0`; a dependency would fail at INSTALL_DEPENDENCY, not ENTRYPOINT.
- Not the reports remediation: reports imports resolve locally and the failing error is
  unrelated to report code.
- Not the model-migration drift: `makemigrations --check` failing is unrelated to the
  build's entrypoint step (see §7).
- Not an env-var problem: required production env names present; base.py DB path is
  satisfied by `DATABASE_URL` (names only verified; values never disclosed).
- Not cache-related: Redis optional + LocMemCache fallback confirmed in `base.py` (lines 291-312).

## 6. BUILD LOGS STATUS

```text
BUILD_LOGS_STATUS = CONSULTED VIA API ERROR FIELDS (authoritative errorCode/message/step)
BUILD_DIAGNOSIS   = READY — exact cause conclusively identified via Vercel API, not guessed
```

## 7. AUTHORITATIVE MIGRATION STATE (carried forward, DO NOT RECLASSIFY)

| Field | Value |
|---|---|
| SOURCE_IDENTITY | NOT_IDENTIFIED |
| SOURCE_PRESENT | NO |
| EXPECTED | UNKNOWN |
| GRAPH_STATUS | VALID |
| LOCAL_STATUS | UNKNOWN |
| TARGET_STATUS | UNKNOWN |
| MODEL_DRIFT | PENDING_MODEL_CHANGES |
| CLASSIFICATION | INSUFFICIENT_EVIDENCE |
| GATE | UNKNOWN |

```text
MODEL_MIGRATION_DRIFT != PROVEN_MISSING_MIGRATION
MAKEMIGRATIONS_CHECK_FAILURE != PROOF_OF_MIGRATION_0028_IDENTITY
```

No migration 0028 was created. No production migrations run. No reclassification.

## 8. VERCEL QUOTA

```text
VERCEL_QUOTA = UNKNOWN
```
No deployment was attempted to test quota (deployment is forbidden in this phase).

## 9. CACHE

```text
CACHE = READY (configuration confirmed: Redis if REDIS_URL/UPSTASH_REDIS_URL present,
               else LocMemCache fallback — base.py:291-312; no change made)
```

## 10. CONCLUSION

The exact build failure is **conclusively diagnosed**: Vercel Python runtime entrypoint
`PYTHON_ENTRYPOINT_NOT_FOUND` caused by `backend/pyproject.toml` → `[tool.vercel]
entrypoint = "backend/config/wsgi.py"`, which is invalid under the project's
`rootDirectory=backend`. A minimal corrective action is documented (remove the entrypoint
override or use `config.wsgi:application`) but **was not implemented** per Phase 96.5's
read-only mandate.