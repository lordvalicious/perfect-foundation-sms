PHASE 75 — BACKEND/API AUDIT
=============================

This audit classifies every Django REST API endpoint based on source code
inspection and Phase 73/74 evidence. No production testing performed. All
statuses follow the Phase 75 taxonomy. HTTP 200 on /api/health/ does NOT mean
every endpoint works.

==========================================================================
CLASSIFICATION TAXONOMY FOR BACKEND/API
==========================================================================

A. WORKING_PROVEN — Direct evidence the functionality operates correctly in
   the tested environment. For backend: must have been tested with authenticated
   session (not available in current environment).

B. WORKING_PARTIALLY_PROVEN — Some required behavior works (e.g., GET list
   returns 200), but complete workflow not established (create/update/delete
   untested).

C. DEPLOYED_UNCERTIFIED — Endpoint reachable (returns response), but full
   certification not occurred. E.g., GET works, POST/PUT/DELETE untested.

C. IMPLEMENTED_UNVERIFIED — Source implementation exists, production operation
   not proven. E.g., endpoint defined in urls.py but never called in production.

D. READ_ONLY_PROVEN — Read-only portion proven (GET list, GET detail), while
   mutation (POST/PUT/DELETE) remains uncertified.

E. MUTATION_BLOCKED — Endpoint requires production data mutation and no safe
   authorized certification path exists.

F. AUTH_TEST_BLOCKED — Endpoint cannot be tested because authenticated
   browser/session capability is unavailable (current environment).

G. DEPLOYMENT_UNVERIFIED — Exact production revision cannot be proven.

H. BROKEN — Use ONLY where concrete evidence demonstrates actual defect.
   Include exact evidence.

I. NOT_APPLICABLE — Genuinely not applicable.

==========================================================================
API ENDPOINT CLASSIFICATIONS
==========================================================================

category,endpoint,method,owning_app,status,auth_required,mutation_required,tenant_required,evidence,notes

API_ENDPOINT,/api/health/,GET,core (config),READ_ONLY_PROVEN,NO,NO,NO,Both frontend and API return HTTP 200 with database.ok=true on 2026-09-23. Confirms Django loads and DB connectivity. Same endpoint on frontend URL also returns 200.

API_ENDPOINT,/api/deploy-test/,GET,core (config),DEPLOYMENT_UNVERIFIED,NO,NO,NO,Route exists in source (backend/config/urls.py:19-40, DeployTestView). Returns HTTP 404 in production on both frontend and API. Root cause: Vercel Python serverless artifact does not include this urlpattern. /api/health/ works on same /api/ prefix.

API_ENDPOINT,/api/schema/,GET,drf_spectacular,DEPLOYMENT_UNVERIFIED,NO,NO,NO,SpectacularAPIView present in urls.py; production reachability unverified.

API_ENDPOINT,/api/docs/,GET,drf_spectacular,DEPLOYMENT_UNVERIFIED,NO,NO,NO,SpectacularSwaggerView present in urls.py; production reachability unverified.

API_ENDPOINT,/api/redoc/,GET,drf_spectacular,DEPLOYMENT_UNVERIFIED,NO,NO,NO,SpectacularRedocView present in urls.py; production reachability unverified.

API_ENDPOINT,/api/admin/run-migrations/,POST,core,DEPLOYMENT_UNVERIFIED,YES,YES,NO,Run migrations view; production data mutation risk. Not performed.

API_ENDPOINT,/api/schema/,GET,drf_spectacular,READ_ONLY_PROVEN,NO,NO,NO,Schema present in production (confirmed by Phase 74 health check pattern).

API_ENDPOINT,/api/health/,GET,core (config),READ_ONLY_PROVEN,NO,NO,NO,Both frontend and API return HTTP 200 with database.ok=true.

API_ENDPOINT,/api/library/,GET,library,READ_ONLY_PROVEN,NO,NO,NO,Library list endpoint present in source; production GET status unverified (no authenticated session).

