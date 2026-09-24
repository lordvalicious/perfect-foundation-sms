# PHASE 84 — ROLE AUTHORIZATION MATRIX

**Generated:** 2026-09-24  
**Repository:** perfect-foundation-sms  
**Branch:** master  
**HEAD:** 2df1989 ("Add Phase 80 and Phase 81 documentation and certification files")  
**Phase 84 Scope:** Fix Phase 83 root cause (hardcoded Role.STAFF in serializer) + add canonical roles + repair FE/BE authorization + prove full chain for 5 specialized accounts.

---

## Executive Summary

| Role (Canonical) | Account Login | /api/auth/me | Canonical Role Returned | Role-Specific API Access | Frontend Page Access | Result |
|------------------|---------------|--------------|------------------------|--------------------------|---------------------|--------|
| **Counsellor** | No documented session fixture | N/A (BLOCKED) | Would return `counsellor` | Helpdesk (staff-family) | Helpdesk (nav + route) | **BLOCKED** — no legitimate session available for E2E |
| **Security Guard** | No documented session fixture | N/A (BLOCKED) | Would return `guard` | Helpdesk, Visitors, Digital IDs | Helpdesk, Visitors (existing nav/route ✓) | **BLOCKED** — no legitimate session available for E2E |
| **Nurse** | SA-EMP-0002 (requires `school_code`) | N/A (BLOCKED) | Would return `nurse` | Health Records (IsStaffRole backend) | Health Records (nav + route FIXED) | **BLOCKED** — no legitimate session fixture |
| **Administrative Officer** | No documented session fixture | N/A (BLOCKED) | Would return `administrative_officer` | Helpdesk (staff-family) | Helpdesk (nav + route FIXED) | **BLOCKED** — no legitimate session available for E2E |
| **Librarian** | SA-EMP-00011 (no session fixture) | N/A (BLOCKED) | Would return `librarian` | Library (IsLibrarianRole backend) | Library (existing nav/route ✓) | **BLOCKED** — no legitimate session available for E2E |

**BLOCKED Reason (all 5):** Per Phase 84 P17, production E2E requires a deployment. Local HEAD 2df1989 is not deployed (production serves stale commits dbb2d95c / 56e4b21b). No legitimate owner-created sessions for the 5 Phase 83 accounts exist in `P43_SESSIONS_DIR`. Tests cannot fabricate credentials/sessions. All 5 roles marked **BLOCKED** with exact reason: *"No legitimate session fixture available; production deployment required for E2E but not authorized (P17); source-only verification = PASS for implementation, BLOCKED for end-to-end certification."*

---

## Detailed Per-Role Evidence

### 1. Counsellor (NEW canonical role: `counsellor`, rank 42)

| Aspect | Status | Evidence |
|--------|--------|----------|
| Role enum entry | ✅ ADDED | `models.py` L18: `COUNSELLOR = "counsellor", "Counsellor / Student Counselor"` |
| ROLE_RANK | ✅ ADDED | `models.py` L47: `Role.COUNSELLOR: 42` (between HR 45 and Receptionist 40) |
| Designation map | ✅ ADDED | `services.py`: `"counsellor" -> "counsellor"` |
| Serializer fix | ✅ FIXED | `serializers.py` L354: `role=role_for_designation(staff.designation)` |
| primary_role priority | ✅ FIXED | `models.py` L184: inserted after HR, before Receptionist |
| Backend permission | ✅ ADDED | `IsStaffRole.roles` + `IsAcademicMemberRole.roles` (staff-family) |
| Frontend route | ✅ ADDED | `/helpdesk` route + nav: added `counsellor` |
| Role-specific module | ⚠️ NONE | No dedicated counsellor module in codebase; uses staff-family (helpdesk) |
| Session fixture | ❌ MISSING | No `sa_counsellor*.txt` in `P43_SESSIONS_DIR` |

### 2. Security Guard (existing canonical role: `guard`, rank 30)

