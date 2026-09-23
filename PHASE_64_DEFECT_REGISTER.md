# Phase 64 — Defect Register

## D-001: Vercel Deployment Pipeline Broken (P0 — Critical)
- **Description**: Vercel serverless Python functions are not deploying the latest code from the repository. Code changes in git are not reaching the live production backend at `perfect-foundation-sms.vercel.app`.
- **Status**: OPEN — Deployment pipeline blocker confirmed
- **Evidence**: 
  - `/api/deploy-test/` returns 404 in production despite being in codebase
  - `/api/health/` returns stale `"deploy_version": "63-test-3"` instead of dynamic commit SHA
  - Multiple "force redeploy" commits (`abc3369`, `fea1f3a`, `1581952`) pushed but blocker persists
- **Root Cause**: Vercel Python serverless function build/artifact issue — old function versions persist after new commits
- **Fix Required**: Fix Vercel deployment configuration (vercel.json rootDirectory/functions/python settings, backend vercel.json alignment, build command execution)
- **Affected Roles**: All specialized roles (Librarian, Accountant, Guard, Admin Officer, Nurse, HR, Receptionist, Student2, Student3, Transport, Inventory, Hostel, Driver, Driver Security) — ALL blocked from production certification
- **Related Code Fixes**: D-005 (Nurse role enum), D-006 (Library sub-endpoints), D-007 (Reports base), D-008 (Library reports 500 errors), D-010 (Specialized modules), D-011 (Missing roles) — all code fixes exist but not deployed

## D-002: `/api/deploy-test/` Endpoint Not Deployed
- **Description**: The deployment verification endpoint exists in `backend/config/urls.py` at line 77 but returns 404 in production.
- **Status**: OPEN
- **Evidence**: `Invoke-WebRequest` returns 404; endpoint code exists but Vercel function not deployed
- **Fix**: Verify Vercel correctly packages and deploys Python serverless functions

## D-003: Library Routes Not Deployed
- **Description**: `/api/library/`, `/api/library/books/`, `/api/library/issues/`, `/api/library/reservations/`, `/api/library/reports/`, `/api/library/members/`, `/api/library/settings/` all return 404 in production.
- **Status**: OPEN — Code exists in `backend/apps/library/urls.py` and `backend/apps/library/views.py` but not deployed
- **Fix**: Fix Vercel deployment pipeline

## D-004: Reports Routes Not Deployed
- **Description**: `/api/reports/`, `/api/reports/library/` and all sub-endpoints return 404 in production.
- **Status**: OPEN — Code exists in `backend/apps/reports/urls.py` and `backend/apps/reports/views.py` but not deployed
- **Fix**: Fix Vercel deployment pipeline

## D-005: Nurse Role Enum and Permissions (CODE FIXED, DEPLOYED)
- **Description**: NURSE role added to Role enum (models.py:11-29), rank 28; IsNurseRole permission added; Nurse accounts fixed (must_change_password=False, role=nurse); login works with school_code=SPR-J4839
- **Status**: CODE FIXED — Fix deployed? Unverified due to deployment blocker
- **Evidence**: Code changes committed; nurse login tested with school_code parameter
- **Awaiting**: Production deployment verification

## D-006: Library Sub-Endpoints Code Fixed, Not Live
- **Description**: Library routes (`/api/library/books/`, `/api/library/issues/`, `/api/library/reservations/`, `/api/library/reports/`, `/api/library/members/`, `/api/library/settings/`) code fixed but NOT LIVE in production — all return 404.
- **Status**: CODE FIXED, NOT DEPLOYED
- **Evidence**: Library URL patterns and views exist in git but `/api/library/` returns 404 in production
- **Awaiting**: Vercel deployment fix

## D-007: Reports Base Code Fixed, Not Live
- **Description**: ReportsRootView and 10 report views code added but NOT LIVE in production — `/api/reports/` returns 404.
- **Status**: CODE FIXED, NOT DEPLOYED
- **Evidence**: Reports code exists in git but production returns 404
- **Awaiting**: Vercel deployment fix

## D-008: Library Reports 500 Errors (Code Fixed, Not Deployed)
- **Description**: 6/10 detailed library report views return 500 in production when accessed via Accountant session. Code fix exists but not deployed to production.
- **Status**: CODE FIXED, NOT DEPLOYED
- **Evidence**: 6/10 reports return 500; problem is deployment-related (stale backend serving old code)
- **Awaiting**: Vercel deployment fix then retest

## D-009: Specialized Modules Not Confirmed Deployed
- **Description**: Visitors, HR, Payroll, Health Records modules code exists but not confirmed deployed to production. Endpoints return 404.
- **Status**: CODE FIXED, NOT DEPLOYED
- **Evidence**: Module URL patterns exist in `backend/config/urls.py` but production returns 404
- **Awaiting**: Vercel deployment fix

## D-010: Missing Roles in Role Enum
- **Description**: TRANSPORT, INVENTORY, HOSTEL, DRIVER, DRIVER_SECURITY roles not in Role enum; ADMIN_OFFICER uses STAFF role (no ADMIN_OFFICER enum entry)
- **Status**: CODE FIXED (NURSE added), OTHER ROLES STILL MISSING
- **Evidence**: NURSE role added to Role enum in models.py; other roles not yet added
- **Awaiting**: Production deployment verification after enum fixes

## D-011: Role-Enum Parity Across System
- **Description**: Role enum, RoleAssignment model, frontend RequireRoles, permission classes, navigation, route guards, and provisioning must all be consistent. Currently: NURSE added to enum; ADMIN_OFFICER uses STAFF role; TRANSPORT, INVENTORY, HOSTEL, DRIVER, DRIVER_SECURITY not in enum.
- **Status**: PARTIALLY FIXED
- **Evidence**: NURSE role added to models.py Role enum and IsNurseRole permission; other roles not added
- **Awaiting**: Full enum parity verification after deployment fix

## D-012: Frontend-Backend Parity for Specialized Roles
- **Description**: Frontend navigation and route guards reference specialized roles (Librarian, Accountant, Guard, etc.) but backend API endpoints return 404, causing parity failure.
- **Status**: CODE FIXED IN FRONTEND, NOT DEPLOYED IN BACKEND
- **Evidence**: Frontend (App.jsx, routes) has Librarian role added to Library route/nav; all specialized roles in navigation; but backend returns 404 for all specialized module endpoints
- **Awaiting**: Vercel deployment fix to make backend match frontend

## Summary of Defects

| Defect | Code Fix | Deployed | Blocked By |
|--------|----------|----------|------------|
| D-001 | N/A | NO | Vercel deployment pipeline |
| D-002 | ✅ (deploy-test endpoint) | NO | Vercel deployment |
| D-003 | ✅ (library routes) | NO | Vercel deployment |
| D-004 | ✅ (reports base) | NO | Vercel deployment |
| D-005 | ✅ (Nurse role) | ? | Deployment blocker |
| D-006 | ✅ (library sub-endpoints) | NO | Vercel deployment |
| D-007 | ✅ (reports base) | NO | Vercel deployment |
| D-008 | ✅ (reports 500 errors) | NO | Vercel deployment |
| D-009 | ✅ (modules) | NO | Vercel deployment |
| D-010 | ✅ (NURSE enum) | ? | Deployment blocker |
| D-011 | ✅ (partial parity) | ? | Deployment blocker |
| D-012 | ✅ (frontend) | NO | Vercel deployment |

**Overall Status**: Production certification BLOCKED until Vercel deployment pipeline is fixed. All code fixes from Phases 57-62 exist in git but are not reaching the live production backend.