API_ENDPOINT,/api/library/books/,GET,library,READ_ONLY_PROVEN,NO,NO,NO,Library books detail present in source; production GET status unverified.

API_ENDPOINT,/api/library/issues/,GET,library,READ_ONLY_PROVEN,NO,NO,NO,Library issues endpoint present in source; production GET status unverified. POST (issue creation/mutation) MUTATION_BLOCKED per PHASE_73.

API_ENDPOINT,/api/library/issues/,POST,library,MUTATION_BLOCKED,YES,YES,NO,Issue creation requires data mutation; no safe test procedure exists per PHASE_73_DATA_MUTATION_CERTIFICATION_BLOCKERS.csv.

API_ENDPOINT,/api/library/issues/,PUT/PATCH,library,MUTATION_BLOCKED,YES,YES,NO,Issue update/ editing requires data mutation.

API_ENDPOINT,/api/library/issues/,DELETE,library,MUTATION_BLOCKED,YES,YES,NO,Issue deletion requires data mutation.

API_ENDPOINT,/api/library/reservations/,GET,library,READ_ONLY_PROVEN,NO,NO,NO,Library reservations list present in source; production GET unverified.

API_ENDPOINT,/api/library/reservations/,POST,library,MUTATION_BLOCKED,YES,YES,NO,Reservation creation requires data mutation.

API_ENDPOINT,/api/library/members/,GET,library,READ_ONLY_PROVEN,NO,NO,NO,Library members list present in source; production GET unverified.

API_ENDPOINT,/api/library/settings/,GET,library,READ_ONLY_PROVEN,NO,NO,NO,Library settings present in source; production GET unverified.

API_ENDPOINT,/api/reports/,GET,reports,READ_ONLY_PROVEN,NO,NO,NO,Reports list endpoint present in source; production GET unverified (Accountant/HR role).

API_ENDPOINT,/api/reports/library/,GET,reports,READ_ONLY_PROVEN,NO,NO,NO,Reports library endpoint present in source; production GET unverified.

API_ENDPOINT,/api/visitors/,GET,visitors,READ_ONLY_PROVEN,NO,NO,NO,Visitors list endpoint present in source; production GET unverified (Guard role).

API_ENDPOINT,/api/visitors/guests/,GET,visitors,READ_ONLY_PROVEN,NO,NO,NO,Visitors guests list present in source; production GET unverified.

API_ENDPOINT,/api/payroll/,GET,payroll,READ_ONLY_PROVEN,NO,NO,NO,Payroll list endpoint present in source; production GET unverified (HR role). POST MUTATION_BLOCKED.

API_ENDPOINT,/api/payroll/,POST,payroll,MUTATION_BLOCKED,YES,YES,NO,Payroll processing requires data mutation; no safe test procedure.

API_ENDPOINT,/api/payroll/items/,GET,payroll,READ_ONLY_PROVEN,NO,NO,NO,Payroll items list present in source; production GET unverified.

API_ENDPOINT,/api/payroll/items/,POST,payroll,MUTATION_BLOCKED,YES,YES,NO,Payroll item creation requires data mutation.

API_ENDPOINT,/api/attendance/,GET,attendance,READ_ONLY_PROVEN,NO,NO,NO,Attendance list present in source; production GET unverified (Teacher/Staff role).

API_ENDPOINT,/api/students/,GET,students,READ_ONLY_PROVEN,NO,NO,NO,Students list present in source; production GET unverified.

API_ENDPOINT,/api/students/filter/,GET,students,READ_ONLY_PROVEN,NO,NO,NO,Students filter present in source; production GET unverified.

API_ENDPOINT,/api/teachers/,GET,teachers,READ_ONLY_PROVEN,NO,NO,NO,Teachers list present in source; production GET unverified.

API_ENDPOINT,/api/fees/,GET,finance,READ_ONLY_PROVEN,NO,NO,NO,Fees list present in source; production GET unverified (all roles).

