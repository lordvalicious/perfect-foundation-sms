# P3 UX & Enterprise Enhancements — Regression & Verification Report

Branch: `dev2/p3-enterprise` · Basis: `master` @ `0c4b98e`

## Scope
Evidence-driven UX hardening on top of the existing design system. Backend was NOT
touched — all changes are frontend-only, additive, and respect the existing
role/module gating. No working component was replaced without cause; no fake data
was introduced; backend permissions remain the security boundary.

## Changes

### 1. Toast feedback system (new)
- `frontend/src/toast.jsx`: `ToastProvider` + `useToast()` (success/error/info, auto-dismiss, click-to-dismiss, stacked, `aria-live="polite"` viewport, `role="status"` / `role="alert"` per card).
- Mounted in `App.jsx` inside `LanguageProvider`.
- CSS in `App.css` using theme variables (light + dark), logical properties
  (`inset-inline-end`, `inset-inline-start`) so toasts render correctly in RTL,
  `prefers-reduced-motion` respected, top-right on desktop, bottom sheet ≤560px.
- Wired into the multi-step flows that previously gave silent/broken feedback:
  - `LibraryPage` — return book, create/edit/delete book, add/delete copy.
  - `AlumniPage` — create/edit/delete alumni.
  - `TimetablePage` — auto-generate (success includes placed/unplaced summary; unplaced lessons surfaced).

### 2. Accessibility (A11y)
- Skip-to-content link (`a.skip-link` → `#main-content`) at the top of the shell, visually hidden until focused (`:focus-visible`).
- Global Escape handler in `Shell`: closes the topmost open `.modal-overlay` by activating its `.modal-close` — every modal in the app is now keyboard-dismissable with no per-dialog wiring.
- `aria-label` on icon-only controls previously exposed via `title` only: `LanguageToggle`, `ThemeToggle`, Notifications bell, logout button (x2), mobile nav menu toggle (`aria-expanded` too), GlobalSearch input, nav-group triggers (`aria-haspopup="true"`).
- Modal semantics on the dialogs touched (Library book/copies, Alumni detail): `role="dialog"`, `aria-modal="true"`, `aria-label`, `aria-label="Close"` on close buttons.
- `aria-label` on Alumni form/filter inputs that previously had placeholders as their only label.

### 3. i18n / Urdu / RTL
- Added Urdu keys for the P2-added navigation: `Alumni`, `Online Courses`,
  `Pending Approvals`, `Workflow Definitions` (previously fell back to English).
- New UI (toasts, skip link) built on CSS logical properties / `[dir="rtl"]` rules —
  RTL-safe without per-page work.

### 4. White-label / school branding
- `schoolContext.jsx`: after the active institution resolves, fetch
  `/api/schools/branding/` (cosmetic, failures are silent) and:
  - set `document.title` to the school's brand name (previously stuck at the
    default/static title after login);
  - expose `branding` (school_name, short_name, motto, primary_color, logo_url) via context;
  - apply `--brand-color` CSS variable + `meta[name="theme-color"]` for mobile browser chrome.
- `App.jsx` Shell: the topbar brand mark now uses the branding — school logo image
  if set, else the short/full name initial (falling back to the school name) instead
  of the hardcoded "S". Brand accent color flows through `var(--brand-color, var(--primary))`.

## Verification

### Build & lint
- `npm run lint` → 0 errors, 0 warnings (fixed one
  `react-refresh/only-export-components` finding by adding the same
  eslint-disable header `i18n.jsx` already uses).
- `npm run build` → PASS, Vite/Rolldown, ~4–11s.

### Regression matrix (static review — no browser automation available in this environment)
| Dimension | Check | Result |
|---|---|---|
| Responsive 320–1920px | Toasts: bottom sheet ≤560px, top-right ≥561px; existing topbar/sidebar/table media queries untouched | PASS (CSS) |
| Light / dark mode | New surfaces use `--surface/--text/--border/--success/--danger/--sky` vars; skip-link uses `--primary/--text-on-primary` | PASS |
| RTL (Urdu) | Toast placement via `inset-inline-*`; reversed slide-in keyframe under `[dir="rtl"]`; skip-link uses `inset-inline-start` | PASS |
| Keyboard nav | Skip link reachable + focusable; Escape dismisses topmost modal; nav triggers `aria-haspopup`; mobile toggle `aria-expanded`; global `:focus-visible` outline retained (`.modal-close`/`.toast-close` don't reset it) | PASS |
| Screen readers | Toast `aria-live="polite"` viewport + `role="status"`/`role="alert"`; dialogs `role="dialog"` + `aria-modal`; icon buttons labelled | PASS |
| Skeleton / loading | Dashboard already shows `SkeletonBlock rows` on first load; `StateArea` default skeleton covers other pages (no change needed) | PASS |
| Empty / error states | Library, Alumni, Timetable use `EmptyState`/`StateArea`; toast errors now also announce on mutation failures | PASS |
| UX consistency | Toast styling matches design system (radius, borders, shadow-lg, theme vars) | PASS |

### Notes / limitations
- No Django runtime and no browser automation available; the matrix above was
  verified at code/CSS level plus `build` + `lint`, not by clicking through the UI.
- `window.confirm` dialogs are retained (never suppressed) — toasts are additive.
- Brand color is applied only to the brand mark + browser chrome; the core design
  system palette is preserved so light/dark contrast rules keep working.

## Follow-up review (post-commit)
Review pass after the initial commit found and fixed:
- Memoized the `useToast()` API object so toasts don't re-render consumers on every
  provider re-render.
- Hardened the timetable generate toast against a missing `sections` field
  (`data.sections || 0`).
- Cleared `meta[name="theme-color"]` when switching to a school with no brand color
  (previously the previous school's tint persisted).
- Added explicit `:focus-visible` outline for `.toast-close`.
- Fixed a formatting slip in the brand mark JSX.
- Confirmed no conflicting global Escape handlers exist besides the two guarded ones
  in `App.jsx` (modal-close + mobile drawer), and that toasts (z-index 5000) layer
  above modals (z-index 200).
- Re-verified: `npm run lint` 0/0, `npm run build` PASS.

## Files changed
- `frontend/src/toast.jsx` (new)
- `frontend/src/App.jsx`
- `frontend/src/App.css`
- `frontend/src/i18n.jsx`
- `frontend/src/schoolContext.jsx`
- `frontend/src/components/LanguageToggle.jsx`
- `frontend/src/pages/LibraryPage.jsx`
- `frontend/src/pages/AlumniPage.jsx`
- `frontend/src/pages/TimetablePage.jsx`