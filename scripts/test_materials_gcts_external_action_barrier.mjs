import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";

if (!globalThis.crypto) globalThis.crypto = webcrypto;

const {
  ACTION_BARRIER_RESPONSE_SCHEMA,
  actionBarrierSha256,
  buildFrozenActionBarrierRequest,
  frozenActionBarrierRequestReceipt,
  validateFrozenActionBarrierResponse,
} = await import("../apps/iqc-growth-live/external-action-barrier.mjs");
const { buildFrozenKineticCompetition } = await import(
  "../apps/iqc-growth-live/frozen-frontier-kinetics.mjs");

const sha = "a".repeat(64);
const rawCandidates = [
  { candidateId: "b", actionLabel: "B", parentType: 1,
    childType: 2, ruleId: 3, emittedSites: [{ species: "Na", positionAngstrom: [1, 0, 0] }],
    actionSites: [{ species: "Na", positionAngstrom: [1, 0, 0] }] },
  { candidateId: "a", actionLabel: "A", parentType: 2,
    childType: 1, ruleId: 4, emittedSites: [{ species: "Cl", positionAngstrom: [0, 1, 0] }],
    actionSites: [{ species: "Cl", positionAngstrom: [0, 1, 0] }] },
];
const candidates = await Promise.all(rawCandidates.map(async (candidate) => ({ ...candidate,
  candidateDigestSha256: await actionBarrierSha256({ candidateId: candidate.candidateId,
    eventDirection: "attach", emittedSites: candidate.emittedSites, removedSites: [],
    actionSites: candidate.actionSites }) })));

const request = await buildFrozenActionBarrierRequest({
  generatedAt: "2026-08-30T00:00:00Z", buildId: "test", scenarioId: "nacl", materialName: "NaCl",
  elements: ["Cl", "Na"], candidates, targetUsed: false, candidateSetTargetUsed: false,
  initialConfiguration: { structureSha256: sha, periodicBoundary: [true, true, true],
    cellVectorsAngstrom: [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
    atoms: [{ siteId: 0, species: "Na", positionAngstrom: [0, 0, 0] }] },
});
assert.deepEqual(request.frontier.candidates.map((candidate) => candidate.candidateId), ["a", "b"]);
assert.match(request.frontier.candidateBatchSha256, /^[a-f0-9]{64}$/);
assert.equal(request.calculation.optionalReservoirThermodynamics.ensemble,
  "grand-canonical-T-V-mu");
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
    initialGeometrySha256: candidate.initialGeometrySha256,
    finalGeometrySha256: candidate.finalGeometrySha256,
    energyDeltaElectronVolt: index ? .25 : -.1,
    energyDeltaUncertaintyElectronVolt: .015,
    uncertaintyElectronVolt: .02, maximumForceElectronVoltPerAngstrom: .01,
    imageCount: 7, converged: true })),
};
const validated = validateFrozenActionBarrierResponse(response, { ...receipt,
  candidates: request.frontier.candidates });
assert.equal(validated.candidateCount, 2);
assert.ok(validated.records[0].lowerBarrierScore > validated.records[1].lowerBarrierScore);
assert.equal(validated.usedAsPhysicalClock, false);
assert.equal(validated.kineticsEligible, false);
assert.deepEqual(validated.eventDirections, ["attach"]);
assert.equal(validated.records[0].energyDeltaUncertaintyElectronVolt, .015);

const kineticResponse = {
  ...response,
  kinetics: { model: "harmonic-transition-state-theory", prefactorMethod: "finite-difference Hessian",
    prefactorSettingsSha256: "e".repeat(64), recrossingCorrection: "not-included",
    catalogScope: "requested-hard-admitted-actions-only" },
  validation: { ...response.validation, prefactorsReported: true, everyPrefactorConverged: true,
    prefactorUncertaintyReported: true },
  records: response.records.map((record, index) => ({ ...record,
    attemptFrequencyPerSecond: 1e13 * (index + 1), attemptFrequencyUncertaintyLog10: .2,
    prefactorConverged: true })),
};
const validatedKinetics = validateFrozenActionBarrierResponse(kineticResponse, { ...receipt,
  candidates: request.frontier.candidates });
assert.equal(validatedKinetics.kineticsEligible, true);
assert.equal(validatedKinetics.records[0].attemptFrequencyPerSecond, 1e13);
assert.equal(validatedKinetics.kinetics.catalogScope, "requested-hard-admitted-actions-only");
const kineticCompetition = buildFrozenKineticCompetition(validatedKinetics.records,
  { temperatureKelvin: 600, mode: "seeded-kmc", eventUniform: .5, waitingUniform: .25 });
assert.equal(kineticCompetition.candidateCount, validatedKinetics.candidateCount);
assert.ok(validatedKinetics.records.some((record) =>
  record.candidateId === kineticCompetition.selectedCandidateId));
assert.ok(kineticCompetition.waitingTimeSeconds > 0);
assert.equal(kineticCompetition.targetUsed, false);

