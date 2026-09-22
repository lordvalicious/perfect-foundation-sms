# Phase 43 — Production Browser/UI Certification Report

**Target:** Perfect Foundation SMS — production frontend `https://perfect-foundation-sms.vercel.app/`
**Method:** Executable Playwright E2E suite (`e2e/`) run against the live production deployment with real production user sessions (session-based auth). No product source changes were made during this phase.
**Run date:** 2026-09-22
**Result:**

```
226 tests, 3 projects (desktop / tablet / mobile)
222 passed · 0 failed · 4 skipped/fixme
```

---

## 1. Verdict

**PRODUCTION UI CERTIFIED WITH KNOWN DEFECTS.**

- All **module render checks pass** for all five tested roles (32 super-admin core + 19 tail pages, plus the role-specific allowed modules) — every permitted page renders real content, unauthenticated users are confined to the login page, and denied routes are blocked on the UI (Access-denied card or route-not-found page).
- **Authorization is enforced** with a clean, verifiable status matrix (see §4). No cross-scope data leaked through the tested endpoints.
- Console/network audit is **clean for the 12 tested core pages** (no JS exceptions, no unexpected console errors, no failed non-CDN requests).
- **One real responsive defect** is certified-open and documented as a fixme (tablet document overflow caused by a hidden measure element — §6-D1).
- **Certification scope limitation:** all authenticated flows used injected real production sessions (chosen auth model). The real-password keystroke login path was NOT exercised (demo hints are invalid in production, and only name-only credentials are available locally). The login UI itself (form rendering, required-field validation, no-dashboard-when-anonymous) is verified.

---

## 2. Execution method

- **Suite location:** `e2e/` (self-contained; not part of the deployed app).
- **Runner:** Playwright, 1 worker, per-test timeout 180s (allowance for the production cold paths).
- **Auth model (user-chosen):** session-based. Each role test injects the real Django `sessionid` (Netscape cookie extracted from secure local config under `P43_SESSIONS_DIR` or `P43_<ROLE>_SESSIONID`) via `context.addCookies`. Sessions are **never printed, written to repo files, or committed**.
- **No destructive writes:** logout flow verifies the button exists and that `/api/auth/me/` confirms an authenticated session; it does NOT click logout, because that would destroy the shared production session.
- **Identity assertion:** every role spec verifies `/api/auth/me/` returns the expected account and role before proceeding.

### Roles & accounts used
| Role | Account | Identity check |
|------|---------|----------------|
| SUPER_ADMIN | FrostFire | `username=FrostFire`, `is_superuser=true` |
| ADMIN | Flora | `username=Flora`, memberships include `principal` |
| TEACHER | SA-EMP-0001 | `username=SA-EMP-0001`, role `teacher` |
| STUDENT | SA-ST-0001 | `username=SA-ST-0001`, role `student` |
| STAFF | DI-EMP-0001 | `username=DI-EMP-0001`, role `staff` |

### Projects / viewports
| Project | Viewport | Specs selected |
|---------|----------|----------------|
| desktop | 1440×900 | all specs |
| tablet | 768×1024 | responsive.spec |
| mobile | 390×844 | responsive.spec |

---

## 3. Results by spec

| Spec | Tests | Result |
|------|-------|--------|
| auth.spec.js | 5 | 5 passed — login UI, empty-submit validation, anonymous→login-only, authenticated→dashboard, logout control present |
| super-admin.spec.js | 55 | 55 passed — identity, dashboard, topbar groups, 33 core + 19 tail pages render |
| admin.spec.js | 26 | 26 passed — identity, dashboard, 16 allowed modules render, 7 denied blocked on UI (incl. `/tenants` → NotFound), 3 backend APIs blocked |
| teacher.spec.js | 22 | 22 passed — 11 allowed render, 8 denied blocked on UI, finance/payroll 403 |
| student.spec.js | 24 | 24 passed — 10 allowed render, 10 denied blocked, payroll 403, scoped reads return ≤200 |
| staff.spec.js | 25 | 25 passed — 10 allowed render, 11 denied blocked, finance/payroll 403, scoped reads return ≤200 |
| authorization.spec.js | 32 | 31 passed / 1 skipped — full role-isolation matrix (§4) |
| navigation.spec.js | 6 | 6 passed — topbar groups, mobile toggle hidden-on-desktop/visible+mobile drawer links, back nav, breadcrumb |
| responsive.spec.js (×3 projects) | 18 | 15 passed / 3 fixme — login/dashboard/drawer/tables/profile at all viewports; 1 known defect fixme (§6-D1) |
| console-network.spec.js | 13 | 13 passed — no JS exceptions / console errors / failed requests on 12 core pages; core APIs respond <20s |

---

## 4. Authorization / role-isolation evidence

