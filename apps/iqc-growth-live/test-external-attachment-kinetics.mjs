import assert from "node:assert/strict";
import { ATTACHMENT_KINETICS_RESPONSE_SCHEMA, attachmentKineticsSha256,
  buildAttachmentKineticsRequest, buildNormalizedKineticWulffGeometry,
  validateAttachmentKineticsResponse, evaluateKineticHabitScore,
  matchedKineticHabitRankingAudit } from "./external-attachment-kinetics.mjs";

const digest = "a".repeat(64);
const basis = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
const request = buildAttachmentKineticsRequest({ generatedAt: "2026-08-31T00:00:00Z", buildId: "test",
  scenarioId: "fixture", materialName: "polar test", elements: ["A", "B"], structureSha256: digest,
  intrinsicDimension: 3, orientationBasisCartesian: basis, targetUsed: false });
assert.equal(request.safeguards.physicalTimeIntegrated, false);
assert.throws(() => buildAttachmentKineticsRequest({ ...request.specimen, generatedAt: "x", buildId: "x",
  scenarioId: "x", materialName: "x", targetUsed: true }), /cannot use a growth target/);
const requestSha256 = await attachmentKineticsSha256(request);
const response = {
  schema: ATTACHMENT_KINETICS_RESPONSE_SCHEMA, requestSha256, structureSha256: digest,
  intrinsicDimension: 3, orientationBasisCartesian: basis, units: "metre per second",
  method: { family: "direct interface advance", program: "test-engine", version: "1",
    settingsSha256: "b".repeat(64) },
  drivingCondition: { description: "fixed undercooling and composition", settingsSha256: "c".repeat(64),
    temperatureKelvin: 900, couplingStateSha256: "d".repeat(64) },
  validation: { passed: true, converged: true, uncertaintyReported: true,
    orientationSetPredeclared: true, steadyStateWindowVerified: true },
  orientations: [
    { orientationId: "+x", normal: [1, 0, 0], normalGrowthVelocity: 4, uncertainty: .1 },
    { orientationId: "-x", normal: [-1, 0, 0], normalGrowthVelocity: 1, uncertainty: .1 },
    { orientationId: "+y", normal: [0, 1, 0], normalGrowthVelocity: 2, uncertainty: .1 },
    { orientationId: "-y", normal: [0, -1, 0], normalGrowthVelocity: 2, uncertainty: .1 },
    { orientationId: "+z", normal: [0, 0, 1], normalGrowthVelocity: 2, uncertainty: .1 },
    { orientationId: "-z", normal: [0, 0, -1], normalGrowthVelocity: 2, uncertainty: .1 },
  ],
};
const validated = validateAttachmentKineticsResponse(response, { requestSha256, structureSha256: digest,
  intrinsicDimension: 3, orientationBasisCartesian: basis });
assert.equal(validated.geometry.kineticWulffShapeConditionalOnSuppliedOrientations, true);
assert.equal(validated.drivingCondition.couplingStateSha256, "d".repeat(64));
assert.equal(validated.geometry.interfacialFreeEnergyUsed, false);
assert.equal(buildNormalizedKineticWulffGeometry(validated.orientations, 3).bounded, true);
assert.throws(() => buildNormalizedKineticWulffGeometry([
  ...validated.orientations.slice(0, 5), { ...validated.orientations[5], normalGrowthVelocity: 0 },
], 3), /positive/);
assert.throws(() => validateAttachmentKineticsResponse({ ...response,
  orientations: response.orientations.map((entry, index) => index ? entry : { ...entry, normalGrowthVelocity: .2, uncertainty: .1 }) },
{ requestSha256, structureSha256: digest, intrinsicDimension: 3, orientationBasisCartesian: basis }), /three-sigma/);

const occupied = [[0, 0, 0], [0, 1, 0], [0, 0, 1], [0, -1, 0], [0, 0, -1]];
const positive = evaluateKineticHabitScore({ occupiedPositions: occupied, emittedPositions: [[3, 0, 0]],
  orientationBasisCartesian: basis, orientations: validated.orientations, maximumAngleRadians: Math.PI / 12 });
const negative = evaluateKineticHabitScore({ occupiedPositions: occupied, emittedPositions: [[-3, 0, 0]],
  orientationBasisCartesian: basis, orientations: validated.orientations, maximumAngleRadians: Math.PI / 12 });
assert.equal(positive.supported, true); assert.equal(negative.supported, true);
assert.ok(positive.score > 0); assert.ok(negative.score < 0);
assert.notEqual(positive.normalGrowthVelocityMetrePerSecond, negative.normalGrowthVelocityMetrePerSecond,
  "opposite polar terminations must remain distinct");
const rotated = evaluateKineticHabitScore({ occupiedPositions: occupied.map(([x, y, z]) => [-y, x, z]),
  emittedPositions: [[0, 3, 0]], orientationBasisCartesian: [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],
  orientations: validated.orientations, maximumAngleRadians: Math.PI / 12 });
assert.ok(Math.abs(rotated.score - positive.score) < 1e-12, "proper specimen-frame transport must be equivariant");
const audit = matchedKineticHabitRankingAudit([
  { candidateId: "slow", baselineScore: 2, regularizedScore: 1, supported: true },
  { candidateId: "fast", baselineScore: 1, regularizedScore: 2, supported: true },
]);
assert.equal(audit.rankInversions, 1); assert.equal(audit.candidateSetIdentical, true);
console.log("external attachment-kinetics / kinetic-Wulff tests passed");
