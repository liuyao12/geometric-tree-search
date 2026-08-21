import assert from "node:assert/strict";
import {
  canonicalPolycubeKey,
  enumeratePolycubes,
  isChiralPolycube,
  polycubeSymmetries,
  POLYCUBE_ISOMETRY_COUNT,
  POLYCUBE_ROTATION_COUNT
} from "../assets/polycube-enumerator.js";
import {
  polycubeCoronaBoundaryKey,
  searchFirstPolycubeCorona,
  searchPolycubeCorona
} from "../assets/polycube-corona-search.js";
import { findPolycubeBoxTiling } from "../assets/polycube-box-tiler.js";
import {
  findPolycubeCyclicTiling,
  findPolycubePeriodicTiling,
  verifyPolycubePeriodicCertificate
} from "../assets/polycube-periodic-tiler.js";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";

assert.equal(POLYCUBE_ROTATION_COUNT, 24);
assert.equal(POLYCUBE_ISOMETRY_COUNT, 48);
assert.equal(polycubeSymmetries([[0, 0, 0]]).length, 24);

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

const unresolvedP9 = POLYCUBE_GCTS_CANDIDATES.find(candidate => candidate.id === "p9-42947");
const periodicP9 = POLYCUBE_GCTS_CANDIDATES.find(candidate => candidate.id === "p9-43172");
assert.ok(unresolvedP9 && periodicP9);
assert.equal(unresolvedP9.mirror_equivalent_id, "p9-42969");
assert.equal(periodicP9.mirror_equivalent_id, "p9-43188");
assert.equal(unresolvedP9.screening.periodic_hnf_max_motif_tiles, 13);
assert.equal(periodicP9.screening.quotient_determinant, 72);

const chair = [[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 1, 1], [1, 0, 0], [1, 0, 1], [1, 1, 0]];
const rotatedChair = chair.map(([x, y, z]) => [z, x, y]);
assert.equal(canonicalPolycubeKey(chair), canonicalPolycubeKey(rotatedChair));
const lTricube = [[0, 0, 0], [1, 0, 0], [0, 1, 0]];
assert.equal(findPolycubeCyclicTiling([[0, 0, 0]]).certified, true);
assert.equal(findPolycubePeriodicTiling(lTricube, { maxCopies: 2 }).certified, true);
const resumedPeriodicRange = findPolycubePeriodicTiling(unresolvedP9.voxels, {
  minCopies: 3,
  maxCopies: 3,
  nodeLimit: 100_000,
  timeLimitMs: 5_000
});
assert.equal(resumedPeriodicRange.stopped_by, null);
assert.equal(resumedPeriodicRange.min_copies, 3);
assert.equal(resumedPeriodicRange.max_copies, 3);
assert.equal(resumedPeriodicRange.hnf_visited, 1210);
assert.deepEqual(resumedPeriodicRange.hnf_exhausted_by_copies, { 3: 1210 });
const exactOneCopyRange = findPolycubePeriodicTiling(unresolvedP9.voxels, {
  minCopies: 1,
  maxCopies: 1,
  nodeLimit: 100_000,
  timeLimitMs: 5_000
});
assert.equal(exactOneCopyRange.min_copies, 1);
assert.equal(exactOneCopyRange.certified, false);
assert.equal(exactOneCopyRange.stopped_by, null);
assert.equal(exactOneCopyRange.hnf_visited, 130);
assert.deepEqual(exactOneCopyRange.hnf_exhausted_by_copies, { 1: 130 });
const noncyclicOneTilePolycube = [
  [0, 0, 0], [0, 0, 1], [0, 0, 2],
  [0, 1, 0], [0, 1, 1], [0, 1, 2],
  [0, 2, 1], [0, 3, 1]
];
assert.equal(
  findPolycubeCyclicTiling(noncyclicOneTilePolycube).certified,
  false,
  "the fast cyclic preflight intentionally misses this non-cyclic quotient"
);
const noncyclicOneTileCertificate = findPolycubePeriodicTiling(noncyclicOneTilePolycube, {
  minCopies: 1,
  maxCopies: 1,
  nodeLimit: 100_000,
  timeLimitMs: 5_000
});
assert.equal(noncyclicOneTileCertificate.certified, true);
assert.equal(noncyclicOneTileCertificate.copies, 1);
assert.deepEqual(noncyclicOneTileCertificate.period_vectors, [[2, 0, 0], [1, 2, 0], [1, 0, 2]]);
assert.equal(
  verifyPolycubePeriodicCertificate(noncyclicOneTilePolycube, noncyclicOneTileCertificate).verified,
  true,
  "the independent quotient verifier must replay the non-cyclic one-tile certificate"
);
const lTricubeBox = findPolycubeBoxTiling(lTricube, { maxCopies: 2, timeLimitMs: 1000 });
assert.equal(lTricubeBox.certified, true, "two L tricubes must tile a finite box");
assert.equal(lTricubeBox.copies, 2);
assert.equal(lTricubeBox.isohedral.certified, true, "the repeated box tiling must be tile-transitive");
assert.equal(
  verifyPolycubePeriodicCertificate(lTricube, lTricubeBox).verified,
  true,
  "the independent quotient verifier must replay a two-copy box certificate"
);
const cyclicCube = findPolycubeCyclicTiling([[0, 0, 0]]);
assert.equal(verifyPolycubePeriodicCertificate([[0, 0, 0]], cyclicCube).verified, true);
assert.equal(
  verifyPolycubePeriodicCertificate([[0, 0, 0]], {
    ...cyclicCube,
    period_vectors: [[2, 0, 0], [0, 1, 0], [0, 0, 1]]
  }).verified,
  false,
  "a certificate with the wrong covolume must be rejected"
);

