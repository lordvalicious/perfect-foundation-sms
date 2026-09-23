# PHASE 78 — STEP 1: PRODUCTION DEPLOYMENT IDENTITY VERIFICATION (READ-ONLY)

Phase: 78 · Step: 1 · Mode: INVESTIGATION ONLY (no source change, no redeploy, no Vercel settings change, no secret rotation)
Date: 2026-09-23 (UTC ~22:40) · Repo: perfect-foundation-sms (master @ e48033b)
Objective: Determine exactly which Vercel deployment/build/revision serves
`https://perfect-foundation-api.vercel.app` and `https://perfect-foundation-sms.vercel.app`,
and investigate R73-P0-001 (deployment identity unproven) with evidence only.

## 1. Objective
Establish the production deployment identity for the API and frontend hosts. If identity cannot be
proven, bound the deployed revision using observable runtime behavior vs. git history, classify the
`/api/deploy-test/` 404, and record all evidence with PROVEN / INFERRED / UNKNOWN status. No action
was taken to repair or alter anything.

## 2. Environment & Method
- Read-only: git inspection, local `vercel` config/file inspection, live HTTP GETs.
- HTTP via `Invoke-WebRequest -UseBasicParsing`; status, headers (Server, x-vercel-id, x-vercel-cache,
  content-type), elapsed ms, and body captured for 5 endpoints.
- Git history search (`git log --follow -S`) used to date the deployed `urls.py` behavior.
- Constraints honored: `PRODUCTION_DATA_MUTATED=NO`, `SOURCE_MODIFIED=NO`, `REDEPLOY_PERFORMED=NO`.

## 3. Local Commit Identity
| Item | Value |
|---|---|
| `git rev-parse HEAD` | `e48033b6f690912eb5a223639d16be8b09024d15` |
| `git log -1 --oneline` | `e48033b Add Phase 65 deployment verification and certification files; document production blockers and status` |
| Branch | `master` (origin/master = `e48033b`, in sync) |
| `git status --short` | 54 lines: 53 untracked (phase deliverables), 1 staged-new (`test_smoke.py`), 0 modified tracked |

Worktree for tracked files is clean; only Phase deliverables/tests are untracked/staged.

## 4. Vercel Access Status
- CLI: **AVAILABLE v59.10.0** (`C:\Users\Ryuk\AppData\Roaming\npm\vercel.cmd --version`).
  The `vercel.ps1` / `npx.ps1` shims are blocked by the local PowerShell execution policy
  (`SecurityError`), so `vercel.cmd` was invoked directly.
- Auth: **UNAVAILABLE** — no `~/.vercel` directory, no `auth.json`, no `config.json`, no
  `VERCEL_TOKEN`, no `VERCEL_ARTIFACTS_TOKEN`, no `VERCEL_GIT_COMMIT_SHA/REF/URL/ENV` environment
  vars. `vercel.cmd whoami` fails on a CLI worker spawn error
  (`Worker timed out after 10 seconds; Failed to spawn get latest worker: write EPIPE`).
  A `--token` smoke test confirms the CLI parses arguments non-interactively but rejects the
  placeholder token; no valid token is available to the agent. No auth bypass attempted.
- Consequence: deployment IDs, deployment URLs, and exact production commit SHAs **cannot be
  enumerated** (`PRODUCTION_DEPLOYMENT_ID=UNKNOWN`, `PRODUCTION_COMMIT_SHA=UNKNOWN`).

## 5. Deployment Configuration (local evidence)
- **root `vercel.json` (307 B, present):** `framework: python`, `rootDirectory: backend`,
  `installCommand: pip install -r requirements.txt`,
  `buildCommand: python manage.py migrate --noinput && python manage.py collectstatic --noinput && echo 'BUILD_VERSION=20260923-05'`,
  `python: python3.11`, plus `functions: "backend"` (a string, not a valid Build Output API
  `functions` object — noted; alternative syntax historically accepted).
- **`backend/vercel.json`: MISSING** on disk — consistent with `4112ad5 "Remove conflicting
  backend/vercel.json; rely on root vercel.json only".`
- **`frontend/vercel.json` (1067 B, present):** rewrites `/api/:path` →
  `https://perfect-foundation-api.vercel.app/api/:path`, fallback `/(.*)` → `/index.html`, CSP +
  `Reporting-Endpoints` headers, `Cache-Control: no-store, must-revalidate`, and a shell-expanded
  `buildId: phase64-deploy-$(date +%s)` (not observable in responses → not usable for identity).
- **`frontend/.vercel/output/` (Build Output API v3):** `vercel build --prod --yes` LOCAL artifact,
  `cliVersion 59.10.0`, `@vercel/static-build`, framework `vite` 8.2.1, node 24, zeroConfig; mirror
  routes incl. the `/api` rewrite. **This proves a local build ran — it does NOT prove what Vercel
  production serves.**
