// Regression guard for the Hostel → Add Room bug (zero-dependency, Node test runner).
//
// The original bug: the Add Room hostel dropdown was fed by the campus-scoped
// hostel-management list (`/api/hostel/hostels/`), which hides hostels the
// user is authorized to create Rooms in (Room management is school-wide within
// the institution). The dropdown MUST fetch the dedicated institution-scoped
// selector `/api/hostel/room-hostels/`.
//
// This test reads the actual HostelPage source and fails if that wiring
// regresses back to the campus-scoped list.

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

const selectorBlock = source.match(
  /fetch\(`\$\{BASE\}room-hostels\/`, \{ credentials: "include", signal \}\)[\s\S]*?\},\s*\[schoolId\]\);/
);

test("Add Room dropdown is fed by the institution-scoped selector", () => {
  assert.ok(
    selectorBlock,
    "HostelPage.jsx must fetch /api/hostel/room-hostels/ inside a school-keyed effect"
  );

  const block = selectorBlock[0];

  assert.match(
    block,
    /room-hostels\//,
    "the Add Room selector must request /api/hostel/room-hostels/ (institution-scoped selector), not the campus-scoped hostel-management list"
  );

  assert.doesNotMatch(
    block,
    /\$\{BASE\}hostels\//,
    "the Add Room selector must NOT reuse the campus-scoped /api/hostel/hostels/ list"
  );

  assert.match(
    block,
    /if \(!signal\.aborted\) setHostels/,
    "Add Room hostels must only be set when the in-flight request was not aborted"
  );
});

test("Add Room dropdown maps the hostels state", () => {
  const dropdownReg = /<option value="">Hostel\.\.\.<\/option>\s*\{hostels\.map/;
  assert.match(
    source,
    dropdownReg,
    "the Add Room hostel <select> must render from the `hostels` state"
  );
});