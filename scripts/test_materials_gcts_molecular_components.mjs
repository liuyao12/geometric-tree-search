import assert from "node:assert/strict";
import { discoverFiniteMolecularComponents } from "../apps/iqc-growth-live/molecular-components.js";

const euclidean = (positions) => (first, second) => Math.hypot(
  positions[first][0] - positions[second][0],
  positions[first][1] - positions[second][1],
  positions[first][2] - positions[second][2],
);

const waterPositions = [
  [0, 0, 0], [.758, .586, 0], [-.758, .586, 0],
  [4, 0, 0], [4.758, .586, 0], [3.242, .586, 0],
  [8, 0, 0], [8.758, .586, 0], [7.242, .586, 0],
  [12, 0, 0], [12.758, .586, 0], [11.242, .586, 0],
];
const waterSpecies = ["O", "H", "H", "O", "H", "H", "O", "H", "H", "O", "H", "H"];
const water = discoverFiniteMolecularComponents({
  species: waterSpecies,
  distance: euclidean(waterPositions),
});
assert.equal(water.accepted, true);
assert.equal(water.materialLabelUsed, false);
assert.equal(water.expectedFormulaUsed, false);
assert.equal(water.components.length, 4);
assert.equal(water.types.length, 1);
assert.deepEqual(water.types[0].formula, [["H", 2], ["O", 1]]);
assert.equal(water.types[0].occurrences.length, 4);
assert.equal(water.coveredAtoms, 12);

const permutation = Array.from({ length: waterSpecies.length }, (_, index) => waterSpecies.length - 1 - index);
const permutedPositions = permutation.map((index) => waterPositions[index]);
const permuted = discoverFiniteMolecularComponents({
  species: permutation.map((index) => waterSpecies[index]),
  distance: euclidean(permutedPositions),
});
assert.equal(permuted.accepted, true);
assert.deepEqual(permuted.types.map((type) => [type.formula, type.occurrences.length]),
  water.types.map((type) => [type.formula, type.occurrences.length]));

const chainPositions = Array.from({ length: 8 }, (_, index) => [1.4 * index, 0, 0]);
const chain = discoverFiniteMolecularComponents({
  species: Array(8).fill("C"),
  distance: euclidean(chainPositions),
});
assert.equal(chain.accepted, false);
assert.equal(chain.reason, "extended covalent network");

const ionic = discoverFiniteMolecularComponents({
  species: ["Na", "Cl", "Na", "Cl"],
  distance: euclidean([[0, 0, 0], [2.8, 0, 0], [0, 2.8, 0], [2.8, 2.8, 0]]),
});
assert.equal(ionic.accepted, false);
assert.equal(ionic.reason, "unsupported chemistry metadata");

console.log("generic finite molecular component discovery: passed", {
  formula: water.types[0].formula,
  occurrences: water.types[0].occurrences.length,
  chainFallback: chain.reason,
});

