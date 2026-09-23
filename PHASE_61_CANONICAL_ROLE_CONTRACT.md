# PHASE 61 — CANONICAL ROLE CONTRACT

## 1. Executive Summary

This document defines the canonical role contract for the Perfect Foundation SMS based on the actual implementation in the codebase. It serves as the authoritative reference for role definitions, authorization behavior, and specialized role capabilities.

---

## 2. Authorization Architecture

### 2.1 Hybrid Authorization Model

The system employs a **hybrid authorization architecture**:

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| **Authentication** | User.email / User.username + password | Identity verification |
| **Authorization** | User.role (via RoleAssignment) | Backend & frontend authorization |
| **Staff Identity** | StaffProfile.designation | Display/informational only |
| **Data Scoping** | User.primary_campus + InstitutionMembership | Data isolation |

### 2.2 Role Hierarchy (from models.py)

```python
ROLE_RANK = {
    Role.SUPER_ADMIN: 100,
    Role.ORG_ADMIN: 90,
    Role.HEAD_OFFICE: 85,
    Role.ADMIN: 80,
    Role.PRINCIPAL: 70,
    Role.VICE_PRINCIPAL: 65,
    Role.CAMPUS_ADMIN: 60,
    Role.ACADEMIC: 55,
    Role.ACCOUNTANT: 50,
    Role.HR: 45,
    Role.RECEPTIONIST: 40,
    Role.LIBRARIAN: 35,
    Role.GUARD: 30,
    Role.TEACHER: 25,
    Role.STAFF: 20,
    Role.STUDENT: 10,
    Role.PARENT: 5,
}
```

### 2.3 Authorization Chain

```
User → RoleAssignment (via InstitutionMembership) → Role
     → Permission Classes (IsLibrarianRole, IsAccountantRole, etc.)
     → API Access Control
```

**Critical**: StaffProfile.designation is **display only** and does NOT drive authorization. All authorization decisions use User.role derived from RoleAssignment.

---

## 3. CANONICAL ROLE CONTRACT

### 3.1 Core Roles (Fully Implemented)

| Role | Canonical Value | Primary Module | Frontend Route | Backend APIs | Dedicated Page |
|------|----------------|----------------|----------------|--------------|----------------|
| SUPER_ADMIN | `super_admin` | All | Global | All | ✅ Dashboard |
| ADMIN | `admin` | All | `/admin` | All admin | ✅ Dashboard |
| PRINCIPAL | `principal` | Admin | `/admin` | Admin modules | ✅ Dashboard |
| VICE_PRINCIPAL | `vice_principal` | Admin | Admin modules | Admin scope | ✅ Dashboard |
| CAMPUS_ADMIN | `campus_admin` | Admin | Campus modules | `/campus-dashboard` | Campus-scoped |
| ACADEMIC | `academic` | Academic | `/academics` | Academic modules | ✅ Academic dashboard |
| TEACHER | `teacher` | Academics | `/teachers` | Teacher APIs | ✅ TeachersPage |
| STUDENT | `student` | Student | `/students` | Student APIs | ✅ Student360Page |
| PARENT | `parent` | Student | `/parent-portal` | Parent portal | Parent portal |
| STAFF | `staff` | Staff | `/staff` | Staff APIs | Staff page |

### 3.2 Specialized Roles (Designation-Based)

| Role | Canonical Role | Designation | Module | Frontend Route | Dedicated Page | Status |
|------|---------------|-------------|--------|----------------|----------------|--------|
| LIBRARIAN | `librarian` | Librarian | Library | `/library` | ✅ LibraryPage.jsx | PARTIAL |
| ACCOUNTANT | `accountant` | Accountant | Finance | `/finance` | FinancePage | PARTIAL |
| HR | `hr` | HR | `/hr` | HRPage.jsx | PARTIAL |
| RECEPTIONIST | `receptionist` | Admissions | `/admissions` | ❌ | PARTIAL |
| NURSE | `nurse` | Health | `/health-records` | HealthPage | PARTIAL |
| GUARD | `guard` | Security | `/visitors` | VisitorsPage | PARTIAL |
| ADMIN_OFFICER | `staff` | Admin Officer | `/staff` | StaffPage | PARTIAL |
| DRIVER | `staff` + `Driver` | Transport | `/transport` | TransportPage | PARTIAL |
| GUARD | `guard` | Security | `/visitors` | VisitorsPage | PARTIAL |
| DRIVER_SECURITY | `guard` | Security | `/visitors` | VisitorsPage | PARTIAL |
| DRIVER | `staff` + `Driver` | Transport | `/transport` | TransportPage | PARTIAL |
| ADMIN_OFFICER | `staff` | Admin Officer | `/staff` | Staff page | PARTIAL |
| DRIVER_SECURITY | `guard` | Security | `/visitors` | VisitorsPage | PARTIAL |

