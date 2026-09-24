# PHASE 82 — Contradiction Log (Blocked Role Authentication / Session Resolution)

Each entry: conflicting evidence, authoritative source, decision, reason, and effect
on classification. Contradictions may reference earlier phases; no earlier phase
artifact was modified.

---

## CON-82-01 — org_admin / head_office "account" references

**Conflicting evidence.**
- `backend/apps/accounts/demo_seed/base.py` contains SOURCE-LEVEL seed accounts
  (`demo_orgadmin`, and per-campus seeds like `{c}.admin`, `principal.{c}`,
  `accountant.{c}`, `hr.{c}`, `reception.{c}`, `librarian.{c}`, `guard.{c}`, `clerk.{c}`
  at `@example.test` addresses).
- No production account identifier exists for `org_admin` or `head_office` in
  `PHASE_78_STEP_3_ROLE_ACCOUNT_MATRIX.csv`, `PHASE_79`/`PHASE_80` final matrices,
  or `PHASE_81_AUTHENTICATION_EVIDENCE_MATRIX.csv`.
- `PHASE_80_STEP_5_org_admin_MACHINE_SUMMARY.txt` / `STEP_6_head_office` report:
  `NO_DOCUMENTED_ACCOUNT_NO_SESSION_FIXTURE_NO_FRONTEND_GUARD_MISS-002_TPR-005`.

**Authoritative source.** `backend/apps/accounts/models.py` `Role` enum + production
evidence matrices. Source-level seed documents are NOT production authentication proof.

**Decision.** Classify `org_admin` and `head_office` as `NO_DOCUMENTED_ACCOUNT`.

**Reason.** A seed fixture in source code is not evidence of a production account; no
authoritative source documents either role's account; no session is enumerated.

**Effect on classification.** `org_admin` / `head_office` ⇒ NO_DOCUMENTED_ACCOUNT.

---

## CON-82-02 — SA-EMP-00041 "administrative officer" vs canonical enum

**Conflicting evidence.**
- `PHASE_62_PROVISIONING_CERTIFICATION.csv` and `PHASE_62_CANONICAL_ROLE_CONTRACT.md`
  list `SA-EMP-00041` as ADMIN_OFFICER with claimed login PASS.
- `Role` enum in `models.py` has NO `admin_officer` value; Phase 55/57 map
  `SA-EMP-00041` to role `staff`.

**Authoritative source.** `Role` enum; prior staff authentication evidence.

**Decision.** `SA-EMP-00041` is not a canonical role and is OUTSIDE this phase's 12-role
list. Role identity is defined by the enum, not by a claim in `PHASE_62`.

**Reason.** The enum is the authoritative role vocabulary; admin_officer is not there.

**Effect on classification.** None for the 12 blocked roles; excluded from the matrix.

---

## CON-82-03 — Phase 62 "login PASS + session cookie" claims vs current invalid fixtures

**Conflicting evidence.**
- `PHASE_62_PROVISIONING_CERTIFICATION.csv`, `PHASE_62_SPECIALIZED_ROLE_E2E.csv`, and
  `PHASE_62_FINAL_RELEASE_CERTIFICATION.md` claim login PASS and a "session cookie" file
  name (e.g. `sa_accountant.txt`, `sa_librarian.txt`, `sa_guard.txt`,
  `sa_nurse_inst4.txt`, `sa_hr.txt`, `sa_receptionist.txt`, `sa_admin_officer.txt`).
- The repository-root `sa_*.txt` files for these claims EXIST but are NOT Netscape
  format (`isNetscape=False`, 2 lines, `keyspec=True`, i.e. a `sessionid`+`csrftoken`
  key/value placeholder), and `e2e/helpers/session.js` requires Netscape tab-delimited
  lines with `parts[5] === "sessionid"` (session.js lines 31–32).
- `P43_SESSIONS_DIR` contains only the five proven roles' fixtures.
- Phase 80/81 report no valid session for these roles.

**Authoritative source.** Current file contents + `e2e/helpers/session.js` parser +
Phase 81 live evidence. Phase 62 was historical documentation against a pre-current
deployment; it is documentation of intended provisioning, not current auth proof.

**Decision.** Do NOT treat Phase 62 login claims or placeholder file names as current
session evidence. No login was performed in Phase 81 or 82 (LOGIN_POSTS=0).

**Reason.** A documented username ≠ a session; a fixture filename ≠ proof of identity;
a placeholder key/value file is unparseable by the session loader.

