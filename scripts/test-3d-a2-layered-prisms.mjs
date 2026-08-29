import assert from "node:assert/strict";
import { A2_LAYERED_PRISM_SPECS, makeA2LayeredPrism } from "../assets/a2-layered-prisms.js";
import { A2_SLICED_SIZE7_CANDIDATES } from "../assets/a2-sliced-size7-candidates.js";
import { makeA2SlicedAlcoveUnion } from "../assets/a2-sliced-alcoves.js";
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

assert.equal(A2_SLICED_SIZE7_CANDIDATES.length, 8);
assert.deepEqual(A2_SLICED_SIZE7_CANDIDATES.map(candidate => candidate.survivor_priority),
  [1, 2, 3, 4, 5, 6, 7, 8]);
for (const candidate of A2_SLICED_SIZE7_CANDIDATES) {
  assert.equal(candidate.kind, "a2_sliced_alcove_census");
  assert.equal(candidate.morphology.polycube, false);
  assert.equal(candidate.morphology.layer_equation, "x+y+z=k");
  assert.equal(candidate.screening.periodic_exact_through, 6);
  assert.equal(candidate.screening.periodic_solver_unknowns, 0);
  assert.equal(candidate.screening.retained_corona_extension_stopped_by, "solver_timeout");
  assert.equal(candidate.screening.corona_completed_radius, 2);
  assert.equal(candidate.screening.corona_completed_verified, true);
  assert.ok(candidate.screening.radius_two_patch_copies >= 190);
  assert.equal(candidate.screening.radius_three_status, "unresolved");
  assert.equal(candidate.screening.radius_three_report,
    "data/a2-sliced-alcove-size7-leads-radius2-radius3-gcts.ndjson.gz");
  const geometry = makeA2SlicedAlcoveUnion(candidate.alcoves);
  assert.deepEqual(geometry.layer_sums,
    Array.from({ length: candidate.morphology.layer_count }, (_, index) => index));
  assert.equal(geometry.geometry_model, "lattice_function");
  assert.equal(geometry.lattice_symmetry, "a2_layers");
  const prepared = preprocessTilingSystem({
    mode_key: candidate.registry_id,
    include_mirrors: false
  }, tileSpecs);
  assert.equal(prepared.prototiles.length, 1);
  assert.equal(prepared.prototiles[0].is_polycube, false);
  assert.equal(prepared.summary.point_group_order, 6);
}

const scale3ParentTypes = new Map([
  ["a2sa_7_00120", 1265], ["a2sa_7_00139", 1268], ["a2sa_7_00170", 2033],
  ["a2sa_7_00569", 1429], ["a2sa_7_00626", 1388], ["a2sa_7_00674", 1291],
  ["a2sa_7_00699", 2229], ["a2sa_7_00822", 1922]
]);
const scale2FourCopyParentTypes = new Map([
  ["a2sa_7_00120", 65110], ["a2sa_7_00139", 65349], ["a2sa_7_00569", 77830],
  ["a2sa_7_00626", 74215], ["a2sa_7_00674", 66674]
]);
for (const candidate of A2_SLICED_SIZE7_CANDIDATES) {
  assert.deepEqual(candidate.screening.three_copy_metatile_substitution_scales_exhausted,
    [2, 3, 4]);
  assert.equal(candidate.screening.three_copy_metatile_scale3_reflected_status,
    "no_three_copy_metatile_scalar3_substitution");
  assert.equal(candidate.screening.three_copy_metatile_scale3_reflected_parent_types,
    scale3ParentTypes.get(candidate.id));
  assert.equal(candidate.screening.three_copy_metatile_scale4_reflected_status,
    "no_three_copy_metatile_scalar4_substitution");
  assert.equal(candidate.screening.three_copy_metatile_scale4_reflected_parent_types,
    scale3ParentTypes.get(candidate.id));
  if (scale2FourCopyParentTypes.has(candidate.id)) {
    assert.deepEqual(candidate.screening.four_copy_metatile_substitution_scales_exhausted,
      [2]);
    assert.equal(candidate.screening.four_copy_metatile_scale2_reflected_status,
      "no_four_copy_metatile_scalar2_substitution");
    assert.equal(candidate.screening.four_copy_metatile_scale2_reflected_parent_types,
      scale2FourCopyParentTypes.get(candidate.id));
  } else {
    assert.deepEqual(candidate.screening.four_copy_metatile_substitution_scales_exhausted, []);
    assert.equal(candidate.screening.four_copy_metatile_scale2_reflected_status, "unresolved");
  }
}

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
  consecutive_layer_candidates: A2_SLICED_SIZE7_CANDIDATES.length,
  point_group_order: hatDirect.summary.point_group_order,
  periodic_control_tiles: finished.tile_count
});
