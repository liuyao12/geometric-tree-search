import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";

const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === "p10-054782");
assert.ok(candidate);

const target = 2;
const checks = [];
let final = null;
for await (const message of createTilingStream({
  mode_key: "cube",
  custom_system: {
    name: candidate.id,
    figure_refs: [],
    polycubes: [{ name: candidate.id, voxels: candidate.voxels }],
    polyhedra: [],
    polycube_lattice: "z3"
  },
  polycube_lattice: "z3",
  criterion: "count",
  target_val: target,
  tiling_strategy: "translational",
  move_order: "periodic",
  include_mirrors: false,
  template_preflight: true,
  periodic_preflight: true,
  periodic_patch_unbounded: false,
  periodic_patch_max_tiles: target,
  periodic_stop_at_growth_goal: true,
  periodic_motif_node_limit: 2500,
  snapshot_every: 0,
  time_limit_ms: 10000
}, tileSpecs, { stop: false })) {
  if (message.type === "translational_check") checks.push(message);
  if (message.type === "finished") final = message;
}

assert.ok(final);
assert.equal(checks.at(-1)?.growth_goal_reached, true);
assert.equal(final.tile_count, target);
assert.equal(final.success, false);
assert.equal(final.result_kind, "search_incomplete");
assert.equal(final.search_stats.termination_reason, "translational_growth_goal_without_certificate");
console.log("3D translational finite-goal regression passed", {
  checks: checks.length,
  tiles: final.tile_count,
  resultKind: final.result_kind
});
