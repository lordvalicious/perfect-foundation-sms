PHASE 97 — STAGE C — AUTHORIZATION CONTRACT + FIVE-ROLE E2E
                                 IMPLEMENTATION PREFLIGHT
============================================================================

MODE: STAGE A PREFLIGHT ONLY
NO SOURCE CHANGES | NO TEST FILE CHANGES | NO DATABASE MUTATIONS
NO PRODUCTION API MUTATIONS | NO SESSION CREATION | NO DEPLOYMENT
NO COMMIT | NO PUSH | NO MIGRATION CREATION/APPLICATION
STOP FOR SEPARATE OWNER IMPLEMENTATION APPROVAL

============================================================================
1. REPOSITORY / BASELINE PREFLIGHT (Step 1)
============================================================================

- HEAD: cd00325 test(e2e): wire five-role session lookup for Phase 96.8 roles
- BRANCH: master (origin/master == cd00325 after git fetch)
- TRACKED WORKTREE: clean (only untracked phase deliverables)
  ?? PHASE_96_3_DEPLOYMENT_PREREQUISITE_AUDIT.md
  ?? PHASE_96_3_MACHINE_SUMMARY.txt
  ?? PHASE_96_3_READINESS_MATRIX.csv
  ?? PHASE_96_4_DEPLOYMENT_READINESS.md
  ?? PHASE_96_4_MACHINE_SUMMARY.txt
  ?? PHASE_96_4_MIGRATION_LINEAGE_AUDIT.md
  ?? PHASE_96_4_READINESS_MATRIX.csv
  ?? PHASE_96_5_DEPLOYMENT_READINESS.md
  ?? PHASE_96_5_MACHINE_SUMMARY.txt
  ?? PHASE_96_5_READINESS_MATRIX.csv
  ?? PHASE_96_5_VERCEL_BUILD_DIAGNOSIS.md
  ?? PHASE_96_6_EXECUTION_MATRIX.csv
  ?? PHASE_96_6_EXECUTION_RESULT.md
  ?? PHASE_96_6_MACHINE_SUMMARY.txt
  ?? PHASE_96_6_PREFLIGHT.md
  ?? PHASE_96_6_READINESS_MATRIX.csv
  ?? PHASE_96_7_EXECUTION_MATRIX.csv
  ?? PHASE_96_7_EXECUTION_RESULT.md
  ?? PHASE_96_7_MACHINE_SUMMARY.txt
  ?? PHASE_96_7_STAGE_A_VERCEL_CONFIGURATION_RECONCILIATION.md
  ?? PHASE_96_8_STAGE_A_ACCOUNT_MATRIX.csv
  ?? PHASE_96_8_STAGE_A_ACCOUNT_READINESS.md
  ?? PHASE_96_8_STAGE_A_MACHINE_SUMMARY.txt
  ?? PHASE_96_8_STAGE_B_EXECUTION_MATRIX.csv
  ?? PHASE_96_8_STAGE_B_EXECUTION_RESULT.md
  ?? PHASE_96_8_STAGE_B_MACHINE_SUMMARY.txt
  ?? PHASE_96_9_STAGE_A_MACHINE_SUMMARY.txt
  ?? PHASE_96_9_STAGE_A_PROVISIONING_DESIGN.md
  ?? PHASE_96_9_STAGE_A_PROVISIONING_MATRIX.csv
  ?? PHASE_96_9_STAGE_B_MACHINE_SUMMARY.txt
  ?? PHASE_96_9_STAGE_B_PROVISIONING_MATRIX.csv
  ?? PHASE_96_9_STAGE_B_PROVISIONING_RESULT.md
  ?? PHASE_97_STAGE_A_E2E_READINESS.md
  ?? PHASE_97_STAGE_A_E2E_READINESS_MATRIX.csv
  ?? PHASE_97_STAGE_A_MACHINE_SUMMARY.txt
  ?? PHASE_97_STAGE_B_GAP_RESOLUTION_REPORT.md
  ?? PHASE_97_STAGE_B_MACHINE_SUMMARY.txt
  ?? PHASE_97_STAGE_B_PREFLIGHT.md
  ?? PHASE_97_STAGE_B_PREFLIGHT_MATRIX.csv
  ?? PHASE_97_STAGE_B_GAP_RESOLUTION_REPORT.md
  ?? PHASE_97_STAGE_C_PREFLIGHT.md   <-- new
  ?? PHASE_97_STAGE_C_AUTHORIZATION_MATRIX.csv   <-- new
  ?? PHASE_97_STAGE_C_MACHINE_SUMMARY.txt   <-- new
  ?? PHASE_97_STAGE_C_GAP_REPORT.md   <-- new
