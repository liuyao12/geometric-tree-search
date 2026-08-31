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
const siteKey = (site) => `${site.species}\u0000${site.positionAngstrom.join(",")}`;
function pathGeometryFor(candidate, initialConfiguration, barrierElectronVolt,
  energyDeltaElectronVolt = 0, maximumForceElectronVoltPerAngstrom = .01) {
  const initial = initialConfiguration.atoms.map((site, index) => ({ pathSiteId: `initial-${index}`,
    species: site.species, positionAngstrom: [...site.positionAngstrom], domain: "material" }));
  const initialById = new Map(initial.map((site) => [site.pathSiteId, site]));
  const finalById = new Map(initial.map((site) => [site.pathSiteId, { ...site,
    positionAngstrom: [...site.positionAngstrom] }]));
  const unusedInitial = new Set(initial.map((site) => site.pathSiteId));
  const removedIds = (candidate.removedSites || []).map((removed) => {
    const match = initial.find((site) => unusedInitial.has(site.pathSiteId)
      && siteKey(site) === siteKey(removed));
    assert.ok(match, `test path source ${siteKey(removed)} must exist`);
    unusedInitial.delete(match.pathSiteId); return match.pathSiteId;
  });
  const far = (index, sign = 1) => [7 + index, sign * (6 + index), 5 + index];
  if (candidate.eventDirection === "hop") {
    const unusedEmitted = new Set((candidate.emittedSites || []).map((_, index) => index));
    removedIds.forEach((pathSiteId) => {
      const source = initialById.get(pathSiteId);
      const emittedIndex = [...unusedEmitted].find((index) =>
        candidate.emittedSites[index].species === source.species);
      assert.notEqual(emittedIndex, undefined); unusedEmitted.delete(emittedIndex);
      finalById.set(pathSiteId, { ...source,
        positionAngstrom: [...candidate.emittedSites[emittedIndex].positionAngstrom],
        domain: "material" });
    });
  } else {
    removedIds.forEach((pathSiteId, index) => {
      const source = initialById.get(pathSiteId);
      finalById.set(pathSiteId, { ...source, positionAngstrom: far(index, -1), domain: "reservoir" });
    });
    (candidate.emittedSites || []).forEach((emitted, index) => {
      const pathSiteId = `incoming-${index}`;
      initialById.set(pathSiteId, { pathSiteId, species: emitted.species,
        positionAngstrom: far(index, 1), domain: "reservoir" });
      finalById.set(pathSiteId, { pathSiteId, species: emitted.species,
        positionAngstrom: [...emitted.positionAngstrom], domain: "material" });
    });
  }
  const fixedMaterialSites = [...unusedInitial].sort().map((pathSiteId) => {
    const site = initialById.get(pathSiteId);
    initialById.delete(pathSiteId); finalById.delete(pathSiteId);
    return { pathSiteId, species: site.species,
      positionAngstrom: [...site.positionAngstrom] };
  });
  const ids = [...initialById.keys()].sort();
  const endpointSites = (table) => ids.map((id) => ({ ...table.get(id),
    positionAngstrom: [...table.get(id).positionAngstrom] }));
  const middleSites = ids.map((id) => {
    const first = initialById.get(id); const last = finalById.get(id);
    return { pathSiteId: id, species: first.species,
      positionAngstrom: first.positionAngstrom.map((value, axis) =>
        (value + last.positionAngstrom[axis]) / 2),
      domain: first.domain === last.domain ? first.domain : "interface" };
  });
  return { candidateId: candidate.candidateId,
    candidateDigestSha256: candidate.candidateDigestSha256,
    initialGeometrySha256: candidate.initialGeometrySha256,
    finalGeometrySha256: candidate.finalGeometrySha256,
    pathModel: candidate.eventDirection === "hop" ? "closed-system-fixed-composition"
      : "explicit-reservoir-extended-system",
    fixedMaterialSites,
    reservoir: candidate.eventDirection === "hop" ? null : {
      mode: "explicit-extended-system", boundaryCondition: "surface-feedstock",
      description: "test-only explicit reservoir sites", settingsSha256: "7".repeat(64),
      chemicalPotentialReference: "test reference" },
    pathConverged: true, endpointMappingVerified: true,
    extendedSystemAtomCountConstant: true, speciesIdentityConstant: true,
    saddleImageIndex: 1,
    images: [
      { reactionCoordinate: 0, energyElectronVolt: 0,
        maximumForceElectronVoltPerAngstrom: 0, sites: endpointSites(initialById) },
      { reactionCoordinate: .5, energyElectronVolt: barrierElectronVolt,
        maximumForceElectronVoltPerAngstrom, sites: middleSites },
      { reactionCoordinate: 1, energyElectronVolt: energyDeltaElectronVolt,
        maximumForceElectronVoltPerAngstrom: 0, sites: endpointSites(finalById) },
    ] };
}
const expectedFor = (request, receipt) => ({ ...receipt,
  candidates: request.frontier.candidates,
  initialConfiguration: request.frontier.initialConfiguration });
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
    uncertaintyReported: true, convergenceReported: true, everyCandidateConverged: true,
    everyPathGeometryValidated: true },
  safeguards: { containsGrowthTargetCoordinates: false, geometricScoresUsedAsPhysicalLabels: false,
    searchStepsUsedAsPhysicalTime: false, candidateSetChanged: false, hardAdmissionChanged: false,
    pathCoordinatesExternallyCalculated: true, pathGeometryChangedCandidateEndpoints: false },
  records: request.frontier.candidates.map((candidate, index) => {
    const barrierElectronVolt = index ? 1.2 : .4;
    const energyDeltaElectronVolt = index ? .25 : -.1;
    return { candidateId: candidate.candidateId,
      candidateDigestSha256: candidate.candidateDigestSha256, barrierElectronVolt,
      initialGeometrySha256: candidate.initialGeometrySha256,
      finalGeometrySha256: candidate.finalGeometrySha256,
      energyDeltaElectronVolt, energyDeltaUncertaintyElectronVolt: .015,
      uncertaintyElectronVolt: .02, maximumForceElectronVoltPerAngstrom: .01,
      imageCount: 3, converged: true,
      pathGeometry: pathGeometryFor(candidate, request.frontier.initialConfiguration,
        barrierElectronVolt, energyDeltaElectronVolt, .01) };
  }),
};
const validated = validateFrozenActionBarrierResponse(response, expectedFor(request, receipt));
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
const validatedKinetics = validateFrozenActionBarrierResponse(kineticResponse,
  expectedFor(request, receipt));
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
const coupledAudit = validateFrozenActionBarrierResponse(coupledResponse,
  expectedFor(coupledRequest, coupledReceipt));
