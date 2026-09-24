# PHASE 84 — ROOT CAUSE AND FIX REPORT

**Phase:** 84 — Specialized Role Mapping Fix + Authorization Repair + End-to-End Certification  
**Root Cause Source:** Phase 83 Specialized Role Authorization Matrix / Root Cause Report  
**Date:** 2026-09-24  
**Repository:** perfect-foundation-sms  
**Branch:** master  
**HEAD:** 2df1989

---

## 1. Root Cause (Phase 83 Finding)

**Location:** `backend/apps/accounts/serializers.py` lines 349–352 (`_build_user_account` method)

```python
RoleAssignment.objects.get_or_create(
    membership=membership,
    role=Role.STAFF,          # <-- HARDCODED: every staff-created account becomes STAFF
)
```

**Effect:** When `StaffProfileSerializer.create(create_account=True)` is called, the auto-provisioned user account **always** receives `Role.STAFF` regardless of the staff member's `designation` field. Specialized roles (Security Guard, Nurse, Librarian, Counsellor, Administrative Officer) were all silently demoted to generic `staff`.

**Phase 83 Classifications:**
| Designation | Phase 83 Classification | Why |
|-------------|------------------------|-----|
| Counsellor | ROLE_RESOLUTION_FAILURE | No canonical `counsellor` role existed; fell to staff |
| Security Guard | ROLE_MAPPING_FAILURE | `guard` role existed but not mapped from designation |
| Nurse | ROLE_MAPPING_FAILURE + FE guard gap | `nurse` role existed but not mapped; FE /health-records omitted nurse+staff |
| Administrative Officer | ROLE_RESOLUTION_FAILURE | No canonical `administrative_officer` role existed; fell to staff |
| Librarian | ROLE_MAPPING_FAILURE | `librarian` role existed but not mapped from designation |

**Contradictions (Phase 83):**
- CON-83-01: `primary_role` priority OMITS librarian (also org_admin, head_office) — `models.py:166-191`
- CON-83-02: Frontend `/health-records` route guard omits nurse+staff — `App.jsx:1303` (TPR-004)

---

## 2. Fix Design Principles

