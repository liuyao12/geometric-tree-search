import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const config = {
  mode_key: "cube",
  custom_system: {
    name: "Finite box regression",
    figure_refs: ["cube::0"],
    polycubes: [],
    polyhedra: [],
    polycube_lattice: "z3"
  },
  polycube_lattice: "z3",
  criterion: "region",
  tiling_strategy: "free_range",
  target_region: {
    type: "box",
    center: [2, 1.5, 1],
    size: [4, 3, 2]
  },
  exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_failure_memo: true,
  generic_failure_memo_symmetry: "rigid",
  generic_geometric_nogood: true,
  include_mirrors: false,
  snapshot_every: 100,
  placement_details: true,
  face_order: "mrv",
  move_order: "rl",
  agent_exhaustive: true,
  template_preflight: true,
  periodic_tile_count: 1,
  node_limit: 5000,
  time_limit_ms: 10000,
  ui_yield_interval_ms: 1000
};

let snapshot = null;
let finished = null;
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  if (message.type === "full_update") snapshot = message;
  if (message.type === "finished") finished = message;
}

assert.equal(finished?.success, true, "the exact finite box must tile");
assert.equal(snapshot?.tile_count, 24);
assert.equal(finished.search_stats.placed_volume, 24);
assert.equal(finished.search_stats.target_volume, 24);
assert.equal(finished.search_stats.region_type, "box");
assert.equal(finished.search_stats.generic_failure_memo_enabled, true);
assert.equal(
  finished.search_stats.generic_failure_memo_key_equivalence,
  "fixed_frame_region_guard",
  "an asymmetric finite region must disable rigid-motion memo equivalence"
);
assert.equal(finished.search_stats.generic_geometric_nogood_enabled, false);
assert.equal(
  finished.search_stats.generic_geometric_nogood_disable_reason,
  "finite_target_region",
  "translation-equivariant nogoods must be disabled inside a fixed finite region"
);
for (const placement of snapshot.placements) {
  assert.ok(placement.center[0] >= 0 && placement.center[0] <= 4);
  assert.ok(placement.center[1] >= 0 && placement.center[1] <= 3);
  assert.ok(placement.center[2] >= 0 && placement.center[2] <= 2);
}

console.log("3D finite-region regression passed", {
  tiles: snapshot.tile_count,
  volume: finished.search_stats.placed_volume,
  spans: finished.search_stats.growth_spans
});

const orthoschemeConfig = {
  mode_key: "orthoscheme",
  criterion: "region",
  target_region: {
    type: "box",
    center: [1, 1, 1],
    size: [2, 2, 2]
  },
  tiling_strategy: "freestyle",
  include_mirrors: true,
  template_preflight: false,
  branch_cap: 1000,
  candidate_cap: 100000,
  node_limit: 100000,
  time_limit_ms: 10000,
  safety_max_tiles: 100,
  ui_yield_interval_ms: 1000
};

let orthoschemeFinished = null;
for await (const message of createTilingStream(orthoschemeConfig, tileSpecs, { stop: false })) {
  if (message.type === "finished") orthoschemeFinished = message;
}

assert.equal(orthoschemeFinished?.result_kind, "certified_tiling");
assert.equal(orthoschemeFinished?.can_tile, true);
assert.equal(orthoschemeFinished?.tile_count, 6);
assert.equal(orthoschemeFinished?.tiling_evidence?.kind, "exact_region_fill");
