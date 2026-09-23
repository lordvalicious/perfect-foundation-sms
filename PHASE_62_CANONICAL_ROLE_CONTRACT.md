# PHASE 62 — CANONICAL ROLE CONTRACT

## Purpose
Defines the authoritative role taxonomy, hierarchy, and access rules for the Perfect Foundation SMS platform. This contract is binding for all backend authorization, frontend navigation, and provisioning logic.

---

## 1. Role Enum (Canonical Source: `backend/apps/accounts/models.py`)

```python
class Role(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Platform Super Admin"
    ADMIN = "admin", "Institution Admin"
    ORG_ADMIN = "org_admin", "Organization Administrator"
    HEAD_OFFICE = "head_office", "Head Office"
    PRINCIPAL = "principal", "Principal"
    VICE_PRINCIPAL = "vice_principal", "Vice Principal"
    CAMPUS_ADMIN = "campus_admin", "Campus Administrator"
    ACADEMIC = "academic", "Academic Administrator"
    ACCOUNTANT = "accountant", "Accountant"
    HR = "hr", "HR / Staff Officer"
    RECEPTIONIST = "receptionist", "Receptionist"
    LIBRARIAN = "librarian", "Librarian"
    GUARD = "guard", "Security Guard"
    NURSE = "nurse", "Nurse / Medical Officer"
    TEACHER = "teacher", "Teacher"
    PARENT = "parent", "Parent / Guardian"
    STUDENT = "student", "Student"
    STAFF = "staff", "Staff Member"
```

**Total Roles: 17**

---

## 2. Role Hierarchy (ROLE_RANK)

| Rank | Role | Description |
|------|------|-------------|
| 100 | SUPER_ADMIN | Platform Super Admin |
| 90 | ORG_ADMIN | Organization Administrator |
| 85 | HEAD_OFFICE | Head Office |
| 80 | ADMIN | Institution Admin |
| 70 | PRINCIPAL | Principal |
| 65 | VICE_PRINCIPAL | Vice Principal |
| 60 | CAMPUS_ADMIN | Campus Administrator |
| 55 | ACADEMIC | Academic Administrator |
| 50 | ACCOUNTANT | Accountant |
| 45 | HR | HR / Staff Officer |
| 40 | RECEPTIONIST | Receptionist |
| 35 | LIBRARIAN | Librarian |
| 30 | GUARD | Security Guard |
| 28 | NURSE | Nurse / Medical Officer |
| 25 | TEACHER | Teacher |
| 20 | STAFF | Staff Member |
| 10 | STUDENT | Student |
| 5 | PARENT | Parent / Guardian |

**Rule**: A user may only manage roles ranked strictly below their own (role_rank comparison).

---

## 3. Permission Classes (Canonical Source: `backend/apps/accounts/permissions.py`)

| Permission Class | Allowed Roles | Use Case |
|-----------------|---------------|----------|
| IsSuperAdmin | super_admin | Platform-level operations |
| IsAdminRole | super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin | Institution admin operations |
| IsAccountantRole | super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, accountant, hr | Finance + Library Reports |
| IsLibrarianRole | super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, librarian, teacher | Library Management |
| IsTeacherRole | super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, teacher | Classroom operations |
| IsStaffRole | super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, accountant, hr, receptionist, guard, nurse, teacher, staff | General staff portal |
| IsNurseRole | super_admin, admin, org_admin, head_office, principal, vice_principal, campus_admin, academic, nurse | Health Records |
| IsAcademicMemberRole | super_admin, admin, principal, vice_principal, campus_admin, academic, accountant, hr, receptionist, nurse, teacher, staff, parent, student | Read-only academic access |
| IsFinanceReaderRole | super_admin, admin, principal, vice_principal, campus_admin, academic, accountant, hr, parent, student | Finance read access |
| IsAnnouncementRole | All academic members (read), admin/academic/hr (write) | Announcements |

---

## 4. Module Access Matrix (Backend Authorization)

| Module | Primary Permission | Specialized Roles |
|--------|-------------------|-------------------|
| Library (Books/Issues/Reservations) | IsLibrarianRole | LIBRARIAN, TEACHER |
| Library Reports | IsAccountantRole + IsLibrarianRole* | ACCOUNTANT, LIBRARIAN |
| Finance | IsAccountantRole | ACCOUNTANT, HR |
| Finance Reports | IsAccountantRole | ACCOUNTANT |
| Staff Portal | IsStaffRole | ADMIN_OFFICER (staff), GUARD, NURSE, HR, RECEPTIONIST |
| Visitors | IsStaffRole | GUARD, RECEPTIONIST |
| HR | IsAccountantRole | HR |
| Payroll | IsAccountantRole | HR, ACCOUNTANT |
| Health Records | IsNurseRole | NURSE |
| Dashboard | IsAcademicMemberRole | All authenticated |
| Students | IsAcademicMemberRole | TEACHER, STAFF, STUDENT |
| Teachers | IsTeacherRole | TEACHER |
| Attendance | IsAcademicMemberRole | TEACHER, STAFF |
| Exams | IsAcademicMemberRole | TEACHER |
| Report Cards | IsAcademicMemberRole | TEACHER, STAFF, STUDENT |

*IsLibrarianRole added to library report views in code (commit e534ded) but NOT DEPLOYED.

---

## 5. Frontend Navigation Roles (Canonical Source: `frontend/src/App.jsx`)

