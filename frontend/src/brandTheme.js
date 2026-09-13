// Centralized brand-theme application. THE single production mechanism for
// applying a school's theme color to the app shell — the Branding page preview
// and save flow use these exact functions, never a parallel preview-only
// engine. Light/Dark mode is untouched: the theme color is mode-independent
// and only `--brand-color` + `--text-on-brand` are injected; every other
// token (strong/soft/glow) derives from them via CSS `color-mix` in App.css.

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

  root.style.setProperty("--brand-color", hex);
  root.style.setProperty("--text-on-brand", brandTextOnColor(hex));
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

  const meta = document.querySelector('meta[name="theme-color"]');

  if (meta) meta.setAttribute("content", "");
}