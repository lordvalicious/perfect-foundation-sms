# PHASE 85 — AUTHORIZATION MATRIX

**Generated:** 2026-09-24  
**Phase:** 85 — Five-Role End-to-End Authorization Proof  
**Repository:** perfect-foundation-sms  
**Branch:** master  
**HEAD:** 2df1989

---

## Authorization Matrix

| Role | Account Found | Authenticated | Primary Role Proven | Intended Read Access | Expected Denial | Frontend/Backend Consistent | Final State |
|------|--------------|---------------|---------------------|----------------------|----------------|------------------------------|-------------|
| counsellor | ❌ NO | ❌ NO | ❌ NO | ❌ NOT TESTED | ❌ NOT TESTED | UNKNOWN | AUTHENTICATION_BLOCKED |
| guard | ❌ NO | ❌ NO | ❌ NO | ❌ NOT TESTED | ❌ NOT TESTED | UNKNOWN | AUTHENTICATION_BLOCKED |
| nurse | ⚠️ HISTORICAL (SA-EMP-00002) | ❌ NO | ❌ NO | ❌ NOT TESTED | ❌ NOT TESTED | UNKNOWN | AUTHENTICATION_BLOCKED |
| administrative_officer | ⚠️ HISTORICAL (SA-EMP-00041) | ❌ NO | ❌ NO | ❌ NOT TESTED | ❌ NOT TESTED | UNKNOWN | AUTHENTICATION_BLOCKED |
| librarian | ⚠️ HISTORICAL (SA-EMP-00011) | ❌ NO | ❌ NO | ❌ NOT TESTED | ❌ NOT TESTED | UNKNOWN | AUTHENTICATION_BLOCKED |

---

## Detailed Evidence per Role

### 1. COUNSELLOR

| Check | Status | Evidence |
|-------|--------|----------|
| Account exists in production | UNKNOWN | No session fixture; no documented account in Phase 83 |
| Legitimate authentication possible | ❌ NO | No sa_counsellor*.txt in P43_SESSIONS_DIR |
| /api/auth/me/ returns primary_role=counsellor | NOT TESTED | AUTHENTICATION_BLOCKED |
| Backend read-only access (helpdesk, announcements) | NOT TESTED | Requires authenticated session |
| Frontend nav shows Helpdesk | NOT TESTED | Requires authenticated session |
| Expected denial (admin/finance endpoints) | NOT TESTED | Requires authenticated session |
| Frontend/Backend consistency | UNKNOWN | Cannot verify without auth |

**Phase 84 Source Fix Status (Local Only):**
- ✅ Role enum: `COUNSELLOR = "counsellor"`
- ✅ ROLE_RANK: 42
- ✅ primary_role priority: includes COUNSELLOR after HR
- ✅ DESIGNATION_ROLE_MAP: "counsellor" → "counsellor"
- ✅ IsStaffRole / IsAcademicMemberRole: includes "counsellor"
- ✅ Frontend Helpdesk nav/route: includes "counsellor"
- ⚠️ NOT DEPLOYED — production serves stale code

---

### 2. GUARD (Security Guard)

| Check | Status | Evidence |
|-------|--------|----------|
| Account exists in production | UNKNOWN | No session fixture; no documented account in Phase 83 |
| Legitimate authentication possible | ❌ NO | No sa_guard*.txt in P43_SESSIONS_DIR |
| /api/auth/me/ returns primary_role=guard | NOT TESTED | AUTHENTICATION_BLOCKED |
| Backend read-only access (helpdesk, visitors, digital-ids) | NOT TESTED | Requires authenticated session |
| Frontend nav shows Helpdesk, Visitors, Digital IDs | NOT TESTED | Requires authenticated session |
| Expected denial (admin/finance/library endpoints) | NOT TESTED | Requires authenticated session |
| Frontend/Backend consistency | UNKNOWN | Cannot verify without auth |

**Phase 84 Source Fix Status (Local Only):**
- ✅ Role enum: `GUARD = "guard"` (existed)
- ✅ ROLE_RANK: 30 (existed)
- ✅ DESIGNATION_ROLE_MAP: "security guard" → "guard"
- ✅ IsStaffRole: includes "guard" (existed)
- ✅ Frontend Helpdesk/Visitors/Digital IDs nav/route: includes "guard" (existed)
- ⚠️ NOT DEPLOYED — production serves stale code

---

### 3. NURSE

| Check | Status | Evidence |
|-------|--------|----------|
| Account exists in production | ⚠️ HISTORICAL | Username SA-EMP-0002 documented (Phase 57); login requires `school_code` |
| Legitimate authentication possible | ❌ NO | sa_nurse_inst4.txt = invalid 1-field placeholder; no valid session |
| /api/auth/me/ returns primary_role=nurse | NOT TESTED | AUTHENTICATION_BLOCKED |
| Backend read-only access (health-records via IsStaffRole) | NOT TESTED | Requires authenticated session |
| Frontend nav shows Health Records | NOT TESTED | Requires authenticated session |
| Expected denial (admin/finance/library endpoints) | NOT TESTED | Requires authenticated session |
| Frontend/Backend consistency | UNKNOWN | Cannot verify without auth |