assert.equal(coupledAudit.kinetics.couplingStateSha256, "9".repeat(64));
assert.throws(() => validateFrozenActionBarrierResponse({ ...coupledResponse,
  kinetics: { ...coupledResponse.kinetics, couplingStateSha256: "8".repeat(64) } },
expectedFor(coupledRequest, coupledReceipt)), /shared coupling state/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...coupledResponse,
  kinetics: { ...coupledResponse.kinetics, temperatureKelvin: 601 } },
expectedFor(coupledRequest, coupledReceipt)), /temperature does not match/);

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
  expectedFor(request, receipt));
assert.equal(validatedThermodynamics.grandCanonicalEvidenceEligible, true);
assert.deepEqual(validatedThermodynamics.records[0].speciesDelta, { Cl: 1 });
assert.ok(Math.abs(validatedThermodynamics.records[0].grandPotentialDeltaElectronVolt + .2) < 1e-12);
assert.ok(validatedThermodynamics.records[0].grandPotentialDeltaUncertaintyElectronVolt > .04);
assert.throws(() => validateFrozenActionBarrierResponse({ ...thermodynamicResponse,
  thermodynamics: { ...thermodynamicResponse.thermodynamics,
    chemicalPotentials: thermodynamicResponse.thermodynamics.chemicalPotentials.slice(0, 1) } },
expectedFor(request, receipt)), /missing chemical potentials/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...thermodynamicResponse,
  safeguards: { ...thermodynamicResponse.safeguards,
    geometricScoresUsedAsThermodynamicLabels: true } },
