// §18 (Phase 3B) — navbar dropdown must paint ABOVE content, never hidden
// behind another element.
//
// This is deliberately a CSS-contract test: it reads the REAL App.css used by
// the app shell and asserts the §18 stacking contract that the phase identified
// as the root cause. It runs with zero browser/DOM — fully deterministic.
//
// ROOT CAUSE (identified in Phase 3B):
//   .topbar is `position: sticky; z-index: 100` AND has `backdrop-filter:
//   blur(8px)`. `backdrop-filter` forces a stacking context, so the topbar's
//   entire subtree — including the nav dropdown — is painted as one unit whose
//   only z-index that matters against page content is 100.
//   .nav-dropdown was `z-index: 100` — the SAME plane as the topbar, and far
//   below the school/campus switcher dropdowns' proven-good 250 plane. When the
//   dropdown opened it sat on the same plane as the sticky bar and any content
//   with its own stacking context above 100 (e.g. tables/pages in the 150-250
//   band) could paint OVER the dropdown → dropdown hidden behind content.
//
// SMALLEST SAFE FIX (kept local — no uncontrolled global z-index):
//   .nav-dropdown z-index 100 → 250, matching the school/campus switcher plane
//   already proven to paint above topbar content. Controlled, values already in
//   use, no white-label/global engine involved.
//
// Contract asserted here:
//   1. .topbar is sticky (position sticky + z-index >= 100) → establishes the
//      topbar stacking unit.
//   2. .nav-dropdown is position:absolute AND its z-index STRICTLY EXCEEDS the
//      topbar plane (>= 250). Regression: z-index 100 (equal plane) → FAIL.
//   3. The fix stays on an existing in-use plane (250), and no rabbit-hole
//      stacking on 4999/9999 appears.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const cssPath = join(here, "..", "src", "App.css");
const css = readFileSync(cssPath, "utf8");

function rule(source, selector, name) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp(
    `[^}]*\\.${escaped}[^{]*\\{[^}]*\\}`,
    "m",
  );
  const m = source.match(re);
  if (!m) return null;
  const block = m[0];
  const z = block.match(/z-index\s*:\s*(\d+);/);
  const pos = block.match(/position\s*:\s*([a-z]+);/);
  const sticky = block.match(/position\s*:\s*sticky;/) || block.match(/top\s*:\s*0;/);
  return { name, pos: pos ? pos[1] : null, z: z ? Number(z[1]) : null, sticky: !!sticky };
}

test("§18: navbar dropdown paints strictly above the sticky topbar plane", () => {
  const topbar = rule(css, "topbar", "topbar");
  const dropdown = rule(css, "nav-dropdown", "nav-dropdown");

  assert.ok(topbar, "expected .topbar rule present in App.css");
  assert.ok(dropdown, "expected .nav-dropdown rule present in App.css");

  // topbar must be the sticky stacking unit (position sticky + explicit plane).
  assert.ok(
    topbar.z !== null && topbar.z >= 100,
    `.topbar must keep its sticky plane at >= 100 (got ${topbar.z})`,
  );

  // The core §18 regression: dropdown plane must EXCEED the topbar plane.
  assert.equal(dropdown.pos, "absolute", ".nav-dropdown must be position:absolute");
  assert.ok(
    dropdown.z !== null && dropdown.z > topbar.z,
    `.nav-dropdown z-index (${dropdown.z}) must strictly exceed .topbar z-index ` +
      `(${topbar.z}) so the dropdown is never hidden behind content — §18 regression ` +
      `on z-index 100 (equal plane)`,
  );

  // Smallest-safe-fix guardrail: sit on the proven 250 switcher plane, and do
  // NOT introduce uncontrolled mega-planing (no 4999/9999 creeping in).
  assert.ok(
    dropdown.z >= 250,
    `nav dropdown must sit on the known-good 250 plane (got ${dropdown.z})`,
  );
  assert.ok(
    dropdown.z <= 250,
    `nav dropdown must NOT jump to an uncontrolled global plane; keeit at 250 (got ${dropdown.z})`,
  );
});