- PROTECTED FIVE-ROLE BASELINE: 7357c18d1e4352bdce41b7de23c36eead4b66681
  is ancestor of HEAD (13 commits)
  Protected source diff vs baseline: EMPTY on
  backend/apps/accounts, backend/apps/schools, backend/apps/authentication
- FRONTEND DEPLOYMENT: https://perfect-foundation-sms.vercel.app
  vercel.json rewrites: /api/:path(.*) →
  https://perfect-foundation-api.vercel.app/api/:path;
  / → /index.html
- CSP: connect-src 'self' https://perfect-foundation-api.vercel.app
- BACKEND DEPLOYMENT: https://perfect-foundation-api.vercel.app
  deploy_version 63-test-3
  health: {"status":"ok","database":{"ok":true,"error":null}}
- E2E HARNESS: playwright.config.js baseURL defaults to
  https://perfect-foundation-sms.vercel.app
  Projects: desktop, tablet, mobile
  session.js: ROLE_FILES maps all five roles;
  getSessionId() reads P43_<ROLE>_SESSIONID env or
  P43_SESSIONS_DIR Netscape files
  .env.example documents P43_<ROLE>_SESSIONID names only
  All env values populated outside the repository
- TEST SUITE: 10 spec files, 54 direct test() calls
  v1-role coverage: SUPER_ADMIN/ADMIN/TEACHER/STUDENT/STAFF
  Zero five-role specs for COUNSELLOR/GUARD/NURSE/
  ADMINISTRATIVE_OFFICER/LIBRARIAN

============================================================================
2. SOURCE OF TRUTH (Step 2-3)
============================================================================

Frontend authorization source: frontend/src/App.jsx
All role expectations traced from navigation array + route-level
RequireRoles gates. "Do not invent permissions. If the source code
does not establish an expectation, mark it NOT_ESTABLISHED."

=== Navigation array (visibleNavGroups) ===
- COUNSELLOR: Helpdesk
- GUARD: Helpdesk + Visitors
- NURSE: Health Records
- ADMINISTRATIVE_OFFICER: Helpdesk
- LIBRARIAN: Library (nav-only; no /library route)

=== Route-level RequireRoles gates (App.jsx lines 1302-1346) ===
/health-records: roles=["super_admin","admin","principal","vice_principal","campus_admin","teacher","nurse","staff"]
  -> NURSE only (staff also). All other five roles BLOCKED.

/helpdesk: roles=["super_admin","admin","principal","vice_principal","campus_admin","academic","hr","receptionist","guard","teacher","counsellor","administrative_officer","staff"]
  -> ALL 5 roles INCLUDED. PROVEN.

/visitors: roles=["super_admin","admin","principal","vice_principal","campus_admin","academic","hr","receptionist","guard","staff"]
  -> GUARD only (staff also). Counsellor, administrative_officer, nurse, librarian BLOCKED.

/digital-ids: roles=["super_admin","admin","principal","vice_principal","campus_admin","academic","hr","receptionist","staff"]
  -> NONE of the 5 roles included. All BLOCKED.

/library: NO route definition in App.jsx. Navigation shows it for
  LIBRARIAN but source is absent. NOT_ESTABLISHED.

