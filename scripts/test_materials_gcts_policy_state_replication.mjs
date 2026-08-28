import assert from "node:assert/strict";
import { runBlockedStateReplication } from "../apps/iqc-growth-live/policy-state-replication.mjs";

const record = (receipt, input, value, options = {}) => ({
  receiptSha256: receipt,
  inputIdentity: input,
  inputStructureSha256: input,
  scenarioId: options.scenarioId || "crystal",
  material: options.material || "test",
  termId: "bond-valence",
  outcomeId: "antichain",
  targetUsed: options.targetUsed ?? false,
  rows: [{ observableId: "coordinationDeficit", resolved: options.resolved ?? true,
    normalizedDifference: value, difference: value, changedCount: 4, stableCount: 4 }],
});

const repeat = runBlockedStateReplication([
  record("a", "input-a", .2), record("b", "input-a", .4), record("c", "input-a", .3),
  record("a", "input-a", .2),
], { termId: "bond-valence", outcomeId: "antichain", observableId: "coordinationDeficit" });
assert.equal(repeat.status, "repeat-run-consistent");
assert.equal(repeat.eligibleRunCount, 3);
assert.equal(repeat.exactDuplicateReceiptsIgnored, 1);
assert.equal(repeat.medianNormalizedDifference, .3);

const crossInput = runBlockedStateReplication([
  record("a", "input-a", -.2), record("b", "input-b", -.4), record("c", "input-c", -.3),
], { termId: "bond-valence", outcomeId: "antichain", observableId: "coordinationDeficit" });
assert.equal(crossInput.status, "cross-input-consistent");
assert.equal(crossInput.dominantDirection, -1);
assert.equal(crossInput.distinctInputs, 3);

const heterogeneous = runBlockedStateReplication([
  record("a", "input-a", .2), record("b", "input-b", -.4), record("c", "input-c", .3),
], { termId: "bond-valence", outcomeId: "antichain", observableId: "coordinationDeficit" });
assert.equal(heterogeneous.status, "heterogeneous");
assert.equal(heterogeneous.replicatedDirection, false);

const guarded = runBlockedStateReplication([
  record("a", "input-a", .2), record("b", "input-b", .4, { resolved: false }),
  record("c", "input-c", .3, { targetUsed: true }),
], { termId: "bond-valence", outcomeId: "antichain", observableId: "coordinationDeficit" });
assert.equal(guarded.status, "insufficient-runs");
assert.equal(guarded.unresolvedRuns, 1);
assert.equal(guarded.targetTaintedRuns, 1);
assert.equal(guarded.frontierRowsPooledAcrossRuns, false);

console.log("policy-state replication tests passed");
