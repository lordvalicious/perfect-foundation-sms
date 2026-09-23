PHASE 74 — PRODUCTION CERTIFICATION EXECUTION PLAN
====================================================

NAME: PHASE_74_PRODUCTION_CERTIFICATION_EXECUTION_PLAN
OBJECTIVE: Execute production certification for the Perfect Foundation SMS system
based on direct evidence obtained after resolving Phase 73 blockers.
This plan performs NO changes to source code, production configuration, Vercel
settings, database, production data, or user accounts. All actions are
investigative/testing only.

==========================================================================
PRECONDITIONS — MUST BE COMPLETED BEFORE PHASE 74 EXECUTION
==========================================================================

1. R73-P0-001 RESOLVED: Production deployment identity established
   - Deployment ID known for frontend project
   - Deployment ID known for backend project
   - Git commit SHA for each deployment verified
   - Production alias targets verified
   - /api/deploy-test/ returns PHASE66_DEPLOYMENT_PROOF_20260923

2. R73-P0-002 RESOLVED: Browser automation capability available
   - Headless browser (Playwright, Selenium) or physical browser access
   - Can navigate to https://perfect-foundation-sms.vercel.app/
   - Can enter credentials for test accounts
   - Can establish authenticated sessions with CSRF tokens

3. R73-P2-003 PARTIALLY RESOLVED: Vercel dashboard access obtained
   - Production deployment configuration visible
   - Build logs reviewable
   - Function artifacts inspectable

If any precondition is NOT met, Phase 74 must not proceed past that step.

==========================================================================
WORKSTREAM A — DEPLOYMENT IDENTITY
==========================================================================

Goal: Prove exactly which Vercel deployment/revision is serving production
frontend and backend.

