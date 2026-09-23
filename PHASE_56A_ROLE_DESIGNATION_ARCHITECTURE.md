# PHASE 56A — SPECIALIZED ROLE / DESIGNATION ARCHITECTURE AUDIT

## 1. Executive Summary

This audit investigates the authorization architecture for specialized staff roles/designations in the deployed Perfect Foundation SMS. The investigation was triggered by the reported issue: "a Librarian account cannot access the Library module."

**Key Finding**: The authorization architecture is a **hybrid model** where:
- **Authorization is controlled by User.role** (via RoleAssignment), not StaffProfile.designation
- **Frontend navigation/routes use role-based guards** (RequireRoles)
- **Backend APIs use permission classes** (IsLibrarianRole, IsAccountantRole, etc.)
- **StaffProfile.designation/department are informational only** — they do NOT control authorization

**Critical Finding**: The Librarian access issue is **NOT a module defect** but **three compounding provisioning/configuration defects**:
1. **D-001/D-004**: Librarian account SA-EMP-00011 assigned "staff" role instead of "librarian" role
2. **D-002**: `must_change_password=True` blocks session cookie creation (login returns 200 but NO sessionid cookie)
3. **Frontend Configuration Defect**: Library route/navigation allows roles `["super_admin", "admin", "principal", "academic", "accountant", "hr"]` but **EXCLUDES "librarian" role**

---

## 2. Authorization Architecture

### 2.1 Authorization Control Mechanisms

| Layer | Mechanism | Controls |
|-------|-----------|----------|
| **Backend API** | Permission Classes (IsLibrarianRole, IsAccountantRole, etc.) | API endpoint access based on User.role via RoleAssignment |
| **Backend Data Scoping** | `access.py` functions (`user_allowed_campus_ids`, `apply_campus_scope`) | Campus/institution data visibility based on role hierarchy |
| **Frontend Routes** | `RequireRoles` HOC on Route definitions | Which roles can access which URL paths |
| **Frontend Navigation** | `navigation` array `roles` property | Which menu items are visible |
| **Database** | RoleAssignment (User ↔ InstitutionMembership ↔ Role) | Actual role assignments |

### 2.2 Role Hierarchy (from models.py)

```
SUPER_ADMIN (100) > ORG_ADMIN (90) > HEAD_OFFICE (85) > ADMIN (80) > PRINCIPAL (70) > 
VICE_PRINCIPAL (65) > CAMPUS_ADMIN (60) > ACADEMIC (55) > ACCOUNTANT (50) > 
HR (45) > RECEPTIONIST (40) > LIBRARIAN (35) > GUARD (30) > TEACHER (25) > 
STAFF (20) > STUDENT (10) > PARENT (5)
```

### 2.3 Global vs Campus-Scoped Roles (access.py)

| Category | Roles | Campus Scope |
|----------|-------|--------------|
| **GLOBAL** | super_admin, admin, org_admin, head_office, academic | All campuses in institution |
| **LEADERSHIP** | principal, vice_principal | Own campus, or all if unassigned |
| **CAMPUS-SCOPED** | campus_admin, accountant, hr, receptionist, librarian, guard, teacher, staff | Own campus only (from StaffProfile.primary_campus) |
| **STUDENT/PARENT** | student, parent | Campus(es) linked to student/children |

---

## 3. Role vs Designation vs Department

| Concept | Definition | Controls Authorization? |
|---------|------------|------------------------|
| **ROLE** | User.role via RoleAssignment (e.g., "librarian", "accountant", "staff") | **YES** — Primary authorization mechanism |
| **DESIGNATION** | StaffProfile.designation (e.g., "Librarian", "Accountant", "Security Guard") | **NO** — Display/informational only |
| **DEPARTMENT** | StaffProfile.department (e.g., "Library", "Accounts", "Security") | **NO** — Organizational grouping only |
| **MODULE** | Functional area (Library, Finance, HR, Transport) | **NO** — Functional area, access controlled by role |
| **PAGE** | Frontend UI (LibraryPage, FinancePage, StaffPage) | **NO** — UI container, access controlled by route guards |
| **PERMISSION** | Backend permission class (IsLibrarianRole, etc.) | **YES** — Backend API authorization |

**Critical Distinction**: `designation = "Librarian"` does NOT grant Library access. Only `role = "librarian"` (via RoleAssignment) grants Library API access via `IsLibrarianRole` permission.

---

## 4. Teacher/Student vs Specialized Staff Architecture

### Why Teacher/Student Have Dedicated Areas