**Effect on classification.** accountant/librarian/guard/nurse ⇒ DOCUMENTED_ACCOUNT_NO_SESSION
(documented account + credential documented-but-unused + no valid session).

---

## CON-82-04 — hr.gvc / reception.gvc documented in Phase 62 vs "NO DOCUMENTED ACCOUNT" in later phases

**Conflicting evidence.**
- `PHASE_62_CANONICAL_ROLE_CONTRACT.md` and `PHASE_62_PROVISIONING_CERTIFICATION.csv`
  document accounts `hr.gvc` (hr) and `reception.gvc` (receptionist) in Institution 2
  ("Demo Education Group") with claimed PASS logins and `sa_hr.txt` /
  `sa_receptionist.txt` "session cookie" files.
- `PHASE_80_STEP_11_hr` / `STEP_12_receptionist` machine summaries and the
  `PHASE_78_STEP_3_ROLE_ACCOUNT_MATRIX.csv` record NO documented account / no session.
- Repo-root `sa_hr.txt` and `sa_receptionist.txt` are non-Netscape placeholders
  (`isNetscape=False`, 2 lines).
- No credential for `hr.gvc` / `reception.gvc` is documented anywhere usable.

**Authoritative source.** Current file contents + `session.js` parser + Phase 81 live
evidence. Phase 62 is historical documentation only.

**Decision.** The account NAMES are considered documented (Phase 62), but no credential
is available and the referenced fixture files are invalid placeholders. Classify as
`DOCUMENTED_ACCOUNT_NO_CREDENTIAL`.

**Reason.** Account identifier documented, credential NOT available, session NOT valid
or reproducible. Never infer a session from a documented username or a .txt file name.

**Effect on classification.** hr / receptionist ⇒ DOCUMENTED_ACCOUNT_NO_CREDENTIAL.

---

## CON-82-05 — Stale / duplicate fixtures SA-ST-0002 and SA-ST-0003 (student)

**Conflicting evidence.**
- `PHASE_62` documents SA-ST-0002/0003 student accounts with `sa_student2.txt` /
  `sa_student3.txt` "session cookie" files.
- Phase 81 live evidence: both fixtures produce HTTP 403 (stale, duplicate accounts);
  `PF-20262027-0121` (student) authenticates 200.
- Repo-root `sa_student2.txt` / `sa_student3.txt` are non-Netscape placeholders.

**Authoritative source.** Phase 81 live `/api/auth/me/` (403), current file contents.

**Decision.** Retain as stale/duplicate student fixtures; not repaired. Both are
student-role, outside this phase's 12 blocked roles.

**Reason.** Prohibited to manufacture/repair sessions; no impact on the 12 roles.

**Effect on classification.** None (student role already AUTHENTICATED_PROVEN via
SA-ST-0001; not among the 12).

---

## CON-82-06 — Deployment mismatch (API vs frontend) from Phase 81

**Conflicting evidence.**
- Phase 81 established deployed API commit differs from deployed frontend commit
  (`/api/deploy-test/` → 404, STALE_DEPLOYMENT_PREDATES_ROUTE).
- Phase 62 deployment contract expected commit `abc3369` or later; deployment status was
  already noted as "current deployed commit unknown (pre-e534ded)".

**Authoritative source.** Phase 81 live probes.

**Decision.** Deployment mismatch remains NOTED and NOT repaired (repair is out of scope).

**Reason.** This phase performs no redeployment and no source modification
(REDEPLOYED=NO, SOURCE_MODIFIED=NO).

**Effect on classification.** No role is re-classified solely because of the mismatch;
it reinforces that historical Phase 62 login claims against a different deployment are
not current authentication evidence.

---

## Summary

| ID | Roles affected | Decision | Effect |
|----|----------------|----------|--------|
| CON-82-01 | org_admin, head_office | NO_DOCUMENTED_ACCOUNT | no auth claim |
| CON-82-02 | SA-EMP-00041 | excluded (not canonical) | no change to 12 roles |
| CON-82-03 | accountant, librarian, guard, nurse | fixture claims invalid | DOCUMENTED_ACCOUNT_NO_SESSION |
| CON-82-04 | hr, receptionist | name documented, no credential | DOCUMENTED_ACCOUNT_NO_CREDENTIAL |
| CON-82-05 | SA-ST-0002/0003 | stale, retained, not repaired | student already authenticated |
| CON-82-06 | all | mismatch noted, not repaired | reinforces no-auth conclusion |

No contradiction was resolved by creating a session, performing a login, modifying a
fixture, or changing credentials/permissions.