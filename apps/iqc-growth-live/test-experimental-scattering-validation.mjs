import assert from "node:assert/strict";
import {
  buildExperimentalScatteringRequest,
  buildInstrumentProfileDemonstrator,
  compareExperimentalScattering,
  validateExperimentalScatteringResponse,
} from "./experimental-scattering-validation.mjs";

const digest = "a".repeat(64);
const request = buildExperimentalScatteringRequest({
  structureSha256: digest, materialLabel: "NaCl", species: ["Na", "Cl"],
  probe: "x-ray", modelChannel: { kind: "xray-neutral-f0" }, qMinimumInverseAngstrom: .2,
  qMaximumInverseAngstrom: 16,
});
assert.equal(request.analysisRole, "post-growth validation only");
assert.equal(request.mayAffectGrowth, false);
assert.deepEqual(request.modelCoherence, { kind: "finite-section", coherenceLengthAngstrom: null });
assert.ok(request.acceptedCifDataNames.includes("_pd_meas.intensity_total"));
const periodicRequest = buildExperimentalScatteringRequest({
  structureSha256: digest, modelChannel: { kind: "xray-neutral-f0" },
  modelCoherence: { kind: "periodic-cell", coherenceLengthAngstrom: 200 },
});
assert.deepEqual(periodicRequest.modelCoherence, { kind: "periodic-cell", coherenceLengthAngstrom: 200 });
assert.throws(() => buildExperimentalScatteringRequest({ structureSha256: digest,
  modelCoherence: { kind: "periodic-cell", coherenceLengthAngstrom: 0 } }), /positive/);

const qDimensionless = Array.from({ length: 64 }, (_, index) => .5 + index * .24);
const values = qDimensionless.map(q => 1 + 2.4 * Math.exp(-(((q - 5.1) / .42) ** 2))
  + 1.2 * Math.exp(-(((q - 9.3) / .67) ** 2)));
const demo = buildInstrumentProfileDemonstrator(request, { q: qDimensionless, values }, {
  nearestNeighborAngstrom: 2.82, resolutionFwhmQ: .08,
});
const profile = validateExperimentalScatteringResponse(request, demo);
assert.equal(profile.demonstratorOnly, true);
assert.equal(profile.experimentalEvidence, false);
assert.equal(profile.q.length, 64);
const comparison = compareExperimentalScattering({ q: qDimensionless, values }, profile, {
  nearestNeighborAngstrom: 2.82, nuisance: "scale+constant",
});
assert.equal(comparison.comparedPoints, 64);
assert.ok(comparison.rwp < .02);
assert.ok(comparison.correlation > .999);
assert.equal(comparison.targetUsedBeforeGrowth, false);
assert.equal(comparison.candidateSetChanged, false);

const twoTheta = qDimensionless.map(q => 2 * Math.asin(q / 2.82 * 1.5406 / (4 * Math.PI)) * 180 / Math.PI);
const experimental = validateExperimentalScatteringResponse(request, {
  requestId: request.requestId, structureSha256: digest, probe: "x-ray",
  modelChannel: { kind: "xray-neutral-f0" }, axis: "two-theta-degree", wavelengthAngstrom: 1.5406,
  abscissa: twoTheta, intensity: demo.intensity, standardUncertainty: demo.standardUncertainty,
  intensityUnits: "counts", resolutionFwhmQ: .08, independentOfGrowth: true,
  usedForGrowth: false, usedForMarking: false, usedForCandidateSelection: false,
  materialCorrespondence: { level: "exact-phase", elements: ["Cl", "Na"], formula: "NaCl",
    phase: "Halite", basis: "exact chemistry plus phase", sameMaterialClaimAllowed: true },
  provenance: { title: "Independent test profile", doi: "10.0000/example", temperatureKelvin: 298 },
});
assert.equal(experimental.experimentalEvidence, true);
assert.equal(experimental.sameMaterialEvidence, true);
experimental.q.forEach((q, index) => assert.ok(Math.abs(q - profile.q[index]) < 1e-12));

const compositionOnly = validateExperimentalScatteringResponse(request, {
  ...demo, probe: "x-ray", independentOfGrowth: true,
  materialCorrespondence: { level: "composition-only", elements: ["Cl", "Na"], formula: "NaCl",
    phase: "unknown polymorph", basis: "exact chemistry only", sameMaterialClaimAllowed: false },
});
assert.equal(compositionOnly.experimentalEvidence, true);
assert.equal(compositionOnly.sameMaterialEvidence, false);

assert.throws(() => validateExperimentalScatteringResponse(request, {
  ...demo, probe: "x-ray", independentOfGrowth: false,
}), /independent/);
assert.throws(() => validateExperimentalScatteringResponse(request, {
  ...demo, usedForCandidateSelection: true,
}), /cannot feed/);
assert.throws(() => validateExperimentalScatteringResponse(request, {
  ...demo, modelChannel: { kind: "unit" },
}), /does not match/);
assert.throws(() => compareExperimentalScattering({ q: [1, 2], values: [1, 1] }, profile, {
  nearestNeighborAngstrom: 2.82,
}), /must align/);

console.log("experimental scattering validation: all tests passed");