=== Established CORE expectations (from Phase 96.9 + models.py) ===
All five roles have:
- Role enum entry (COUNSELLOR/ADMINISTRATIVE_OFFICER/LIBRARIAN/GUARD/NURSE)
- ROLE_RANK ranking
- primary_role property
- DESIGNATION_ROLE_MAP
- Auth-verified via POST /api/auth/login/ -> GET /api/auth/me/ (HTTP 200)

=== NOT ESTABLISHED from source ===
- /library route-level authorization for LIBRARIAN (route absent)
- /visitors access for counsellor, administrative_officer, nurse, librarian
- /health-records access for counsellor, administrative_officer, guard, librarian
- /digital-ids access for any of the 5 roles
- Backend API permission classes for helpdesk/visitors/health-records/library
- ROLE_GRANTS for counsellor, nurse, administrative_officer in demo_seed
- Frontend primary_role/has_any_role/ROLE_ACCESS references (grep = empty)

============================================================================
3. BACKEND AUTHORIZATION AUDIT (Step 4)
============================================================================

Read-only audit of backend/apps/accounts/. No production database queries.

=== Permission Catalog (models.py line 1439-1780) ===
Codename naming convention: <resource>.<action>
Library codenames defined:
  library.book.view, library.book.create, library.book.edit, library.book.delete
  library.issue.view, library.issue.create, library.issue.return, library.issue.overdue
  library.export
All are system permissions (is_system=True). Catalog exists but may be empty
in production if not seeded.

=== ROLE_GRANTS (demo_seed/part1_foundation.py line 23-67) ===
ROLE_GRANTS = {
  "super_admin": ALL, "admin": ALL, "org_admin": ALL, "head_office": ALL,
  "academic": ALL, "campus_admin": ALL, "principal": [...],
  "vice_principal": [...],
  "accountant": ["student.view","finance.","payroll.","report."],
  "hr": ["student.view","staff.","attendance.","hr.","payroll.","communication.","report.","user.view"],
  "receptionist": ["student.view","admission.","communication.","attendance.view"],
  "librarian": ["library.","report.view","student.view"],     <-- only role with library grants
  "guard": ["attendance.view","student.view"],
  "teacher": ["student.view","teacher.","attendance.","exam.result.","exam.view","lms.","communication.","report.view"],
  "staff": ["student.view","attendance.view","report.view","communication."],
  "parent": ["student.view","communication.view","report.view"],
  "student": ["student.view","lms.view","communication.view","report.view"],
}
CRITICAL: ROLE_GRANTS are seed definitions. They do NOT prove production
RolePermission assignments. If production RolePermission data is unavailable:
PRODUCTION_ROLEPERMISSION_ASSIGNMENTS = UNKNOWN

=== RolePermission model (models.py line 1782-1881) ===
Links: role + permission + institution with UniqueConstraint:
  - role = CharField(choices=Role.choices)
  - permission = ForeignKey(Permission)
  - institution = ForeignKey(School)
  - Constraint: UniqueConstraint(fields=["role","permission","institution"],
    name="unique_role_permission_per_institution")
This is the mechanism that assigns permissions to roles per institution.
NO direct evidence of existing RolePermission rows for the five roles in
production database (read-only; data not accessible in this preflight).

=== User.get_permissions() (models.py line 276-329) ===
Combines:
  - Role-based perms (via RolePermission for role_names)
  - allow_perms (via UserPermission with effect="allow", excludes expired)
  - deny_perms (via UserPermission with effect="deny", excludes expired)
  - Formula: (role_perms | allow_perms) - deny_perms
  - superuser = all Permission codenames

=== DRF Permission Classes (permissions.py) ===
- IsStaffRole: includes ALL roles (super_admin → staff) — the five roles ARE included
- IsNurseRole: nurse + admin-tier roles (super_admin through academic)
- IsLibrarianRole: librarian + teacher + admin-tier roles
- IsAccountantRole: admin-tier + accountant, hr
- IsTeacherRole: admin-tier + teacher
No five-role-specific permission classes in permissions_new.py.