### 4.1 UI denied-card matrix (each checked in-browser)
| Route | ADMIN | TEACHER | STUDENT | STAFF |
|-------|-------|---------|---------|-------|
| /finance, /payroll | allowed (renders) | Access denied | Access denied | Access denied |
| /hr, /staff | allowed | denied | denied | denied |
| /settings | allowed | denied | denied | denied |
| /audit-logs, /branding, /sms, /templates, /data-export, /data-import | denied | — | — | — |
| /tenants | NotFound (route unregistered for non-platform-ADMIN) | — | — | — |
| /attendance, /exams, /report-cards | allowed | allowed | denied | denied |
| /students, /teachers | allowed | allowed (class-scoped) | allowed (self) | denied |

### 4.2 Backend enforcement matrix (actual production HTTP statuses)
| Endpoint | SUPER_ADMIN | ADMIN | TEACHER | STUDENT | STAFF |
|----------|-------------|-------|---------|---------|-------|
| /api/auth/me/ | 200 | 200 | 200 | 200 | 200 |
| /api/finance/invoices/ | 200 | 200 | **403** | 200 count=0 | **403** |
| /api/finance/payments/ | 200 | 200 | **403** | 200 count=0 | **403** |
| /api/payroll/records/ | 200 | 200 | **403** | **403** | **403** |
| /api/students/ | 200 | 200 | 200 (self/class) | 200 count=0 | 200 count=0 |
| /api/hr/employees/ | 200 | 200 | 200 (scoped) | 200 count=0 | 200 count=0 |
| /api/exams/ | 200 | 200 | 200 (scoped) | 200 count=0 | — |
| /api/attendance/ | 200 | 200 | 200 (scoped) | 200 count=0 | — |
| /api/staff/ | 200 | 200 | 200 | **200 count=3** | 200 |

Non-privileged roles receive **403 on cross-tenant Finance/Payroll**, empty self-scoped lists (`count=0`) on shared directories, and no endpoint returned 500 for any role.

---

## 5. Real findings

### F-43-1 — Responsive defect: hidden measure element overflows document at tablet widths (OPEN, fixme)
- **Repro:** `/students` (and every authenticated page) at viewport ≤ ~843px: `document.documentElement.scrollWidth` = 943 vs `clientWidth` = 770/768.
- **Root cause (verified against live DOM + source):** `div.topbar-nav-measure` (App.css:551-562) is `position:absolute; width:max-content; visibility:hidden` inside `header.topbar` (`position:sticky`). At tablet widths the hidden 843px measuring row escapes the clipped `body{overflow-x:hidden}` and inflates the document scroll width. It is an invisible DOM element — content tables were *verified contained* (each `table.data-table` sits in a `.table-wrapper`/`.students-table-wrapper` with `overflow-x:auto`; table width 978px scrolls correctly inside its 702px wrapper).
- **Impact:** horizontal page scroll / zoom on tablet & mobile; cosmetic, no data or interaction impact.
- **Suite treatment:** responsive.spec records it as an annotated `test.fixme` (desktop/tablet/mobile projects) so the defect stays executable evidence while the expected-failure is explicitly tracked.
- Suggested product fix (not part of this phase): change `.topbar-nav-measure` to `display:none` under `@media (max-width:960px)` (matching `.topbar-nav` hiding), or wrap the measure in a clipped container.

### F-43-2 — Students can read the staff directory listing (INFO, API surface)
- `/api/staff/` returns `200` with `count=3` for the STUDENT role (records ids 100/102/103). Matches the Phase 42 authz matrix ("staff 3 read-only"). Directory metadata exposure; no privileged fields observed. Flag for product review of whether student self-service legitimately needs a staff roster.

### F-43-3 — Google-fonts console noise filtered (INFO)
- console-network audit filters `fonts.googleapis.com` / `fonts.gstatic.com` / `accounts.google.com`; no other console errors observed on the 12 audited core pages.

---

## 6. Certification details

- **Module coverage:** super-admin core (33) + tail (19) + per-role allowed lists — every routed module a role is permitted renders actual content (not `Loading…`/empty/denied). Verified via `#main-content` settled-text polling in `helpers/role.js`.
- **Denied coverage:** every route outside a role's permitted set is blocked on the UI by either the Access-denied `state-card.error` (RequireRoles gate) or the route-not-found page; `helpers/role.js#checkDeniedRoute` treats both as blocked.
- **Identity/context:** each authenticated context re-verifies `/api/auth/me/`; sessions never leave the encrypted/temp-local config.

## 7. Reproduce

```
# from repo root (e2e/ has its own playwright + package.json)
$env:P43_SESSIONS_DIR = "C:\Users\Ryuk\AppData\Local\Temp\opencode"   # Netscape cookie files sa_*.txt
npx playwright test --reporter=list                                   # full suite (desktop+tablet+mobile)
npx playwright test staff student --project=desktop --reporter=list   # a single role spec
```

Env knobs (names only, no secret values in this doc): `P43_BASE_URL`, `P43_SESSIONS_DIR`, `P43_<ROLE>_SESSIONID`. See `e2e/README.md`.

## 8. Phase-42 carry-forward status

- Authoritative authz matrix (Phase 42) is now executed, not just probed — statuses above are the executable evidence set.
- Phase 42 open conditions: role scoping nuances (class-scoped teacher reads, `/api/staff/` exposure F-43-2) remain recorded; the responsive defect F-43-1 is newly captured.