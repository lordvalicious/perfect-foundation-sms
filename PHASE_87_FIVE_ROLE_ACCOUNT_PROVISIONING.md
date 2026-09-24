# PHASE 87 — FIVE-ROLE ACCOUNT PROVISIONING

**Generated:** 2026-09-24  
**Phase:** 87 — Five-Role Production Deployment + Authentication Unblock + Read-Only E2E Proof  
**Repository:** perfect-foundation-sms  
**Branch:** master  
**HEAD:** 7357c18  
**Deployment Status:** BLOCKED  

---

## Provisioning Status

**DEPLOYMENT_BLOCKED** — Phase 84 code not deployed to production.  
Cannot provision accounts without deployed application.

---

## Required Accounts (Not Provisioned)

| Role | Canonical Value | Account Status | Provisioning Path |
|------|----------------|----------------|-------------------|
| **Counsellor** | counsellor | NOT PROVISIONED | StaffProfileSerializer.create(create_account=True) with designation="Counsellor" |
| **Guard** | guard | NOT PROVISIONED | StaffProfileSerializer.create(create_account=True) with designation="Security Guard" |
| **Nurse** | nurse | NOT PROVISIONED | StaffProfileSerializer.create(create_account=True) with designation="Nurse" |
| **Administrative Officer** | administrative_officer | NOT PROVISIONED | StaffProfileSerializer.create(create_account=True) with designation="Administrative Officer" |
| **Librarian** | librarian | NOT PROVISIONED | StaffProfileSerializer.create(create_account=True) with designation="Librarian" |

---

## Provisioning Mechanism (When Deployed)

Per Phase 84 implementation, accounts are created via:

```python
# StaffProfileSerializer.create()
# 1. Creates StaffProfile with designation field
# 2. If create_account=True: calls _build_user_account()
# 3. _build_user_account() calls create_user_with_username()
# 4. Creates InstitutionMembership
# 5. Creates RoleAssignment via role_for_designation(staff.designation)
```

**Expected role resolution:**
- "Counsellor" → `counsellor` (NEW)
- "Security Guard" → `guard`
- "Nurse" → `nurse`
- "Administrative Officer" → `administrative_officer` (NEW)
- "Librarian" → `librarian`

---

## Current Status

| Role | Account Exists | Provisioned | Credentials Available | Session Fixture |
|------|---------------|-------------|----------------------|-----------------|
| counsellor | ❌ NO | ❌ NO | ❌ NO | ❌ NO |
| guard | ❌ NO | ❌ NO | ❌ NO | ❌ NO |
| nurse | ❌ NO (historical SA-EMP-0002) | ❌ NO | ❌ NO | ❌ NO |
| administrative_officer | ❌ NO (historical SA-EMP-00041) | ❌ NO | ❌ NO | ❌ NO |
| librarian | ❌ NO (historical SA-EMP-00011) | ❌ NO | ❌ NO | ❌ NO |

**All five roles: NOT PROVISIONED — DEPLOYMENT_BLOCKED prevents account creation**

---

## Blocking Factor

**DEPLOYMENT_BLOCKED** — Phase 84 code not deployed to production.  
Cannot access `/api/accounts/staff/` or admin UI to create accounts.  
Cannot verify role assignment via `/api/auth/me/` without deployed backend.

---

## Required to Unblock

1. Deploy Phase 84 code (HEAD 7357c18) to production via Render + Vercel
2. Access production admin UI or API to create StaffProfile records with:
   - `create_account=True`
   - Appropriate `designation` for each role
3. Verify RoleAssignment created with correct canonical role via `/api/auth/me/`
4. Capture legitimate session fixtures for E2E testing