- **`.vercel/project.json` linkage:** org `team_tfsvfjmV8ob1tVBJEIsNIMVy`; frontend/root project
  `prj_01w0P0HcW9BnLS6ustNxn6b6qsE3` (`perfect-foundation-sms`, framework `vite`, node `24.x`);
  backend project `prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9` (`perfect-foundation-api`). Linked project IDs
  identify the local Vercel projects; they do not by themselves prove what those projects serve in
  production.
- **`frontend/.vercel/.env.production.local` (2636 B, 36 lines):** key names only —
  `BLOB_READ_WRITE_TOKEN, DATABASE_URL, DATABASE_URL_UNPOOLED, DJANGO_ALLOWED_HOSTS,
  DJANGO_CSRF_TRUSTED_ORIGINS, DJANGO_EMAIL_HOST, DJANGO_EMAIL_PASSWORD, DJANGO_EMAIL_PORT,
  DJANGO_EMAIL_USER, DJANGO_EMAIL_USE_TLS, DJANGO_SECRET_KEY, DJANGO_SECURE_SSL_REDIRECT,
  GOOGLE_CLIENT_ID, NX_DAEMON, TURBO_CACHE, TURBO_DOWNLOAD_LOCAL_ENABLED, TURBO_REMOTE_ONLY,
  TURBO_RUN_SUMMARY, VERCEL, VERCEL_ENV, VERCEL_GIT_COMMIT_AUTHOR_LOGIN, VERCEL_GIT_COMMIT_AUTHOR_NAME,
  VERCEL_GIT_COMMIT_MESSAGE, VERCEL_GIT_COMMIT_REF, VERCEL_GIT_COMMIT_SHA, VERCEL_GIT_PREVIOUS_SHA,
  VERCEL_GIT_PROVIDER, VERCEL_GIT_PULL_REQUEST_ID, VERCEL_GIT_REPO_ID, VERCEL_GIT_REPO_OWNER,
  VERCEL_GIT_REPO_SLUG, VERCEL_OIDC_TOKEN, VERCEL_TARGET_ENV, VERCEL_URL, VITE_API_URL`.
  Values were NOT read except non-secret metadata: `VERCEL_ENV=production`,
  `VITE_API_URL=https://perfect-foundation-api.vercel.app/api`, and the injected build vars
  `VERCEL_GIT_COMMIT_SHA`, `VERCEL_GIT_PREVIOUS_SHA`, `VERCEL_URL` are all EMPTY here (local build
  run without the Vercel Git integration injecting them) → **no commit SHA stored in local build
  artifacts.**
- **CI (`/.github/workflows/ci.yml`):** pushes to `master`/`Improvement`/`feature/**` and PRs trigger
  frontend `npm ci && lint && build` and backend `makemigrations --check` + `manage.py test` ONLY.
  **No workflow step calls `vercel`, `vercel deploy`, `vercel --prod`, or the Vercel GH action** →
  pushes to master do not auto-deploy; production is manually deployed (CLI/dashboard), which is
  consistent with a stale production build.

## 6. `/api/deploy-test/` Source Evidence (HEAD @ e48033b)
- Registration: `backend/config/urls.py:81` — `path("api/deploy-test/", DeployTestView.as_view(), name="deploy-test")`.
- Implementation: `DeployTestView` at `backend/config/urls.py:19-40` — `permission_classes=[]`, GET
  runs `git rev-parse HEAD` (cwd `/app/backend`) and returns
  `{"status": "deployed", "marker": "PHASE66_DEPLOYMENT_PROOF_20260923", "commit": "<sha or unknown>", ...}`.
- Marker constant: `backend/config/urls.py:17` — `PHASE_66_MARKER = "PHASE66_DEPLOYMENT_PROOF_20260923"`.
- `/api/health/` evidence: registered at `config/urls.py:79`; check returns `deploy_version:
  "63-test-3"` at `config/urls.py:65` in HEAD.
- Git history (bounds production):
  - `d540ab2` introduced the `api/deploy-test/` route.
  - `30fa841` added `deploy_version` to `health_check`.
  - `4a14028` added the `PHASE66_DEPLOYMENT_PROOF_20260923` marker to `DeployTestView`.
  - `health_check` itself exists since initial commit `946fca3`.

