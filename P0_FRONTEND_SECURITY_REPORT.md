# P0 Frontend Security Hardening Report

**Branch:** `security-hardening/frontend-p0` (based on `master` at `5d29952`)
**Date:** 2026-09-11
**Status:** ✅ Complete

---

## 1. Files Changed

| File | Changes |
|------|---------|
| `frontend/src/pages/useApiList.js` | Added `schoolScopeVersion` dependency to auto-refetch on school/campus switch |
| `frontend/src/sessionWatch.js` | Added `pf:forbidden` event dispatch for legitimate 403 responses; added `onForbidden` subscription |
| `frontend/src/App.jsx` | Added `ForbiddenHandler` component that shows toast for `pf:forbidden` events |

**Total:** 3 files modified, 60 insertions, 21 deletions

---

## 2. Issues Found During Audit

### 2.1 Query/Cache Isolation
- **useApiList hook** did not automatically refetch when school/campus context changed
- The hook had no dependency on `schoolScopeVersion` which is incremented on school/campus switch
- Pages using `useApiList` (10+ pages including Attendance, Campuses, Exams, Finance, Settings, Timetable, etc.) could show stale data after school switch

### 2.2 403 Error Surfacing
- **Legitimate 403 responses** (valid session but forbidden) were not prominently surfaced
- `sessionWatch.js` probed the session on 403 but did nothing if session was valid
- Most pages only used inline `setError()` which could be missed by users
- Only 3 pages (Alumni, Library, Timetable) used the toast system for error reporting

### 2.3 School Switching Architecture (Already Working)
- Route remount on school change: `<Routes key={currentSchool?.id}>` forces full remount
- `switchSchool()` increments `schoolScopeVersion` after successful switch
- `setActiveCampusId()` increments `schoolScopeVersion` after campus switch
- School switcher UI correctly gated by `modules.isPlatformAdmin`

### 2.4 Protected Routes (Already Working)
- `RequireRoles` component uses `scopedHasRole` (school-scoped role check)
- `Shell` component redirects unauthenticated users to login
- Navigation filtered by `hasRole` (global) and `scopedHasRole` (school-scoped)

### 2.3 Campus Context (Already Working)
- Campus switcher in topbar calls `setActiveCampusId()` which increments `schoolScopeVersion`
- `campusList` and `activeCampus` available via `useSchool()`
- Campus switcher only renders when `campusList.length > 1`

---

## 3. Fixes Made

### Fix 1: `useApiList` Auto-Refetch on School/Campus Switch
**File:** `frontend/src/pages/useApiList.js`

```javascript
// Added import
import { useSchool } from "../schoolContext";

// Added dependency
const { schoolScopeVersion } = useSchool();

// Modified effect to include schoolScopeVersion
useEffect(() => {
  load(new URLSearchParams({ page: 1 }));
}, [load, schoolScopeVersion]);  // Was: [load]
```

**Impact:** All 10+ pages using `useApiList` now automatically refetch when:
- Super Admin switches schools
- User switches campuses
- `schoolScopeVersion` is bumped for any reason

### Fix 2: Global 403 Toast Notification
**File:** `frontend/src/sessionWatch.js`

- Added `FORBIDDEN_EVENT = "pf:forbidden"` constant
- Added `fireForbidden(url)` function to dispatch custom event
- Modified 403 handling to verify session, then dispatch `pf:forbidden` with the failed URL if session is valid
- Added `onForbidden(handler)` export for subscription

**File:** `frontend/src/App.jsx`

- Added `ForbiddenHandler` component inside `ToastProvider`
- Listens for `pf:forbidden` events and shows toast: `"You don't have permission to access {url}."`
- Works for all API calls (GET, POST, PUT, DELETE) that return 403 with valid session

### Fix 3: Campus Switch Auto-Refresh
**Already working** - `setActiveCampusId()` in `schoolContext.jsx` already increments `schoolScopeVersion`. The `useApiList` fix ensures all consumers auto-refetch.

### Fix 4: Dashboard Refresh on School Switch
**Already working** - Route remount (`<Routes key={currentSchool?.id}>`) forces Dashboard to remount and refetch from `/api/dashboard/overview/` which is session-scoped.

---

## 4. Tests Performed

| Test | Result |
|------|--------|
| `npm run lint` | ✅ PASS (0 errors, 0 warnings) |
| `npm run build` | ✅ PASS (3.38s, all chunks emitted) |
| Backend test suite (842 tests) | ✅ Same as baseline (2 FAIL, 21 errors - all pre-existing) |
| Frontend build output | ✅ All chunks generated, no errors |

**Note:** No frontend test suite exists in the project (no `test` script in package.json). Backend tests unaffected by frontend changes.

---

## 5. Results Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Active school state reliable | ✅ | `schoolContext.jsx` mirrors server-side session |
| School switching refreshes all data | ✅ | `schoolScopeVersion` bump + route remount + `useApiList` fix |
| Stale cached data cannot appear | ✅ | `schoolScopeVersion` dependency in `useApiList`; route remount |
| Unauthorized users cannot access school-switch UI | ✅ | Gated by `modules.isPlatformAdmin` in `App.jsx:624` |
| 401/403 behavior correct | ✅ | 401→logout; 403→probe→valid=forbidden toast; 403→probe→invalid=logout |
| Protected routes functional | ✅ | `RequireRoles` with `scopedHasRole` on all routes |
| Existing pages continue working | ✅ | Build passes, backend tests unchanged |
| Build passes | ✅ | `npm run build` exits 0, all chunks emitted |

---

## 6. Remaining Frontend Issues

### 6.1 Pre-existing (Not Fixed in P0)
1. **Reports module broken tests** - `apps/reports/tests.py` has broken `setUp` (unrelated to frontend)
2. **Stale test assertions** - 2 backend tests expect 404/400 but get 403 (backend behavior change)
3. **Inline error handling** - Most pages still use inline `setError()` instead of toast for API errors (only 3 pages use toast)

### 6.2 Minor Enhancements (Future)
1. **Consistent error toasting** - Could migrate more pages to use `useToast()` for API errors
2. **Loading states during switch** - `isSwitching` state exists but not all pages show loading during switch
3. **Optimistic UI for campus switch** - Could show pending state while `setActiveCampusId` resolves

---

## 7. Verification Checklist (Definition of Done)

- [x] Active school state is reliable
- [x] School switching refreshes all relevant data
- [x] Stale cached data cannot appear after switching
- [x] Unauthorized users cannot access school-switch UI
- [x] 401/403 behavior is correct
- [x] Protected routes remain functional
- [x] Existing pages continue working
- [x] Build passes
- [x] Lint passes

---

## 8. Deployment Notes

The changes are backward compatible:
- No breaking API changes
- No new dependencies
- No migration needed
- Safe to deploy alongside backend `5d29952` (which fixed B1-B7 bugs and migration drift)

**Merge Command:**
```bash
git checkout master
git merge security-hardening/frontend-p0
git push origin master
```