# UI_AUDIT — Perfect Foundation SMS Frontend

Audit date: 2026-08-30 · Auditor: Developer 2 · Scope: `frontend/src` (React 19 + Vite + react-router-dom 7)

## 1. Cheat sheet

| Area | Status |
| --- | --- |
| Total page components | 58 (`pages/*.jsx`) |
| Routed in `App.jsx` | ~46 routes |
| Dead / unrouted pages | 4: `ReportsCenter`, `PendingApprovalsPage`, `WorkflowDefinitionAdminPage`, `WorkflowInstanceDetailPage` |
| Shared components | 10 (`components/*`) — `PermissionGate` is unused |
| App shell | `App.jsx` (950 lines): auth guard, top nav, global search, notifications bell, theme + language toggle |
| Design system | `App.css` (3,698 lines), CSS custom properties, light + dark via `[data-theme]`, 7 media queries |
| Charts | recharts (`ResponsiveContainer` in dashboards) |
| Icons | lucide-react |
| i18n | `i18n.jsx` single Urdu dict (~130 keys), RTL flip supported; ~4/58 pages use it |
| API layer | `api.js` (`getCookie`, `authHeaders`, `jsonHeaders`, `apiFetch`, `readJson`, `apiDownload`) |
| Data helpers | `pages/useApiList.js`, `pages/ui.jsx` (PageHeader, PanelHeader, StateArea, EmptyState, Pagination, StatusBadge), `pages/format.js` |

## 2. App shell

- **Auth**: `auth.jsx` AuthProvider / `useAuth()` → `/api/auth/me/`. Provides `user`, `hasRole`, `hasPermission`, `refresh`. Login flow (incl. OTP stage) in `LoginPage.jsx`; 2FA self-service in `TwoFASection.jsx` (embedded in Settings).
- **Routing/guards**: `Shell()` fetches `/api/schools/modules/current/` for module gating + platform admin flag; `RequireRoles` does client-side role checks (flag: client-side only — never trust for authorization; D1 secures APIs).
- **Navigation**: 43 nav entries + 5 system entries, grouped into People / Academics / Finance / Resources / Communication / Support & Security / System. Dropdown groups on `topbar`, full list in a mobile drawer.
- **Global search**: debounced 300 ms against `/api/search/?q=`, dropdown of results. No error/empty styling for a failed request (treated as no results).
- **Notifications**: `/api/communication/notifications/`, read-all + per-item read. Loaded on demand only when opened.
- **Theme**: `localStorage["pf-theme"]` + `prefers-color-scheme`, applied as `data-theme` on `<html>`; toggle animates via `.theme-transitioning`. Both themes fully tokenized in `App.css`.
- **Language**: `localStorage["pf-lang"]` (`en`/`ur`); Urdu sets `dir="rtl"` + `lang="ur"`. Toggle in `components/LanguageToggle.jsx`.

## 3. Design system (App.css)

- Fonts: **DM Sans** (body) + **Sora** (display) loaded via Google Fonts `@import` — **network dependency; offline/FaaS builds lose fonts**.
- ~22 semantic tokens per theme (`--bg`, `--surface`, `--text`, `--primary`, `--success`, `--danger`, `--warning`, shadows, overlays). Light + dark palettes defined. `color-scheme` set per theme.
- Primitive classes reused everywhere: `.state-card`, `.empty-state`, `.data-table`/`.table-wrapper`, `.status-badge` (tone: active/inactive/warn/info), `.filter-row`, `.modal`, `.notice`, `.page-header`, `.teacher-list-header`, `.topbar`, `.nav-dropdown`.
- Responsive: only **7 media queries**, plus a handful of grid `minmax()`/auto-fill patterns. Wide tables rely on horizontal scroll in `.table-wrapper` (no mobile card fallback).
- Notable absence: **no skeleton styles**, no toast/notification system class, no focus-visible styling verified, no print stylesheet for report cards/timetable.

## 4. Shared building blocks

| Block | File | Notes |
| --- | --- | --- |
| `StateArea` | `pages/ui.jsx` | Loading = plain text `state-card` (**no skeleton**); error = `.state-card.error` with optional Retry |
| `EmptyState` | `pages/ui.jsx` | Icon + title + message + optional action; present on most list pages |
| `Pagination` | `pages/ui.jsx` | Prev/Next + page count; silent when `count` falsy |
| `StatusBadge` | `pages/ui.jsx` | tone inferred from status value |
| `useApiList` | `pages/useApiList.js` | fetch+réponse de pagination; **swallows non-ok into thrown Error only in some callers** |
| `formatDate`, `formatCurrency` | `pages/format.js` | PKR hardcoded (en-PK), en-GB dates — not locale-parameterized |

## 5. State-coverage matrix (verified per page by code audit)

Group summary (y = present at least once in the file; "–" = absent):

