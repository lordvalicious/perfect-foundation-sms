// Regression guard for the BRAND THEME COLORS feature (zero-dependency, Node
// test runner).
//
// The feature must stay centralized and fail-closed:
//  1. ONE engine (`brandTheme.js`) injects exactly `--brand-color` +
//     `--text-on-brand`; every other token is derived in App.css via
//     `color-mix`, with per-mode `var(--primary)` fallbacks so the default
//     appearance is unchanged when no theme is set.
//  2. The app shell clears the previous school's theme before fetching the
//     new school's branding and only applies a confirmed, valid `theme_color`
//     from the CURRENT school.
//  3. The Branding page validates client-side, only ever applies the CONFIRMED
//     backend echo, and its preview is scoped to the preview node (never the
//     live shell via documentElement).
//  4. The unused white_label engine must never be wired into the frontend.
//
// This test reads the actual sources and fails if that wiring regresses.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel) =>
  readFileSync(join(here, "..", "src", ...rel.split("/")), "utf8");

const brandTheme = read("brandTheme.js");
const appCss = read("App.css");
const schoolContext = read("schoolContext.jsx");
const brandingPage = read("pages/BrandingPage.jsx");

test("brandTheme.js exposes exactly the expected contract", () => {
  assert.match(
    brandTheme,
    /export const THEME_PRESETS = \[[\s\S]*?\];/,
    "the preset list must be exported"
  );

  const names = [...brandTheme.matchAll(/name: "([A-Za-z]+)", value: "(#[0-9a-fA-F]{6})"/g)];
  assert.equal(names.length, 10, `expected 10 presets, found ${names.length}`);
  assert.ok(
    names.every((m) => /^[0-9a-fA-F]{6}$/.test(m[2].slice(1))),
    "every preset must be a strict six-digit hex color"
  );

  assert.ok(
    brandTheme.includes("/^#[0-9A-Fa-f]{6}$/.test(value)"),
    "isHexColor must use the strict #RRGGBB pattern"
  );

  assert.match(
    brandTheme,
    /root\.style\.setProperty\("--brand-color", hex\);/,
    "applyBrandTheme must set --brand-color"
  );
  assert.match(
    brandTheme,
    /root\.style\.setProperty\("--text-on-brand", brandTextOnColor\(hex\)\);/,
    "applyBrandTheme must set --text-on-brand"
  );
  assert.ok(
    brandTheme.includes('root.style.removeProperty("--brand-color")'),
    "clearBrandTheme must remove --brand-color"
  );
  assert.ok(
    brandTheme.includes('root.style.removeProperty("--text-on-brand")'),
    "clearBrandTheme must remove --text-on-brand"
  );
});

test("no parallel engine: only brandTheme.js may touch --brand-color directly", () => {
  for (const [name, source] of [
    ["schoolContext.jsx", schoolContext],
    ["pages/BrandingPage.jsx", brandingPage],
  ]) {
    assert.ok(
      !source.includes('setProperty("--brand-color"'),
      `${name} must not write --brand-color directly`
    );
    assert.ok(
      !source.includes('document.documentElement.style'),
      `${name} must not mutate the live shell's inline style`
    );
  }
});

test("App.css keeps per-mode brand tokens with indigo fallbacks", () => {
  const countOf = (needle) => appCss.split(needle).length - 1;

  // Light mode: darken-on-hover (darkens toward black).
  assert.equal(
    countOf("color-mix(in srgb, var(--brand-color) 88%, #000)"), 1,
    "light mode brand-strong must darken on hover"
  );
  // Dark mode: lighten-on-hover (lightens toward white, preserving the
  // existing dark-theme convention where --primary-strong is lighter).
  assert.equal(
    countOf("color-mix(in srgb, var(--brand-color) 72%, #fff)"), 1,
    "dark mode brand-strong must lighten on hover"
  );
  assert.equal(countOf("--brand-color: var(--primary);"), 2, "light AND dark defaults must fall back to var(--primary)");
  assert.equal(countOf("--brand-soft: color-mix(in srgb, var(--brand-color) 8%, transparent);"), 2);
  assert.equal(countOf("--brand-glow: color-mix(in srgb, var(--brand-color) 14%, transparent);"), 2);
  assert.equal(countOf("--text-on-brand: var(--text-on-primary);"), 2);
});