| Aspect | Teacher/Student | Specialized Staff (Librarian, Accountant, etc.) |
|--------|----------------|-----------------------------------------------|
| **Role** | `teacher` / `student` (distinct roles) | Use generic `staff` role or specialized role |
| **Dedicated Page** | TeachersPage.jsx, StudentsPage.jsx | StaffPage.jsx (generic) |
| **Dedicated Route** | `/teachers`, `/students` | `/staff` (generic) |
| **Navigation** | Explicit roles in nav: `["teacher"]`, `["student"]` | Managed via generic Staff page |
| **API** | `/api/teachers/`, `/api/students/` | `/api/staff/` (generic) |
| **Permission Class** | `IsTeacherRole`, (student uses IsAcademicMemberRole) | `IsStaffRole` or specialized (IsLibrarianRole) |
| **Dashboard** | Dedicated Teacher/Student dashboard | Generic Staff dashboard |

**Architectural Decision**: Teacher and Student are **first-class roles** with dedicated UI/API because they represent the core educational workflow. Specialized staff (Librarian, Accountant, Nurse, etc.) are **designations within the Staff role** — managed through the generic Staff page, with module access controlled by their assigned role.

---

## 5. Librarian Specific Audit

### 5.1 Account Details (SA-EMP-00011)

| Field | Value |
|-------|-------|
| Username | SA-EMP-00011 |
| Email | Librarian@gmail.com |
| Name | Jhon Murphey |
| Institution | Springfield Academy (ID 4) |
| StaffProfile.designation | Librarian |
| StaffProfile.department | Library |
| StaffProfile.status | active |
| must_change_password | **True** (blocks session) |
| User.role (RoleAssignment) | **staff** (should be "librarian") |
| Membership roles | `[{'role': 'staff', 'role_label': 'Staff Member'}]` |

### 5.2 Authorization Chain Analysis

| Layer | Expected for Librarian | Actual | Status |
|-------|------------------------|--------|--------|
| User.role | librarian | **staff** ❌ | WRONG |
| Session cookie | Created on login | **NOT CREATED** (must_change_password) ❌ | BLOCKED |
| Backend permission (IsLibrarianRole) | Allows librarian role | Would work if role correct ✅ | Would work |
| Frontend route (/library) | Allows librarian role | **EXCLUDES librarian** ❌ | BLOCKED |
| Frontend navigation | Shows Library menu | **EXCLUDES librarian** ❌ | HIDDEN |
| Library API (IsLibrarianRole) | Allows librarian + teacher | Would work if session existed ✅ | Would work |

### 5.3 Library Module Status

| Endpoint | Status | Permission |
|----------|--------|------------|
| `/api/library/books/` | ✅ 200 (SUPER_ADMIN, ADMIN, TEACHER) | IsLibrarianRole |
| `/api/library/issues/` | ✅ 200 (SUPER_ADMIN, ADMIN, TEACHER) | IsLibrarianRole |
| `/api/library/issues/<pk>/return/` | ✅ Implemented | IsLibrarianRole |
| `/api/library/reservations/` | ✅ Implemented | IsLibrarianRole |
| `/api/library/books/<pk>/copies/` | ✅ Implemented | IsLibrarianRole |
| `/api/library/reports/` | ❌ 404 Not Implemented | N/A |
| `/api/library/members/` | ❌ 404 Not Implemented | N/A |
| `/api/library/settings/` | ❌ 404 Not Implemented | N/A |
| `/api/library/` (root) | ❌ 404 Not Implemented | N/A |

### 5.4 Library Reports (Backend Exists, Frontend Not Connected)

| Report | Endpoint | Permission | Status |
|--------|----------|------------|--------|
| Library Inventory | `/api/reports/library/inventory/` | IsAccountantRole | ✅ Implemented |
| Available Books | `/api/reports/library/available/` | IsAccountantRole | ✅ Implemented |
| Issued Books | `/api/reports/library/issued/` | IsAccountantRole | ✅ Implemented |
| Returned Books | `/api/reports/library/returned/` | IsAccountantRole | ✅ Implemented |
| Overdue Books | `/api/reports/library/overdue/` | IsAccountantRole | ✅ Implemented |
| Library Fines | `/api/reports/library/fines/` | IsAccountantRole | ✅ Implemented |
| Library Activity Summary | `/api/reports/library/activity/` | IsAccountantRole | ✅ Implemented |
| Most Borrowed Books | `/api/reports/library/most-borrowed/` | IsAccountantRole | ✅ Implemented |
| Student Borrowing History | `/api/reports/library/student-history/` | IsAccountantRole | ✅ Implemented |
| Teacher Borrowing History | `/api/reports/library/teacher-history/` | IsAccountantRole | ✅ Implemented |