| Aspect | Status | Evidence |
|--------|--------|----------|
| Role enum entry | ✅ EXISTED | `models.py` L24: `GUARD = "guard", "Security Guard"` |
| ROLE_RANK | ✅ EXISTED | `models.py` L51: `Role.GUARD: 30` |
| Designation map | ✅ ADDED | `services.py`: `"security guard" -> "guard"` |
| Serializer fix | ✅ FIXED | `serializers.py` L354: resolves via `role_for_designation` |
| primary_role priority | ✅ UNCHANGED | Already in priority (after Librarian) |
| Backend permission | ✅ EXISTED | `IsStaffRole.roles` (includes guard) |
| Frontend route | ✅ EXISTED | `/helpdesk`, `/visitors`, `/digital-ids` all include guard |
| Role-specific module | ✅ COVERED | Helpdesk, Visitors, Digital IDs |
| Session fixture | ❌ MISSING | No `sa_guard*.txt` in `P43_SESSIONS_DIR` |

### 3. Nurse (existing canonical role: `nurse`, rank 28)

| Aspect | Status | Evidence |
|--------|--------|----------|
| Role enum entry | ✅ EXISTED | `models.py` L25: `NURSE = "nurse", "Nurse / Medical Officer"` |
| ROLE_RANK | ✅ EXISTED | `models.py` L52: `Role.NURSE: 28` |
| Designation map | ✅ ADDED | `services.py`: `"nurse" -> "nurse"`, `"lady health worker" -> "nurse"` |
| Serializer fix | ✅ FIXED | `serializers.py` L354: resolves via `role_for_designation` |
| primary_role priority | ✅ UNCHANGED | Already in priority (after Guard) |
| Backend permission | ✅ EXISTED | `IsStaffRole.roles` (includes nurse); `IsNurseRole` defined but unused |
| Frontend route | ✅ FIXED (P7) | `/health-records`: added `nurse` + `staff` (TPR-004) |
| Frontend nav | ✅ FIXED (P8) | Health Records nav: added `nurse` + `staff` |
| Role-specific module | ✅ COVERED | Health Records |
| Session fixture | ❌ MISSING | `sa_nurse_inst4.txt` invalid; `SA-EMP-0002` requires `school_code` |

### 4. Administrative Officer (NEW canonical role: `administrative_officer`, rank 38)

| Aspect | Status | Evidence |
|--------|--------|----------|
| Role enum entry | ✅ ADDED | `models.py` L23: `ADMINISTRATIVE_OFFICER = "administrative_officer", "Administrative Officer"` |
| ROLE_RANK | ✅ ADDED | `models.py` L49: `Role.ADMINISTRATIVE_OFFICER: 38` (between Receptionist 40 and Librarian 35) |
| Designation map | ✅ ADDED | `services.py`: `"administrative officer" -> "administrative_officer"` |
| Serializer fix | ✅ FIXED | `serializers.py` L354: `role=role_for_designation(staff.designation)` |
| primary_role priority | ✅ FIXED | `models.py` L186: inserted after Receptionist, before Librarian |
| Backend permission | ✅ ADDED | `IsStaffRole.roles` + `IsAcademicMemberRole.roles` (staff-family) |
| Frontend route | ✅ ADDED | `/helpdesk` route + nav: added `administrative_officer` |
| Role-specific module | ⚠️ NONE | No dedicated admin-officer module; uses staff-family (helpdesk) |
| Session fixture | ❌ MISSING | No `sa_admin_officer*.txt` in `P43_SESSIONS_DIR`; historical SA-EMP-00041 forced to staff |

### 5. Librarian (existing canonical role: `librarian`, rank 35)

| Aspect | Status | Evidence |
|--------|--------|----------|
| Role enum entry | ✅ EXISTED | `models.py` L24: `LIBRARIAN = "librarian", "Librarian"` |
| ROLE_RANK | ✅ EXISTED | `models.py` L50: `Role.LIBRARIAN: 35` |
| Designation map | ✅ ADDED | `services.py`: `"librarian" -> "librarian"` |
| Serializer fix | ✅ FIXED | `serializers.py` L354: resolves via `role_for_designation` |
| primary_role priority | ✅ FIXED (P4) | `models.py` L187: **added LIBRARIAN** (was OMITTED in Phase 83) |
| Backend permission | ✅ EXISTED | `IsLibrarianRole.roles` (includes librarian) |
| Frontend route | ✅ EXISTED | `/library` route + nav: includes librarian |
| Role-specific module | ✅ COVERED | Library |
| Session fixture | ❌ MISSING | `sa_librarian.txt` invalid; SA-EMP-00011 no session |