=== Backend Authorization STATUS SUMMARY ===
  - Permission CATALOG: EXISTS (library codenames defined in system default)
  - ROLE_GRANTS for five roles: PARTIAL — only librarian has "library." prefix
  - ROLE_PERMISSION assignments: UNKNOWN (no production data accessible)
  - Five roles' specific library permissions: NOT_ESTABLISHED
  - Five roles' specific helpdesk/visitors/health-records permissions: NOT_ESTABLISHED

============================================================================
4. FIVE-ROLE AUTHORIZATION MATRIX (Step 5)
============================================================================

ROLE × MODULE × NAV × ROUTE_EXISTS × FRONTEND_GATE × BACKEND_PERMISSION ×
PRODUCTION_ASSIGNMENT × EXPECTATION_STATUS

COUNSELLOR / helpdesk:    NAV=YES ROUTE=YES GATE=PROVEN(B) BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
COUNSELLOR / visitors:    NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
COUNSELLOR / health-records: NAV=NO ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
COUNSELLOR / digital-ids:  NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
COUNSELLOR / library:     NAV=NO  ROUTE=NO  GATE=NOT_APPLICABLE BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED

GUARD / helpdesk:    NAV=YES ROUTE=YES GATE=PROVEN(B) BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
GUARD / visitors:    NAV=YES ROUTE=YES GATE=PROVEN(B) BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
GUARD / health-records: NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
GUARD / digital-ids:  NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
GUARD / library:     NAV=NO  ROUTE=NO  GATE=NOT_APPLICABLE BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED

NURSE / helpdesk:    NAV=YES ROUTE=YES GATE=PROVEN(B) BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
NURSE / visitors:    NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
NURSE / health-records: NAV=YES ROUTE=YES GATE=PROVEN(B) BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
NURSE / digital-ids:  NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
NURSE / library:     NAV=NO  ROUTE=NO  GATE=NOT_APPLICABLE BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED

ADMINISTRATIVE_OFFICER / helpdesk:    NAV=YES ROUTE=YES GATE=PROVEN(B) BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
ADMINISTRATIVE_OFFICER / visitors:    NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
ADMINISTRATIVE_OFFICER / health-records: NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
ADMINISTRATIVE_OFFICER / digital-ids:  NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
ADMINISTRATIVE_OFFICER / library:     NAV=NO  ROUTE=NO  GATE=NOT_APPLICABLE BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED

LIBRARIAN / helpdesk:    NAV=YES ROUTE=YES GATE=PROVEN(B) BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
LIBRARIAN / visitors:    NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
LIBRARIAN / health-records: NAV=YES ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
LIBRARIAN / digital-ids:  NAV=NO  ROUTE=YES GATE=PROVEN_DENY BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED
LIBRARIAN / library:     NAV=YES ROUTE=NO  GATE=NOT_APPLICABLE BKEND=UNKNOWN ASSIGN=UNKNOWN EXP=NOT_ESTABLISHED

Key:
- NAV: whether navigation array shows role for module (YES/NO)
- ROUTE_EXISTS: whether route exists in App.jsx (YES/NO)
- FRONTEND_GATE: PROVEN=role included in RequireRoles; PROVEN_DENY=role explicitly excluded; NOT_APPLICABLE=no route
- BACKEND_PERMISSION: PROVEN/ PROVEN_DENY/ NOT_ESTABLISHED/ UNKNOWN per backend source
- PRODUCTION_ASSIGNMENT: PROVEN/ PROVEN_DENY/ NOT_ESTABLISHED/ UNKNOWN (depends on production RolePermission data)
- EXPECTATION_STATUS: what E2E tests can safely assert (PROVEN/ NOT_ESTABLISHED/ UNKNOWN/ NOT_APPLICABLE)