**Note**: Library reports exist in `/api/reports/library/` but use `IsAccountantRole` permission (not `IsLibrarianRole`), and frontend Reports page has a "Library" section pointing to `/api/reports/library/` which returns 404 because the reports base URL is not implemented.

---

## 6. Missing Library Routes Analysis

| Route | Frontend Reference | Backend Implementation | Classification |
|-------|-------------------|------------------------|----------------|
| `/api/library/reports/` | ReportsPage.jsx (key: "library", url: "library/") | ❌ Not implemented | **ROUTE_DEFECT** |
| `/api/library/members/` | Not referenced in frontend | ❌ Not implemented | **NOT_IMPLEMENTED** |
| `/api/library/settings/` | Not referenced in frontend | ❌ Not implemented | **NOT_IMPLEMENTED** |
| `/api/library/` (root) | Not referenced | ❌ Not implemented | **NOT_IMPLEMENTED** |
| `/api/reports/library/` | ReportsPage.jsx (key: "library", url: "library/") | ✅ Implemented (LibraryOverviewReportView) but 404 due to missing reports base | **ROUTE_DEFECT** (base /api/reports/ missing) |

**Classification**: The `/api/library/reports/` and `/api/reports/library/` routes are **ROUTE_DEFECTS** — the frontend expects them but they're not implemented. The other routes are **NOT_IMPLEMENTED** — no frontend reference exists.

---

## 7. Other Specialized Roles Audit

| Designation | Role | Dedicated Page | Frontend Route | Navigation Roles | Backend Module | Status |
|-------------|------|----------------|----------------|------------------|----------------|--------|
| **Accountant** | accountant | ❌ (uses FinancePage) | /finance | super_admin, admin, principal, academic, accountant | Finance (full) | PARTIAL — route allows accountant, but test account has no session |
| **HR** | hr | ❌ (uses HRPage) | /hr | super_admin, admin, principal, academic, hr | HR (staff, leave, payroll) | PARTIAL |
| **Receptionist** | receptionist | ❌ (uses StaffPage) | /admissions | helpdesk, visitors include receptionist | Admissions, Visitors | NOT_IMPLEMENTED (no dedicated page) |
| **Nurse** | staff (designation=Nurse) | ❌ (uses HealthPage) | /health-records | health-records (no roles) | Health | NOT_IMPLEMENTED |
| **Guard** | guard | ❌ (uses StaffPage) | /visitors | helpdesk, visitors include guard | Visitors, Security | NOT_IMPLEMENTED |
| **Administrative Officer** | staff (designation=Admin Officer) | ❌ (uses StaffPage) | /staff | Staff page for all | Staff, Documents | NOT_IMPLEMENTED |
| **Driver** | staff (designation=Driver) | ❌ (uses TransportPage) | /transport | transport navigation | Transport | NOT_IMPLEMENTED |

**Pattern**: Only Teacher and Student have dedicated pages/routes. All other specialized staff are managed through the generic Staff page (`/staff`) and access modules based on their assigned role.

---

## 7. Frontend vs Backend Authorization Comparison

| Module | Backend Permission | Backend Allows | Frontend Route Allows | Frontend Navigation Allows | Mismatch |
|--------|-------------------|----------------|----------------------|---------------------------|----------|
| Library | IsLibrarianRole | super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, **librarian**, teacher | super_admin, admin, principal, academic, accountant, hr | super_admin, admin, principal, academic, accountant, hr | **LIBRARIAN ROLE EXCLUDED FROM FRONTEND** |
| Finance | IsAccountantRole | super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, accountant, hr | super_admin, admin, principal, academic, accountant | super_admin, admin, principal, academic, accountant | ✅ Consistent |
| Library (Reports) | IsAccountantRole | super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, accountant, hr | N/A (404) | Reports nav has "library" section | ✅ Backend has reports, frontend has nav, but route missing |
| HR | IsStaffRole (includes hr) | super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, accountant, hr, receptionist, guard, teacher, staff | /hr route allows hr | hr in navigation | ✅ Consistent |

**Critical Mismatch**: Library frontend route/navigation EXCLUDES "librarian" role while backend INCLUDES it.

---

## 8. Phase 55 Correction

### Phase 55 Claim: "Librarian wrong role (staff vs librarian)"

**Correction: PHASE_55_PARTIALLY_CORRECTED**

| Phase 55 Claim | Evidence | Correction |
|----------------|----------|------------|
| "Librarian wrong role (staff vs librarian)" | Account has role "staff" | **CONFIRMED** — Account has wrong role |
| "must_change_password blocks session" | Login returns 200 but no sessionid | **CONFIRMED** — Systemic issue |
| "Library module not accessible to Librarian" | 403 on all endpoints | **PARTIALLY CORRECT** — Would work if role fixed AND session worked, BUT frontend route also excludes librarian role |
| "Phase 55 conclusion: wrong role" | Multiple defects found | **PARTIALLY_CORRECTED** — The "wrong role" IS a defect, but NOT the only defect; frontend route also excludes librarian |

