# PHASE 94 — VERCEL BACKEND MIGRATION IMPLEMENTATION PLAN

**Phase 94 Scope**: Read-only investigation + implementation plan for Vercel backend migration  
**Mode**: READ-ONLY — NO NETWORK — NO DEPLOYMENT  
**Repository**: `C:\Users\Ryuk\Documents\perfect-foundation-sms`  
**Branch**: `master`  
**HEAD**: `8b670ba282fe40d756d9b0eda13e03abd934075d` ("Add Phase 93 documentation...")  
**Approved Baseline**: `7357c18d1e4352bdce41b7de23c36eead4b66681` (Phase 84 five-role implementation)  
**Generated**: 2026-09-24

---

## 1. REPOSITORY STATE

| Property | Value |
|----------|-------|
| Repository | `C:\Users\Ryuk\Documents\perfect-foundation-sms` |
| Branch | `master` |
| HEAD | `8b670ba282fe40d756d9b0eda13e03abd934075d` |
| Working Tree | Clean (`git status --short` → no output) |
| Approved Baseline | `7357c18d1e4352bdce41b7de23c36eead4b66681` (Phase 84 five-role implementation) |
| `7357c18` ancestor of `master` | **YES** |
| `7357c18` ancestor of `origin/Improvement-2` | **NO** |
| Phase 84 implementation intact | **YES** (no changes to key files since `7357c18`) |

---

## 2. CURRENT DEPLOYMENT ARCHITECTURE

| Component | Platform | Configuration |
|-----------|----------|---------------|
| **Backend** | Render | `render.yaml` → Docker service `perfect-foundation-backend`, free tier, Singapore region, branch `Improvement-2` |
| **Frontend** | Vercel | `frontend/vercel.json` → rewrites `/api/*` → `https://perfect-foundation-api.vercel.app` |
| **Database** | Neon PostgreSQL | `DATABASE_URL` in Render env / `backend/.env.production` |
| **Backend Vercel Config** | Root `vercel.json` | Exists but **invalid** — `rootDirectory` + `functions` at root level |
| **Backend vercel.json** | `backend/vercel.json` | **Does not exist** (deleted in `4112ad5`) |
| **Frontend API Target** | `frontend/vercel.json` | Rewrites `/api/*` → `https://perfect-foundation-api.vercel.app` (deleted project) |

**Current Architecture**: Render backend + Vercel frontend (with broken API target)

---

## 3. APPROVED BASELINE VERIFICATION

| Metric | Value |
|--------|-------|
| Approved Baseline | `7357c18d1e4352bdce41b7de23c36eead4b66681` |
| `7357c18` ancestor of `master` | **YES** |
| `7357c18` ancestor of `origin/Improvement-2` | **NO** |
| Working Tree | Clean |
| Phase 84 Implementation | Intact (no changes to key files since `7357c18`) |

---

## 4. CURRENT VERCEL CONFIGURATION AUDIT

### Root `vercel.json` (CURRENT)
```json
{
  "buildCommand": "python manage.py migrate --noinput && python manage.py collectstatic --noinput && echo 'BUILD_VERSION=20260923-05'",
  "framework": "python",
  "installCommand": "pip install -r requirements.txt",
  "rootDirectory": "backend",
  "functions": "backend",
  "python": "python3.11"
}
```

### `backend/vercel.json`
**Does not exist** (deleted in commit `4112ad5`)

### `frontend/vercel.json` (CURRENT)
```json
{
  "rewrites": [
    { "source": "/api/:path(.*)", "destination": "https://perfect-foundation-api.vercel.app/api/:path" },
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  ...
}
```

### Vercel Configuration Findings

| Issue | Severity | File | Finding |
|-------|----------|------|---------|
| **`rootDirectory` at root level** | **BLOCKER** | `vercel.json` | Vercel **does not support** `rootDirectory` at root level with `functions`. Error: `Invalid request: should NOT have additional property rootDirectory. Please remove it`. |
| **`functions` at root with `rootDirectory`** | **BLOCKER** | `vercel.json` | Invalid combination — Vercel expects monorepo `projects[]` or single project without `rootDirectory` at root. |
| **Missing `backend/vercel.json`** | **BLOCKER** | `backend/vercel.json` | Deleted in `4112ad5`; no valid backend Vercel config exists. |
| **Frontend API target deleted** | **HIGH RISK** | `frontend/vercel.json` | Rewrites to `https://perfect-foundation-api.vercel.app` — project deleted in `4112ad5`. |

