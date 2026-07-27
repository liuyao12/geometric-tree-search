import assert from "node:assert/strict";
import { OnlineFailureMarking } from "../apps/3d-lattice-tiler/online-failure-marking.js";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
const orient = { __mark_matrix: identity, __mark_shift: [0, 0, 0] };
const placement = (translation) => ({ prototile_idx: 0, orient, translation });

const learner = new OnlineFailureMarking({ max_reach: 8, enable_pair_marking: true });
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

async function runComparison(overrides) {
  let finished = null;
  for await (const message of createTilingStream({ ...config, ...overrides }, tileSpecs, { stop: false })) {
    if (message.type === "finished") finished = message;
  }
  assert.ok(finished, "comparison run must emit a terminal result");
  return finished;
}

const naive = await runComparison({ online_failure_marking: false, template_preflight: false });
const geometricGcts = await runComparison({ online_failure_marking: true, online_pair_marking: false, template_preflight: false });
const clusterAgent = await runComparison({
  online_failure_marking: true, online_pair_marking: false,
  move_order: "rl", agent_exhaustive: true, template_preflight: true, periodic_tile_count: 2
});
assert.equal(naive.success, true);
assert.equal(geometricGcts.success, true);
assert.equal(clusterAgent.success, true);
assert.ok(geometricGcts.search_stats.branch_choices_visited < naive.search_stats.branch_choices_visited, "3D GCTS must visit fewer branch choices than naive DFS");
assert.ok(geometricGcts.search_stats.backtracks < naive.search_stats.backtracks, "3D GCTS must backtrack less than naive DFS");
assert.equal(geometricGcts.search_stats.marking_pending_failures, 0, "every observed 3D failure must be geometrically encoded");
assert.equal(geometricGcts.search_stats.marking_geometric_clauses, geometricGcts.search_stats.marking_observed_failures, "one unique 3D clause must retain each deterministic failure");
assert.ok(geometricGcts.search_stats.marking_geometric_prunes > 0, "3D geometric clauses must prune repeated configurations");
assert.ok(clusterAgent.search_stats.branch_choices_visited < geometricGcts.search_stats.branch_choices_visited, "exhaustive cluster/agent proposals must improve on GCTS-only ordering");

console.log("3D naive/GCTS/GCTS+cluster comparison passed", {
  naiveChoices: naive.search_stats.branch_choices_visited,
  gctsChoices: geometricGcts.search_stats.branch_choices_visited,
  clusterChoices: clusterAgent.search_stats.branch_choices_visited
});
