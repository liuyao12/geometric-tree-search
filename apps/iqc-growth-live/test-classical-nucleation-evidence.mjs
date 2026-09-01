import assert from "node:assert/strict";
import { buildNormalizedWulffGeometry } from "./external-interfacial-energy.mjs";
import { buildBulkDrivingForceRequest, buildClassicalNucleationWork,
  BULK_DRIVING_FORCE_RESPONSE_SCHEMA, measureNormalizedWulffGeometry,
  validateBulkDrivingForceResponse } from "./classical-nucleation-evidence.mjs";

const STRUCTURE = "a".repeat(64); const INTERFACE = "b".repeat(64);
const REQUEST = "c".repeat(64); const SETTINGS = "d".repeat(64);
const directions = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
const orientations = directions.map((normal, index) => ({ orientationId: `n${index}`, normal,
  interfacialFreeEnergy: 0.2, uncertainty: 0.002 }));
const interfacial = { responseAccepted: true, targetUsed: false, structureSha256: STRUCTURE,
  responseSha256: INTERFACE, intrinsicDimension: 3, orientations,
  geometry: buildNormalizedWulffGeometry(orientations, 3) };

const request = buildBulkDrivingForceRequest({ generatedAt: "2026-09-01T00:00:00Z", buildId: "test",
  scenarioId: "fixture", materialName: "fixture", structureSha256: STRUCTURE,
  interfacialEnergyResponseSha256: INTERFACE, intrinsicDimension: 3,
  adjacentParentPhase: "liquid", temperatureKelvin: 300, targetUsed: false });
assert.equal(request.calculation.units, "joule per cubic metre");
assert.equal(request.safeguards.bulkDrivingForceNotInferredFromGrowth, true);

const response = { schema: BULK_DRIVING_FORCE_RESPONSE_SCHEMA, requestSha256: REQUEST,
  structureSha256: STRUCTURE, interfacialEnergyResponseSha256: INTERFACE, intrinsicDimension: 3,
  units: "joule per cubic metre", temperatureKelvin: 300,
  phases: { parent: "liquid", nucleus: "solid" },
  bulkDrivingFreeEnergyDensity: 1e8, uncertainty: 1e6,
  method: { family: "thermodynamic integration", program: "fixture", version: "1",
    settingsSha256: SETTINGS },
  validation: { passed: true, converged: true, uncertaintyReported: true, phaseIdentityMatched: true } };
const bulk = validateBulkDrivingForceResponse(response, { requestSha256: REQUEST,
  structureSha256: STRUCTURE, interfacialEnergyResponseSha256: INTERFACE,
  intrinsicDimension: 3, temperatureKelvin: 300, adjacentParentPhase: "liquid" });
const measured = measureNormalizedWulffGeometry(interfacial);
assert.ok(Math.abs(measured.normalizedContent - 8) < 1e-9);
assert.ok(Math.abs(measured.interfacialCoefficient - 4.8) < 1e-9);
assert.ok(measured.wulffIdentityRelativeResidual < 1e-12);
const work = buildClassicalNucleationWork(interfacial, bulk);
assert.ok(Math.abs(work.criticalScaleNanometre - 4) < 1e-9);
assert.ok(Math.abs(work.barrierJoule - 2.56e-17) < 1e-28);
assert.equal(work.workProfile.length, 81);
assert.equal(work.criticalAtomCountInferred, false);
assert.equal(work.nucleationRateInferred, false);
assert.equal(work.targetUsed, false);
assert.ok(work.workProfile[20].workJoule > work.workProfile[19].workJoule);
assert.ok(work.workProfile[21].workJoule < work.workProfile[20].workJoule);

const sheetOrientations = [[1, 0], [-1, 0], [0, 1], [0, -1]].map((normal, index) => ({
  orientationId: `e${index}`, normal, interfacialFreeEnergy: 2e-10, uncertainty: 1e-12 }));
const sheetInterface = { ...interfacial, intrinsicDimension: 2, orientations: sheetOrientations,
  geometry: buildNormalizedWulffGeometry(sheetOrientations, 2) };
const sheetBulk = { ...bulk, intrinsicDimension: 2, units: "joule per square metre",
  bulkDrivingFreeEnergyDensity: 0.1, uncertainty: 0.001 };
const sheetWork = buildClassicalNucleationWork(sheetInterface, sheetBulk);
assert.ok(Math.abs(sheetWork.criticalScaleNanometre - 2) < 1e-9);
assert.equal(sheetWork.intrinsicDimension, 2);

assert.throws(() => buildBulkDrivingForceRequest({ ...request, targetUsed: true }), /growth target/);
assert.throws(() => validateBulkDrivingForceResponse({ ...response, bulkDrivingFreeEnergyDensity: 2e6,
  uncertainty: 1e6 }, { requestSha256: REQUEST, structureSha256: STRUCTURE,
  interfacialEnergyResponseSha256: INTERFACE, intrinsicDimension: 3,
  temperatureKelvin: 300, adjacentParentPhase: "liquid" }), /three-sigma/);
assert.throws(() => validateBulkDrivingForceResponse({ ...response,
  phases: { parent: "solid", nucleus: "liquid" } }, { requestSha256: REQUEST,
  structureSha256: STRUCTURE, interfacialEnergyResponseSha256: INTERFACE,
  intrinsicDimension: 3, temperatureKelvin: 300, adjacentParentPhase: "liquid" }), /parent phase/);
assert.throws(() => buildClassicalNucleationWork(interfacial,
  { ...bulk, interfacialEnergyResponseSha256: "f".repeat(64) }), /not bound/);

console.log("conditional classical-nucleation evidence tests passed");
