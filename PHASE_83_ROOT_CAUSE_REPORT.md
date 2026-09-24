# PHASE 83 — Root Cause Report: Specialized-Role Accounts Cannot Access Their Modules

**Status: READ-ONLY DIAGNOSIS — no fix implemented.**
Target: five newly created accounts (Counsellor, Security Guard, Nurse,
Administrative Officer, Librarian) that log in successfully but are met with
"You don't have permission to use this thing/page."

---

## 1. Executive summary

All five accounts can **authenticate** (login is role-independent —
`LoginView` has `permission_classes = []`, so Django only checks the
credential pair), but **every one of them is stored with the single generic
role `staff`**. The role that corresponds to their designation (Security
Guard → `guard`, Nurse → `nurse`, Librarian → `librarian`) is **never
assigned at account-creation time**, and for two designations (Counsellor,
Administrative Officer) **no canonical role exists at all**. Because the
frontend route guards and several backend permission classes require the
specialized role, these staff-tagged accounts are denied everywhere their
module lives.

This is not a session/authentication failure and not a missing permission
object — it is a **provisioning failure**: the designation→role mapping that
the system owner several times asserted exists in the account-creation path
does not exist. The creator of accounts (the Staff module serializer) is
hardcoded to `Role.STAFF`.

---

## 2. Root cause chain (proven by static analysis)

### 2.1 The single decisive defect — `serializers.py:343-354`

`StaffProfileCRUDSerializer._build_user_account` (called only when the staff
creation payload has `create_account: true`):

```python
role_assignment, created = RoleAssignment.objects.get_or_create(
    membership=membership,
    role=Role.STAFF,          # <-- HARDCODED to "staff"
)
```

- The `designation` field of the `StaffProfile` is **never read** here.
- No lookup to `Role` by designation. No default category table. Nothing.
- Therefore **any staff account created through the Staff module —
  regardless of whether the profile designation is "Librarian", "Security
  Guard", "Nurse", "Counsellor", or "Administrative Officer" — gets exactly
  one role: `staff`.**

`StaffListCreateView` (`views.py:1124`) uses `IsAdminOrReadOnly`, so any
campus admin admin-created account goes down this path.

### 2.2 Secondary element — the canonical Role enum has no Counsellor / Admin Officer role

`backend/apps/accounts/models.py:11-29`:

```python
class Role(models.TextChoices):
    SUPER_ADMIN   = "super_admin",  "Super Admin"
    ADMIN         = "admin",        "Institution Admin"
    ORG_ADMIN     = "org_admin",    "Organization Admin"
    HEAD_OFFICE   = "head_office",  "Head Office"
    PRINCIPAL     = "principal",    "Principal"
    VICE_PRINCIPAL= "vice_principal","Vice Principal"
    CAMPUS_ADMIN  = "campus_admin", "Campus Admin"
    ACADEMIC      = "academic",     "Academic Coordinator"
    ACCOUNTANT    = "accountant",   "Accountant / Bursar"
    HR            = "hr",           "HR Officer"
    RECEPTIONIST  = "receptionist", "Receptionist"
    LIBRARIAN     = "librarian",    "Librarian"
    GUARD         = "guard",        "Security Guard"
    NURSE         = "nurse",        "Nurse"
    TEACHER       = "teacher",      "Teacher"
    PARENT        = "parent",       "Parent"
    STUDENT       = "student",      "Student"
    STAFF         = "staff",        "Staff"
```

There is **no `counsellor`, `counslor`, `admin_officer`, or `administrative_officer`**
role. Even if the serializer had a designation→role mapper, it could not
produce a valid role for these two designations. Counsellor and
Administrative Officer therefore cannot be fixed by mapping alone — a new
canonical role must be introduced first.

### 2.3 Confirmed supporting evidence (contradiction with the seeding story)

- `seed_staff.py` (management command) creates **StaffProfile rows only** —
  it does **not** create `User`/`RoleAssignment` for them. So any claim "the
  seed created these accounts" is false; the login-capable accounts must
  have come from the **Staff module UI/serializer** path, which hardcodes `staff`.
- `demo_seed/base.py` `_campus_role_users` (lines ~102-122) shows the
  **intended** behavior the owner expects — it maps specific campus users to
  explicit roles (e.g. librarian → `Role.LIBRARIAN`, guard → `Role.GUARD`).
  That function is only used by the demo seed for named campus users, NOT by
  the Staff-module account creator.
- `demo_seed/part2_people.py:28-39` lists "Security Guard" / "Nurse" as
  support-staff designations; `seed_support_staff` assigns `Role.STAFF` to
  all of them (`base.assign_roles(ctx, user, [Role.STAFF])`), repeating the
  same generic-staff bug for support staff created in the demo seed.

### 2.4 What the sign-in eventually returns (`/api/auth/me`)

- `LoginView` (`views.py:234`) authenticates any valid credential.
- `CurrentUserView` (`views.py:430`) serializes the user; `UserSerializer`
  includes `primary_role`, computed by `User.primary_role` (`models.py:166-191`).
