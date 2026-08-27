import assert from "node:assert/strict";
import {
  canonicalA2LayeredPolyprism,
  enumerateA2LayeredPolyprisms,
  makeA2LayeredPolyprism
} from "../assets/a2-layered-polyprisms.js";
import { preprocessTilingSystem, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { A2_LAYERED_SIZE7_CANDIDATES } from "../assets/a2-layered-size7-candidates.js";

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
}


console.log("A2 layered-polyprism census regression passed", {
  counts: expected,
  first_nonproduct_count: sizeThree.length,
  point_group_order: prepared.summary.point_group_order
});
