import assert from "node:assert/strict";
import { validateExternalPhysicsResponse } from "../apps/iqc-growth-live/external-physics-response.mjs";

const sha = "a".repeat(64);
const structureSha = "b".repeat(64);
const base = (quantityId, results) => ({
  schema: "gcts-external-physics-response-v1", requestSha256: sha, quantityId,
  configuration: { role: "observation", structureSha256: structureSha },
  method: { family: "reference calculation", program: "solver", version: "1",
    settingsSha256: "c".repeat(64) },
  validation: { passed: true, protocolMatchesRequest: true, independentHoldout: true,
    uncertaintyReported: true, convergenceReported: true },
  results,
  safeguards: { containsGrowthTargetCoordinates: false,
    geometricScoresUsedAsPhysicalLabels: false, searchStepsUsedAsPhysicalTime: false },
});
const expected = (quantityId) => ({ requestSha256: sha, quantityId,
  configurations: { observation: { structureSha256: structureSha, atomCount: 2 },
    growthSeed: { structureSha256: "d".repeat(64), atomCount: 1 } } });

const cases = {
  trajectory: { frames: [
    { timeSeconds: 0, positionsAngstrom: [[0, 0, 0], [1, 0, 0]] },
    { timeSeconds: 1e-12, positionsAngstrom: [[0, .1, 0], [1, .1, 0]] },
  ] },
  clock: { exposureSeconds: 2, eventCount: 4, censoredEventCount: 1, ratePerSecond: 2 },
  barrier: { initialState: "A", finalState: "B", energyProfileElectronVolt: [0, .8, .1],
    maximumForceElectronVoltPerAngstrom: .02 },
  "free-energy": { deltaFreeEnergyElectronVolt: -.2, uncertaintyElectronVolt: .03,
    temperatureKelvin: 300, ensemble: "NPT" },
  probability: { transitionCount: 8, exposureSeconds: 4, ratePerSecond: 2,
    independentTrajectoryCount: 3 },
  forces: { forceVectorsElectronVoltPerAngstrom: [[.1, 0, 0], [-.1, 0, 0]],
    totalEnergyElectronVolt: -3, stressTensorGigaPascal: [[1, 0, 0], [0, 1, 0], [0, 0, 1]] },
};

for (const [quantityId, results] of Object.entries(cases)) {
  const audit = validateExternalPhysicsResponse(base(quantityId, results), expected(quantityId));
  assert.equal(audit.validationPassed, true);
  assert.equal(audit.quantityId, quantityId);
  assert.equal(audit.eligibleAsTransferableLaw, false);
  assert.equal(audit.usedForCandidateRanking, false);
}

assert.throws(() => validateExternalPhysicsResponse(
  { ...base("forces", cases.forces), requestSha256: "e".repeat(64) }, expected("forces")), /request SHA/);
assert.throws(() => validateExternalPhysicsResponse(
  { ...base("forces", cases.forces), validation: { passed: true } }, expected("forces")), /validation gate/);
assert.throws(() => validateExternalPhysicsResponse(
  { ...base("forces", cases.forces), safeguards: { containsGrowthTargetCoordinates: true } }, expected("forces")), /safeguards/);
assert.throws(() => validateExternalPhysicsResponse(
  base("forces", { ...cases.forces, forceVectorsElectronVoltPerAngstrom: [[0, 0, 0]] }), expected("forces")), /2 site-resolved/);

console.log("external physics response contract: passed");
