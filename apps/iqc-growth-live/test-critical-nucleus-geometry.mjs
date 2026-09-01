import assert from "node:assert/strict";
import {
  buildCriticalNucleusGeometryRequest,
  validateCriticalNucleusGeometryResponse,
  embedCriticalNucleusAtScheduledEvents,
} from "./critical-nucleus-geometry.mjs";

const sha = character => character.repeat(64);
const schedule = {
  schema: "gcts-conditional-nucleation-schedule-v1",
  intrinsicDimension: 3,
  structureSha256: sha("a"),
  workSha256: sha("b"),
  kineticsRequestSha256: sha("c"),
  parentPhase: "liquid",
  nucleusPhase: "fcc-solid",
  temperatureKelvin: 950,
  characteristicLengthMetre: 1e-7,
  events: [
    { eventId: "nucleus-0001", eventTimeSeconds: 1e-3,
      normalizedPosition: [.5, .5, .5], positionMetre: [5e-8, 5e-8, 5e-8] },
    { eventId: "nucleus-0002", eventTimeSeconds: 2e-3,
      normalizedPosition: [.9999, .2, .3], positionMetre: [9.999e-8, 2e-8, 3e-8] },
  ],
  targetUsed: false,
  gctsSeedChanged: false,
};
const scheduleSha256 = sha("d");

const request = buildCriticalNucleusGeometryRequest({
  schedule,
  scheduleSha256,
  criticalScaleMetre: 2.5e-9,
  generatedAt: "2026-09-01T00:00:00.000Z",
  buildId: "20260901-422",
  scenarioId: "al-fcc",
  materialName: "Al",
  sourceProvenance: { kind: "unit fixture" },
  targetUsed: false,
});
assert.equal(request.safeguards.cntScaleDoesNotDetermineAtomCount, true);
assert.equal(request.expectedResponse.geometry.orientationDistribution,
  "isotropic-proper-rotation");

function response(overrides = {}) {
  return {
    schema: "gcts-critical-nucleus-geometry-response-v1",
    requestSha256: sha("e"),
    scheduleSha256,
    workSha256: schedule.workSha256,
    structureSha256: schedule.structureSha256,
    intrinsicDimension: 3,
    temperatureKelvin: 950,
    phases: { parent: "liquid", nucleus: "fcc-solid" },
    geometry: {
      coordinateUnits: "angstrom",
      periodic: false,
      orientationDistribution: "isotropic-proper-rotation",
      sites: [
        { siteId: "Al-1", species: "Al", positionAngstrom: [1, 1, 1],
          membershipProbability: .99, region: "core" },
        { siteId: "Al-2", species: "Al", positionAngstrom: [3, 1, 1],
          membershipProbability: .91, region: "interface" },
        { siteId: "Al-3", species: "Al", positionAngstrom: [1, 3, 1],
          membershipProbability: .88, region: "interface" },
        { siteId: "Al-4", species: "Al", positionAngstrom: [1, 1, 3],
          membershipProbability: .86, region: "interface" },
      ],
    },
    criticality: {
      reactionCoordinateName: "solidlike atom count",
      meanCommittor: .51,
      committorStandardError: .04,
      independentShootingTrajectories: 96,
      representativeSelection: "medoid of the pB in [0.45,0.55] ensemble",
    },
    method: { family: "transition-interface sampling", program: "RareEventX",
      version: "2.1", settingsSha256: sha("f"), classifier: "averaged q6" },
    validation: { passed: true, converged: true, uncertaintiesReported: true,
      criticalityValidated: true, speciesAndUnitsValidated: true,
      representativeGeometryDeclared: true },
    ...overrides,
  };
}

