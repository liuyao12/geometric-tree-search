import assert from "node:assert/strict";
import { learnLocalPairDistanceUncertaintyEnsemble } from "../apps/iqc-growth-live/ensemble-geometry-uncertainty.js";

const frame = (points) => ({
  species: ["O", "H", "H"],
  distance: (first, second) => Math.hypot(...points[first].map((value, axis) => value - points[second][axis])),
});

const reference = [[0, 0, 0], [1, 0, 0], [0, 1, 0]];
const rigid = reference.map(([x, y, z]) => [4 - y, -3 + x, 2 + z]);
const rigidModel = learnLocalPairDistanceUncertaintyEnsemble([frame(reference), frame(rigid)], { localCutoff: 1.5 });
assert.equal(rigidModel.available, true);
assert.ok(rigidModel.maximumPairDistanceSigma < 1e-12);
assert.equal(rigidModel.localPairCount, 3);

const onePairFrames = [1, 1.1, .9].map((distance) => ({
  species: ["Na", "Cl"],
  distance: () => distance,
}));
const deformed = learnLocalPairDistanceUncertaintyEnsemble(onePairFrames, { localCutoff: 1.2, upperQuantile: .9 });
assert.ok(Math.abs(deformed.medianPairDistanceSigma - .1) < 1e-12);
assert.ok(Math.abs(deformed.upperPairDistanceSigma - .1) < 1e-12);
assert.equal(deformed.frameCount, 3);
assert.equal(deformed.atomPresentations, 6);
assert.equal(deformed.crossFramePairsConstructed, false);
assert.equal(deformed.temporalOrderingUsed, false);

assert.throws(() => learnLocalPairDistanceUncertaintyEnsemble([
  frame(reference),
  { species: ["O", "D", "H"], distance: () => 1 },
], { localCutoff: 1.5 }), /changes fixed atom identity/);

const unavailable = learnLocalPairDistanceUncertaintyEnsemble([frame(reference)], { localCutoff: 1.5 });
assert.equal(unavailable.available, false);

console.log("ensemble local pair-distance uncertainty: passed", {
  rigidSigma: rigidModel.maximumPairDistanceSigma,
  deformedSigma: deformed.upperPairDistanceSigma,
});
