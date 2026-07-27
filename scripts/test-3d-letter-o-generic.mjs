import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const letterOVoxels = [];
for (let x = 0; x < 3; x++) {
  for (let y = 0; y < 4; y++) {
    if (x === 1 && (y === 1 || y === 2)) continue;
    letterOVoxels.push([x, y, 0]);
  }
}

const baseConfig = {
  mode_key: "letter_o",
  polycube_lattice: "z3",
  criterion: "count",
  target_val: 12,
  exhaustive: false,
  include_mirrors: false,
  snapshot_every: 100,
  face_order: "mrv",
  move_order: "rl",
  agent_exhaustive: true,
  branch_cap: null,
  node_limit: 3000,
  candidate_cap: null,
  time_limit_ms: 10000,
  ui_yield_interval_ms: 1000,
  online_failure_marking: true,
  template_preflight: true,
  periodic_tile_count: 2
};

async function solve(customSystem) {
  let finished = null;
  let certifiedSteps = 0;
  let certifiedGrowthNodes = 0;
  for await (const message of createTilingStream(
    { ...baseConfig, custom_system: customSystem },
    tileSpecs,
    { stop: false }
  )) {
    if (message.type === "placement_delta" && message.action === "add") certifiedSteps += 1;
    if (message.type === "branch_set") certifiedGrowthNodes +=
      (message.branches ?? []).filter(branch => branch.text === "certified forced growth").length;
    if (message.type === "finished") finished = message;
  }
  assert.ok(finished, "Letter O regression must emit a terminal result");
  return { finished, certifiedSteps, certifiedGrowthNodes };
}

const catalog = await solve({
  name: "Catalog Letter O",
  figure_refs: ["letter_o::0"],
  polycubes: [],
  polycube_lattice: "z3"
});
const anonymous = await solve({
  name: "Anonymous custom system",
  figure_refs: [],
  polycubes: [{ name: "Anonymous ring", voxels: letterOVoxels }],
  polycube_lattice: "z3"
});

for (const result of [catalog, anonymous]) {
  assert.equal(result.finished.success, true);
  assert.equal(result.finished.tile_count, baseConfig.target_val);
  assert.equal(result.finished.search_stats.branch_choices_visited, 0);
  assert.equal(result.finished.search_stats.backtracks, 0);
  assert.equal(result.finished.search_stats.marking_observed_failures, 0);
  assert.equal(result.finished.search_stats.marking_geometric_clauses, 0);
  assert.equal(result.certifiedSteps, baseConfig.target_val - 1);
  assert.equal(result.certifiedGrowthNodes, 1);
  assert.equal(result.finished.search_stats.forced_total, baseConfig.target_val - 1);
}
assert.deepEqual(
  {
    tiles: catalog.finished.tile_count,
    choices: catalog.finished.search_stats.branch_choices_visited,
    certifiedSteps: catalog.certifiedSteps
  },
  {
    tiles: anonymous.finished.tile_count,
    choices: anonymous.finished.search_stats.branch_choices_visited,
    certifiedSteps: anonymous.certifiedSteps
  },
  "catalog identity and tile name must not affect the generic Letter O solution"
);

console.log("3D Letter O tile-agnostic regression passed", {
  tiles: catalog.finished.tile_count,
  certifiedSteps: catalog.certifiedSteps,
  catalogName: "Letter O",
  customName: "Anonymous ring"
});
