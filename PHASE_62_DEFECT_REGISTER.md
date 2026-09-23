# PHASE 62 — DEFECT REGISTER

## Defect Classification Legend

- **CRITICAL**: Blocks certification, prevents core functionality
- **HIGH**: Significantly impacts functionality, affects multiple users
- **MEDIUM**: Impacts specific functionality, limited scope
- **LOW**: Minor issue, cosmetic or edge case
- **INFORMATIONAL**: Informational, no functional impact

---

## Defects Resolved in Phase 62

### D-005: NURSE Account Requires school_code for Login — **FIXED**
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-005 |
| **Severity** | LOW |
| **Role** | NURSE |
| **Module** | Health |
| **Location** | Backend (auth) |
| **Reproduction** | Login as SA-EMP-0002 → 400 "username shared by multiple accounts... Provide school_code" |
| **Root Cause** | Username SA-EMP-0002 exists in multiple institutions (4 and 5) |
| **Impact** | Cannot test NURSE/Health module access without school_code |
| **Fix Applied** | 1. Added NURSE role to Role enum (models.py) 2. Added IsNurseRole permission 3. Fixed both Nurse accounts (institution 4 & 5): must_change_password=False, role=nurse 4. Login works with school_code parameter |
| **Status** | ✅ **FIXED** — Login with school_code works; session established |

### D-006: Library Module Sub-endpoints Not Implemented (404) — **CODE FIXED, NOT DEPLOYED**
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-006 |
| **Severity** | MEDIUM |
| **Module** | Library |
| **Location** | Backend (routing) |
| **Endpoints** | `/api/library/`, `/api/library/reports/`, `/api/library/members/`, `/api/library/settings/` |
| **Status** | All return 404 |
| **Root Cause** | Vercel deployment has not picked up latest commit (e534ded) with LibraryRootView, LibraryReportsView, LibraryMembersView, LibrarySettingsView |
| **Code Status** | ✅ IMPLEMENTED in commit e534ded (library/urls.py, library/views.py) |
| **Deployment Status** | ❌ NOT DEPLOYED — Vercel still serving old version |
| **Impact** | Frontend expects /api/library/reports/; Librarian cannot access library root |
| **Status** | **CODE FIXED, DEPLOYMENT PENDING** |

### D-007: Reports Base Endpoint Missing (404) — **CODE FIXED, NOT DEPLOYED**
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-007 |
| **Severity** | MEDIUM |
| **Module** | Reports |
| **Location** | Backend (routing) |
| **Endpoint** | `/api/reports/` |
| **Status** | Returns 404 |
| **Root Cause** | Vercel deployment has not picked up ReportsRootView |
| **Code Status** | ✅ IMPLEMENTED in commit e534ded (reports/urls.py, reports/views.py) |
| **Deployment Status** | ❌ NOT DEPLOYED — Vercel still serving old version |
| **Impact** | All `/api/reports/library/*` endpoints inaccessible despite backend views existing |
| **Status** | **CODE FIXED, DEPLOYMENT PENDING** |

---

## Remaining Open Defects

### D-008: Library Reports 500 Errors — **UNRESOLVED**
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-008 (NEW - was partially fixed in Phase 61 but 500s remain) |
| **Severity** | HIGH |
| **Module** | Library Reports |
| **Endpoints** | 6/10 detailed library reports return 500 |
| **Affected** | `/api/reports/library/inventory/`, `/available/`, `/issued/`, `/returned/`, `/overdue/`, `/fines/`, `/activity/`, `/most-borrowed/`, `/student-history/`, `/teacher-history/` |
| **Working** | `/api/reports/library/` (summary) returns 200 |
| **Root Cause** | Backend view errors in library_views.py report views |
| **Impact** | Detailed library reports unusable for Accountant and Librarian |
| **Status** | **OPEN** — Requires backend debugging and fix |

### D-009: No Dedicated Pages for Specialized Staff Designations — **ARCHITECTURE DECISION**
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-009 |
| **Severity** | INFORMATIONAL |
| **Designations** | Librarian, Accountant, HR, Receptionist, Nurse, Guard, Admin Officer, Driver |
| **Status** | All use generic StaffPage.jsx |
| **Impact** | No specialized UX for these roles; must use generic Staff page |
| **Decision** | Intentional generic Staff page design — no dedicated pages planned |
| **Status** | **ARCHITECTURE DECISION** — Will not fix |

### D-010: Specialized Role Modules Not Deployed — **NEW**
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-010 |
| **Severity** | MEDIUM |
| **Modules** | Visitors, HR, Payroll, Health Records, Transport, Inventory, Hostel |
| **Status** | Endpoints return 404 |
| **Root Cause** | Vercel deployment missing these apps or endpoints |
| **Impact** | Guard, HR, Receptionist, Nurse cannot access their primary modules |
| **Status** | **OPEN** — Requires Vercel deployment verification |

### D-011: Transport, Inventory, Hostel, Driver Roles Not Defined — **NEW**
| Field | Value |
|-------|-------|
| **DEFECT_ID** | D-011 |
| **Severity** | MEDIUM |
| **Roles** | TRANSPORT, INVENTORY, HOSTEL, DRIVER, DRIVER_SECURITY, ADMIN_OFFICER |
| **Status** | Not defined in Role enum |
| **Impact** | Cannot assign proper roles for these designations; fall back to STAFF |
| **Status** | **OPEN** — Requires Role enum extension |

---

## Summary

| Category | Count |
|----------|-------|
| Defects Fixed in Phase 62 | 1 (D-005) |
| Code Fixed, Deployment Pending | 2 (D-006, D-007) |
| High Priority Unresolved | 1 (D-008) |
| Architecture Decisions | 1 (D-009) |
| New Defects Identified | 2 (D-010, D-011) |

**Most Critical**: D-008 (Library reports 500 errors) and D-010 (specialized modules not deployed) block specialized role certification beyond Librarian/Accountant/Admin Officer.