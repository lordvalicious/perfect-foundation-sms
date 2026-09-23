PHASE 77 - STEP 19/20: TECHNICAL REMEDIATION PLAN
==================================================
Phase: 77
Date: 2026-09-24
Method: Proposed fixes for every OPEN item in PHASE_77_TECHNICAL_PROBLEM_REGISTER.csv + MISSING FEATURE REGISTER. FIXES ARE PROPOSED ONLY — NONE WERE EXECUTED (audit is READ-ONLY). Each item: target, fix approach, verification, safe-to-deploy-sandbox. Priority ordering by certification-blocking impact.

Columns:
item_id | sigma | priority | target | resolution_category | fix | verification | owner

======================================================================
REMEDIATION PLAN
======================================================================

R-01|TPR-001|P0|Production deploy-test 404|DEPLOYMENT|Redeploy API with DeployTestView bundled or replace subprocess-git view with a pure function reading build env var (e.g. VERCE_COMMIT) at app bootstrap; ensure urlpattern is registered under same include that serves /api/health/|curl https://perfect-foundation-api.vercel.app/api/deploy-test/ and https://perfect-foundation-sms.vercel.app/api/deploy-test/ -> expect 200 with commit+sha; reconcile with Vercel dashboard deployment list|Deployment owner + reviewer

R-02|TPR-002|P0|Deployment identity proof|DEPLOYMENT|After R-01, record the exact commit SHA served by deploy-test; match against GitHub release tag; store in PHASE_78 evidence|Compare deploy-test response sha vs git rev-parse HEAD; replicate in status report|Deployment owner

R-03|TPR-003|P0|Browser/auth production verification|ENVIRONMENT|Provision headless browser (Playwright/Cypress) or user-mediated session capability; grant read-only test account(s) per role; define CSRF/cookie session bootstrap|Run smoke suite for 18 roles; record each role's reachable modules vs guard list|Audit lead + infra

R-04|TPR-004|P1|nurse HealthRecords lockout|CODE|Add "nurse" to '/health-records' route guard role list in App.jsx (and nav visibility if role-filtered)|Unit test asserting guard contains nurse; open /health-records as nurse in browser when R-03 ready|Frontend dev

R-05|TPR-005|P1|Role consistency (org_admin, head_office, alumni, digital_ids)|CODE|Single source of truth: backend Role enum. Add org_admin + head_office to frontend guards/nav (or assign them existing admin-level guard). Decide alumni/digital_ids: either add real roles with permissions or remove phantom references|Greppable sync check across Role enum, App.jsx guards, nav; role->guard diff test|Architect + FE dev

R-06|TPR-008|P1|LMS quiz question delete unreachable|CODE|Split route: keep QuestionDetailView on questions/<pk>/; add QuizQuestionDeleteView at questions/<int:pk>/delete/ (name quiz-question-delete). Remove duplicate quizzes/<quiz_id>/questions/new/ block (lines 69–73 vs 79–83). Reverse-make unique names|manage.py check + URL reverse smoke; pytest_lms: add DELETE question integration test|LMS dev

R-07|TPR-009|P1|7 zero-test apps|TEST|Add test suites: discipline (incident CRUD, authz, scoping), documents (upload control, authz, protected media), health (record scope, nurse/teacher access), homework (submission lifecycle, grading), lms (course/lesson/quiz + R-06 route fix), search (scoping), transport (CRUD, assignment, GPS endpoint authz)|pytest per app green; coverage report shows >0 for each|QA + app owners

R-08|TPR-010|P1|Zero frontend tests|TEST|Add Vitest + React Testing Library (or Playwright E2E): route-guard matrix test (include TPR-004/TPR-005 guards), page render smoke for 58 pages, api.js client mock|CI runs FE suite; guard matrix green|FE QA

R-09|TPR-011|P1|Cross-origin auth between FE and API hosts|VERIFY|When R-03 ready, verify CSRF+cookie session through the /api/ rewrite (SameSite, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS). Confirm non-GET flows (e.g. create announcement) work via proxy|Browser: login, CRUD both hosts, inspect cookies|Backend+SRE

