import assert from "node:assert/strict";
import { discoverIrregularCover } from "../apps/iqc-growth-live/irregular-cover.js";

function periodicDistance(points, side) {
  return (first, second) => Math.sqrt(points[first].reduce((sum, value, axis) => {
    let delta = points[second][axis] - value;
    delta -= Math.round(delta / side) * side;
    return sum + delta * delta;
  }, 0));
}

function orientedVolume(points, vector = (first, second) => points[second].map((value, axis) => value - points[first][axis])) {
  return (first, second, third, fourth) => {
    const a = vector(first, second), b = vector(first, third), c = vector(first, fourth);
    return a[0] * (b[1] * c[2] - b[2] * c[1])
      - a[1] * (b[0] * c[2] - b[2] * c[0])
      + a[2] * (b[0] * c[1] - b[1] * c[0]);
  };
}

function periodicVector(points, side) {
  return (first, second) => points[first].map((value, axis) => {
    let delta = points[second][axis] - value;
    delta -= Math.round(delta / side) * side;
    return delta;
  });
}

const side = 6;
const points = [];
const species = [];
for (let x = 0; x < side; x++) for (let y = 0; y < side; y++) for (let z = 0; z < side; z++) {
  points.push([x, y, z]);
  species.push((x + y + z) % 2 ? "Cl" : "Na");
}
const nacl = discoverIrregularCover({
  species,
  distance: periodicDistance(points, side),
  orientedVolume: orientedVolume(points, periodicVector(points, side)),
  referenceSpacing: 1,
  shellRadius: 1.1,
});
assert.equal(nacl.complete, true);
assert.equal(nacl.coveredAtoms, points.length);
assert.equal(nacl.residualAtoms, 0);
assert.equal(nacl.types.filter((type) => !type.residual).length, 2);
assert.deepEqual(new Set(nacl.types.filter((type) => !type.residual).map((type) => type.support.length)), new Set([7]));
assert.equal(nacl.selectedCenterFreeOccurrences, 0);
assert.ok(nacl.recurringCenterFreeClasses > 0);
assert.equal(nacl.replayConnectorCount, 0);
assert.equal(nacl.disconnectedReplayComponents, 0);
const reversedPoints = points.slice().reverse();
const reversed = discoverIrregularCover({
  species: species.slice().reverse(),
  distance: periodicDistance(reversedPoints, side),
  orientedVolume: orientedVolume(reversedPoints, periodicVector(reversedPoints, side)),
  referenceSpacing: 1,
  shellRadius: 1.1,
});
assert.deepEqual(
  nacl.types.map((type) => type.signature).sort(),
  reversed.types.map((type) => type.signature).sort(),
);
assert.equal(reversed.complete, true);
assert.equal(reversed.residualAtoms, 0);

const isolatedPoints = [[0, 0, 0], [3, 0, 0], [0, 4, 0], [0, 0, 5]];
const isolated = discoverIrregularCover({
  species: ["A", "B", "C", "D"],
  distance: (first, second) => Math.hypot(...isolatedPoints[first].map((value, axis) => isolatedPoints[second][axis] - value)),
  orientedVolume: orientedVolume(isolatedPoints),
  referenceSpacing: 3,
  shellRadius: .4,
});
assert.equal(isolated.complete, true);
assert.equal(isolated.coveredAtoms, isolatedPoints.length);
assert.equal(isolated.residualAtoms, isolatedPoints.length);
assert.ok(isolated.residualTypes.length >= 1);

const decoratedPoints = [];
const decoratedSpecies = [];
const motif = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]];
for (let copy = 0; copy < 2; copy++) {
  motif.forEach((point, index) => {
    decoratedPoints.push([point[0] + copy * 10, point[1], point[2]]);
    decoratedSpecies.push(["A", "B", "C", "D"][index]);
  });
  motif.forEach((point, index) => {
    const outward = [point[0] < .5 ? -1 : 1, point[1] < .5 ? -1 : 1, 0];
    decoratedPoints.push([point[0] + copy * 10 + outward[0] * .86, point[1] + outward[1] * .86, 0]);
    decoratedSpecies.push(`X${copy}-${index}`);
  });
}
const decorated = discoverIrregularCover({
  species: decoratedSpecies,
  distance: (first, second) => Math.hypot(...decoratedPoints[first]
    .map((value, axis) => decoratedPoints[second][axis] - value)),
  orientedVolume: orientedVolume(decoratedPoints),
  referenceSpacing: 1,
  shellRadius: 1.3,
});
assert.equal(decorated.complete, true);
assert.ok(decorated.recurringCenterFreeClasses > 0);
assert.ok(decorated.selectedCenterFreeOccurrences > 0);
assert.ok(decorated.residualAtoms > 0);
assert.ok(decorated.disconnectedReplayComponents > 0);

const glassPoints = [];
const glassSpecies = [];
for (let x = 0; x < 4; x++) for (let y = 0; y < 4; y++) for (let z = 0; z < 4; z++) {
  const index = glassPoints.length;
  glassPoints.push([
    x + Math.sin(index * 1.17) * .17,
    y + Math.sin(index * 1.91 + .3) * .17,
    z + Math.sin(index * 2.37 + .7) * .17,
  ]);
  glassSpecies.push(index % 5 < 3 ? "Cu" : "Zr");
}
const glass = discoverIrregularCover({
  species: glassSpecies,
  distance: (first, second) => Math.hypot(...glassPoints[first]
    .map((value, axis) => glassPoints[second][axis] - value)),
  orientedVolume: orientedVolume(glassPoints),
  referenceSpacing: 1,
  shellRadius: 1.3,
});
assert.equal(glass.complete, true);
assert.equal(glass.selectedCenterFreeOccurrences, 0);
assert.equal(glass.types.filter((type) => !type.residual).length, 0);
assert.equal(glass.residualAtoms, glassPoints.length);

const chiralPoints = [];
const chiralSpecies = [];
[[0, 1], [10, -1], [20, 1], [30, -1]].forEach(([offset, handedness]) => {
  [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, handedness]].forEach((point, index) => {
    chiralPoints.push([point[0] + offset, point[1], point[2]]);
    chiralSpecies.push(["A", "B", "C", "D"][index]);
  });
});
const chiral = discoverIrregularCover({
  species: chiralSpecies,
  distance: (first, second) => Math.hypot(...chiralPoints[first]
    .map((value, axis) => chiralPoints[second][axis] - value)),
  orientedVolume: orientedVolume(chiralPoints),
  referenceSpacing: 1,
  shellRadius: 1.5,
});
const chiralTypes = chiral.types.filter((type) => !type.residual);
assert.equal(chiralTypes.length, 2);
assert.ok(chiralTypes.some((type) => type.signature.endsWith("chi:+")));
assert.ok(chiralTypes.some((type) => type.signature.endsWith("chi:-")));

console.log("generic irregular complete-cover learner: passed", {
  naclTypes: nacl.types.length,
  naclPlacements: nacl.placements.length,
  centerFreeCandidates: nacl.recurringCenterFreeClasses,
  isolatedResiduals: isolated.residualAtoms,
  selectedCenterFree: decorated.selectedCenterFreeOccurrences,
  glassRecurringTypes: glass.types.filter((type) => !type.residual).length,
  chiralTypes: chiralTypes.length,
});
