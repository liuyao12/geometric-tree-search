import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  a2SlicedAlcoveNeighbors,
  a2SlicedAlcoveVertices,
  canonicalA2SlicedAlcoves,
  enumerateA2SlicedAlcoves,
  makeA2SlicedAlcoveUnion
} from "../assets/a2-sliced-alcoves.js";
import { preprocessTilingSystem, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const seed = { base: [0, 0, 0], order: [0, 1, 2] };
assert.deepEqual(a2SlicedAlcoveVertices(seed).map(point => point.reduce((a, b) => a + b, 0)), [0, 1, 2, 3]);
assert.equal(a2SlicedAlcoveNeighbors(seed).length, 4);
for (const neighbor of a2SlicedAlcoveNeighbors(seed)) {
  const common = new Set(a2SlicedAlcoveVertices(seed).map(String));
  assert.equal(a2SlicedAlcoveVertices(neighbor).filter(point => common.has(String(point))).length, 3);
}

const shifted = { base: [7, -3, 11], order: [0, 1, 2] };
assert.equal(canonicalA2SlicedAlcoves([seed]).key, canonicalA2SlicedAlcoves([shifted]).key);

const expected = [1, 2, 7, 22, 83, 314];
for (let size = 1; size <= expected.length; size += 1) {
  const census = enumerateA2SlicedAlcoves({ size });
  assert.equal(census.length, expected[size - 1], `size-${size} alcove census`);
  assert.ok(census.every(candidate => candidate.morphology.layer_equation === "x+y+z=k"));
}

const single = makeA2SlicedAlcoveUnion([seed]);
assert.deepEqual(single.occ.map(entry => entry[1]).sort((a, b) => a - b), [1, 1, 3, 3]);
assert.deepEqual(single.layer_sums, [0, 1, 2, 3]);
assert.equal(single.geometry_model, "lattice_function");
assert.equal(single.lattice_symmetry, "a2_layers");
const pair = makeA2SlicedAlcoveUnion([seed, a2SlicedAlcoveNeighbors(seed)[2]]);
assert.equal(pair.f_data.length, 6, "the shared triangular face must be removed");
assert.ok(pair.occ.every(entry => Number.isInteger(entry[1]) && entry[1] > 0 && entry[1] <= 48));

const prepared = preprocessTilingSystem({
  mode_key: "cube",
  include_mirrors: false,
  custom_system: {
    name: "A2-sliced probe",
    a2_sliced_alcoves: [{ name: "alcove pair", alcoves: [seed, a2SlicedAlcoveNeighbors(seed)[2]] }]
  }
}, tileSpecs);
assert.equal(prepared.summary.point_group_order, 6);
assert.equal(prepared.prototiles[0].geometry_model, "lattice_function");
assert.equal(prepared.prototiles[0].is_polycube, false);
assert.ok(prepared.prototiles[0].unique_orientations.length > 1);

const readNdjson = async path => (await readFile(new URL(path, import.meta.url), "utf8"))
  .trim().split("\n").filter(Boolean).map(JSON.parse);
const sizeSix = await readNdjson("../data/a2-sliced-alcove-size6-directed-periodic-exact1.ndjson");
assert.equal(sizeSix.length, 222);
assert.ok(sizeSix.every(record =>
  record.classification === "periodic"
  && record.periodic_z3.certificate.certified
  && record.periodic_z3.certificate.copies === 1
  && record.periodic_z3.certificate.determinant === 1
  && record.periodic_z3.replay.verified
));
const sizeSeven = await readNdjson("../data/a2-sliced-alcove-size7-directed-periodic-exact6.ndjson");
assert.equal(sizeSeven.length, 1112);
assert.equal(sizeSeven.filter(record => record.classification === "periodic").length, 853);
assert.equal(sizeSeven.filter(record => record.classification === "unresolved").length, 259);
assert.ok(sizeSeven.filter(record => record.classification === "periodic").every(record =>
  record.periodic_z3.certificate.copies === 6
  && record.periodic_z3.certificate.determinant === 7
  && record.periodic_z3.replay.verified
));
assert.ok(sizeSeven.filter(record => record.classification === "unresolved").every(record =>
  record.periodic_z3.solver_unknown === 0
  && record.periodic_z3.hnf_covered === 57
  && record.periodic_z3.exhausted_by_copies[6] === 57
));
assert.equal(sizeSeven.reduce((sum, record) =>
  sum + record.periodic_z3.exact_multicover_nodes, 0), 206993651);

const coronas = await readNdjson("../data/a2-sliced-alcove-size7-directed-corona1.ndjson");
assert.equal(coronas.length, 259);
assert.equal(coronas.filter(record => record.corona_classification === "root_corona_exists").length, 255);
assert.deepEqual(coronas.filter(record => record.corona_classification === "unresolved")
  .map(record => record.id), [
    "a2sa_7_00147", "a2sa_7_00570", "a2sa_7_01108", "a2sa_7_01109"
  ]);
assert.ok(coronas.filter(record => record.corona_classification === "root_corona_exists")
  .every(record => record.corona_z3.replay.verified));
assert.ok(coronas.filter(record => record.corona_classification === "unresolved")
  .every(record =>
    record.corona_z3.stopped_by === "exact_gcts_node_limit"
    && record.corona_z3.exact_gcts.nodes === 100000
  ));

console.log("A2-sliced alcove census regression passed", { expected });
