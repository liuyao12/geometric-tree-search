import assert from "node:assert/strict";
import {
  canonicalA2LayeredPolyprism,
  describeA2LayeredPolyprism,
  enumerateA2LayeredPolyprisms,
  makeA2LayeredPolyprism
} from "../assets/a2-layered-polyprisms.js";
import { preprocessTilingSystem, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { A2_LAYERED_SIZE7_CANDIDATES } from "../assets/a2-layered-size7-candidates.js";
import { A2_LAYERED_SIZE8_CANDIDATES } from "../assets/a2-layered-size8-candidates.js";

const expected = [1, 2, 4, 15, 50, 237];
for (let size = 1; size <= expected.length; size += 1) {
  const census = enumerateA2LayeredPolyprisms({ size, includeProduct: true });
  assert.equal(census.length, expected[size - 1], `size-${size} fixed-lattice census`);
  assert.equal(new Set(census.map(candidate => candidate.key)).size, census.length);
}

const sizeThree = enumerateA2LayeredPolyprisms({ size: 3 });
assert.equal(sizeThree.length, 2, "the first non-product census should have two shapes");
const shifted = sizeThree[0].cells.map(cell => ({ ...cell, q: cell.q + 7, r: cell.r - 4, k: cell.k + 3 }));
assert.equal(
  canonicalA2LayeredPolyprism(shifted).key,
  canonicalA2LayeredPolyprism(sizeThree[0].cells).key,
  "canonicalization must remove translations"
);
const verticalThree = describeA2LayeredPolyprism([
  { q: 0, r: 0, k: 0, kind: "u" },
  { q: 0, r: 0, k: 1, kind: "u" },
  { q: 0, r: 0, k: 2, kind: "u" }
]);
assert.equal(verticalThree.product_prism, true);
assert.equal(verticalThree.layer_essential, false);
assert.deepEqual(verticalThree.layer_profile, [1, 1, 1]);
const changingThree = describeA2LayeredPolyprism([
  { q: 0, r: 0, k: 0, kind: "u" },
  { q: 0, r: 0, k: 1, kind: "u" },
  { q: 0, r: 0, k: 1, kind: "d" },
  { q: 0, r: 0, k: 2, kind: "u" }
]);
assert.equal(changingThree.layer_essential, true);
assert.deepEqual(changingThree.layer_profile, [1, 2, 1]);
assert.equal(changingThree.cross_section_changes, 2);
assert.equal(enumerateA2LayeredPolyprisms({ size: 4, layerEssentialOnly: true }).length, 5);

for (const candidate of sizeThree) {
  const data = makeA2LayeredPolyprism(candidate.cells);
  assert.equal(data.geometry_model, "lattice_function");
  assert.equal(data.lattice_symmetry, "a2_layers");
  assert.ok(data.occ.every(([point, weight]) =>
    point.every(Number.isInteger) && Number.isInteger(weight) && weight > 0 && weight <= 48
  ));
}

const prepared = preprocessTilingSystem({
  mode_key: "cube",
  include_mirrors: false,
  custom_system: {
    name: "A2 layered census probe",
    a2_layered_polyprisms: [{ name: "A2-3-0", cells: sizeThree[0].cells }]
  }
}, tileSpecs);
assert.equal(prepared.summary.point_group_order, 6);
assert.equal(prepared.prototiles[0].geometry_model, "lattice_function");
assert.equal(prepared.prototiles[0].unique_orientations.length, 6);
assert.equal(prepared.prototiles[0].is_convex_polyhedron, false);

assert.equal(A2_LAYERED_SIZE7_CANDIDATES.length, 8);
const expectedEightCopyOrbits = {
  a2lp_7_00128: 12, a2lp_7_00211: 4, a2lp_7_00232: 4, a2lp_7_00235: 4,
  a2lp_7_00694: 1, a2lp_7_00755: 12, a2lp_7_00777: 12, a2lp_7_00809: 12
};
for (const candidate of A2_LAYERED_SIZE7_CANDIDATES) {
  const catalogue = preprocessTilingSystem({
    mode_key: candidate.registry_id,
    include_mirrors: false
  }, tileSpecs);
  assert.equal(catalogue.prototiles[0].name, candidate.name);
  assert.equal(catalogue.prototiles[0].unique_orientations.length, 6);
  assert.equal(candidate.screening.periodic_exact_through, 6);
  assert.equal(candidate.screening.periodic_six_copy_hnf_visited, 741);
  assert.equal(candidate.screening.periodic_six_copy_solver_unknowns, 0);
  assert.equal(candidate.screening.periodic_six_copy_complete, true);
  assert.ok(candidate.screening.periodic_six_copy_exact_multicover_nodes > 0);
  assert.equal(candidate.screening.corona2_outer_exhausted, false);
  assert.ok(Number.isInteger(candidate.screening.corona2_gcts_new_clauses_long_run));
  assert.ok(candidate.screening.corona2_gcts_new_clauses_long_run > 0);
  assert.equal(candidate.screening.periodic_eight_copy_orbits_checked,
    expectedEightCopyOrbits[candidate.id]);
  assert.equal(candidate.screening.periodic_eight_copy_solver_unknowns, 0);
}

assert.deepEqual(A2_LAYERED_SIZE8_CANDIDATES.map(candidate => candidate.id), [
  "a2lp_8_02131", "a2lp_8_02151", "a2lp_8_03411", "a2lp_8_04836"
]);
for (const candidate of A2_LAYERED_SIZE8_CANDIDATES) {
  assert.equal(candidate.morphology.layer_essential, true);
  assert.ok(candidate.morphology.layer_count >= 3);
  assert.ok(candidate.morphology.distinct_cross_sections >= 3);
  assert.equal(candidate.screening.periodic_exact_through, 6);
  assert.equal(candidate.screening.periodic_solver_unknowns, 0);
  assert.equal(candidate.screening.periodic_hnf_bases_exhausted_by_copies[6], 2015);
  assert.equal(candidate.screening.periodic_six_copy_complete, true);
  assert.ok(candidate.screening.periodic_six_copy_exact_multicover_nodes > 0);
  assert.equal(candidate.screening.corona_completed_radius, 1);
  assert.equal(candidate.screening.corona_completed_verified, true);
  assert.ok(candidate.screening.corona_root_patch_copies >= 24);
  assert.ok(candidate.screening.corona2_gcts_rounds >= 17);
  assert.ok(candidate.screening.corona2_gcts_sound_clauses >= 16);
  assert.equal(candidate.screening.corona2_gcts_outer_exhausted, false);
  assert.deepEqual(candidate.screening.direct_scalar_substitution_scales_exhausted,
    [2, 3, 4, 5, 6, 7, 8]);
  assert.equal(candidate.screening.direct_layer_scale_pairs_exhausted, 49);
  assert.deepEqual(candidate.screening.two_copy_metatile_substitution_scales_exhausted,
    [2, 3]);
  assert.deepEqual(candidate.screening.three_copy_metatile_substitution_scales_exhausted,
    [2, 3]);
  const catalogue = preprocessTilingSystem({
    mode_key: candidate.registry_id,
    include_mirrors: false
  }, tileSpecs);
  assert.equal(catalogue.prototiles[0].geometry_model, "lattice_function");
  assert.ok(catalogue.prototiles[0].unique_orientations.length > 0);
  assert.ok(catalogue.prototiles[0].unique_orientations.length <= 6);
}


console.log("A2 layered-polyprism census regression passed", {
  counts: expected,
  first_nonproduct_count: sizeThree.length,
  point_group_order: prepared.summary.point_group_order,
  size8_layer_essential_survivors: A2_LAYERED_SIZE8_CANDIDATES.length
});
