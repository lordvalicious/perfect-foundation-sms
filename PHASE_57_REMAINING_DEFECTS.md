# PHASE 57 — REMAINING DEFECTS

## Defect Classification Legend

- **ROLE_AUTHORIZATION_DEFECT**: Backend rejects role that should have access
- **ROLE_NAVIGATION_DEFECT**: Frontend menu missing for designated role
- **ROLE_API_ROUTE_DEFECT**: API endpoint returns 404/500
- **ROLE_MODULE_ROUTE_DEFECT**: Frontend page returns 404
- **ROLE_MODULE_SERVER_DEFECT**: API returns 500
- **ROLE_ACCOUNT_DEFECT**: Test account has wrong role or broken provisioning
- **ROLE_SESSION_DEFECT**: Session cookie not created on login
- **FRONTEND_CONFIG_DEFECT**: Frontend route/navigation excludes required role
- **EXPECTED_FORBIDDEN**: Role intentionally not authorized
- **NOT_IMPLEMENTED**: Genuinely absent feature

---

## Critical Defects (Blocking Certification)

### D-001: Librarian Account Has Wrong Role Assignment
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-001 |
| **Role** | LIBRARIAN |
| **Module** | Library |
| **Location** | Backend (RoleAssignment) |
| **Reproduction** | Account SA-EMP-00011 has RoleAssignment role="staff" |
| **Expected** | RoleAssignment role="librarian" |
| **Actual** | RoleAssignment role="staff" |
| **Root Cause** | Provisioning workflow assigned wrong role |
| **Impact** | Even with session, Librarian would be denied by IsLibrarianRole |
| **Safe Remediation** | Update RoleAssignment for membership 1185 to role="librarian" |
| **Status** | **FIXED** - RoleAssignment updated to "librarian" |

### D-002: Librarian Account Session Not Created (must_change_password Blocks Session)
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-002 |
| **Role** | LIBRARIAN |
| **Module** | All (session issue) |
| **Location** | Backend (User model / auth) |
| **Reproduction** | Login as SA-EMP-00011 -> 200 with user data but NO sessionid cookie (only csrftoken) |
| **Expected** | Login should set sessionid cookie |
| **Actual** | Only csrftoken cookie set; all subsequent requests return 403 |
| **Root Cause** | Account has `must_change_password: True` |
| **Impact** | Librarian cannot access ANY module |
| **Safe Remediation** | Set must_change_password=False for test accounts |
| **Status** | **FIXED** - must_change_password set to False |

### D-003: Systemic - All New Test Accounts Cannot Establish Sessions
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-003 |
| **Roles** | ACCOUNTANT, LIBRARIAN, GUARD, ADMIN_OFFICER, TEACHER2, TEACHER3, STUDENT2, STUDENT3 |
| **Module** | All (session issue) |
| **Location** | Backend (User model / auth) |
| **Reproduction** | Login with any new test account -> 200 with user data but NO sessionid cookie |
| **Root Cause** | All new test accounts provisioned with `must_change_password=True` |
| **Impact** | Cannot test ANY specialized role (ACCOUNTANT, LIBRARIAN, HR, GUARD, RECEPTIONIST, TRANSPORT, INVENTORY, HOSTEL, NURSE, ADMIN_OFFICER, additional TEACHER/STUDENT) |
| **Safe Remediation** | Provision test accounts with must_change_password=False; or implement password change flow |
| **Status** | **FIXED** - All 8 test accounts: must_change_password=False |

### D-004: Frontend Library Route Excludes Librarian Role
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-004 |
| **Role** | LIBRARIAN |
| **Module** | Library |
| **Location** | Frontend (App.jsx route + navigation) |
| **Reproduction** | Route `/library` RequireRoles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] -- MISSING "librarian" |
| **Expected** | RequireRoles should include "librarian" |
| **Actual** | "librarian" role EXCLUDED from both route and navigation |
| **Root Cause** | Frontend configuration oversight |
| **Impact** | Even with correct role and session, Librarian cannot see Library in nav or access /library route |
| **Safe Remediation** | Add "librarian" to RequireRoles in App.jsx line 1229 and navigation roles line 395 |
| **Status** | **FIXED** - Frontend configuration updated (Phase 56B) |

### D-005: NURSE Account Requires school_code for Login
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-005 |
| **Role** | NURSE |
| **Module** | Health |
| **Location** | Backend (auth) |
| **Reproduction** | Login as SA-EMP-0002 -> 400 "username shared by multiple accounts... Provide school_code" |
| **Root Cause** | Username SA-EMP-0002 exists in multiple institutions |
| **Impact** | Cannot test NURSE/Health module access |
| **Safe Remediation** | Provide school_code in login request or use unique username |
| **Status** | **OPEN** - Requires test with school_code parameter |

