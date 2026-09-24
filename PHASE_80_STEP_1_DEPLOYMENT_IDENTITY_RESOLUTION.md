# PHASE 80 STEP 1 — DEPLOYMENT IDENTITY RESOLUTION

Date: 2026-09-24 (read-only scope; no source/data/settings modified, no redeploy)

## 1. Objective

Resolve the R73-P0-001 deployment-identity blocker (TPR-001) by determining exactly which Vercel
deployment/build/revision serves `https://perfect-foundation-api.vercel.app` and
`https://perfect-foundation-sms.vercel.app`, strictly from read-only evidence. No source data,
users, permissions, passwords, migrations, Vercel settings, environment variables, secrets, or
deployment configuration were modified. No redeploy, promote, rollback, or '/api/deploy-test/'
repair was performed.

## 2. Method (read-only)

- Git identity of the local repository (HEAD, branch, worktree state).
- Local Vercel metadata: `.vercel/project.json`, `backend/.vercel/project.json`,
  `frontend/.vercel/project.json`, root `vercel.json`, `frontend/vercel.json`, local
  `frontend/.vercel/output` build artifact manifests.
- Vercel CLI availability and identity (`vercel whoami`).
- Paged `vercel ls --json` + `vercel inspect --json` for both projects to resolve production
  aliases to concrete deployments and their GitHub commit provenance.
- Git history ordering checks (`git merge-base --is-ancestor`).
- Fresh read-only HTTP probes (GET) of `/api/health/`, `/api/deploy-test/`, and the frontend
  index route, capturing status, headers, and bodies.

## 3. Findings

### 3.1 Local repository identity

- HEAD: `4306570dd19fb3c4b61e6997ce21624606c97185`
- HEAD message: "Add Phase 78 deployment identity verification and remediation plan documents"
- Branch: `master`
- Worktree: dirty with only generated deliverables (modified `e2e/test-results/.last-run.json`;
  untracked PHASE_77/78/79 files plus Phase 80 deliverables).

### 3.2 Vercel project identity (local metadata)

- Org (all projects): `team_tfsvfjmV8ob1tVBJEIsNIMVy` — scope `lordvalicious-projects`
- API project: `prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9` (projectName `perfect-foundation-api`)
  — `.vercel/project.json` at repo root and `backend/.vercel/project.json`
- Frontend project: `prj_01w0P0HcW9BnLS6ustNxn6b6qsE3` (projectName `perfect-foundation-sms`)
  — `.vercel/project.json` at repo root and frontend copy
- Vercel CLI: 59.10.0, authenticated as `lordvalicious` (`vercel whoami`). Vercel platform access
  was available and used only to inspect deployment metadata (read-only).

### 3.3 Production API deployment identity — PROVEN

- Production alias `https://perfect-foundation-api.vercel.app` resolves to deployment
  `https://perfect-foundation-a37ruonxb-lordvalicious-projects.vercel.app`
- Deployment ID: `dpl_DN4cuVyGznhQMrAQcPnsWWLJPVLJ`
- State: READY; target: production; created: 1790095348315 (2026-09-22 21:42 PKT)
- Aliases: production alias + `perfect-foundation-api-git-master-...`
- Commit provenance (Vercel metadata `githubCommitSha`):
  `dbb2d95cacb83f95cb08da03e28b36e333f63a97` — "Add Phase 53 final defects documentation and
  finance certification matrix"

### 3.4 Production frontend deployment identity — PROVEN

- Production alias `https://perfect-foundation-sms.vercel.app` resolves to deployment
  `https://perfect-foundation-od2kdd726-lordvalicious-projects.vercel.app`
- Deployment ID: `dpl_8WodGPTxrcczH87BY4bfFA4DoxVd`
- State: READY; target: production; created: 1790152553913 (2026-09-23 13:35 PKT)
- Aliases: production alias + `perfect-foundation-sms-git-master-...`
- Commit provenance (Vercel metadata `githubCommitSha`):
  `56e4b21b263a911884bc8f6d631ba31ddf1de917` — "fix: Update backend vercel.json with rootDirectory
  and functions config"

