import assert from "node:assert/strict";
import { bindValidatedTrajectoryGeometry, buildValidatedTrajectoryGeometryRuntime }
  from "../apps/iqc-growth-live/external-trajectory-geometry.mjs";

const audit = {
  quantityId: "trajectory", configurationRole: "observation", validationPassed: true,
  targetCoordinatesEmbedded: false, configurationSha256: "a".repeat(64), requestSha256: "b".repeat(64),
  method: { family: "MD", program: "solver", version: "1", settingsSha256: "c".repeat(64) },
};
const reference = [[0, 0, 0], [2, 0, 0]];
const response = { results: { frames: [
  { timeSeconds: 0, positionsAngstrom: [[0, 0, 0], [2, 0, 0]] },
  { timeSeconds: 1, positionsAngstrom: [[1, 1, 0], [3, -1, 0]] },
  { timeSeconds: 2, positionsAngstrom: [[2, 0, 0], [4, 0, 0]] },
] } };
const runtime = buildValidatedTrajectoryGeometryRuntime(response, audit, "d".repeat(64), reference);
assert.equal(runtime.frameCount, 3);
assert.equal(runtime.timeSpanSeconds, 2);
assert.deepEqual(runtime.records.map((record) => record.endpointDisplacementAngstrom), [[0, 0, 0], [0, 0, 0]]);
assert.deepEqual(runtime.records.map((record) => record.maximumExcursionAngstrom), [1, 1]);
assert.equal(runtime.trajectoryProvenance.globalTranslationRemovedPerFrame, true);
assert.equal(runtime.trajectoryProvenance.usedAsPhysicalClock, false);

const atoms = [{ species: "A" }, { species: "B" }];
const binding = bindValidatedTrajectoryGeometry(atoms, runtime, .5);
assert.deepEqual(atoms.map((atom) => atom.observedRelaxationWorldSceneArray), [[0, 0, 0], [0, 0, 0]]);
assert.deepEqual(atoms.map((atom) => atom.externalTrajectoryMaximumExcursionAngstrom), [1, 1]);
assert.equal(binding.properPoseTransport, "delta_r_world = R_cluster delta_r_local");
assert.equal(binding.trajectoryIntegrated, false);

assert.throws(() => buildValidatedTrajectoryGeometryRuntime({ results: { frames: [
  { timeSeconds: 0, positionsAngstrom: [[.1, 0, 0], [2, 0, 0]] },
  { timeSeconds: 1, positionsAngstrom: [[0, 0, 0], [2, 0, 0]] },
] } }, audit, "d".repeat(64), reference), /reference frame does not match/);
assert.throws(() => buildValidatedTrajectoryGeometryRuntime(response,
  { ...audit, targetCoordinatesEmbedded: true }, "d".repeat(64), reference), /target-free/);

console.log("external trajectory geometry contract: passed");
