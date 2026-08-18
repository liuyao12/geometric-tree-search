import assert from "node:assert/strict";

import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const polyhedron = (id, vertices) => ({
  mode_key: "cube",
  custom_system: {
    name: `Census ${id}`,
    figure_refs: [],
    polycubes: [],
    polyhedra: [{ name: `Candidate ${id}`, vertices }],
    polycube_lattice: "z3"
  },
  polycube_lattice: "z3",
  criterion: "count",
  target_val: 24,
  tiling_strategy: "isohedral",
  move_order: "isohedral",
  face_order: "mrv",
  exhaustive: true,
  include_mirrors: false,
  template_preflight: true,
  snapshot_every: 0,
  branch_cap: null,
  candidate_cap: null,
  node_limit: 500000,
  ui_yield_interval_ms: 1000000
});

async function solve(config) {
  let finished = null;
  let finalSnapshot = null;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.type === "full_update") finalSnapshot = message;
    if (message.type === "finished") finished = message;
  }
  return { finished, finalSnapshot };
}

const certified = await solve({
  ...polyhedron("10_27010", [[0,0,0],[0,1,1],[1,0,1],[1,1,2],[1,2,0],[2,0,0],[2,1,1]]),
  time_limit_ms: 10000
});

assert.equal(certified.finished?.success, true);
assert.equal(certified.finished?.result_kind, "certified_tiling");
assert.equal(certified.finished?.tiling_evidence?.kind, "isohedral_certificate");
assert.equal(certified.finished?.tiling_evidence?.patch_size, 24);
assert.equal(certified.finished?.can_tile, true);

const limited = await solve({
  ...polyhedron("10_45026", [[0,0,2],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,0],[1,2,1],[2,1,0],[2,1,1]]),
  time_limit_ms: 100
});

assert.equal(limited.finished?.success, false);
assert.equal(limited.finished?.result_kind, "search_incomplete");
assert.equal(limited.finished?.search_incomplete, true);
assert.equal(limited.finished?.tile_count, 1);
assert.equal(limited.finalSnapshot?.tile_count, 1, "failed isohedral runs must restore the root view");

console.log("3D exact isohedral certificate regressions passed", {
  certifiedMotif: certified.finished.tiling_evidence.patch_size,
  limitedResult: limited.finished.result_kind,
  restoredTiles: limited.finalSnapshot.tile_count
});