const coupledRequest = await buildFrozenActionBarrierRequest({
  generatedAt: "2026-08-30T00:00:00Z", buildId: "test", scenarioId: "nacl", materialName: "NaCl",
  elements: ["Cl", "Na"], candidates, targetUsed: false, candidateSetTargetUsed: false,
  couplingStateExpectation: { couplingStateSha256: "9".repeat(64), temperatureKelvin: 600,
    sourceEvidence: ["interface-flux", "attachment-kinetics"] },
  initialConfiguration: request.frontier.initialConfiguration,
});
const coupledReceipt = await frozenActionBarrierRequestReceipt(coupledRequest);
assert.equal(coupledReceipt.couplingStateExpectation.temperatureKelvin, 600);
const coupledResponse = { ...kineticResponse,
  requestSha256: coupledReceipt.requestSha256,
  candidateBatchSha256: coupledReceipt.candidateBatchSha256,
  initialStructureSha256: coupledReceipt.initialStructureSha256,
  kinetics: { ...kineticResponse.kinetics, couplingStateSha256: "9".repeat(64),
    temperatureKelvin: 600 } };
const coupledAudit = validateFrozenActionBarrierResponse(coupledResponse, { ...coupledReceipt,
  candidates: coupledRequest.frontier.candidates });
assert.equal(coupledAudit.kinetics.couplingStateSha256, "9".repeat(64));
assert.throws(() => validateFrozenActionBarrierResponse({ ...coupledResponse,
  kinetics: { ...coupledResponse.kinetics, couplingStateSha256: "8".repeat(64) } },
{ ...coupledReceipt, candidates: coupledRequest.frontier.candidates }), /shared coupling state/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...coupledResponse,
  kinetics: { ...coupledResponse.kinetics, temperatureKelvin: 601 } },
{ ...coupledReceipt, candidates: coupledRequest.frontier.candidates }), /temperature does not match/);

const thermodynamicResponse = {
  ...kineticResponse,
  safeguards: { ...kineticResponse.safeguards,
    chemicalPotentialsExternallySupplied: true,
    stateFreeEnergiesExternallySupplied: true,
    geometricScoresUsedAsThermodynamicLabels: false,
    globalDetailedBalanceClaimed: false },
  thermodynamics: { model: "grand-canonical-state-free-energy",
    ensemble: "grand-canonical-T-V-mu", systemFreeEnergyKind: "Helmholtz",
    temperatureKelvin: 600, freeEnergyMethod: "harmonic free energy",
    freeEnergySettingsSha256: "1".repeat(64),
    chemicalPotentialReference: "separately converged elemental reservoirs",
    chemicalPotentialSettingsSha256: "2".repeat(64), evidenceSha256: "3".repeat(64),
    uncertaintyAssumption: "independent-one-sigma", volumeHeldFixedAcrossPath: true,
    chemicalPotentials: [
      { species: "Na", electronVolt: -1, uncertaintyElectronVolt: .02 },
      { species: "Cl", electronVolt: -2, uncertaintyElectronVolt: .03 },
    ] },
  validation: { ...kineticResponse.validation, thermodynamicsReported: true,
    everyStateFreeEnergyConverged: true, chemicalPotentialUncertaintyReported: true },
  records: kineticResponse.records.map((record, index) => ({ ...record,
    systemFreeEnergyDeltaElectronVolt: index ? -.8 : -2.2,
    systemFreeEnergyDeltaUncertaintyElectronVolt: .04,
    stateFreeEnergyConverged: true })),
};
const validatedThermodynamics = validateFrozenActionBarrierResponse(thermodynamicResponse,
  { ...receipt, candidates: request.frontier.candidates });
assert.equal(validatedThermodynamics.grandCanonicalEvidenceEligible, true);
assert.deepEqual(validatedThermodynamics.records[0].speciesDelta, { Cl: 1 });
assert.ok(Math.abs(validatedThermodynamics.records[0].grandPotentialDeltaElectronVolt + .2) < 1e-12);
assert.ok(validatedThermodynamics.records[0].grandPotentialDeltaUncertaintyElectronVolt > .04);
assert.throws(() => validateFrozenActionBarrierResponse({ ...thermodynamicResponse,
  thermodynamics: { ...thermodynamicResponse.thermodynamics,
    chemicalPotentials: thermodynamicResponse.thermodynamics.chemicalPotentials.slice(0, 1) } },
{ ...receipt, candidates: request.frontier.candidates }), /missing chemical potentials/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...thermodynamicResponse,
  safeguards: { ...thermodynamicResponse.safeguards,
    geometricScoresUsedAsThermodynamicLabels: true } },
{ ...receipt, candidates: request.frontier.candidates }), /geometry-derived/);

assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  records: [response.records[0], response.records[0]] }, { ...receipt,
  candidates: request.frontier.candidates }), /duplicate|exactly/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  records: response.records.map((record, index) => ({ ...record, barrierElectronVolt: index ? -1 : .2 })) },
{ ...receipt, candidates: request.frontier.candidates }), /nonnegative/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  candidateBatchSha256: "0".repeat(64) }, { ...receipt, candidates: request.frontier.candidates }),
/not bound/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...kineticResponse,
  records: kineticResponse.records.map((record, index) => ({ ...record,
    prefactorConverged: index ? false : true })) }, { ...receipt, candidates: request.frontier.candidates }),
/prefactor/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...kineticResponse,
  kinetics: { ...kineticResponse.kinetics, model: "unspecified-rate-model" } },
{ ...receipt, candidates: request.frontier.candidates }), /harmonic-transition-state-theory/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  records: response.records.map((record, index) => index ? record
    : { ...record, energyDeltaUncertaintyElectronVolt: null }) },
{ ...receipt, candidates: request.frontier.candidates }), /supplied together/);

const detachRaw = { candidateId: "detach:2", eventDirection: "detach", actionLabel: "detach leaf",
  parentType: 1, childType: 2, ruleId: 3, emittedSites: [],
  removedSites: [{ species: "Na", positionAngstrom: [0, 0, 0] }],
  actionSites: [{ species: "Na", positionAngstrom: [0, 0, 0] }] };
const detach = { ...detachRaw, candidateDigestSha256: await actionBarrierSha256({
  candidateId: detachRaw.candidateId, eventDirection: "detach", emittedSites: [],
  removedSites: detachRaw.removedSites, actionSites: detachRaw.actionSites }) };
const reversibleRequest = await buildFrozenActionBarrierRequest({
  generatedAt: "2026-08-30T00:00:00Z", buildId: "test", scenarioId: "nacl", materialName: "NaCl",
  elements: ["Na"], candidates: [candidates[0], detach], targetUsed: false,
  initialConfiguration: { structureSha256: sha,
    atoms: [{ siteId: 0, species: "Na", positionAngstrom: [0, 0, 0] }] },
});
assert.deepEqual(reversibleRequest.frontier.candidates.map((candidate) => candidate.eventDirection),
  ["attach", "detach"]);
assert.equal(reversibleRequest.frontier.candidates.find((candidate) =>
  candidate.eventDirection === "detach").finalAtomCount, 0);
const reversibleReceipt = await frozenActionBarrierRequestReceipt(reversibleRequest);
const reversibleThermodynamicResponse = {
  schema: ACTION_BARRIER_RESPONSE_SCHEMA,
  requestSha256: reversibleReceipt.requestSha256,
  candidateBatchSha256: reversibleReceipt.candidateBatchSha256,
  initialStructureSha256: reversibleReceipt.initialStructureSha256,
  method: response.method,
  thermodynamics: { ...thermodynamicResponse.thermodynamics,
    chemicalPotentials: [{ species: "Na", electronVolt: -1,
      uncertaintyElectronVolt: .02 }] },
  validation: { ...response.validation, thermodynamicsReported: true,
    everyStateFreeEnergyConverged: true, chemicalPotentialUncertaintyReported: true },
  safeguards: thermodynamicResponse.safeguards,
  records: reversibleRequest.frontier.candidates.map((candidate) => ({
    candidateId: candidate.candidateId,
    candidateDigestSha256: candidate.candidateDigestSha256,
    initialGeometrySha256: candidate.initialGeometrySha256,
    finalGeometrySha256: candidate.finalGeometrySha256,
    barrierElectronVolt: .5, uncertaintyElectronVolt: .02,
    maximumForceElectronVoltPerAngstrom: .01, imageCount: 7, converged: true,
    systemFreeEnergyDeltaElectronVolt: candidate.eventDirection === "attach" ? -.8 : .8,
    systemFreeEnergyDeltaUncertaintyElectronVolt: .04,
    stateFreeEnergyConverged: true,
  })),
};
const reversibleThermodynamics = validateFrozenActionBarrierResponse(
  reversibleThermodynamicResponse, { ...reversibleReceipt,
    candidates: reversibleRequest.frontier.candidates });
assert.deepEqual(reversibleThermodynamics.records.find((record) =>
  record.eventDirection === "attach").speciesDelta, { Na: 1 });
assert.deepEqual(reversibleThermodynamics.records.find((record) =>
  record.eventDirection === "detach").speciesDelta, { Na: -1 });
await assert.rejects(() => buildFrozenActionBarrierRequest({
  generatedAt: "x", buildId: "test", scenarioId: "nacl", materialName: "NaCl", elements: ["Na"],
  candidates: [{ ...detach, removedSites: [{ species: "Na", positionAngstrom: [9, 0, 0] }],
    candidateDigestSha256: "0".repeat(64) }], targetUsed: false,
  initialConfiguration: { structureSha256: sha,
    atoms: [{ siteId: 0, species: "Na", positionAngstrom: [0, 0, 0] }] },
}), /absent/);

console.log("external action barrier contract: passed");