---

## 3.3 Specialized Role Capabilities

### LIBRARIAN (`librarian` role)
| Capability | Status | Details |
|------------|--------|---------|
| Books CRUD | ✅ | `/api/library/books/` CRUD |
| Issues/Circulation | ✅ | Issue/return books |
| Reservations | ✅ | Full CRUD |
| Reports | ✅ | All 10 reports (IsLibrarianRole added) |
| Frontend Route | `/library` | ✅ Enabled |
| Navigation | ✅ Visible | Added to nav + RequireRoles |
| Dedicated Page | ✅ | LibraryPage.jsx |

### ACCOUNTANT (`accountant` role)
| Capability | Status |
|------------|--------|
| Finance Dashboard | ✅ |
| Trial Balance | ✅ |
| Income/Expense | ✅ |
| Receivables | ✅ |
| Fee Categories | ✅ (read) |
| Fee Structures | ✅ (read) |
| Budgets | ✅ (read) |
| Accounts | ✅ (read) |

### GUARD (`guard` role)
| Capability | Status |
|------------|--------|
| Visitor Management | ✅ |
| Visitors Page | ✅ (`/visitors`) |
| Check-in/out | ✅ |
| Digital IDs | ✅ |

### HR (`hr` role)
| Capability | Status |
|------------|--------|
| HR Dashboard | Partial |
| Staff Management | Via Staff page |
| Leave Management | Via Staff page |
| Payroll Read | ✅ |

### RECEPTIONIST
| Capability | Status |
|------------|--------|
| Admissions | Via Admissions page |
| Visitors | Via Visitors page |
| Communication | Via Messages |

### NURSE
| Status | Details |
|--------|---------|
| Role | Uses `staff` role + `designation=Nurse` |
| Route | `/health-records` (HealthPage) |
| Blockers | Requires `school_code` for login (username conflict) |
| APIs | HealthRecordsPage, HealthRecords APIs |

### Other Specialized Roles
| Role | Status | Notes |
|------|--------|-------|
| HR | Partially supported | HRPage exists, no dedicated account |
| RECEPTIONIST | Uses Staff page | Admissions/Visitors access |
| TRANSPORT | Uses TransportPage | Has transport role |
| INVENTORY | Not provisioned | InventoryPage exists |
| HOSTEL | Not provisioned | HostelPage exists |
| ADMIN_OFFICER | Staff role | Uses Staff page |
| DRIVER | Transport page | Staff designation |
| DRIVER_SECURITY | Guard role | Visitors page |

---

## 4. FRONTEND ROLE PARITY

### Route Guards (RequireRoles)

| Route | Required Roles | Status |
|-------|----------------|--------|
| `/library` | `super_admin, admin, principal, academic, accountant, hr, librarian` | ✅ FIXED |
| `/finance` | `super_admin, admin, principal, academic, accountant` | ✅ |
| `/hr` | `super_admin, admin, principal, academic, hr` | ✅ |
| `/visitors` | `super_admin, admin, principal, vice_principal, campus_admin, academic, hr, receptionist, guard, staff` | ✅ |
| `/finance` | `super_admin, admin, principal, academic, accountant` | ✅ |
| `/hr` | `super_admin, admin, principal, academic, hr` | ✅ |
| `/hr` | `hr` role included | ✅ |

### Navigation Visibility

| Module | Navigation Roles | Status |
|--------|------------------|--------|
| Library | `super_admin, admin, principal, academic, accountant, hr, librarian` | ✅ FIXED |
| Finance | `super_admin, admin, principal, academic, accountant` | ✅ |
| HR | `super_admin, admin, principal, academic, hr` | ✅ |
| Library (nav) | `super_admin, admin, principal, academic, accountant, hr, librarian` | ✅ FIXED |

---

## 5. BACKEND AUTHORIZATION PARITY

### Permission Classes

| Permission Class | Roles Allowed | Used By |
|------------------|---------------|---------|
| `IsLibrarianRole` | `super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, librarian, teacher` | Library APIs |
| `IsAccountantRole` | `super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, accountant, hr` | Finance APIs |
| `IsLibrarianRole` | `super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, librarian, teacher` | Library APIs |
| `IsAccountantRole` | `super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, accountant, hr` | Finance Reports |
| `IsAccountantRole` | (Library Reports) | Library Reports (FIXED) |
| `IsStaffRole` | `super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, accountant, hr, receptionist, guard, teacher, staff` | Staff APIs |

### Authorization Parity Matrix