============================================================================
5. E2E EXPECTATION BOUNDARY (Step 6-7)
============================================================================

SAFE TO ESTABLISH ONLY WHERE THE SOURCE CONTRACT IS PROVEN.

Minimum expectations that may be proposed:
- Authentication: POST /api/auth/login/ per role (env-driven, credentials outside repo)
- Identity: username, primary_role confirmation via GET /api/auth/me/
- Role: primary_role property matches role name
- Navigation visibility: nav array establishes COUNSELLOR→Helpdesk, GUARD→Helpdesk+Visitors, NURSE→Health Records, ADMINISTRATIVE_OFFICER→Helpdesk, LIBRARIAN→Library
- /helpdesk route-access: PROVEN for all five roles (frontend gate confirmed)
- /visitors route-access: PROVEN for GUARD only; PROVEN_DENY for the other four
- /health-records route-access: PROVEN for NURSE only; PROVEN_DENY for the other four
- /digital-ids route-access: PROVEN_DENY for all five roles

NOT SAFE to establish:
- /library route-access for LIBRARIAN (route absent in App.jsx)
- Any backend permission expectations without production RolePermission evidence
- Any production RolePermission assignment assertions
- Scope behavior beyond what source explicitly establishes
- LIBRARIAN /library navigation + route test combination (nav visible but route absent)

SESSION STRATEGY (Step 8):
SESSION_STRATEGY = OPTION_A

Runtime login through POST /api/auth/login/ for each of the five roles.
Credentials must remain outside the repository.
Use existing env-driven session architecture (P43_<ROLE>_SESSIONID,
P43_SESSIONS_DIR fallback in session.js).
Do NOT create sessions or perform login during this preflight.
Do NOT commit passwords, cookies, session IDs, or secrets.

============================================================================
6. MIGRATION / SOURCE SAFETY (Step 9)
============================================================================

Carry forward unchanged:
- MIGRATION_0028_CLASSIFICATION = INSUFFICIENT_EVIDENCE
- MIGRATION_GATE = UNKNOWN
- No migration 0028 is to be created
- No migration is to be run
- Protected five-role/account/school authorization baseline remains unchanged
- Phase 84 baseline 7357c18 is ancestor of HEAD (cd00325)
- Protected source diff vs baseline: EMPTY

============================================================================
7. FINAL GATE (Step 10-12)
============================================================================

PHASE_97_STAGE_C_PREFLIGHT = COMPLETE

FINAL_GATE = UNKNOWN
(requiring owner implementation review)

RATIONALE: Source establishes partial authorization expectations for 4 of 5
roles via frontend navigation + /helpdesk gate. One critical gap:
/library route absent for LIBRARIAN, making that expectation NOT_ESTABLISHED.
Backend permission classes and production RolePermission assignments are
UNKNOWN (no production database access in preflight). Session strategy
Option A is documented but not yet executed. No five-role E2E specs exist.

Explicit STOP condition:
Do NOT implement, modify source, create sessions, execute E2E, commit,
or push without separate owner approval.

============================================================================
8. UNAUTHORIZED / FABRICATED ITEMS (Explicitly excluded)
============================================================================

The following MUST NOT be in any Stage C deliverable:
- Fabricated /library route or RequireRoles gate
- Invented backend permission expectations
- Production RolePermission assignment assertions
- Session creation or credential logging
- E2E test execution
- Source code modifications
- Deployment or push
- Commit or push operations
- Database mutations
- Migration creation or application

============================================================================
9. DELIVERABLES (untracked, no secrets)
============================================================================

1. PHASE_97_STAGE_C_PREFLIGHT.md             (this file)
2. PHASE_97_STAGE_C_AUTHORIZATION_MATRIX.csv
3. PHASE_97_STAGE_C_MACHINE_SUMMARY.txt
4. PHASE_97_STAGE_C_GAP_REPORT.md

STOP: Do NOT implement, modify source, create sessions, or execute E2E.
Wait for separate owner approval.