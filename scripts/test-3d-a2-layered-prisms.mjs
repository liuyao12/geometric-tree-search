import assert from "node:assert/strict";
import { A2_LAYERED_PRISM_SPECS, makeA2LayeredPrism } from "../assets/a2-layered-prisms.js";
import { createTilingStream, preprocessTilingSystem, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

for (const spec of A2_LAYERED_PRISM_SPECS) {
  const data = makeA2LayeredPrism(spec.loop, { geometryModel: spec.geometry_model });
  assert.deepEqual(
    [...new Set(data.v.map(vertex => vertex.reduce((sum, value) => sum + value, 0)))].sort((a, b) => a - b),
    [0, 3]
  );
  assert.ok(data.occ.length > data.v.length);
  assert.ok(data.occ.every(([point, weight]) =>
    point.every(Number.isInteger) && Number.isInteger(weight) && weight > 0 && weight <= 24
  ));
  const prepared = preprocessTilingSystem({ mode_key: spec.id, include_mirrors: false }, tileSpecs);
  assert.equal(prepared.summary.point_group_order, 6);
  assert.equal(prepared.summary.point_group, "proper cubic rotations preserving x+y+z=constant layers");
  assert.equal(prepared.prototiles[0].lattice_symmetry, "a2_layers");
}

const hatDirect = preprocessTilingSystem({ mode_key: "a2_hat_prism", include_mirrors: false }, tileSpecs);
assert.equal(hatDirect.prototiles.length, 1);
assert.equal(hatDirect.prototiles[0].unique_orientations.length, 6);
assert.equal(hatDirect.prototiles[0].is_convex_polyhedron, false);

const hatWithReflections = preprocessTilingSystem({ mode_key: "a2_hat_prism", include_mirrors: true }, tileSpecs);
assert.equal(hatWithReflections.prototiles.length, 2);
assert.deepEqual(hatWithReflections.prototiles.map(tile => tile.unique_orientations.length), [6, 6]);

const config = {
  mode_key: "a2_hexagonal_prism",
  criterion: "count",
  target_val: 24,
  tiling_strategy: "translational",
  include_mirrors: false,
  template_preflight: true,
  periodic_tile_count: 2,
  periodic_stop_at_growth_goal: true,
  exhaustive: false,
  node_limit: 10000,
  time_limit_ms: 10000,
  snapshot_every: 0,
  ui_yield_interval_ms: 1000,
  placement_details: true
};
let finished = null;
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  if (message.type === "finished") finished = message;
}
assert.equal(finished?.success, true);
assert.equal(finished?.tile_count, 24);
assert.equal(finished?.can_tile, true);
assert.equal(finished?.tiling_evidence?.certificate_kind, "one_tile_translational_lattice_polyhedron");

console.log("A2 layered-prism regression passed", {
  catalogue_entries: A2_LAYERED_PRISM_SPECS.length,
  point_group_order: hatDirect.summary.point_group_order,
  periodic_control_tiles: finished.tile_count
});
