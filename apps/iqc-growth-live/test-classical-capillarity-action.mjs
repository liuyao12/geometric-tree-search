import assert from "node:assert/strict";
import { buildNormalizedWulffGeometry } from "./external-interfacial-energy.mjs";
import { buildClassicalNucleationWork } from "./classical-nucleation-evidence.mjs";
import { evaluateClassicalCapillarityAction, matchedClassicalCapillarityRankingAudit }
  from "./classical-capillarity-action.mjs";

const directions = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
const orientations = directions.map((normal, index) => ({ orientationId: `n${index}`, normal,
  interfacialFreeEnergy: .2, uncertainty: .002 }));
const interfacial = { responseAccepted: true, targetUsed: false, structureSha256: "a".repeat(64),
  responseSha256: "b".repeat(64), intrinsicDimension: 3, orientations,
  geometry: buildNormalizedWulffGeometry(orientations, 3) };
const bulk = { responseAccepted: true, targetUsed: false, structureSha256: "a".repeat(64),
  interfacialEnergyResponseSha256: "b".repeat(64), intrinsicDimension: 3,
  requestSha256: "c".repeat(64), phases: { parent: "liquid", nucleus: "solid" },
  temperatureKelvin: 300, bulkDrivingFreeEnergyDensity: 1e8, uncertainty: 1e6 };
const work = buildClassicalNucleationWork(interfacial, bulk);
const cube = (extent) => {
  const points = [];
  for (const x of [-extent, extent]) for (const y of [-extent, extent]) {
    for (const z of [-extent, extent]) points.push([x, y, z]);
  }
  return points;
};

const subcritical = evaluateClassicalCapillarityAction({
  occupiedPositionsAngstrom: cube(20), emittedPositionsAngstrom: [[22, 0, 0]],
  orientationBasisCartesian: [[1, 0, 0], [0, 1, 0], [0, 0, 1]], orientations,
  maximumAngleRadians: Math.PI / 4, nucleationWork: work });
assert.equal(subcritical.supported, true);
assert.equal(subcritical.regime, "subcritical");
assert.ok(subcritical.afterScaleAngstrom > subcritical.beforeScaleAngstrom);
assert.ok(subcritical.deltaWorkJoule > 0);
assert.ok(subcritical.score < 0);
assert.equal(subcritical.coordinateUnit, "angstrom");
assert.equal(subcritical.atomCountInferred, false);
assert.equal(subcritical.nucleationRateInferred, false);
assert.equal(subcritical.targetUsed, false);

const supercritical = evaluateClassicalCapillarityAction({
  occupiedPositionsAngstrom: cube(50), emittedPositionsAngstrom: [[60, 0, 0]],
  orientationBasisCartesian: [[1, 0, 0], [0, 1, 0], [0, 0, 1]], orientations,
  maximumAngleRadians: Math.PI / 4, nucleationWork: work });
assert.equal(supercritical.supported, true);
assert.equal(supercritical.regime, "supercritical");
assert.ok(supercritical.deltaWorkJoule < 0);
assert.ok(supercritical.score > 0);

const audit = matchedClassicalCapillarityRankingAudit([
  { candidateId: "subcritical", baselineScore: 1, regularizedScore: 1 + subcritical.score,
    supported: true, deltaWorkJoule: subcritical.deltaWorkJoule },
  { candidateId: "supercritical", baselineScore: .9, regularizedScore: .9 + supercritical.score,
    supported: true, deltaWorkJoule: supercritical.deltaWorkJoule },
  { candidateId: "abstain", baselineScore: .8, regularizedScore: .8,
    supported: false, deltaWorkJoule: null },
]);
assert.equal(audit.candidateSetIdentical, true);
assert.equal(audit.favorableCandidates, 1);
assert.equal(audit.unfavorableCandidates, 1);
assert.equal(audit.abstainedCandidates, 1);
assert.equal(audit.targetUsed, false);

const sheetOrientations = [[1, 0], [-1, 0], [0, 1], [0, -1]].map((normal, index) => ({
  orientationId: `e${index}`, normal, interfacialFreeEnergy: 2e-10, uncertainty: 1e-12 }));
const sheetInterface = { ...interfacial, intrinsicDimension: 2, orientations: sheetOrientations,
  geometry: buildNormalizedWulffGeometry(sheetOrientations, 2) };
const sheetWork = buildClassicalNucleationWork(sheetInterface, { ...bulk, intrinsicDimension: 2,
  bulkDrivingFreeEnergyDensity: .1, uncertainty: .001 });
const sheet = evaluateClassicalCapillarityAction({
  occupiedPositionsAngstrom: [[-10, -10, 0], [-10, 10, 0], [10, -10, 0], [10, 10, 0]],
  emittedPositionsAngstrom: [[12, 0, 0]],
  orientationBasisCartesian: [[1, 0, 0], [0, 1, 0]], orientations: sheetOrientations,
  maximumAngleRadians: Math.PI / 4, nucleationWork: sheetWork });
assert.equal(sheet.supported, true);
assert.equal(sheet.regime, "subcritical");
assert.ok(sheet.deltaWorkJoule > 0);
assert.equal(sheet.targetUsed, false);

assert.throws(() => evaluateClassicalCapillarityAction({ occupiedPositionsAngstrom: cube(20),
  emittedPositionsAngstrom: [[22, 0, 0]], orientationBasisCartesian: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
  orientations, maximumAngleRadians: Math.PI / 4, nucleationWork: { ...work, targetUsed: true } }),
/target-blind/);

console.log("conditional classical-capillarity action tests passed");
