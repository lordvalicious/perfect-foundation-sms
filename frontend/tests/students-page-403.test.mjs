// Regression guard for the Students page 403 / missing-data crash
// (zero-dependency, Node test runner).
//
// Background: when GET /api/students/?campus=N&page=1 returns 403 (the backend
// intentionally denies campus requests outside the caller's scope), the old
// fetch .catch() persisted a PARTIAL per-campus entry ({loaded, loading,
// error} only). The render-side `campusData[campus.id] || {default}` guard
// only kicks in when the key is ABSENT, so the partial entry leaked through
// with `count === undefined`, and `data.count.toLocaleString()` threw
// "Cannot read properties of undefined (reading 'toLocaleString')",
// surfacing the ErrorBoundary as a blank "Something went wrong" page.
//
// The contract below locks in: (1) a complete `emptyCampusData` module
// constant, (2) the render path merging partial entries onto that complete
// default, (3) BOTH fetch error paths persisting the complete shape, and
// (4) a distinct permission message on 403.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(
  join(here, "..", "src", "pages", "StudentsPage.jsx"),
  "utf8"
);

const countOf = (needle) => src.split(needle).length - 1;

test("emptyCampusData is defined at module scope with a complete shape", () => {
  const block = src.match(/const emptyCampusData = \{\s*([\s\S]*?)\n\};/);
  assert.ok(block, "emptyCampusData must be defined at module scope");

  for (const field of [
    "students: []",
    "count: 0",
    "page: 1",
    "next: null",
    "previous: null",
    "loading: true",
    'error: ""',
  ]) {
    assert.ok(
      block[1].includes(field),
      `emptyCampusData must keep "${field}"`
    );
  }
});

test("render merges a partial entry onto the complete default", () => {
  assert.match(
    src,
    /const data = \{\s*\.\.\.emptyCampusData,\s*\.\.\.\(campusData\[campus\.id\] \|\| \{\}\),\s*\};/,
    "render must spread emptyCampusData before the (possibly partial) campus entry"
  );

  assert.equal(
    countOf("...emptyCampusData,"),
    3,
    "emptyCampusData must also be merged in BOTH fetch .catch handlers"
  );
});

test("a failed/403 entry can never produce undefined count or students", () => {
  const empty = {
    students: [],
    count: 0,
    page: 1,
    next: null,
    previous: null,
    loading: true,
    error: "",
  };
  const partial403 = {
    loaded: true,
    loading: false,
    error: "You don't have permission to view these students.",
  };

  const data = { ...empty, ...partial403 };

  assert.equal(typeof data.count, "number");
  assert.ok(Array.isArray(data.students));
  assert.doesNotThrow(() => data.count.toLocaleString());
  assert.doesNotThrow(() => data.students.map(() => {}));
});

test("403 is surfaced with a permission message, not a generic failure", () => {
  assert.equal(
    countOf("response.status === 403"),
    2,
    "both students fetch paths must special-case a 403"
  );
  assert.ok(
    src.includes("You don't have permission to view these students."),
    "a 403 must produce a clear permission message"
  );
});

test("success path still normalizes missing/paginated fields", () => {
  assert.ok(
    src.includes("students: data.results || [],"),
    "success must default results to []"
  );
  assert.ok(
    src.includes("count: data.count || 0,"),
    "success must default count to 0"
  );
});