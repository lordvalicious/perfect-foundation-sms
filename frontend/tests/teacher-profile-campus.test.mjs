// Regression guard for the teacher-profile Campus display bug (zero-dependency, Node test runner).
//
// The original bug: the teacher detail endpoint exposes the primary campus under
// `primary_campus_name` (source `primary_campus.name`), but the profile views read
// `profile.campus_name`, which the teacher payload never contains — so the "Campus"
// field silently rendered nothing.
//
// The fix: fall back to `primary_campus_name`. These tests read the two profile views and
// fail if the teacher Campus row reverts to `profile.campus_name`.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));

for (const file of ["ProfileModal.jsx", "ProfilePage.jsx"]) {
  const source = readFileSync(join(here, "..", "src", "pages", file), "utf8");

  test(`${file}: teacher Campus row reads primary_campus_name`, () => {
    const teacherBlock = source.match(
      /\{profile\?\.kind === "teacher" && \([\s\S]*?label="Campus"[\s\S]*?value=\{profile\.primary_campus_name \|\| profile\.campus_name\}/
    );

    assert.ok(
      teacherBlock,
      `${file} must render the teacher Campus value from primary_campus_name (API field), falling back to campus_name`
    );

    assert.doesNotMatch(
      source,
      /value=\{profile\.campus_name\}/,
      `${file} must never read profile.campus_name alone (the teacher payload has no campus_name)`
    );
  });
}