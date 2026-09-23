PHASE 73 REMEDIATION ROADMAP
============================

This roadmap is based ENTIRELY on the evidence from Phase 73 audit deliverables.
No new issues are invented. All items below are extracted from existing audit findings.

IMPORTANT SEPARATIONS (do not conflate):
1. application defect — proven failure in live production
2. deployment/revision verification problem — cannot prove which commit is deployed
3. testing-environment limitation — cannot test due to environment constraints
4. feature implemented but uncertified — source exists but not proven in production
5. feature requiring controlled data mutation — can test only with authorized mutation
6. feature not implemented — source code does not exist

==================================================
P0 — BLOCKS PRODUCTION CERTIFICATION
==================================================

ID: R73-P0-001
AREA: Deployment Marker / Revision Verification
PROBLEM: /api/deploy-test/ returns HTTP 404 on both frontend and backend production URLs.
EVIDENCE: Confirmed 404 from https://perfect-foundation-api.vercel.app/api/deploy-test/ and https://perfect-foundation-sms.vercel.app/api/deploy-test/
CURRENT_STATUS: UNVERIFIED — cannot prove which Git commit is deployed to production
WHY_IT_MATTERS: Without knowing which revision is deployed, no feature can be certified as "working in production." The /api/deploy-test/ marker was added in commit 4a14028 but the deployment artifact does not appear to include it.
REQUIRED_ACTION: Access Vercel dashboard to identify the current production deployment ID, its Git commit SHA, and verify whether commit 4a14028 (containing the deploy-test marker) is serving production.
DEPENDENCY: Vercel dashboard access required. Cannot resolve from current shell environment.
SAFE_TO_FIX_NOW: NO — requires Vercel dashboard/configuration access.
REQUIRES_BROWSER: NO
REQUIRES_PRODUCTION_DATA: NO
REQUIRES_DATA_MUTATION: NO
OWNER_TYPE: DevOps / Platform
EXPECTED_OUTPUT: Production deployment ID, Git commit SHA, confirmation that /api/deploy-test/ returns PHASE66_DEPLOYMENT_PROOF_20260923
COMPLETION_CRITERIA: Production deployment identity is definitively established (deployment ID, commit SHA, alias target verified).

ID: R73-P0-002
AREA: Authenticated Session Establishment
PROBLEM: Cannot establish authenticated sessions in the current shell/PowerShell environment. No browser automation available.
EVIDENCE: Browser/UI environment cannot open production frontend, enter credentials, submit login forms, or establish sessions with CSRF tokens.
CURRENT_STATUS: TESTING_ENVIRONMENT_LIMITATION — cannot test authentication without browser access
WHY_IT_MATTERS: All role-specific certification, module access testing, and read-only operations require authenticated sessions. No roles or modules can be certified without this capability.
REQUIRED_ACTION: Obtain browser automation capability (headless browser, Playwright, Selenium, or physical browser access) to establish authenticated sessions with the production frontend.
DEPENDENCY: Browser automation tooling or physical browser access.
SAFE_TO_FIX_NOW: NO — environment limitation; cannot fix without tooling.
REQUIRES_BROWSER: YES — browser automation or access required.
REQUIRES_PRODUCTION_DATA: NO
REQUIRES_DATA_MUTATION: NO
OWNER_TYPE: QA / Testing
EXPECTED_OUTPUT: Authenticated session established with at least one test account; CSRF tokens captured; session cookies verified.
COMPLETION_CRITERIA: Browser automation capability available and successfully used to establish at least one authenticated session with production frontend.

==================================================
P1 — HIGH PRIORITY
==================================================

