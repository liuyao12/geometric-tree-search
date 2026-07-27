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
  target_region: {
    type: "box",
    center: [2, 1.5, 1],
    size: [4, 3, 2]
  },
  exhaustive: false,
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
