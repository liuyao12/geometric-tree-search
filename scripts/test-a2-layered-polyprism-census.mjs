import assert from "node:assert/strict";
import {
  A2_LAYERED_POLYPRISM_CANDIDATES,
  canonicalA2LayeredPolyprism,
  enumerateA2LayeredPolyprisms,
  makeA2LayeredPolyprism
} from "../assets/a2-layered-polyprisms.js";
import { preprocessTilingSystem, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

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

const catalogueCandidate = preprocessTilingSystem({
  mode_key: A2_LAYERED_POLYPRISM_CANDIDATES[0].registry_id,
  include_mirrors: false
}, tileSpecs);
assert.equal(catalogueCandidate.prototiles[0].name, A2_LAYERED_POLYPRISM_CANDIDATES[0].name);
assert.equal(catalogueCandidate.prototiles[0].unique_orientations.length, 6);

console.log("A2 layered-polyprism census regression passed", {
  counts: expected,
  first_nonproduct_count: sizeThree.length,
  point_group_order: prepared.summary.point_group_order
});
