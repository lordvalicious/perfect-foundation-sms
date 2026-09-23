# PHASE 55 — ROLE × MODULE DEFECTS REPORT

## Defect Classification Legend

- **ROLE_AUTHORIZATION_DEFECT**: Backend rejects role that should have access
- **ROLE_NAVIGATION_DEFECT**: Frontend menu missing for designated role
- **ROLE_API_ROUTE_DEFECT**: API endpoint returns 404/500
- **ROLE_MODULE_ROUTE_DEFECT**: Frontend page returns 404
- **ROLE_MODULE_SERVER_DEFECT**: API returns 500
- **ROLE_ACCOUNT_DEFECT**: Test account has wrong role or broken provisioning
- **ROLE_SESSION_DEFECT**: Session cookie not created on login
- **ROLE_MODULE_ROUTE_DEFECT**: API endpoint returns 404
- **EXPECTED_FORBIDDEN**: Role intentionally not authorized

---

## Critical Defects

### D-001: Librarian Account Has Wrong Role Assignment
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-001 |
| **Role** | LIBRARIAN |
| **Module** | Library |
| **Location** | Backend (role assignment) |
| **Reproduction** | Login as SA-EMP-00011 (Librarian account) → /api/auth/me/ returns primary_role: "staff" not "librarian" |
| **Expected** | Account should have primary_role: "librarian" with Library module access |
| **Actual** | Account has primary_role: "staff"; memberships show role: "staff" |
| **HTTP Status** | Login: 200; /api/auth/me/: 403 (no session); /api/library/books/: 403 |
| **Root Cause** | Account provisioning assigned "staff" role instead of "librarian" role |
| **Impact** | Librarian cannot access Library module despite being provisioned for it |
| **Safe Remediation** | Update RoleAssignment for membership 1185 to role="librarian"; ensure Librarian role has Library permissions |

### D-002: Librarian Account Session Not Created (must_change_password Blocks Session)
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-002 |
| **Role** | LIBRARIAN |
| **Module** | All (session issue) |
| **Location** | Backend (auth/session) |
| **Reproduction** | Login as SA-EMP-00011 → 200 with user data but NO sessionid cookie set (only csrftoken) |
| **Expected** | Login should set sessionid cookie for authenticated requests |
| **Actual** | Only csrftoken cookie set; all subsequent requests return 403 |
| **HTTP Status** | Login: 200; /api/auth/me/: 403; all module endpoints: 403 |
| **Root Cause** | Account has `must_change_password: True` which prevents full session establishment |
| **Impact** | Librarian cannot access ANY module including Library |
| **Safe Remediation** | Either: (a) Set must_change_password=False for test accounts, or (b) Implement password change flow that establishes session after change |

### D-003: New Test Accounts Cannot Establish Sessions (Systemic)
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-003 |
| **Role** | ACCOUNTANT, TEACHER2, TEACHER3, STUDENT2, STUDENT3, GUARD, ADMIN_OFFICER |
| **Module** | All (session issue) |
| **Location** | Backend (auth/session) |
| **Reproduction** | Login with any new test account credentials → 200 with user data but NO sessionid cookie |
| **Expected** | All valid credentials should establish session |
| **Actual** | Only csrftoken cookie set; all subsequent requests return 403 |
| **HTTP Status** | Login: 200; all subsequent requests: 403 |
| **Root Cause** | All new test accounts have `must_change_password: True` which prevents session establishment |
| **Impact** | Cannot test specialized roles (ACCOUNTANT, LIBRARIAN, HR, GUARD, RECEPTIONIST, TRANSPORT, INVENTORY, HOSTEL, NURSE, ADMIN_OFFICER, GUARD) |
| **Safe Remediation** | Provision test accounts with must_change_password=False or implement password change flow |

### D-004: Librarian Role Not Assigned to Librarian Account
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-004 |
| **Role** | LIBRARIAN |
| **Module** | Library |
| **Location** | Backend (RBAC) |
| **Reproduction** | Account SA-EMP-00011 (username suggests Librarian) has role "staff" not "librarian" |
| **Expected** | Account with username SA-EMP-00011 should have role "librarian" |
| **Actual** | RoleAssignment shows role: "staff" |
| **Root Cause** | Provisioning workflow assigned wrong role |
| **Impact** | Even if session worked, Librarian role permissions would not apply |
| **Safe Remediation** | Update RoleAssignment for membership 1185 from role="staff" to role="librarian" |

