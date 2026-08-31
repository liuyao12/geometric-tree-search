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
assert.equal(request.responseContract.schema, "gcts-external-state-relaxation-response-v2");
assert.match(request.responseContract.geometryHashCanonicalization, /sites sorted by atomId/);

const finalSites = [
  { atomId: 1, species: "Na", positionAngstrom: [.1, 0, 0] },
  { atomId: 2, species: "Cl", positionAngstrom: [.9, 0, 0] },
];
const response = {
  schema: "gcts-external-state-relaxation-response-v2",
  requestSha256: request.requestSha256,
  initialGeometrySha256: request.initialState.geometrySha256,
  initialStateSha256: request.initialState.stateSha256,
  finalGeometrySha256: await stateRelaxationSha256(finalSites),
  finalStateSha256: await stateRelaxationSha256({ sites: finalSites,
    cellAngstrom: null, periodicBoundary: [false, false, false] }),
  finalSites, finalCellAngstrom: null, totalEnergy: -4.2, energyUnit: "eV",
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
assert.equal(validated.audit.cell.cellPolicy, "fixed");

const periodicSites = [
  { atomId: 0, species: "Si", positionAngstrom: [1, 1, 1] },
  { atomId: 1, species: "Si", positionAngstrom: [3, 3, 3] },
];
const initialCell = [[4, 0, 0], [0, 4, 0], [0, 0, 4]];
const finalCell = [[4.08, 0, 0], [0, 4.08, 0], [0, 0, 4.08]];
const variableRequest = await buildExternalStateRelaxationRequest({
  generatedAt: "2026-08-31T00:00:00.000Z", buildId: "test", materialName: "Si",
  sites: periodicSites, cellAngstrom: initialCell, periodicBoundary: [true, true, true],
  cellPolicy: "variable-isotropic-pressure", targetPressureGPa: 0,
});
const variableFinalSites = periodicSites.map((site) => ({ ...site,
  positionAngstrom: site.positionAngstrom.map((value) => value * 1.02) }));
const variableResponse = {
  ...response, requestSha256: variableRequest.requestSha256,
  initialGeometrySha256: variableRequest.initialState.geometrySha256,
  initialStateSha256: variableRequest.initialState.stateSha256,
  finalSites: variableFinalSites, finalCellAngstrom: finalCell,
  finalGeometrySha256: await stateRelaxationSha256(variableFinalSites),
  finalStateSha256: await stateRelaxationSha256({ sites: variableFinalSites,
    cellAngstrom: finalCell, periodicBoundary: [true, true, true] }),
  stressTensor: [[.01, 0, 0], [0, .01, 0], [0, 0, .01]], stressUnit: "GPa",
  stressConvention: "positive tension", targetPressureGPa: 0, maximumStressResidualGPa: .01,
};
const variableValidated = await validateExternalStateRelaxationResponse(variableResponse,
  variableRequest);
assert.equal(variableValidated.audit.cellRelaxationAuthorized, true);
assert.ok(Math.abs(variableValidated.audit.cell.volumeRatio - 1.02 ** 3) < 1e-12);
assert.ok(variableValidated.audit.cell.greenLagrangeStrainNorm > 0);
assert.ok(variableValidated.audit.displacement.nonAffineRmsAngstrom < 1e-12);
assert.ok(variableValidated.audit.displacement.affineRmsAngstrom > 0);
assert.equal(variableValidated.response.stress.maximumResidualGPa, .01);

const fixedPeriodicRequest = await buildExternalStateRelaxationRequest({
  generatedAt: "2026-08-31T00:00:00.000Z", buildId: "test", materialName: "Si",
  sites: periodicSites, cellAngstrom: initialCell, periodicBoundary: [true, true, true],
});
const fixedPeriodicResponse = {
  ...response, requestSha256: fixedPeriodicRequest.requestSha256,
  initialGeometrySha256: fixedPeriodicRequest.initialState.geometrySha256,
  initialStateSha256: fixedPeriodicRequest.initialState.stateSha256,
  finalSites: periodicSites, finalCellAngstrom: initialCell,
  finalGeometrySha256: await stateRelaxationSha256(periodicSites),
  finalStateSha256: await stateRelaxationSha256({ sites: periodicSites,
    cellAngstrom: initialCell, periodicBoundary: [true, true, true] }),
};
assert.equal((await validateExternalStateRelaxationResponse(fixedPeriodicResponse,
  fixedPeriodicRequest)).audit.cellPreserved, true);

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
await assert.rejects(buildExternalStateRelaxationRequest({
  generatedAt: "2026-08-31T00:00:00.000Z", buildId: "test", materialName: "Si",
  sites: periodicSites, cellAngstrom: initialCell, periodicBoundary: [true, false, true],
  cellPolicy: "variable-isotropic-pressure", targetPressureGPa: 0,
}), /fully periodic/);
await assert.rejects(validateExternalStateRelaxationResponse({ ...variableResponse,
  finalCellAngstrom: [[4.08, 0, 0], [0, 4.08, 0], [0, 0, -4.08]],
}, variableRequest), /cell handedness|state SHA-256/);
await assert.rejects(validateExternalStateRelaxationResponse({ ...variableResponse,
  maximumStressResidualGPa: -1 }, variableRequest), /stress residual/);
await assert.rejects(validateExternalStateRelaxationResponse({ ...fixedPeriodicResponse,
  finalCellAngstrom: finalCell }, fixedPeriodicRequest), /fixed-cell relaxation changed the cell/);
await assert.rejects(validateExternalStateRelaxationResponse({ ...variableResponse,
  stressTensor: [[0, 1, 0], [0, 0, 0], [0, 0, 0]] }, variableRequest), /symmetric/);

console.log("external post-leap state-relaxation contract tests passed");
