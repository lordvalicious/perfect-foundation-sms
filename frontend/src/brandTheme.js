// Centralized brand-theme application. THE single production mechanism for
// applying a school's theme color to the app shell — the Branding page preview
// and save flow use these exact functions, never a parallel preview-only
// engine. Light/Dark mode is untouched: the theme color is mode-independent
// and injects the base `--brand-color` + `--text-on-brand` tokens together
// with the design-system `--primary*` family (which many components still
// consume for chips, soft surfaces, focus shadows, selected/active states and
// secondary buttons). `--brand-strong/-soft/-glow` stay mode-aware CSS
// `color-mix` derivations in App.css; `--primary-strong/-soft/-glow` simply
// reference those so BOTH token families follow the school color.

export const THEME_PRESETS = [
  { name: "Blue", value: "#2563eb" },
  { name: "Indigo", value: "#4f46e5" },
  { name: "Purple", value: "#7c3aed" },
  { name: "Violet", value: "#8b5cf6" },
  { name: "Teal", value: "#0d9488" },
  { name: "Green", value: "#16a34a" },
  { name: "Emerald", value: "#059669" },
  { name: "Orange", value: "#ea580c" },
  { name: "Red", value: "#dc2626" },
  { name: "Rose", value: "#e11d48" },
];

export function isHexColor(value) {
  return typeof value === "string" && /^#[0-9A-Fa-f]{6}$/.test(value);
}

// Readable foreground on top of a brand-colored surface. Dark colors get white
// text; light colors get the dark ink the design system ships with.
export function brandTextOnColor(hex) {
  if (!isHexColor(hex)) return "#ffffff";

  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  return luminance > 0.55 ? "#1c1917" : "#ffffff";
}

function ensureThemeColorMeta() {
  let meta = document.querySelector('meta[name="theme-color"]');

  if (!meta) {
    meta = document.createElement("meta");
    meta.setAttribute("name", "theme-color");
    document.head.appendChild(meta);
  }

  return meta;
}

export function applyBrandTheme(hex) {
  if (!isHexColor(hex)) {
    clearBrandTheme();
    return;
  }

  const root = document.documentElement;

  // Base accents — referenced by buttons, tabs, focus rings, active nav.
  root.style.setProperty("--brand-color", hex);
  root.style.setProperty("--text-on-brand", brandTextOnColor(hex));

  // Mirror the brand onto the `--primary*` design-system family so every
  // consumer still reading the legacy fallback tokens (soft chips/surfaces,
  // selected & hover states, focus shadows, secondary buttons, dark-dash
  // hero gradients) follows the school color too. The soft/strong/glow
  // variants are indirected through the mode-aware `--brand-*` mixers in
  // App.css, so hover/emphasis behavior stays correct in light AND dark mode.
  root.style.setProperty("--primary", hex);
  root.style.setProperty("--text-on-primary", brandTextOnColor(hex));
  root.style.setProperty("--primary-strong", "var(--brand-strong)");
  root.style.setProperty("--primary-soft", "var(--brand-soft)");
  root.style.setProperty("--primary-glow", "var(--brand-glow)");

  ensureThemeColorMeta().setAttribute("content", hex);
}

// Fail-closed: removing the tokens makes the design system fall back to the
// per-mode default accent (the `--brand-*: var(--primary-*)` fallbacks in
// App.css), so a cleared/missing/expired school context never shows another
// school's colors.
export function clearBrandTheme() {
  const root = document.documentElement;

  root.style.removeProperty("--brand-color");
  root.style.removeProperty("--text-on-brand");
  root.style.removeProperty("--primary");
  root.style.removeProperty("--text-on-primary");
  root.style.removeProperty("--primary-strong");
  root.style.removeProperty("--primary-soft");
  root.style.removeProperty("--primary-glow");

  const meta = document.querySelector('meta[name="theme-color"]');

  if (meta) meta.setAttribute("content", "");
}