Required evidence:
- deployment_id_frontend
- deployment_id_backend
- commit_sha_frontend
- commit_sha_backend
- production_alias_frontend (https://perfect-foundation-sms.vercel.app/)
- production_alias_backend (https://perfect-foundation-api.vercel.app/)
- branch_frontend
- branch_backend
- build_result_frontend
- build_result_backend
- deploy_test_marker_confirmed (PHASE66_DEPLOYMENT_PROOF_20260923)

Procedure:
1. Access Vercel dashboard for perfect-foundation-sms project
2. Record current deployment ID, commit SHA, branch, build timestamp
3. Access Vercel dashboard for perfect-foundation-api project
4. Record current deployment ID, commit SHA, branch, build timestamp
5. Call /api/deploy-test/ on both frontend and backend
6. Verify response contains PHASE66_DEPLOYMENT_PROOF_20260923
7. Document frontend→backend revision match (or mismatch)

Acceptance criterion:
Production deployment identity is definitively established.
Both deployments have known commit SHAs. /api/deploy-test/ returns
expected marker on both. Any revision mismatch is documented.

==========================================================================
WORKSTREAM B — REAL BROWSER AUTHENTICATION
==========================================================================

Goal: Perform actual authenticated testing through the deployed frontend.

For each available test account (see Phase 73 role inventory):

PROCEDURE per role:
1. NAVIGATE to https://perfect-foundation-sms.vercel.app/
2. LOGIN with test account credentials
   - Capture CSRF token from form
   - Submit login POST
   - Verify session cookie set
3. SESSION verification
   - Verify CSRF token valid on subsequent requests
   - Verify session persists across page refreshes
4. DASHBOARD
   - Verify dashboard page loads
   - Verify user role displayed correctly
5. ROLE ACCESS
   - Verify navigation to role-permitted sections
   - Verify denial/restriction of role-forbidden sections where safely testable
6. MODULE ACCESS
   - Navigate to module endpoints appropriate for role
   - Library (librarian role)
   - Reports (accountant/HR role)
   - Visitors (guard role)
   - Health Records (nurse role)
   - Payroll (HR role)
   - Record which modules load and which return 403/404
7. READ-ONLY OPERATION
   - Perform safe read-only operation appropriate for role
   - Example: List records, view details (not create/edit/delete)
   - Capture HTTP status, response body
8. LOGOUT
   - Initiate logout
   - Verify session invalidated
   - Verify re-login required
9. RELOGIN
   - Re-enter credentials
   - Verify session establishment works consistently

Acceptance criterion:
Authentication and role access are proven for every tested role.
Each role: login → dashboard → module access → read-only operation → logout
all recorded with direct evidence (HTTP statuses, response snippets, session behavior).

==========================================================================
WORKSTREAM C — ROLE CERTIFICATION
==========================================================================

Use the existing Phase 73 role×module matrix. Do not create a new role
inventory unless Phase 73 evidence requires it.

The Phase 73 identified roles are:
SUPER_ADMIN, ADMIN, PRINCIPAL, VICE_PRINCIPAL, CAMPUS_ADMIN, ACADEMIC,
ACCOUNTANT, TEACHER, STUDENT, PARENT, HR, STAFF, RECEPTIONIST, GUARD, NURSE,
LIBRARIAN, ALUMNI, DIGITAL_IDS

For each role, perform:

1. authenticate — login through production frontend, capture session
2. verify_dashboard — dashboard loads, role displayed correctly
3. verify_navigation — permitted modules accessible; forbidden modules
   inaccessible (record HTTP status)
4. perform_read_only — safe read-only operation (list, view details)
5. record_evidence — HTTP statuses, response snippets, session behavior

Status must be exactly one of:
- PASS — all steps completed successfully with expected behavior
- FAIL — step demonstrably failed (e.g., 403, 404, redirect to login)
- UNVERIFIABLE — step could not be performed (environment limitation, not failure)

Never infer PASS from source code. PASS must come from direct evidence
of the deployed production system.

Acceptance criterion:
Every tested role has a recorded status of PASS, FAIL, or UNVERIFIED.
No role is certified as PASS unless direct production evidence exists.

==========================================================================
WORKSTREAM D — MODULE CERTIFICATION
==========================================================================

Use the existing Phase 73 master feature matrix. Do not create a new
module inventory unless Phase 73 evidence requires it.

For every module identified in Phase 73:

PROCEDURE:
1. identify_implemented — is the module present in source code? (YES/NO)
   - Based on Phase 73 master feature matrix source code inspection
   - This step does NOT certify production functionality
2. identify_deployed — is the module present in the deployed production
   revision? (YES/NO)
   - Based on Phase 73 deployment verification (or UNVERIFIED if
     deployment identity not yet established)
3. authenticate_with_role — login with appropriate role (from Phase 73
   role×matrix)
4. test_safe_read_only — perform safe read-only operation on the module
   - List records, view details, search, filter
   - Do NOT create, edit, or delete records
   - Capture HTTP status, response body evidence
5. record_result — one of:
   - PASS — read-only operation succeeded in production
   - FAIL — read-only operation failed (404, 500, authorization error)
   - UNVERIFIABLE — could not test (no authenticated session, module
     not deployed, role not permitted)
   - IMPLEMENTED_BUT_NOT_CERTIFIED — module present in source but not
     proven in production (documentation status only)

Where data mutation is required for full certification:
- DO NOT mutate production.
- Keep the feature marked: IMPLEMENTED BUT NOT CERTIFIED
- until an approved safe test procedure exists in a staging/test environment
- Document the mutation required and the blocker.

Acceptance criterion:
Every module has a recorded status. No module is certified PASS unless
direct production evidence exists. IMPLEMENTED BUT NOT CERTIFIED is an
acceptable status for features that are source-implemented but not yet
production-certified.

==========================================================================
WORKSTREAM E — DATA-MUTATION CERTIFICATION
==========================================================================

Use PHASE_73_DATA_MUTATION_CERTIFICATION_BLOCKERS.csv.

For every feature listed in that document determine:

1. staging_test_tenant_exists — does a non-production tenant /
   environment exist with test data?
2. disposable_test_dataset_exists — does a disposable test dataset
   exist that mimics production data structure?
3. production_safe_test_procedure_exists — is there an approved test
   procedure that does not risk real school data?
4. certification_without_data_mutation — can the feature be certified
   as working without performing data mutation?

Determination table:

| FEATURE | STAGING_EXISTS | TEST_DATA_EXISTS | SAFE_PROCEDURE | CERTIFICATION_PATH |
|---------|---------------|-----------------|----------------|-------------------|
| student CRUD | TO BE DETERMINED | TO BE DETERMINED | TO BE DETERMINED | impemented_but_not_certified |
| payroll processing | TO BE DETERMINED | TO BE DETERMINED | TO BE DETERMINED | implemented_but_not_certified |
| fee payment | TO BE DETERMINED | TO BE DETERMINED | TO BE DETERMINED | implemented_but_not_certified |
| library issue/return | TO BE DETERMINED | TO BE DETERMINED | TO BE DETERMINED | implemented_but_not_certified |
| ... (all 17 features) | ... | ... | ... | ... |

DECISION RULES:
- If staging/test tenant exists WITH test data → certification can proceed
  using test data (do not touch production)
- If staging/test tenant exists WITHOUT test data → cannot certify without
  mutation authorization; document as "requires_mutation_auth"
- If no staging/test tenant exists → cannot certify; document as
  "staging_required"
- If production data mutation would be required and no authorization →
  keep feature marked "IMPLEMENTED BUT NOT CERTIFIED"

Acceptance criterion:
For each mutation-blocked feature, one of the following is documented:
(a) certification completed using safe test data, OR
(b) explicit path to certification established (staging required,
   test data needed, authorization pending), OR
(c) feature remains marked IMPLEMENTED BUT NOT CERTIFIED with documented
   reason.

No data mutation is performed during Phase 74 unless explicitly authorized
in a separate task outside this plan.

==========================================================================
WORKSTREAM F — SECURITY / TENANT ISOLATION
==========================================================================

Only perform safe, non-destructive verification. Do NOT attempt destructive
security testing against production.

TEST ITEMS (perform only what is safely possible without authentication
or data mutation):

1. ROLE AUTHORIZATION — via HTTP status codes and routing verification:
   - Attempt authenticated API calls with known session (if available)
   - Record 200/401/403/404 responses for each role on each endpoint
   - Verify role-based permissions produce expected responses
   - DO NOT attempt to bypass or exploit authorization checks

2. TENANT BOUNDARIES — via routing and header verification:
   - Verify that endpoints include tenant/campus identifiers where expected
   - Check CORS headers for expected origins
   - Verify CSRF token requirements on sensitive endpoints
   - DO NOT attempt cross-tenant access testing

3. CAMPUS BOUNDARIES — via routing and header verification:
   - Same as tenant boundaries, for campus-level isolation
   - Verify expected campus-specific behavior from response headers

4. SESSION SECURITY — via HTTP-only, SameSite, Secure flag inspection:
   - If browser automation available, inspect session cookie flags
   - Verify HttpOnly flag present on session cookies
   - Verify SameSite attribute set
   - Verify Secure flag on HTTPS endpoints
   - DO NOT attempt session fixation or hijacking

5. CSRF VERIFICATION — via token requirement inspection:
   - Verify CSRF token required on POST/PUT/DELETE endpoints
   - Verify CSRF token validation behavior (403 without token)
   - DO NOT attempt CSRF token theft or replay

6. CORS INSPECTION — via HTTP headers:
   - Check Access-Control-Allow-Origin on API endpoints
   - Check Access-Control-Allow-Methods
   - Check Access-Control-Allow-Headers
   - Verify expected origins are allowed (or restricted)
   - DO NOT attempt cross-origin request forgery

7. PERMISSIONS VERIFICATION — via role-based endpoint access:
   - If authenticated session available, test each role on each endpoint
   - Record which roles can access which endpoints
   - Record 403/404 responses for unauthorized access
   - DO NOT attempt to escalate privileges

8. AUDIT LOGGING — via header and response inspection:
   - Check for audit log entries on CRUD operations (if any)
   - Verify log entries include user, timestamp, action, resource
   - DO NOT attempt to manipulate or delete audit logs

Acceptance criterion:
All safely testable security items have been verified. Findings documented
as PASS (expected behavior observed), FAIL (unexpected behavior), or
UNVERIFIABLE (could not test due to environment limitations). No
destructive testing performed. No production data risked.

==========================================================================
FINAL PHASE 74 ACCEPTANCE CRITERIA
==========================================================================

Phase 74 should only be considered complete when ALL of the following
are satisfied. Each criterion must be met with direct evidence, not
inference or source-code analysis.

1. FRONTEND DEPLOYMENT IDENTITY PROVEN
   - Frontend deployment ID known
   - Frontend commit SHA known
   - Frontend branch known
   - /api/deploy-test/ returns PHASE66_DEPLOYMENT_PROOF_20260923 on frontend

2. BACKEND DEPLOYMENT IDENTITY PROVEN
   - Backend deployment ID known
   - Backend commit SHA known
   - Backend branch known
   - /api/deploy-test/ returns PHASE66_DEPLOYMENT_PROOF_20260923 on backend

3. FRONTEND→BACKEND PRODUCTION CONNECTION PROVEN
   - Frontend and backend serving matching deployment revision
   - /api/deploy-test/ marker consistent across both
   - At least one authenticated API call from frontend to backend succeeds

4. AUTHENTICATION PROVEN THROUGH REAL DEPLOYED UI
   - At least one test account successfully logs in via production frontend
   - Session established with CSRF token
   - Session persists across page refreshes
   - Logout works and invalidates session

5. REQUIRED PRODUCTION ROLES TESTED
   - At least the core roles (SUPER_ADMIN, ADMIN, TEACHER, STUDENT)
     have been tested through authenticated production frontend
   - Status recorded for each: PASS, FAIL, or UNVERIFIED

6. MAJOR MODULES TESTED
   - At least the major modules (Library, Reports, Visitors, Payroll,
     Health Records) have been tested with appropriate roles
   - Status recorded for each: PASS, FAIL, UNVERIFIED, or
     IMPLEMENTED_BUT_NOT_CERTIFIED

7. WORKING FEATURES SEPARATED FROM UNCERTIFIED FEATURES
   - Features proven working in production (direct evidence)
   - Features uncertified (source implemented but not proven in production)
   - Actual failures separated from untested features
   - No feature claimed as "working" without production evidence

8. ACTUAL FAILURES SEPARATED FROM UNTESTED FEATURES
   - Verified failing features (tested and demonstrably broken)
   - Untested features (cannot be tested without browser/auth)
   - No failure claimed without direct test evidence
   - No feature claimed as "working" without production evidence

9. DEPLOYMENT PROBLEMS SEPARATED FROM APPLICATION PROBLEMS
   - Deployment/revision verification problems identified (deployment
     marker 404, unknown commit SHA, alias mismatch)
   - Application defects identified (actual endpoint failures, broken
     workflows, error conditions)
   - Testing environment limitations documented (no browser access,
     no authenticated session possible)
   - Each problem classified into exactly one category

10. MUTATION-DEPENDENT FEATURES HAVE EXPLICIT CERTIFICATION PATH
    - For each feature requiring data mutation, one of:
      (a) certification completed using safe test data, OR
      (b) explicit path documented (staging required, authorization
          pending), OR
      (c) feature remains IMPLEMENTED BUT NOT CERTIFIED with documented
          reason
    - No feature certified PASS without safe test procedure

11. ALL CRITICAL TECHNICAL BLOCKERS RESOLVED OR EXPLICITLY DOCUMENTED
    - R73-P0-001 (deployment identity) resolved or explicit blocker
      documented preventing resolution
    - R73-P0-002 (browser authentication) resolved or explicit blocker
      documented preventing resolution
    - R73-P2-003 (deployment pipeline config) resolved or documented
    - All Phase 73 critical technical issues addressed or documented

12. FINAL PRODUCTION CERTIFICATION REPORT CAN BE PRODUCED FROM DIRECT EVIDENCE
    - All findings based on direct evidence from deployed production system
    - No claims based on source code, Git commits (unverified), or
      inference
    - Report includes: deployment identities, role certification
      statuses, module certification statuses, working features,
      failing features, uncertified features, technical blockers,
      data-mutation certification paths
    - Report can be generated from the Phase 74 deliverables

==========================================================================
REQUIRED PHASE 74 DELIVERABLES
==========================================================================

Must create the following files (none perform changes; all are
investigative/test plan and evidence records):

1. PHASE_74_DEPLOYMENT_IDENTITY_REPORT.md
   - Production deployment identities (frontend + backend)
   - Commit SHAs, branches, deployment IDs
   - /api/deploy-test/ marker verification
   - Any revision mismatches documented

2. PHASE_74_AUTHENTICATED_TEST_LOG.md
   - Per-role: login, session, dashboard, module access, read-only ops, logout
   - HTTP statuses, response snippets, session behavior
   - PASS/FAIL/UNVERIFIED status for each role

3. PHASE_74_ROLE_CERTIFICATION_MATRIX.csv
   - Every role: PASS/FAIL/UNVERIFIED
   - Per-module access verified
   - Read-only operation results

4. PHASE_74_MODULE_CERTIFICATION_MATRIX.csv
   - Every module: PASS/FAIL/UNVERIFIED/IMPLEMENTED_BUT_NOT_CERTIFIED
   - Per-role test results
   - Read-only operation evidence

5. PHASE_74_SECURITY_VERIFICATION_REPORT.md
   - All safely testable security findings
   - Role authorization results
   - Session security flag inspection
   - CSRF, CORS, permission verification

6. PHASE_74_DATA_MUTATION_STATUS_REPORT.md
   - Per the PHASE_73_DATA_MUTATION_CERTIFICATION_BLOCKERS.csv
   - For each feature: staging exists, test data exists, safe procedure,
     certification path
   - No data mutated during Phase 74

7. PHASE_74_FINAL_CERTIFICATION_REPORT.md
   - Complete production certification report
   - All 12 acceptance criteria met or documented as unresolved
   - Overall: PRODUCTION_CERTIFIED / PARTIALLY_CERTIFIED /
     NOT_YET_CERTIFIED
   - Recommendations for Phase 75 (if needed)

==========================================================================
PHASE 74 EXECUTION ORDER
==========================================================================

Phase 74 must be executed in strict order. Do not skip or reorder:

PHASE 74 STEP 1: WORKSTREAM A (Deployment Identity)
   — Must complete before any other workstream
   — Requires Vercel dashboard access
   — Output: PHASE_74_DEPLOYMENT_IDENTITY_REPORT.md

PHASE 74 STEP 2: WORKSTREAM B (Browser Authentication)
   — Must complete after Step 1
   — Requires browser automation or physical browser
   — Output: PHASE_74_AUTHENTICATED_TEST_LOG.md

PHASE 74 STEP 3: WORKSTREAM C (Role Certification)
   — Must complete after Step 2
   — Test each role through authenticated frontend
   — Output: PHASE_74_ROLE_CERTIFICATION_MATRIX.csv

PHASE 74 STEP 4: WORKSTREAM D (Module Certification)
   — Must complete after Step 3
   - Test each module with appropriate role
   — Output: PHASE_74_MODULE_CERTIFICATION_MATRIX.csv

PHASE 74 STEP 5: WORKSTREAM E (Data-Mutation Certification)
   — Can begin parallel with Step 4
   - Determine certification paths for mutation-blocked features
   — Output: PHASE_74_DATA_MUTATION_STATUS_REPORT.md

PHASE 74 STEP 6: WORKSTREAM F (Security/Tenant Isolation)
   — Can begin after Step 2 (browser auth) or parallel with Steps 4-5
   - Only safe, non-destructive verification
   — Output: PHASE_74_SECURITY_VERIFICATION_REPORT.md

PHASE 74 STEP 7: FINAL CERTIFICATION REPORT
   — Must complete after all workstreams have produced output
   - Evaluate all 12 acceptance criteria
   - Output: PHASE_74_FINAL_CERTIFICATION_REPORT.md

==========================================================================
ROLLING AUTHORIZATIONS
==========================================================================

The following authorizations are REQUIRED before proceeding:

AUTHORIZATION_Vercel_Dashboard_Access:
- Required for: WORKSTREAM A (Deployment Identity)
- Obtain from: Platform/DevOps team with Vercel account
- Without: Phase 74 cannot proceed past Step 1

AUTHORIZATION_Browser_Automation:
- Required for: WORKSTREAM B, C (partially), F (partially)
- Obtain from: QA/Testing team with Playwright/Selenium setup
- Without: All browser-dependent steps blocked

AUTHORIZATION_Test_Staging_Access:
- Required for: WORKSTREAM E (Data-Mutation Certification)
- Obtain from: Platform/DBA team with staging environment access
- Without: Mutation-blocked features cannot be certified; must remain
  IMPLEMENTED BUT NOT CERTIFIED with documented reason

AUTHORIZATION_Production_Data_Mutation:
- Required ONLY if explicit mutation test procedure approved outside
- this plan. NEVER assume authorization. Always verify separately.
- Without: No production data mutation permitted during Phase 74

==========================================================================
PLAN STATUS ON ENTRY
==========================================================================

PHASE_74_STATUS=PENDING — awaiting precondition verification
PRECONDITIONS_MET=0 of 3 (deployment identity, browser auth, dashboard access)
EXPECTED_COMPLETION=7 workstreams, 13 deliverables
CRITICAL_PATH=Step 1 → Step 2 → Step 3 → Step 4 → [Step 5 & 6 parallel] → Step 7

ALL STATEMENTS BASED ON PHASE 73 EVIDENCE. NO NEW ISSUES INVENTED.
NO CHANGES TO PRODUCTION PERFORMED. THIS PLAN IS INVESTIGATIVE/TEST-ONLY.