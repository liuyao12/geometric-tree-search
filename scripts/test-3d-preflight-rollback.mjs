import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const config = {
  mode_key: "rhombic",
  custom_system: {
    name: "Transactional preflight regression",
    figure_refs: ["rhombic::0"],
    polycubes: [],
    polycube_lattice: "z3"
  },
  polycube_lattice: "z3",
  criterion: "count",
  target_val: 8,
  exhaustive: false,
  include_mirrors: false,
  snapshot_every: 1000,
  face_order: "mrv",
  move_order: "isohedral",
  agent_exhaustive: true,
  branch_cap: null,
  node_limit: 10000,
  candidate_cap: null,
  time_limit_ms: 30000,
  ui_yield_interval_ms: 1000,
  template_preflight: true,
  periodic_preflight: false,
  isohedral_preflight_max_steps: 2
};

let rollbackRemovals = 0;
let rollbackStatuses = 0;
let finished = null;
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  if (message.type === "placement_delta" && message.action === "remove") rollbackRemovals += 1;
  if (message.type === "node_status" && message.text === "isohedral preflight rolled back") {
    rollbackStatuses += 1;
  }
  if (message.type === "finished") finished = message;
}

assert.equal(rollbackRemovals, config.isohedral_preflight_max_steps);
assert.equal(rollbackStatuses, config.isohedral_preflight_max_steps);
assert.ok(finished?.success, "complete fallback search must solve after speculative rollback");
assert.equal(finished.tile_count, config.target_val);
assert.ok(
  finished.search_stats.branch_choices_visited > 0 || finished.search_stats.forced_total > 0,
  "fallback DFS must actually run"
);

console.log("3D transactional preflight rollback regression passed", {
  rolledBack: rollbackRemovals,
  tiles: finished.tile_count,
  fallbackChoices: finished.search_stats.branch_choices_visited,
  fallbackForced: finished.search_stats.forced_total
});