ID: R73-P1-001
AREA: Frontend-Backend Production Connection
PROBLEM: Frontend and backend URLs respond (health endpoints return 200), but /api/deploy-test/ 404 prevents production revision verification. Frontend→backend authenticated flow untested.
EVIDENCE: Health endpoints confirmed working on both sides (/api/health/ returns 200 with database.ok=true). /api/deploy-test/ returns 404. Authenticated API flow unverifiable.
CURRENT_STATUS: PARTIALLY_VERIFIED — connectivity confirmed but revision verification failed
WHY_IT_MATTERS: Cannot confirm that frontend and backend are serving the same deployment revision or that authenticated API flows work end-to-end.
REQUIRED_ACTION: Once deployment identity (R73-P0-001) is resolved, verify frontend→backend connection with authenticated sessions. Confirm that API routes used by roles are accessible from the deployed production system.
DEPENDENCY: Resolution of R73-P0-001 (deployment identity).
SAFE_TO_FIX_NOW: YES — once deployment identity is established, can verify connectivity without mutations.
REQUIRES_BROWSER: NO (once deployment known)
REQUIRES_PRODUCTION_DATA: NO
REQUIRES_DATA_MUTATION: NO
OWNER_TYPE: Full Stack / DevOps
EXPECTED_OUTPUT: Frontend and backend serving same deployment revision; authenticated API routes accessible; /api/deploy-test/ returns expected marker.
COMPLETION_CRITERIA: Frontend and backend deployment identities confirmed and verified as matching; at least one authenticated API call succeeds.

ID: R73-P1-002
AREA: Role Certification — All 11+ Roles
PROBLEM: All roles unverifiable. Cannot login, establish sessions, verify dashboards, or test module access for any role.
EVIDENCE: Phase 73 role-by-role matrix shows all roles with LOGIN_TESTED=NO, all results UNVERIFIABLE.
CURRENT_STATUS: TESTING_ENVIRONMENT_LIMITATION — all roles blocked by inability to establish authenticated sessions
WHY_IT_MATTERS: 11+ production roles (SUPER_ADMIN, ADMIN, PRINCIPAL, VICE_PRINCIPAL, CAMPUS_ADMIN, ACADEMIC, ACCOUNTANT, TEACHER, STUDENT, PARENT, HR) cannot be certified. All role-based access controls remain unproven.
REQUIRED_ACTION: After R73-P0-001 and R73-P0-002 are resolved, test each role through authenticated production frontend. Record login, dashboard loading, module access, and read-only operations for each.
DEPENDENCY: R73-P0-001 (deployment identity) and R73-P0-002 (browser authentication).
SAFE_TO_FIX_NOW: NO — requires browser authentication capability.
REQUIRES_BROWSER: YES
REQUIRES_PRODUCTION_DATA: NO
REQUIRES_DATA_MUTATION: NO
OWNER_TYPE: QA / Testing
EXPECTED_OUTPUT: Each role authenticated, dashboard accessed, permitted modules verified, read-only operations recorded, logout completed.
COMPLETION_CRITERIA: All 11+ roles tested and certified (PASS/FAIL/UNVERIFIED) through authenticated production frontend.

ID: R73-P1-003
AREA: Module Certification — Major Modules
PROBLEM: All modules unverified. Library, Reports, Visitors, Payroll, Health Records, and all others cannot be tested without authenticated sessions.
EVIDENCE: Phase 73 master feature matrix shows all modules with DEPLOYED_CONFIRMED=NO, PRODUCTION_TESTED=NO.
CURRENT_STATUS: TESTING_ENVIRONMENT_LIMITATION — all modules blocked by authentication limitation
WHY_IT_MATTERS: Major functional modules (at least 17+ identified) remain uncertified. Library, Reports, and Visitors endpoints return 404 in production (confirmed).
REQUIRED_ACTION: After R73-P0-001 and R73-P0-002, test each module with appropriate role. Record read-only behavior. Where mutation required, document and await authorized test procedure.
DEPENDENCY: R73-P0-001 and R73-P0-002.
SAFE_TO_FIX_NOW: YES — can verify implemented-but-not-certified status and record 404 findings without mutations.
REQUIRES_BROWSER: YES
REQUIRES_PRODUCTION_DATA: NO (can record what exists without accessing)
REQUIRES_DATA_MUTATION: NO (record status only; do not mutate)
OWNER_TYPE: QA / Testing
EXPECTED_OUTPUT: Each module tested with appropriate role; read-only operations recorded; 404 failures documented; features marked IMPLEMENTED BUT NOT CERTIFIED.
COMPLETION_CRITERIA: All major modules tested and status recorded (PASS/FAIL/UNVERIFIED/IMPLEMENTED_BUT_NOT_CERTIFIED).