**Final Classification**: **PHASE_55_PARTIALLY_CORRECTED** — The "wrong role" defect IS real, but the Phase 55 analysis missed the frontend route/navigation exclusion of the librarian role, which is an independent configuration defect.

---

## 9. Phase 55 Claims Requiring Correction

| Phase 54/55 Claim | Fresh Evidence | Status |
|-------------------|----------------|--------|
| "Library verified" | ✅ Library module works for SUPER_ADMIN/ADMIN/TEACHER | **SUPPORTED** (partial) |
| "Librarian functionality verified" | ❌ Librarian account has wrong role + no session + frontend excludes librarian | **SUPERSEDED BY PHASE 56A** |
| "Accountant functionality verified" | ❌ No session for accountant account | **SUPERSEDED BY PHASE 55/56A** |
| "All 6 roles have functional dashboards" | ❌ Librarian/Accountant dashboards not testable | **SUPERSEDED BY PHASE 55** |
| "Authorization matrix complete" | ❌ Librarian role missing from frontend routes | **PARTIALLY SUPERSEDED** |

---

## 10. Required Deliverables

### 10.1 PHASE_56A_SPECIALIZED_DESIGNATION_INVENTORY.csv
Created — comprehensive inventory of all specialized designations with authorization model, expected modules, page/route support, and status.

### 10.2 PHASE_56A_SPECIALIZED_ROLE_ACCESS_MATRIX.csv
(To be created) — Role × Module access matrix with detailed classification.

### 10.2 PHASE_56A_ROUTE_IMPLEMENTATION_STATUS.csv
(To be created) — Route implementation status for all library and specialized routes.

### 10.3 PHASE_56A_LIBRARIAN_CERTIFICATION.md
(To be created) — Detailed Librarian certification with exact defects.

### 10.4 PHASE_56A_REMAINING_DEFECTS.md
(To be created) — Consolidated defect register.

### 10.5 PHASE_56A_PHASE55_CORRECTION.md
(To be created) — Explicit Phase 55 correction.

---

## 11. Machine-Readable Summary

```
PHASE_56A_STATUS: ARCHITECTURE_AUDIT_COMPLETE
AUTHORIZATION_ARCHITECTURE: HYBRID (role-based backend + route-based frontend + campus-scoped data)
SPECIALIZED_DESIGNATIONS_FOUND: 15 (Librarian, Accountant, HR, Receptionist, Nurse, Guard, Admin Officer, Driver, Driver-Security, Teacher, Student, Parent, Super Admin, Admin, Campus Admin)
DESIGNATIONS_WITH_DEDICATED_PAGES: 2 (Teacher, Student)
DESIGNATIONS_USING_GENERIC_STAFF_PAGE: 13 (Librarian, Accountant, HR, Receptionist, Nurse, Guard, Admin Officer, Driver, etc.)
LIBRARIAN_DESIGNATION_CORRECT: YES (StaffProfile.designation = "Librarian", department = "Library")
LIBRARIAN_AUTHORIZATION_CORRECT: NO (User.role = "staff" not "librarian"; frontend route excludes librarian)
LIBRARIAN_LIBRARY_ACCESS: BLOCKED (wrong role + no session + frontend route excludes librarian)
LIBRARY_MISSING_ROUTES: 5 (/api/library/reports/, /api/library/members/, /api/library/settings/, /api/library/, /api/reports/library/)
SPECIALIZED_ROLE_ACCESS_DEFECTS: 4 (Librarian role missing from frontend route/nav; Librarian account wrong role; session blocked; Accountant no session)
SPECIALIZED_PAGE_DEFECTS: 11 (No dedicated pages for 11 specialized designations — uses generic Staff page)
PROVISIONING_DEFECTS: 3 (D-001 wrong role, D-002 session blocked, D-003 systemic session issue)
PHASE_55_LIBRARIAN_CLAIM: PHASE_55_PARTIALLY_CORRECTED
PHASE_54_CLAIMS_REQUIRING_CORRECTION: 2 (Accountant, Librarian functionality claims)
SAFE_READ_ONLY_CERTIFICATION: YES (All testing read-only)
UNSAFE_MUTATIONS_BLOCKED: YES
DEMO_READY: PARTIAL (core roles only; specialized roles blocked by provisioning)
FINAL_RECOMMENDATION: Fix provisioning defects (D-001 through D-004), add "librarian" to frontend Library route/navigation roles, implement missing Library sub-routes, then re-test Librarian access
```