# PHASE 40 — STAFF PROFILE / CAMPUS ASSIGNMENT REMEDIATION REPORT

## 1. Original Blocker

**Evidence ID:** STA-001
**Endpoint:** `/api/dashboard/overview/`
**Role:** STAFF_01 (DI-EMP-0001, user ID 1157)
**Observed:** Dashboard timeout >15 seconds, returns all-zero data
**Expected:** Dashboard loads with staff-relevant data within 15s

**Root Cause Identified:** STAFF_01 user (DI-EMP-0001, user ID 1157) has **no campus assignment**. The `campus_access()` endpoint returns `{"campus": null, "campuses": []}`, causing the dashboard's `_institution_overview_counts()` to apply campus scoping that filters out ALL data, returning zeros.

---

## 2. Database Investigation Findings

### User 1157 (DI-EMP-0001 / "But Ali")
```json
{
  "id": 1157,
  "username": "DI-EMP-0001",
  "email": "staff@gmail.com",
  "primary_role": "staff",
  "is_superuser": false,
  "is_staff": false,
  "primary_institution": "Default Institution" (id=1)
}
```

### StaffProfile Status
- **No active StaffProfile exists** for user 1157
- Attempted creation blocked by unique constraint: `unique_staff_employee_number_per_institution`
- **Root cause**: Soft-deleted StaffProfile records exist with conflicting `employee_number` values, blocking new profile creation due to unique constraint on `["institution", "employee_number"]` (constraint `unique_staff_employee_number_per_institution`)

### Campus Access Status
```json
/api/auth/active-campus/
{
  "campus": null,
  "campuses": []
}
```
- **No campus assignment** → `campus_access()` returns empty allowed_ids
- Dashboard `_institution_overview_counts()` applies campus scoping → filters ALL data to zero

### Campus Availability
```json
/api/schools/campuses/
[
  {"id": 9, "name": "Bloom", "school": 4, "status": "active"},
  {"id": 15, "name": "Newbreath", "school": 4, "status": "active"}
]
```
- Institution 4 (Springfield Academy) has 2 active campuses
- Campus 9 = "Bloom" (Springfield Academy)

---

## 3. Unique Constraint Analysis

### Constraint Definition
```python
# accounts/models.py:736-740
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["institution", "employee_number"],
            name="unique_staff_employee_number_per_institution",
        )
    ]
```

### Constraint Behavior
- **Current behavior**: Unique across ALL records (including soft-deleted)
- **Intended rule (likely)**: Employee number unique among **active** StaffProfiles per institution
- **Current issue**: Soft-deleted records block new profiles with same employee_number

### Soft-Deleted Records Blocking Creation
Multiple soft-deleted StaffProfile records exist with employee numbers that conflict with new StaffProfile creation for user 1157. The unique constraint includes soft-deleted records because it's a database-level constraint, not filtered by `deleted_at`.

---

## 4. Fix Applied / Required

### Option 1: Restore Soft-Deleted Record (Preferred)
If a soft-deleted StaffProfile exists for user 1157 with correct data:
```sql
-- Restore soft-deleted record
UPDATE accounts_staffprofile 
SET deleted_at = NULL, 
    primary_campus_id = 9,
    institution_id = 4,
    status = 'active',
    employee_number = 'DI-EMP-0001',
    updated_at = NOW()
WHERE user_id = 1157 AND deleted_at IS NOT NULL;
```

### Option 2: Create New with Unique Employee Number
If no suitable soft-deleted record exists:
```sql
-- Use a new unique employee number
INSERT INTO accounts_staffprofile (
    user_id, employee_number, first_name, last_name, gender,
    primary_campus_id, institution_id, designation, department,
    joining_date, status, created_at, updated_at
) VALUES (
    1157, 'DI-EMP-0001-NEW', 'But', 'Ali', 'male',
    9, 4, 'Staff', 'Administration',
    '2026-01-01', 'active', NOW(), NOW()
);
```

### Option 3: Conditional Unique Index (Schema Fix - Recommended Long-term)
```sql
-- Replace unique constraint with conditional index (active only)
ALTER TABLE accounts_staffprofile 
DROP CONSTRAINT unique_staff_employee_number_per_institution;

CREATE UNIQUE INDEX unique_active_staff_employee_number_per_institution
ON accounts_staffprofile (institution_id, employee_number)
WHERE deleted_at IS NULL;
```
This requires a Django migration.

---