| Route | RequireRoles |
|-------|--------------|
| /dashboard/ | super_admin, admin, principal, vice_principal, campus_admin, academic, accountant, hr, receptionist, librarian, guard, nurse, teacher, staff, student |
| /library/ | super_admin, admin, principal, academic, accountant, hr, librarian |
| /finance/ | super_admin, admin, principal, academic, accountant, hr |
| /staff/ | super_admin, admin, principal, academic, hr, receptionist, guard, nurse |
| /visitors/ | super_admin, admin, principal, academic, hr, receptionist, guard |
| /health-records/ | super_admin, admin, principal, academic, nurse |
| /hr/ | super_admin, admin, principal, academic, hr |
| /payroll/ | super_admin, admin, principal, academic, accountant, hr |
| /transport/ | super_admin, admin, principal, academic |
| /inventory/ | super_admin, admin, principal, academic |
| /hostel/ | super_admin, admin, principal, academic |
| /reports/ | super_admin, admin, principal, academic, accountant, hr |

**Note**: Frontend includes all specialized roles in navigation. Backend authorization is the enforcement layer.

---

## 6. Provisioning Rules

| Role | Default Institution | Default Campus | must_change_password | Designation | Department |
|------|-------------------|----------------|---------------------|-------------|------------|
| SUPER_ADMIN | Platform (none) | N/A | False | Super Admin | Platform |
| ADMIN | Institution | Main Campus | False | Admin | Administration |
| PRINCIPAL | Institution | Main Campus | False | Principal | School Leadership |
| VICE_PRINCIPAL | Institution | Main Campus | False | Vice Principal | School Leadership |
| CAMPUS_ADMIN | Institution | Assigned Campus | False | Campus Admin | Campus Leadership |
| ACADEMIC | Institution | Main Campus | False | Academic Admin | Academics |
| ACCOUNTANT | Institution | Main Campus | False | Accountant | Finance |
| HR | Institution | Main Campus | False | HR Officer | HR |
| RECEPTIONIST | Institution | Main Campus | False | Receptionist | Front Office |
| LIBRARIAN | Institution | Main Campus | False | Librarian | Library |
| GUARD | Institution | Main Campus | False | Security Guard | Security |
| NURSE | Institution | Main Campus | False | Nurse | Health |
| TEACHER | Institution | Assigned Campus | False | Teacher | Academic |
| STAFF | Institution | Assigned Campus | False | Staff Member | General |
| STUDENT | Institution | Assigned Campus | False | Student | Student |
| PARENT | Institution | N/A | False | Parent | Parent |

---

## 7. Specialized Role Provisioning Status (Phase 62)

| Role | Provisioned | Test Account | Institution | Login Works | Notes |
|------|-------------|--------------|-------------|-------------|-------|
| LIBRARIAN | ✅ | SA-EMP-00011 | 4 (Springfield Academy) | ✅ | sa_librarian.txt |
| ACCOUNTANT | ✅ | DEG-EMP-00031 | 2 (Demo Education Group) | ✅ | sa_accountant.txt |
| GUARD | ✅ | SA-EMP-00031 | 4 (Springfield Academy) | ✅ | sa_guard.txt |
| ADMIN_OFFICER | ✅ | SA-EMP-00041 | 4 (Springfield Academy) | ✅ | Uses STAFF role (no ADMIN_OFFICER role) |
| NURSE | ✅ | SA-EMP-0002 | 4 (Springfield Academy) | ✅* | Requires school_code=SPR-J4839 |
| HR | ✅ | hr.gvc | 2 (Demo Education Group) | ✅ | sa_hr.txt |
| RECEPTIONIST | ✅ | reception.gvc | 2 (Demo Education Group) | ✅ | sa_receptionist.txt |
| TRANSPORT | ❌ | — | — | — | ROLE_NOT_DEFINED |
| INVENTORY | ❌ | — | — | — | ROLE_NOT_DEFINED |
| HOSTEL | ❌ | — | — | — | ROLE_NOT_DEFINED |
| DRIVER | ❌ | — | — | — | ROLE_NOT_DEFINED |
| DRIVER_SECURITY | ❌ | — | — | — | ROLE_NOT_DEFINED |

*School code required due to duplicate username across institutions 4 and 5.

---

## 8. Deployment Contract

### Code Commits (Ready for Deployment)
- **e534ded**: Library endpoints (LibraryRootView, LibraryReportsView, LibraryMembersView, LibrarySettingsView), ReportsRootView, Library report permissions (IsLibrarianRole added to 10 views)
- **a5d254d**: NURSE role added to Role enum, ROLE_RANK, primary_role priority, IsNurseRole permission, IsStaffRole updated, IsAcademicMemberRole updated
- **abc3369**: Force Vercel rebuild

### Vercel Deployment Status
- **Current Deployed Commit**: Unknown (pre-e534ded)
- **Required Deployed Commit**: abc3369 (or later)
- **Blockers**: D-006, D-007, D-010 — all code fixed, deployment pending

---

## 9. Contract Enforcement

1. **Backend**: All authorization checks use permission classes from `apps.accounts.permissions`
2. **Frontend**: Navigation uses `RequireRoles` array matching backend permission classes
3. **Provisioning**: Scripts in `backend/phase57_fix_provisioning.py` enforce role assignments
4. **Testing**: E2E tests in `PHASE_62_SPECIALIZED_ROLE_E2E.csv` validate contract compliance
5. **CI/CD**: Vercel deployment must include latest commits for contract compliance

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Phase 60 | Initial canonical role contract |
| 1.1 | Phase 61 | Added LIBRARIAN to Library route/nav, fixed Library report permissions |
| 1.2 | Phase 62 | Added NURSE role, IsNurseRole permission, fixed Nurse provisioning |

---

**CONTRACT STATUS: ACTIVE — DEPLOYMENT PENDING FOR v1.2**

This contract is the single source of truth for role definitions, hierarchy, and access control. All code, configuration, and testing must align with this contract.