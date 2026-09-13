// Regression guard for the ACTIVE-SCHOOL FAILURE POLICY (zero-dependency, Node
// test runner).
//
// Hostel Allocation (and the hostel page generally) must fail closed:
//  1. The student selector is fetched only AFTER the active school resolves,
//     keyed on `currentSchool?.id` — never an unconditional /api/students/ call.
//  2. With no active school the selector state is cleared, the scoped tables
//     are cleared, and an explicit "No active school selected..." message is
//     rendered — never a populated (or unscoped) student list.
//  3. Every school-scoped request is aborted when the active school changes
//     (shared AbortController) so a stale response from a previous school can
//     never overwrite the new school's rows.
//
// This test reads the actual HostelPage source and fails if that wiring
// regresses back to an unscoped or populated-by-default selector.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(
  join(here, "..", "src", "pages", "HostelPage.jsx"),
  "utf8"
);

test("student selector is fetched only after the active school resolves", () => {
  const studentEffect = source.match(
    /useEffect\(\(\) => \{\s*if \(!schoolId\) \{\s*setStudents\(\[\]\);[\s\S]*?fetch\("\/api\/students\/\?page_size=1000", \{ credentials: "include", signal \}\)[\s\S]*?\}, \[schoolId\]\);/
  );

  assert.ok(
    studentEffect,
    "the /api/students/ fetch must live inside an effect gated on schoolId that clears students when the active school is missing"
  );

  const block = studentEffect[0];

  assert.match(
    block,
    /if \(!signal\.aborted\) setStudents\(json\.results \|\| \[\]\)/,
    "student results must only be applied when the request was not aborted"
  );
});

test("students state is never set from an unguarded fetch", () => {
  const setCalls = source.match(/setStudents\(/g) || [];
  assert.equal(
    setCalls.length,
    2,
    `expected exactly 2 setStudents calls (fail-closed clear + guarded set), found ${setCalls.length}`
  );
});

test("rooms options are keyed to the active school and abortable", () => {
  assert.match(
    source,
    /useEffect\(\(\) => \{\s*if \(!schoolId\) \{\s*setRoomOptions\(\[\]\);/,
    "room options must be cleared when the active school is missing"
  );

  assert.match(
    source,
    /fetch\(`\$\{BASE\}rooms\/`, \{ credentials: "include", signal \}\)/,
    "the rooms fetch must share the aborted signal"
  );

  assert.match(
    source,
    /if \(!signal\.aborted\) setRoomOptions\(data\.results \|\| data\)/,
    "room options must only be applied when the request was not aborted"
  );
});

test("load() fails closed without an active school", () => {
  assert.match(
    source,
    /if \(!schoolId\) \{\s*setRows\(\[\]\);\s*setLoading\(false\);\s*return;\s*\}/,
    "load() must clear rows and stop loading when the active school is missing"
  );

  assert.match(
    source,
    /if \(!signal\.aborted\) setRows\(data\.results \|\| data\)/,
    "rows must only be applied when the request was not aborted"
  );
});

test("school switch aborts all in-flight school-scoped requests", () => {
  assert.match(source, /const scopeRef = useRef\(null\);/, "an AbortController ref must exist");
  assert.match(
    source,
    /useEffect\(\(\) => \{\s*const controller = new AbortController\(\);\s*scopeRef\.current = controller;\s*return \(\) => \{\s*controller\.abort\(\);/,
    "a new AbortController must be created per active school and aborted on change/unmount"
  );
  assert.match(
    source,
    /\}, \[schoolId\]\);[\s\S]*?const \{ signal \} = scopeRef\.current;/,
    "fetches must consume the signal of the shared controller"
  );
});

test("fail-closed message is rendered when no active school is selected", () => {
  assert.match(
    source,
    /No active school selected\. Please select a school to view hostel allocation students\./,
    "the allocations tab must show the mandated message when no active school is selected"
  );
  assert.match(
    source,
    /No active school selected\. Please select a school to manage hostels and rooms\./,
    "the hostels/rooms tabs must show a match message when no active school is selected"
  );
  assert.match(
    source,
    /const noActiveSchool = !schoolId && !isSwitching;/,
    "a no-active-school flag must drive the fail-closed UI"
  );
  assert.match(
    source,
    /noActiveSchool \? \([\s\S]*?state-card error/,
    "the fail-closed message must render inside the error card UI"
  );
});