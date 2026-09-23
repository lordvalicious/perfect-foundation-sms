# Phase 64 — Deployment Configuration Audit

## Repository Structure

```
C:\Users\Ryuk\Documents\perfect-foundation-sms\
├── backend/          # Django project (Python 6.1)
│   ├── manage.py
│   ├── config/       # Django settings, URLs, WSGI
│   ├── apps/         # All Django apps (library, reports, accounts, etc.)
│   ├── .vercel/      # Vercel project configuration
│   └── vercel.json   # Vercel deployment config
├── frontend/         # React application
│   ├── vercel.json   # Frontend rewrites to backend API
│   └── src/          # React source
└── .github/          # GitHub workflows
```

## Root Vercel Configuration (`vercel.json`)

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

**Issues identified:**
- `rootDirectory: "backend"` tells Vercel to use the `backend/` directory as the project root
- `functions: "backend"` tells Vercel to deploy functions from the `backend/` directory
- `python: "python3.11"` specifies the Python runtime version
- **Missing**: The `installCommand` `pip install -r requirements.txt` may not be executing correctly if the `requirements.txt` path is relative to the wrong directory

## Backend Vercel Configuration (`backend/vercel.json`)

```json
{
  "buildCommand": "python manage.py migrate --noinput && python manage.py collectstatic --noinput && echo 'BUILD_VERSION=20260923-05'",
  "framework": "python",
  "installCommand": "pip install -r requirements.txt",
  "rootDirectory": ".",
  "functions": ".",
  "python": "python3.11"
}
```

**Issues identified:**
- Previously this file was missing `rootDirectory`, `functions`, and `python` settings
- The updated version matches the root configuration
- The `requirements.txt` is at `backend/requirements.txt`; the `installCommand` should ideally be `pip install -r backend/requirements.txt` or the `rootDirectory` should handle path resolution

## Frontend Vercel Configuration (`frontend/vercel.json`)

```json
{
  "buildId": "phase64-deploy-$(date +%s)",
  "rewrites": [
    {
      "source": "/api/:path(.*)",
      "destination": "https://perfect-foundation-api.vercel.app/api/:path"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [...]
}
```

**Key findings:**
- **All `/api/*` requests from the frontend are proxied to `https://perfect-foundation-api.vercel.app/api/:path`**
- This confirms the backend is a completely separate Vercel project
- The frontend has no direct access to Django models or Python code - all backend logic runs on the API project

## Django Settings Configuration

- `config/settings/base.py` - Base settings; reads `DATABASE_URL` from environment; `SECRET_KEY` required from env
- `config/settings/development.py` - Debug mode enabled; CORS/CSRF for localhost
- `config/settings/production.py` - Production hardening; SECURE_SSL_REDIRECT, HSTS, session security; reads `VERCEL` env var to switch to production settings
- `manage.py` - Uses `config.settings.development` by default; Vercel sets `VERCEL=1` to trigger production settings

## URL Routing (`config/urls.py`)

Key endpoints configured:
- `api/health/` - Health check with deploy_version
- `api/deploy-test/` - Deployment verification endpoint (returns git HEAD commit)
- `api/auth/` - Accounts authentication
- `api/library/` - Library app routes (included from `apps.library.urls`)
- `api/reports/` - Reports app routes (included from `apps.reports.urls`)
- `api/transport/` - Transport app routes
- `api/inventory/` - Inventory app routes
- `api/payroll/` - Payroll app routes
- `api/hr/` - HR app routes
- `api/health-records/` - Health records app routes
- `api/hostel/` - Hostel app routes
- And many more API prefixes

**Missing/broken endpoints observed:**
- `/api/deploy-test/` returns 404 in production (code exists but not deployed)
- `/api/library/` returns 404 in production
- `/api/reports/` returns 404 in production

## Database Configuration

- `DATABASE_URL` environment variable connects to Neon PostgreSQL (ap-southeast-1)
- Fallback database vars: `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- The health endpoint confirms database connectivity: `"database": {"ok": true, "error": null}`

## Environment Variables

Critical env vars for deployment:
- `DJANGO_SECRET_KEY` - Required, no default
- `DATABASE_URL` - Neon PostgreSQL connection
- `DJANGO_ALLOWED_HOSTS` - Vercel domains configured
- `VERCEL` - Environment flag; when set, production settings activate
- `DJANGO_CSRF_TRUSTED_ORIGINS` - Frontend origins
- `BLOB_READ_WRITE_TOKEN` - Vercel Blob storage (optional)

## Git Integration

- Repository: `https://github.com/lordvalicious/perfect-foundation-sms`
- Current HEAD: `d9dcb7d` (test: add deployment marker file)
- Branch: `master`, tracking `origin/master`
- Multiple commits related to Vercel deployment fixes have been pushed but not reflected in live behavior

## Summary

The deployment pipeline has these configuration layers:
1. **Frontend** (SMS) → rewrites `/api/*` to backend API
2. **Backend API** (API) - Vercel Python serverless functions - STALE
3. **Django app** - code in git, not reaching the serverless functions
4. **Database** - Neon PostgreSQL, accessible and functional

The blocker is between layers 2 and 3: code changes in git are not being packaged and deployed to the Vercel Python serverless functions.