**Phase 84 Source Fix Status (Local Only):**
- ✅ Role enum: `NURSE = "nurse"` (existed)
- ✅ ROLE_RANK: 28 (existed)
- ✅ DESIGNATION_ROLE_MAP: "nurse" → "nurse", "lady health worker" → "nurse"
- ✅ IsStaffRole: includes "nurse" (existed)
- ✅ Frontend /health-records route guard: added "nurse", "staff" (TPR-004 fix)
- ✅ Frontend Health Records nav: added "nurse", "staff"
- ⚠️ NOT DEPLOYED — production serves stale code (TPR-004 still active in production)

---

### 4. ADMINISTRATIVE OFFICER

| Check | Status | Evidence |
|-------|--------|----------|
| Account exists in production | ⚠️ HISTORICAL | Username SA-EMP-00041 (Phase 57); historically forced to "staff" |
| Legitimate authentication possible | ❌ NO | No sa_admin_officer*.txt in P43_SESSIONS_DIR |
| /api/auth/me/ returns primary_role=administrative_officer | NOT TESTED | AUTHENTICATION_BLOCKED |
| Backend read-only access (helpdesk, announcements) | NOT TESTED | Requires authenticated session |
| Frontend nav shows Helpdesk | NOT TESTED | Requires authenticated session |
| Expected denial (admin/finance/library endpoints) | NOT TESTED | Requires authenticated session |
| Frontend/Backend consistency | UNKNOWN | Cannot verify without auth |

**Phase 84 Source Fix Status (Local Only):**
- ✅ Role enum: `ADMINISTRATIVE_OFFICER = "administrative_officer"` (NEW)
- ✅ ROLE_RANK: 38 (NEW)
- ✅ primary_role priority: includes ADMINISTRATIVE_OFFICER after Receptionist
- ✅ DESIGNATION_ROLE_MAP: "administrative officer" → "administrative_officer"
- ✅ IsStaffRole / IsAcademicMemberRole: includes "administrative_officer"
- ✅ Frontend Helpdesk nav/route: includes "administrative_officer"
- ⚠️ NOT DEPLOYED — production serves stale code

---

### 5. LIBRARIAN

| Check | Status | Evidence |
|-------|--------|----------|
| Account exists in production | ⚠️ HISTORICAL | Username SA-EMP-00011 (Phase 55/57); no valid session |
| Legitimate authentication possible | ❌ NO | sa_librarian.txt = invalid placeholder; no valid session |
| /api/auth/me/ returns primary_role=librarian | NOT TESTED | AUTHENTICATION_BLOCKED |
| Backend read-only access (library via IsLibrarianRole) | NOT TESTED | Requires authenticated session |
| Frontend nav shows Library | NOT TESTED | Requires authenticated session |
| Expected denial (admin/finance/health endpoints) | NOT TESTED | Requires authenticated session |
| Frontend/Backend consistency | UNKNOWN | Cannot verify without auth |

**Phase 84 Source Fix Status (Local Only):**
- ✅ Role enum: `LIBRARIAN = "librarian"` (existed)
- ✅ ROLE_RANK: 35 (existed)
- ✅ primary_role priority: **ADDED LIBRARIAN** (was omitted — Phase 83 CON-83-01)
- ✅ DESIGNATION_ROLE_MAP: "librarian" → "librarian"
- ✅ IsLibrarianRole: includes "librarian" (existed)
- ✅ Frontend Library nav/route: includes "librarian" (existed)
- ⚠️ NOT DEPLOYED — production serves stale code

---

## Deployment Blocking Factor

| Factor | Status | Impact |
|--------|--------|--------|
| Phase 84 deployed to production | ❌ NO | All backend/frontend guards serve stale code |
| Vercel deployment authorization | ❌ NOT GRANTED | Phase 84 P17: explicit authorization required |
| Production revision verification | ❌ UNKNOWN | Cannot query Vercel without dashboard/CLI access |
| DEPLOYMENT_BLOCKED | **YES** | All five roles blocked at deployment level |

---

## Final State Classification

Per Phase 85 rules, the only valid final states when authentication is unavailable:

- **AUTHENTICATION_BLOCKED** — legitimate session unavailable (all 5 roles)
- **DEPLOYMENT_BLOCKED** — Phase 84 not deployed (all 5 roles)

**All five roles: AUTHENTICATION_BLOCKED + DEPLOYMENT_BLOCKED**

No role can be classified as FULLY_CERTIFIED, PARTIALLY_PROVEN, or any proven state without:
1. Phase 84 deployed to production
2. Legitimate session fixtures for the five accounts
3. Successful authentication and /api/auth/me/ verification