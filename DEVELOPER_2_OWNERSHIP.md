# DEVELOPER_2_OWNERSHIP

Defines ownership boundaries, standards, and conventions for Developer 2 in the perfect-foundation-sms monorepo.

## 1. Role

Developer 2 owns the **ERP module implementation, frontend, UI/UX, portals, operational workflows, and module-level user experience**.

Developer 1 owns **backend architecture, database, authentication, RBAC, campus isolation, security infrastructure, API platform, SaaS infrastructure, DevOps**.

> Rule: do not overwrite Developer 1's core architecture. Consume its APIs/services; never duplicate business logic client-side. Frontend role checks are UX conveniences only — authorization is enforced server-side.

## 2. Ownership map

### Owned (full authority)

| Path | What |
| --- | --- |
| `frontend/src/` | All UI code: pages, components, hooks, `App.jsx`, `App.css`, `main.jsx`, config |
| `frontend/src/pages/*` | 58 page modules (ERP screens, portals, dashboards) |
| `frontend/src/components/*` | Shared components (PermissionGate, LanguageToggle, Workflow\*, Approval\*) |
| `frontend/src/api.js` | Client fetch/CSRF/download helpers |
| `frontend/src/auth.jsx` | `AuthProvider`/`useAuth` (consumes D1 `/api/auth/*`) |
| `frontend/src/i18n.jsx` | Language provider + Urdu dict + RTL |
| `frontend/src/config/reports.ts` | Report catalog (single source for report metadata) |
| `frontend/package.json` | FE dependencies/web tooling (with care: coordinate heavy additions) |
| `UI_AUDIT.md`, `ERP_MODULE_AUDIT.md`, `UX_ROADMAP.md` | Module + UX enablement docs |

### Consumed from Developer 1 (no modifications without coordination)

| Surface | Usage by D2 |
| --- | --- |
| `/api/auth/*` (`me/`, `login/`, `logout/`, `2fa/*`, `google/*`) | Login, session, 2FA UI |
| `/api/schools/modules/current/` | Module toggles in nav/routes |
| `/api/schools/*` (campuses, classes, sections, years, terms, subjects, offerings, branding, tenants, modules) | Reference data everywhere |
| `/api/<module>/*` | All ERP data via `MODULE_PREFIXES` (see `backend/apps/schools/modules.py`) |
| `/api/dashboard/*`, `/api/reports/*`, `/api/search/`, `/api/audit/` | Dashboards, reports, search, audit |
| RBAC role/permission payloads on `/api/auth/me/` | `hasRole`/`hasPermission` client UX gating |

### Not owned / do-not-touch (Developer 1)

`backend/apps/**` (models, migrations, views, serializers, permissions, middleware, services), Django settings/urls, `vercel.json`, root build/deploy scripts, `docs/white-label-plan.md` implementation, DB schema, API response contracts (D2 reads them, doesn't define them).

### Cross-cutting ownership note

FE additions must stay **module-aware**: any new page relying on a togglable module must set `module: <key>` on its nav entry and follow `RequireRoles` route guards exactly as existing pages do.

## 3. UI/UX standard (mandatory per feature)

Every feature ships with, in order:

1. **Loading state** — skeleton (Phase 0 of roadmap); text fallback via `StateArea`.
2. **Skeleton** where data shapes are predictable (tables, profiles, cards).
3. **Empty state** — `EmptyState` component, never a blank panel.
4. **Error state** — `StateArea.error` + Retry; errors must never resolve to empty data.
5. **Success state** — toast/notice after mutations (roadmap 0.2); never silent.
6. **Confirmation** — `useConfirm()` dialog before destructive/irreversible actions; no native `confirm/prompt/alert`.
7. **Validation** — client-side checks before submit; server errors surfaced field-by-field from `apiFetch`.
8. **Responsive** — 375 / 768 / 1280 / 1600+ widths; tables degrade gracefully.
9. **Accessibility** — labels, `aria-label` on icon buttons, focus-visible, keyboard operability.
10. **Mobile** — drawer nav + touch targets.

Plus: **light + dark mode** via tokens (never inline hex), and **Urdu/RTL** where `t()`/`dir` apply (i18n by default, English fallback).

## 4. Conventions

- **State/UI vocabulary**: use `pages/ui.jsx` primitives (`PageHeader`, `PanelHeader`, `StateArea`, `EmptyState`, `StatusBadge`, `Pagination`) — extend them, don't fork them.
- **Data fetching**: `apiFetch` from `api.js` for mutations (`headers: authHeaders(...)`); reads may use `fetch(..., {credentials:"include"})` but must still surface errors; migrate remaining raw fetch to `apiFetch` (roadmap 0.4). Never `.catch(() => {})` silently on user-visible actions.
- **No business logic in FE**: calculations (fees, grades, attendance rates) come from D1 endpoints; the FE only formats (see `format.js`, prefer `Intl`).
- **i18n**: new user-facing copy goes through `t()`; all keys default to English.
- **No redesign of stable screens** unless the audit or a logged bug justifies it; changes to shared primitives must pass lint/build + the checklist.
- **Naming**: page components `XPage.jsx`, shared UI in `pages/` or `components/`; kebab-case CSS classes, token-first styling.

## 5. Verification (run before finishing a task)

```powershell
npm run lint     # eslint — must be clean
npm run build    # vite build — must pass (chunk-size warning is pre-existing baseline)
```

Manual checklist: viewport matrix + both themes + English/Urdu on affected screens; confirm no console errors in Network panel; verify all states (loading/empty/error/success) of the touched feature. Frontend tests (Vitest) are planned (roadmap Phase 4) — not yet present.

Full end-to-end needs the Django API running locally (see `frontend/README.md` / `LAUNCH.md`).

## 6. Interface with Developer 1 — expectations

- D2 raises API needs (missing mutating endpoints, pagination, batch endpoints) as tickets against D1 rather than calling unguaranteed URLs.
- D2 does not merge changes to backend-owned paths; single pointer-person model, separated by `frontend/` boundary.
- Breaking API changes must be announced with a FE migration note in the commit that changes `/api` contracts.

## 7. Current ownership status

- **UI_AUDIT.md, ERP_MODULE_AUDIT.md, UX_ROADMAP.md** shipped (2026-08-30).
- Top open items: skeleton system + toast/confirm primitives (Phase 0); silent-error + confirmation sweep (Phase 1); HostelPage room-form bug; ReportsCenter routing decision.