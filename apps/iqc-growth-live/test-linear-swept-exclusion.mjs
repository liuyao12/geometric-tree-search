import assert from "node:assert/strict";
import { auditLinearSweptExclusion } from "./linear-swept-exclusion.mjs";

const crossing = auditLinearSweptExclusion([{
  firstId: "a", secondId: "b",
  firstStart: [-1, 0, 0], firstEnd: [1, 0, 0],
  secondStart: [1, 0, 0], secondEnd: [-1, 0, 0],
  exclusion: .4,
}]);
assert.equal(crossing.passed, false);
assert.equal(crossing.closestPair.fraction, .5);
assert.equal(crossing.closestPair.closestDistance, 0);
assert.equal(crossing.sampledOnly, false);

const parallel = auditLinearSweptExclusion([{
  firstStart: [0, 0, 0], firstEnd: [1, 0, 0],
  secondStart: [0, 2, 0], secondEnd: [1, 2, 0],
  exclusion: 1,
}]);
assert.equal(parallel.passed, true);
assert.equal(parallel.minimumMargin, 1);
assert.equal(parallel.targetUsed, false);

const interiorClosest = auditLinearSweptExclusion([{
  firstStart: [0, 0, 0], firstEnd: [0, 0, 0],
  secondStart: [-1, 1, 0], secondEnd: [1, 1, 0],
  exclusion: .9,
}]);
assert.equal(interiorClosest.passed, true);
assert.equal(interiorClosest.closestPair.fraction, .5);
assert.ok(Math.abs(interiorClosest.closestPair.closestDistance - 1) < 1e-12);

assert.throws(() => auditLinearSweptExclusion([]), /at least one pair/);
assert.throws(() => auditLinearSweptExclusion([{
  firstStart: [0, 0, 0], firstEnd: [0, 0, 0],
  secondStart: [1, 0, 0], secondEnd: [1, 0, 0], exclusion: -1,
}]), /invalid exclusion/);

console.log("linear swept-exclusion tests passed");