R-10|TPR-007|P2|hr/urls.py duplicate patterns|CLEANUP|Delete duplicate urlpattern blocks (78–82 vs 143–146; 138–139 vs 147–148) and duplicated imports (lines 3–66 vs 58–65); fix indentation lines 76–77|manage.py check; reverse smoke; pytest_hr green|HR dev

R-11|TPR-014|P2|reports URL-name collisions|CLEANUP|Rename duplicates (report-fee-defaulters, report-payroll-summary, report-subject-performance, report-timetable-* etc) with unique names; consolidate legacy+new namespaces; add catalog uniqueness test|Reverse-name uniqueness test passes; downstream links updated|Reports owner

R-12|TPR-006|P2|Dead PermissionGate components|CLEANUP|Either delete PermissionGate.jsx (recommended) with App.jsx RequireRoles as the single guard, or migrate RequireRoles into the component and wire it everywhere|grep shows single import path; guard behavior tests still green (R-08)|FE dev

R-13|TPR-013|P2|demoReports.js fallback|CLEANUP|Remove DEMO_REPORTS or guard behind explicit DEV flag; API failure must surface error rather than demo data|Inspect ReportsPage error path; FE test for API-failure disables fallback|FE dev

R-14|TPR-012|P3|Stale pytest teacher harness|DOCS|Repair/remove pytest script referencing apps.teacher|Run harness -> green; remove from CI if obsolete|QA

R-15|TPR-015|P3|hr/urls.py formatting/duplicate imports|CLEANUP|Fold into R-10; dedupe imports + reindent|Lint + manage.py check|HR dev

R-16|TPR-016|P2|Role integrity (TextChoices vs DB)|ARCH|Decision: either add DB-level enforcement (role FK/constraint) or keep enum + comprehensive tests asserting Role usage; remove duplicate TransferManager definition|Existing 252 account tests still green + new role-usage test|Architect

R-17|TPR-017|P2|Documents ownership mismatch|ARCH|Clarify: relocate document endpoints under students/hr or add model to documents app; document decision in architecture note|Doc updated; no duplicate data paths|Architect

R-18|MISS-008|P1|Cron auto-scheduling not wired|DEPLOYMENT|Add Vercel Cron (vercel.json "crons" snippet) or external scheduler for FeeReminder/AbsenceAlert/ProcessNotifications/LateFee/WeeklyReport cron views; keep manual dry-run for audit trial|Cron fires in sandbox/prod, auditable runs recorded|SRE + product

R-19|MISS-006|P2|Admin/tooling UI gaps|SCOPE|Acceptable via Django admin + API for password-reset, role-permission CRUD, run-migrations, feature-flag admin; add documentation OR build minimal UI|Outcome decision logged|Product owner

R-20|MUTATION_CERT_26|P0|26 mutation-blocked modules production certification|PROCESS|Establish an authorized mutation sandbox (staging copy or dedicated test school) to exercise: library issue/return/reserve, payroll process, payments, attendance, marks, report-card publish, health records, visitor check-in, documents upload, inventory ops, transfers/graduation. Sequence per module after R-01/R-03|Per-module mutation tests PASS in sandbox, then replicate on prod read path|Audit lead + product + infra

R-21|MISS-003|P2|alumni/digital_ids phantom roles|ARCH (with R-05)|Decide real roles vs removal; align FE nav + backend|Role enum + guardian consistency test|Architect

======================================================================
REMEDIATION PLAN SUMMARY
======================================================================
P0 (certification-blocking): R-01 (deploy-test), R-02 (identity), R-03 (browser/auth), R-20 (mutation sandbox)
P1 (functional/correctness): R-04 (nurse), R-05 (role sync), R-06 (LMS delete), R-09 (cross-origin), R-18 (cron)
P1 (test quality): R-07 (7 apps), R-08 (frontend)
P2 (quality/cleanup): R-10..R-13, R-16, R-17, R-19, R-21
P3 (docs/form): R-14, R-15
TOTAL_PROPOSED_ACTIONS: 21
EXECUTED: 0 (awaiting authorization — audit READ-ONLY)

======================================================================
STEP 19/20 COMPLETE - 2026-09-24
======================================================================