const cubeCorona = searchFirstPolycubeCorona([[0, 0, 0]], { nodeLimit: 1000, timeLimitMs: 1000 });
assert.equal(cubeCorona.success, true, "a cube must have a six-cube first corona");
assert.equal(cubeCorona.corona.length, 6);
assert.equal(
  polycubeCoronaBoundaryKey([[0, 0, 0]], cubeCorona.corona, 1),
  "",
  "the unit-cube first corona has no protruding boundary occupancy"
);
const extendedCubeCorona = searchPolycubeCorona([[0, 0, 0]], {
  layers: 2,
  fixedPlacements: cubeCorona.corona,
  nodeLimit: 1000,
  timeLimitMs: 1000
});
assert.equal(extendedCubeCorona.success, true, "a fixed first cube corona must extend to radius two");
assert.equal(extendedCubeCorona.fixed_placements, 6);
assert.equal(extendedCubeCorona.resolved_fixed_conflict, null);
const rejectedCubeCorona = searchPolycubeCorona([[0, 0, 0]], {
  layers: 1,
  nodeLimit: 1000,
  timeLimitMs: 1000,
  nogoods: true,
  acceptSolution: () => ({ accept: false, nogood_placement_indices: [0] })
});
assert.equal(rejectedCubeCorona.exhausted, true, "rejecting the cube's unique corona must exhaust the search");
assert.equal(rejectedCubeCorona.solutions_rejected, 1);
assert.equal(rejectedCubeCorona.nogood_clauses, 1);
assert.throws(
  () => searchPolycubeCorona(lTricube, {
    layers: 1,
    fixedPlacements: [{ cells: [[10, 0, 0], [11, 0, 0], [12, 0, 0]] }]
  }),
  /not a congruent tile copy/,
  "conditional corona proofs must reject malformed fixed placements"
);

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
const ringThirdCoronaWithNogoods = searchPolycubeCorona(ringOctacube, {
  layers: 3,
  nodeLimit: 500_000,
  timeLimitMs: 15_000,
  nogoods: true,
  returnNogoods: true
});
assert.equal(ringThirdCoronaWithNogoods.success, true);
assert.ok(ringThirdCoronaWithNogoods.nogood_clauses > 0);
assert.ok(ringThirdCoronaWithNogoods.nogood_prunes > 0);
assert.ok(ringThirdCoronaWithNogoods.nodes < ringThirdCorona.nodes);
const ringThirdCoronaWithCarriedNogoods = searchPolycubeCorona(ringOctacube, {
  layers: 3,
  seed: 1,
  nodeLimit: 500_000,
  timeLimitMs: 15_000,
  nogoods: true,
  initialNogoodPlacementKeys: ringThirdCoronaWithNogoods.nogood_clause_keys
});
assert.equal(ringThirdCoronaWithCarriedNogoods.success, true);
assert.ok(ringThirdCoronaWithCarriedNogoods.initial_nogood_clauses > 0);

