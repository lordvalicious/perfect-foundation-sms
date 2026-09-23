# Phase 66 — Deployment Architecture Audit

## Current Production Backend

**URL**: https://perfect-foundation-api.vercel.app  
**Vercel Project**: perfect-foundation-api (projectId: prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9)  
**Organization**: team_tfsvfjmV8ob1tVBJEIsNIMVy  
**Frontend URL**: https://perfect-foundation-sms.vercel.app  
**Frontend Vercel Project**: perfect-foundation-sms (projectId: prj_01w0P0HcW9BnLS6ustNxn6b6qsE3)  

## Repository Structure

- **Repository root**: C:\Users\Ryuk\Documents\perfect-foundation-sms
- **Git remote**: origin https://github.com/lordvalicious/perfect-foundation-sms (fetch/push)
- **Current HEAD**: latest commit SHA referenced in code
- **Default branch**: master (tracking origin/master)

## Vercel Configuration Files

### Root vercel.json
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

### Backend vercel.json
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

### Frontend .vercel/project.json
```json
{
  "projectId": "prj_01w0P0HcW9BnLS6ustNxn6b6qsE3",
  "orgId": "team_tfsvfjmV8ob1tVBJEIsNIMVy",
  "projectName": "perfect-foundation-sms",
  "settings": {
    "framework": "vite",
    "nodeVersion": "24.x",
    "rootDirectory": ".",
    "outputDirectory": null
  }
}
```

## Django Configuration

- **ROOT_URLCONF**: config.urls
- **manage.py**: invokes `config.settings` (development by default; Vercel VERCEL=1 env var triggers production)
- **wsgi.py**: has VERCEL environment detection for production vs development settings
- **asgi.py**: similar VERCEL detection for async support

## URL Routing (config/urls.py)

Key endpoints configured:
- `api/health/` — Health check endpoint (returns 200, stale deploy version)
- `api/deploy-test/` — Deployment verification endpoint (RETURNS 404 IN PRODUCTION)
- `api/auth/` — Accounts authentication
- `api/library/` — Library app routes (404 in production)
- `api/reports/` — Reports app routes (404 in production)
- `api/staff/` — Staff endpoints
- `api/dashboard/` — Dashboard endpoints
- `api/students/` — Student endpoints
- `api/teachers/` — Teacher endpoints
- `api/attendance/` — Attendance endpoints
- `api/schools/` — School endpoints
- `api/finance/` — Finance endpoints
- `api/exams/` — Exam endpoints
- `api/report-cards/` — Report cards endpoints
- `api/timetable/` — Timetable endpoints
- `api/events/` — Event endpoints
- `api/communication/` — Communication endpoints
- `api/csp-report/` — CSP violation reporting
- `api/audit/` — Audit endpoints
- `api/library/` — Library app routes (included from apps.library.urls)
- `api/transport/` — Transport app routes
- `api/inventory/` — Inventory app routes
- `api/payroll/` — Payroll app routes
- `api/hr/` — HR app routes
- `api/reports/` — Reports app routes (included from apps.reports.urls)
- `api/search/` — Search endpoints
- `api/documents/` — Document endpoints
- `api/discipline/` — Discipline endpoints
- `api/homework/` — Homework endpoints
- `api/health-records/` — Health records endpoints
- `api/alumni/` — Alumni endpoints
- `api/hostel/` — Hostel endpoints
- `api/lms/` — LMS endpoints
- `api/portal/` — Portal endpoints
- `api/white-label/` — White label endpoints
- `api/workflow/` — Workflow endpoints
- `api/helpdesk/` — Helpdesk endpoints
- `api/visitors/` — Visitor endpoints
- `api/digital-ids/` — Digital IDs endpoints
- `api/saas/` — SaaS endpoints

## Verified Live Production State (Before Phase 66)

| Endpoint | Status | Notes |
|----------|--------|-------|
| `/api/deploy-test/` | **404** | Critical — deployment verification endpoint not deployed |
| `/api/health/` | **200** | Works (DB connectivity confirmed); returns stale deploy version |
| `/api/library/` | **404** | Library root not deployed |
| `/api/library/books/` | **403** | Returns 403 (auth issue in stale deployment) |
| `/api/reports/` | **404** | Reports base not deployed |
| `/api/reports/library/` | **403** | Returns 403 (permission issue in stale deployment) |

Both `perfect-foundation-api.vercel.app` and `perfect-foundation-sms.vercel.app` serve stale code. The deployment pipeline is broken.

## Root Cause (Provisional)

The Vercel Python serverless function build/artifact process is not updating to reflect new commits. Multiple configuration fixes have been pushed to git (vercel.json updates, deploy-test endpoint modification, buildId markers, backend vercel.json alignment, Nurse role enum) but the live production backend continues serving stale code.

**Evidence of blocker**:
- `/api/deploy-test/` returns 404 despite code existence in repository
- `/api/health/` returns static `"deploy_version": "63-test-3"` instead of dynamic commit SHA
- Multiple redeploy commits pushed (`abc3369`, `fea1f3a`, `1581952`, `d9dcb7d`, `0ab87f0`) — blocker persists
- Both Vercel projects (frontend and backend) serve stale code

## Deployment Architecture Summary

```
Frontend (perfect-foundation-sms.vercel.app)
    │
    └── rewrites ALL /api/* to → Backend API (perfect-foundation-api.vercel.app)
                                          │
                                          └── Django Python serverless functions
                                               │
                                               └── STALE — latest code not reaching production
```

## Key Findings

1. **Two separate Vercel projects**: frontend (SMS React SPA) and backend (Django Python serverless functions)
2. **Frontend rewrites all `/api/*` to backend**: confirmed in frontend vercel.json
3. **Both projects serve stale code**: verified by `/api/deploy-test/` returning 404 on both
4. **Deployment pipeline broken**: Vercel Python serverless functions not deploying latest code from repository
5. **Configuration files updated in git**: multiple vercel.json fixes pushed but not reflected in production
6. **Health endpoint works**: confirms database connectivity but returns stale deploy version
7. **No way to verify live commit SHA**: `/api/deploy-test/` (which would return the commit) is not deployed

## Pending Repair Actions

The repair must address the fundamental Vercel Python serverless deployment blocker. Potential causes to investigate:
- Vercel project not linked to correct GitHub repository/branch
- `functions` directory not being picked up by Vercel build
- `rootDirectory` misconfiguration causing wrong artifact packaging
- Stale serverless function cache not clearing on redeploy
- `requirements.txt` path resolution issue
- Django `manage.py` execution environment mismatch
- Vercel dashboard settings overriding `vercel.json` configuration

**Next Phase (Part 4)**: Create a unique Phase 66 deployment marker and prove it reaches production.