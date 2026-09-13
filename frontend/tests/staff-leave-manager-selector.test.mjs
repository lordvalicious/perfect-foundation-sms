// Regression guard for the Staff/HR leave-request bug (zero-dependency, Node test runner).
//
// The original bug: HR/admin users have no linked staff profile of their own, and the
// leave form never sent a `staff` member id, so `POST /api/staff/leave/` returned 404
// ("No staff profile is linked to this account, and no staff member was selected.").
//
// The fix: manager roles get a staff-member <select> in the leave form and the payload
// includes `staff` when one is picked; non-managers omit `staff` so the backend derives
// their own profile. These tests read StaffOperationsPage.jsx and fail if the wiring
// regresses.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(
  join(here, "..", "src", "pages", "StaffOperationsPage.jsx"),
  "utf8"
);

test("leave form state carries an optional staff member id", () => {
  assert.match(
    source,
    /staff: "",/,
    "leaveForm must initialize the `staff` field (used only by managers)"
  );
});

test("submitLeave drops staff for non-managers / empty selection", () => {
  assert.match(
    source,
    /const payload = \{ \.\.\.leaveForm \};\s*if \(!canReview \|\| !payload\.staff\) delete payload\.staff;/,
    "submitLeave must build a payload and omit `staff` when the user is not a manager or no staff member was selected (avoids the backend 404)"
  );

  assert.match(
    source,
    /body: JSON\.stringify\(payload\),/,
    "submitLeave must POST the payload (with optional `staff`), not the raw form state"
  );
});

test("leave form renders a staff selector for manager roles only", () => {
  const selectorBlock = source.match(
    /\{canReview && \([\s\S]*?value=\{leaveForm\.staff\}[\s\S]*?<option value="">For myself<\/option>[\s\S]*?staffList\.map\(\(member\) => \([\s\S]*?full_name[\s\S]*?<\/select>/
  );

  assert.ok(
    selectorBlock,
    "the leave form must gate a staff-member <select> on canReview with a 'For myself' default option"
  );

  const block = selectorBlock[0];

  assert.match(
    block,
    /setLeaveForm\(\{ \.\.\.leaveForm, staff: e\.target\.value \}\)/,
    "changing the staff <select> must update leaveForm.staff"
  );

  assert.match(
    block,
    /<option value="">For myself<\/option>/,
    "the staff <select> must offer a self-leave default before the staff list"
  );
});

test("leave form must NOT send the raw form state", () => {
  assert.doesNotMatch(
    source,
    /body: JSON\.stringify\(leaveForm\)/,
    "the leave POST must use the payload builder (staff would otherwise leak as an empty id)"
  );
});