| Requirement | People/Academic (18 pages) | Finance/Resources (13) | Comms/Portal/Support (15) | Reports/Auth/Misc (12) |
| --- | --- | --- | --- | --- |
| Loading indicator | 18/18 | 13/13 | 13/15 | 10/12 |
| **Skeleton placeholders** | **0/18** | **0/13** | **0/15** | **0/12** |
| Empty state | 17/18 | 11/13 | 11/15 | 8/12 |
| Error state | 18/18 | 13/13 | 13/15 | 11/12 |
| Success feedback | 10/18 | 5/13 | 6/15 | 2/12 |
| Confirm before destructive | 6/18 | 1/13 | 1/15 | 3/12 |
| Client-side validation | 7/18 | 3/13 | 8/15 | 5/12 |
| Responsive | 14/18 | 12/13 | 7/15 | 2/12 |
| i18n (`t()`) | 2/18 | 1/13 | 0/15 | 1/12 |

## 6. Top global gaps (code-verified)

1. **No skeleton loading anywhere** (0/58 pages). Loading is a text `state-card`.
2. **i18n is nearly absent** — ~4/58 pages call `useLang()`; even those are partial (StudentsPage modal, FinancePage labels, AttendancePage headers, LoginPage). Urdu toggle + RTL infrastructure exists but is mostly unused.
3. **Fetch inconsistency**: raw `fetch` + hand-rolled CSRF cookie parsing coexists with `api.js` helpers; some list loads restore to `{}`/`[]` on failure so **errors render as empty data** (ReportsPage, MessagesPage, TemplatesPage, AwarenessPage-like silent catches).
4. **Silent failure paths** `.catch(() => {})` with no user feedback: HelpdeskPage (reply/resolve/reopen/detail), VisitorsPage (check-in/out/stats), ExportPage, ReportBuilderPage (duplicate/delete), DigitalIdsPage (revoke), EventsPage (RSVP).
5. **Destructive actions without confirmation**: Hostel vacate, Digital ID revoke, timetable auto-generate (only window.confirm), Admissions accept/reject, Workflow delete, Payroll mark paid, Library return, Tenants deactivate. Native `window.confirm` used where present (Finance fee-structure delete, TimetablePage).
6. **No toast/success system** — success is either absent, a weak subtitle swap, or modal-close-and-silent-refresh.
7. **Responsive inconsistent** — fixed inline `1fr 1fr` grids (BrandingPage), single-row many-field filter forms (StaffOperations, HealthRecords, Discipline, Homework), wide tables only horizontally scrolled.
8. **Accessibility unverified & likely weak** — icon-only buttons rely on `title`, no `aria-label` pass, `alert()`/`window.prompt()` used (ProfilePage downloads, Admissions accept), no skip-link/focus-visible audit done.
9. **Dead code**: `PermissionGate`/`RoleGate` (+ HOCs) never imported; `ReportsCenter` (config-driven, 136-report catalog) not routed; 3 Workflow pages not routed; `SingleDetailReports` reachable only from ReportsPage tab.
10. **Heavy client workloads**: AttendancePage recursive roster loader (no cap), ParentPortalPage sequential `fetchAllPages`, MarksEntryPanel per-student N+1 POST/PATCH, AssignmentsPage 8 reference endpoints on mount.

## 7. Notable per-page findings (highlights)

- **HostelPage**: room-creation form reads `rows` of the *current tab* (assumes hostels) — broken on Rooms/Allocations tabs; `vacate` unconfirmed.
- **LoginPage**: demo credentials hardcoded (production risk — D1 flag).
- **AttendancePage**: roster loader unbounded recursion; validates JS-side.
- **TimetablePage**: auto-generate **replaces all campus entries** behind only a `window.confirm`; no per-class scoping of the action.
- **MarksEntryPanel**: sequential per-student saves → partial-failure UX on large rosters.
- **AuditLogsPage**: search refetches on every keystroke — no debounce.
- **SMSPage**: issues a GET to the **send endpoint** `/email/send/` on tab open as a config probe (side-effect on an action URL).
- **PendingApprovalsPage**: N+1 instance fetches + 30 s poll with no busy/refresh indicator (page unrouted).
- **Dashboard.jsx**: raw `fetch` (not `apiFetch`), hardcoded "2026–2027" year badge.
- **ReportsPage/SingleDetailReports**: teacher/staff profiles show fewer sections than student profiles.
- **ProfileModal vs ProfilePage**: near-duplicate markup/logic — consolidation candidate.

## 8. What is healthy

- Theming is exemplary (fully tokenized, light+dark, system-preference aware).
- Common primitives (`StateArea`, `EmptyState`, `StatusBadge`, `.table-wrapper`) are widely adopted — consistent vocabulary.
- Module gating + role gating in shell is coherent (nav items + routes + `/api/schools/modules/current/`).
- Urdu/RTL scaffolding and the language toggle exist and work at shell level.
- Most list pages provide loading/empty/error/retry states via `StateArea`.