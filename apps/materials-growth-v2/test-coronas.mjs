import assert from "node:assert/strict";
import { CoronaCheckpoints } from "./coronas.mjs";
const engine = (rows) => ({
  graph: new Map(
    rows.map(([id, , degree]) => [
      id,
      new Set(Array.from({ length: degree }, (_, i) => i)),
    ]),
  ),
  points: new Map(rows.map(([id, generation]) => [id, { generation }])),
});
const c = new CoronaCheckpoints();
assert.equal(
  c.check(
    engine([
      ["near", 2, 1],
      ["far", 20, 1],
    ]),
  ),
  null,
);
assert.equal(c.check(engine([["near", 3, 1]])), null);
assert.equal(
  c.check(
    engine([
      ["near", 4, 1],
      ["dead", 20, 0],
    ]),
  ),
  null,
);
assert.equal(c.next, 3); // A manual pause or blocked domain does not consume it.
assert.equal(c.check(engine([["near", 4, 1]])).corona, 3);
assert.equal(c.next, 5);
assert.equal(c.check(engine([["near", 4, 1]])), null);
assert.equal(c.check(engine([["rollback", 1, 1]])), null);
assert.equal(c.check(engine([["near", 6, 1]])).corona, 5);
assert.equal(c.check(engine([["near", 8, 1]])).corona, 7);
assert.equal(c.check(engine([])), null); // Empty frontier is not infinity.
assert.equal(c.progress(engine([])).completed, null);
const jump = new CoronaCheckpoints();
assert.equal(jump.check(engine([["near", 10, 1]])).corona, 3);
assert.equal(jump.next, 11);
console.log(
  "PASS corona thresholds 3/5/7, frontier holes, distant dead/unknown domains, resume, rollback, empty frontier and jumps",
);
