# Phase 64 — Deployment Root Cause

## Finding

The Vercel serverless Python deployment pipeline is broken. Code changes in the repository are not reaching the live production backend at `perfect-foundation-sms.vercel.app`.

## Evidence

1. **`/api/deploy-test/` returns 404** in production despite the endpoint existing in the codebase at commit `d540ab2`. This proves the deployed backend revision does not include the latest code.

2. **`/api/health/` returns `"deploy_version": "63-test-3"`** - this is outdated and does not match the latest commit `30fa841` (or any of the recent Phase 63/64 commits).

3. **Multiple "force redeploy" commits exist** (`abc3369`, `fea1f3a`, `1581952`) but the deployment blocker persists, confirming that Vercel deployment is not simply a matter of pushing commits.

4. **Frontend rewrites ALL `/api/*` to `https://perfect-foundation-api.vercel.app/api/:path`** - the backend is a separate Vercel project, and the Python serverless functions are not updating.

5. **Root vercel.json** has `rootDirectory: "backend"`, `functions: "backend"`, `python: "python3.11"` but the **backend vercel.json** was previously missing these settings, causing Vercel to use default behavior that doesn't deploy the Python backend correctly.

6. **Git pushes have occurred** with fixes (vercel.json updates, deploy-test endpoint, buildId markers) but the live production backend continues serving stale code.

## Root Cause

Vercel's Python serverless function deployment is not detecting/packaging the latest code changes. The exact mechanism is:
- Vercel builds serverless functions from the `functions` directory specified in `vercel.json`
- The build command (`python manage.py migrate && python manage.py collectstatic`) runs but the resulting Python artifact is not being redeployed to the live functions
- This appears to be a Vercel caching/artifact issue where old function versions persist even after new commits are pushed

## Configuration Files Inspected

- `vercel.json` (root) - Build command, framework, rootDirectory, functions, python settings
- `backend/vercel.json` - Project-specific overrides (previously missing rootDirectory/functions/python)
- `backend/config/urls.py` - Contains `DeployTestView` at `/api/deploy-test/`
- `backend/config/wsgi.py` - WSGI application with VERCEL environment detection
- `frontend/vercel.json` - Rewrites all `/api/*` to backend host

## Immediate Next Steps

1. Fix the actual Vercel deployment pipeline so Python code changes reach production
2. Verify `/api/deploy-test/` returns the correct git commit SHA
3. Re-run specialized role certification against the live production backend
4. Generate all Phase 64 deliverables