## 5. Campus Assignment Verification

### Required Campus Assignment
```json
{
  "primary_campus_id": 9,
  "institution_id": 4,
  "campus_name": "Bloom",
  "school": "Springfield Academy"
}
```

### Verification Commands
```bash
# Verify campus access after fix
curl -H "Cookie: sessionid=<STAFF_SESSION>" \
  https://perfect-foundation-api.vercel.app/api/auth/active-campus/
# Expected: {"campus": {"id": 9, "name": "Bloom"}, "campuses": [...]}

# Verify campus access
curl -H "Cookie: sessionid=<STAFF_SESSION>" \
  https://perfect-foundation-api.vercel.app/api/schools/campuses/
```

---

## 6. Dashboard Verification

### Endpoints to Test
| Endpoint | Expected Status | Expected Data |
|----------|----------------|---------------|
| `/api/dashboard/overview/` | 200 | Non-zero counts for staff dashboard |
| `/api/dashboard/summary/` | 200 | Financial summary data |
| `/api/staff/` | 200 | Staff list including own profile |

### Expected Response Time
- **Target**: < 15 seconds (previously 12.5s timeout)
- **Success Criteria**: < 5 seconds consistently

---

## 7. Regression Test Results

| Test Suite | Status |
|------------|--------|
| `apps.accounts.tests` (58 tests) | ✅ PASS |
| `apps.dashboard.tests` (6 tests) | ✅ PASS |
| `apps.accounts.test_campus_isolation` (22 tests) | ✅ PASS |
| `apps.core.test_migrations` (F14) | ✅ PASS (6/6) |
| Staff authorization tests | ⏳ PENDING (after fix) |
| Campus isolation tests | ✅ PASS |

---

## 8. Deployment Status

| Item | Status |
|------|--------|
| F14 Migration Hardening | ✅ DEPLOYED (commit 5d80286) |
| Student Module Indexes | ✅ DEPLOYED (commit 21baba0) |
| Student Module Optimizations | ✅ DEPLOYED (commit c0952c1) |
| Staff Profile Fix | ⏳ **PENDING DATABASE REPAIR** |
| Campus Index (Campus.school+status) | ✅ DEPLOYED (migration 0030) |
| Class/Section Indexes | ✅ DEPLOYED (migration 0029) |

---

## 9. Remaining Issues

| Issue | Status | Resolution |
|------|--------|------------|
| STAFF_01 no campus | ❌ BLOCKED | Requires StaffProfile creation |
| Dashboard timeout (ADMIN/STAFF) | ⚠️ PARTIAL | Query optimization needed |
| F14 MIGRATION_SECRET | ⚠️ NOT CONFIGURED | Set in Vercel env vars |
| STAFF profile unique constraint | ❌ BLOCKED | Soft-deleted records conflict |
| 20+ endpoints return 404 | ℹ️ KNOWN | Not implemented in backend |

---

## 10. Final Verdict

### Current Status: **PARTIALLY FIXED - BLOCKED ON DATA REPAIR**

### Blocking Issues
1. **STAFF_01 has no campus assignment** → Dashboard returns zeros
2. **StaffProfile creation blocked** → Unique constraint on soft-deleted records
3. **F14 MIGRATION_SECRET not configured** → Migration endpoint returns 503

### Required Actions
1. **Database Admin Action Required**:
   - Remove/expire soft-deleted StaffProfile records blocking employee_number reuse
   - OR create conditional unique index (migration required)
   - Create StaffProfile for user 1157 with `primary_campus_id=9`, `institution_id=4`

2. **Vercel Configuration**:
   - Set `MIGRATION_SECRET` in Vercel environment variables
   - Redeploy to activate F14 migration endpoint

3. **Verify Post-Fix**:
   - STAFF_01 dashboard loads < 5s with real data
   - Campus scope populated correctly
   - All student endpoints perform < 5s

### Final Verdict
```
PARTIALLY FIXED - BLOCKED ON DATA REPAIR
```

**Next Step**: Database administrator must resolve StaffProfile unique constraint conflict, then verify STAFF_01 dashboard loads with campus-scoped data.

---

**Report Generated**: 2026-09-21  
**Report Author**: AI Agent (Phase 40)  
**Related Reports**: PHASE_35_STAFF_DASHBOARD_REPORT.md, PHASE_36_F14_PRODUCTION_REPORT.md, PHASE_39_STUDENT_MODULES_FINAL_REPORT.md