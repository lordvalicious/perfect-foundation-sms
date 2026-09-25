# PHASE 96.9 STAGE B - FIVE-ROLE PROVISIONING EXECUTION RESULT

Generated: 2026-09-25
Authorized: Owner-approved Phase 96.9 Stage B (POST /api/staff/ only)
Gate: READY FOR FIVE-ROLE E2E

## Executive summary

Exactly five dedicated production E2E accounts were provisioned via the sole sanctioned path
`POST /api/staff/` (StaffProfileCRUDSerializer, `create_account=True`), one at a time, each
verified before proceeding. All five were created with HTTP 201 and each authenticated through
the normal login flow (`POST /api/auth/login/` with `school_code=PF-CLEMD`) with
`primary_role` and `username` confirmed via `GET /api/auth/me/` (HTTP 200).

- Final: 5/5 accounts provisioned and auth-verified
- Scope: Default Institution (id 1, code PF-CLEMD), primary_campus 7 (existing campus)
- Identifiers: DI-EMP-0002 .. DI-EMP-0006 (auto-generated, no collision)
- No new school, campus, organization, permission, or unrelated user was created
- No source/authorization/migration/Vercel/secret changes; no demo seed; no deletes/resets
- POSTED ONLY via /api/staff/; one random secure temp password per account, returned once,
  retained ONLY in the authorized runtime environment (never in terminal, reports, or commits)

## Delivered accounts (non-secret identifiers only)

| ROLE                     | Username                     | staff profile id | employee# | verified primary_role        | designations |
|--------------------------|------------------------------|------------------|-----------|------------------------------|--------------|
| COUNSELLOR               | e2e.counsellor               | 117              | DI-EMP-0002| counsellor                   | Counsellor   |
| GUARD                    | e2e.guard                    | 118              | DI-EMP-0003| guard                        | Security Guard|
| NURSE                    | e2e.nurse                    | 119              | DI-EMP-0004| nurse                        | Nurse        |
| ADMINISTRATIVE_OFFICER   | e2e.administrative_officer   | 120              | DI-EMP-0005| administrative_officer       | Administrative Officer |
| LIBRARIAN                | e2e.librarian                | 121              | DI-EMP-0006| librarian                    | Librarian    |

Each account: one StaffProfile + one User + InstitutionMembership + exactly one RoleAssignment
(role from `role_for_designation`/DESIGNATION_ROLE_MAP). must_change_password=True (secure
14-char temp password, returned exactly once). No shared/deterministic credentials.

## Execution log (chronological, high-level)

1. Reconfirmed state: HEAD == origin/master == cd00325, tracked worktree clean.
2. Session channel: valid production admin session (FrostFire super_admin, active institution
   Default/PF-CLEMD) loaded from authorized runtime dir; CSRF acquired via GET /api/auth/csrf/.
3. Collision pre-check per role: full paginated staff list scanned for intended username and
   deterministic fallback email; no e2e.* username or email present. COUNSELLOR created first,
   followed by the remaining roles in order. (An internal script traceback occurred after
   COUNSELLOR; the run was made resumable and COUNSELLOR was re-verified from its retained temp
   password before any further role was created - no partial/duplicate account ever existed.)
4. Each role: POST /api/staff/ (201) -> capture temp password into runtime env -> fresh session
   login with school_code PF-CLEMD -> GET /api/auth/me/ -> assert primary_role == intended role
   and username == intended username. Proceed to next role only after pass.
5. Order executed: COUNSELLOR -> GUARD -> NURSE -> ADMINISTRATIVE_OFFICER -> LIBRARIAN.
6. Post-checks: backend health 200 (database ok, deploy_version 63-test-3 - unchanged); git status
   shows only pre-existing untracked phase deliverables (no tracked modifications); exactly five
   new DI-EMP-* staff records accounted for.

## Verification summary matrix

| Check                          | Result |
|--------------------------------|--------|
| Account exists (profile row)   | YES 5/5 (ids 117-121) |
| Linked user account (account)  | YES 5/5 (usernames e2e.*) |
| Role assignment                | EXPECTED 5/5 (counsellor/guard/nurse/administrative_officer/librarian) |
| E2E identity (dedicated, non-personal test handle) | YES 5/5 |
| Auth via normal login flow     | YES 5/5 (login 200, /me 200, must_change_password honored) |
| No unrelated user touched      | confirmed |
| Health after provisioning      | 200 {"status":"ok","database":{"ok":true,"error":null}} |

## Security & compliance

- No password, cookie, secret, or session value appears in this report, the matrix CSV, or the
  machine summary. Temp passwords live only in the authorized runtime credential file
  (outside this repository) and were never echoed.
- No demo_seed, no repo-root provisioning scripts, no scripts with embedded credentials were used.
- Exactly five accounts were created; nothing else was mutated.

## Cleanup / reversibility

Reverse = delete the five StaffProfile rows (cascade removes linked User, membership,
role assignment), or use staff delete path with admin authorization. Owner sign-off required
before any deletion.

## Files

- PHASE_96_9_STAGE_B_PROVISIONING_RESULT.md (this file)
- PHASE_96_9_STAGE_B_PROVISIONING_MATRIX.csv
- PHASE_96_9_STAGE_B_MACHINE_SUMMARY.txt
- (runtime-only, NOT deliverables) p969_stage_b_credentials.env in authorized temp dir

FINAL GATE: READY FOR FIVE-ROLE E2E