import assert from "node:assert/strict";
import {
  discoverFiniteMolecularComponents,
  discoverMolecularConnectionTopology,
} from "../apps/iqc-growth-live/molecular-components.js";

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
assert.equal(water.componentCount, 4);
assert.equal(water.largestComponent, 3);
assert.equal(water.covalentEdges, 8);
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

const noisyWaterPositions = Array.from({ length: 4 }, (_, molecule) => {
  const scale = molecule < 2 ? .995 : 1.005;
  const origin = 4 * molecule;
  return [[origin, 0, 0], [origin + .758 * scale, .586 * scale, 0], [origin - .758 * scale, .586 * scale, 0]];
}).flat();
const strictNoisyWater = discoverFiniteMolecularComponents({
  species: waterSpecies,
  distance: euclidean(noisyWaterPositions),
  descriptorToleranceA: .01,
});
const thermalNoisyWater = discoverFiniteMolecularComponents({
  species: waterSpecies,
  distance: euclidean(noisyWaterPositions),
  descriptorToleranceA: .05,
});
assert.equal(strictNoisyWater.accepted, true);
assert.equal(strictNoisyWater.types.length, 2);
assert.equal(thermalNoisyWater.accepted, true);
assert.equal(thermalNoisyWater.types.length, 1);

const chainPositions = Array.from({ length: 8 }, (_, index) => [1.4 * index, 0, 0]);
const chain = discoverFiniteMolecularComponents({
  species: Array(8).fill("C"),
  distance: euclidean(chainPositions),
});
assert.equal(chain.accepted, false);
assert.equal(chain.reason, "extended covalent network");
assert.equal(chain.componentCount, 1);
assert.equal(chain.largestComponent, 8);

const ionic = discoverFiniteMolecularComponents({
  species: ["Na", "Cl", "Na", "Cl"],
  distance: euclidean([[0, 0, 0], [2.8, 0, 0], [0, 2.8, 0], [2.8, 2.8, 0]]),
});
assert.equal(ionic.accepted, false);
assert.equal(ionic.reason, "unsupported chemistry metadata");
assert.deepEqual(ionic.unsupported, ["Na"]);
assert.equal(ionic.materialLabelUsed, false);

const co2Centers = [[0, 0, 0], [5, 0, 0], [5, 5, 0], [0, 5, 0]];
const co2Positions = co2Centers.flatMap(([x, y, z]) => [[x, y, z], [x, y, z - 1.16], [x, y, z + 1.16]]);
const co2Species = co2Centers.flatMap(() => ["C", "O", "O"]);
const co2 = discoverFiniteMolecularComponents({ species: co2Species, distance: euclidean(co2Positions) });
assert.equal(co2.accepted, true);
assert.deepEqual(co2.types[0].formula, [["C", 1], ["O", 2]]);
const co2Topology = discoverMolecularConnectionTopology({
  discovery: co2,
  species: co2Species,
  distance: euclidean(co2Positions),
});
assert.equal(co2Topology.componentGraphConnected, true);
assert.equal(co2Topology.connections.length, 4);
assert.equal(co2Topology.connectionTypeCount, 1);
assert.equal(co2Topology.voids.length, 1);
assert.equal(co2Topology.voids[0].components.length, 4);
assert.equal(co2Topology.voidTypeCount, 1);
assert.equal(co2Topology.expectedRingSizeUsed, false);

console.log("generic finite molecular component discovery: passed", {
  formula: water.types[0].formula,
  occurrences: water.types[0].occurrences.length,
  chainFallback: chain.reason,
  co2Topology: [co2Topology.connections.length, co2Topology.voids.length],
  noisyToleranceTypes: [strictNoisyWater.types.length, thermalNoisyWater.types.length],
});
