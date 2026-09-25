PHASE 97 STAGE B GAP-RESOLUTION / READINESS REPORT
==================================================

STATUS: Read-only audit and evidence report. No source modification, no E2E execution,
no session creation, no implementation. STOP after report; wait for separate owner
approval before any implementation phase.

(UPDATED with backend authorization audit findings)

==========================================================================
1. LIBRARY_ROUTE_STATUS
==========================================================================
Status: NOT_ESTABLISHED
Evidence:
  - frontend/src/App.jsx contains NO <Route path="/library"> definition
  - Nav array at line ~395 shows LIBRARIAN with roles: ["library"]
  - No /library Route definition exists in App.jsx
  - No /library RequireRoles gate exists

Future action (read-only prerequisite):
  - Investigate existing frontend library components/pages (read-only)
  - Investigate backend library endpoints (read-only)
  - Investigate backend permission classes for library (read-only)
  - Investigate existing library URL patterns (read-only)
  - Role/scope enforcement for library resources (read-only)
  - Do NOT infer missing permissions

E2E Scope: Test LIBRARIAN navigation visibility only.
Do not create route-access test for /library until real route + authorization
contract established.

==========================================================================
2. LIBRARY_BACKEND_STATUS
==========================================================================
Status: CATALOG_EXISTS / ROLE_PERMISSIONS_UNKNOWN
Evidence (read-only audit of backend/apps/accounts/):

=== Permission Catalog (models.py line 1659-1668) ===
The Permission model includes these library codenames:
  - library.book.view, library.book.create, library.book.edit, library.book.delete
  - library.issue.view, library.issue.create, library.issue.return, library.issue.overdue
  - library.export
These exist in the catalog and are system-generated (default permissions).

=== ROLE_GRANTS (demo_seed/part1_foundation.py line 48-50) ===
Only "librarian" receives library permissions via prefixes ["library."]:
  - Grants every catalog permission matching "library." prefix to RolePermission
  - Other roles with library-relevant prefixes: NONE
  - "counsellor": NO entry in ROLE_GRANTS
  - "nurse": NO entry in ROLE_GRANTS
  - "administrative_officer": NO entry in ROLE_GRANTS

=== RolePermission model (models.py line 1782-1881) ===
Links role + permission + institution with UniqueConstraint:
  - role = CharField(choices=Role.choices)
  - permission = ForeignKey(Permission)
  - institution = ForeignKey(School)
  - UniqueConstraint on (role, permission, institution)
This is the mechanism that assigns permissions to roles per institution.
NO direct evidence of existing RolePermission rows for the five roles in
production database (read-only; data not accessible in this preflight).

=== ROLE_RANK (models.py line 36-57) ===
All five roles have numeric rankings:
  - COUNSELLOR: 42, ADMINISTRATIVE_OFFICER: 38, LIBRARIAN: 35, GUARD: 30, NURSE: 28
Hierarchy established but does not automatically grant permissions.

=== DRF Permission Classes (permissions.py) ===
- IsStaffRole: includes ALL roles (super_admin → staff) — the five roles ARE included
- IsNurseRole: nurse + admin-tier roles (super_admin through academic)
- IsLibrarianRole: librarian + teacher + admin-tier roles

=== permissions_new.py ===
No five-role-specific permission classes. Only student, teacher, staff, admission,
attendance, exam, finance, HR, settings, user/role/permission management, report,
system classes exist.

=== Backend Authorization STATUS SUMMARY ===
  - Permission CATALOG: EXISTS (library codenames defined in system)
  - ROLE_GRANTS for five roles: PARTIAL — only librarian has "library." prefix
  - ROLE_PERMISSION assignments: UNKNOWN (no production data accessible)
  - Five roles' specific library permissions: NOT ESTABLISHED

==========================================================================
3. FIVE_ROLE_SESSION_STRATEGY
==========================================================================
Chosen: OPTION A — runtime login through POST /api/auth/login/ for each of
the five roles.

Requirements (binding):
  - Credentials remain outside the repository
  - Use existing env-driven session architecture (P43_<ROLE>_SESSIONID,
    P43_SESSIONS_DIR fallback in session.js)
  - Do NOT create fabricated session files
  - Do NOT commit passwords, cookies, session IDs, or secrets
  - Acquire sessions only during authorized E2E execution
  - Do NOT mutate production data merely to establish sessions

Not chosen: Option B (temp Netscape session files in P43_SESSIONS_DIR) —
viable but higher-friction; no scripts provided in this preflight.

==========================================================================
4. BACKEND AUTHORIZATION STATUS (per-module, read-only)
==========================================================================
All statuses derive from source code audit. No production database queries.