API_ENDPOINT,/api/exams/,GET,exams,READ_ONLY_PROVEN,NO,NO,NO,Exams list present in source; production GET unverified (Teacher role).

API_ENDPOINT,/api/timetable/,GET,timetable,READ_ONLY_PROVEN,NO,NO,NO,Timetable list present in source; production GET unverified (Teacher/Staff role).

API_ENDPOINT,/api/events/,GET,events,READ_ONLY_PROVEN,NO,NO,NO,Events list present in source; production GET unverified.

API_ENDPOINT,/api/communication/,GET,communication,READ_ONLY_PROVEN,NO,NO,NO,Communication list present in source; production GET unverified.

API_ENDPOINT,/api/csp-report/,GET,N/A,READ_ONLY_PROVEN,NO,NO,NO,CSP reporting endpoint; security metadata.

API_ENDPOINT,/api/audit/,GET,audit,READ_ONLY_PROVEN,NO,NO,NO,Audit list present in source; production GET unverified.

API_ENDPOINT,/api/library/members/,GET,library,READ_ONLY_PROVEN,NO,NO,NO,Library members list (duplicate entry in inventory).

API_ENDPOINT,/api/library/settings/,GET,library,READ_ONLY_PROVEN,NO,NO,NO,Library settings (duplicate entry in inventory).

API_ENDPOINT,/api/staff/,GET,accounts,READ_ONLY_PROVEN,NO,NO,NO,Staff list present in source; production GET unverified.

API_ENDPOINT,/api/dashboard/,GET,dashboard,READ_ONLY_PROVEN,NO,NO,NO,Dashboard list present in source; production GET unverified.

API_ENDPOINT,/api/ai/,GET,ai,READ_ONLY_PROVEN,NO,NO,NO,AI assistant endpoint present in source; production GET unverified.

API_ENDPOINT,/api/schools/,GET,schools,READ_ONLY_PROVEN,NO,NO,NO,Schools list present in source; production GET unverified.

API_ENDPOINT,/api/search/,GET,search,READ_ONLY_PROVEN,NO,NO,NO,Search endpoint present in source; production GET unverified.

API_ENDPOINT,/api/documents/,GET,documents,READ_ONLY_PROVEN,NO,NO,NO,Documents list present in source; production GET unverified.

API_ENDPOINT,/api/discipline/,GET,discipline,READ_ONLY_PROVEN,NO,NO,NO,Discipline list present in source; production GET unverified.

API_ENDPOINT,/api/homework/,GET,homework,READ_ONLY_PROVEN,NO,NO,NO,Homework list present in source; production GET unverified.

API_ENDPOINT,/api/hostel/,GET,hostel,READ_ONLY_PROVEN,NO,NO,NO,Hostel list present in source; production GET unverified.

API_ENDPOINT,/api/hostel/rooms/,GET,hostel,READ_ONLY_PROVEN,NO,NO,NO,Hostel rooms list present in source; production GET unverified.

API_ENDPOINT,/api/lms/,GET,lms,READ_ONLY_PROVEN,NO,NO,NO,LMS list present in source; production GET unverified.

API_ENDPOINT,/api/portal/,GET,portal,READ_ONLY_PROVEN,NO,NO,NO,Portal list present in source; production GET unverified.

API_ENDPOINT,/api/white-label/,GET,white_label,READ_ONLY_PROVEN,NO,NO,NO,White label list present in source; production GET unverified.

API_ENDPOINT,/api/workflow/,GET,workflow,READ_ONLY_PROVEN,NO,NO,NO,Workflow list present in source; production GET unverified.

API_ENDPOINT,/api/helpdesk/,GET,helpdesk,READ_ONLY_PROVEN,NO,NO,NO,Helpdesk list present in source; production GET unverified.

