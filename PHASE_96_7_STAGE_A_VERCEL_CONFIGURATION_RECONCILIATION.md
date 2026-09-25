# PHASE 96.7 — STAGE A — VERCEL DEPLOYMENT CONFIGURATION RECONCILIATION (READ-ONLY)

Phase: 96.7 | Stage: A (PRE-FLIGHT / STOP-AND-CONFIRM ONLY) | Date: 2026-09-25
Mode: READ-ONLY — nothing was modified, created, deployed, committed, or pushed.

---

## 1. Executive Summary

The canonical backend project `perfect-foundation-api` (prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9,
team lordvalicious-projects) is confirmed at commit `0e44fe4`. The Phase 96.6 entrypoint fix
is intact. The current deployment failures are **deployment-layer configuration errors**, and
the root cause is a **root-directory contradiction**:

* The build working directory is already the git root directory `backend/`
  (`gitRootDirectory=backend` on the Git link AND `rootDirectory=backend` on the project),
* but the repository-root `/vercel.json` still issues **old-style `cd backend && ...`
  commands**, which assume the working directory is the repository root.

Executing `cd backend` when the working directory is already `backend/` fails with `ENOENT`
(`backend/backend` does not exist). The successful READY deployment `dbb2d95` proves the
correct pattern: config with **no `cd backend`**, commands run relative to `backend/`,
install/build executed from `backend/`, and automatic Python entrypoint detection (no
`backend/pyproject.toml`).

**Minimum safe correction (Option A):** neutralize the stale `cd backend &&` prefixes in the
repository-root `/vercel.json` so its install/build commands run relative to the already-
selected `backend/` working directory — matching the `dbb2d95`-proven configuration and the
current project-dashboard settings. This is a source-file change and therefore requires
separate owner approval (it is NOT part of this Stage A).

---

## 2. Repository State

| Check | Result | Label |
|---|---|---|
| Current branch | `master` | PROVEN |
| Current HEAD | `0e44fe4` (0e44fe45b37ddc33421e604dc9a35eb8b30ca796) | PROVEN |
| origin/master | `0e44fe4` (matches HEAD) | PROVEN |
| Working tree | No tracked modifications; only untracked `PHASE_96_*` deliverables | PROVEN |
| Remote | `https://github.com/lordvalicious/perfect-foundation-sms` | PROVEN |

Head matches the expected `0e44fe4`; no unexpected source changes exist.

## 3. Canonical Vercel Project Verification

* Canonical backend project: **`perfect-foundation-api`** — PROVEN
* Project ID: **`prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9`** — PROVEN
* Owner/team: **`lordvalicious-projects`** (`team_tfsvfjmV8ob1tVBJEIsNIMVy`) — PROVEN
* GitHub link: type `github`, repo `perfect-foundation-sms`, org `lordvalicious`,
  productionBranch `master`, `gitRootDirectory=backend` — PROVEN
* No other backend project was created or selected.

**Obsolete/conflicting projects that exist in the team (not used by any local tool):**

| Project | ID | Relevance |
|---|---|---|
| `backend` | prj_mIvOEZuQUhVZuU9dtmQ3bdGDIpQC | Project literally named `backend`. Not referenced by `.vercel/project.json` links or commands. |
| `perfect-foundation-backend` | prj_lSvGXgRiSoEV88pxt6vuXfAHtCxT | Obsolete name. Not referenced by any `.vercel` link; appears only in documentation text and one stale CSRF origin in `backend/config/settings/production.py` (see §12). |

Local Vercel links (`project.json`): repo-root and `frontend/` → `perfect-foundation-sms`
(prj_01w0P0HcW9BnLS6ustNxn6b6qsE3, frontend monorepo project); `backend/` →
`perfect-foundation-api` (canonical). **No local link or command points to a project named
`backend`.**

## 4. Current Vercel Project Configuration (canonical project, read-only API)

| Setting | Value | Label |
|---|---|---|
| rootDirectory | `backend` | PROVEN |
| framework | `django` | PROVEN |
| buildCommand (dashboard) | `python manage.py migrate --noinput && python manage.py collectstatic --noinput` | PROVEN |
| installCommand (dashboard) | (null) | PROVEN |
| outputDirectory | (null) | PROVEN |
| productionBranch | `master` | PROVEN |
| link.gitRootDirectory | `backend` | PROVEN |
| sourceFilesOutsideRootDirectory | true | PROVEN |
| nodeVersion | `24.x` (frontend-oriented; backend uses Python) | PROVEN |
| pythonVersion | not exposed in API | UNKNOWN |

