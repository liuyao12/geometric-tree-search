import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";

if (!globalThis.crypto) globalThis.crypto = webcrypto;

const {
  ACTION_BARRIER_RESPONSE_SCHEMA,
  buildFrozenActionBarrierRequest,
  frozenActionBarrierRequestReceipt,
  validateFrozenActionBarrierResponse,
} = await import("../apps/iqc-growth-live/external-action-barrier.mjs");

const sha = "a".repeat(64);
const candidates = [
  { candidateId: "b", candidateDigestSha256: "b".repeat(64), actionLabel: "B", parentType: 1,
    childType: 2, ruleId: 3, emittedSites: [{ species: "Na", positionAngstrom: [1, 0, 0] }],
    actionSites: [{ species: "Na", positionAngstrom: [1, 0, 0] }] },
  { candidateId: "a", candidateDigestSha256: "c".repeat(64), actionLabel: "A", parentType: 2,
    childType: 1, ruleId: 4, emittedSites: [{ species: "Cl", positionAngstrom: [0, 1, 0] }],
    actionSites: [{ species: "Cl", positionAngstrom: [0, 1, 0] }] },
];

const request = await buildFrozenActionBarrierRequest({
  generatedAt: "2026-08-30T00:00:00Z", buildId: "test", scenarioId: "nacl", materialName: "NaCl",
  elements: ["Cl", "Na"], candidates, targetUsed: false, candidateSetTargetUsed: false,
  initialConfiguration: { structureSha256: sha, periodicBoundary: [true, true, true],
    cellVectorsAngstrom: [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
    atoms: [{ siteId: 0, species: "Na", positionAngstrom: [0, 0, 0] }] },
});
assert.deepEqual(request.frontier.candidates.map((candidate) => candidate.candidateId), ["a", "b"]);
assert.match(request.frontier.candidateBatchSha256, /^[a-f0-9]{64}$/);
const permuted = await buildFrozenActionBarrierRequest({
  generatedAt: "later", buildId: "test", scenarioId: "nacl", materialName: "NaCl", elements: ["Na", "Cl"],
  candidates: [...candidates].reverse(), targetUsed: false, candidateSetTargetUsed: false,
  initialConfiguration: { structureSha256: sha,
    atoms: [{ siteId: 0, species: "Na", positionAngstrom: [0, 0, 0] }] },
});
assert.equal(permuted.frontier.candidateBatchSha256, request.frontier.candidateBatchSha256);
const receipt = await frozenActionBarrierRequestReceipt(request);
const response = {
  schema: ACTION_BARRIER_RESPONSE_SCHEMA, requestSha256: receipt.requestSha256,
  candidateBatchSha256: receipt.candidateBatchSha256, initialStructureSha256: receipt.initialStructureSha256,
  method: { family: "NEB", program: "test", version: "1", settingsSha256: "d".repeat(64) },
  validation: { passed: true, protocolMatchesRequest: true, independentHoldout: true,
    uncertaintyReported: true, convergenceReported: true, everyCandidateConverged: true },
  safeguards: { containsGrowthTargetCoordinates: false, geometricScoresUsedAsPhysicalLabels: false,
    searchStepsUsedAsPhysicalTime: false, candidateSetChanged: false, hardAdmissionChanged: false },
  records: request.frontier.candidates.map((candidate, index) => ({ candidateId: candidate.candidateId,
    candidateDigestSha256: candidate.candidateDigestSha256, barrierElectronVolt: index ? 1.2 : .4,
    uncertaintyElectronVolt: .02, maximumForceElectronVoltPerAngstrom: .01,
    imageCount: 7, converged: true })),
};
const validated = validateFrozenActionBarrierResponse(response, { ...receipt,
  candidates: request.frontier.candidates.map(({ candidateId, candidateDigestSha256 }) =>
    ({ candidateId, candidateDigestSha256 })) });
assert.equal(validated.candidateCount, 2);
assert.ok(validated.records[0].lowerBarrierScore > validated.records[1].lowerBarrierScore);
assert.equal(validated.usedAsPhysicalClock, false);

assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  records: [response.records[0], response.records[0]] }, { ...receipt,
  candidates: request.frontier.candidates }), /duplicate|exactly/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  records: response.records.map((record, index) => ({ ...record, barrierElectronVolt: index ? -1 : .2 })) },
{ ...receipt, candidates: request.frontier.candidates }), /nonnegative/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  candidateBatchSha256: "0".repeat(64) }, { ...receipt, candidates: request.frontier.candidates }),
/not bound/);

console.log("external action barrier contract: passed");
