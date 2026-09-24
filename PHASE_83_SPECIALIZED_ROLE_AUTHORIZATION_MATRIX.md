# PHASE 83 — Specialized Role Authorization Matrix

**Target:** Five newly created accounts — Counsellor, Security Guard, Nurse,
Administrative Officer, Librarian — that can sign in but then receive
"You don't have permission to use this thing/page."

**Repo:** `C:\Users\Ryuk\Documents\perfect-foundation-sms` · branch `master`
· HEAD `2df1989d11009380f0a818e0cd5ac9b1f049f325`

**Scope:** Read-only diagnosis. No account, role, permission, password,
session, migration, or source modification was performed.

---

## Matrix

| Account | Login | `/api/auth/me` | Actual Role | Expected Role | Role Match | Backend Authorization | Frontend Guard | Result |
|---|---|---|---|---|---|---|---|---|
| Counsellor | PASS (attested — login API is role-independent; `LoginView` `permission_classes=[]`, `views.py:237`) | Returns `primary_role="staff"`, memberships `[{roles:[staff]}]` (stored role `staff`) | `staff` | NONE — no canonical `counsellor` role exists anywhere (`Role` enum, `models.py:11-29`; grep `counsellor|counselor` = 0 hits) | NO (cannot match) | Whatever module they target: `/api/students` = `IsAdminOrReadOnly` (read OK, write 403); `/api/hr` writes = `IsAccountantRole` 403; `/api/library` = `IsLibrarianRole` 403 | `/students` `RequireRoles` excludes `staff` (App.jsx:1089) → Access-denied card (App.jsx:1013-1028) | **ROLE_RESOLUTION_FAILURE** |
| Security Guard | PASS (attested) | `primary_role="staff"`, roles `[staff]` | `staff` | `guard` (exists: `Role.GUARD`, `models.py:24`, rank 30) | NO | `/api/visitors/*` = `IsStaffRole` (includes `staff`, `guard`) → would ALLOW; `/api/library` = `IsLibrarianRole` 403 | `/visitors` `RequireRoles` includes `guard` AND `staff` (App.jsx:1337) → allowed; other pages (e.g. `/library`) denied | **ROLE_MAPPING_FAILURE** — designation "Security Guard" never mapped to `Role.GUARD` at account creation |
| Nurse | PASS (attested) | `primary_role="staff"`, roles `[staff]` | `staff` | `nurse` (exists: `Role.NURSE`, `models.py:25`, rank 28) | NO | `/api/health-records/*` = `IsStaffRole` (includes `staff`, `nurse`) → would ALLOW (backend not the blocker) | `/health-records` `RequireRoles` omits `nurse` AND `staff` (App.jsx:1303) → FRONTEND denies even if stored role were `nurse` | **ROLE_MAPPING_FAILURE** (primary) + secondary `FRONTEND_ROLE_GUARD_FAILURE` on `/health-records` |
| Administrative Officer | PASS (attested) | `primary_role="staff"`, roles `[staff]` | `staff` | NONE — no canonical `admin_officer` role (Role enum has none) | NO (cannot match) | `/api/hr/` writes = `IsAccountantRole` 403; `/api/staff` writes = `IsAdminOrReadOnly` 403; `/api/library` 403 | `/hr`, `/staff`, `/library` `RequireRoles` exclude `staff` → denied | **ROLE_RESOLUTION_FAILURE** |
| Librarian | PASS (attested) | `primary_role="staff"`, roles `[staff]` | `staff` | `librarian` (exists: `Role.LIBRARIAN`, `models.py:23`, rank 35) | NO | `/api/library/*` = `IsLibrarianRole` (roles incl. librarian/teacher, NOT staff) → 403 | `/library` `RequireRoles` requires `librarian` (App.jsx:1229), `staff` excluded → denied | **ROLE_MAPPING_FAILURE** — designation "Librarian" never mapped to `Role.LIBRARIAN` |

---

## Classification totals (exactly one per account)

| Class | Count | Accounts |
|---|---|---|
| AUTHENTICATION_FAILURE | 0 | — |
| ROLE_RESOLUTION_FAILURE | 2 | Counsellor, Administrative Officer |
| ROLE_MAPPING_FAILURE | 3 | Security Guard, Nurse, Librarian |
| PERMISSION_MAPPING_FAILURE | 0 | — |
| BACKEND_AUTHORIZATION_FAILURE | 0 | — |
| FRONTEND_ROLE_GUARD_FAILURE | 0 (primary) | — (contributing for Nurse on `/health-records`) |
| CORRECT_ROLE_BUT_MISSING_PERMISSION | 0 | — |
| UNRESOLVED | 0 | — |

**Authenticated (login accepted): 5 of 5** — but only `staff` role is ever
stored for these accounts, so none can access specialized pages.

---

## Evidence anchors

- `backend/apps/accounts/serializers.py:343-354` — `StaffProfileCRUDSerializer._build_user_account`
  hardcodes `RoleAssignment(role=Role.STAFF)` for every staff account; `designation` is never consulted.
- `backend/apps/accounts/views.py:234-237` — `LoginView` has no role gate; any valid credential authenticates.
- `backend/apps/accounts/views.py:430-444` — `CurrentUserView` returns `UserSerializer`; `primary_role`
  derived from stored RoleAssignments via `User.primary_role` (`models.py:166-191`).
- `backend/apps/accounts/models.py:169-185` — `primary_role` priority list omits `LIBRARIAN`
  (also ORG_ADMIN, HEAD_OFFICE); a hypothetical librarian-only account would yield `primary_role=None`.
- `backend/apps/accounts/permissions.py:163-187` (`IsLibrarianRole`), `:219-242` (`IsNurseRole`),
  `:70-92` (`IsAdminOrReadOnly`), `:116-137` (`IsAccountantRole`), `:190-216` (`IsStaffRole` incl. staff/nurse/guard).
- `backend/apps/library/views.py` — all views `IsLibrarianRole`.
- `backend/apps/visitors/views.py:29,72,82,102` — `IsStaffRole`.
- `backend/apps/health/views.py:15,48` — `IsStaffRole`.
- `frontend/src/App.jsx:1006-1032` — `RequireRoles` renders "Access denied / You don't have permission
  to view this page." when `scopedHasRole(roles)` fails; `:1420` — toast "You don't have permission to access {url}."
- `frontend/src/schoolContext.jsx:331-349` — `scopedHasRole` reads `memberships[].roles[].role` only.
- `e2e/helpers/session.js:4-12` — ROLE_FILES cover SUPER_ADMIN/ADMIN/TEACHER/STUDENT/STAFF only; no
  session fixtures exist for the five accounts, so live `/api/auth/me` capture was not possible (no fabrication).