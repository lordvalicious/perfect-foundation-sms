# PHASE 96.8 STAGE A — ACCOUNT READINESS (READ-ONLY PREFlight)

## 1. Purpose and Scope

Read-only reconciliation of canonical-production readiness for the **five-role E2E
proof** (COUNSELLOR, GUARD, NURSE, ADMINISTRATIVE_OFFICER, LIBRARIAN), using
repository evidence and authorized read-only deployment information only.

Stage A performs NO account creation, NO E2E execution, NO source/Vercel/env/secret
changes, NO migrations, NO prov/sysctl changes, and NO commits/pushes/deploys.

## 2. Rules Observed

- #15 Do NOT infer an account exists merely because a role exists in source code.
- #16 Do NOT infer an account can be provisioned merely because an API endpoint appears to exist.
- #17 Do NOT invent credentials or sessions.
- Insufficient evidence ⇒ status `NOT_PROVEN` / `UNKNOWN` (never assumed).
- The phrase `READY_FOR_FIVE_ROLE_E2E` is NOT claimed anywhere in this report (5/5 roles lack sufficient evidence).
- No secrets are reproduced in this report. Files renamed/stored include not actual session or password values.

## 3. Repository State

- HEAD: `9cedc33e402322235bc6ab7de5973a05a51b0bb3` (branch `master`)
- origin/master == HEAD: YES; tracked working tree clean (untracked phase artifacts only)
- Protected baseline: `7357c18d1e4352bdce41b7de23c36eead4b66681` — ancestor of HEAD: YES
- FIVE_ROLE_BASELINE=PROTECTED; protected files diff vs baseline at HEAD: EMPTY
- Migration `0028`: NOT present in `backend/apps/accounts/migrations/`; none created; classification unchanged:

```
MIGRATION_0028_SOURCE_IDENTITY=NOT_IDENTIFIED
MIGRATION_0028_SOURCE_PRESENT=NO
MIGRATION_0028_EXPECTED=UNKNOWN
MIGRATION_0028_GRAPH_STATUS=VALID
MIGRATION_0028_LOCAL_STATUS=UNKNOWN
MIGRATION_0028_TARGET_STATUS=UNKNOWN
MIGRATION_0028_MODEL_DRIFT=PENDING_MODEL_CHANGES
MIGRATION_0028_CLASSIFICATION=INSUFFICIENT_EVIDENCE
MIGRATION_GATE=UNKNOWN
```

## 4. Deployment State (canonical backend `perfect-foundation-api`)

- Canonical project: `perfect-foundation-api` (`prj_RP5IoqTXfXDkP3AeI3UxwgkspUN9`), alias `https://perfect-foundation-api.vercel.app`
- Production deploy `dpl_DC4o4oLjdmh5iuH4qYotJdHds5bw` (commit `9cedc33`): **READY**, aliasAssigned, no build error
- Health: `GET https://perfect-foundation-api.vercel.app/api/health/` → **HTTP 200** `{"status":"ok","database":{"ok":true,"error":null},"deploy_version":"63-test-3"}`
- Root `GET /` → HTTP 200
- Deployment-specific URL `perfect-foundation-piatb9rz9-lordvalicious-projects.vercel.app` → SSO/team-scope page for unauthenticated requests (expected; NOT authoritative)

## 5. Frontend / E2E Target State (NEW FINDING — E2E BLOCKER)

- E2E harness default base URL (`e2e/playwright.config.js`, `e2e/helpers/page.js`) = `https://perfect-foundation-sms.vercel.app` (FRONTEND project)
- Frontend project `perfect-foundation-sms` (`prj_01w0P0HcW9BnLS6ustNxn6b6qsE3`): **30/30 most recent production deployments are state `ERROR`** (build error), including at HEAD `9cedc33` (dpl_GDPc7oqLu5PfuR4VK1tK2wEWVLQw).
- Last READY frontend deploy: `dpl_DSS1czrvcXu36BXDKNVDToL9BFqF` (commit `56e4b21`, 2026-09-25) — an ANCESTOR of HEAD. The live frontend domain currently serves that STALE build (HTTP 200).
- `frontend/vercel.json` rewrites `/api/:path` → `https://perfect-foundation-api.vercel.app/api/:path` (canonical backend proxy) — confirmed live: `GET https://perfect-foundation-sms.vercel.app/api/health/` → 200, same backend `63-test-3`.
- **Impact**: Any UI-level five-role E2E targeting the frontend would exercise a STALE (pre-HEAD) frontend build; the frontend project cannot build at HEAD. API-level role checks can still target the canonical backend directly.
- FRONTEND_BACKEND_TARGET (backend): `perfect-foundation-api.vercel.app` — READY.

