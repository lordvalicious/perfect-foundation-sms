# UX_ROADMAP — Developer 2

Derived from UI_AUDIT.md + ERP_MODULE_AUDIT.md (2026-08-30). Principle: **do not blindly redesign stable functionality** — fix gaps, standardize the vocabulary, ship module UX in priority order.

## Non-negotiables (from brief)

- Every feature ships with: loading, skeleton where appropriate, empty, error, success, confirmation, validation, responsive, accessibility, mobile.
- Light + dark mode for all new surfaces (tokenized CSS already exists).
- Consume Developer 1 APIs/services — never duplicate business logic in the frontend.
- Authorization stays server-side; frontend role checks are UX only.

## Phase 0 — UX foundation (unblocks everything else)

| # | Work item | Files | Gaps it closes |
| --- | --- | --- | --- |
| 0.1 | **Skeleton system**: add `.skeleton` pulse styles + `SkeletonLines`/`SkeletonTable` primitives; convert `StateArea` loading branch to skeleton by default | `App.css`, `pages/ui.jsx` | 0/58 pages have skeletons |
| 0.2 | **Toast/Notice system**: `useNotice()` context + `.toast` stack (success/error/info), auto-dismiss; add `NoticeStack` in `Layout` | `App.jsx`, new `components/Notice.jsx`, css | No success feedback anywhere (avg ≤50%) |
| 0.3 | **ConfirmDialog component**: replace native `window.confirm`/`prompt`/`alert`; `useConfirm()` promise-based | `components/ConfirmDialog.jsx`, `pages/ui.jsx` | Unconfirmed destructive actions; native dialogs |
| 0.4 | **Unify API layer**: all pages → `apiFetch`/`api.js`; kill raw `fetch` + hand-rolled CSRF; stop coercing failures to `[]`/`{}` | `pages/*` | Fetch inconsistency (12/15 in group 3) |
| 0.5 | **`useDebounce` + `useFetch` hooks**; fix AuditLogs search, GlobalSearch dedupe | `pages/useDebounce.js` | Keystroke refetch N+1 |
| 0.6 | **i18n registry**: convert i18n.jsx to a default-exported key registry usable page-by-page; add `useT` helper; start from shell + top pages | `i18n.jsx` | ~4/58 pages translated |

**DoD Phase 0**: skeleton everywhere; toasts on all mutating actions; no native confirm/prompt/alert; 0 raw `fetch` calls; debounce pattern used; i18n on the 10 most-used pages.

## Phase 1 — Correctness (silent failures & destructive flight)

Order by blast radius:

1. **Un-silence error paths** (expose real messages + retry): Helpdesk reply/resolve/reopen/detail, Visitors check-in/out/stats, Events RSVP/create, Export/Backup, ReportBuilder duplicate/delete, DigitalIds revoke, Messages/Templates list loads.
2. **Confirmations before irreversible writes**: hostel vacate; digital-ID revoke; timetable auto-generate; admissions accept/reject; workflow delete; tenancy deactivate; payroll mark-paid; data-import commit.
3. **Success feedback on every mutation** (toasts from 0.2): close-then-confirm pattern with explicit "Saved." etc.
4. **Mark-entry partial failure**: MarksEntryPanel — batch endpoint or queue + per-row status instead of silent sequential POST/PATCH.
5. **HostelPage bug**: room-creation form must read hostels, not the active tab's rows (**highest-priority bug**).

**DoD Phase 1**: zero `.catch(() => {})`; every destructive action confirmed; every mutation notifies; hostel fix tested.

## Phase 2 — Consistency sweep

1. Tables on mobile: card/stack layout under a `data-table-responsive` class or the existing media queries (7 → widen).
2. Empty states everywhere `StateArea` isn't enough (SMSPage logs, ExecutiveDashboard charts, CampusDashboard no-campuses, ReportsCenter search).
3. Responsive single-row forms → stacked grid: StaffOperations, HealthRecords, Discipline, Homework, Login.
4. i18n + RTL pass on top pages (Students, Staff, Finance, Attendance, Parent portal, login) incl. numeric/date formatting via `Intl` instead of hardcoded PKR/en-GB.
5. a11y baseline: `aria-label` on icon-only buttons, focus-visible ring, form `<label>`/`htmlFor`, skip-to-content link, no `alert()` for errors (use 0.2 toast).
6. **consolidate** `ProfileModal`/`ProfilePage` into one renderer.

**DoD Phase 2**: all pages pass the 10-state checklist; both themes verified on top pages; Lighthouse a11y ≥ 90 on shell + top pages.

## Phase 3 — Module UX (value order)

| Module | Work |
| --- | --- |
| Reports | Route `ReportsCenter`; deprecate duplicate legacy tabs; respect config-driven catalog as single source |
| Exams | Exam create/edit/schedule UI against existing D1 services (marks entry already good) |
| Transport/Inventory | Elevate from read-only → CRUD using existing API surface (confirm with D1 on mutating endpoints) |
| Report Cards | Open/print/download single card; keep grading flows untouched |
| Attendance | Cap roster loader + server-side pagination; allow record correction UI |
| Parent portal | Server-side per-child scoping; cache; skeleton charts |
| Helpdesk | Optional assign-picker to backend assign action |
| Workflow | Wire the 3 unrouted pages into nav under a Workflow group or integrate with pending approvals |

## Phase 4 — Hardening & DX

- Dead code removal/documentation (`PermissionGate`, unrouted pages) after Phase 3 decisions.
- ESLint rules for the standard (no raw fetch, no window.confirm, required states) — encode as lint rules or a checklist.
- Frontend unit/integration smoke tests (Vitest) for shared primitives + top flows.
- `npm run lint` + `npm run build` CI-gate every change (verify against current baseline warnings).

## Interlock with Developer 1 (blocking decisions)

- Confirm which mutating endpoints exist for Transport/Inventory CRUD (don't invent).
- Confirm module keys for nav entries lacking one (`lms`, assignments, announcements, documents, timetable, campuses, teachers, staff).
- ReportsCenter vs ReportsPage: product decision to route or retire.
- LoginPage demo credentials removal (security, D1).
- SMSPage GET-on-send-endpoint: fix with a dedicated status endpoint (D1 API addition).

## Definition of done (global)

Run `npm run lint` clean + `npm run build` pass; manual matrix on 4 viewport sizes (≤375 / 768 / 1280 / 1600+) and both themes; each feature touches ≤1 shared primitive change; no page regression on the 10-state checklist.