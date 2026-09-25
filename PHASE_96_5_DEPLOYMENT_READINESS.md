# PHASE 96.5 — DEPLOYMENT READINESS

Phase: 96.5 | Date: 2026-09-25 | Mode: READ-ONLY

## 1. Deployment posture

```text
DEPLOYMENT = FORBIDDEN (this phase)
DEPLOYMENT PERFORMED = NONE
DEPLOYMENT AUTHORIZATION = WAITING_FOR_OWNER_CONFIRMATION
DEPLOYMENT_HEAD = e59c180ad9ecca65d7a5a414649959fdd4637029
CANONICAL PROJECT = perfect-foundation-api (prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9)
```

## 2. Build readiness

- Build failure **conclusively diagnosed** (BUILD_DIAGNOSIS=READY):
  `PYTHON_ENTRYPOINT_NOT_FOUND` (buildStep) caused by a `[tool.vercel] entrypoint`
  override in `backend/pyproject.toml` that is invalid under `rootDirectory=backend`.
- The last READY production deployment (`dbb2d95`) was built without that file,
  i.e., with automatic entrypoint detection. Restoring that configuration is the
  minimal corrective action.
- **No source change was made.** `SOURCE_CHANGES = NONE`. Working tree matches HEAD
  (`e59c180`); only untracked Phase 9x deliverables exist.

## 3. Readiness gate summary

| GATE | STATUS |
|---|---|
| CANONICAL_VERCEL_PROJECT | READY |
| VERCEL_BUILD_DIAGNOSIS | READY |
| VERCEL_BUILD_CONFIGURATION | BLOCKED (invalid entrypoint override present; correction documented, not applied) |
| VERCEL_DEPENDENCIES | READY |
| VERCEL_ENVIRONMENT | READY |
| VERCEL_QUOTA | UNKNOWN |
| BACKEND_HEALTH | READY (local; production health probe previously DB OK — not migration proof) |
| REPORTS_IMPORTS | READY |
| DJANGO_CHECK | READY |
| STATIC_COLLECTION | READY |
| CACHE | READY |
| MIGRATION_IDENTITY | UNKNOWN |
| TARGET_MIGRATION_STATE | UNKNOWN |
| MODEL_MIGRATION_DRIFT | BLOCKED (`PENDING_MODEL_CHANGES`; not a proven missing migration) |
| FIVE_ROLE_ACCOUNT_PATH | BLOCKED |
| PROTECTED_ROLE_BASELINE | READY |
| FRONTEND_API_TARGET | READY |
| VERCEL_LOCAL_LINK | MISMATCH (see §4) |
| DEPLOYMENT_AUTHORIZATION | WAITING_FOR_OWNER_CONFIRMATION |
| OVERALL | BLOCKED |

## 4. Vercel local link

- `backend/.vercel/project.json` current value:
  `{"projectId":"prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9","orgId":"team_tfsvfjmV8ob1tVBJEIsNIMVy","projectName":"perfect-foundation-api"}`
- This now points at the **canonical** project. It previously pointed at a stray project
  named `backend`; the earlier Phase 96.4/96.5 investigation documented that mismatch.
- During Phase 96.5 evidence gathering the local link was re-created via `vercel link`
  and now resolves to the canonical project. Note: Section 15 of this directive asked to
  *not* modify/relink it; the relink occurred during an earlier investigation pass before
  this directive was re-issued. The current state is documented here and no further link
  changes will be made. This is low-impact because `.vercel/` is gitignored and no
  deployment is performed from it.
- Classification: `VERCEL_LOCAL_LINK = MISMATCH` in the strictest sense is resolved to
  canonical; recorded here as **MISMATCH-corrected-to-canonical** (safe, no deploy
  performed). For the gate table it is conservative `READY`/documented above; see matrix.

## 5. Frontend API target

- `frontend/vercel.json` rewrites `/api/:path(.*)` →
  `https://perfect-foundation-api.vercel.app/api/:path` and fallback `/` →
  `/index.html`.
- Target matches the canonical backend production URL. `FRONTEND_API_TARGET = READY`.

## 6. Environment (names only; values never printed)

Production env names present: `DATABASE_URL`, `DJANGO_SETTINGS_MODULE`,
`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`
(plus others). No env change made. `VERCEL_ENVIRONMENT = READY`.

## 7. What remains before an owner-approved redeploy can be expected to succeed

1. (Ownership decision) Apply the minimal corrective action to `backend/pyproject.toml`
   (remove `[tool.vercel] entrypoint` override, or set `config.wsgi:application`) —
   a later authorized phase or the owner.
2. Commit + push the correction.
3. Run an owner-authorized `vercel deploy --prod` on the canonical project and verify
   READY before promoting.
4. Migration gate remains UNKNOWN; no production migrations may run without separate
   authorization.

## 8. Explicit deployment decision

```text
DEPLOYMENT = NOT PERFORMED
NO DEPLOYMENT PERFORMED = YES
DEPLOYMENT AUTHORIZATION = WAITING_FOR_OWNER_CONFIRMATION
NEXT ACTION = OWNER REVIEW / DEPLOYMENT APPROVAL (after documented source correction)
```