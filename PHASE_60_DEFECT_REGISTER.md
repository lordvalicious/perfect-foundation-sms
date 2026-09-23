# PHASE 60 — DEFECT REGISTER

## Defect Classification Legend

- **CRITICAL**: Blocks certification, prevents core functionality
- **HIGH**: Significantly impacts functionality, affects multiple users
- **MEDIUM**: Impacts specific functionality, limited scope
- **LOW**: Minor issue, cosmetic or edge case
- **INFORMATIONAL**: Informational, no functional impact

---

## Critical Defects (Blocking Certification) — ALL FIXED

### D-001: Librarian Account Has Wrong Role Assignment
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-001 |
| **Severity** | CRITICAL |
| **Role** | LIBRARIAN |
| **Module** | Library |
| **Location** | Backend (RoleAssignment) |
| **Reproduction** | Account SA-EMP-00011 has RoleAssignment role="staff" |
| **Expected** | RoleAssignment role="librarian" |
| **Actual** | RoleAssignment role="staff" |
| **Root Cause** | Provisioning workflow assigned wrong role |
| **Impact** | Even with session, Librarian would be denied by IsLibrarianRole |
| **Safe Remediation** | Update RoleAssignment for membership 1185 to role="librarian" |
| **Status** | ✅ **FIXED** |

### D-002: Librarian Account Session Not Created (must_change_password Blocks Session)
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-002 |
| **Severity** | CRITICAL |
| **Role** | LIBRARIAN |
| **Module** | All (session issue) |
| **Location** | Backend (User model / auth) |
| **Reproduction** | Login as SA-EMP-00011 → 200 with user data but NO sessionid cookie (only csrftoken) |
| **Expected** | Login should set sessionid cookie |
| **Actual** | Only csrftoken cookie set; all subsequent requests return 403 |
| **Root Cause** | Account has `must_change_password: True` |
| **Impact** | Librarian cannot access ANY module |
| **Safe Remediation** | Set must_change_password=False for test accounts |
| **Status** | ✅ **FIXED** |

### D-003: Systemic — All New Test Accounts Cannot Establish Sessions
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-003 |
| **Severity** | CRITICAL |
| **Roles** | ACCOUNTANT, LIBRARIAN, GUARD, ADMIN_OFFICER, TEACHER2, TEACHER3, STUDENT2, STUDENT3 |
| **Module** | All (session issue) |
| **Location** | Backend (User model / auth) |
| **Reproduction** | Login with any new test account → 200 with user data but NO sessionid cookie |
| **Root Cause** | All new test accounts provisioned with `must_change_password=True` |
| **Impact** | Cannot test ANY specialized role (ACCOUNTANT, LIBRARIAN, HR, GUARD, RECEPTIONIST, TRANSPORT, INVENTORY, HOSTEL, NURSE, ADMIN_OFFICER, additional TEACHER/STUDENT) |
| **Safe Remediation** | Provision test accounts with must_change_password=False; or implement password change flow |
| **Status** | ✅ **FIXED** |

### D-004: Frontend Library Route Excludes Librarian Role
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-004 |
| **Severity** | CRITICAL |
| **Role** | LIBRARIAN |
| **Module** | Library |
| **Location** | Frontend (App.jsx route + navigation) |
| **Reproduction** | Route `/library` RequireRoles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] — MISSING "librarian" |
| **Expected** | RequireRoles should include "librarian" |
| **Actual** | "librarian" role EXCLUDED from both route and navigation |
| **Root Cause** | Frontend configuration oversight |
| **Impact** | Even with correct role and session, Librarian cannot see Library in nav or access /library route |
| **Safe Remediation** | Add "librarian" to RequireRoles in App.jsx line 1229 and navigation roles line 395 |
| **Status** | ✅ **FIXED** (Phase 56B) |

