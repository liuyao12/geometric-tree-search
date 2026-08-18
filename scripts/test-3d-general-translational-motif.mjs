import assert from "node:assert/strict";

import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const config = {
  mode_key: "cube",
  custom_system: {
    name: "Census 10_24775 translational regression",
    figure_refs: [],
    polycubes: [],
    polyhedra: [{
      name: "Candidate 10_24775",
      vertices: [[-1,-1,0],[-1,1,1],[0,0,2],[0,1,-1],[1,0,0],[1,2,1]]
    }],
    polycube_lattice: "z3"
  },
  criterion: "count",
  target_val: 60,
  tiling_strategy: "translational",
  move_order: "balanced",
  face_order: "mrv",
  exhaustive: true,
  template_preflight: true,
  periodic_patch_max_tiles: 4,
  snapshot_every: 0,
  placement_details: true,
  node_limit: 200000,
  time_limit_ms: 30000,
  branch_cap: null,
  candidate_cap: null,
  ui_yield_interval_ms: 1000000
};

const checks = [];
let certificate = null;
let finished = null;
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  if (message.type === "translational_check") {
    checks.push(message.patch_size);
    if (message.certified) certificate = message.periodic_template;
  }
  if (message.type === "finished") finished = message;
}

assert.deepEqual(checks, [1, 2, 3]);
assert.equal(certificate?.kind, "3_tile_boundary_quotient");
assert.equal(certificate?.motif.length, 3);
assert.equal(certificate?.cell_volume, 14);
assert.equal(Math.abs(
  certificate.period_vectors[0][0] * (
    certificate.period_vectors[1][1] * certificate.period_vectors[2][2]
      - certificate.period_vectors[1][2] * certificate.period_vectors[2][1]
  )
  - certificate.period_vectors[0][1] * (
    certificate.period_vectors[1][0] * certificate.period_vectors[2][2]
      - certificate.period_vectors[1][2] * certificate.period_vectors[2][0]
  )
  + certificate.period_vectors[0][2] * (
    certificate.period_vectors[1][0] * certificate.period_vectors[2][1]
      - certificate.period_vectors[1][1] * certificate.period_vectors[2][0]
  )
), 14);
assert.equal(certificate.proof.method, "face_paired_boundary_equal_covolume");
assert.equal(certificate.proof.boundary_pairing.length * 2, certificate.proof.boundary_face_count);
assert.equal(finished?.success, true);
assert.equal(finished?.result_kind, "certified_tiling");
assert.equal(finished?.tile_count, 60);
assert.equal(finished?.search_stats?.growth_axis_rank, 3);
assert.ok(finished?.search_stats?.periodic_motif_nodes > 0);

console.log("General polyhedral translational-motif regression passed", {
  checks,
  motifSize: certificate.motif.length,
  cellVolume: certificate.cell_volume,
  periodVectors: certificate.period_vectors,
  searchNodes: finished.search_stats.periodic_motif_nodes
});