expectedFor(request, receipt)), /geometry-derived/);

assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  records: [response.records[0], response.records[0]] }, expectedFor(request, receipt)),
  /duplicate|exactly/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  records: response.records.map((record, index) => ({ ...record,
    barrierElectronVolt: index ? -1 : record.barrierElectronVolt })) },
expectedFor(request, receipt)), /nonnegative/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  candidateBatchSha256: "0".repeat(64) }, expectedFor(request, receipt)),
/not bound/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...kineticResponse,
  records: kineticResponse.records.map((record, index) => ({ ...record,
    prefactorConverged: index ? false : true })) }, expectedFor(request, receipt)),
/prefactor/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...kineticResponse,
  kinetics: { ...kineticResponse.kinetics, model: "unspecified-rate-model" } },
expectedFor(request, receipt)), /harmonic-transition-state-theory/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  records: response.records.map((record, index) => index ? record
    : { ...record, energyDeltaUncertaintyElectronVolt: null }) },
expectedFor(request, receipt)), /supplied together/);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  validation: { ...response.validation, everyPathGeometryValidated: false } },
expectedFor(request, receipt)), /path geometry|validation/i);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  records: response.records.map((record, index) => index ? record
    : { ...record, pathGeometry: null }) }, expectedFor(request, receipt)),
/path geometry|candidate/i);
assert.throws(() => validateFrozenActionBarrierResponse({ ...response,
  records: response.records.map((record, index) => index ? record : { ...record,
    pathGeometry: { ...record.pathGeometry, images: record.pathGeometry.images.map(
      (image, imageIndex) => imageIndex === record.pathGeometry.images.length - 1
        ? { ...image, sites: image.sites.map((site, siteIndex) => siteIndex
          ? site : { ...site, positionAngstrom: [99, 99, 99] }) } : image) } }) },
expectedFor(request, receipt)), /does not reproduce|endpoint/i);

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
    maximumForceElectronVoltPerAngstrom: .01, imageCount: 3, converged: true,
    pathGeometry: pathGeometryFor(candidate,
      reversibleRequest.frontier.initialConfiguration, .5, 0, .01),
    systemFreeEnergyDeltaElectronVolt: candidate.eventDirection === "attach" ? -.8 : .8,
    systemFreeEnergyDeltaUncertaintyElectronVolt: .04,
    stateFreeEnergyConverged: true,
  })),
};
const reversibleThermodynamics = validateFrozenActionBarrierResponse(
  reversibleThermodynamicResponse, expectedFor(reversibleRequest, reversibleReceipt));
assert.deepEqual(reversibleThermodynamics.records.find((record) =>
  record.eventDirection === "attach").speciesDelta, { Na: 1 });
assert.deepEqual(reversibleThermodynamics.records.find((record) =>
  record.eventDirection === "detach").speciesDelta, { Na: -1 });
const hopRaw = { candidateId: "hop:2->9", eventDirection: "hop", actionLabel: "surface hop",
  parentType: 1, childType: 1, ruleId: 8,
  emittedSites: [{ species: "Na", positionAngstrom: [2, 0, 0] }],
  removedSites: [{ species: "Na", positionAngstrom: [0, 0, 0] }],
  actionSites: [{ species: "Na", positionAngstrom: [0, 0, 0] },
    { species: "Na", positionAngstrom: [2, 0, 0] }] };
const hop = { ...hopRaw, candidateDigestSha256: await actionBarrierSha256({
  candidateId: hopRaw.candidateId, eventDirection: "hop", emittedSites: hopRaw.emittedSites,
  removedSites: hopRaw.removedSites, actionSites: hopRaw.actionSites }) };
