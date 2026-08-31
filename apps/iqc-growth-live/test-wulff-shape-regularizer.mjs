import assert from "node:assert/strict";
import {
  cartesianNormalToIntrinsic,
  evaluateWulffShapeRegularizer,
  matchedWulffRankingAudit,
  orientedEnergyKernelEstimate,
} from "./wulff-shape-regularizer.mjs";

const square = [
  { orientationId: "+x", normal: [1, 0], interfacialFreeEnergy: 1, uncertainty: .02 },
  { orientationId: "-x", normal: [-1, 0], interfacialFreeEnergy: 1, uncertainty: .02 },
  { orientationId: "+y", normal: [0, 1], interfacialFreeEnergy: 1, uncertainty: .02 },
  { orientationId: "-y", normal: [0, -1], interfacialFreeEnergy: 1, uncertainty: .02 },
];

const exact = orientedEnergyKernelEstimate(square, [1, 0], Math.PI / 6);
assert.equal(exact.supported, true);
assert.equal(exact.interfacialFreeEnergy, 1);
assert.equal(exact.nearestAngleRadians, 0);

const polar = square.map((entry) => entry.orientationId === "-x"
  ? { ...entry, interfacialFreeEnergy: 2 } : entry);
assert.equal(orientedEnergyKernelEstimate(polar, [1, 0], Math.PI / 6).interfacialFreeEnergy, 1);
assert.equal(orientedEnergyKernelEstimate(polar, [-1, 0], Math.PI / 6).interfacialFreeEnergy, 2);
assert.equal(orientedEnergyKernelEstimate(polar, [0, 0.5], Math.PI / 18).supported, true);
assert.equal(orientedEnergyKernelEstimate(square, [Math.SQRT1_2, Math.SQRT1_2], Math.PI / 12).supported, false);

const occupied = [[-.8, -1.2, 0], [.8, -1.2, 0], [.8, 1.2, 0], [-.8, 1.2, 0]];
const improved = evaluateWulffShapeRegularizer({
  occupiedPositions: occupied, emittedPositions: [[1, 0, 0]],
  orientationBasisCartesian: [[1, 0, 0], [0, 1, 0]], orientations: square,
  maximumAngleRadians: Math.PI / 6,
});
assert.equal(improved.supported, true);
assert.ok(improved.score > 0);
assert.ok(improved.mismatchAfter < improved.mismatchBefore);

const worsened = evaluateWulffShapeRegularizer({
  occupiedPositions: [[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]],
  emittedPositions: [[1.5, 0, 0]], orientationBasisCartesian: [[1, 0, 0], [0, 1, 0]],
  orientations: square, maximumAngleRadians: Math.PI / 6,
});
assert.equal(worsened.supported, true);
assert.ok(worsened.score < 0);

const rotated = evaluateWulffShapeRegularizer({
  occupiedPositions: occupied.map(([x, y]) => [-y, x, 0]), emittedPositions: [[0, 1, 0]],
  orientationBasisCartesian: [[0, 1, 0], [-1, 0, 0]], orientations: square,
  maximumAngleRadians: Math.PI / 6,
});
assert.ok(Math.abs(rotated.score - improved.score) < 1e-12);
assert.deepEqual(cartesianNormalToIntrinsic([0, 1, 0], [[0, 1, 0], [-1, 0, 0]]), [1, 0]);

const unsupported = evaluateWulffShapeRegularizer({
  occupiedPositions: occupied, emittedPositions: [[1, 1, 0]],
  orientationBasisCartesian: [[1, 0, 0], [0, 1, 0]], orientations: square,
  maximumAngleRadians: Math.PI / 12,
});
assert.equal(unsupported.supported, false);
assert.equal(unsupported.score, 0);

const audit = matchedWulffRankingAudit([
  { candidateId: "a", baselineScore: 3, regularizedScore: 1, supported: true },
  { candidateId: "b", baselineScore: 2, regularizedScore: 3, supported: true },
  { candidateId: "c", baselineScore: 1, regularizedScore: 2, supported: false },
]);
assert.equal(audit.candidateSetIdentical, true);
assert.equal(audit.rankInversions, 2);
assert.equal(audit.leaderChanged, true);
assert.equal(audit.supportedCandidates, 2);

console.log("wulff-shape-regularizer tests passed");