- Because the only RoleAssignment is `staff` — and `staff` **is** in the
  priority list — `primary_role` resolves to `"staff"`, the frontend sees
  `roles: ["staff"]`, and **every specialized route guard denies access**.

### 2.5 Where the specific denial message originates (frontend)

- `frontend/src/App.jsx:1006-1032` — `RequireRoles` guard: if
  `scopedHasRole(requiredRoles)` fails, it renders "Access denied —
  You don't have permission to view this page."
- `frontend/src/schoolContext.jsx:331-349` — `scopedHasRole` reads only
  `memberships[].roles[].role` for the active school. No fallback to
  `is_superuser`, no module-based inference.
- `App.jsx:1420` — session interceptor toast "You don't have permission to
  access {url}" when the backend returns a 403 (e.g. `/api/library` for
  `staff`).

### 2.6 Backend permission classes relevant to each account

| Endpoint area | Permission class | `staff` allowed? | Specialized role allowed? |
|---|---|---|---|
| `/api/library/*` | `IsLibrarianRole` (`permissions.py:163`) | NO → 403 | `librarian` only |
| `/api/visitors/*` | `IsStaffRole` (`permissions.py:190`) | YES | `guard`, `nurse`, `teacher`, `staff` |
| `/api/health-records/*` | `IsStaffRole` (`permissions.py:190`) | YES | incl. `nurse` |
| `/api/staff/*` (profiles) | `IsAdminOrReadOnly` | GET only; write 403 | admins only for write |
| `/api/hr/*` records | `IsAccountantRole` (`permissions.py:116`) | NO → 403 | `accountant`, admins |
| `/api/students/*` | `IsAdminOrReadOnly` / `IsAdminRole` | GET only; write 403 | admins/academic |
| `/api/ai/*` | `IsTeacherRole`, `IsAccountantRole` | NO → 403 | role-specific |

So **behind the API**, a `staff`-tagged Nurse or Security Guard can already
reach health/visitor data (backend `IsStaffRole` allows), but the *frontend
guard* (2.5) still blocks them on the specialized pages; a `staff`-tagged
Librarian is blocked at the backend itself (`IsLibrarianRole`).

---

## 3. Per-account verdict (primary classification — one each)

| # | Account | Stored role | Canonical role exists? | Required for its module | Primary class |
|---|---|---|---|---|---|
| 1 | Counsellor | `staff` | NO | (none — no role) | **ROLE_RESOLUTION_FAILURE** |
| 2 | Security Guard | `staff` | YES — `guard` | `guard` | **ROLE_MAPPING_FAILURE** |
| 3 | Nurse | `staff` | YES — `nurse` | `nurse` | **ROLE_MAPPING_FAILURE** |
| 4 | Administrative Officer | `staff` | NO | (none — no role) | **ROLE_RESOLUTION_FAILURE** |
| 5 | Librarian | `staff` | YES — `librarian` | `librarian` | **ROLE_MAPPING_FAILURE** |

---

## 4. Contributing / latent defects (secondary, recorded not fixed)

1. `Role` enum has **no counsellor / admin_officer** choice — even the
   "correct" mapping cannot exist today. **Suggested future role:**
   `COUNSELLOR = "counsellor"`, `ADMIN_OFFICER = "admin_officer"` (or reuse
   `hr`), then frontend nav + guards would need entries too.
2. `primary_role` priority (`models.py:166-191`) **omits `LIBRARIAN`**
   (also ORG_ADMIN, HEAD_OFFICE). A librarian-only account would yield
   `primary_role=None`, confusing all consumers (Auth context,
   `/api/auth/me`, seed e2e).
3. Frontend `/health-records` route (`App.jsx:1303`) requires
   super_admin/admin/principal/vice_principal/campus_admin/teacher — it
   **omits both `nurse` and `staff`**, blocking the Nurse even when the
   account is someday correctly mapped, despite the backend allowing
   `IsStaffRole`.
4. E2E `ROLE_FILES` (`e2e/helpers/session.js:4-12`) contain no fixtures for
   `librarian`, `nurse`, or `guard` accounts, so none of these roles can be
   exercised headlessly today.

---

## 5. Confirmed-by-verification summary

- **Login:** Code supports it (`permission_classes=[]`); 5/5 attested
  successful by system owner; not live-verified (no credentials/session
  fixtures permitted in read-only phase).
- **`/api/auth/me`:** `primary_role="staff"`, `roles=["staff"]` — inferred
  from stored RoleAssignment; not live-verified.
- **Database role store:** Not directly probe-able — the documented
  `DATABASE_URL` endpoint (used by `backend/check_nurse.py`, `check_users.py`,
  `audit_users.py`) points at a host/schema where `relation "accounts_user"
  does not exist`, meaning the check scripts point at a database that does
  not contain the SMS schema (environment drift, recorded as CON-83-05).
- **Root defect line:** `C:\Users\Ryuk\Documents\perfect-foundation-sms\backend\apps\accounts\serializers.py:349-352`.

---

## 6. What was NOT done (read-only compliance)

- No role/account/permission/password changes. No migrations. No redeploy.
- No session fabrication; no login POST; no live `/api/auth/me` capture.
- No source-code edits. The four Phase 83 deliverables are the only new files.