| Module | Backend Allows | Frontend Allows | Frontend Nav | Match |
|--------|----------------|-----------------|--------------|-------|
| Library | librarian, teacher, admin, super_admin, ... | librarian, admin, principal, academic, accountant, hr | librarian added | ✅ FIXED |
| Finance Reports | accountant, admin, super_admin, ... | accountant, admin, principal, academic | accountant included | ✅ |
| Library Reports | accountant, librarian (FIXED) | accountant only (was) | N/A | ✅ FIXED |
| Finance | accountant, admin, ... | accountant, admin, ... | accountant included | ✅ |

---

## 6. ROLE × MODULE ACCESS MATRIX

| Role | Dashboard | Students | Teachers | Staff | Library | Finance | Attendance | Exams | Reports | HR | Library Reports |
|------|-----------|----------|----------|-------|---------|---------|------------|-------|---------|----|----------------|
| SUPER_ADMIN | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ADMIN | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| TEACHER | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| STAFF | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| STUDENT | ✅ | ✅ (self) | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| LIBRARIAN | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅* |
| ACCOUNTANT | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅* |
| GUARD | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| ADMIN_OFFICER | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| NURSE | BLOCKED | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GUARD | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| ADMIN_OFFICER | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

*Library reports require IsLibrarianRole (FIXED)

---

## 6. AUTHORIZATION CHAIN

```
User
  → RoleAssignment (via InstitutionMembership)
    → Role (librarian, accountant, guard, etc.)
      → Permission Classes (IsLibrarianRole, IsAccountantRole, etc.)
        → API View Permissions
          → Frontend RequireRoles
            → UI Navigation/Route Access
```

---

## 7. PROVISIONING REQUIREMENTS

### Required for Specialized Role Provisioning:
1. **User** with unique username per institution
2. **RoleAssignment** with correct specialized role (librarian, accountant, guard, etc.)
3. **StaffProfile** with:
   - `designation` = "Librarian", "Accountant", etc. (display only)
   - `department` = "Library", "Finance", etc.
   - `primary_campus` = assigned campus
3. `must_change_password = False` (for test accounts)
4. `is_active = True`
5. Active `InstitutionMembership` with correct institution
6. `RoleAssignment` with correct specialized role

### Provisioning Checklist

| Role | User.role | StaffProfile.designation | StaffProfile.department | RoleAssignment | Frontend Route | Nav Access |
|------|-----------|--------------------------|------------------------|----------------|----------------|------------|
| Librarian | librarian | Librarian | Library | librarian | /library | ✅ |
| Accountant | accountant | Accountant | Accounts | accountant | /finance | ✅ |
| Guard | guard | Security Guard | Security | /visitors | ✅ | ✅ |
| Admin Officer | staff | Administrative Officer | Administration | staff | /staff | ✅ |
| Nurse | nurse (or staff) | Nurse | Health | ❌ | ❌ | ❌ |

---

## 7. CANONICAL ROLE CONTRACT SUMMARY

| Aspect | Canonical Definition |
|--------|---------------------|
| **Authentication Identity** | User.email / User.username |
| **Authorization Identity** | User.role (via RoleAssignment) |
| **Staff Identity** | StaffProfile.designation (display only) |
| **Authorization Source** | RoleAssignment → Role → Permission Classes |
| **Frontend Access** | RequireRoles → scopedHasRole(user.roles) |
| **Backend API** | Permission Classes → has_any_role() |
| **Data Scope** | InstitutionMembership + primary_campus |
| **Display Identity** | StaffProfile.designation / department |

---

## 8. IMPLEMENTATION STATUS

| Component | Status | Notes |
|-----------|--------|-------|
| Role Enum | ✅ Complete | All 14 roles defined |
| RoleAssignment | ✅ Working | Links User ↔ Institution ↔ Role |
| Permission Classes | ✅ Complete | 15+ permission classes |
| Frontend RequireRoles | ✅ Fixed | Librarian added to Library route/nav |
| Backend Permissions | ✅ Complete | IsLibrarianRole, IsAccountantRole, etc. |
| Frontend Navigation | ✅ Fixed | Librarian added to Library nav/route |
| Dedicated Pages | Partial | Only Teacher/Student/Parent have dedicated pages |
| Library API | ✅ Working | Books, Issues, Reservations, Copies |
| Library Reports | Partial | Permissions fixed, 500 errors on some |
| Reports Base | ❌ 404 | `/api/reports/` returns 404 |
| Library Sub-endpoints | ❌ 404 | `/reports/`, `/members/`, `/settings/`, `/` |

---

**Document Version**: 1.0  
**Last Updated**: Phase 61  
**Status**: Canonical Reference for Phase 61 Implementation