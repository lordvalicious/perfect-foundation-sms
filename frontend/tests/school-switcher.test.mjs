// Regression guard for the TOP-NAVBAR SCHOOL SWITCHER (zero-dependency, Node
// test runner).
//
// The switcher is fed by `schoolContext.jsx`. A Super Admin's school list comes
// from `/api/auth/super-admin/schools/` (a plain JSON array) and is requested
// through `Promise.allSettled`, so the settled entry is a `{status, value}`
// wrapper — NOT the payload. The provider must unwrap `.value`, otherwise the
// school list is discarded and `availableSchools` collapses to the user's single
// membership, which silently hides the dropdown gate
// (`availableSchools.length > 0`) in App.jsx.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel) =>
  readFileSync(join(here, "..", "src", ...rel.split("/")), "utf8");

const schoolContext = read("schoolContext.jsx");
const appJsx = read("App.jsx");

test("schoolContext unwraps the allSettled school list (not the result wrapper)", () => {
  assert.match(
    schoolContext,
    /const allSchools =\s*schoolsResult\?\.status === "fulfilled" \? schoolsResult\.value : null;/,
    "the super-admin school list must be read from the fulfilled result's .value"
  );
  assert.ok(
    !/const allSchools = schoolsResult \?\? null;/.test(schoolContext),
    "the settled-result wrapper must never be handed to apply() as the school list"
  );
});

test("the navbar ships an openable platform-admin school dropdown", () => {
  assert.ok(
    appJsx.includes("schoolDropdownOpen && availableSchools.length > 0"),
    "the dropdown must be gated on the open flag and the available school count"
  );
  assert.ok(
    appJsx.includes('className="school-switcher-dropdown"'),
    "the dropdown menu must keep its school-switcher-dropdown class"
  );
});