const hopRequest = await buildFrozenActionBarrierRequest({
  generatedAt: "2026-08-30T00:00:00Z", buildId: "test", scenarioId: "nacl",
  materialName: "NaCl", elements: ["Na"], candidates: [hop], targetUsed: false,
  initialConfiguration: { structureSha256: sha,
    atoms: [{ siteId: 0, species: "Na", positionAngstrom: [0, 0, 0] }] },
});
assert.equal(hopRequest.frontier.candidates[0].eventDirection, "hop");
assert.equal(hopRequest.frontier.candidates[0].initialAtomCount, 1);
assert.equal(hopRequest.frontier.candidates[0].finalAtomCount, 1);
assert.notEqual(hopRequest.frontier.candidates[0].initialGeometrySha256,
  hopRequest.frontier.candidates[0].finalGeometrySha256);
const exchangeRaw = { candidateId: "exchange:2->9", eventDirection: "exchange",
  actionLabel: "local Na/K exchange", parentType: 1, childType: 2, ruleId: 9,
  emittedSites: [{ species: "K", positionAngstrom: [2, 0, 0] }],
  removedSites: [{ species: "Na", positionAngstrom: [0, 0, 0] }],
  actionSites: [{ species: "Na", positionAngstrom: [0, 0, 0] },
    { species: "K", positionAngstrom: [2, 0, 0] }] };
const exchange = { ...exchangeRaw, candidateDigestSha256: await actionBarrierSha256({
  candidateId: exchangeRaw.candidateId, eventDirection: "exchange",
  emittedSites: exchangeRaw.emittedSites, removedSites: exchangeRaw.removedSites,
  actionSites: exchangeRaw.actionSites }) };
const exchangeRequest = await buildFrozenActionBarrierRequest({
  generatedAt: "2026-08-30T00:00:00Z", buildId: "test", scenarioId: "nacl",
  materialName: "NaKCl", elements: ["Na", "K"], candidates: [exchange], targetUsed: false,
  initialConfiguration: { structureSha256: sha,
    atoms: [{ siteId: 0, species: "Na", positionAngstrom: [0, 0, 0] }] },
});
assert.equal(exchangeRequest.frontier.candidates[0].eventDirection, "exchange");
assert.equal(exchangeRequest.frontier.candidates[0].initialAtomCount, 1);
assert.equal(exchangeRequest.frontier.candidates[0].finalAtomCount, 1);
assert.notEqual(exchangeRequest.frontier.candidates[0].initialGeometrySha256,
  exchangeRequest.frontier.candidates[0].finalGeometrySha256);
await assert.rejects(() => buildFrozenActionBarrierRequest({
  generatedAt: "x", buildId: "test", scenarioId: "nacl", materialName: "NaCl",
  elements: ["Na", "Cl"], targetUsed: false,
  initialConfiguration: { structureSha256: sha,
    atoms: [{ siteId: 0, species: "Na", positionAngstrom: [0, 0, 0] }] },
  candidates: [{ ...hop, emittedSites: [{ species: "Cl", positionAngstrom: [2, 0, 0] }],
    candidateDigestSha256: "0".repeat(64) }],
}), /equal colored emitted\/removed populations/);
await assert.rejects(() => buildFrozenActionBarrierRequest({
  generatedAt: "x", buildId: "test", scenarioId: "nacl", materialName: "NaCl",
  elements: ["Na"], targetUsed: false,
  initialConfiguration: { structureSha256: sha,
    atoms: [{ siteId: 0, species: "Na", positionAngstrom: [0, 0, 0] }] },
  candidates: [{ ...exchange, emittedSites: [{ species: "Na", positionAngstrom: [2, 0, 0] }],
    candidateDigestSha256: "0".repeat(64) }],
}), /differently colored/);
await assert.rejects(() => buildFrozenActionBarrierRequest({
  generatedAt: "x", buildId: "test", scenarioId: "nacl", materialName: "NaCl", elements: ["Na"],
  candidates: [{ ...detach, removedSites: [{ species: "Na", positionAngstrom: [9, 0, 0] }],
    candidateDigestSha256: "0".repeat(64) }], targetUsed: false,
  initialConfiguration: { structureSha256: sha,
    atoms: [{ siteId: 0, species: "Na", positionAngstrom: [0, 0, 0] }] },
}), /absent/);

console.log("external action barrier contract: passed");
