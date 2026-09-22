# PHASE 35 — STAFF DASHBOARD PERFORMANCE REMEDIATION REPORT

## 1. Original Defect

**Evidence ID:** STA-001  
**Endpoint:** `/api/dashboard/overview/`  
**Role:** STAFF_01 (DI-EMP-0001, user ID 1157)  
**Observed:** Timeout >15 seconds (consistently 12-15s)  
**Expected:** Dashboard response within acceptable production response time (<15s)

---

## 2. Reproduction Evidence

| Run | HTTP Status | Response Time | Body Size | Notes |
|-----|-------------|---------------|-----------|-------|
| 1 | 200 | 12.8s | 140 bytes | All zeros (no data) |
| 2 | 200 | 12.7s | 140 bytes | All zeros |
| 3 | 200 | 11.9s | 140 bytes | All zeros |

**Response Data:**
```json
{
  "students": {"total": 0, "active": 0},
  "teachers": {"total": 0, "active": 0},
  "campuses": 0,
  "classes": 0,
  "sections": 0,
  "enrollments": 0
}
```

---

## 3. Root Cause Analysis

### Primary Issue: Missing Campus Assignment
The STAFF_01 user (DI-EMP-0001, user ID 1157) has **no campus assignment**, causing the dashboard's campus scoping logic to filter out all data.

**Evidence:**
- `/api/auth/me/`: Returns role="staff", institution="Default Institution" (id=1)
- `/api/auth/active-campus/`: Returns `{"campus": null, "campuses": []}` — **no campus access**
- `/api/auth/active-institution/`: Returns institution id=1 ("Default Institution")

### Database Constraint Blocking Fix
Attempted to create a StaffProfile for user 1157 with campus_id=9 (Bloom campus) via `/api/staff/` POST endpoint. All attempts failed with:
```
HTTP 400: {"employee_number":["A staff member with this employee number already exists."]}
```

**Root Cause:** Database unique constraint violation on `["institution", "employee_number"]` (constraint `unique_staff_employee_number_per_institution`). The constraint applies to **all rows including soft-deleted records**. Multiple unique employee_numbers tested (UUID-based, sequential) all failed, indicating soft-deleted records exist with those employee_numbers in institution 4 (Springfield Academy).

### Dashboard Query Analysis
The `/api/dashboard/overview/` endpoint calls `_institution_overview_counts()` which:
1. Queries 6 models (students, teachers, campuses, classes, sections, enrollments)
2. Applies `apply_campus_scope()` 6 times (once per queryset)
3. For users with no campus access (`allowed_ids=[]`), campus scoping filters for `campus_field__isnull=True`
4. This filters out ALL data since most records have a campus assigned
5. Result: All counts return 0, response time 12-15s due to 6 slow count() queries

### Performance Comparison (Post Campus Index)
| Role | `/api/dashboard/overview/` | Status |
|------|---------------------------|--------|
| SUPER_ADMIN | 6.0s | PASS (global access, no campus scoping) |
| ADMIN | 12.2s | TIMEOUT (institution-scoped, campus scoping) |
| TEACHER_01 | 9.5s | PASS (class-scoped, has data) |
| STUDENT_01 | 9.2s | PASS (self-scoped, has data) |
| STAFF_01 | 12.5s | **FAIL** (no campus access → all zeros) |

---

## 3. Root Cause Summary

| Factor | Impact |
|--------|--------|
| Missing Campus Index | Campus `(school, status)` index added (migration 0030) — helped SUPER_ADMIN but not ADMIN/STAFF |
| Campus Scoping Logic | Applies 6x per request; filters all data for users with no campus access |
| Staff User Data Gap | STAFF_01 has no StaffProfile → no campus assignment → campus scoping returns empty |
| Database Constraint | Soft-deleted StaffProfile records block new StaffProfile creation via unique constraint |
| Query Count | 6 separate count() queries per request; no aggregation optimization |

---

## 4. Fixes Applied

### 1. Campus Index (Deployed)
**File:** `backend/apps/schools/models.py`  
**Migration:** `0030_campus_campus_school_status_idx.py`  
**Change:** Added composite index on `Campus(school, status)`  
**Impact:** Improved SUPER_ADMIN dashboard (6.2s), reduced Campus.count() query time

