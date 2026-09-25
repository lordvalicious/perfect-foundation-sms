PHASE 97 STAGE B PREFLIGHT
=========================

Objective
---------
Read-only design of minimum implementation to unblock five-role E2E:
  five-role specs, CORE blocks, ROLE_INFO blocks, safe runtime session
  acquisition from Phase 96.9 credentials. Do NOT implement, do NOT modify
  source, do NOT create sessions, do NOT execute E2E, do NOT commit/push/deploy.
Stop after deliverables and wait for separate OWNER IMPLEMENTATION APPROVAL.

Important Details (superset binding)
------------------------------------
Safety: READ-ONLY preflight only. No source/E2E/session/credentials
setup. No commits/pushes/deploys. No migration 0028. No demo_seed.
No fabricating tests/sessions/expectations. Nothing ambiguous ->
NOT ESTABLISHED / BLOCKED / UNKNOWN.

Repo State
----------
HEAD == origin/master == cd00325 (test(e2e): wire five-role session lookup
for Phase 96.8 roles). Tracked worktree clean; only untracked phase
deliverables. Protected baseline 7357c18 is ancestor (13 commits);
diff on backend/apps/accounts, backend/apps/schools, backend/apps/authentication
vs baseline = EMPTY. Migration 0028 absent, graph unchanged since baseline.

Accounts (Phase 96.9, verified read-only)
-----------------------------------------
Five production E2E accounts created via POST /api/staff/ in Default
Institution (id 1, PF-CLEMD), campus 7, department E2E, gender other,
create_account=True. Auth-verified via POST /api/auth/login/ (school_code
PF-CLEMD) -> GET /api/auth/me/ (HTTP 200, primary_role matches).
  e2e.counsellor/DI-EMP-0002/id 117; e2e.guard/DI-EMP-0003/id 118;
  e2e.nurse/DI-EMP-0004/id 119; e2e.administrative_officer/DI-EMP-0005/id 120;
  e2e.librarian/DI-EMP-0006/id 121. Staff count 11 -> 16. Health 200
  {"status":"ok","database":{"ok":true,"error":null},"deploy_version":"63-test-3"}.
Temp passwords retained ONLY at
C:\Users\Ryuk\AppData\Local\Temp\opencode\p969_stage_b_credentials.env
(OUTSIDE repo; never printed/committed). No sa_<role>.txt session files
exist yet (Stage A finding F2).

Phase 97 Stage A Gate
---------------------
PHASE 97 STAGE A FINAL GATE: BLOCKED.
Findings: F1 = zero five-role E2E specs (10 spec files, 54 direct test()
calls, coverage only SUPER_ADMIN/ADMIN/TEACHER/STUDENT/STAFF);
F2 = no five-role session configuration (no P43_<ROLE>_SESSIONID, no
sa_<role>.txt files); F3 = modules.js has no CORE/ROLE_INFO entries for
the five roles. Frontend/backend health, proxy target, migration safety,
account existence = PASS.

Frontend Authorization Source-of-Truth (critical for Stage B)
-------------------------------------------------------------
File: frontend/src/App.jsx (routes + navigation array). All role
expectations traced to this source. "Do not invent permissions. If the
source code does not establish an expectation, mark it NOT ESTABLISHED."

=== Navigation array (visibleNavGroups) ===
Line ~380-418. item.roles.length === 0 || hasRole(item.roles) means
roles: [] is visible to everyone; non-empty roles gate visibility.

  - COUNSELLOR: Helpdesk (line 408, roles: ["helpdesk"])
  - GUARD: Helpdesk (line 408), Visitors (lines 408-409)
  - NURSE: Health Records (line 376, roles: ["health-records"])
  - ADMINISTRATIVE_OFFICER: Helpdesk (line 408, roles: ["helpdesk"])
  - LIBRARIAN: Library (line 395, roles: ["library"])

=== Route-level RequireRoles gates (lines 1302-1346) ===
  /health-records: roles=["super_admin","admin","principal","vice_principal","campus_admin","teacher","nurse","staff"]
    -> NURSE only (staff also). Counsellor, administrative_officer, guard, librarian BLOCKED.

  /helpdesk: roles=["super_admin","admin","principal","vice_principal","campus_admin","academic","hr","receptionist","guard","teacher","counsellor","administrative_officer","staff"]
    -> ALL 5 roles (counsellor, guard, nurse, administrative_officer, staff) INCLUDED.

  /visitors: roles=["super_admin","admin","principal","vice_principal","campus_admin","academic","hr","receptionist","guard","staff"]
    -> GUARD only (staff also). Counsellor, administrative_officer, nurse, librarian BLOCKED.

  /digital-ids: roles=["super_admin","admin","principal","vice_principal","campus_admin","academic","hr","receptionist","staff"]
    -> NONE of the 5 roles included. All BLOCKED.

  /library: NO route definition in App.jsx. Nav shows it for librarian
    but source is absent. GAP: module/authorization expectation for
    /library cannot be established from source.