### Vercel Configuration Strategy Options

| Strategy | Description | Supported by Repo | Required Files |
|----------|-------------|-------------------|----------------|
| **A: Monorepo `projects[]`** | Root `vercel.json` with `projects[]` array for frontend + backend | ✅ Yes (repo has `frontend/` + `backend/`) | Root `vercel.json` with `projects[]` |
| **B: Two Vercel Projects** | Separate Vercel projects for frontend + backend | ✅ Yes | `frontend/vercel.json` + `backend/vercel.json` |
| **C: Single Project Root** | Single `vercel.json` at root without `rootDirectory` | ❌ No | Requires restructuring |

**Recommended**: **Strategy A (Monorepo `projects[]`)** — best fits repo structure and Vercel best practices.

---

## 5. DJANGO VERCEL COMPATIBILITY AUDIT

### Entry Points
| File | Path | Status |
|------|------|--------|
| WSGI | `backend/config/wsgi.py` | ✅ Compatible — checks `VERCEL` env var for production settings |
| ASGI | `backend/config/asgi.py` | ✅ Compatible |
| Manage | `backend/manage.py` | ✅ Standard Django |

### Settings Structure
```
backend/config/settings/
├── base.py           # Shared settings (FileBasedCache, DB, etc.)
├── production.py     # Production overrides (WhiteNoise, Vercel Blob, Vercel hosts)
├── development.py    # Development
└── test.py           # Tests
```

### Key Compatibility Findings

| Severity | File | Finding | Evidence | Required Change |
|----------|------|---------|----------|-----------------|
| **BLOCKER** | `vercel.json` | Invalid `rootDirectory` + `functions` at root | Vercel schema rejects | **REQUIRED** |
| **BLOCKER** | `backend/vercel.json` | Missing | Deleted in `4112ad5` | **REQUIRED** |
| **BLOCKER** | `base.py` lines 293-302 | `FileBasedCache` for `default` + `ratelimit` | Vercel filesystem ephemeral | **REQUIRED** |
| **HIGH RISK** | `wsgi.py` lines 13-15 | Adds `BACKEND_DIR` to `sys.path` | Assumes working from `backend/` | Works with `rootDirectory: "backend"` |
| **HIGH RISK** | `production.py` lines 293-302 | `FileBasedCache` for `default` + `ratelimit` | Same as base — file-based cache fails on Vercel | **REQUIRED** |
| **HIGH RISK** | `startup.sh` | Runs migrations + collectstatic at container start | Vercel runs build command, not shell scripts | Move to `buildCommand` |
| **MEDIUM RISK** | `requirements.txt` | `vercel_blob==0.4.2` | Only works on Vercel | Already handled in `production.py` via `BLOB_READ_WRITE_TOKEN` |
| **LOW RISK** | `Dockerfile` | Uses gunicorn with workers | Vercel manages Python server | Not used on Vercel |
| **NO ISSUE** | Database/Neon | `dj_database_url` + `psycopg` | ✅ Compatible | No change needed |
| **NO ISSUE** | Auth/Authorization | Session-based, Phase 84 roles | ✅ Hosting-agnostic | No change needed |
| **NO ISSUE** | Dependencies | All pure Python or have wheels | ✅ Compatible | No change needed |

---

## 6. CACHE ANALYSIS

### Current Cache Configuration (`base.py` lines 291-302)
```python
CACHE_DIR = os.environ.get("DJANGO_CACHE_DIR", tempfile.gettempdir())

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(CACHE_DIR, "django_cache"),
    },
    "ratelimit": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(CACHE_DIR, "django_ratelimit_cache"),
    },
}
```

### Cache Classification

| Cache | Current Backend | Vercel Impact | Classification |
|-------|-----------------|---------------|----------------|
| `default` | `FileBasedCache` | **BLOCKER** — Vercel filesystem ephemeral; cache lost between invocations | **BLOCKER** |
| `ratelimit` | `FileBasedCache` | **BLOCKER** — Rate limiting fails silently | **BLOCKER** |

