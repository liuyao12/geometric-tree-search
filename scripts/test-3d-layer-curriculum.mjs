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
  gcts_failure_marking: true,
  gcts_marking_symmetry: "fixed",
  gcts_marking_index: true,
  agent_exhaustive: true,
  agent_policy: "cold_geometry",
  learned_layer_macro: true,
  learned_layer_macro_max_motif_tiles: 8,
  learned_layer_macro_motif_node_limit: 2500,
  learned_layer_macro_discovery_time_ms: 15000,
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

let final = null;
let maximumCompletedShell = 0;
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
  maximumCompletedShell = Math.max(
    maximumCompletedShell,
    snapshot?.frontier_stats?.complete_shell_depth ?? 0
  );
  if (message.type === "finished") final = message;
}

assert.equal(final?.success, true, "cold GCTS+RL must fill the shell-2 periodic control");
assert.ok(maximumCompletedShell >= 2, "success must mean the live patch completed shell 2");
assert.equal(final?.tiling_evidence?.kind, "translational_certificate");
assert.equal(final?.tiling_evidence?.patch_size, 6, "the six-tile cluster must be discovered from geometry");
assert.equal(final?.search_incomplete, false);

console.log("3D cold shell-curriculum regression passed", {
  completedShell: maximumCompletedShell,
  tiles: final.tile_count,
  motifTiles: final.tiling_evidence.patch_size,
  visitedNodes: final.search_stats.visited_nodes
});
