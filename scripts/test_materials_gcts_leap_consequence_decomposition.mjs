import assert from "node:assert/strict";
import {
  LEAP_CONSEQUENCE_COMPONENTS,
  resolveLeapConsequenceComparison,
} from "../apps/iqc-growth-live/leap-consequence-decomposition.mjs";

const before = { atoms: 100, coordination: 0.2 };
const asPlaced = { atoms: 112, coordination: 0.16 };
const after = { atoms: 112, coordination: 0.12 };
const leap = {
  before,
  asPlaced,
  after,
  relaxation: { accepted: true, reason: "certified" },
};

assert.deepEqual(Object.keys(LEAP_CONSEQUENCE_COMPONENTS), ["total", "attachment", "settling"]);

const total = resolveLeapConsequenceComparison(leap, "total");
assert.equal(total.before, before);
assert.equal(total.after, after);
assert.equal(total.mode, "total");

const attachment = resolveLeapConsequenceComparison(leap, "attachment");
assert.equal(attachment.before, before);
assert.equal(attachment.after, asPlaced);
assert.equal(attachment.axisLabel, "before → as placed");

const settling = resolveLeapConsequenceComparison(leap, "settling");
assert.equal(settling.before, asPlaced);
assert.equal(settling.after, after);
assert.equal(settling.settlingAccepted, true);
assert.match(settling.explanation, /Only newly emitted sites move/);

const rejected = resolveLeapConsequenceComparison({ ...leap,
  after: asPlaced, relaxation: { accepted: false, reason: "hard exclusion" } }, "settling");
assert.equal(rejected.before, asPlaced);
assert.equal(rejected.after, asPlaced);
assert.match(rejected.explanation, /hard exclusion/);

const legacy = resolveLeapConsequenceComparison({ before, after }, "settling");
assert.equal(legacy.mode, "total");
assert.equal(legacy.componentAvailable, false);

const seed = resolveLeapConsequenceComparison(null, "attachment", before);
assert.equal(seed.mode, "total");
assert.equal(seed.before, before);
assert.equal(seed.after, before);

console.log("leap consequence decomposition contract passed");