Module              | Catalog | ROLE_GRANTS | ROLE_PERMISSION | Gate Decision
COUNSELLOR          | EXISTS  | ABSENT      | UNKNOWN         | NOT_ESTABLISHED
GUARD               | EXISTS  | present ("attendance.view","student.view") | UNKNOWN | PARTIAL
NURSE               | EXISTS  | ABSENT      | UNKNOWN         | NOT_ESTABLISHED
ADMINISTRATIVE_OFFICER | EXISTS | ABSENT     | UNKNOWN         | NOT_ESTABLISHED
LIBRARIAN           | EXISTS  | present ("library.") | UNKNOWN | PARTIAL (librarian only)

PROVEN from source:
  - Permission catalog includes library codenames (book, issue, export)
  - ROLE_GRANTS grants library permissions to "librarian" via "library." prefix
  - ROLE_RANK hierarchy established for all five roles
  - Role enum includes all five roles (COUNSELLOR through NURSE)
  - User.get_permissions() mechanism combines RolePermission | allow - deny
  - Frontend navigation establishes module visibility per role
  - /helpdesk route-level RequireRoles includes all five roles

NOT ESTABLISHED from source:
  - Actual RolePermission assignments for the five roles in production
  - Whether librarian's "library." grants extend to all library codenames or
    only library.book.*
  - Whether counsellor, nurse, administrative_officer have any library
    permissions (ROLE_GRANTS explicitly absent)
  - Backend API endpoint permission classes for helpdesk/visitors/health-records
  - Frontend primary_role/has_any_role/ROLE_ACCESS references (grep = empty)
  - /library route in App.jsx (absent)
  - /library Route-level RequireRoles gate (not established)

==========================================================================
5. WHAT IS PROVEN
==========================================================================
- Five production E2E accounts exist (counsellor, guard, nurse,
  administrative_officer, librarian) in Default Institution, campus 7,
  department E2E, verified via auth login + GET /api/auth/me/
- Frontend navigation array establishes visible modules per role:
  COUNSELLOR→Helpdesk, GUARD→Helpdesk+Visitors, NURSE→Health Records,
  ADMINISTRATIVE_OFFICER→Helpdesk, LIBRARIAN→Library
- /helpdesk route-level RequireRoles includes all five roles
- Repo state: HEAD == origin/master == cd00325; tracked clean; 0028 absent
- Session strategy Option A (runtime login) compatible with existing harness
- Permission catalog includes library codenames (book, issue, export)
- ROLE_GRANTS grants library permissions to "librarian" only
- No destructive ops in e2e suite; five accounts active and verified

==========================================================================
6. WHAT REMAINS UNKNOWN
==========================================================================
- Actual RolePermission assignments for the five roles in production database
- Whether librarian's "library." grants cover all library codenames or only book.*
- Whether counsellor, nurse, administrative_officer have any library permissions
- /library route existence and authorization for LIBRARIAN
- Backend API permission classes for helpdesk/visitors/health-records/library
- Frontend role-based access pattern references (primary_role etc. = empty grep)
- Session material: no sa_<role>.txt files or P43_<ROLE>_SESSIONID env vars exist
- Safe test scope for LIBRARIAN beyond nav visibility

==========================================================================
7. WHAT IS SAFE TO IMPLEMENT NEXT (read-only, pre-implementation)
==========================================================================
Per the gate: "READY FOR IMPLEMENTATION REVIEW" requires owner approval.
The following CAN be prepared as deliverables (untracked, no secrets, no source change):

  a) Updated PHASE_97_STAGE_B_PREFLIGHT.md with gap-resolution findings
  b) Updated PHASE_97_STAGE_B_PREFLIGHT_MATRIX.csv with LIBRARY_ROUTE_STATUS=
     NOT_ESTABLISHED and updated BACKEND_AUTHORIZATION_STATUS matrix
  c) Updated PHASE_97_STAGE_B_MACHINE_SUMMARY.txt reflecting Option A session
     strategy and all authorization statuses
  d) Updated PHASE_97_STAGE_B_GAP_RESOLUTION_REPORT.md with full backend audit
  e) Five-role test scope outline (nav-visibility only for LIBRARIAN; core
     identity/role/scope tests for the other 4 roles where source-supported)
  f) Session acquisition design doc (Option A: runtime login via env-driven
     P43_<ROLE>_SESSIONID, credentials outside repo)

NOT safe to implement without separate owner approval:
  - Any source modification (adding /library route, modifying RequireRoles,
    modifying backend permissions, modifying ROLE_GRANTS)
  - Any E2E test creation beyond nav-visibility scope
  - Any session file creation
  - Any deployment or push

==========================================================================
DELIVERABLES (untracked, no secrets, STOP pending owner approval)
------------------------------------------------------------------
  PHASE_97_STAGE_B_PREFLIGHT.md              (updated with gap-resolution)
  PHASE_97_STAGE_B_PREFLIGHT_MATRIX.csv      (updated matrix)
  PHASE_97_STAGE_B_MACHINE_SUMMARY.txt       (updated summary)
  PHASE_97_STAGE_B_GAP_RESOLUTION_REPORT.md   (this updated report)

  STOP: Do NOT implement, modify source, create sessions, or execute E2E.
  Wait for separate owner approval before implementation phase.