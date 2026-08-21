import assert from "node:assert/strict";
import {
  canonicalPolycubeKey,
  enumeratePolycubes,
  isChiralPolycube,
  POLYCUBE_ISOMETRY_COUNT,
  POLYCUBE_ROTATION_COUNT
} from "../assets/polycube-enumerator.js";
import { searchFirstPolycubeCorona, searchPolycubeCorona } from "../assets/polycube-corona-search.js";
import { findPolycubeBoxTiling } from "../assets/polycube-box-tiler.js";
import { findPolycubeCyclicTiling, findPolycubePeriodicTiling } from "../assets/polycube-periodic-tiler.js";

assert.equal(POLYCUBE_ROTATION_COUNT, 24);
assert.equal(POLYCUBE_ISOMETRY_COUNT, 48);

const expectedOneSidedCounts = [1, 1, 2, 8, 29];
const expectedFreeCounts = [1, 1, 2, 7, 23];
for (let size = 1; size <= expectedOneSidedCounts.length; size++) {
  assert.equal(
    enumeratePolycubes(size).length,
    expectedOneSidedCounts[size - 1],
    `unexpected one-sided polycube count at volume ${size}`
  );
  assert.equal(
    enumeratePolycubes(size, { includeReflections: true }).length,
    expectedFreeCounts[size - 1],
    `unexpected free polycube count at volume ${size}`
  );
}
assert.equal(enumeratePolycubes(5).filter(candidate => isChiralPolycube(candidate.voxels)).length, 12);

const chair = [[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 1, 1], [1, 0, 0], [1, 0, 1], [1, 1, 0]];
const rotatedChair = chair.map(([x, y, z]) => [z, x, y]);
assert.equal(canonicalPolycubeKey(chair), canonicalPolycubeKey(rotatedChair));
const lTricube = [[0, 0, 0], [1, 0, 0], [0, 1, 0]];
assert.equal(findPolycubeCyclicTiling([[0, 0, 0]]).certified, true);
assert.equal(findPolycubePeriodicTiling(lTricube, { maxCopies: 2 }).certified, true);
const lTricubeBox = findPolycubeBoxTiling(lTricube, { maxCopies: 2, timeLimitMs: 1000 });
assert.equal(lTricubeBox.certified, true, "two L tricubes must tile a finite box");
assert.equal(lTricubeBox.copies, 2);
assert.equal(lTricubeBox.isohedral.certified, true, "the repeated box tiling must be tile-transitive");

const cubeCorona = searchFirstPolycubeCorona([[0, 0, 0]], { nodeLimit: 1000, timeLimitMs: 1000 });
assert.equal(cubeCorona.success, true, "a cube must have a six-cube first corona");
assert.equal(cubeCorona.corona.length, 6);

const ringOctacube = [];
for (let x = 0; x < 3; x++) for (let y = 0; y < 3; y++) {
  if (x !== 1 || y !== 1) ringOctacube.push([x, y, 0]);
}
const ringCorona = searchFirstPolycubeCorona(ringOctacube, {
  nodeLimit: 2_000_000,
  timeLimitMs: 10_000
});
assert.equal(ringCorona.success, true, "the ring octacube survives a first-corona screen");
const ringThirdCorona = searchPolycubeCorona(ringOctacube, {
  layers: 3,
  nodeLimit: 500_000,
  timeLimitMs: 15_000
});
assert.equal(ringThirdCorona.success, true, "the ring octacube survives three exact corona layers");

const cappedRingDecacube = [...ringOctacube, [1, 0, 1], [1, 1, 1]];
const cappedRingCorona = searchFirstPolycubeCorona(cappedRingDecacube, {
  nodeLimit: 2_000_000,
  timeLimitMs: 10_000
});
assert.equal(cappedRingCorona.exhausted, true, "the capped ring must have a finite first-corona obstruction");
assert.equal(cappedRingCorona.certified_non_tiler, true);

console.log("Polycube enumerator regression passed", {
  counts: expectedOneSidedCounts,
  freeCounts: expectedFreeCounts,
  rotations: POLYCUBE_ROTATION_COUNT,
  isometries: POLYCUBE_ISOMETRY_COUNT,
  ringNodes: ringCorona.nodes,
  ringThirdCoronaNodes: ringThirdCorona.nodes,
  cappedRingNodes: cappedRingCorona.nodes
});
