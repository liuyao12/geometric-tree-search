import assert from "node:assert/strict";
import {
  buildClassicalNucleationKineticsRequest,
  validateClassicalNucleationKineticsResponse,
  buildConditionalClassicalNucleationRate,
  evaluatePoissonNucleationWindow,
} from "./classical-nucleation-kinetics.mjs";

const hex = (character) => character.repeat(64);
const work = {
  conditionalClassicalModel: true,
  targetUsed: false,
  intrinsicDimension: 3,
  structureSha256: hex("a"),
  interfacialEnergyResponseSha256: hex("b"),
  bulkDrivingForceRequestSha256: hex("c"),
  parentPhase: "liquid",
  nucleusPhase: "fcc solid",
  temperatureKelvin: 1000,
  barrierJoule: 30 * 1.380649e-23 * 1000,
  barrierUncertaintyElectronVolt: .001,
  criticalScaleMetre: 4e-9,
};

const request = buildClassicalNucleationKineticsRequest({
  generatedAt: "2026-09-01T00:00:00.000Z",
  buildId: "test",
  scenarioId: "nacl",
  materialName: "NaCl",
  nucleationWork: work,
  workSha256: hex("d"),
  targetUsed: false,
});
assert.equal(request.calculation.definition,
  "J = rho_site * Z * f_plus * exp[-DeltaG_star/(k_B T)]");
assert.equal(request.safeguards.barrierAloneCannotProduceARate, true);

const response = {
  schema: "gcts-classical-nucleation-kinetics-response-v1",
  requestSha256: hex("e"),
  workSha256: hex("d"),
  structureSha256: hex("a"),
  intrinsicDimension: 3,
  temperatureKelvin: 1000,
  phases: { parent: "liquid", nucleus: "fcc solid" },
  siteDensity: 1e28,
  siteDensityUnits: "nucleation sites per cubic metre",
  siteDensityUncertainty: 1e26,
  zeldovichFactor: .02,
  zeldovichFactorUncertainty: .001,
  attachmentFrequencyPerSecond: 1e12,
  attachmentFrequencyUncertaintyPerSecond: 1e10,
  reactionCoordinate: { name: "largest crystalline cluster", criticalValue: 512,
    definition: "connected fcc-like particles" },
  method: { family: "rare-event simulation", program: "fixture", version: "1",
    settingsSha256: hex("f") },
  validation: { passed: true, converged: true, uncertaintiesReported: true,
    reactionCoordinateValidated: true, steadyStateAssumptionDeclared: true,
    homogeneousNucleationDeclared: true },
};
const expected = { requestSha256: hex("e"), workSha256: hex("d"),
  structureSha256: hex("a"), intrinsicDimension: 3, temperatureKelvin: 1000,
  parentPhase: "liquid", nucleusPhase: "fcc solid" };
const kinetics = validateClassicalNucleationKineticsResponse(response, expected);
const rate = buildConditionalClassicalNucleationRate(work, kinetics);
const expectedLog = Math.log(1e28) + Math.log(.02) + Math.log(1e12) - 30;
assert.ok(Math.abs(rate.logRateDensityPerSi - expectedLog) < 1e-12);
assert.equal(rate.growthRankingChanged, false);
const window = evaluatePoissonNucleationWindow(rate, 1e-6, 1);
assert.ok(Math.abs(window.logExpectedEventCount - (expectedLog + Math.log(1e-18))) < 1e-12);
assert.ok(window.atLeastOneEventProbability >= 0 && window.atLeastOneEventProbability <= 1);
assert.equal(window.physicalClockIntegrated, false);

assert.throws(() => validateClassicalNucleationKineticsResponse(
  { ...response, zeldovichFactorUncertainty: .01 }, expected), /three sigma/);
assert.throws(() => validateClassicalNucleationKineticsResponse(
  { ...response, workSha256: hex("9") }, expected), /not bound/);
assert.throws(() => buildClassicalNucleationKineticsRequest({ nucleationWork: work,
  workSha256: hex("d"), materialName: "x", targetUsed: true }), /cannot use a growth target/);

const work2d = { ...work, intrinsicDimension: 2 };
const request2d = buildClassicalNucleationKineticsRequest({ generatedAt: "x", buildId: "x",
  scenarioId: "sheet", materialName: "sheet", nucleationWork: work2d,
  workSha256: hex("d") });
assert.equal(request2d.calculation.siteDensityUnits, "nucleation sites per square metre");

console.log("classical nucleation kinetics numerical tests passed");