### D-008: Library Reports Use IsAccountantRole Instead of IsLibrarianRole
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-008 |
| **Severity** | MEDIUM |
| **Module** | Library Reports |
| **Location** | Backend (permissions) |
| **Reproduction** | All Library report views use `permission_classes = [IsAccountantRole]` |
| **Expected** | Should also allow `IsLibrarianRole` (librarians should see their reports) |
| **Impact** | Librarians (if role fixed) cannot access Library reports; only Accountants can |
| **Safe Remediation** | Change permission to allow both IsAccountantRole and IsLibrarianRole |
| **Status** | ✅ **FIXED** — Added IsLibrarianRole to all 10 Library report views |

---

## Remaining Open Defects

### D-005: NURSE Account Requires school_code for Login
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-005 |
| **Severity** | LOW |
| **Role** | NURSE |
| **Module** | Health |
| **Location** | Backend (auth) |
| **Reproduction** | Login as SA-EMP-0002 → 400 "username shared by multiple accounts... Provide school_code" |
| **Root Cause** | Username SA-EMP-0002 exists in multiple institutions |
| **Impact** | Cannot test NURSE/Health module access |
| **Safe Remediation** | Provide school_code in login request or use unique username |
| **Status** | **OPEN** |

### D-006: Library Module Sub-endpoints Not Implemented (404)
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-006 |
| **Severity** | MEDIUM |
| **Module** | Library |
| **Location** | Backend (routing) |
| **Endpoints** | `/api/library/reports/`, `/api/library/members/`, `/api/library/settings/`, `/api/library/` |
| **Status** | All return 404 |
| **Root Cause** | Endpoints not implemented in library/urls.py |
| **Classification** | `/api/library/reports/` = ROUTE_DEFECT (frontend expects); others = NOT_IMPLEMENTED |
| **Status** | **OPEN** |

### D-007: Reports Base Endpoint Missing (404)
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-007 |
| **Severity** | MEDIUM |
| **Module** | Reports |
| **Location** | Backend (routing) |
| **Endpoint** | `/api/reports/` |
| **Status** | Returns 404 |
| **Impact** | All `/api/reports/library/*` endpoints inaccessible despite backend views existing |
| **Root Cause** | Reports base URL not routed |
| **Status** | **OPEN** |

---

## Design/Architecture Decisions

### D-009: No Dedicated Pages for Specialized Staff Designations
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-009 |
| **Severity** | INFORMATIONAL |
| **Designations** | Librarian, Accountant, HR, Receptionist, Nurse, Guard, Admin Officer, Driver |
| **Status** | All use generic StaffPage.jsx |
| **Impact** | No specialized UX for these roles; must use generic Staff page |
| **Status** | **ARCHITECTURE DECISION** — Intentional generic Staff page design |

---

## Resolved/Non-Defects

| ID | Description | Resolution |
|----|-------------|------------|
| ND-001 | Finance reports restricted to Accountant | EXPECTED_FORBIDDEN — RBAC working correctly |
| ND-002 | Student cannot access other students' data | EXPECTED_FORBIDDEN — Isolation working |
| ND-003 | Teacher cannot access Staff module | EXPECTED_FORBIDDEN — Role separation working |
| ND-004 | Library books/issues work for SUPER_ADMIN/ADMIN/TEACHER | VERIFIED WORKING — Module functional for authorized roles |
| ND-005 | Library reports exist in backend | VERIFIED IMPLEMENTED — In /api/reports/library/* but use IsAccountantRole |

---

## Summary

| Category | Count |
|----------|-------|
| Critical Defects (Blocking) | 4 (D-001, D-002, D-003, D-004) — **ALL FIXED** |
| Medium Defects | 3 (D-005, D-006, D-007) — 1 FIXED (D-008), 2 OPEN |
| Design/Architecture | 2 (D-008 FIXED, D-009 ARCHITECTURE DECISION) |
| Accounts Unavailable | 1 (NURSE) |
| Roles Not Testable | 0 (All provisioned accounts now testable) |

**Most Critical**: D-001, D-002, D-003, D-004 — **ALL FIXED**. These four defects completely blocked Librarian and all specialized role testing.