---

## Cross-Cutting Fixes

| Fix Area | Change | Rationale |
|----------|--------|-----------|
| **Serializer root cause** | `_build_user_account`: `Role.STAFF` → `role_for_designation(staff.designation)` | Phase 83: ALL staff-created accounts forced to `staff` |
| **Designation resolver** | New `role_for_designation()` in `services.py` | Deterministic, case/whitespace-insensitive, safe default=staff |
| **ROLE_RANK new roles** | COUNSELLOR=42, ADMINISTRATIVE_OFFICER=38 | Documented: peer-group placement, no privilege escalation |
| **primary_role priority** | Added ORG_ADMIN, HEAD_OFFICE, COUNSELLOR, ADMINISTRATIVE_OFFICER, LIBRARIAN | Phase 83: librarian + org_admin + head_office OMITTED |
| **IsStaffRole** | Added `counsellor`, `administrative_officer` | Staff-grade employees get staff-family access (match guard/nurse precedent) |
| **IsAcademicMemberRole** | Added `counsellor`, `administrative_officer` | Member-level access (announcements read, helpdesk read) |
| **FE /health-records** | Added `nurse`, `staff` (route + nav) | TPR-004: nurse+staff omitted; backend IsStaffRole allows both |
| **FE Helpdesk** | Added `counsellor`, `administrative_officer` (route + nav) | Staff-grade nav visibility for new roles |
| **Migration** | `accounts.0016_alter_role_choices` | Choices-only (TextChoices), no schema change; max_length=30 fits new values |

---

## Negative / Least-Privilege Verification

| Scenario | Expected | Verified |
|----------|----------|----------|
| Counsellor → IsAdminRole / IsAccountantRole / IsFinanceReaderRole | DENIED | ✅ Not added to any admin/finance/teacher-class lists |
| Administrative Officer → IsAdminRole / finance | DENIED | ✅ Not added |
| Nurse → IsLibrarianRole / IsFinanceReaderRole | DENIED | ✅ Nurse NOT in those lists (only IsStaffRole/IsNurseRole) |
| Guard → IsLibrarianRole / finance | DENIED | ✅ Guard NOT in those lists |
| Unknown designation (e.g., "Janitor") → staff (never specialized) | staff | ✅ `role_for_designation` default = Role.STAFF |
| Known-good roles (super_admin, principal, teacher, student, staff) | Unchanged | ✅ Serializer path unused for these; explicit role assignment paths untouched |

---

## Existing-Role Regression (Phase 84 P16)

| Role | /api/auth/me | Primary Role | Staff-Family Access | Admin Access | Result |
|------|--------------|--------------|---------------------|--------------|--------|
| super_admin | super_admin | super_admin | ✅ | ✅ | ✅ PASS (source) |
| principal | principal | principal | ✅ | ✅ | ✅ PASS (source) |
| teacher | teacher | teacher | ✅ | ❌ (correct) | ✅ PASS (source) |
| student | student | student | ❌ (correct) | ❌ (correct) | ✅ PASS (source) |
| staff | staff | staff | ✅ | ❌ (correct) | ✅ PASS (source) |

*Note: Source-verified only; no live session fixtures for E2E.*

---

## Production Safety (Phase 84 P17-18)

| Check | Status | Detail |
|-------|--------|--------|
| No production deployment | ✅ | Local HEAD 2df1989 ≠ production deployments |
| No production migrations | ✅ | Migration `accounts.0016_alter_role_choices` generated/applied locally only |
| No password resets | ✅ | Not performed |
| No debug code / bypasses | ✅ | Clean diff |
| No secrets disclosed | ✅ | No passwords/tokens in changes |
| Sessions fabricated | 0 | No test created/fabricated sessions |
| Redeployments | 0 | None performed |

---

## Legend

- ✅ = Implemented and source-verified
- ⚠️ = Partial (no dedicated module, but staff-family access works)
- ❌ = Missing / Not available
- **BLOCKED** = Cannot complete E2E certification due to P17 deployment gate + missing legitimate session fixtures
- **PASS (source)** = Source code implements the correct behavior; E2E not possible per constraints