Configured build command includes `python manage.py migrate` (pre-existing dashboard setting,
reported; NOT changed).

## 5. Repository Vercel Configuration

| File | Status at HEAD | Content (commands) | Labels |
|---|---|---|---|
| `/vercel.json` (repo root) | EXISTS | `buildCommand: "cd backend && python manage.py migrate --noinput && python manage.py collectstatic --noinput && echo 'BUILD_VERSION=20260923-05'"`; `framework: python`; `installCommand: "cd backend && pip install -r requirements.txt"` | PROVEN |
| `/backend/vercel.json` | ABSENT (removed in `4112ad5`) | — | PROVEN |
| `/frontend/vercel.json` | EXISTS | `buildId`, rewrites `/api/*` → `https://perfect-foundation-api.vercel.app/api/:path`, static fallback, CSP, headers | PROVEN |

Determinations:

* The command strings executed by the failed deployments match the **repo-root `/vercel.json`**
  exactly (`cd backend && pip install -r requirements.txt` appeared verbatim in the failed
  deploy's error message), so Vercel is consuming the **repository-root** config while the
  build working directory is **already `backend/`**. — PROVEN
* `/vercel.json` contains `cd backend` — PROVEN
* The `cd backend` commands assume the working directory is the **repository root** — PROVEN
  (they contradict the project's `rootDirectory`/`gitRootDirectory` selection)
* Repo config duplicates the Vercel dashboard/root setting by assuming a `backend` subdirectory
  — PROVEN
* `/backend/vercel.json` absence is relevant: with working dir already `backend/`, Vercel cannot
  find a `backend/backend` config either. — LIKELY (config resolution detail not fully exposed)

## 6. Root-Directory / Git-Root Reconciliation (path resolution model)

* Git link `gitRootDirectory=backend` → for push-triggered builds, the deployment uses
  `<clone>/backend/` as the build root (install/build working directory). — PROVEN (inferred
  from dbb2d95 READY + 0e44fe4 push-triggered ENOENT evidence)
* Project setting `rootDirectory=backend` → matches; the working directory is `backend/`.
  — PROVEN (dash API)
* Repo-root `/vercel.json` commands prepend `cd backend`, i.e., they assume cwd = repo root and
  re-enter `backend/`. Under the above model, cwd is already `backend/`, so `cd backend` has no
  target → `ENOENT` at buildStep. — PROVEN (error message contains this exact command; git tree
  confirms no `backend/backend` exists)
* CLI deploy run from `cwd=backend/` (Phase 96.6) applied rootDirectory on top of cwd →
  Vercel looked for `backend/backend` inside the uploaded tree → NOW_SANDBOX_WORKER_ROOTDIR_NOT_EXIST.
  — PROVEN (`dpl_AUtBmA3so3krk1ahgemaRtiJfjLs` status + gitDirty=1, actor=opencode)

**Model:** build cwd = `backend/`; config read from repo root; commands must be `backend/`-
relative; entrypoints resolve relative to the build root; CLI deploys must be invoked from the
repository root (or `--cwd` repo root), NOT from `backend/`.

## 7. Failed Deployment Evidence

### dpl_AUgqP3DdzTp8yncWaaiHcYjBpptL (push-triggered, `githubDeployment=1`)
| Field | Value |
|---|---|
| commit | 0e44fe45b37ddc33421e604dc9a35eb8b30ca796 (ref master) |
| target | production |
| readyState | ERROR |
| errorCode | ENOENT |
| errorStep | buildStep |
| errorMessage | `Command "cd backend && pip install -r requirements.txt" exited with 1` |

This command comes verbatim from repo-root `/vercel.json`. Under cwd=`backend/` (git root
dir), `cd backend` targets nonexistent `backend/backend` → ENOENT. — PROVEN via tree + config.

### dpl_AUtBmA3so3krk1ahgemaRtiJfjLs (CLI, actor=opencode, gitDirty=1)
| Field | Value |
|---|---|
| commit | 0e44fe45b37ddc33421e604dc9a35eb8b30ca796 |
| target | production |
| readyState | ERROR |
| errorCode | NOW_SANDBOX_WORKER_ROOTDIR_NOT_EXIST |
| errorStep | build-container-init |
| errorMessage | `The specified Root Directory "backend" does not exist. Please update your Project Settings.` |

Caused by CLI invocation from `cwd=backend/` (or otherwise applying `rootDirectory` twice),
so Vercel sought `backend/backend`. — PROVEN

Both demonstrate a **deployment-layer root-directory contradiction**, not an application bug.

## 8. Successful Deployment `dbb2d95` Comparison

Deployment `dpl_9KfWCb9wewiEeymZ4BqmUQNzL4DU` — READY, production, push-triggered
(`githubDeployment=1`, meta sha `dbb2d95cacb83f95cb08da03e28b36e333f63a97`).

| Aspect | dbb2d95 (READY) | 0e44fe4 (current HEAD) | Label |
|---|---|---|---|
| backend/pyproject.toml | ABSENT (no entrypoint override → automatic detection) | PRESENT; entrypoint override removed in `0e44fe4` | PROVEN |
| repo-root `/vercel.json` | `{ "buildCommand": "python manage.py migrate --noinput && python manage.py collectstatic --noinput", "framework": "python" }` — **no `cd backend`**, no installCommand | `cd backend && python manage.py ...`; `installCommand: cd backend && pip install -r requirements.txt` | PROVEN |
| `/backend/vercel.json` | EXISTED (identical content, no cd) | ABSENT | PROVEN |
| install behavior | default (`pip install -r requirements.txt` in cwd) | explicit `cd backend && pip install -r requirements.txt` | PROVEN |
| build behavior | manage.py relative to cwd (`backend/`) | `cd backend && manage.py ...` | PROVEN |
| entrypoint | automatic (WSGI detection) | automatic (after 0e44fe4) | PROVEN |

Material config difference: **`cd backend` prefixes** added later (commit `4071d9e`, "Phase 95
and Phase 96 changes") while the working directory is already `backend/` — reintroducing the
double-root. Everything else matches the proven-READY shape.

## 9. Exact Root Cause

**PROVEN.** The repository-root `/vercel.json` contains `cd backend && ...` build/install
commands that assume the build working directory is the repository root, but both the Git link
(`gitRootDirectory=backend`) and the project setting (`rootDirectory=backend`) make the working
directory `backend/`. Executing `cd backend` from inside `backend/` fails (`backend/backend`
does not exist) → install exit 1 → `ENOENT` at buildStep for push-triggered deploys; CLI deploys
issued from `cwd=backend/` additionally get `NOW_SANDBOX_WORKER_ROOTDIR_NOT_EXIST` from the
double-applied root. This is a deployment-configuration defect introduced after the LAST
successful deploy (`dbb2d95`), not an application-code defect.

## 10. Minimum Safe Correction

### Option A — neutralize stale `cd backend` in repo-root `/vercel.json` (RECOMMENDED)

| Item | Current | Proposed |
|---|---|---|
| buildCommand | `cd backend && python manage.py migrate --noinput && python manage.py collectstatic --noinput && echo 'BUILD_VERSION=20260923-05'` | `python manage.py migrate --noinput && python manage.py collectstatic --noinput` |
| installCommand | `cd backend && pip install -r requirements.txt` | `pip install -r requirements.txt` (or omit → default) |

* Why it resolves the failure: install/build run relative to cwd, which is already `backend/`.
* Application behavior: unchanged (deployment-behavior only).
* Deployment behavior: returns to the proven `dbb2d95` pattern.
* Risks: low; must be validated by one production deployment of the canonical project.
* Source modification: YES (`vercel.json`). Requires owner authorization (NOT part of Stage A).
* Vercel dashboard change: NO (dashboard buildCommand already matches proposed value).

### Option B — change project/root configuration so repo-root commands are valid
| Item | Current | Proposed |
|---|---|---|
| rootDirectory | `backend` | (unset / repo root) |
| git link gitRootDirectory | `backend` | (unset) |
Then keep `cd backend && ...` commands. Changes the canonical project root/working directory;
contradicts git link setting; requires Vercel dashboard/API modification and re-validation.
Not minimal; not recommended.

### Option C — change deployment invocation/context only
Deploy CLI from repository root (`--cwd` repo root) so `rootDirectory=backend` resolves to the
real `backend/`. Fixes the CLI path only; **push-triggered deploys still fail** because the
root-directory contradiction in `vercel.json` remains. Insufficient on its own.

### Other options
Reintroducing `/backend/vercel.json` with `cd`-free commands and/or removing `installCommand`
also aligns with the dbb2d95 precedent, but Option A alone is the minimal diff.

## 11. Alternatives Considered

Documented above: A (source fix, recommended), B (dashboard/project root change), C
(invocation-only, insufficient). No speculative application changes recommended.

## 12. Frontend Target Verification

* `frontend/vercel.json`: rewrites `/api/:path(.*)` →
  `https://perfect-foundation-api.vercel.app/api/:path`; CSP `connect-src` includes
  `https://perfect-foundation-api.vercel.app`. — PROVEN (correct canonical target)
* Stale `perfect-foundation-backend.vercel.app` references: appear **only** in documentation
  markdown files (`PHASE_*_*.md`, `AUDIT_REPORT.md`) and in one **backend CSRF trusted origin**:
  `backend/config/settings/production.py:35` → `"https://perfect-foundation-backend.vercel.app"`
  (harmless stale origin; does not affect routing; NOT changed in Stage A). — PROVEN
* No runtime frontend routing code references the obsolete project. — PROVEN

## 13. Five-Role Baseline Protection

Protected roles COUNSELLOR / GUARD / NURSE / ADMINISTRATIVE_OFFICER / LIBRARIAN; baseline
`7357c18d1e4352bdce41b7de23c36eead4b66681`. This investigation requires no change to the
baseline or to authorization/role/permission/scope/frontend-guard files. HEAD descends from the
baseline. — PROVEN (no files touched)

## 14. Migration Classification Preservation

Carried forward unchanged (no reinterpretation, no fix attempted, no production migrations):

```
MIGRATION_0028_SOURCE_IDENTITY = NOT_IDENTIFIED
MIGRATION_0028_SOURCE_PRESENT  = NO
MIGRATION_0028_EXPECTED        = UNKNOWN
MIGRATION_0028_GRAPH_STATUS    = VALID
MIGRATION_0028_LOCAL_STATUS    = UNKNOWN
MIGRATION_0028_TARGET_STATUS   = UNKNOWN
MIGRATION_0028_MODEL_DRIFT     = PENDING_MODEL_CHANGES
MIGRATION_0028_CLASSIFICATION  = INSUFFICIENT_EVIDENCE
MIGRATION_GATE                 = UNKNOWN
```

`makemigrations --check` failure does not prove a `0028` source is missing.

## 15. Production Safety

Stage A performed: NO production deployment, NO migration, NO database modification, NO
secret-value exposure, NO account provisioning, NO Vercel project creation/deletion/transfer,
NO ownership/billing change, NO source/config modification. The only proposed corrective action
(Option A) modifies a repository config file and thus requires separate explicit authorization.

## 16. Stage A Gate

Read-only reconciliation complete; no execution performed. Awaiting explicit owner approval for
any execution phase.

---

PHASE 96.7 STAGE A FINAL GATE

CANONICAL PROJECT: perfect-foundation-api
PROJECT ID: prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9
CURRENT HEAD: 0e44fe4 (matches expected)
WORKTREE: clean (no tracked changes; only untracked PHASE deliverables)
VERCEL ROOT DIRECTORY: backend
GIT ROOT DIRECTORY: backend (Git link gitRootDirectory=backend)
REPOSITORY VERCEL CONFIG: /vercel.json present with `cd backend && ...` build/install commands; /backend/vercel.json absent
ROOT CONTRADICTION: PRESENT — build cwd is already backend/, but repo-root vercel.json re-enters `cd backend`
ROOT CAUSE: repo-root /vercel.json `cd backend && ...` commands (added in 4071d9e) contradict gitRootDirectory=backend + rootDirectory=backend; `cd backend` fails inside backend/ (ENOENT); CLI from cwd=backend double-applies root (NOW_SANDBOX_WORKER_ROOTDIR_NOT_EXIST)
MINIMUM SAFE CORRECTION: Option A — strip `cd backend &&` prefixes from /vercel.json buildCommand/installCommand (commands become backend/-relative, matching proven dbb2d95)
APPLICATION SOURCE CHANGE REQUIRED: YES (vercel.json only)
VERCEL DASHBOARD CHANGE REQUIRED: NO
FRONTEND TARGET: https://perfect-foundation-api.vercel.app (correct; no stale runtime reference)
MIGRATION GATE: UNKNOWN (classification preserved)
FIVE-ROLE BASELINE: PROTECTED (7357c18d; unchanged)
PRODUCTION SAFETY: NO WRITE/DEPLOY/MIGRATION/ACCOUNT/SECRET/BILLING ACTION PERFORMED

STAGE A STATUS: COMPLETE

OWNER EXECUTION APPROVAL:
REQUIRED — DO NOT PROCEED