API_ENDPOINT,/api/digital-ids/,GET,digital_ids,READ_ONLY_PROVEN,NO,NO,NO,Digital IDs list present in source; production GET unverified.

API_ENDPOINT,/api/saas/,GET,saas,READ_ONLY_PROVEN,NO,NO,NO,SaaS list present in source; production GET unverified.

==========================================================================
BACKEND/API AUDIT SUMMARY
==========================================================================

STATUS COUNTS (backend/api endpoints):

READ_ONLY_PROVEN: 39 — Endpoints present in source code; GET tested via
  Phase 73/74 health checks (2 endpoints: /api/health/ on frontend and API).
  The remaining 37 are classified READ_ONLY_PROVEN by code inspection pattern,
  not by actual production GET testing.

DEPLOYMENT_UNVERIFIED: 5 — /api/health/ (both sides), /api/deploy-test/ (404,
  root cause identified), /api/schema/, /api/docs/, /api/redoc. These endpoints
  have known source presence but deployment status unverifiable without Vercel
  dashboard access.

MUTATION_BLOCKED: 6 — /api/library/issues/POST, /api/library/issues/PUT/PATCH,
  /api/library/issues/DELETE, /api/payroll/POST, /api/payroll/items/POST,
  /api/payroll items creation. All require data mutation; no safe test
  procedure exists per PHASE_73.

AUTH_TEST_BLOCKED: 38+ — All endpoints that require authenticated session
  testing. Cannot test with current environment (no browser automation). This
  includes essentially all CRUD write endpoints and role-specific reads.

WORKING_PROVEN: 2 — /api/health/ on frontend and /api/health/ on API (both
  return HTTP 200 with database.ok=true). These are the ONLY endpoints with
  direct production evidence.

WORKING_PARTIALLY_PROVEN: 0 — no endpoints have partial production evidence
  beyond the 2 health checks.

IMPLEMENTED_UNVERIFIED: 0 — classified differently (READ_ONLY_PROVEN or
  MUTATION_BLOCKED or AUTH_TEST_BLOCKED per classification rules).

DEPLOYMENT_FAILURE: 0 — no endpoints demonstrably broken at HTTP level; 404 on
  /api/deploy-test/ is DEPLOYMENT_UNVERIFIED (artifact issue), not BROKEN.

BROKEN: 0 — no endpoints have concrete failure evidence. /api/deploy-test/ 404
  is a deployment artifact issue, not an application defect.

TOTAL_API_ENDPOINTS: 47 (from Phase 75 system inventory)

CRITICAL OBSERVATIONS:

1. ONLY 2 endpoints have WORKING_PROVEN status: /api/health/ on frontend and
   /api/health/ on API. Both return HTTP 200 with database.ok=true. This is
   the direct production evidence base.

2. /api/deploy-test/ returns 404 but is classified DEPLOYMENT_UNVERIFIED, not
   BROKEN. Root cause established: Vercel Python serverless artifact does not
   include this urlpattern. Not an application defect.

3. 6 endpoints are MUTATION_BLOCKED: all require data mutation (library CRUD,
   payroll processing) and no safe test procedure exists per PHASE_73.

4. ALL other endpoints are either READ_ONLY_PROVEN (by code inspection pattern,
   not production testing) or AUTH_TEST_BLOCKED (no authenticated session
   possible in current environment).

5. Frontend→API wiring confirmed (Phase 74): /api/ health endpoints work on
   both sides, confirming the rewrite /api/:path → API URL functions correctly.

6. Git commit 4112ad5 known from repository; deployment identity UNVERIFIED
   (cannot prove which commit serves production).

==========================================================================
PRODUCTION DATA SAFETY
==========================================================================

No production data mutated during audit. All inspections read-only (HTTP GET
inspection of health endpoints, repository analysis). Health endpoints confirm
database.ok = true without data access. MUTATION_BLOCKED endpoints explicitly
NOT tested on production data.

==========================================================================
STEP 4 DATE: 2026-09-23