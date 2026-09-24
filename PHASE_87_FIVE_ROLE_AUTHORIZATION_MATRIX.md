# PHASE 87 — FIVE-ROLE AUTHORIZATION MATRIX

**Generated:** 2026-09-24  
**Phase:** 87 — Five-Role Production Deployment + Authentication Unblock + Read-Only E2E Proof  
**Repository:** perfect-foundation-sms  
**Branch:** master  
**HEAD:** 7357c18  
**Deployment Status:** BLOCKED  

---

## Authorization Matrix

| Role | Account Found | Authenticated | Primary Role Proven | Intended Read Access | Expected Denial | Frontend/Backend Consistent | Final State |
|------|--------------|---------------|---------------------|----------------------|----------------|------------------------------|-------------|
| counsellor | ❌ | ❌ | ❌ | NOT TESTED | NOT TESTED | UNKNOWN | AUTHENTICATION_BLOCKED |
| guard | ❌ | ❌ | ❌ | NOT TESTED | NOT TESTED | UNKNOWN | AUTHENTICATION_BLOCKED |
| nurse | ⚠️ Historical | ❌ | ❌ | NOT TESTED | NOT TESTED | UNKNOWN | AUTHENTICATION_BLOCKED |
| administrative_officer | ⚠️ Historical | ❌ | ❌ | NOT TESTED | NOT TESTED | UNKNOWN | AUTHENTICATION_BLOCKED |
| librarian | ⚠️ Historical | ❌ | ❌ | NOT TESTED | NOT TESTED | UNKNOWN | AUTHENTICATION_BLOCKED |

---

## Phase 84 Source Implementation Status (Local — Not Deployed)

| Component | Status | Detail |
|-----------|--------|--------|
| Role enum | ✅ | COUNSELLOR, ADMINISTRATIVE_OFFICER added |
| ROLE_RANK | ✅ | COUNSELLOR=42, ADMINISTRATIVE_OFFICER=38 |
| primary_role priority | ✅ | ORG_ADMIN, HEAD_OFFICE, COUNSELLOR, ADMINISTRATIVE_OFFICER, LIBRARIAN added |
| DESIGNATION_ROLE_MAP | ✅ | 6 mappings + safe default=staff |
| role_for_designation() | ✅ | Deterministic, case-insensitive |
| _build_user_account fix | ✅ | Uses role_for_designation() |
| IsStaffRole / IsAcademicMemberRole | ✅ | counsellor, administrative_officer added |
| /health-records FE guard | ✅ | nurse + staff added (TPR-004) |
| Health Records FE nav | ✅ | nurse + staff added |
| Helpdesk FE guard/nav | ✅ | counsellor + administrative_officer added |
| Migration | ✅ | 0016_alter_role_choices generated |

---

## Role-Specific Source Fix Verification (Local Only — Not Deployed)

### 1. counsellor
- ✅ Role enum: `COUNSELLOR = "counsellor"`
- ✅ ROLE_RANK: 42
- ✅ primary_role priority: after HR, before Receptionist
- ✅ DESIGNATION_ROLE_MAP: "counsellor" → "counsellor"
- ✅ IsStaffRole: includes "counsellor"
- ✅ IsAcademicMemberRole: includes "counsellor"
- ✅ Frontend Helpdesk nav/route: includes "counsellor"

### 2. guard
- ✅ Role enum: `GUARD = "guard"` (existed)
- ✅ ROLE_RANK: 30 (existed)
- ✅ DESIGNATION_ROLE_MAP: "security guard" → "guard"
- ✅ IsStaffRole: includes "guard" (existed)
- ✅ Frontend Helpdesk/Visitors/Digital IDs nav/route: includes "guard" (existed)

### 3. nurse
- ✅ Role enum: `NURSE = "nurse"` (existed)
- ✅ ROLE_RANK: 28 (existed)
- ✅ DESIGNATION_ROLE_MAP: "nurse" → "nurse", "lady health worker" → "nurse"
- ✅ IsStaffRole: includes "nurse" (existed)
- ✅ Frontend /health-records route guard: added "nurse", "staff" (TPR-004)
- ✅ Frontend Health Records nav: added "nurse", "staff"

### 4. administrative_officer
- ✅ Role enum: `ADMINISTRATIVE_OFFICER = "administrative_officer"` (NEW)
- ✅ ROLE_RANK: 38 (NEW)
- ✅ primary_role priority: after Receptionist, before Librarian
- ✅ DESIGNATION_ROLE_MAP: "administrative officer" → "administrative_officer"
- ✅ IsStaffRole: includes "administrative_officer"
- ✅ IsAcademicMemberRole: includes "administrative_officer"
- ✅ Frontend Helpdesk nav/route: includes "administrative_officer"

### 5. librarian
- ✅ Role enum: `LIBRARIAN = "librarian"` (existed)
- ✅ ROLE_RANK: 35 (existed)
- ✅ primary_role priority: **ADDED LIBRARIAN** (was omitted — Phase 83 CON-83-01)
- ✅ DESIGNATION_ROLE_MAP: "librarian" → "librarian"
- ✅ IsLibrarianRole: includes "librarian" (existed)
- ✅ Frontend Library nav/route: includes "librarian" (existed)

---

## Deployment Blocking Factor

| Factor | Status | Impact |
|--------|--------|--------|
| Phase 84 deployed to production | ❌ NO | All backend/frontend guards serve stale code |
| Vercel/Render deployment access | ❌ NOT AVAILABLE | Cannot deploy or verify deployed revision |
| DEPLOYMENT_BLOCKED | **YES** | All five roles blocked at deployment level |

---

## Final State Classification

Per Phase 87 rules, with DEPLOYMENT_BLOCKED + AUTHENTICATION_BLOCKED:

- **AUTHENTICATION_BLOCKED** — legitimate session unavailable (all 5 roles)
- **DEPLOYMENT_BLOCKED** — Phase 84 not deployed (all 5 roles)

**All five roles: AUTHENTICATION_BLOCKED + DEPLOYMENT_BLOCKED**

No role can be classified as AUTHENTICATED_PROVEN or READ_ONLY_PROVEN without:
1. Phase 84 deployed to production
2. Legitimate session fixtures for the five accounts
3. Successful authentication and /api/auth/me/ verification