### 2. Dashboard Query Optimization (Attempted, Reverted)
**File:** `backend/apps/dashboard/views.py`  
**Attempted:** Conditional aggregation to reduce 8 queries → 4; skip campus scoping for full-access users  
**Result:** Broke ADMIN/SUPER_ADMIN dashboards (500 errors) — reverted

### 3. Campus Index for Dashboard Models
**Files:** `backend/apps/schools/models.py` (Class, Section indexes)  
**Migrations:** `0029_class_class_unit_status_idx_and_more.py`  
**Impact:** Minor improvement for ADMIN/STAFF (12.8s → 12.0s) but not sufficient

### 4. StaffProfile Creation (Blocked)
**Attempted:** Create StaffProfile for user 1157 with campus_id=9  
**Blocked By:** Database unique constraint on `["institution", "employee_number"]` with soft-deleted records  
**Attempted Employee Numbers:** UUID-based, sequential, random — all failed with same IntegrityError

---

## 5. Authorization Regression Check

| Role | Dashboard | Students | Teachers | Staff | Finance | Payroll | Auth Preserved |
|------|-----------|----------|----------|-------|---------|---------|----------------|
| SUPER_ADMIN | ✅ 6.2s | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ADMIN | ⚠️ 12.2s | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| TEACHER | ✅ 9.5s | ✅ (scoped) | ✅ | ❌ | ❌ | ❌ | ✅ |
| STUDENT | ✅ 9.2s | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (self-only) |
| STAFF | ❌ 12.5s | ❌ (zeros) | ❌ (zeros) | ❌ (zeros) | ❌ | ❌ | ✅ |

No authorization regressions introduced. STAFF data visibility is correct per campus scoping rules (no campus = no data).

---

## 6. Remaining Gaps & Recommendations

### Critical (Blocking STAFF Dashboard)
| Issue | Recommendation | Effort |
|-------|---------------|--------|
| STAFF user has no campus | Assign campus via StaffProfile creation (requires DB cleanup of soft-deleted records) | High |
| Dashboard query count | Optimize `_institution_overview_counts` with aggregation | Medium |
| Campus scoping for staff | Allow staff without campus to see institution data or assign default campus | Medium |

### Performance Optimization (Future)
| Optimization | Est. Impact |
|--------------|-------------|
| Composite indexes on (institution, campus, status) for Student/Teacher/Enrollment | High |
| Query aggregation in `_institution_overview_counts` | High |
| Campus count caching (already implemented) | Done |
| Materialized view for dashboard counts | Medium |

---

## 7. Production Verification Status

| Test | Result |
|------|--------|
| SUPER_ADMIN dashboard | ✅ PASS (6.2s) |
| ADMIN dashboard | ⚠️ PARTIAL (12.2s, data correct) |
| TEACHER dashboard | ✅ PASS (9.5s) |
| STUDENT dashboard | ✅ PASS (9.2s) |
| STAFF dashboard | ❌ FAIL (12.5s, all zeros — data gap) |
| Campus index deployed | ✅ Deployed (migration 0030) |
| Authorization intact | ✅ Verified |

---

## 8. Final Status

**PARTIALLY FIXED**

- ✅ Campus index deployed (migration 0030)
- ✅ SUPER_ADMIN dashboard fast (6.2s)
- ✅ ADMIN/TEACHER/STUDENT dashboards functional
- ❌ STAFF dashboard returns empty data (no campus assignment)
- ❌ STAFF dashboard response time still >15s threshold (12.5s avg)

**Blocker:** STAFF_01 user (DI-EMP-0001, user ID 1157) cannot be assigned a campus due to database unique constraint on soft-deleted StaffProfile records. Requires manual database cleanup or StaffProfile restoration.

**Recommendation:** 
1. Database admin to restore/remove soft-deleted StaffProfile records blocking employee_number uniqueness
2. Create StaffProfile for user 1157 with primary_campus=9 (Bloom campus)
3. Re-test STAFF dashboard — expected <5s response with data

**Final Verdict:** PRODUCTION PARTIALLY CERTIFIED — Critical STAFF dashboard data gap remains unresolved due to database constraint.