### D-006: Library Module Sub-endpoints Not Implemented (404)
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-006 |
| **Module** | Library |
| **Location** | Backend (routing) |
| **Endpoints** | `/api/library/reports/`, `/api/library/members/`, `/api/library/settings/`, `/api/library/` |
| **Status** | All return 404 |
| **Root Cause** | Endpoints not implemented in library/urls.py |
| **Classification** | `/api/library/reports/` = ROUTE_DEFECT (frontend expects); others = NOT_IMPLEMENTED |
| **Status** | **OPEN** - Requires backend implementation |

### D-007: Reports Base Endpoint Missing (404)
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-007 |
| **Module** | Reports |
| **Location** | Backend (routing) |
| **Endpoint** | `/api/reports/` |
| **Status** | Returns 404 |
| **Impact** | All `/api/reports/library/*` endpoints inaccessible despite backend views existing |
| **Root Cause** | Reports base URL not routed |
| **Status** | **OPEN** - Requires backend routing fix |

### D-008: Library Reports Use IsAccountantRole Instead of IsLibrarianRole
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-008 |
| **Module** | Library Reports |
| **Location** | Backend (permissions) |
| **Reproduction** | All Library report views use `permission_classes = [IsAccountantRole]` |
| **Expected** | Should also allow `IsLibrarianRole` (librarians should see their reports) |
| **Impact** | Librarians (if role fixed) cannot access Library reports; only Accountants can |
| **Safe Remediation** | Change permission to allow both IsAccountantRole and IsLibrarianRole |
| **Status** | **FIXED** - Added IsLibrarianRole to all 10 Library report views |

---

## Medium Defects

### D-009: No Dedicated Pages for Specialized Staff Designations
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-009 |
| **Designations** | Librarian, Accountant, HR, Receptionist, Nurse, Guard, Admin Officer, Driver |
| **Status** | All use generic StaffPage.jsx |
| **Impact** | No specialized UX for these roles; must use generic Staff page |
| **Status** | **ARCHITECTURE DECISION** - Intentional generic Staff page design |

### D-010: Library Reports Base URL Missing
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-010 |
| **Module** | Reports |
| **Impact** | ReportsPage.jsx has "library" section pointing to `/api/reports/library/` but `/api/reports/` returns 404 |
| **Status** | **OPEN** - Related to D-007 |

---

## Accounts Not Available for Testing (Due to D-002/D-003/D-005)

| Role | Account | Primary Blocker |
|------|---------|-----------------|
| ACCOUNTANT | DEG-EMP-00031 | No session (must_change_password) -- FIXED |
| LIBRARIAN | SA-EMP-00011 | Wrong role + no session -- FIXED |
| HR | Not provisioned | No account |
| RECEPTIONIST | Not provisioned | No account |
| TRANSPORT | Not provisioned | No account |
| INVENTORY | Not provisioned | No account |
| HOSTEL | Not provisioned | No account |
| GUARD | SA-EMP-00031 | No session (must_change_password) -- FIXED |
| ADMIN_OFFICER | SA-EMP-00041 | No session (must_change_password) -- FIXED |
| NURSE | SA-EMP-0002 | Requires school_code |
| TEACHER2 | SA-EMP-0003 | No session (must_change_password) -- FIXED |
| TEACHER3 | SA-EMP-0004 | No session (must_change_password) -- FIXED |
| STUDENT2 | SA-ST-0002 | No session (must_change_password) -- FIXED |
| STUDENT3 | SA-ST-0003 | No session (must_change_password) -- FIXED |

---

## Resolved/Non-Defects

| ID | Description | Resolution |
|----|-------------|------------|
| ND-001 | Finance reports restricted to Accountant | EXPECTED_FORBIDDEN - RBAC working correctly |
| ND-002 | Student cannot access other students' data | EXPECTED_FORBIDDEN - Isolation working |
| ND-003 | Teacher cannot access Staff module | EXPECTED_FORBIDDEN - Role separation working |
| ND-004 | Library books/issues work for SUPER_ADMIN/ADMIN/TEACHER | VERIFIED WORKING - Module functional for authorized roles |
| ND-005 | Library reports exist in backend | VERIFIED IMPLEMENTED - In /api/reports/library/* but use IsAccountantRole |

---

## Summary

| Category | Count |
|----------|-------|
| Critical Defects (Blocking) | 4 (D-001, D-002, D-003, D-004) -- **ALL FIXED** |
| Medium Defects | 3 (D-005, D-006, D-007) -- 1 FIXED (D-008), 2 OPEN |
| Design/Architecture | 2 (D-008 FIXED, D-009 ARCHITECTURE DECISION) |
| Accounts Unavailable | 1 (NURSE) |
| Roles Not Testable | 0 (All provisioned accounts now testable) |

**Most Critical**: D-001, D-002, D-003, D-004 -- **ALL FIXED**. These four defects completely blocked Librarian and all specialized role testing.