PHASE 97 — STAGE C — GAP REPORT
============================================================================

STATUS: Read-only audit and evidence report. No source modification, no E2E execution,
no session creation, no implementation. STOP after report; wait for separate owner
approval before any implementation phase.

============================================================================
1. /LIBRARY ROUTE GAP
============================================================================

Status: NOT_ESTABLISHED

Evidence:
  - frontend/src/App.jsx contains NO <Route path="/library"> definition
  - Nav array at line ~395 shows LIBRARIAN with roles: ["library"]
  - No /library Route definition exists in App.jsx
  - No /library RequireRoles gate exists
  - LIBRARIAN navigation entry exists but route is absent

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

============================================================================
2. BACKEND AUTHORIZATION UNCERTAINTY
============================================================================

Status: UNRESOLVED

The following remain uncertain because production database RolePermission
assignments are not accessible in this preflight:

  a) Whether any RolePermission rows exist for the five roles (counsellor,
     guard, nurse, administrative_officer, librarian) in the production
     database. The RolePermission model (role + permission + institution,
     unique constraint) is the mechanism, but actual assignments are
     unverified.

  b) Whether librarian's ROLE_GRANTS "library." prefix grants cover all
     library codenames (library.book.view, library.book.create, library.book.edit,
     library.book.delete, library.issue.view, library.issue.create, library.issue.return,
     library.issue.overdue, library.export) or only library.book.*.

  c) Whether counsellor, nurse, or administrative_officer have any library
     permissions. ROLE_GRANTS has no entries for these three roles.

  c) Whether helpdesk, visitors, or health-records backend permission
     classes explicitly establish access for any of the five roles beyond
     the frontend RequireRoles gate.

All such items are classified PRODUCTION_ASSIGNMENT = UNKNOWN.

============================================================================
3. PRODUCTION ROLEPERMISSION ASSIGNMENTS
============================================================================

Status: UNKNOWN

The RolePermission model assigns permissions to roles per institution via:
  - role = CharField(choices=Role.choices)
  - permission = ForeignKey(Permission)
  - institution = ForeignKey(School)
  - UniqueConstraint on (role, permission, institution)

NO direct evidence of existing RolePermission rows for the five roles in
production database is accessible in this preflight. Seed definitions
(ROLE_GRANTS in demo_seed/part1_foundation.py) are not proof of production
authorization.

Classification: PRODUCTION_ROLEPERMISSION_ASSIGNMENTS = UNKNOWN

============================================================================
4. FRONTEND ROLE-BASED ACCESS PATTERNS
============================================================================

Status: NOT_ESTABLISHED

Grepping frontend/src for primary_role, has_any_role, roles.includes,
ROLE_ACCESS returns NO matches for the five roles (COUNSELLOR, GUARD,
NURSE, ADMINISTRATIVE_OFFICER, LIBRARIAN). No frontend role-based access
JavaScript patterns establish runtime permission checks for these roles.

============================================================================
5. SESSION MATERIAL
============================================================================

Status: MISSING (per Phase 97 Stage A finding F2)

No sa_<role>.txt session files exist in runtime directory.
No P43_<ROLE>_SESSIONID environment variables are set.
Five production E2E accounts exist and are auth-verified, but no runtime
session material has been configured or acquired yet.
Session strategy Option A (runtime login via env-driven mechanism) is
documented but not yet executed.

============================================================================
6. SUMMARY OF EVIDENCE GAPS
============================================================================

The following evidence gaps prevent a fully proven authorization contract:

  1. /library route for LIBRARIAN (route absent; nav-only)
  2. Production RolePermission assignments (data not accessible)
  3. Backend API permission classes for helpdesk/visitors/health-records/library
  4. ROLE_GRANTS gaps for counsellor, nurse, administrative_officer
  5. Frontend role-based access pattern references (empty grep)
  5. Session material not yet configured

No item may be fabricated or assumed. All must remain classified as
NOT_ESTABLISHED or UNKNOWN until owner-authorized investigation proves
otherwise.

============================================================================
6. DELIVERABLES
============================================================================

1. PHASE_97_STAGE_C_PREFLIGHT.md              (this file's content source)
2. PHASE_97_STAGE_C_AUTHORIZATION_MATRIX.csv
3. PHASE_97_STAGE_C_MACHINE_SUMMARY.txt
4. PHASE_97_STAGE_C_GAP_REPORT.md

============================================================================
7. FINAL STOP CONDITION
============================================================================

STOP: Do NOT implement, modify source, create sessions, or execute E2E.
Wait for separate owner approval before implementation phase.

All four Stage C deliverables are untracked, contain no secrets, and no source
changes have been made. The protected five-role baseline (7357c18) remains
unchanged. HEAD remains cd00325.