1. **Deterministic resolution:** Same designation → same role, always.
2. **Case/whitespace-insensitive:** `" Security Guard "`, `"SECURITY GUARD"`, `"security guard"` all map to `guard`.
3. **Safe default:** Unknown designations → generic `staff` (NEVER silent elevation to specialized role).
4. **Least privilege:** New roles granted ONLY staff-family access (helpdesk, announcements read). NO admin/finance/teacher-class grants.
5. **Preserve known-good:** super_admin, principal, teacher, student, staff paths untouched (they don't use `_build_user_account`).
6. **Source-only changes authorized:** Phase 84 P17 forbids production deployment without explicit authorization.

---

## 3. Implementation — Source Changes

### 3.1 New Canonical Roles (models.py)

```python
# Role enum (TextChoices) — additions:
COUNSELLOR = "counsellor", "Counsellor / Student Counselor"
ADMINISTRATIVE_OFFICER = "administrative_officer", "Administrative Officer"

# ROLE_RANK — additions with documented rationale:
Role.COUNSELLOR: 42,           # Between HR(45) and Receptionist(40) — student-services peer
Role.ADMINISTRATIVE_OFFICER: 38,  # Between Receptionist(40) and Librarian(35) — general admin support
```

**Rank rationale:** Placed to group with peer student-services/administration roles without outranking principals/admins; priority order reflects practical dashboard/primary_role precedence.

### 3.2 primary_role Priority Fixed (models.py)

**Before (omitted org_admin, head_office, librarian):**
```python
priority = [
    Role.SUPER_ADMIN, Role.ADMIN, Role.PRINCIPAL, Role.VICE_PRINCIPAL,
    Role.CAMPUS_ADMIN, Role.ACADEMIC, Role.ACCOUNTANT, Role.HR,
    Role.RECEPTIONIST, Role.GUARD, Role.NURSE, Role.TEACHER,
    Role.PARENT, Role.STAFF, Role.STUDENT,
]
```

**After (all roles in rank-aware order):**
```python
priority = [
    Role.SUPER_ADMIN, Role.ORG_ADMIN, Role.HEAD_OFFICE, Role.ADMIN,
    Role.PRINCIPAL, Role.VICE_PRINCIPAL, Role.CAMPUS_ADMIN, Role.ACADEMIC,
    Role.ACCOUNTANT, Role.HR, Role.COUNSELLOR, Role.RECEPTIONIST,
    Role.ADMINISTRATIVE_OFFICER, Role.LIBRARIAN, Role.GUARD, Role.NURSE,
    Role.TEACHER, Role.PARENT, Role.STAFF, Role.STUDENT,
]
```

### 3.3 Canonical Designation → Role Resolver (services.py)

```python
DESIGNATION_ROLE_MAP = {
    "counsellor": "counsellor",
    "security guard": "guard",
    "nurse": "nurse",
    "lady health worker": "nurse",      # Girls' campus synonym (seed_staff.py)
    "administrative officer": "administrative_officer",
    "librarian": "librarian",
}

def role_for_designation(designation):
    normalized = " ".join((designation or "").strip().lower().split())
    role_value = DESIGNATION_ROLE_MAP.get(normalized, Role.STAFF)
    return Role(role_value)
```

**Properties:**
- Deterministic, no side effects
- Normalizes: strips, lowercases, collapses whitespace
- Default = `Role.STAFF` (generic, never elevated)
- Returns `Role` enum member (compatible with `RoleAssignment.role` CharField)

### 3.4 Serializer Fix (serializers.py:317-354)

```python
def _build_user_account(self, staff, username, password):
    from apps.accounts.services import (
        create_user_with_username,
        role_for_designation,          # NEW import
    )
    # ... school resolution ...
    if school is not None:
        membership, _ = InstitutionMembership.objects.get_or_create(...)
        RoleAssignment.objects.get_or_create(
            membership=membership,
            role=role_for_designation(staff.designation),  # FIXED
        )
```

### 3.5 Backend Permission Updates (permissions.py)

**IsStaffRole** (staff-family gate for helpdesk, visitors, digital-ids, health, documents):
```python
roles = [
    "super_admin", "admin", "org_admin", "head_office", "principal",
    "vice_principal", "campus_admin", "academic", "accountant", "hr",
    "receptionist", "guard", "nurse",
    "counsellor",                    # NEW
    "administrative_officer",        # NEW
    "teacher", "staff",
]
```

**IsAcademicMemberRole** (member-level: announcements read, helpdesk read, events):
```python
roles = [
    "super_admin", "admin", "principal", "vice_principal", "campus_admin",
    "academic", "accountant", "hr", "receptionist", "nurse",
    "counsellor",                    # NEW
    "administrative_officer",        # NEW
    "teacher", "staff", "parent", "student",
]
```

**No changes to:** IsAdminRole, IsAccountantRole, IsFinanceReaderRole, IsLibrarianRole, IsNurseRole, IsTeacherRole — preserving least privilege.

### 3.6 Frontend Fixes (App.jsx)

| Location | Before | After |
|----------|--------|-------|
| `/health-records` route (L1303) | `["super_admin", "admin", "principal", "vice_principal", "campus_admin", "teacher"]` | + `"nurse", "staff"` (TPR-004) |
| Health Records nav (L376) | roles: `["super_admin", "admin", "principal", "vice_principal", "campus_admin", "teacher"]` | + `"nurse", "staff"` |
| `/helpdesk` route (L1331) | `[..., "guard", "teacher", "staff"]` | + `"counsellor", "administrative_officer"` |
| Helpdesk nav (L408) | `[..., "guard", "teacher", "staff"]` | + `"counsellor", "administrative_officer"` |

### 3.7 Migration

- **File:** `backend/apps/accounts/migrations/0016_alter_role_choices.py` (auto-generated)
- **Type:** Choices-only (TextChoices enum values)
- **Schema impact:** NONE — `RoleAssignment.role` is `CharField(max_length=30, choices=Role.choices)`. New values `'counsellor'` (10 chars) and `'administrative_officer'` (20 chars) fit within 30.
- **Reversible:** Yes — `python manage.py migrate accounts 0015`
- **Data migration:** NONE — no mass-rewrite of existing users; existing `staff` assignments unchanged unless re-provisioned.

---

## 4. Verification Evidence

### Unit Tests (9 tests PASS — `DesignationRoleMappingRegressionTests`)

| Test | Designation | Expected Role | Result |
|------|-------------|---------------|--------|
| `test_counsellor_maps_to_counsellor_role` | "Counsellor" | counsellor | ✅ |
| `test_security_guard_maps_to_guard_role` | "Security Guard" | guard | ✅ |
| `test_nurse_maps_to_nurse_role` | "Nurse" | nurse | ✅ |
| `test_lady_health_worker_maps_to_nurse_role` | "Lady Health Worker" | nurse | ✅ |
| `test_administrative_officer_maps_to_administrative_officer_role` | "Administrative Officer" | administrative_officer | ✅ |
| `test_librarian_maps_to_librarian_role` | "Librarian" | librarian | ✅ |
| `test_unknown_designation_falls_back_to_staff` | Janitor, Clerk, Driver, Cook, Cleaner, Unknown | staff | ✅ |
| `test_known_good_roles_unaffected` | super_admin, principal, teacher, student, staff | (explicit assignment) | ✅ |
| `test_case_insensitive_designation_matching` | All variants | Correct role | ✅ |

### Integration Verification (source inspection)

- `role_for_designation()` returns correct Role enum for all 6 mapped designations + safe default
- `primary_role` returns correct highest-priority role for mixed-role users (e.g., `[counsellor, staff, teacher]` → `counsellor`)
- Role enum choices include new values; `ROLE_RANK` contains correct ranks
- `IsStaffRole` / `IsAcademicMemberRole` contain new roles; admin/finance lists unchanged

### Negative Tests (least privilege)

| Attempted Access | Role | Result | Verified |
|------------------|------|--------|----------|
| Finance endpoints | Counsellor / Admin Officer / Nurse / Guard | DENIED (not in IsFinanceReaderRole) | ✅ Source |
| Admin endpoints | Counsellor / Admin Officer / Nurse / Guard | DENIED (not in IsAdminRole) | ✅ Source |
| Teacher endpoints | Counsellor / Admin Officer / Nurse / Guard | DENIED (not in IsTeacherRole) | ✅ Source |
| Library manage | Nurse / Guard / Counsellor / Admin Officer | DENIED (not in IsLibrarianRole) | ✅ Source |

---

## 5. Outstanding / Blocked Items

| Item | Status | Blocker |
|------|--------|---------|
| Live E2E for 5 accounts | BLOCKED | P17: Production deployment required; local HEAD 2df1989 not deployed; no legitimate session fixtures for Phase 83 accounts |
| Counsellor/Administrative Officer dedicated modules | NONE | No such modules exist in codebase; staff-family (helpdesk) is the intended surface |
| Frontend build verification | NOT RUN | `npm run build` disabled on this host (execution policy); JSX changes are array additions only |

---

## 6. Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `backend/apps/accounts/models.py` | +11/-4 | Role enum, ROLE_RANK, primary_role priority |
| `backend/apps/accounts/services.py` | +37 | DESIGNATION_ROLE_MAP + role_for_designation() |
| `backend/apps/accounts/serializers.py` | +6/-3 | Import + serializer fix |
| `backend/apps/accounts/permissions.py` | +4 | IsStaffRole + IsAcademicMemberRole additions |
| `frontend/src/App.jsx` | +8/-8 | 4 route/nav guard updates |
| `backend/apps/accounts/test_regressions.py` | +130 | 9 new regression tests |

**Migration generated:** `backend/apps/accounts/migrations/0016_alter_role_choices.py`

---

## 7. Compliance with Phase 84 Directives

| Directive (P0-P20) | Status | Note |
|-------------------|--------|------|
| P1: Reconcile Role enum + search synonyms | ✅ | No existing counsellor/admin_officer equivalents |
| P2: Canonical designation→role mapping | ✅ | 5 targets + lady health worker; safe default=staff |
| P3: Fix _build_user_account hardcoded STAFF | ✅ | Replaced with `role_for_designation()` |
| P4: Update all role resolution + primary_role | ✅ | Added org_admin, head_office, counsellor, admin_officer, librarian |
| P5: Backend permissions least privilege | ✅ | Only staff-family gates updated |
| P6: Object-level authorization intact | ✅ | No changes to object-level scoping |
| P7: FE /health-records guard | ✅ | Added nurse + staff (TPR-004) |
| P8: Nav visibility for 5 roles | ✅ | Health Records nav + Helpdesk nav updated |
| P9: Minimum reversible migration | ✅ | Choices-only, no data migration |
| P10: Regression tests | ✅ | 9 tests PASS |
| P11: Auth tests with legitimate accounts | BLOCKED | No legitimate sessions available |
| P12: E2E API auth for role-specific endpoints | BLOCKED | Same as P11 |
| P13: Frontend E2E | BLOCKED | Same as P11 |
| P14: Acceptance matrix | ✅ | PHASE_84_ROLE_AUTHORIZATION_MATRIX.md |
| P15: Negative/least-privilege tests | ✅ | Source-verified |
| P16: Existing-role regression | ✅ | Source-verified |
| P17: Production safety (no deploy) | ✅ | No deployment performed |
| P18: Git diff clean | ✅ | No debug code, no secrets |
| P19: 5 deliverables | ✅ | This + 4 others |
| P20: Machine summary | ✅ | PHASE_84_MACHINE_SUMMARY.txt |