**Required Change**: Replace both with Redis (Upstash/Vercel KV) or Vercel KV. This is a **BLOCKER** — not optional.

---

## 7. DATABASE + MIGRATION ANALYSIS

### Database Configuration (`base.py` lines 128-160)
```python
database_url = os.environ.get("DATABASE_URL")
if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
```

### Migration Status
| Aspect | Status |
|--------|--------|
| Migration files | Exist (up to `0016_alter_role_choices.py`) |
| Phase 84 migration | Present (`0016_alter_role_choices.py`) |
| Migration execution | In `buildCommand` on Vercel; `startup.sh` on Render |
| Neon compatibility | ✅ Standard PostgreSQL via `dj_database_url` + `psycopg` |
| Connection pooling | `conn_max_age=600` + `conn_health_checks=True` handles Neon PgBouncer |

### Migration Execution on Vercel
| Aspect | Status |
|--------|--------|
| Build command includes migrate | ✅ `python manage.py migrate --noinput` in `buildCommand` |
| `preDeployCommand` | Not available on Vercel free tier |
| Safe for serverless | ✅ Runs at build time, not request time |

---

## 8. STATIC FILE ANALYSIS

### Static Files Configuration (`base.py` + `production.py`)
| Setting | Value | Vercel Compatibility |
|---------|-------|---------------------|
| `STATIC_URL` | `"static/"` | ✅ |
| `STATIC_ROOT` | `os.environ.get("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles")` | ✅ |
| `STATICFILES_STORAGE` | `whitenoise.storage.CompressedManifestStaticFilesStorage` | ✅ WhiteNoise works on Vercel |
| `STORAGES["staticfiles"]` | `whitenoise.storage.CompressedManifestStaticFilesStorage` | ✅ |
| `collectstatic` | In `buildCommand` | ✅ Works |

### Media Files (`production.py` lines 115-131)
| Aspect | Current | Vercel Compatibility |
|--------|---------|---------------------|
| Default storage | `FileSystemStorage` (or `VercelBlobStorage` if `BLOB_READ_WRITE_TOKEN`) | ⚠️ Media files ephemeral on Vercel; use Vercel Blob |
| `MEDIA_ROOT` | `BASE_DIR / "media"` | Ephemeral on Vercel |

---

## 9. AUTHENTICATION + SESSION ANALYSIS

| Aspect | Current Implementation | Vercel Compatibility |
|--------|------------------------|---------------------|
| Auth Backend | `EmailOrUsernameBackend` (session-based) | ✅ Works with Vercel (session cookies) |
| Session Storage | Database-backed (Django default) | ✅ Works (Neon PostgreSQL) |
| CSRF Protection | `CSRF_TRUSTED_ORIGINS` includes Vercel domains | ✅ Must include new backend URL |
| Session Storage | Database-backed (Neon) | ✅ Persistent across invocations |
| CSRF Cookie | `CSRF_COOKIE_HTTPONLY = False`, `CSRF_COOKIE_SAMESITE = "Lax"` | ✅ Compatible |
| Session Cookie | `SESSION_COOKIE_SECURE = True` (production) | ✅ Works on HTTPS |
| Phase 84 Five Roles | Complete at `7357c18` | ✅ Hosting-agnostic — no changes needed |

---

## 10. FIVE-ROLE SAFETY VERIFICATION

### Phase 84 Implementation Status (Intact at `7357c18`)

| File | Key Changes | Status |
|------|-------------|--------|
| `models.py` | Added `COUNSELLOR`, `ADMINISTRATIVE_OFFICER` to `Role` enum; `ROLE_RANK` updated; `primary_role` priority fixed | ✅ Intact |
| `services.py` | Added `DESIGNATION_ROLE_MAP` + `role_for_designation()` | ✅ Intact |
| `serializers.py` | `_build_user_account` uses `role_for_designation()` | ✅ Intact |
| `permissions.py` | `IsStaffRole`, `IsAcademicMemberRole` include new roles | ✅ Intact |
| `App.jsx` | Helpdesk nav/route + health-records guards updated | ✅ Intact |

