import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { LATTICE_POLYHEDRON_CENSUS_POOL } from "../assets/lattice-polyhedron-survivors.js";

const candidate = LATTICE_POLYHEDRON_CENSUS_POOL.find(entry => entry.id === "10_45033");
assert.ok(candidate, "the periodic hard control must remain in the census pool");

const config = {
  mode_key: "cube",
  custom_system: {
    name: "Cold layer curriculum 10_45033",
    figure_refs: [],
    polycubes: [],
    polyhedra: [{ name: "Anonymous lattice polyhedron", vertices: candidate.vertices }],
    polycube_lattice: "z3"
  },
  criterion: "shell",
  target_val: 2,
  tiling_strategy: "free_range",
  move_order: "rl",
  face_order: "mrv",
  complete_lattice_point_branching: true,
  gcts_failure_marking: false,
  gcts_marking_symmetry: "fixed",
  gcts_marking_index: true,
  agent_exhaustive: true,
  agent_policy: "cold_linucb",
  agent_ucb_alpha: 0,
  learned_layer_macro: false,
  known_periodic_template: null,
  initial_patch: null,
  proposal_program: null,
  template_preflight: false,
  periodic_preflight: false,
  forced_move_layer_lag_cap: 0,
  generic_complete_shell_enumeration: true,
  generic_failure_memo: true,
  random_seed: 1,
  seeded_tie_breaks: true,
  exhaustive: true,
  node_limit: 1000000,
  time_limit_ms: 10000,
  snapshot_every: 1,
  ui_yield_interval_ms: 1000000
};

const run = async (marking, overrides = {}) => {
  let final = null;
  let maximumCompletedShell = 0;
  for await (const message of createTilingStream(
    { ...config, ...overrides, gcts_failure_marking: marking },
    tileSpecs,
    { stop: false }
  )) {
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    maximumCompletedShell = Math.max(
      maximumCompletedShell,
      snapshot?.frontier_stats?.complete_shell_depth ?? 0
    );
    if (message.type === "finished") final = message;
  }
  return { final, maximumCompletedShell };
};

const rl = await run(false);
const hybrid = await run(true);
for (const result of [rl, hybrid]) {
  assert.equal(result.final?.success, true, "cold RL policies must fill the shell-2 periodic control");
  assert.ok(result.maximumCompletedShell >= 2, "success must mean the live patch completed shell 2");
  assert.equal(result.final?.search_stats?.learned_layer_macro_enabled, false);
  assert.equal(result.final?.search_stats?.learned_layer_macro_tiles_applied, 0);
  assert.equal(result.final?.search_stats?.agent_model_parameter_count, 143);
  assert.equal(result.final?.search_stats?.agent_model_weight_count, 11);
  assert.equal(result.final?.search_stats?.agent_model_payload_bytes, 1144);
  assert.equal(result.final?.search_incomplete, false);
}
assert.ok(
  hybrid.final.search_stats.visited_nodes <= rl.final.search_stats.visited_nodes,
  "GCTS+RL must not visit more branches than the identical RL policy on the parity control"
);

const negativeCandidate = LATTICE_POLYHEDRON_CENSUS_POOL.find(entry => entry.id === "10_16113");
assert.ok(negativeCandidate, "the exact shell-2 non-tiler control must remain in the census pool");
const negativeOverrides = {
  custom_system: {
    name: "Anonymous exact shell control",
    figure_refs: [],
    polycubes: [],
    polyhedra: [{ name: "Anonymous lattice polyhedron", vertices: negativeCandidate.vertices }],
    polycube_lattice: "z3"
  },
  learned_layer_macro: false
};
const negativeRl = await run(false, negativeOverrides);
const negativeHybrid = await run(true, negativeOverrides);
for (const result of [negativeRl, negativeHybrid]) {
  assert.equal(result.final?.result_kind, "no_tiling", "both parity lanes must retain the exact shell obstruction");
  assert.equal(result.final?.can_tile, false);
}
assert.ok(
  negativeHybrid.final.search_stats.visited_nodes <= negativeRl.final.search_stats.visited_nodes,
  "exact GCTS pruning must not visit more nodes than the identical RL shell search"
);

console.log("3D cold shell-curriculum regression passed", {
  completedShell: hybrid.maximumCompletedShell,
  tiles: hybrid.final.tile_count,
  oneTileActions: hybrid.final.search_stats.branch_choices_visited,
  rlVisitedNodes: rl.final.search_stats.visited_nodes,
  hybridVisitedNodes: hybrid.final.search_stats.visited_nodes,
  negativeRlNodes: negativeRl.final.search_stats.visited_nodes,
  negativeHybridNodes: negativeHybrid.final.search_stats.visited_nodes,
  negativeMarkingPrunes: negativeHybrid.final.search_stats.marking_geometric_prunes
});