### D-005: NURSE Account Requires school_code for Login
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-005 |
| **Role** | NURSE |
| **Module** | Health |
| **Location** | Backend (auth) |
| **Reproduction** | Login as SA-EMP-0002 → 400 "username or email is shared by multiple accounts in different schools. Provide your school_code to log in." |
| **Expected** | Login should work with username/password |
| **Actual** | Login fails with 400 requiring school_code |
| **HTTP Status** | 400 |
| **Root Cause** | Username SA-EMP-0002 exists in multiple institutions |
| **Impact** | Cannot test NURSE/Health module access |
| **Safe Remediation** | Provide school_code in login request or use unique username |

### D-006: Library Module Sub-endpoints Not Implemented (404)
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-006 |
| **Role** | LIBRARIAN, SUPER_ADMIN, ADMIN, TEACHER |
| **Module** | Library |
| **Location** | Backend (routing) |
| **Reproduction** | Access /api/library/reports/, /api/library/members/, /api/library/settings/, /api/library/ |
| **Expected** | Library sub-modules should be accessible |
| **Actual** | All return 404 |
| **HTTP Status** | 404 |
| **Root Cause** | Library sub-endpoints not implemented in URL routing |
| **Impact** | Cannot access Library reports, members management, settings |
| **Safe Remediation** | Implement missing Library endpoints in URL configuration |

### D-007: Reports Endpoint Returns 404
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-007 |
| **Role** | SUPER_ADMIN |
| **Module** | Reports |
| **Location** | Backend (routing) |
| **Reproduction** | Access /api/reports/ as SUPER_ADMIN |
| **Expected** | Reports dashboard/list should be accessible |
| **Actual** | Returns 404 |
| **HTTP Status** | 404 |
| **Root Cause** | Reports endpoint not implemented in URL routing |
| **Impact** | Cannot access reports module via API |
| **Safe Remediation** | Implement /api/reports/ endpoint |

---

## Non-Defects (Expected Behavior)

### ND-001: Finance Reports Restricted to Accountant Role
| Module | Finance |
|--------|---------|
| Behavior | /api/finance/reports/trial-balance/ returns 403 for TEACHER, STAFF, STUDENT |
| Classification | EXPECTED_FORBIDDEN |
| Reason | Role-based access control working correctly |

### ND-002: Student Cannot Access Other Students' Data
| Module | Students |
|--------|---------|
| Behavior | Student gets 403 on /api/students/ (list) |
| Classification | EXPECTED_FORBIDDEN |
| Reason | Student isolation working correctly |

### ND-003: Teacher Cannot Access Staff Module
| Module | Staff |
|--------|---------|
| Behavior | Teacher gets 403 on /api/staff/me/ |
| Classification | EXPECTED_FORBIDDEN |
| Reason | Teacher ≠ Staff role separation working correctly |

---

## Accounts Not Available for Testing

| Role | Account | Reason |
|------|---------|--------|
| ACCOUNTANT | DEG-EMP-00031 | Session not created (must_change_password) |
| LIBRARIAN | SA-EMP-00011 | Wrong role + no session |
| HR | Not provisioned | No test account |
| RECEPTIONIST | Not provisioned | No test account |
| TRANSPORT | Not provisioned | No test account |
| INVENTORY | Not provisioned | No test account |
| HOSTEL | Not provisioned | No test account |
| GUARD | SA-EMP-00031 | No session |
| ADMIN_OFFICER | SA-EMP-00041 | No session |
| NURSE | SA-EMP-0002 | Requires school_code |

---

## Summary

| Category | Count |
|----------|-------|
| Critical Defects | 7 |
| Expected Forbidden | 3 |
| Accounts Unavailable | 11 |
| Roles Not Testable | 11 (ACCOUNTANT, LIBRARIAN, HR, RECEPTIONIST, TRANSPORT, INVENTORY, HOSTEL, GUARD, ADMIN_OFFICER, NURSE, plus TEACHER2/3, STUDENT2/3) |

**Most Critical**: D-001, D-002, D-003 (block Librarian and all new specialized role testing)