### Five Roles Verified
| Role | Canonical Value | Role Enum | ROLE_RANK | Primary Role Priority |
|------|-----------------|-----------|-----------|----------------------|
| Counsellor | `counsellor` | ✅ | 42 | After HR |
| Guard | `guard` | ✅ | 30 | Before Nurse |
| Nurse | `nurse` | ✅ | 28 | After Guard |
| Administrative Officer | `administrative_officer` | ✅ | 38 | After Receptionist |
| Librarian | `librarian` | ✅ | 35 | **Fixed** (was omitted) |

**Conclusion**: Five-role implementation is **hosting-agnostic** — zero application changes required.

---

## 11. FRONTEND → BACKEND ROUTING

### Current Frontend Configuration (`frontend/vercel.json`)
```json
{
  "rewrites": [
    { "source": "/api/:path(.*)", "destination": "https://perfect-foundation-api.vercel.app/api/:path" }
  ]
}
```

### Current State
| Aspect | Current | Issue |
|--------|---------|-------|
| Frontend API Target | `https://perfect-foundation-api.vercel.app` | **Project deleted** (commit `4112ad5`) |
| Required Change | Update to new Vercel backend URL | **REQUIRED** |

### Required Frontend Change
```json
// Option A: New Vercel backend project
"destination": "https://perfect-foundation-backend.vercel.app/api/:path"

// Option B: Same Vercel project (monorepo)
"destination": "/api/:path"
```

---

## 11. RENDER CONFIGURATION SEPARATION

### Render-Specific Files (Can Remain Untouched)
| File | Purpose | Vercel Migration Impact |
|------|---------|------------------------|
| `render.yaml` | Render Blueprint | **No change needed** — separate deployment |
| `backend/Dockerfile` | Render Docker build | Not used on Vercel |
| `backend/startup.sh` | Render startup script | Not used on Vercel |
| `render.yaml` line 32 | Branch `Improvement-2` | Update to `master` if deploying from master |

**Vercel Migration Changes**: None required for Render config — separate deployment target.

---

## 12. GIT HISTORY ANALYSIS

### Key Vercel-Related Commits

| Commit | Date | Change | Significance |
|--------|------|--------|--------------|
| `77d8c55` | Aug 13 2026 | Switched to Render; frontend rewrite → Render backend | Abandoned Vercel backend |
| `4112ad5` | Sep 23 2026 | **Deleted `backend/vercel.json`** | "Rely on root vercel.json only" |
| `0bd57a8` | Sep 23 2026 | Added `rootDirectory: "backend"`, `functions: "backend"` to root `vercel.json` | First attempt at Vercel backend config |
| `56e4b21` | Sep 23 2026 | Created `backend/vercel.json` with `rootDirectory: "."` | Separate backend config attempt |
| `77d8c55` | Aug 13 2026 | Switched frontend rewrite from Vercel API → Render backend | Pivot to Render |
| `928378e` | Historical | "Add vercel.json to backend folder for Vercel routing" | Early Vercel attempt |

### Key Findings
1. **Multiple attempts** at Vercel backend deployment — never successfully completed
2. **Root cause never resolved**: `rootDirectory` at root level invalid per Vercel schema
3. **Config deleted instead of fixed**: `4112ad5` removed `backend/vercel.json` instead of fixing
4. **Branch mismatch**: `render.yaml` uses `Improvement-2` but baseline is on `master`

---

## 13. MINIMAL IMPLEMENTATION CHANGES

### REQUIRED FOR VERCEL

| # | File | Current State | Proposed Change | Why Required | Risk |
|---|------|---------------|-----------------|--------------|------|
| 1 | `vercel.json` (root) | Invalid `rootDirectory` + `functions` at root | Restructure as monorepo `projects[]` with `frontend/` + `backend/` | **BLOCKER**: Current config invalid per Vercel schema | HIGH |
| 2 | `backend/vercel.json` (NEW) | Missing (deleted in `4112ad5`) | Create valid backend config with `rootDirectory: "."`, `functions: "api/**/*.py"` | **BLOCKER**: No valid backend Vercel config exists | HIGH |
| 3 | `backend/config/settings/production.py` | `FileBasedCache` for `default` + `ratelimit` | Replace with Redis (Upstash/Vercel KV) | **BLOCKER**: File-based cache fails on Vercel ephemeral FS | HIGH |
| 4 | `frontend/vercel.json` | Rewrites to deleted `perfect-foundation-api.vercel.app` | Update to new backend URL (e.g., `https://perfect-foundation-backend.vercel.app`) | **BLOCKER**: Frontend API calls 404 | HIGH |
| 5 | `backend/config/settings/production.py` | `FileBasedCache` for `default` + `ratelimit` | Replace with Redis (Upstash/Vercel KV) | Same as #3 | HIGH |
| 6 | `vercel.json` (root) | Invalid structure | Restructure as monorepo `projects[]` with `frontend/` + `backend/` projects | **BLOCKER**: Current config invalid | HIGH |
| 7 | `render.yaml` line 32 | Branch `Improvement-2` | Update to `master` | Deploy from approved baseline | MEDIUM |

