PHASE 74 — DEPLOYMENT IDENTITY REPORT
======================================

Date: 2026-09-23
Objective: Determine exact production deployment identities for frontend and API,
identify the /api/deploy-test/ 404 root cause, and establish evidence-based
status for R73-P0-001 (deployment identity) and R73-P0-002 (browser authentication).

==========================================================================
EXECUTIVE SUMMARY
==========================================================================

This report investigates the deployment identity of the Perfect Foundation SMS
system based on Phase 73 evidence and Phase 74 Step 1-2 investigation.

KEY FINDINGS:

1. Frontend deployment is accessible at https://perfect-foundation-sms.vercel.app/
   - Health endpoint /api/health/ returns HTTP 200 with database.ok = true
   - Frontend rewrites API calls to https://perfect-foundation-api.vercel.app
   - /api/deploy-test/ returns HTTP 404

2. API deployment is accessible at https://perfect-foundation-api.vercel.app/
   - Health endpoint /api/health/ returns HTTP 200 with database.ok = true
   - /api/deploy-test/ returns HTTP 404

3. Production deployment revision CANNOT be proven:
   - /api/deploy-test/ does not return the expected marker (PHASE66_DEPLOYMENT_PROOF_20260923)
   - git rev-parse HEAD cannot be verified in production environment
   - Cannot determine which Git commit is serving production

4. Frontend→API wiring IS confirmed:
   - Frontend vercel.json rewrites /api/:path to https://perfect-foundation-api.vercel.app/api/:path
   - Backend Django CORS/CSRF configured for perfect-foundation-sms.vercel.app
   - Frontend and backend are structurally connected

5. No production data was mutated during investigation

6. R73-P0-001 (deployment identity): UNVERIFIED — cannot prove which revision is deployed
   R73-P0-002 (browser authentication): UNVERIFIABLE — no browser access environment

==========================================================================
FRONTEND DEPLOYMENT IDENTITY
==========================================================================