## 6. Five-Role Account Readiness Matrix (verdicts below)

| ROLE | ROLE_DEFINED (models.py) | In migration 0016 choices | ACCOUNT_STATUS | AUTH EVIDENCE | PROVISIONING PATH | E2E_READINESS |
|------|--------------------------|--------------------------|----------------|----------------|-------------------|---------------|
| COUNSELLOR | YES (:20) | NO | **BLOCKED** | NONE | NONE | BLOCKED |
| GUARD | YES (:26) | YES | **NOT_PROVEN** | NONE (invalid placeholder) | seed-only (demo_seed/base.py:120) | BLOCKED |
| NURSE | YES (:27) | NO | **BLOCKED** | NONE | NONE | BLOCKED |
| ADMINISTRATIVE_OFFICER | YES (:24) | NO | **BLOCKED** | NONE | NONE | BLOCKED |
| LIBRARIAN | YES (:25) | YES | **NOT_PROVEN** | NONE (invalid placeholder) | seed-only (demo_seed/base.py:116) | BLOCKED |

## 7. Per-Role Evidence (A–F separation)

### COUNSELLOR
- A (role in code): YES — `models.py:20` `Role.TextChoices`
- B (valid production account): NO evidence
- C (can authenticate): NO evidence
- D (role assignment): NO evidence
- E (safe for E2E): NO (no account)
- F (proven provisioning path): NO — no demo_seed entry, no management command, no documented workflow (Phase 96.4: `ACCOUNT_PROVISIONING_NOT_AVAILABLE`)
- **ACCOUNT_STATUS = BLOCKED**

### GUARD
- A (role in code): YES — `models.py:26`
- B (valid production account): **NOT_PROVEN** — `sa_guard.txt` is an 88-byte placeholder whose content (`sessionid=...` / `csrftoken=` single lines) is NOT a valid Netscape cookie file; `e2e/helpers/session.js` parser requires tab-separated `#HttpOnly_...\tsessionid\t<value>` rows and returns NULL for this file. Historical `SA-EMP-00031` (Phase 62/91) documented as "no valid session".
- C: NOT_PROVEN — no usable session
- D: NOT_PROVEN — historical account's current assignment unverified
- E: NO
- F: seed-only — `demo_seed/base.py:120` `guard.{c}@example.test`; NOT exercised in production; seed creation requires owner authorization
- **ACCOUNT_STATUS = NOT_PROVEN** (do NOT read 96.7 carry-forward `GUARD=EXISTS` as proven)

### NURSE
- A (role in code): YES — `models.py:27`
- B: NO evidence (historical `SA-EMP-0002` only; `sa_nurse_inst4.txt` also an 88-byte invalid placeholder)
- C: NO evidence
- D: NO evidence
- E: NO
- F: NO — no seed, no command, no documented workflow (Phase 96.4: `ACCOUNT_PROVISIONING_NOT_AVAILABLE`)
- **ACCOUNT_STATUS = BLOCKED**

### ADMINISTRATIVE_OFFICER
- A (role in code): YES — `models.py:24`; NOTE Phase 83 documented "no canonical admin_officer role" claims until Phase 96.4 added role per models; no migration 0016 choice
- B: NO evidence (historical `SA-EMP-00041` forced to STAFF role; no valid session; Phase 91)
- C: NO evidence
- D: NO evidence
- E: NO
- F: NO — no provisioning path (Phase 96.4: `ACCOUNT_PROVISIONING_NOT_AVAILABLE`)
- **ACCOUNT_STATUS = BLOCKED**

### LIBRARIAN
- A (role in code): YES — `models.py:25`
- B (valid production account): **NOT_PROVEN** — `sa_librarian.txt` is an 88-byte invalid-placeholder file (same format problem as guard); historical `SA-EMP-00011` (Phase 62/91) documented as "no valid session"
- C: NOT_PROVEN — no usable session
- D: NOT_PROVEN — historical account was at one point mis-assigned `staff` (Phase 55 correction); current assignment unverified
- E: NO
- F: seed-only — `demo_seed/base.py:116` `librarian.{c}@example.test`; NOT exercised in production; requires owner authorization
- **ACCOUNT_STATUS = NOT_PROVEN** (do NOT read 96.7 carry-forward `LIBRARIAN=EXISTS` as proven)

## 8. Provisioning Paths Found (Stage A — nothing executed)