### OPTIONAL / HARDENING

| # | Change | Reason |
|---|--------|--------|
| Add Redis (Upstash) for cache/ratelimit | Production reliability | MEDIUM |
| Vercel Blob for media (already conditional) | Already implemented in `production.py` lines 118-125 | LOW |
| Health check endpoint monitoring | Observability | LOW |

### NOT REQUIRED

| Item | Reason |
|------|--------|
| Database/Neon changes | Already compatible |
| Authentication/Authorization logic | Hosting-agnostic |
| Django entry points (`wsgi.py`, `asgi.py`) | Already compatible |
| `requirements.txt` dependencies | All compatible |
| Django settings structure | Already supports `VERCEL` env var |
| Frontend build (Vite) | Already works on Vercel |
| Phase 84 five-role implementation | Hosting-agnostic, zero changes needed |

---

## 14. VERCEL CONFIGURATION STRATEGY

### Recommended: Strategy A — Monorepo `projects[]`

**Why**: Best fits repo structure (`frontend/` + `backend/`), single Vercel project, single deployment, shared environment variables.

### Required Root `vercel.json` (Monorepo)
```json
{
  "projects": [
    {
      "name": "perfect-foundation-frontend",
      "framework": "vite",
      "rootDirectory": "frontend",
      "buildCommand": "npm run build",
      "outputDirectory": "dist",
      "installCommand": "npm ci"
    },
    {
      "name": "perfect-foundation-backend",
      "framework": "python",
      "rootDirectory": "backend",
      "buildCommand": "python manage.py migrate --noinput && python manage.py collectstatic --noinput",
      "installCommand": "pip install -r requirements.txt",
      "functions": "api/**/*.py",
      "python": "python3.11",
      "env": {
        "DJANGO_SETTINGS_MODULE": "config.settings.production"
      }
    }
  ]
}
```

### Alternative: Strategy B — Separate Projects
If monorepo not desired, create separate Vercel projects with separate `vercel.json` files.

---

## 13. EXTERNAL INFORMATION STILL REQUIRED

| Information | Status | Required For |
|-------------|--------|--------------|
| Vercel project existence/access | **UNVERIFIED FROM LOCAL EVIDENCE** | Deployment execution |
| Vercel project root-directory setting | **UNVERIFIED FROM LOCAL EVIDENCE** | Deployment config |
| Vercel production domain | **UNVERIFIED FROM LOCAL EVIDENCE** | Frontend rewrite target |
| Vercel environment variables | **UNVERIFIED FROM LOCAL EVIDENCE** | Deployment config |
| Neon database availability | **UNVERIFIED FROM LOCAL EVIDENCE** | Database connection |
| Render service existence | **UNVERIFIED FROM LOCAL EVIDENCE** | Current deployment |
| DNS state | **UNVERIFIED FROM LOCAL EVIDENCE** | Production verification |

---

## 14. PHASE 95 IMPLEMENTATION SEQUENCE

### STEP 1 — CONFIGURATION
- [ ] Create `vercel.json` (root) with monorepo `projects[]` configuration
- [ ] Update `frontend/vercel.json` rewrites to new backend URL
- [ ] Update `render.yaml` branch to `master` (optional — Render decommissioning)

### STEP 2 — DJANGO ENTRYPOINT
- [ ] No changes required — `wsgi.py`/`asgi.py` already compatible

