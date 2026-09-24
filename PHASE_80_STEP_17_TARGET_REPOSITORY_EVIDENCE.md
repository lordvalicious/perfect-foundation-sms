# PHASE 80 — STEP 17 — TARGET REPOSITORY EVIDENCE

**Target positively identified (read-only inspection, no modifications).**

## Repository
- **Path:** `C:\Users\Ryuk\Documents\perfect-foundation-sms`
- **Git:** yes — branch `master`
- **HEAD:** `4306570` — "Add Phase 78 deployment identity verification and remediation plan documents"
- **Layout:** `backend/`, `frontend/`, `e2e/`, `demo_data/`, `docs/`, `tools/`, `.vercel/`

## Why it is the Phase 78–80 target
1. Git history carries the Phase workflow: HEAD commit names Phase 78; log includes
   Phase 65 deployment verification commits.
2. Full artifact lineage PHASE_31 → PHASE_79 present at repo root, including the exact
   deliverable file families required by this certification exercise.
3. `PHASE_80_STEP_15_parent_*` files exist (MACHINE_SUMMARY.txt, MODULE_MATRIX.csv,
   READONLY_CERTIFICATION.md, ROUTE_MATRIX.csv) — Step 15's `parent` result block
   matches 1:1.
4. Canonical role contract source present:
   `backend/apps/accounts/models.py`

## Canonical role ordering (Role / ROLE_RANK)
`class Role(models.TextChoices)` (lines 11–29) includes:
SUPER_ADMIN, ADMIN, ORG_ADMIN, HEAD_OFFICE, PRINCIPAL, VICE_PRINCIPAL, CAMPUS_ADMIN,
ACADEMIC, ACCOUNTANT, HR, RECEPTIONIST, LIBRARIAN, GUARD, NURSE, TEACHER, PARENT,
STUDENT, STAFF.

`ROLE_RANK` (lines 34–53):
| Role            | Rank |
|-----------------|------|
| PARENT          | 5    |
| STUDENT         | 10   |
| STAFF           | 20   |
| TEACHER         | 25   |
| NURSE           | 28   |
| GUARD           | 30   |
| LIBRARIAN       | 35   |
| RECEPTIONIST    | 40   |
| HR              | 45   |
| ACCOUNTANT      | 50   |
| ACADEMIC        | 55   |
| CAMPUS_ADMIN    | 60   |
| VICE_PRINCIPAL  | 65   |
| PRINCIPAL       | 70   |
| ADMIN           | 80   |
| HEAD_OFFICE     | 85   |
| ORG_ADMIN       | 90   |
| SUPER_ADMIN     | 100  |

`role_rank(role)` returns `ROLE_RANK.get(role, 0)` at `access.py:33,48-66`.

## Session infrastructure (e2e/helpers/session.js)
- `ROLE_FILES`: SUPER_ADMIN→sa_frostfire.txt, ADMIN→sa_flora.txt,
  TEACHER→sa_SA-EMP-0001.txt, STUDENT→sa_SA-ST-0001.txt, STAFF→sa_DI-staff.txt
- Env var scheme `P43_<ROLE>_SESSIONID`; fallback dir `P43_SESSIONS_DIR`
  with Netscape cookie files (sessionid field, `#HttpOnly_` prefixes handled).
- `e2e/helpers/` also includes `role.js`, `modules.js`, `page.js`, `wait.js`.

## Confirmation vs. Step 16 contradictions
- Contradiction 3 (unknown role ordering) → resolved: PARENT=5 (lowest rank).
- Contradiction 4 (D:\ drive "PERFECT FOUNDATION SMS" folder) → D:\ folder holds a
  report text file, not the source repo; the git-tracked checkout is the authoritative
  target.

## Safety / disclosure note
No session/cookie file contents, credentials, or production route responses were read or
copied into these deliverables — only file existence, names, and structural metadata.
No certification was attempted in Step 17.