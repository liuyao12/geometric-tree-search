import assert from "node:assert/strict";
import { GeometricFailureMemo } from "../assets/geometric-failure-memo.js";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const placement = (orientation, translation) => ({
  kind: "tile",
  orientation,
  translation
});

// A learned failure is translation equivariant, but only the complete exact
// context may trigger it. A strict subset must remain admissible.
const memo = new GeometricFailureMemo({
  contextMatch: "subset",
  describePlacement: value => value
});
const root = placement("o0", [0, 0, 0]);
const neighbor = placement("o1", [0, 1, 0]);
const failed = placement("o2", [1, 0, 0]);
const encoded = memo.encode([root, neighbor], failed, { source: "synthetic" });
assert.equal(encoded.duplicate, false);
assert.equal(
  memo.compatible(
    placement("o2", [11, -4, 3]),
    [placement("o0", [10, -4, 3]), placement("o1", [10, -3, 3])]
  ),
  false,
  "a translated copy of the complete failed context must be pruned"
);
assert.equal(
  memo.compatible(
    placement("o2", [11, -4, 3]),
    [placement("o0", [10, -4, 3])]
  ),
  true,
  "an incomplete context must not trigger the learned failure"
);

async function solve(genericGeometricNogood) {
  let final = null;
  let largestPatch = 0;
  const config = {
    mode_key: "census_10_45026",
    polycube_lattice: "z3",
    criterion: "count",
    target_val: 24,
    tiling_strategy: "free_range",
    move_order: "balanced",
    face_order: "mrv",
    exhaustive: true,
    agent_exhaustive: true,
    forced_move_layer_lag_cap: 0,
    include_mirrors: false,
    template_preflight: false,
    branch_cap: null,
    candidate_cap: null,
    node_limit: 200,
    time_limit_ms: 5000,
    ui_yield_interval_ms: 1000000,
    generic_failure_memo: true,
    generic_geometric_nogood: genericGeometricNogood,
    generic_geometric_nogood_max_clauses: 20000
  };
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    largestPatch = Math.max(largestPatch, message.tile_count ?? message.snapshot?.tile_count ?? 0);
    if (message.type === "finished") final = message;
  }
  assert.ok(final, "the integrated proof search must emit a terminal result");
  return { final, largestPatch };
}

const baseline = await solve(false);
const learned = await solve(true);
assert.equal(baseline.final.search_stats.termination_reason, "node_limit");
assert.equal(learned.final.search_stats.termination_reason, "node_limit");
assert.equal(baseline.final.search_incomplete, true);
assert.equal(learned.final.search_incomplete, true);
assert.equal(baseline.final.search_stats.generic_geometric_nogood_enabled, false);
assert.equal(learned.final.search_stats.generic_geometric_nogood_enabled, true);
assert.ok(learned.final.search_stats.generic_geometric_nogood_clauses >= 1000);
assert.ok(learned.final.search_stats.generic_geometric_nogood_prunes >= 400);
assert.equal(learned.final.search_stats.generic_geometric_nogood_capacity_reached, false);
assert.ok(
  learned.largestPatch >= baseline.largestPatch + 4,
  "online translated nogoods must deepen the fixed-node candidate proof search"
);

console.log("3D online geometric-failure learning regression passed", {
  baselinePatch: baseline.largestPatch,
  learnedPatch: learned.largestPatch,
  clauses: learned.final.search_stats.generic_geometric_nogood_clauses,
  prunes: learned.final.search_stats.generic_geometric_nogood_prunes
});