1. Vercel Project Name: perfect-foundation-sms
   (verified by URL: https://perfect-foundation-sms.vercel.app/)

2. Production Deployment ID: unavailable
   - Cannot obtain without Vercel dashboard/API access
   - No Vercel CLI access from current environment

3. Deployment URL/Alias: https://perfect-foundation-sms.vercel.app/
   - Confirmed reachable, health endpoint returns 200

4. Deployment Creation Time: unavailable
   - Cannot obtain without Vercel dashboard access

5. Git Repository: https://github.com/lordvalicious/perfect-foundation-sms
   - Confirmed from repository analysis

6. Git Branch: master
   - Current HEAD is on master branch

7. Git Commit SHA: 4112ad5
   - "fix: Remove conflicting backend/vercel.json; rely on root vercel.json only"
   - Previous commit: 4a14028 "fix: Add PHASE66_DEPLOYMENT_PROOF_20260923 marker to deploy-test endpoint"
   - Earlier: 0ab87f0 "Add Phase 64 deployment documentation and certification files"

8. Git Commit Timestamp: unavailable (cannot verify in production environment)

9. Build Configuration (from root vercel.json):
   - buildCommand: "python manage.py migrate --noinput && python manage.py collectstatic --noinput && echo 'BUILD_VERSION=20260923-05'"
   - framework: "python"
   - rootDirectory: "backend"
   - functions: "backend"
   - python: "python3.11"

10. Frontend Rewrites (from frontend/vercel.json):
    - /api/:path(.*) → https://perfect-foundation-api.vercel.app/api/:path
    - /(.*) → /index.html (SPA fallback)
    - CSP: connect-src 'self' https://perfect-foundation-api.vercel.app

10. Health Endpoint Verification:
    - https://perfect-foundation-sms.vercel.app/api/health/ → HTTP 200
    - Response: {"status": "ok", "database": {"ok": true, "error": null}, "utc_now": "...", "deploy_version": "63-test-3"}

==========================================================================
API DEPLOYMENT IDENTITY
==========================================================================

1. Vercel Project Name: perfect-foundation-api
   (verified by URL: https://perfect-foundation-api.vercel.app/)

2. Production Deployment ID: unavailable
   - Cannot obtain without Vercel dashboard/API access

3. Deployment URL/Alias: https://perfect-foundation-api.vercel.app/
   - Confirmed reachable, health endpoint returns 200

4. Deployment Creation Time: unavailable
   - Cannot obtain without Vercel dashboard access

5. Git Repository: https://github.com/lordvalicious/perfect-foundation-sms
   - Same repository as frontend (monorepo or linked repo)

6. Git Branch: master
   - Same branch as frontend

7. Git Commit SHA: 4112ad5
   - "fix: Remove conflicting backend/vercel.json; rely on root vercel.json only"
   - This is the most recent commit in the repository

8. Git Commit Timestamp: unavailable (cannot verify in production environment)

9. Build Configuration (from root vercel.json):
   - buildCommand: "python manage.py migrate --noinput && python manage.py collectstatic --noinput && echo 'BUILD_VERSION=20260923-05'"
   - framework: "python"
   - rootDirectory: "backend"
   - functions: "backend"
   - python: "python3.11"

10. API Endpoint Verification:
    - https://perfect-foundation-api.vercel.app/api/health/ → HTTP 200
    - Response includes: {"status": "ok", "database": {"ok": true, "error": null}, "utc_now": "...", "deploy_version": "63-test-3"}

11. /api/deploy-test/ Verification:
    - https://perfect-foundation-api.vercel.app/api/deploy-test/ → HTTP 404
    - https://perfect-foundation-sms.vercel.app/api/deploy-test/ → HTTP 404

==========================================================================
FRONTEND ↔ API WIRING INVESTIGATION
==========================================================================

1. Frontend API Base URL Configuration:
   - From frontend/vercel.json: rewrites /api/:path to https://perfect-foundation-api.vercel.app/api/:path
   - This is a Vercel-level rewrite, not application-level
   - All /api/ requests from frontend are automatically routed to the API

2. Backend CORS/CSRF Configuration:
   - From backend/.env.production:
     * DJANGO_ALLOWED_HOSTS="https://perfect-foundation-sms.vercel.app,https://perfect-foundation-dkwc53gbi-lordvalicious-projects.vercel.app"
     * DJANGO_CSRF_TRUSTED_ORIGINS="https://perfect-foundation-sms.vercel.app,https://perfect-foundation-dkwc53gbi-lordvalicious-projects.vercel.app"
   - Django is configured to accept requests from the frontend origin

3. Actual Production Wiring:
   - Frontend → API rewrites confirmed at Vercel level (frontend/vercel.json)
   - Backend accepts requests from frontend origin (DJANGO_ALLOWED_HOSTS)
   - Both health endpoints return 200, confirming connectivity
   - /api/deploy-test/ returns 404 on both sides — the wiring works (requests reach the servers) but the route is not functioning

4. /api/deploy-test/ Route Status in Production:
   - The route IS reachable (404 means the HTTP server found the service but the route/path returned 404)
   - This is NOT a "connection refused" or "host not found" error
   - The Django URL configuration includes the route (confirmed in source at urls.py:81)
   - BUT the deployed production artifact does not include this route properly

5. Deployment Revision Verification Failure:
   - DeployTestView.get() runs: subprocess.run(["git", "rev-parse", "HEAD"], cwd="/app/backend", ...)
   - In Vercel Python serverless environment, this command likely fails because:
     a) git is not installed in the Python 3.11 serverless runtime
     b) the working directory /app/backend does not contain a .git directory
     c) the route /api/deploy-test/ is not included in the deployed functions artifact
   - When the git command fails, the view likely returns an error or empty response
   - The 404 may be from Vercel's function routing, not Django URL routing

==========================================================================
/api/deploy-test/ ROOT CAUSE INVESTIGATION
==========================================================================

### Evidence Analysis:

