PHASE 76 — DEPLOYMENT MARKER ANALYSIS
======================================

This document investigates the /api/deploy-test/ endpoint. Per Phase 76
workstream B guidelines, I do not immediately modify code. I first determine
the source route, expected response, whether the route exists in the deployed
artifact, and the root cause of the 404.

==========================================================================
SOURCE ROUTE INVESTIGATION
==========================================================================

1. ROUTE DEFINITION IN SOURCE CODE:
   - File: backend/config/urls.py
   - Line 19: class DeployTestView(APIView)
   - Line 81: path("api/deploy-test/", DeployTestView.as_view(), name="deploy-test")
   - The view runs: subprocess.run(["git", "rev-parse", "HEAD"], cwd="/app/backend", ...)
   - On success, returns: {"status": "deployed", "marker": "PHASE66_DEPLOYMENT_PROOF_20260923", "commit": "<sha>", "message": "..."}
   - On failure (git command error), returns marker as "unknown" but still 200

2. ROUTE EXPECTATION:
   - Expected response: HTTP 200 with marker PHASE66_DEPLOYMENT_PROOF_20260923
   - This would prove the deployed revision and Phase 66 deployment status
   - Expected behavior per Phase 73: this marker validates production deployment

==========================================================================
DEPLOYED ARTIFACT INSPECTION
==========================================================================

1. PRODUCTION RESPONSE:
   - https://perfect-foundation-api.vercel.app/api/deploy-test/ → HTTP 404
   - https://perfect-foundation-sms.vercel.app/api/deploy-test/ → HTTP 404
   - Both return 404, not 200 with "unknown" marker or 200 with marker

2. WHAT 404 MEANS:
   - HTTP 404 means Django URL routing did not match the path /api/deploy-test/
   - The path IS defined in urlpatterns (confirmed in source), but not matched in
     production
   - This indicates the route is not included in the deployed Python serverless
     functions artifact, OR the git command fails and the view error path results
     in a 404 rather than a 200 response

3. /api/health/ COMPARISON:
   - /api/health/ returns HTTP 200 on both frontend and API ✅
   - Both /api/health/ and /api/deploy-test/ are in the same urlpatterns list
   - The fact that one works and the other doesn't proves the issue is route-
     specific, not a broad /api/ prefix blocking
   - /api/health/ does NOT run git commands; /api/deploy-test/ does

==========================================================================
ROOT CAUSE ANALYSIS
==========================================================================

### Cause A: Vercel Python serverless artifact does not include the urlpattern
(MOST PROBABLE)

- Vercel serverless functions are built from a specific set of files.
- If the urlpatterns in config/urls.py are not included in the deployed artifact,
  the route would return 404.
- The root vercel.json was recently changed (commit 4112ad5 removed conflicting
  backend/vercel.json), and the deployment artifact may not have been updated
  accordingly.
- This is the most probable cause because: (a) /api/health/ works, (b) both
    routes are in the same urlpatterns list, (c) the recent commits (4112ad5,
    4a14028) modify deployment configuration and add the marker, suggesting
    deployment reconfiguration was needed.

### Cause B: git rev-parse HEAD fails in production, causing the view to error
- DeployTestView runs: git rev-parse HEAD from /app/backend
- If it fails, the view should still return 200 with marker="unknown"
- But 404 suggests the route itself is not being matched, not that the view
  returned an error with 404 status
- This cause is less probable because 404 specifically means "route not found"
  rather than "view error"

### Cause C: Vercel routing/rewrite configuration intercepts the route
- Vercel may have its own routing that conflicts with /api/deploy-test/
- However, the health endpoint /api/health/ works, so /api/ prefix is not
  universally blocked
- This cause is less probable for the same reason as Cause B

### Cause D: Deployment artifact is stale (pre-dates commit 4112ad5 or 4a14028)
- The production deployment may have been created before the deploy-test marker
  was added
- Commit 4a14028 added the marker, but the deployment may not have been
  redeployed since
- Commit 4112ad5 removed conflicting vercel.json, but deployment may not have
  been triggered
- This cause is plausible but cannot be confirmed without Vercel dashboard access

==========================================================================
REDEPLOYMENT REQUIRED ASSESSMENT
==========================================================================

REDEPLOYMENT_REQUIRED: LIKELY YES — but cannot confirm without Vercel dashboard
access.

Reasoning:
- The /api/deploy-test/ route exists in source code but returns 404 in production
- The most probable cause is that the Vercel Python serverless artifact does not
  include this urlpattern
- Redeployment would likely fix this by rebuilding the serverless functions from
  the current codebase
- BUT: I am explicitly instructed not to redeploy merely to make the audit pass
  unless explicitly authorized. The Phase 76 workstream B guidelines state:
  "If a redeployment is clearly required, STOP before performing it and report:
  REDEPLOYMENT_REQUIRED = YES. Do not redeploy merely to make the audit pass unless
  explicitly authorized."

STATUS: REDEPLOYMENT_REQUIRED = YES (cannot confirm without Vercel access;
  but do not redeploy without explicit authorization)

==========================================================================
DEPLOYMENT MARKER FINDINGS
==========================================================================

1. ROUTE DEFINED IN SOURCE: YES ✅
   - backend/config/urls.py:81, DeployTestView class at urls.py:19-40

2. ROUTE IN DEPLOYED ARTIFACT: NO ❌
   - Both production URLs return HTTP 404

3. CURRENT DEPLOYMENT CONTAINS THE ROUTE: NO ❌
   - Cannot prove from current environment, but 404 suggests it does not

4. VERCEL BUILD CONFIGURATION EXCLUDES IT: PROBABLE ✅
   - Most likely the Python serverless build does not include this urlpattern

5. PYTHON RUNTIME/SERVERLESS ROUTING EXCLUDES IT: PROBABLE ✅
   - Same as above; the Django view exists but may not be built into the
     serverless artifact

6. /api/deploy-test/ 404 ROOT CAUSE: DEPLOYMENT ARTIFACT STALE/INCOMPLETE
   - Most probable: Vercel Python serverless artifact incomplete
   - Not an application defect; /api/health/ works on same /api/ prefix
   - Not a broad routing block; issue is route-specific

7. REDEPLOYMENT WOULD LIKELY RESOLVE: YES ✅
   - But cannot perform without explicit authorization per Phase 76 guidelines

==========================================================================
PHASE_76_DEPLOYMENT_MARKER_ANALYSIS.md
==========================================================================