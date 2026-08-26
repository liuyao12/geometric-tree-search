import assert from "node:assert/strict";
import { generateAmorphousMixture } from "../apps/iqc-growth-live/amorphous-glass.js";
import {
  besselJ0,
  powderStructureFactor,
  summarizeStructureFactor,
  weightedPowderStructureFactor,
} from "../apps/iqc-growth-live/structure-observables.js";

function pairDistances(positions, spacing = 1) {
  const distances = [];
  for (let first = 0; first < positions.length; first++) {
    for (let second = first + 1; second < positions.length; second++) {
      distances.push(Math.hypot(...positions[second].map((value, axis) =>
        (value - positions[first][axis]) / spacing)));
    }
  }
  return distances;
}

assert.equal(besselJ0(0), 1);
assert.ok(Math.abs(besselJ0(2.4048255577)) < 2e-8, "2D kernel must reproduce the first J0 zero");
assert.ok(Math.abs(besselJ0(10) + .2459357645) < 2e-7);

const glass = generateAmorphousMixture();
const glassSq = powderStructureFactor(pairDistances(glass.positions, 2.72), glass.positions.length, 3);
const glassSummary = summarizeStructureFactor(glassSq);
assert.equal(glassSq.values.length, 48);
assert.ok(glassSq.values.every((value) => Number.isFinite(value) && value >= 0));
assert.ok(Math.abs(glassSummary.highQMean - 1) < .04,
  `hard-core glass should approach unit incoherent baseline at high q, got ${glassSummary.highQMean}`);
assert.ok(glassSummary.peakProminence < 1.5, "amorphous powder peak should remain broad and modest");

const cubic = [];
for (let x = 0; x < 6; x++) for (let y = 0; y < 6; y++) for (let z = 0; z < 6; z++) cubic.push([x, y, z]);
const cubicSq = powderStructureFactor(pairDistances(cubic), cubic.length, 3);
const cubicSummary = summarizeStructureFactor(cubicSq);
assert.ok(cubicSummary.peakHeight > 2 * glassSummary.peakHeight,
  "periodic order should have a substantially sharper powder peak than the glass control");

const cubicDistances = pairDistances(cubic);
const unitWeightedCubic = weightedPowderStructureFactor(cubicDistances.map((distance) => ({
  distance, weightProduct: 1,
})), cubic.length, 3);
assert.ok(unitWeightedCubic.values.every((value, index) => Math.abs(value - cubicSq.values[index]) < 1e-12),
  "all-unit weighted Debye scattering must reproduce the established geometric S(q)");
const rescaledWeightedCubic = weightedPowderStructureFactor(cubicDistances.map((distance) => ({
  distance, weightProduct: 49,
})), cubic.length * 49, 3);
assert.ok(rescaledWeightedCubic.values.every((value, index) =>
  Math.abs(value - unitWeightedCubic.values[index]) < 1e-12),
  "a common scattering-weight rescaling must cancel under squared-self normalization");
const binaryLinePositions = [[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]];
const binaryWeights = [1, -1, 1, -1];
const binaryTerms = [];
for (let first = 0; first < binaryLinePositions.length; first++) {
  for (let second = first + 1; second < binaryLinePositions.length; second++) binaryTerms.push({
    distance: second - first,
    weightProduct: binaryWeights[first] * binaryWeights[second],
  });
}
const chemicalContrast = weightedPowderStructureFactor(binaryTerms, 4, 3);
assert.ok(chemicalContrast.values.every((value) => Number.isFinite(value) && value >= 0));
assert.ok(chemicalContrast.values.some((value, index) =>
  Math.abs(value - powderStructureFactor(pairDistances(binaryLinePositions), 4, 3).values[index]) > .1),
"composition-centered signed weights must expose chemical ordering hidden by unit density contrast");

const planarHexagonal = [];
for (let i = -7; i <= 7; i++) for (let j = -7; j <= 7; j++) {
  const point = [i + .5 * j, Math.sqrt(3) / 2 * j, 0];
  if (Math.hypot(point[0], point[1]) < 7) planarHexagonal.push(point);
}
const planarSq = powderStructureFactor(pairDistances(planarHexagonal), planarHexagonal.length, 2);
assert.equal(planarSq.dimension, 2);
assert.ok(summarizeStructureFactor(planarSq).peakHeight > 5,
  "the J0 powder average must retain strong reciprocal order in a 2D hexagonal patch");

const reversedSq = powderStructureFactor(pairDistances(glass.positions.slice().reverse(), 2.72), glass.positions.length, 3);
assert.ok(reversedSq.values.every((value, index) => Math.abs(value - glassSq.values[index]) < 1e-12),
  "S(q) must be invariant to atom ordering up to floating-point summation order");

console.log("dimension-aware geometric powder structure factor: passed", {
  glassPeak: glassSummary.peakHeight.toFixed(3),
  glassHighQ: glassSummary.highQMean.toFixed(3),
  crystalPeak: cubicSummary.peakHeight.toFixed(3),
});
