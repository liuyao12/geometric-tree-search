import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const latticeCube = {
  name: "User-defined lattice cube",
  vertices: [
    [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
    [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]
  ]
};
const target = Math.max(1, Number(process.env.TILER_TARGET) || 200);

const config = {
  mode_key: "cube",
  custom_system: {
    name: "Custom convex lattice polyhedron regression",
    figure_refs: [],
    polycubes: [],
    polyhedra: [latticeCube],
    polycube_lattice: "z3"
  },
  polycube_lattice: "z3",
  criterion: "count",
  target_val: target,
  exhaustive: false,
  include_mirrors: false,
  snapshot_every: 1000,
  placement_details: true,
  face_order: "mrv",
  move_order: "rl",
  agent_exhaustive: true,
  branch_cap: null,
  node_limit: 10000,
  candidate_cap: null,
  time_limit_ms: 30000,
  ui_yield_interval_ms: 1000,
  template_preflight: true,
  periodic_tile_count: 2,
  online_failure_marking: true
};

let prototileInfo = null;
let periodicCertificate = null;
let finished = null;
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  if (message.type === "prototile_info") prototileInfo = message;
  if (message.periodic_template?.kind === "one_tile_translational_parallelepiped") {
    periodicCertificate = message.periodic_template;
  }
  if (message.type === "finished") finished = message;
}

assert.ok(finished?.success);
assert.equal(finished.tile_count, config.target_val);
assert.equal(prototileInfo?.tiles?.[0]?.name, latticeCube.name);
assert.ok(periodicCertificate, "the arbitrary lattice cube must receive a translational certificate");
assert.equal(periodicCertificate.proof.method, "paired_facets_integral_lattice_and_equal_covolume");
assert.equal(periodicCertificate.proof.face_pairs.length, 3);
assert.equal(periodicCertificate.proof.polyhedron_volume, periodicCertificate.proof.lattice_determinant);
assert.equal(finished.search_stats.growth_axis_rank, 3);
assert.ok(finished.search_stats.growth_isotropy >= 0.75);
assert.equal(finished.search_stats.branch_choices_visited, 0);
assert.equal(finished.search_stats.backtracks, 0);
assert.equal(finished.search_stats.marking_observed_failures, 0, "custom polyhedron runs standalone without an injected plugin");

assert.throws(
  () => tileSpecs.buildLatticePolyhedronTile("Flat", [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]),
  /non-coplanar/
);
assert.throws(
  () => tileSpecs.buildLatticePolyhedronTile("Off lattice", [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0.5]]),
  /integer lattice/
);
assert.doesNotThrow(() => tileSpecs.buildLatticePolyhedronTile(
  "Explicit tetrahedron",
  [[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]],
  [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]
));
assert.throws(
  () => tileSpecs.buildLatticePolyhedronTile(
    "Open shell",
    latticeCube.vertices,
    [[0, 2, 3, 1]]
  ),
  /closed convex shell/
);
assert.throws(
  () => tileSpecs.buildLatticePolyhedronTile(
    "Bent face",
    latticeCube.vertices,
    [[0, 1, 6, 2], [0, 4, 5, 1], [2, 6, 4, 0], [1, 5, 7, 3], [2, 3, 7, 6], [4, 6, 7, 5]]
  ),
  /not planar/
);

console.log("3D custom lattice-polyhedron regression passed", {
  name: latticeCube.name,
  tiles: finished.tile_count,
  spans: finished.search_stats.growth_spans,
  isotropy: finished.search_stats.growth_isotropy
});