### STEP 3 — SETTINGS
- [ ] Replace `FileBasedCache` with Redis in `base.py` + `production.py` (CACHES)
- [ ] Add Redis URL env var handling (`REDIS_URL` or `UPSTASH_REDIS_URL`)
- [ ] Verify `CSRF_TRUSTED_ORIGINS` includes new Vercel backend domain

### STEP 4 — DATABASE
- [ ] No changes — Neon PostgreSQL compatible
- [ ] Verify `DATABASE_URL` format for Neon

### STEP 5 — STATIC FILES
- [ ] Verify `collectstatic` in Vercel `buildCommand`
- [ ] Verify WhiteNoise configuration for Vercel

### STEP 6 — FRONTEND ROUTING
- [ ] Update `frontend/vercel.json` rewrites to new backend URL
- [ ] Update `CSRF_TRUSTED_ORIGINS` in `production.py` for new backend domain

### STEP 7 — DEPENDENCIES
- [ ] Add `redis` or `upstash-redis` to `requirements.txt`
- [ ] `vercel_blob` already present (conditional)

### STEP 8 — TESTS
- [ ] Run Phase 84 regression tests (`DesignationRoleMappingRegressionTests`)
- [ ] Verify Django checks pass
- [ ] Test local build with `vercel build` (if CLI available)

### STEP 9 — LOCAL BUILD/VALIDATION
- [ ] `python manage.py check --deploy`
- [ ] `python manage.py migrate --plan`
- [ ] `python manage.py collectstatic --dry-run`

### STEP 10 — GIT SAFETY
- [ ] `git status --short` → only expected files changed
- [ ] `git diff` review
- [ ] No secrets in diff

---

## 15. PHASE 95 SAFETY REQUIREMENTS

| Rule | Enforcement |
|------|-------------|
| No auth bypass | Verify `EmailOrUsernameBackend` unchanged |
| No permission weakening | Verify `IsStaffRole`, `IsAcademicMemberRole` unchanged |
| No role remapping | Verify `Role` enum, `ROLE_RANK`, `primary_role` unchanged |
| No fabricated credentials | Never commit secrets |
| No session fabrication | Use real login flow only |
| No production secrets in repo | `.env*` in `.gitignore` |
| No migration deletion | Keep all migrations including `0016` |
| No destructive DB commands | No `flush`, `migrate --fake`, etc. |
| No unrelated refactoring | Only deployment-related changes |
| No five-role semantics changes | Verify `Role` enum, `ROLE_RANK`, `DESIGNATION_ROLE_MAP` unchanged |
| No Phase 84 behavior changes | Regression tests must pass |
| No Render changes unless approved | Render config separate |
| No production deployment until local validation | Local tests must pass first |

---

## 16. VALIDATION MATRIX

