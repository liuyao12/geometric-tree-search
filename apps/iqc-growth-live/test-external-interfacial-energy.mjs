import assert from "node:assert/strict";
import { buildInterfacialEnergyRequest, buildNormalizedWulffGeometry,
  INTERFACIAL_ENERGY_RESPONSE_SCHEMA, interfacialEnergySha256,
  validateInterfacialEnergyResponse } from "./external-interfacial-energy.mjs";

const SHA = "a".repeat(64);
const SETTINGS = "b".repeat(64);

function orientations3d(energies = [1, 1, 1, 1, 1, 1]) {
  return [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]
    .map((normal, index) => ({ orientationId: `n${index}`, normal,
      interfacialFreeEnergy: energies[index], uncertainty: 0.01 }));
}

function response(orientations, dimension = 3) {
  return {
    schema: INTERFACIAL_ENERGY_RESPONSE_SCHEMA, requestSha256: SHA, structureSha256: SHA,
    intrinsicDimension: dimension,
    interface: { adjacentPhase: "vacuum", temperatureKelvin: 300 },
    method: { family: "slab free energy", program: "fixture", version: "1",
      settingsSha256: SETTINGS },
    validation: { passed: true, converged: true, uncertaintyReported: true,
      orientationSetPredeclared: true },
    units: dimension === 3 ? "joule per square metre" : "joule per metre",
    orientations,
  };
}

const request = buildInterfacialEnergyRequest({ generatedAt: "2026-08-31T00:00:00Z", buildId: "test",
  scenarioId: "fixture", materialName: "fixture", elements: ["Na", "Cl"], structureSha256: SHA,
  intrinsicDimension: 3, targetUsed: false });
assert.equal(request.safeguards.morphologyUsedToInferInterfacialEnergy, false);
assert.equal(request.safeguards.orientedNormalsNotSilentlyInversionSymmetrized, true);
assert.deepEqual(request.specimen.orientationBasisCartesian, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]);
assert.equal((await interfacialEnergySha256(request)).length, 64);
assert.throws(() => buildInterfacialEnergyRequest({ generatedAt: "now", buildId: "test",
  scenarioId: "2d", materialName: "sheet", elements: ["C"], structureSha256: SHA,
  intrinsicDimension: 2 }), /orientation basis/);
const sheetRequest = buildInterfacialEnergyRequest({ generatedAt: "now", buildId: "test",
  scenarioId: "2d", materialName: "sheet", elements: ["C"], structureSha256: SHA,
  intrinsicDimension: 2, orientationBasisCartesian: [[1, 0, 0], [0, 1, 0]] });
assert.equal(sheetRequest.specimen.orientationBasisCartesian.length, 2);

const cube = validateInterfacialEnergyResponse(response(orientations3d()), {
  requestSha256: SHA, structureSha256: SHA, intrinsicDimension: 3,
});
assert.equal(cube.geometry.vertexCount, 8);
assert.equal(cube.geometry.facetCount, 6);
assert.equal(cube.geometry.completeEquilibriumShapeCertified, false);
assert.equal(cube.usedAsGrowthLaw, false);

const prism = buildNormalizedWulffGeometry(orientations3d([1, 1, 1, 1, 2, 2]), 3);
const extent = (axis) => Math.max(...prism.vertices.map((point) => point[axis]))
  - Math.min(...prism.vertices.map((point) => point[axis]));
assert.ok(Math.abs(extent(0) - 2) < 1e-7);
assert.ok(Math.abs(extent(2) - 4) < 1e-7);

const squareOrientations = [[1, 0], [-1, 0], [0, 1], [0, -1]].map((normal, index) => ({
  orientationId: `e${index}`, normal, interfacialFreeEnergy: index < 2 ? 1 : 1.5, uncertainty: 0.01,
}));
const rectangle = validateInterfacialEnergyResponse(response(squareOrientations, 2), {
  requestSha256: SHA, structureSha256: SHA, intrinsicDimension: 2,
});
assert.equal(rectangle.geometry.vertexCount, 4);
assert.equal(rectangle.geometry.facetCount, 4);

const angle = 0.731;
const rotation = [[Math.cos(angle), -Math.sin(angle), 0], [Math.sin(angle), Math.cos(angle), 0], [0, 0, 1]];
const rotate = (point) => rotation.map((row) => row.reduce((sum, value, index) => sum + value * point[index], 0));
const rotated = buildNormalizedWulffGeometry(orientations3d().map((entry) => ({ ...entry,
  normal: rotate(entry.normal) })), 3);
const distanceSpectrum = (geometry) => geometry.vertices.flatMap((first, index) =>
  geometry.vertices.slice(index + 1).map((second) => Math.hypot(...first.map((value, axis) => value - second[axis]))))
  .sort((a, b) => a - b);
distanceSpectrum(cube.geometry).forEach((value, index) => assert.ok(Math.abs(value
  - distanceSpectrum(rotated)[index]) < 1e-7));

assert.throws(() => buildNormalizedWulffGeometry(orientations3d().slice(0, 3), 3), /at least 4|unbounded/);
assert.throws(() => validateInterfacialEnergyResponse(response(orientations3d().map((entry, index) =>
  index === 0 ? { ...entry, uncertainty: 0.34 } : entry)), {
  requestSha256: SHA, structureSha256: SHA, intrinsicDimension: 3,
}), /three-sigma/);
assert.throws(() => validateInterfacialEnergyResponse(response([...orientations3d(), {
  ...orientations3d()[0], orientationId: "duplicate",
}]), { requestSha256: SHA, structureSha256: SHA, intrinsicDimension: 3 }), /duplicate oriented normals/);
assert.throws(() => buildInterfacialEnergyRequest({ materialName: "fixture", structureSha256: SHA,
  intrinsicDimension: 3, targetUsed: true }), /growth target/);

const permuted = buildNormalizedWulffGeometry([...orientations3d()].reverse(), 3);
assert.deepEqual(distanceSpectrum(permuted), distanceSpectrum(cube.geometry));

console.log("external interfacial-energy / Wulff geometry tests passed");