### 3.5 Commit match vs local HEAD — MISMATCH (both projects)

- Local/remote-master HEAD = `4306570...` (the latest push also triggered production builds
  `b8vrnlmfa` / `b2xj976mu` for API and frontend respectively, which ERRORED; the production
  aliases therefore still serve the last successful READY deployments above).
- Live API  = `dbb2d95...` (old, Phase 53-era)  -> does NOT match HEAD.
- Live frontend = `56e4b21...` (Phase 64-era) -> does NOT match HEAD.
- `git merge-base --is-ancestor dbb2d95 d540ab2` => YES: the live API revision strictly predates
  commit `d540ab2` ("test: Add deployment test endpoint to config urls"), and also predates
  `30fa841` ("test: Add deploy version to health endpoint") and `4a14028` (PHASE66 marker).

### 3.6 Live HTTP probes (fresh, read-only, 2026-09-24 ~03:27 UTC)

| Host | Endpoint | Result |
|---|---|---|
| perfect-foundation-api.vercel.app | /api/health/ | 200 `{"status":"ok","database":{"ok":true,"error":null},"utc_now":...}` — NO `deploy_version` field |
| perfect-foundation-api.vercel.app | /api/deploy-test/ | 404 (text/html; Vercel platform) |
| perfect-foundation-sms.vercel.app | /api/health/ | 200 (rewritten to API host; DB ok) |
| perfect-foundation-sms.vercel.app | /api/deploy-test/ | 404 (rewritten to API host) |
| perfect-foundation-sms.vercel.app | / | 200, serves `index-BVKtMrNZ.js`, `Last-Modified: Wed, 23 Sep 2026 10:23:30 GMT`, `ETag "a835a770eb7dd367d023e20f0b66356c"` |

- The live `/api/health/` response lacks `deploy_version`, which current source introduces
  (`backend/config/urls.py` line 65 `"deploy_version": "63-test-3"` added by commit `30fa841`).
  This is consistent with the served revision being `dbb2d95...` (predates `30fa841`).

### 3.7 Root-cause of the 404 and mismatch

- The production aliases point to deployments that predate the commits that added the
  `deploy-test` route (`d540ab2`) and the `deploy_version` health field (`30fa841`). The deployed
  revision therefore never contained `/api/deploy-test/`; the 404 is a stale-deployment artifact,
  not an application defect in the deployed route logic.
- Subsequent deployment attempts for newer commits (including HEAD `4306570`) ERRORED and never
  won the production alias, so the aliases remained pinned to older READY deployments.

## 4. Classifications

- Deployment identity: **MISMATCH_PROVEN**
  Neither production alias serves the local/remote HEAD; both live deployments are precisely
  identified by Vercel deployment metadata (authoritative for alias-to-deployment resolution).
- `/api/deploy-test/` 404 classification: **STALE_DEPLOYMENT_PREDATES_ROUTE**
  Proven via `git merge-base --is-ancestor dbb2d95 d540ab2` — the served revision predates the
  commit that introduced the route. Applies to both hosts (frontend rewrites `/api/*` to the API
  host).

## 5. Integrity attestation

- `PRODUCTION_DATA_MUTATED=NO`
- `SOURCE_MODIFIED=NO`
- `REDEPLOY_PERFORMED=NO`
- `VERCEL_SETTINGS_CHANGED=NO`
- No accounts created or modified. No tokens, cookies, passwords, CSRF values, authentication
  headers, or secrets were extracted, printed, or written to deliverables.

## 6. Certification impact

- R73-P0-001 / TPR-001 disposition updated: the 404 is a STALE_DEPLOYMENT_PREDATES_ROUTE evidence
  finding, consistent with prior "stale deployment artifact, not a confirmed application defect"
  disposition. It remains deployment-blocking until a successful production redeploy of a revision
  containing commits `d540ab2`..HEAD occurs. Release-demo certification is not achievable from the
  currently-served revisions.