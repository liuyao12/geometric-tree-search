import assert from "node:assert/strict";
import { buildExternalStateRelaxationRequest, stateRelaxationSha256,
  validateExternalStateRelaxationResponse } from "./external-state-relaxation.mjs";

const sites = [
  { atomId: 2, species: "Cl", positionAngstrom: [1, 0, 0] },
  { atomId: 1, species: "Na", positionAngstrom: [0, 0, 0] },
];
const request = await buildExternalStateRelaxationRequest({
  generatedAt: "2026-08-31T00:00:00.000Z", buildId: "test", materialName: "NaCl",
  sites, periodicBoundary: [false, false, false], boundary: { kind: "sphere", radiusAngstrom: 5 },
});
assert.equal(request.initialState.atomCount, 2);
assert.deepEqual(request.initialState.sites.map((site) => site.atomId), [1, 2]);
assert.equal(request.safeguards.atomCountMayChange, false);
assert.equal(request.safeguards.adoptionCreatesNewObservationRound, true);
assert.equal(request.responseContract.schema, "gcts-external-state-relaxation-response-v1");
assert.match(request.responseContract.geometryHashCanonicalization, /sites sorted by atomId/);

const finalSites = [
  { atomId: 1, species: "Na", positionAngstrom: [.1, 0, 0] },
  { atomId: 2, species: "Cl", positionAngstrom: [.9, 0, 0] },
];
const response = {
  schema: "gcts-external-state-relaxation-response-v1",
  requestSha256: request.requestSha256,
  initialGeometrySha256: request.initialState.geometrySha256,
  finalGeometrySha256: await stateRelaxationSha256(finalSites),
  finalSites, totalEnergy: -4.2, energyUnit: "eV",
  maximumResidualForce: .008, forceRms: .004, forceUnit: "eV/angstrom",
  converged: true, convergenceCriterion: "max force < 0.01 eV/angstrom",
  iterationCount: 14, method: "DFT", methodVersion: "1.0", settingsSha256: "a".repeat(64),
};
const validated = await validateExternalStateRelaxationResponse(response, request);
assert.equal(validated.audit.atomCountPreserved, true);
assert.equal(validated.audit.speciesPreserved, true);
assert.equal(validated.audit.displacement.movedAtomCount, 2);
assert.ok(Math.abs(validated.audit.displacement.rmsAngstrom - .1) < 1e-12);
assert.equal(validated.audit.targetUsed, false);

await assert.rejects(validateExternalStateRelaxationResponse({ ...response,
  finalSites: [{ ...finalSites[0], species: "Cl" }, finalSites[1]] }, request), /changed species/);
await assert.rejects(validateExternalStateRelaxationResponse({ ...response,
  finalSites: finalSites.slice(0, 1) }, request), /atom count/);
await assert.rejects(validateExternalStateRelaxationResponse({ ...response,
  converged: false }, request), /converged finite energy/);
await assert.rejects(validateExternalStateRelaxationResponse({ ...response,
  finalGeometrySha256: "b".repeat(64) }, request), /does not match/);
await assert.rejects(validateExternalStateRelaxationResponse(response, { ...request,
  materialName: "mutated" }), /request SHA-256/);

console.log("external post-leap state-relaxation contract tests passed");