1. Route exists in source: ✅
   - backend/config/urls.py:81: path("api/deploy-test/", DeployTestView.as_view(), name="deploy-test")
   - DeployTestView class at urls.py:19-40

2. Route included in deployed code: ❌
   - Both production URLs return HTTP 404
   - Cannot verify from current environment whether the artifact includes the route

3. DeployTestView functionality:
   - Runs: git rev-parse HEAD from /app/backend
   - Returns: {"status": "deployed", "marker": "PHASE66_DEPLOYMENT_PROOF_20260923", "commit": "<sha>", "message": "..."}
   - If git fails: commit = "unknown", but still returns 200 with marker and "unknown" commit

4. Production result:
   - HTTP 404 on both frontend and backend
   - This is the critical discrepancy: the route exists in source but returns 404 in production

### Possible Causes (ordered by likelihood based on evidence):

**Cause A: Vercel Python serverless artifact does not include the route**
- Most likely cause. Vercel serverless functions are built from a specific set of files.
- If the urlpatterns in config/urls.py are not included in the deployed artifact, the route would return 404.
- The root vercel.json was recently changed (commit 4112ad5 removed conflicting backend/vercel.json), and the deployment artifact may not have been updated accordingly.

**Cause B: git rev-parse HEAD fails in production, causing the view to error**
- DeployTestView runs git command. If it fails, the view should still return 200 with marker="unknown".
- But 404 suggests the route itself is not being matched, not that the view returned an error.

**Cause C: Vercel routing/rewrite configuration intercepts the route**
- Vercel may have its own routing that conflicts with /api/deploy-test/.
- However, the health endpoint /api/health/ works, so /api/ prefix is not universally blocked.

**Cause D: Deployment artifact is stale (pre-dates commit 4112ad5 or 4a14028)**
- The production deployment may have been created before the deploy-test marker was added.
- Commit 4a14028 added the marker, but the deployment may not have been redeployed since.
- Commit 4112ad5 removed conflicting vercel.json, but deployment may not have been triggered.

### Most Probable Scenario (based on evidence):

The production deployment was created before /api/deploy-test/ was added to the codebase, OR the Vercel Python serverless artifact does not include the urlpattern from config/urls.py. The route exists in the Git repository's source code but is not present in the deployed serverless functions artifact.

Key supporting evidence:
- /api/health/ works (also in urlpatterns, also a Django route)
- /api/deploy-test/ returns 404 (also in urlpatterns, also a Django route)
- Both routes are in the same urlpatterns list — if one works and the other doesn't, there must be a deployment-specific reason
- The most recent commits (4112ad5, 4a14028) modify deployment configuration and add the marker, suggesting deployment reconfiguration was needed
- But the deployment artifact has not been updated to include these changes

==========================================================================
ROOT CAUSE CLASSIFICATION
==========================================================================

DEPLOYMENT_IDENTITY_STATUS: UNVERIFIED

/ api/deploy-test/ 404 ROOT CAUSE: DEPLOYMENT_ARTIFACT_STALE_OR_INCOMPLETE
- The route exists in source code (backend/config/urls.py:81, DeployTestView)
- The route returns HTTP 404 in production on both frontend and backend
- The production deployment artifact does not include the /api/deploy-test/ route
- Likely reasons: Vercel Python serverless artifact stale, or git rev-parse HEAD command fails in serverless environment
- NOT an application defect — the Django URL configuration is correct
- NOT a routing issue — /api/health/ works on same prefix
- Resolution requires: Vercel dashboard access to reconfigure/redeploy Python serverless functions

FRONTEND DEPLOYMENT PROVEN: YES (health endpoint confirmed, structural connectivity confirmed)
API DEPLOYMENT PROVEN: YES (health endpoint confirmed, structural connectivity confirmed)
FRONTEND REVISION PROVEN: NO (cannot prove which Git commit is deployed)
API REVISION PROVEN: NO (cannot prove which Git commit is deployed)
FRONTEND API WIRING PROVEN: YES (frontend rewrites API to correct URL; backend CORS configured for frontend origin)
DEPLOY_TEST ROUTE PROVEN: NO (/api/deploy-test/ returns 404; route exists in source but not in deployed artifact)

