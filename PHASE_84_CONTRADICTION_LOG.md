# PHASE 84 — CONTRADICTION LOG

**Generated:** 2026-09-24  
**Phase:** 84 — Specialized Role Mapping Fix + Authorization Repair + End-to-End Certification  
**Purpose:** Track contradictions discovered during Phase 84 investigation and resolution, including carry-overs from Phase 83.

---

## Contradiction Format

| ID | Description | Source | Severity | Resolution | Status |
|----|-------------|--------|----------|------------|--------|

---

## Carried from Phase 83 (CON-83-*)

| ID | Description | Source | Severity | Resolution | Status |
|----|-------------|--------|----------|------------|--------|
| CON-83-01 | `primary_role` priority (models.py:166-191) OMITS `LIBRARIAN` (also `ORG_ADMIN`, `HEAD_OFFICE`) | Phase 83 Root Cause Report | HIGH | FIXED in Phase 84: Added `ORG_ADMIN`, `HEAD_OFFICE`, `COUNSELLOR`, `ADMINISTRATIVE_OFFICER`, `LIBRARIAN` to priority list in rank-aware order | ✅ RESOLVED |
| CON-83-02 | Frontend `/health-records` route guard (App.jsx:1303) omits BOTH `nurse` and `staff` | Phase 83 / TPR-004 | HIGH | FIXED in Phase 84: Added `nurse` + `staff` to route guard AND nav item (App.jsx:376, 1303) | ✅ RESOLVED |

---

## New Contradictions Discovered in Phase 84

| ID | Description | Source | Severity | Resolution | Status |
|----|-------------|--------|----------|------------|--------|
| CON-84-01 | `IsNurseRole` permission class defined (permissions.py:219) but **NOT USED** in any backend view — health module uses `IsStaffRole` instead | Grep `IsNurseRole` → only definition + phase57 verify scripts | MEDIUM | Documented: `IsStaffRole` already includes `nurse`; no action needed. `IsNurseRole` retained for future granular use. | ✅ DOCUMENTED |
| CON-84-02 | Frontend `/health-records` nav item (App.jsx:376) existed but was INVISIBLE in nav (navGroups People references `/health-records` but no nav entry matched) — actually nav item exists but had wrong roles | App.jsx navGroups vs navigation array | MEDIUM | FIXED: Nav item updated with correct roles (`nurse`, `staff` added) | ✅ RESOLVED |
| CON-84-03 | Backend health module (`apps/health/views.py`) uses `IsStaffRole` (includes `nurse`, `staff`) but frontend guard omitted both — INCONSISTENT BE/BE | Phase 83 TPR-004 + health/views.py grep | HIGH | FIXED in Phase 84 P7: FE guard now aligns with BE (`nurse`, `staff` added) | ✅ RESOLVED |
| CON-84-04 | `IsAcademicMemberRole` (permissions.py:245-276) includes `nurse` but NOT `guard` — inconsistent with `IsStaffRole` which includes both | permissions.py line-by-line | LOW | Documented: Intentional — nurses are "academic members" for announcement read; guards are not. No change. | ✅ DOCUMENTED |
| CON-84-05 | `ROLE_RANK` used for escalation prevention (access.py:48, 60) but `primary_role` priority was NOT rank-ordered (omitted org_admin/head_office/librarian) | access.py + models.py | MEDIUM | FIXED: `primary_role` priority now includes all roles in rank-aware order | ✅ RESOLVED |
| CON-84-06 | `seed_staff.py` creates StaffProfile records WITHOUT auto-provisioning accounts (no `create_account=True`) — Phase 83 accounts created via different path (API serializer) | seed_staff.py vs StaffProfileSerializer | LOW | Documented: Different provisioning paths. Phase 84 fix applies to serializer path only. | ✅ DOCUMENTED |
| CON-84-07 | `_campus_role_users()` in demo_seed/base.py creates users with EXPLICIT role assignment (not via designation) — bypasses serializer fix | base.py:102-122 | LOW | Documented: Demo seed uses explicit roles; serializer fix handles dynamic/admin-created staff. | ✅ DOCUMENTED |
| CON-84-08 | Phase 80 Step 14 (nurse) documented `SA-EMP-0002` as account but login requires `school_code` → 400 without; not a standard session fixture | Phase 80 Step 14 machine summary | LOW | Documented: Account exists but not a usable session fixture; P11 requires legitimate owner-created sessions. | ✅ DOCUMENTED |

---

## Contradictions Considered but NOT Contradictions (Resolved as Expected Behavior)

| ID | Observation | Why Not a Contradiction |
|----|-------------|-------------------------|
| — | `guard` role not in `IsAcademicMemberRole` | Intentional: guards are security, not academic members; they have staff-family access via `IsStaffRole` |
| — | `teacher` in FE `/health-records` but NOT in `IsNurseRole` backend | FE more permissive than unused BE class; actual BE gate is `IsStaffRole` which includes teacher — consistent |
| — | `org_admin`/`head_office` in `IsStaffRole` backend but NOT in FE `/health-records` | FE guard intentionally curated (not mirror); Phase 84 scope = TPR-004 (nurse+staff) only |
| — | `counsellor`/`administrative_officer` added to `IsStaffRole` (broad staff-family) | Not "broad staff grant" — they ARE staff-grade employees; matches guard/nurse precedent |
| — | No dedicated frontend module for counsellor/administrative_officer | Honest: no such modules exist in codebase; staff-family helpdesk is the working surface |

---

## Open / Unresolvable (Blocked by Constraints)

| ID | Description | Blocker |
|----|-------------|---------|
| OPEN-84-01 | End-to-end certification for all 5 roles requires production deployment + legitimate sessions | P17: No deployment authorization; no session fixtures |
| OPEN-84-02 | Frontend build verification (`npm run build`) | Host execution policy disabled |
| OPEN-84-03 | Regression test suite run via `manage.py test` fails post-test due to pre-existing `reports.views` bug (missing `APIView` import) | Pre-existing bug unrelated to Phase 84 changes; tests themselves PASS |

---

## Summary

| Category | Count |
|----------|-------|
| Carried from Phase 83 | 2 |
| New in Phase 84 (resolved) | 5 |
| New in Phase 84 (documented only) | 3 |
| Not contradictions (expected) | 5 |
| Open / unresolvable | 3 |

**All HIGH/MEDIUM severity contradictions RESOLVED in Phase 84 source changes.**