==================================================
P2 — NORMAL PRIORITY
==================================================

ID: R73-P2-001
AREA: Security / Tenant Isolation Verification
PROBLEM: Cannot verify role-based authorization, tenant boundaries, or campus boundaries without authenticated testing.
EVIDENCE: Phase 73 security audit section marked all findings UNVERIFIABLE. No authenticated API calls possible.
CURRENT_STATUS: TESTING_ENVIRONMENT_LIMITATION
WHY_IT_MATTERS: Production security (role permissions, tenant isolation, campus boundaries) remains unproven. Critical for a school management system handling student data, grades, fees, etc.
REQUIRED_ACTION: After R73-P0-001 and R73-P0-002, perform safe, non-destructive security verification. Test role authorization boundaries, session security, CSRF, CORS — all without data mutation.
DEPENDENCY: R73-P0-001 and R73-P0-002.
SAFE_TO_FIX_NOW: YES — can run non-destructive security checks (status codes, headers, routing) without mutation.
REQUIRES_BROWSER: YES (for full flow) / NO (for HTTP-level checks)
REQUIRES_PRODUCTION_DATA: NO (can check routing, headers, status codes safely)
REQUIRES_DATA_MUTATION: NO
OWNER_TYPE: Security / DevOps
EXPECTED_OUTPUT: Role authorization status codes, session security verification, CSRF/CORS header inspection, permission boundaries documented.
COMPLETION_CRITERIA: Security verification complete for all tested roles; findings documented (PASS/FAIL/UNVERIFIED).

ID: R73-P2-002
AREA: Data-Mutation Certification Paths
PROBLEM: 17+ features require data mutation for certification (student creation, payroll processing, fee payment, library CRUD, etc.). No safe test procedure exists.
EVIDENCE: Phase 73 DATA_MUTATION_CERTIFICATION_BLOCKERS.csv identifies 17 features requiring mutation.
CURRENT_STATUS: CERTIFICATION_BLOCKED — mutation not authorized
WHY_IT_MATTERS: Many important features cannot be certified without mutation, but production data must not be risked without authorized test procedure.
REQUIRED_ACTION: Determine whether staging/test tenants exist, disposable test datasets exist, or production-safe test procedures can be established. Do not mutate production data without explicit authorization.
DEPENDENCY: Staging environment availability; test dataset authorization; separate authorization task.
SAFE_TO_FIX_NOW: NO — requires authorization for test data mutation.
REQUIRES_BROWSER: NO
REQUIRES_PRODUCTION_DATA: NO (must NOT access production data for testing)
REQUIRES_DATA_MUTATION: YES — but blocked until authorization obtained
OWNER_TYPE: DBA / Platform / Authorized Testing
EXPECTED_OUTPUT: Determination of whether safe test procedure exists; if yes, certification path established. If no, explicit documentation that certification requires mutation authorization.
COMPLETION_CRITERIA: Either (a) safe staging/test tenant with test data exists and certification can proceed, or (b) explicit documentation that mutation authorization is required before certification.

ID: R73-P2-003
AREA: Deployment Pipeline Configuration
PROBLEM: Vercel Python serverless deployment pipeline configuration may not be properly including backend artifacts. Conflicting vercel.json files were removed (commit 4112ad5), but deployment artifact verification remains blocked.
EVIDENCE: Commit 4112ad5 "fix: Remove conflicting backend/vercel.json; rely on root vercel.json only." Removed conflicting config. /api/deploy-test/ still returns 404. Root vercel.json has rootDirectory: "backend", functions: "backend", python: "python3.11".
CURRENT_STATUS: UNRESOLVED — configuration changed but verification blocked
WHY_IT_MATTERS: Deployment pipeline configuration affects what artifacts are built and deployed. Until deployment identity is verified, cannot determine if configuration is correct or if the issue is elsewhere.
REQUIRED_ACTION: After R73-P0-001 (deployment identity established), verify that the production deployment includes the expected backend code and config. Check Vercel dashboard for build logs, function artifacts, and deployment settings.
DEPENDENCY: R73-P0-001.
SAFE_TO_FIX_NOW: YES — can inspect Vercel dashboard configuration once access obtained.
REQUIRES_BROWSER: NO (dashboard access via web interface)
REQUIRES_PRODUCTION_DATA: NO
REQUIRES_DATA_MUTATION: NO
OWNER_TYPE: DevOps
EXPECTED_OUTPUT: Vercel dashboard view showing production deployment config, build results, function artifacts, and verified commit SHA.
COMPLETION_CRITERIA: Vercel dashboard confirms production deployment includes expected backend code and /api/deploy-test/ returns marker.

