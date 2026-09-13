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

const loadHostelsBlock = source.match(
  /const loadHostels = useCallback\(\(\) => \{[\s\S]*?\}, \[\]\);/
);

test("Add Room dropdown is fed by the institution-scoped selector", () => {
  assert.ok(
    loadHostelsBlock,
    "HostelPage.jsx must define a loadHostels useCallback that feeds the Add Room dropdown"
  );

  const block = loadHostelsBlock[0];

  assert.match(
    block,
    /room-hostels\//,
    "loadHostels must request /api/hostel/room-hostels/ (institution-scoped selector), not the campus-scoped hostel-management list"
  );

  assert.doesNotMatch(
    block,
    /\$\{BASE\}hostels\//,
    "loadHostels must NOT reuse the campus-scoped /api/hostel/hostels/ list"
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