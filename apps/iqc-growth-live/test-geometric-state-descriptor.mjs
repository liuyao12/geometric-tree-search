import assert from "node:assert/strict";
import { buildGeometricStateDescriptor, materialEndpointSites }
  from "./geometric-state-descriptor.mjs";

const octahedron = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0],
  [0, 0, 1], [0, 0, -1]].map((positionAngstrom, index) => ({
  species: index % 2 ? "Cl" : "Na", positionAngstrom,
}));
const descriptor = buildGeometricStateDescriptor(octahedron, { contactReach: 1.1 });
assert.equal(descriptor.atomCount, 6);
assert.equal(descriptor.rotationallyInvariant, true);
assert.ok(Number.isFinite(descriptor.steinhardtQ4));
assert.ok(Number.isFinite(descriptor.steinhardtQ6));
assert.equal(descriptor.chemicalBondClaimed, false);
assert.equal(descriptor.dimensionlessPowderScattering.qTimesMedianNearestNeighbor.length, 24);
assert.equal(descriptor.dimensionlessPowderScattering.unitWeightIntensity.length, 24);
assert.equal(descriptor.dimensionlessPowderScattering.pairCount, 15);
assert.equal(descriptor.dimensionlessPowderScattering.qDependentFormFactorsUsed, false);

const rotation = [[0, -1, 0], [1, 0, 0], [0, 0, 1]];
const transformed = [...octahedron].reverse().map((site) => ({ ...site,
  positionAngstrom: rotation.map((row) => row.reduce((sum, value, axis) =>
    sum + value * site.positionAngstrom[axis], 0)).map((value) => value + 7) }));
const transformedDescriptor = buildGeometricStateDescriptor(transformed,
  { contactReach: 1.1 });
for (const field of ["medianNearestNeighborAngstrom", "contactCount", "meanCoordination",
  "coordinationStandardDeviation", "steinhardtQ4", "steinhardtQ6"]) {
  assert.ok(Math.abs(descriptor[field] - transformedDescriptor[field]) < 1e-12, field);
}
assert.deepEqual(descriptor.dimensionlessPowderScattering.qTimesMedianNearestNeighbor,
  transformedDescriptor.dimensionlessPowderScattering.qTimesMedianNearestNeighbor);
descriptor.dimensionlessPowderScattering.unitWeightIntensity.forEach((value, index) => {
  assert.ok(Math.abs(value
    - transformedDescriptor.dimensionlessPowderScattering.unitWeightIntensity[index]) < 1e-12);
});

const path = { coordinateBearingImagesValidated: true,
  fixedMaterialSites: [{ species: "Na", positionAngstrom: [0, 0, 0] }],
  images: [
    { sites: [{ species: "Cl", domain: "reservoir", positionAngstrom: [2, 0, 0] }] },
    { sites: [{ species: "Cl", domain: "material", positionAngstrom: [1, 0, 0] }] },
  ] };
assert.equal(materialEndpointSites(path, "initial").length, 1);
assert.equal(materialEndpointSites(path, "final").length, 2);

console.log("global geometric state descriptor: ok");