==================================================
P3 — OPTIONAL / POST-RELEASE
==================================================

ID: R73-P3-001
AREA: Frontend UI/UX Verification
PROBLEM: Cannot verify frontend rendering, CSS, JavaScript bundles, asset loading, routing, or SPA fallback without browser access.
EVIDENCE: Frontend health endpoint returns 200, but full frontend UI unverifiable in shell environment.
CURRENT_STATUS: TESTING_ENVIRONMENT_LIMITATION
WHY_IT_MATTERS: Frontend quality and correctness cannot be asserted without browser testing. Not a production certification blocker if backend APIs are verified.
REQUIRED_ACTION: After R73-P0-002 (browser authentication), perform frontend UI verification. Document rendering, routing, asset loading, CSS, JavaScript bundles.
DEPENDENCY: R73-P0-002.
SAFE_TO_FIX_NOW: NO — requires browser access.
REQUIRES_BROWSER: YES
REQUIRES_PRODUCTION_DATA: NO
REQUIRES_DATA_MUTATION: NO
OWNER_TYPE: Frontend / UI/UX
EXPECTED_OUTPUT: Frontend UI verified across key workflows; rendering documented; no critical UI defects found.
COMPLETION_CRITERIA: Frontend UI verified for certified workflows; UI issues documented (optional, post-release).

ID: R73-P3-002
AREA: Comprehensive Feature Completion Percentages
PROBLEM: Cannot calculate exact completion percentages without browser access to verify each feature's production status.
EVIDENCE: Phase 73 found "NOT CALCULABLE FROM AVAILABLE EVIDENCE" for all percentages.
CURRENT_STATUS: EVIDENCE_SUFFICIENCY_LIMITATION
WHY_IT_MATTERS: Stakeholders may want completion metrics, but they cannot be accurately calculated without full verification.
REQUIRED_ACTION: After Phase 74 completes (deployment identity + browser authentication), calculate precise percentages based on direct evidence.
DEPENDENCY: Phase 74 completion.
SAFE_TO_FIX_NOW: NO — requires Phase 74 evidence.
REQUIRES_BROWSER: YES (after Phase 74)
REQUIRES_PRODUCTION_DATA: NO
REQUIRES_DATA_MUTATION: NO
OWNER_TYPE: Program Management
EXPECTED_OUTPUT: Calculated percentages for: implementation completion, deployment verification, production test coverage, verified working, verified failing, implemented but uncertified, not implemented.
COMPLETION_CRITERIA: Precise percentages calculated from direct evidence obtained in Phase 74.

==================================================
ROADMAP SUMMARY
============================

TOTAL P0 BLOCKERS: 2
TOTAL P1 ITEMS: 3
TOTAL P2 ITEMS: 3
TOTAL P3 ITEMS: 2

DEPLOYMENT_IDENTITY_FIRST: R73-P0-001 must be resolved before any role/module certification can proceed.
BROWSER_AUTHENTICATION_SECOND: R73-P0-002 depends on R73-P0-001 but is independent of module testing order.
DEPLOYMENT_VERIFICATION_THRID: R73-P2-003 (deployment pipeline config) depends on R73-P0-001.

CRITICAL PATH: R73-P0-001 → R73-P0-002 → [R73-P1-002, R73-P1-003] → [R73-P2-001, R73-P2-002] → R73-P3-001

NOTICE: Items marked "SAFE_TO_FIX_NOW: YES" can be worked on IF the required dependency is already available. For example, R73-P2-003 can be worked on as soon as Vercel dashboard access is obtained, independent of R73-P0-001 — but the VERIFICATION of the fix depends on R73-P0-001.

All items strictly based on Phase 73 evidence. No new issues invented.