import assert from "node:assert/strict";
import { OnlineFailureMarking } from "../apps/3d-lattice-tiler/online-failure-marking.js";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
const orient = { __mark_matrix: identity, __mark_shift: [0, 0, 0] };
const placement = (translation) => ({ prototile_idx: 0, orient, translation });

const learner = new OnlineFailureMarking({ max_reach: 8 });
const root = placement([0, 0, 0]);
const good = placement([1, 0, 0]);
const bad = placement([2, 0, 0]);

assert.equal(learner.support.size, 0, "marking starts literally empty");
const update = learner.learn([root, good], bad);
assert.equal(update.committed, true, "failed branch should be encodable");
assert.equal(learner.patchCompatible([root, good], learner.support), true, "surviving prefix replays");
assert.equal(learner.compatible(bad, [root, good]), false, "learned marking rejects failed branch");

const nextBad = placement([3, 0, 0]);
const next = learner.learn([root, good], nextBad);
assert.equal(next.committed, true, "support can grow along the lattice");
assert.equal(learner.patchCompatible([root, good], learner.support), true);
for (const failure of learner.failures) {
  assert.equal(learner.compatible(failure.candidate, failure.context), false, "old failures stay rejected");
}
assert.equal(learner.failureLedger.length, 2, "every observed failed branch is retained");
assert.equal(learner.pendingFailures.length, 0, "both synthetic failures are encoded");

// Exercise the real 3D search integration, not only the learner in isolation.
// 1-Cross generates a genuine exhausted branch quickly; stop after observing
// the first transactional marking update so the regression remains bounded.
const stopToken = { stop: false };
const config = {
  mode_key: "1_cross",
  custom_system: { name: "3D GCTS regression", figure_refs: ["1_cross::0"], polycubes: [], polycube_lattice: "z3" },
  polycube_lattice: "z3",
  criterion: "count",
  target_val: 8,
  exhaustive: false,
  include_mirrors: false,
  snapshot_every: 100,
  move_order: "coverage",
  face_order: "mrv",
  branch_cap: null,
  node_limit: 3000,
  candidate_cap: null,
  time_limit_ms: 10000,
  ui_yield_interval_ms: 8,
  online_failure_marking: true,
  template_preflight: false,
  periodic_tile_count: 0
};
let engineUpdate = null;
for await (const message of createTilingStream(config, tileSpecs, stopToken)) {
  if (message.type !== "marking_update") continue;
  engineUpdate = message;
  stopToken.stop = true;
}
assert.ok(engineUpdate, "the 3D tiler must learn from a genuinely exhausted search branch");
assert.ok(engineUpdate.revision > 0 && engineUpdate.failures > 0);
assert.equal(engineUpdate.pending_failures, 0, "the emitted 3D failure is geometrically encoded");
assert.equal(engineUpdate.search_stats.marking_revisions, engineUpdate.revision);

console.log("3D online failure marking and engine integration passed", {
  revision: engineUpdate.revision,
  supportSites: engineUpdate.support_sites,
  observedFailures: engineUpdate.observed_failures,
  pendingFailures: engineUpdate.pending_failures
});