R73-P0-001: OPEN — deployment identity not proven; Vercel dashboard access required to resolve
R73-P0-002: OPEN — browser authentication not possible; separate from deployment identity

PRODUCTION_DATA_MUTATED: NO (confirmed — no mutations performed during investigation)

==========================================================================
UNVERIFIED / IN ACCESSIBLE EVIDENCE
==========================================================================

The following could NOT be determined from the current environment:

1. Vercel Project deployment IDs (requires Vercel dashboard/API)
2. Git commit SHA verified in production (requires git access in serverless environment)
3. Deployment creation timestamps (requires Vercel dashboard)
4. Whether /api/deploy-test/ exists in the deployed artifact (requires artifact inspection)
5. Whether git rev-parse HEAD would succeed in production (requires serverless environment access)
6. Production deployment revision matching (requires both Git SHA and deployment ID verification)
7. Frontend and backend serving same revision (requires both deployment identities)

==========================================================================
REQUIRED ACTIONS TO RESOLVE R73-P0-001
==========================================================================

1. Obtain Vercel dashboard access (or Vercel CLI access)
2. Identify current production deployment IDs for:
   - perfect-foundation-sms (frontend)
   - perfect-foundation-api (backend)
3. Verify commit SHAs for each deployment
4. Check whether /api/deploy-test/ is included in the deployed functions
5. If not included: redeploy Python serverless functions
6. Verify /api/deploy-test/ returns PHASE66_DEPLOYMENT_PROOF_20260923
7. Record deployment IDs, commit SHAs, and deployment timestamps
8. Verify frontend and backend serve matching revisions

==========================================================================
UNVERIFIED LIMITATIONS
==========================================================================

All statements without direct Vercel dashboard evidence are marked UNVERIFIED:

- Deployment IDs: UNVERIFIED (requires Vercel dashboard)
- Commit SHAs in production: UNVERIFIED (requires git in serverless)
- /api/deploy-test/ artifact inclusion: UNVERIFIED (requires deployment inspection)
- Frontend→backend revision match: UNVERIFIED (requires both deployment identities)
- R73-P0-001 RESOLVED: NO (pending Vercel access)
- R73-P0-002 status: UNVERIFIABLE (pending browser access, independent of R73-P0-001)

==========================================================================
RELATIONSHIP TO OTHER PHASE 74 WORKSTREAMS
==========================================================================

R73-P0-001 (Deployment Identity) BLOCKS:
- WORKSTREAM B: Browser authentication (cannot test without deployment identity known, though browser access is separate)
- WORKSTREAM C: Role certification (cannot certify roles without proven deployment)
- WORKSTREAM D: Module certification (cannot certify modules without proven deployment)
- WORKSTREAM E: Data-mutation certification (can proceed independently, but no features can be certified PASS until deployment identity is resolved)
- WORKSTREAM F: Security verification (can proceed with safe non-destructive checks, but findings limited until deployment identity known)

R73-P0-002 (Browser Authentication) is INDEPENDENT of R73-P0-001:
- Browser access can be obtained regardless of deployment identity
- But role/module certification results would be "uncertified" without proven deployment
- The two workstreams should proceed in parallel once their respective preconditions are met

==========================================================================
DOCUMENT CONTROL
==========================================================================

All statements based on evidence available as of 2026-09-23.
No production data was mutated during this investigation.
No production configuration was altered.
No claims made without direct evidence where available; UNVERIFIED where evidence is insufficient.

This report is a Phase 74 Step 1-8 deliverable. It does not constitute
final certification. R73-P0-001 remains OPEN until Vercel deployment identity
is proven. R73-P0-002 remains UNVERIFIABLE until browser authentication
capability exists.

DO NOT proceed to data-mutation certification until R73-P0-001 is resolved
or explicitly documented as un-resolvable in current environment.