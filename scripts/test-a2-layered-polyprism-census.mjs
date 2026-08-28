import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  canonicalA2LayeredPolyprism,
  describeA2LayeredPolyprism,
  enumerateA2LayeredPolyprisms,
  makeA2LayeredPolyprism
} from "../assets/a2-layered-polyprisms.js";
import { preprocessTilingSystem, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { A2_LAYERED_SIZE7_CANDIDATES } from "../assets/a2-layered-size7-candidates.js";
import { A2_LAYERED_SIZE8_CANDIDATES } from "../assets/a2-layered-size8-candidates.js";
import { A2_LAYERED_SIZE9_CANDIDATES } from "../assets/a2-layered-size9-candidates.js";

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
assert.equal(changingThree.four_layer_essential, false);
assert.equal(changingThree.layer_coupled, true);
assert.equal(changingThree.layer_equation, "x+y+z=3k");
assert.equal(changingThree.transverse_profile_asymmetric, false);
assert.deepEqual(changingThree.layer_profile, [1, 2, 1]);
assert.equal(changingThree.cross_section_changes, 2);
assert.equal(enumerateA2LayeredPolyprisms({ size: 4, layerEssentialOnly: true }).length, 5);
const fourLayerSizeEight = enumerateA2LayeredPolyprisms({
  size: 8,
  layerEssentialOnly: true,
  minLayerCount: 4,
  minDistinctCrossSections: 3,
  minCrossSectionChanges: 2
});
assert.equal(fourLayerSizeEight.length, 2137);
assert.ok(fourLayerSizeEight.every(candidate =>
  candidate.morphology.four_layer_essential
  && candidate.morphology.layer_coupled
));
const transverseAsymmetricSizeEight = enumerateA2LayeredPolyprisms({
  size: 8,
  layerEssentialOnly: true,
  minLayerCount: 4,
  minDistinctCrossSections: 3,
  minCrossSectionChanges: 2,
  requireTransverseProfileAsymmetry: true
});
assert.ok(transverseAsymmetricSizeEight.length > 0);
assert.ok(transverseAsymmetricSizeEight.length < fourLayerSizeEight.length);
assert.ok(transverseAsymmetricSizeEight.every(candidate =>
  candidate.morphology.transverse_profile_asymmetric));
const fullyChangingSizeEight = enumerateA2LayeredPolyprisms({
  size: 8,
  layerEssentialOnly: true,
  minLayerCount: 4,
  requireTransverseProfileAsymmetry: true,
  requireAllCrossSectionsDistinct: true
});
assert.ok(fullyChangingSizeEight.length > 0);
assert.ok(fullyChangingSizeEight.every(candidate =>
  candidate.morphology.distinct_cross_sections === candidate.morphology.layer_count));

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
const expectedFourCopyTypes = {
  a2lp_8_02131: 62134,
  a2lp_8_02151: 1105225,
  a2lp_8_03411: 1105225,
  a2lp_8_04836: 62134
};
for (const candidate of A2_LAYERED_SIZE8_CANDIDATES) {
  assert.equal(candidate.morphology.layer_essential, true);
  assert.ok(candidate.morphology.layer_count >= 3);
  assert.ok(candidate.morphology.distinct_cross_sections >= 3);
  assert.equal(candidate.screening.periodic_exact_through, 7);
  assert.equal(candidate.screening.periodic_solver_unknowns, 0);
  assert.equal(candidate.screening.periodic_hnf_bases_exhausted_by_copies[7], 1995);
  assert.equal(candidate.screening.periodic_seven_copy_complete, true);
  assert.ok(candidate.screening.periodic_seven_copy_exact_multicover_nodes > 0);
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
  assert.deepEqual(candidate.screening.four_copy_metatile_substitution_scales_exhausted,
    [2]);
  assert.equal(candidate.screening.four_copy_metatile_types_exhausted_by_scale[2],
    expectedFourCopyTypes[candidate.id]);
  const catalogue = preprocessTilingSystem({
    mode_key: candidate.registry_id,
    include_mirrors: false
  }, tileSpecs);
  assert.equal(catalogue.prototiles[0].geometry_model, "lattice_function");
  assert.ok(catalogue.prototiles[0].unique_orientations.length > 0);
  assert.ok(catalogue.prototiles[0].unique_orientations.length <= 6);
}

assert.deepEqual(A2_LAYERED_SIZE9_CANDIDATES.map(candidate => candidate.id), [
  "a2lp_9_00000", "a2lp_9_00002", "a2lp_9_00003", "a2lp_9_00010"
]);
const expectedSizeNineThreeCopyTypes = {
  a2lp_9_00000: 11811,
  a2lp_9_00002: 12502,
  a2lp_9_00003: 14254,
  a2lp_9_00010: 16710
};
for (const candidate of A2_LAYERED_SIZE9_CANDIDATES) {
  assert.equal(candidate.morphology.layer_count, 5);
  assert.equal(candidate.morphology.distinct_cross_sections, 5);
  assert.equal(candidate.morphology.transverse_profile_asymmetric, true);
  assert.equal(candidate.screening.periodic_exact_through, 6);
  assert.equal(candidate.screening.periodic_six_copy_orbit_representatives_visited, 233);
  assert.equal(candidate.screening.periodic_six_copy_hnf_covered, 1210);
  assert.equal(candidate.screening.periodic_six_copy_complete, true);
  assert.equal(candidate.screening.corona_completed_verified, true);
  assert.equal(candidate.screening.direct_layer_scale_pairs_exhausted, 49);
  assert.deepEqual(candidate.screening.two_copy_metatile_substitution_scales_exhausted, [2, 3]);
  assert.deepEqual(candidate.screening.three_copy_metatile_substitution_scales_exhausted, [2, 3]);
  assert.equal(candidate.screening.three_copy_metatile_types_exhausted_by_scale[2],
    expectedSizeNineThreeCopyTypes[candidate.id]);
  assert.equal(candidate.screening.three_copy_metatile_types_exhausted_by_scale[3],
    expectedSizeNineThreeCopyTypes[candidate.id]);
  assert.ok(candidate.screening.corona2_gcts_sound_clauses > 0);
}
const sizeNineExactTwo = (await readFile(new URL(
  "../data/a2-layered-size9-directed-periodic-exact2.ndjson", import.meta.url
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
assert.equal(sizeNineExactTwo.length, 724);
assert.equal(sizeNineExactTwo.filter(record => record.classification === "periodic").length, 430);
assert.equal(sizeNineExactTwo.filter(record => record.classification === "unresolved").length, 294);
assert.ok(sizeNineExactTwo.every(record => record.periodic_z3.solver_unknown === 0));
assert.ok(sizeNineExactTwo
  .filter(record => record.classification === "periodic")
  .every(record => record.periodic_z3.replay?.verified));
assert.ok(sizeNineExactTwo
  .filter(record => record.classification === "unresolved")
  .every(record => record.periodic_z3.hnf_range_exhausted));
const sizeNineExactSix = (await readFile(new URL(
  "../data/a2-layered-size9-directed-periodic-exact6.ndjson", import.meta.url
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
assert.equal(sizeNineExactSix.length, 4);
assert.ok(sizeNineExactSix.every(record =>
  record.periodic_z3.hnf_range_exhausted
  && record.periodic_z3.hnf_visited === 233
  && record.periodic_z3.hnf_covered === 1210
  && record.periodic_z3.solver_unknown === 0));
const sizeNineDirectSubstitutions = (await readFile(new URL(
  "../data/a2-layered-size9-directed-substitution-direct-s2to8.ndjson", import.meta.url
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
assert.equal(sizeNineDirectSubstitutions.length, 196);
assert.ok(sizeNineDirectSubstitutions.every(record => record.substitution.certified));
const sizeNineTwoCopySubstitutions = (await readFile(new URL(
  "../data/a2-layered-size9-directed-substitution-two-copy-s2to3.ndjson", import.meta.url
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
assert.equal(sizeNineTwoCopySubstitutions.length, 8);
assert.ok(sizeNineTwoCopySubstitutions.every(record =>
  record.two_copy_metatile_screen.certified
  && record.two_copy_metatile_screen.unknown_metatile_indices.length === 0));
let sizeNineThreeCopyParentScaleCases = 0;
let sizeNineThreeCopyExactUnsat = 0;
for (const candidate of A2_LAYERED_SIZE9_CANDIDATES) for (const scale of [2, 3]) {
  const report = JSON.parse((await readFile(new URL(
    `../data/a2-layered-size9-three-cluster-substitution-scalar${scale}-${candidate.id}.ndjson`,
    import.meta.url
  ), "utf8")).trim());
  const screen = report.three_copy_metatile_screen;
  assert.equal(report.classification, `no_three_copy_metatile_scalar${scale}_substitution`);
  assert.equal(screen.certified, true);
  assert.equal(screen.parents_completed, expectedSizeNineThreeCopyTypes[candidate.id]);
  assert.equal(screen.parent_counts.unresolved, 0);
  assert.equal(screen.parent_counts.mixed_metatile_rule, 0);
  assert.ok(screen.parent_results.every(parent =>
    parent.classification === "local_obstruction"
      ? parent.local_obstruction_replay?.verified === true
      : parent.classification === "exact_unsat"
        && parent.primary_exact_result === "unsat"
        && (parent.algorithm_x_replay?.verified === true
          || parent.exact_unsat_replay?.verified === true)
  ));
  sizeNineThreeCopyParentScaleCases += screen.parents_completed;
  sizeNineThreeCopyExactUnsat += screen.parent_counts.exact_unsat;
}
assert.equal(sizeNineThreeCopyParentScaleCases, 110554);
assert.equal(sizeNineThreeCopyExactUnsat, 5);


console.log("A2 layered-polyprism census regression passed", {
  counts: expected,
  first_nonproduct_count: sizeThree.length,
  point_group_order: prepared.summary.point_group_order,
  size8_layer_essential_survivors: A2_LAYERED_SIZE8_CANDIDATES.length
});