test("brand surfaces consume the centralized tokens", () => {
  assert.match(
    appCss,
    /\.primary-button \{\s*background: var\(--brand-color, var\(--primary\)\);\s*color: var\(--text-on-brand, var\(--text-on-primary\)\);/,
    ".primary-button must use --brand-color/--text-on-brand"
  );
  assert.match(
    appCss,
    /\.tab-button\.active \{\s*color: var\(--brand-color, var\(--primary\)\);\s*border-bottom-color: var\(--brand-color, var\(--primary\)\);/,
    "active tabs must use --brand-color"
  );
  assert.match(
    appCss,
    /\.topbar-link\.active \{[\s\S]*?background: var\(--brand-soft, var\(--primary-soft\)\);[\s\S]*?color: var\(--brand-color, var\(--primary\)\);/,
    "active topbar links must use the brand soft/color tokens"
  );
  assert.ok(
    (appCss.match(/var\(--brand-color, var\(--primary\)\)/g) || []).length >= 6,
    "the --brand-color, --primary fallback pattern must be preserved across consumers"
  );
});

test("shell clears the previous theme before every school-branding fetch", () => {
  assert.match(
    schoolContext,
    /import \{ applyBrandTheme, clearBrandTheme, isHexColor \} from "\.\/brandTheme";/,
    "schoolContext must use the centralized engine"
  );

  assert.match(
    schoolContext,
    /useEffect\(\(\) => \{\s*clearBrandTheme\(\);\s*const name = currentSchool/,
    "the effect must clear the previous theme BEFORE the new fetch"
  );

  assert.match(
    schoolContext,
    /if \(isHexColor\(next\.theme_color\)\) \{\s*applyBrandTheme\(next\.theme_color\);\s*\} else \{\s*clearBrandTheme\(\);/,
    "only an isHexColor-valid theme_color may be applied"
  );

  assert.match(
    schoolContext,
    /\.catch\(\(\) => \{\s*if \(cancelled\) return;\s*clearBrandTheme\(\);/,
    "a failed branding fetch must clear to the default theme"
  );

  assert.ok(
    !schoolContext.includes("applyBrandTheme(next.primary_color)"),
    "the shell must never apply the print primary_color as the theme"
  );

  assert.ok(
    schoolContext.includes("theme_color: data.theme_color || \"\""),
    "the shell branding state must source theme_color"
  );
});

test("Branding page validates client-side and applies only the confirmed echo", () => {
  assert.match(
    brandingPage,
    /if \(!isHexColor\(form\.theme_color\)\) \{\s*setError\("Theme color must be a valid hex color, e\.g\. #7c3aed\."\);/,
    "an invalid theme color must block the save before any request"
  );

  assert.match(
    brandingPage,
    /const confirmed = await response\.json\(\)\.catch\(\(\) => null\);\s*if \(confirmed && isHexColor\(confirmed\.theme_color\)\) \{\s*applyBrandTheme\(confirmed\.theme_color\);/,
    "only the backend-confirmed theme_color may be applied after save"
  );

  assert.ok(
    brandingPage.includes("theme_color: data.theme_color || DEFAULT_COLORS.theme_color,"),
    "the page must load the saved theme_color"
  );

  assert.match(
    brandingPage,
    /THEME_PRESETS\.map\(\(p\) => \{/,
    "the preset swatches must come from the shared THEME_PRESETS list"
  );
  assert.ok(
    brandingPage.includes('aria-pressed={selected}'),
    "the chosen swatch must expose its selected state"
  );

  assert.match(
    brandingPage,
    /"--brand-color": isHexColor\(form\.theme_color\)\s*\?[\s\S]*?DEFAULT_COLORS\.theme_color,\s*"--text-on-brand": brandTextOnColor\(/,
    "the preview must reuse the same brand tokens, scoped to the preview node and guarded to a valid hex"
  );
});

test("the unused white_label engine is never wired into the frontend", () => {
  const walk = (dir) => {
    const entries = readdirSync(dir, { withFileTypes: true });
    return entries.flatMap((e) => {
      const p = join(dir, e.name);
      if (e.isDirectory()) return walk(p);
      if (/\.(js|jsx|ts|tsx)$/.test(e.name)) return [p];
      return [];
    });
  };
  const files = walk(join(here, "..", "src"));

  for (const file of files) {
    const content = readFileSync(file, "utf8");
    assert.ok(
      !/white-label\/branding|theme-preview|css-variables/.test(content),
      `${file} must not reference the unused white_label engine`
    );
  }
});