## 7. Live Production Evidence (fresh, this session)
| Endpoint | Status | Elapsed | Key headers | Body marker |
|---|---|---|---|---|
| `api.vercel.app/api/health/?probe=db` | 200 | ~6.8 s (cold) | `Server: Vercel`, `x-vercel-id: bom1::iad1::8kqhr-1790203166383-004be40b26b1`, `x-vercel-cache: MISS`, `application/json` | `{"status":"ok","database":{"ok":true,"error":null},"utc_now":"..."}` — **NO `deploy_version` key** |
| `api.vercel.app/api/deploy-test/` | 404 | ~2.5 s | `text/html; charset=utf-8`, `Server: Vercel`, `x-vercel-cache: MISS` | none (Vercel 404 page) |
| `sms.vercel.app/api/health/?probe=db` | 200 | ~2.8 s | `Server: Vercel`, `x-vercel-id: bom1:bom1:bom1::iad1::...`, `MISS` | same JSON as API (rewrite/proxy works) |
| `sms.vercel.app/api/deploy-test/` | 404 | ~2.3 s | `text/html`, `Server: Vercel`, `MISS` | none (proxied API 404) |
| `sms.vercel.app/` | 200 | — | `Server: Vercel`, `text/html` | Vite SPA, `<title>School Management System</title>`, `/assets/index-*` bundles |

- `x-vercel-id` values are request/function invocation tokens (e.g. `bom1::iad1::...`), **not**
  deployment IDs, and differ per request as expected.

## 8. Deployment Identifiers Discovered
| Identifier | Value | Status |
|---|---|---|
| Vercel team/org ID | `team_tfsvfjmV8ob1tVBJEIsNIMVy` | PROVEN (local project.json) |
| Frontend project ID | `prj_01w0P0HcW9BnLS6ustNxn6b6qsE3` | PROVEN (local project.json) |
| API project ID | `prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9` | PROVEN (local project.json) |
| Production deployment ID (API) | none recoverable | UNKNOWN |
| Production deployment ID (frontend) | none recoverable | UNKNOWN |
| Production commit SHA (API / frontend) | none recoverable | UNKNOWN (API bounded, see §9) |
| Build env commit SHA (local build) | empty / not stored | NA |

## 9. Production Commit Identity — Bounding Analysis
The live API health body exactly equals the HEAD `health_check` payload **minus** `deploy_version:
"63-test-3"`, and `/api/deploy-test/` returns 404 although the route + `PHASE66_DEPLOYMENT_PROOF_20260923`
marker are present in HEAD. Because the identical Django function/process serves `/api/health/`
successfully, the deployed `urls.py` simply predates the deploy-test feature:

- Deployed revision is a descendant of `946fca3` (has `health_check`) and is **NOT** a descendant of
  `d540ab2` (lacks `deploy-test`) — and therefore also predates `30fa841` (lacks `deploy_version`).
- Exact deployed SHA is **not provable** without Vercel dashboard/CLI auth. Site is bound to the
  commit interval `[946fca3 .. d540ab2^)` for `backend/config/urls.py` content.
- Conclusion: the API **executes correctly and is healthy** but runs an **older revision than local
  HEAD `e48033b`** → `DEPLOYMENT_COMMIT_MATCH = MISMATCH_PROVEN`.

## 10. `/api/deploy-test/` 404 Classification
**STALE_DEPLOYMENT_PREDATES_ROUTE** (confident, evidence-backed):
- The route was introduced in commit `d540ab2`; the deployed backend revision predates it.
- Not a rewrite defect: the frontend `/api` proxy demonstrably forwards `/api/health/` correctly.
- Not a packaging/runtime defect: the same serverless function executes Django + DB (health 200).
- Not an env-config defect: the endpoint has no env dependencies (`permission_classes=[]`, marker is
  a constant, commit lookup degrades to `"unknown"`).
- Therefore this is **not a confirmed application defect**; it is a symptom of an un-synced,
  stale deployment. Reproducing the expected 200 response requires deploying a revision >= `4a14028`
  (which REDEPLOYMENT — Phase 78 later steps — may perform after Step 1 approval).

## 11. Limitations
- No authenticated Vercel session: exact deployment IDs, URLs, and commit SHAs cannot be enumerated.
- No CI/CD auto-deploy: production is manually deployed; its age cannot be dated from logs.
- Local `.vercel/output` proves only a local build, not production state (deliberately not conflated).
- Frontend commit cannot be fingerprinted from the SPA HTML/bundles in this pass.
- Browser automation (R73-P0-002) and any production mutation remain prohibited here.

## 12. Conclusion
- **Deployment identity (exact revision): UNKNOWN.** Production serves an older, un-synced build;
  exact deployment ID/SHA require an authenticated Vercel session (or dashboard access by the user).
- **Commit match: MISMATCH_PROVEN.** Production API lacks `deploy_version` and `deploy-test` that
  exist in HEAD `e48033b`.
- **404 classification:** stale deployment predating route introduction, **not** a confirmed
  application defect.
- **R73-P0-001 (deployment identity unproven): NOT resolved by this step** — but the 404 root cause
  is now explained, materially de-risking the follow-up remediation steps (verify deploy at Step 3,
  deploy + re-verify at later steps).
- **CERTIFICATION IMPACT: STILL BLOCKED** (identity verification required before certification; no
  production mutation performed; `SOURCE_MODIFIED=NO`, `PRODUCTION_DATA_MUTATED=NO`,
  `REDEPLOY_PERFORMED=NO`).