=== Established CORE expectations (auth, username, role, scope) ===
All five roles. Role enum in backend/apps/accounts/models.py includes
COUNSELLOR/ADMINISTRATIVE_OFFICER/LIBRARIAN/GUARD/NURSE; ROLE_RANK;
Permission (category/action, resource.action); RolePermission
(role+permission+institution, unique); UserPermission (allow/deny,
expiry); User.get_permissions(institution) = RolePermission perms |
allow - deny; superuser = all.

=== NOT ESTABLISHED from source ===
- Any /library route-level authorization for LIBRARIAN (route absent)
- /visitors access for counsellor, administrative_officer, nurse, librarian (explicitly gated)
- /health-records access for counsellor, administrative_officer, guard, librarian (explicitly gated)
- /digital-ids access for any of the 5 roles (all excluded)
- Backend API permission classes for helpdesk/visitors/health-records/library
- ROLE_GRANTS in demo_seed/part1_foundation.py for counsellor, nurse,
  administrative_officer (gaps confirmed: only librarian and guard have grants)
- Frontend role-based access patterns (primary_role/has_any_role/ROLE_ACCESS)
  grep across frontend/src = NO matches for the five roles

Session Acquisition Strategy Analysis
-------------------------------------
Two options, both compatible with existing harness (session.js):
  A. Runtime login at test startup: use Phase 96.9 runtime credential file
     (p969_stage_b_credentials.env) via normal POST /api/auth/login/ per role,
     keeping passwords outside repo. Per-role STOP on auth failure. Existing
     harness getSessionId() supports P43_<ROLE>_SESSIONID env vars.
  B. Temporary runtime session files outside repo: Netscape format in
     P43_SESSIONS_DIR. Phase 96.9 temp passwords could generate these, but
     no scripts provided; session.js supports as fallback.

  Recommendation: Option A (runtime login) is lower-friction and aligns
  with existing harness design (env-driven, no temp files in repo). Option
  B is viable if owner prefers file-based sessions.

Proposed Five-Role Test Scope (derived deterministically from source)
---------------------------------------------------------------------
Core identity/role/scope/per-role authz where source-supported:
  - COUNSELLOR: /helpdesk render + permission checks (role in RequireRoles)
  - GUARD: /helpdesk + /visitors render + permission checks
  - NURSE: /health-records render + permission checks
  - ADMINISTRATIVE_OFFICER: /helpdesk render + permission checks
  - LIBRARIAN: /library nav entry but NO route — test nav visibility only,
    mark /library route-access as NOT ESTABLISHED; design test for nav
    visibility + attempt /library route to document block

Test enumeration (example counts, NOT executable yet):
  - 5 role-spec files, ~12 test() calls each = ~60 direct tests
  - Plus 5 nav-visibility assertions + 4 route-access block tests
  - Total ~70 test() calls across 5 files (superset of existing 54)

Production-Safety Findings
--------------------------
- No destructive ops in e2e suite (only UI clicks on empty login form,
  nav toggles; no .request.post/put/patch/delete)
- Five accounts exist and are active; re-login verified via GET /api/auth/me/
- Frontend proxy /api/health/ -> 200; CSP connect-src matches target
- No hard-coded creds in repo (.env.example gitignored; .env files
  documented as runtime-only)
- Session strategy A keeps passwords outside repo; B uses temp files also
  outside repo (both acceptable)

Final Gate
----------
PHASE 97 STAGE B PREFLIGHT FINAL GATE: UNKNOWN
(requiring owner implementation review)

RATIONALE: Source establishes partial module/authorization expectations
for 4 of 5 roles via navigation + /helpdesk gate. One critical gap:
/library route absent for LIBRARIAN, making that expectation NOT
ESTABLISHED. Session strategy not decided. Owner must review and either
(1) authorize implementation to fill gaps, or (2) confirm scope reduction.

Deliverables (untracked, no secrets)
-------------------------------------
  PHASE_97_STAGE_B_PREFLIGHT.md          (this file)
  PHASE_97_STAGE_B_PREFLIGHT_MATRIX.csv
  PHASE_97_STAGE_B_MACHINE_SUMMARY.txt

STOP: Do NOT implement, modify source, create sessions, or execute E2E.
Wait for separate owner approval.