import assert from "node:assert/strict";
import { assessGeometrySurrogatePromotion, evaluateFrozenGeometrySurrogate,
  frozenGeometrySurrogateArtifact, frozenGeometrySurrogatePreference,
  frozenGeometryFeatureSupport,
  geometryCalculationCalibration, geometryCalculationSurrogate, geometryReferenceIndices,
  geometrySurrogateCompatibilityDifferences, geometrySurrogateCompatibilityKey }
  from "../apps/iqc-growth-live/geometry-calculation-calibration.js";

const monotone = [
  { mismatch: 0, energy: 0, force: 0 },
  { mismatch: 1, energy: 2, force: 4 },
  { mismatch: 2, energy: 4, force: 1 },
  { mismatch: 3, energy: 6, force: 3 },
];
const energy = geometryCalculationCalibration(monotone, "mismatch", "energy");
assert.equal(energy.pairedFrames, 4);
assert.ok(Math.abs(energy.pearson - 1) < 1e-12);
assert.ok(Math.abs(energy.spearman - 1) < 1e-12);
assert.ok(Math.abs(energy.slope - 2) < 1e-12);
assert.ok(Math.abs(energy.intercept) < 1e-12);
assert.equal(energy.predictiveValidationPerformed, false);

const force = geometryCalculationCalibration(monotone, "mismatch", "force");
assert.ok(force.spearman > 0 && force.spearman < 1,
  "rank correlation must distinguish nonmonotone residual force from energy");
const ties = geometryCalculationCalibration([
  { x: 1, y: 2 }, { x: 1, y: 2 }, { x: 2, y: 3 }, { x: 3, y: 4 },
], "x", "y");
assert.ok(Math.abs(ties.spearman - 1) < 1e-12, "average ranks must preserve tied monotonic order");
const missing = geometryCalculationCalibration([{ x: 1, y: null }, { x: 2, y: 3 }], "x", "y");
assert.equal(missing.pairedFrames, 1);
assert.equal(missing.pearson, null);
assert.equal(missing.spearman, null);

assert.deepEqual(geometryReferenceIndices(4, "final"), [3]);
assert.deepEqual(geometryReferenceIndices(4, "first"), [0]);
assert.deepEqual(geometryReferenceIndices(4, "pooled"), [0, 1, 2, 3]);
assert.deepEqual(geometryReferenceIndices(4, "unknown"), [3]);
assert.throws(() => geometryReferenceIndices(0, "pooled"), /requires frames/);

const surrogateRecords = Array.from({ length: 8 }, (_, index) => ({
  distance: index,
  angle: (index % 3) - 1,
  coordination: index % 2,
  energy: 2 * index - .5 * ((index % 3) - 1) + .25 * (index % 2),
}));
const surrogate = geometryCalculationSurrogate(surrogateRecords,
  ["distance", "angle", "coordination"], "energy", { ridge: 1e-6 });
assert.equal(surrogate.available, true);
assert.equal(surrogate.predictions.length, 8);
assert.ok(surrogate.predictionSpearman > .99);
assert.ok(surrogate.meanAbsoluteError < 1e-3);
assert.equal(surrogate.independentValidationClaimed, false);
assert.equal(surrogate.usedForGrowth, false);
const shortSurrogate = geometryCalculationSurrogate(surrogateRecords.slice(0, 4),
  ["distance", "angle", "coordination"], "energy");
assert.equal(shortSurrogate.available, false);
assert.equal(shortSurrogate.requiredPairs, 5);
const artifact = frozenGeometrySurrogateArtifact(surrogate);
assert.equal(artifact.schema, "gcts-frozen-geometry-calculation-surrogate-v3");
assert.ok(artifact.targetScale > 0);
assert.deepEqual(artifact.featureMinimums, [0, -1, 0]);
assert.deepEqual(artifact.featureMaximums, [7, 1, 1]);
const transfer = evaluateFrozenGeometrySurrogate(surrogateRecords.map((record) => ({
  ...record, distance: record.distance + .25,
  energy: 2 * (record.distance + .25) - .5 * record.angle + .25 * record.coordination,
})), artifact);
assert.equal(transfer.available, true);
assert.equal(transfer.refitPerformed, false);
assert.equal(transfer.targetValuesUsedForPrediction, false);
assert.ok(transfer.predictionSpearman > .99);
assert.ok(transfer.meanAbsoluteError < 1e-3);
assert.equal(transfer.supportedFrames, 8);
assert.equal(transfer.featureSupportCoverage, 1);
const promotion = assessGeometrySurrogatePromotion(transfer);
assert.equal(promotion.eligible, true);
assert.equal(promotion.physicalPotentialValidated, false);
const preference = frozenGeometrySurrogatePreference(surrogateRecords[0], artifact);
assert.ok(Number.isFinite(preference.predicted));
assert.ok(preference.score >= -3 && preference.score <= 3);
assert.equal(preference.hardAdmissionChanged, false);
assert.equal(preference.inFeatureSupport, true);
const outOfSupport = frozenGeometrySurrogatePreference({ distance: 100, angle: 0, coordination: 0 }, artifact);
assert.equal(outOfSupport.abstained, true);
assert.equal(outOfSupport.score, 0);
assert.ok(frozenGeometryFeatureSupport({ distance: 100, angle: 0, coordination: 0 }, artifact)
  .maximumStandardizedExcess > 0);
const unsupportedTransfer = evaluateFrozenGeometrySurrogate(surrogateRecords.map((record) => ({
  ...record, distance: record.distance + 100,
})), artifact);
assert.equal(unsupportedTransfer.featureSupportCoverage, 0);
assert.equal(assessGeometrySurrogatePromotion(unsupportedTransfer).eligible, false);
assert.equal(assessGeometrySurrogatePromotion({ ...transfer, predictionSpearman: .79 }).eligible, false);
assert.equal(assessGeometrySurrogatePromotion({ ...transfer, predictiveQSquared: 0 }).eligible, false);
assert.throws(() => evaluateFrozenGeometrySurrogate(surrogateRecords, { ...artifact, featureScales: [0, 1, 1] }),
  /invalid frozen/);
const compatibility = {
  targetMode: "energy", targetKey: "relativeEnergyElectronVoltPerPrimitiveAtom",
  referenceMode: "pooled", featureSchema: "distance|angle|coordination",
  reducedComposition: '{"Cl":1,"Na":1}', periodicAxes: "[true,true,true]",
  programName: "VASP", programVersion: "6.4", methodCanonicalJson: '{"dft":{"xc":"PBE"}}',
  energyUnit: "eV", forceUnit: "eV/Å",
};
assert.equal(geometrySurrogateCompatibilityKey({ ...compatibility }),
  geometrySurrogateCompatibilityKey({ ...compatibility }));
assert.deepEqual(geometrySurrogateCompatibilityDifferences(compatibility,
  { ...compatibility, methodCanonicalJson: '{"dft":{"xc":"LDA"}}' }), ["methodCanonicalJson"]);
assert.throws(() => geometrySurrogateCompatibilityKey({ ...compatibility, programVersion: null }),
  /complete geometry surrogate provenance/);

console.log("geometry/calculation calibration statistics: passed");
