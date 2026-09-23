# Phase 65 — Defect Register

## Deployment Blockers (P0 — Critical)

| Defect ID | Title | Description | Status | Evidence |
|-----------|-------|-------------|--------|----------|
| D-001 | Vercel Deployment Pipeline Broken | Vercel Python serverless functions not deploying latest code from repository; `/api/deploy-test/` returns 404 in production despite endpoint existing in source | CONFIRMED | `/api/deploy-test/` returns 404; `/api/health/` returns stale deploy version; multiple redeploy commits pushed but blocker persists |
| D-002 | `/api/deploy-test/` Not Deployed | Endpoint exists in `backend/config/urls.py` at line 77 but returns 404 in production | CONFIRMED | Production test: 404; Code: present at commit `0ab87f0` |
| D-003 | Library Routes Not Deployed | `/api/library/`, `/api/library/books/`, `/api/library/issues/`, `/api/library/reservations/`, `/api/library/reports/`, `/api/library/members/`, `/api/library/settings/` all return 404 in production | CONFIRMED | All library endpoints tested against `perfect-foundation-sms.vercel.app` return 404 |
| D-004 | Reports Routes Not Deployed | `/api/reports/`, `/api/reports/library/` and all sub-endpoints return 404 in production | CONFIRMED | All reports endpoints tested return 404 |
| D-005 | Nurse Role Enum and Permissions | NURSE role added to Role enum (models.py:11-29), rank 28; IsNurseRole permission added; Nurse accounts fixed (must_change_password=False, role=nurse); login works with school_code=SPR-J4839 | CODE_FIXED_NOT_DEPLOYED | Code fix present in git; deployment blocker prevents live verification; `/api/health-records/` status unknown |
| D-006 | Library Sub-Endpoints Code Fixed, Not Live | Library routes code fixed but NOT LIVE in production — all return 404 | CODE_FIXED_NOT_DEPLOYED | Code in `backend/apps/library/urls.py` and `backend/apps/library/views.py`; production returns 404 for all `/api/library/*` |
| D-007 | Reports Base Code Fixed, Not Live | ReportsRootView and 10 report views code added but NOT LIVE in production — `/api/reports/` returns 404 | CODE_FIXED_NOT_DEPLOYED | Code in `backend/apps/reports/urls.py` and `backend/apps/reports/views.py`; production returns 404 |
| D-008 | Library Reports 500 Errors | 6/10 detailed report views return 500 in production when accessed via Accountant session | CODE_FIXED_NOT_DEPLOYED | 6/10 reports return 500; problem is deployment-related (stale Django app serving old code); not resolvable without deployment fix |
| D-009 | Specialized Modules Not Confirmed Deployed | Visitors, HR, Payroll, Health Records modules code exists but not confirmed deployed to production | CODE_FIXED_NOT_DEPLOYED | Module URL patterns exist in `backend/config/urls.py` but production returns 404; status unverified |
| D-010 | Missing Roles Not Deployed | TRANSPORT, INVENTORY, HOSTEL, DRIVER, DRIVER_SECURITY roles not in Role enum; ADMIN_OFFICER uses STAFF role (no ADMIN_OFFICER in enum) | CODE_FIXED_NOT_DEPLOYED | NURSE added to enum in Phase 62; other roles not added; all code fixes pending deployment |
| D-011 | Role-Enum Parity Across System | Role enum, RoleAssignment, frontend RequireRoles, permission classes, navigation, route guards, provisioning, and StaffProfile designation must all be consistent | CODE_FIXED_NOT_DEPLOYED | NURSE added to models.py Role enum and IsNurseRole permission; ADMIN_OFFICER still uses STAFF role; other roles not in enum; frontend navigation updated but backend not deployed |
| D-012 | Frontend-Backend Parity for Specialized Roles | Frontend navigation and route guards reference specialized roles (Librarian, Accountant, Guard, etc.) but backend API endpoints return 404, causing parity failure | CODE_FIXED_NOT_DEPLOYED | Frontend (App.jsx, routes) has Librarian role added to Library route/nav; all specialized roles in navigation; but backend returns 404 for all specialized module endpoints |

## Code-Only Defects (Not Deployed)

These 8 defects have fixes in the repository code but have not been deployed to production:

- **D-005**: Nurse role enum and school_code login
- **D-006**: Library sub-endpoints
- **D-007**: Reports base endpoint
- **D-008**: Library reports 500 errors
- **D-009**: Specialized modules (Visitors, HR, Payroll, Health)
- **D-010**: Missing roles (Transport, Inventory, Hostel, Driver, Driver Security)
- **D-011**: Role-enum parity across system
- **D-012**: Frontend-backend parity for specialized roles

## Deployment Blocker Defect (P0)

| Defect ID | Title | Description | Root Cause | Status |
|-----------|-------|-------------|------------|--------|
| D-001 | Vercel Deployment Pipeline Broken | Vercel Python serverless function artifact not updating after new commits pushed to GitHub | Vercel Python serverless deployment pipeline fundamentally broken; old function versions persist; `/api/deploy-test/` returns 404 in production; `/api/health/` returns stale deploy version | CONFIRMED — blocking ALL specialized role certification |

## Defect Status Summary

| Status | Count | Defects |
|--------|-------|---------|
| CONFIRMED (deployment blocker) | 1 | D-001 |
| CODE_FIXED_NOT_DEPLOYED | 8 | D-005 through D-012 |
| Total Blocked | 9 | D-001 through D-012 |

## Resolution Path

All defects are blocked by **D-001 (Vercel Deployment Pipeline Broken)**. Until the Vercel Python serverless function deployment pipeline is repaired so that the expected commit SHA is verified live at `/api/deploy-test/`, no specialized role endpoints, module accesses, or authorization tests can be certified in production.

**Prerequisite for all defect resolution**: Fix the Vercel deployment pipeline. All other defect fixes (D-005 through D-012) are CODE_ONLY until the deployment pipeline delivers the code to the live production backend.