1. **`StaffProfileSerializer` auto-provision** (`backend/apps/accounts/serializers.py`, `create_account=True` → `_build_user_account()` lines 317–357, logic 360–423): a real create path, but POSTs are gated by `IsAdminOrReadOnly` (admin only); NOT a standalone safe-test provisioning workflow.
2. **Demo seed** (`backend/apps/accounts/demo_seed/base.py`): only LIBRARIAN (`:116`) and GUARD (`:120`) specs exist. This is the only evidence of a NON-admin provisioning author; NEVER run against canonical production; would require explicit owner authorization. Not a proven production path (rule #16).
3. **Throwaway scripts `create_staff_profile*.py`** (repo root, pre-existing, untracked): POST `/api/staff/` with EMBEDDED hardcoded sessionid/CSRF tokens and a candidate password, all targeting `https://perfect-foundation-api.vercel.app/api/staff/`. These are NOT a sanctioned provisioning path; they carry live-looking tokens (do not run; do not propagate). No evidence any succeeded.
4. **No E2E five-role provisioning** exists: `e2e/helpers/session.js` `ROLE_FILES` maps only SUPER_ADMIN/ADMIN/TEACHER/STUDENT/STAFF; no five-role entries.

## 9. E2E Test Readiness Audit

- `e2e/tests/*.spec.js` present: admin, auth, authorization, console-network, navigation, responsive, staff, student, super-admin, teacher.
- **No E2E spec references COUNSELLOR / GUARD / NURSE / LIBRARIAN / ADMINISTRATIVE_OFFICER** (grep over `e2e/` returned zero matches).
- No `P43_*` env-name mapping for the five roles exists in `session.js` (only the 5 default roles).
- E2E default target is the FRONTEND domain whose project cannot build at HEAD (see §5).
- Therefore **FIVE-ROLE_E2E_TEST_READINESS = NOT_PROVEN**.

## 10. Frontend/Backend Target Match

- Frontend proxy rewrites → canonical backend `perfect-foundation-api.vercel.app`: CONFIRMED live (200 via frontend proxy).
- But the frontal E2E base URL points at a frontend build that is stale (last READY = `56e4b21`, ancestor of HEAD). Target match for UI-level E2E at HEAD: **NO**.
- API-level role E2E targeting the canonical backend alias directly: READY.

## 11. Production Safety

- PRODUCTION_DATABASE_TOUCHED_BY_OPERATOR=NO
- MANUAL_PRODUCTION_MIGRATION=NO
- MIGRATION_0028 not created; classification preserved verbatim
- PROJECT_CREATED=NO; PROJECT_TRANSFERRED=NO; BILLING_CHANGED=NO
- SECRETS_EXPOSED=NO (this report exposes none)
- SOURCE_CHANGES=NONE; COMMIT=NONE; PUSH=NONE; DEPLOY=NONE; ACCOUNT_CREATION=NONE; E2E_EXECUTION=NOT_RUN

## 12. Blockers

- **B1**: 0/5 roles have a valid production account/session (GUARD/LIBRARIAN placeholders invalid; COUNSELLOR/ADMIN_OFFICER/NURSE none documented).
- **B2**: 3/5 roles (COUNSELLOR, ADMINISTRATIVE_OFFICER, NURSE) have NO provisioning path at all; the other 2 have only an owner-authorized seed path (never run in production).
- **B3**: E2E harness has no five-role session/role wiring and no five-role specs.
- **B4**: Frontend E2E target project cannot build at HEAD (all recent deployments ERROR); live frontend is a stale ancestor build.

## 13. Stage B (execution) Prerequisites

1. Owner must explicitly authorize E2E execution and — if accounts are absent — authorize account provisioning via a sanctioned path.
2. For GUARD/LIBRARIAN: decide + authorize the demo-seed path (or documented equivalent) as THE provisioning path; verification must then be performed in Stage B.
3. For COUNSELLOR/ADMINISTRATIVE_OFFICER/NURSE: a sanctioned, non-admin-safe provisioning workflow must first be defined (e.g., a management command) before any account can exist.
4. Resolve the frontend build failures or pin the E2E target to the canonical backend alias.
5. A five-role E2E spec + our callback wiring would be REQUIRED; none exists today.

## 14. Final Gate

```
FINAL_GATE=UNKNOWN is NOT used; per the rules the evidence is decisive:
FINAL_GATE=BLOCKED
```

Reason: no role meets account/authent/role-assignment E2E-sufficiency; 3/5 lack any provisioning path; E2E harness and target are not five-role ready. `READY_FOR_FIVE_ROLE_E2E` is NOT claimed.

## 15. Deliverables Cross-Reference

- `PHASE_96_8_STAGE_A_ACCOUNT_MATRIX.csv` — machine-readable matrix
- `PHASE_96_8_STAGE_A_MACHINE_SUMMARY.txt` — deterministic K/V summary