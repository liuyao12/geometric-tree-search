import assert from "node:assert/strict";

import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

async function solve(config) {
  let finished = null;
  for await (const message of createTilingStream({
    snapshot_every: 0,
    ui_yield_interval_ms: 1_000_000,
    time_limit_ms: 10_000,
    ...config
  }, tileSpecs, { stop: false })) {
    if (message.type === "finished") finished = message;
  }
  assert.ok(finished);
  return finished;
}

const certificateWithoutGoal = await solve({
  mode_key: "cube",
  criterion: "count",
  target_val: 100,
  tiling_strategy: "translational",
  periodic_stop_at_growth_goal: true,
  periodic_patch_max_tiles: 1,
  safety_max_tiles: 1
});
assert.equal(certificateWithoutGoal.can_tile, true);
assert.equal(certificateWithoutGoal.success, false);
assert.equal(certificateWithoutGoal.result_kind, "certified_tiling_goal_incomplete");
assert.equal(certificateWithoutGoal.search_incomplete, true);
assert.equal(certificateWithoutGoal.search_stats.termination_reason, "safety_tile_limit");

const multiSpeciesRootFailure = await solve({
  mode_key: "custom",
  custom_system: {
    name: "non-tiling root plus tiling cube species",
    polyhedra: [
      { name: "scalene tetrahedron", vertices: [[0, 0, 0], [2, 0, 0], [0, 3, 0], [0, 0, 5]] },
      { name: "unit cube", vertices: [
        [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
        [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]
      ] }
    ],
    polycubes: [],
    polycube_lattice: "z3"
  },
  criterion: "shell",
  target_val: 1,
  tiling_strategy: "generic",
  move_order: "shell",
  exhaustive: true,
  generic_complete_shell_enumeration: true,
  forced_move_layer_lag_cap: 0,
  branch_cap: null,
  candidate_cap: null,
  node_limit: 100_000,
  template_preflight: false
});
assert.notEqual(multiSpeciesRootFailure.can_tile, false);
assert.notEqual(multiSpeciesRootFailure.result_kind, "no_tiling");
assert.equal(multiSpeciesRootFailure.tiling_evidence?.can_tile_in_rooted_face_to_face_model, false);

console.log("3D independent-audit correctness regressions passed", {
  certificateGoal: certificateWithoutGoal.result_kind,
  multiSpecies: multiSpeciesRootFailure.result_kind
});