const expected = {
  requestSha256: sha("e"),
  scheduleSha256,
  workSha256: schedule.workSha256,
  structureSha256: schedule.structureSha256,
  intrinsicDimension: 3,
  temperatureKelvin: 950,
  parentPhase: "liquid",
  nucleusPhase: "fcc-solid",
};
const evidence = validateCriticalNucleusGeometryResponse(response(), expected);
assert.equal(evidence.atomCount, 4);
assert.deepEqual(evidence.speciesCounts, { Al: 4 });
assert.ok(evidence.suppliedCentroidAngstrom.every(value => value === 1.5));
assert.ok(Math.abs(evidence.minimumPairDistanceAngstrom - 2) < 1e-12);
assert.equal(evidence.targetUsed, false);

const preview = embedCriticalNucleusAtScheduledEvents(schedule, evidence, {
  scheduleSha256,
  orientationSeed: 414,
  maximumEmbeddedEvents: 2,
});
const replay = embedCriticalNucleusAtScheduledEvents(schedule, evidence, {
  scheduleSha256,
  orientationSeed: 414,
  maximumEmbeddedEvents: 2,
});
assert.deepEqual(preview, replay);
assert.equal(preview.embeddedEventCount, 2);
assert.equal(preview.totalEmbeddedSites, 8);
assert.equal(preview.nucleiCommittedToGrowth, false);
assert.equal(preview.events[0].fullyInsideObservation, true);
assert.equal(preview.events[1].fullyInsideObservation, false);
const matrix = preview.events[0].pose.matrix;
for (let i = 0; i < 3; i += 1) {
  for (let j = 0; j < 3; j += 1) {
    const dot = matrix[i].reduce((sum, value, axis) => sum + value * matrix[j][axis], 0);
    assert.ok(Math.abs(dot - (i === j ? 1 : 0)) < 1e-12);
  }
}
const determinant = matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
  - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
  + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
assert.ok(Math.abs(determinant - 1) < 1e-12);
const firstDistances = preview.events[0].sites.slice(1).map(site =>
  Math.hypot(...site.localRotatedPositionAngstrom.map((value, axis) =>
    value - preview.events[0].sites[0].localRotatedPositionAngstrom[axis]))).sort();
assert.ok(firstDistances.every(value => Math.abs(value - 2) < 1e-12));
const changed = embedCriticalNucleusAtScheduledEvents(schedule, evidence, {
  scheduleSha256, orientationSeed: 415, maximumEmbeddedEvents: 2,
});
assert.notDeepEqual(changed.events[0].pose, preview.events[0].pose);

assert.throws(() => buildCriticalNucleusGeometryRequest({ schedule,
  scheduleSha256, criticalScaleMetre: 1e-9, materialName: "Al", targetUsed: true }),
  /cannot use a growth target/);
assert.throws(() => validateCriticalNucleusGeometryResponse(response({
  scheduleSha256: sha("0"),
}), expected), /scheduleSha256 mismatch/);
assert.throws(() => validateCriticalNucleusGeometryResponse(response({ criticality: {
  ...response().criticality, meanCommittor: .8, committorStandardError: .02,
} }), expected), /must contain 0.5/);
assert.throws(() => validateCriticalNucleusGeometryResponse(response({ geometry: {
  ...response().geometry,
  sites: response().geometry.sites.map((site, index) => index === 1
    ? { ...site, positionAngstrom: [1.01, 1, 1] } : site),
} }), expected), /implausibly close/);
assert.throws(() => embedCriticalNucleusAtScheduledEvents(schedule,
  { ...evidence, targetUsed: true }, { scheduleSha256 }), /target-blind/);

const schedule2d = { ...schedule, intrinsicDimension: 2,
  events: [{ eventId: "nucleus-0001", eventTimeSeconds: 1,
    normalizedPosition: [.5, .5], positionMetre: [5e-8, 5e-8] }] };
const request2d = buildCriticalNucleusGeometryRequest({ schedule: schedule2d,
  scheduleSha256, criticalScaleMetre: 1e-9, generatedAt: "now", buildId: "414",
  scenarioId: "sheet", materialName: "2D sheet" });
assert.equal(request2d.expectedResponse.geometry.orientationDistribution, "uniform-in-plane");

console.log("critical nucleus geometry: all tests passed");
