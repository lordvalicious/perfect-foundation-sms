# PHASE 78 — STEP 3: AUTHORIZED PRODUCTION TEST-ACCOUNT READINESS

Phase: 78 · Step: 3 · Mode: READ-ONLY (no source change, no user create/modify, no password reset, no role/permission
change, no production data change, no redeploy, no Vercel change)
Date: 2026-09-23 (UTC ~23:10) · Target: `https://perfect-foundation-sms.vercel.app`
Objective: Determine whether a legitimate, already-authorized production account/session exists for **read-only**
production certification, resolving `AUTHENTICATED_SESSION_CREDENTIALS_UNAVAILABLE` from Step 2.

## 1. Documented Account Evidence (repository & Phase 73-78 artifacts)
- **Session mechanism (Phase 43+):** `e2e/README.md` + `e2e/helpers/session.js` — sessions supplied at runtime via
  Netscape cookie files under `P43_SESSIONS_DIR` (`sa_frostfire.txt`=SUPER_ADMIN, `sa_flora.txt`=ADMIN,
  `sa_SA-EMP-0001.txt`=TEACHER, `sa_SA-ST-0001.txt`=STUDENT, `sa_DI-staff.txt`=STAFF) or `P43_<ROLE>_SESSIONID`
  env vars. Phase 43 report documents the runtime dir `C:\Users\Ryuk\AppData\Local\Temp\opencode`.
- **Phase 57 role/auth/session matrix** documents accounts: SUPER_ADMIN=FrostFire, ADMIN=Flora (auth_me_role
  principal), TEACHER=SA-EMP-0001, STAFF=DI-EMP-0001, STUDENT=SA-ST-0001, LIBRARIAN=SA-EMP-00011,
  ACCOUNTANT=DEG-EMP-00031, GUARD=SA-EMP-00031, ADMIN_OFFICER=SA-EMP-00041, NURSE=SA-EMP-0002 (login requires
  `school_code`; 400 without).
- **Application-published demo hints:** login page (`frontend/src/pages/LoginPage.jsx:239-240`) displays
  `admin / Admin123!`, `accountant / Accountant123!`, `teacher / Teacher123!`, `student / Student123!`.
- **Committed secrets found (NOT exposed, NOT used):** `docs/audit/SECURITY_AUDIT.md` and
  `docs/audit/RISK_REGISTER.md` R-01 flag a **hardcoded superadmin credential committed in a VCS migration**
  (`accounts/migrations/0014_create_frostfire_superadmin.py`, re-forced on every migrate) — classified
  `SECRET_PRESENT_NOT_EXPOSED`; this is a documented vulnerability to remove, **not** a legitimate authorized test
  credential, and was NOT used. `phase55_*.py` scripts likewise contain committed account passwords —
  `SECRET_PRESENT_NOT_EXPOSED`, unused.

## 2. Local Environment Variables
- Scanned for `P43_*`, `E2E_*`, `TEST_*`, `PLAYWRIGHT_*`, `AUTH_*` → **NONE SET** (only Windows `SESSIONNAME`,
  unrelated). No values read/printed.

## 3. Playwright Auth State
- Repository search: no `storageState`, no `.auth/`, no `auth.json`, no Playwright saved-state files.
- `sa_*.txt` cookie files inventoried (metadata only; **cookie/session values never read out**):
  - Temp dir `C:\Users\Ryuk\AppData\Local\Temp\opencode` (the documented `P43_SESSIONS_DIR`): 11 files contain only
    a `csrftoken` (no `sessionid` → cannot authenticate). **`sa_frostfire_di.txt`** (2026-09-22) contains a
    `sessionid` + 2 `csrftoken` (client expiry 2026-10-06).
  - Repo root: `sa_accountant.txt`, `sa_admin_officer.txt`, `sa_guard.txt`, `sa_hr.txt`, `sa_librarian.txt`,
    `sa_nurse_inst4.txt`, `sa_receptionist.txt`, `sa_student2.txt`, `sa_student3.txt` (2026-09-23) — not valid
    Netscape cookie files (1-field lines, no cookie rows).
- **Validity tested safely (non-mutating):** injecting `sa_frostfire_di.txt` via Playwright →
  `GET /api/auth/me/` = **403**, frontend shows login page → **server-side session invalid** (expired/logged-out).
  Structurally valid file, functionally invalid session.

## 4. Role-Account Matrix (18 canonical roles)
| Classification | Count | Roles |
|---|---|---|
| DOCUMENTED_ACCOUNT | 10 | super_admin, admin, principal, accountant, librarian, guard, nurse, teacher, student, staff |
| NO_DOCUMENTED_ACCOUNT | 6 | org_admin, head_office, vice_principal, campus_admin, academic, parent |
| UNKNOWN | 2 | hr, receptionist (placeholder session files only; no documented identifier) |

No role has a **usable authenticated session** (0/18). See `PHASE_78_STEP_3_ROLE_ACCOUNT_MATRIX.csv`.

## 5. Authentication Preflight Attempts (read-only, non-mutating)
1. **Session injection (SUPER_ADMIN)** — `sa_frostfire_di.txt` → `/api/auth/me/` 403; login page persists. Result:
   **FAILED** (session invalid server-side).
2. **Normal login (application-published demo `admin`)** — GET csrf 200, `POST /api/auth/login/` → **400**
   ("Unable to sign in"); `/api/auth/me/` 403; no session, no role determined, no forced password-change screen, no
   dashboard. Result: **FAILED** (demo credentials do not match the deployed backend).
No password was changed, no account created, no permission/role altered, no mutation workflow submitted.

## 6. Blocker
`AUTHENTICATED_TESTING_REQUIRES_AUTHORIZED_CREDENTIALS`. The previously-authorized session file is invalid
server-side, application-published demo credentials are rejected (400), and no other legitimate authorized
credential/session is available. Per Phase 78 rules no registration, admin creation, SQL/Django-shell creation,
password reset, role assignment, or database modification is performed, and the in-VCS compromised superadmin
credential (R-01) is deliberately **not** used.

## 7. Safety Verification
```
SOURCE_MODIFIED=NO        PRODUCTION_DATA_MUTATED=NO      USERS_CREATED=NO
USERS_MODIFIED=NO         USERS_DELETED=NO                PERMISSIONS_CHANGED=NO
PASSWORDS_CHANGED=NO      MIGRATIONS_RUN=NO               REDEPLOY_PERFORMED=NO
VERCEL_SETTINGS_CHANGED=NO
```
No passwords, tokens, cookies, session IDs, or authorization headers printed anywhere. In-VCS secrets referenced as
`SECRET_PRESENT_NOT_EXPOSED` only.

## 8. Conclusion
Authorized account evidence is **PARTIAL** (10/18 roles have documented account identifiers from prior audit
artifacts; 0 usable live sessions). Playwright auth state is **UNAVAILABLE** (no valid session). Authentication
preflight **FAILED** for both the only stored session (403) and the demo login (400). Authenticated browser
certification remains **BLOCKED** until the user supplies an authorized production session via the documented
mechanism (`P43_SESSIONS_DIR`/`P43_<ROLE>_SESSIONID`). Exact result:
`AUTHENTICATED_TESTING_REQUIRES_AUTHORIZED_CREDENTIALS`.