const unresolvedRadiusFour = searchPolycubeCorona(unresolvedP9.voxels, {
  layers: 4,
  seed: 3,
  nodeLimit: 2_000_000,
  timeLimitMs: 15_000,
  nogoods: true
});
assert.equal(unresolvedRadiusFour.success, true);
const trappedRadiusFour = searchPolycubeCorona(unresolvedP9.voxels, {
  layers: 5,
  seed: 3,
  fixedPlacements: unresolvedRadiusFour.corona,
  nodeLimit: 100_000,
  timeLimitMs: 1000,
  nogoods: true
});
assert.equal(trappedRadiusFour.exhausted, true);
assert.equal(trappedRadiusFour.fixed_obstruction_nogood.candidate_rows_blocked, 72);
assert.equal(trappedRadiusFour.fixed_obstruction_nogood.fixed_placement_indices.length, 2);

const resolvedConflictHexacube = [
  [0, 0, 0], [0, 0, 1], [0, 1, 0],
  [1, 0, 1], [1, 1, 0], [1, 1, 1]
];
const resolvedConflictFirstCorona = searchPolycubeCorona(resolvedConflictHexacube, {
  layers: 1,
  nodeLimit: 50_000,
  timeLimitMs: 5_000
});
assert.equal(resolvedConflictFirstCorona.success, true);
const resolvedConflictSecondCorona = searchPolycubeCorona(resolvedConflictHexacube, {
  layers: 2,
  fixedPlacements: resolvedConflictFirstCorona.corona,
  nodeLimit: 500_000,
  timeLimitMs: 5_000,
  nogoods: true
});
assert.equal(resolvedConflictSecondCorona.exhausted, true);
assert.equal(resolvedConflictSecondCorona.fixed_obstruction_nogood.kind, "resolved_subtree_conflict");
assert.equal(resolvedConflictSecondCorona.fixed_obstruction_nogood.target_cell, null);
assert.deepEqual(resolvedConflictSecondCorona.fixed_obstruction_nogood.fixed_placement_indices, [2, 3, 6]);
const resolvedConflictReplay = searchPolycubeCorona(resolvedConflictHexacube, {
  layers: 2,
  fixedPlacements: resolvedConflictSecondCorona.fixed_obstruction_nogood.fixed_placement_indices
    .map(index => resolvedConflictFirstCorona.corona[index]),
  nodeLimit: 500_000,
  timeLimitMs: 5_000,
  nogoods: true
});
assert.equal(
  resolvedConflictReplay.exhausted,
  true,
  "the resolved outer-only conflict must independently reproduce the obstruction"
);
const incompleteResolvedConflict = searchPolycubeCorona(resolvedConflictHexacube, {
  layers: 2,
  fixedPlacements: resolvedConflictFirstCorona.corona,
  nodeLimit: 1,
  timeLimitMs: 5_000,
  nogoods: true
});
assert.equal(incompleteResolvedConflict.exhausted, false);
assert.equal(incompleteResolvedConflict.resolved_fixed_conflict, null);

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