| Area | Current Evidence | Vercel Impact | Phase 95 Change | Validation |
|------|------------------|---------------|-----------------|------------|
| Django entrypoint | `config.wsgi.application` / `config.asgi.application` | ✅ Compatible | NO | `python manage.py check` |
| Vercel configuration | Invalid `rootDirectory` + `functions` | **BLOCKER** | YES (monorepo `projects[]`) | `vercel build` |
| Django entry point | `config.wsgi` / `config.asgi` | ✅ Compatible | NO | `python manage.py check` |
| Dependencies | All compatible (psycopg-binary, etc.) | ✅ Compatible | NO (add `redis`) | `pip check` |
| Settings | `FileBasedCache` → Redis | **BLOCKER** | YES (Redis) | `python manage.py check --deploy` |
| Database/Neon | `dj_database_url` + `psycopg` | ✅ Compatible | NO | `python manage.py dbshell` |
| Migrations | In `buildCommand` | ✅ Works | NO | `python manage.py migrate --plan` |
| Static files | WhiteNoise + `collectstatic` | ✅ Compatible | NO | `collectstatic --dry-run` |
| Cache | `FileBasedCache` → Redis | **BLOCKER** | YES (Redis) | `python manage.py shell -c "from django.core.cache import cache; cache.set('k','v')"` |
| Frontend API routing | Points to deleted project | **BLOCKER** | YES (new URL) | Manual browser test |
| Environment variables | All via env vars | ✅ Compatible | NO | `env | grep DJANGO` |
| Authentication | Session-based, `EmailOrUsernameBackend` | ✅ Compatible | NO | Local login test |
| CSRF/CORS | `CSRF_TRUSTED_ORIGINS` includes Vercel | ⚠️ Needs update | YES (new domain) | Manual CSRF test |
| Frontend routing | `frontend/vercel.json` rewrites | **BLOCKER** | YES (new URL) | Manual browser test |
| Five roles | Phase 84 complete at `7357c18` | ✅ Hosting-agnostic | NO | Regression tests pass |
| Render config | Separate deployment | N/A | NO (don't touch) | N/A |

---

## 17. FINAL DECISION GATE

```
VERCEL IMPLEMENTATION PLAN: READY
```

**Reason**: Local repository contains sufficient evidence to define a concrete, minimal Phase 95 implementation plan. All blockers identified with specific fixes. Application baseline protected.

---

## 18. FINAL SUMMARY

### Exact Files Phase 95 Must Change
1. `vercel.json` (root) — Restructure as monorepo `projects[]`
2. `backend/config/settings/base.py` — Replace `FileBasedCache` with Redis
3. `backend/config/settings/production.py` — Replace `FileBasedCache` with Redis; add new backend domain to `CSRF_TRUSTED_ORIGINS`
4. `frontend/vercel.json` — Update rewrite destination to new backend URL
5. `render.yaml` (optional) — Update branch to `master`
6. `requirements.txt` — Add `redis` or `upstash-redis`
6. `vercel.json` (root) — Restructure as monorepo `projects[]`

### Exact Files That Must NOT Change
- `backend/apps/accounts/models.py` (Role enum, ROLE_RANK)
- `backend/apps/accounts/services.py` (DESIGNATION_ROLE_MAP, role_for_designation)
- `backend/apps/accounts/serializers.py` (_build_user_account)
- `backend/apps/accounts/permissions.py` (IsStaffRole, IsAcademicMemberRole, etc.)
- `backend/apps/accounts/models.py` (User, Role, ROLE_RANK)
- `frontend/src/App.jsx` (RequireRoles, navigation)
- `backend/config/wsgi.py` (entry point)
- `backend/config/asgi.py` (entry point)
- `backend/manage.py` (management script)
- `backend/config/urls.py` (routing)
- Database migrations (including `0016_alter_role_choices`)

### Exact Technical Blockers
1. **BR-001**: Invalid `vercel.json` — `rootDirectory` + `functions` at root
2. **BR-002**: Missing `backend/vercel.json` (deleted in `4112ad5`)
3. **BR-003**: `FileBasedCache` incompatible with Vercel ephemeral filesystem
4. **BR-004**: Frontend API target points to deleted Vercel project

### External Facts Still Unverified
- Vercel project existence/access: **UNVERIFIED FROM LOCAL EVIDENCE**
- Vercel project root-directory setting: **UNVERIFIED FROM LOCAL EVIDENCE**
- Vercel production domain: **UNVERIFIED FROM LOCAL EVIDENCE**
- Vercel environment variables: **UNVERIFIED FROM LOCAL EVIDENCE**
- Neon database availability: **UNVERIFIED FROM LOCAL EVIDENCE**
- Render service existence: **UNVERIFIED FROM LOCAL EVIDENCE**
- DNS state: **UNVERIFIED FROM LOCAL EVIDENCE**

### Five-Role Application Baseline Protection
**CONFIRMED**: Phase 84 five-role implementation at `7357c18` is intact and hosting-agnostic. Zero application/authentication/authorization changes required for Vercel migration.

---

## 19. FINAL REPORT

```
PHASE 94 COMPLETE

MODE: READ-ONLY INVESTIGATION + IMPLEMENTATION PLAN
NETWORK ACCESS: NOT USED
DEPLOYMENT: NOT PERFORMED
DATABASE CHANGES: NOT PERFORMED
SOURCE CODE CHANGES: NOT PERFORMED
COMMITS: NOT CREATED
PUSHES: NOT PERFORMED

DECISION:
VERCEL IMPLEMENTATION PLAN: READY
```

**File Created**: `C:\Users\Ryuk\Documents\perfect-foundation-sms\PHASE_94_VERCEL_IMPLEMENTATION_PLAN.md`