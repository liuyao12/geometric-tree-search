import assert from "node:assert/strict";
import {
  extremeLatticePoints,
  parseBlancoSantosLatticePoints,
  parsePolyDbLatticePolytopes,
  POLYDB_FEW_LATTICE_POINTS_COUNTS,
  polyDbLatticePolytopeAggregateRequest
} from "../assets/lattice-polytope-census.js";

const cube = Array.from({ length: 8 }, (_, index) => [index & 1, index >> 1 & 1, index >> 2 & 1]);
assert.equal(extremeLatticePoints([...cube, [0, 0, 0], [0.5, 0.5, 0.5]]).length, 8);

const blanco = parseBlancoSantosLatticePoints(`
Polytope ID: 5_0
0 1 0 0 0
0 0 1 0 0
0 0 0 1 0
`);
assert.equal(blanco.length, 1);
assert.equal(blanco[0].lattice_points.length, 5);
assert.equal(blanco[0].vertices.length, 4);

const polyDb = parsePolyDbLatticePolytopes([{
  _id: "12_000042",
  N_LATTICE_POINTS: 12,
  VERTICES: [["1", "0", "0", "0"], ["1", "2", "0", "0"], ["1", "0", "2", "0"], ["1", "0", "0", "2"]]
}]);
assert.deepEqual(polyDb, [{
  id: "12_000042",
  lattice_points: 12,
  vertices: [[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]]
}]);
assert.throws(() => parsePolyDbLatticePolytopes([{
  _id: "bad",
  N_LATTICE_POINTS: 12,
  VERTICES: [["2", "0", "0", "0"]]
}]), /homogeneous/);

const request = polyDbLatticePolytopeAggregateRequest(12, -5, 999999);
assert.equal(request.start, 0);
assert.equal(request.end, POLYDB_FEW_LATTICE_POINTS_COUNTS[12]);
const query = JSON.parse(new URL(request.url).searchParams.get("query"));
assert.deepEqual(query[0].$match, {
  _id: { $gte: "12_000000", $lt: "12_503443" },
  N_LATTICE_POINTS: 12
});
assert.deepEqual(query.at(-1).$project, { _id: 1, VERTICES: 1, N_LATTICE_POINTS: 1 });

console.log("Lattice-polytope census adapters passed", {
  configuredSize12: POLYDB_FEW_LATTICE_POINTS_COUNTS[12],
  requestRange: [request.start, request.end]
});
