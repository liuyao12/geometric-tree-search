import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  canonicalPolycubeKey,
  enumeratePolycubes,
  isChiralPolycube,
  polycubeKey,
  polycubeOrientations,
  polycubeSymmetries,
  POLYCUBE_ISOMETRY_COUNT,
  POLYCUBE_ROTATION_COUNT
} from "../assets/polycube-enumerator.js";
import {
  enumeratePolycubeCoronaPlacements,
  polycubePlacementClauseOrbitKeys,
  polycubePlacementOrbitKeys,
  polycubeCoronaBoundaryKey,
  polycubeReciprocalPlacement,
  polycubeRootContactKey,
  searchFirstPolycubeCorona,
  searchPolycubeCorona,
  verifyPolycubeCoronaPatch
} from "../assets/polycube-corona-search.js";
import { findPolycubeBoxTiling } from "../assets/polycube-box-tiler.js";
import {
  findPolycubeCyclicTiling,
  findPolycubePeriodicTiling,
  verifyPolycubePeriodicCertificate
} from "../assets/polycube-periodic-tiler.js";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";

const volume10Through2 = JSON.parse(readFileSync(
  new URL("../data/polycube-volume10-periodic-through2-2026-08-20.json", import.meta.url),
  "utf8"
));
assert.equal(volume10Through2.enumeration.candidates, 346543);
assert.equal(volume10Through2.final.periodic, 322644);
assert.deepEqual(volume10Through2.final.periodic_by_motif_tiles, { "1": 112531, "2": 210113 });
assert.equal(volume10Through2.final.exactly_exhausted_survivors, 23899);
assert.equal(volume10Through2.timeout_retry.remaining_time_or_node_limits, 0);
assert.deepEqual(volume10Through2.protocol.hnf_candidates_exhausted_per_final_survivor, {
  "1_copy": 217,
  "2_copies": 1085,
  total: 1302
});

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
assert.equal(polycubeOrientations(unresolvedP9.voxels).length, 8);
const unresolvedFirstCoronaCatalog = enumeratePolycubeCoronaPlacements(unresolvedP9.voxels, 1);
assert.equal(unresolvedFirstCoronaCatalog.length, 605);
const unresolvedContactTypeKeys = [...new Set(unresolvedFirstCoronaCatalog.map(placement =>
  polycubeRootContactKey(unresolvedP9.voxels, placement)
))].sort();
assert.equal(unresolvedContactTypeKeys.length, 69);
const unresolvedContactTypeId = new Map(unresolvedContactTypeKeys.map((key, index) => [key, index]));
const activeContactTypes = new Set([3, 25, 29, 43, 44, 53]);
const activeReciprocalEdges = new Map();
const activeReciprocalPlacementOrbits = new Map();
for (const placement of unresolvedFirstCoronaCatalog) {
  const from = unresolvedContactTypeId.get(polycubeRootContactKey(unresolvedP9.voxels, placement));
  if (!activeContactTypes.has(from)) continue;
  const reciprocal = polycubeReciprocalPlacement(unresolvedP9.voxels, placement);
  assert.ok(reciprocal);
  assert.ok(polycubeOrientations(unresolvedP9.voxels).some(orientation =>
    orientation.key === polycubeKey(reciprocal.cells)
  ));
  const to = unresolvedContactTypeId.get(polycubeRootContactKey(unresolvedP9.voxels, reciprocal));
  const reciprocalOrbit = polycubePlacementOrbitKeys(unresolvedP9.voxels, reciprocal)[0];
  activeReciprocalPlacementOrbits.set(reciprocalOrbit, to);
  const key = `${from}->${to}`;
  activeReciprocalEdges.set(key, (activeReciprocalEdges.get(key) ?? 0) + 1);
}
assert.deepEqual([...activeReciprocalEdges].sort(), [
  ["25->36", 3], ["29->29", 3], ["3->44", 3], ["43->0", 3], ["43->17", 3],
  ["43->54", 3], ["43->58", 9], ["43->63", 3], ["44->3", 3], ["53->42", 3]
].sort());
const firstActivePlacement = unresolvedFirstCoronaCatalog.find(placement =>
  activeContactTypes.has(unresolvedContactTypeId.get(
    polycubeRootContactKey(unresolvedP9.voxels, placement)
  ))
);
const firstActivePlacementOrbit = polycubePlacementOrbitKeys(unresolvedP9.voxels, firstActivePlacement);
const firstActiveClauseOrbit = polycubePlacementClauseOrbitKeys(
  unresolvedP9.voxels,
  [firstActivePlacement.key]
);
assert.deepEqual(firstActiveClauseOrbit.map(clause => clause[0]), firstActivePlacementOrbit);
assert.equal(activeReciprocalPlacementOrbits.size, 12);
assert.equal([...activeReciprocalPlacementOrbits.values()].filter(type => activeContactTypes.has(type)).length, 3);
assert.deepEqual([...new Set(activeReciprocalPlacementOrbits.values())].sort((left, right) => left - right), [
  0, 3, 17, 29, 36, 42, 44, 54, 58, 63
]);
const unresolvedFirstCorona = searchPolycubeCorona(unresolvedP9.voxels, {
  layers: 1,
  nodeLimit: 100_000,
  timeLimitMs: 5_000
});
assert.equal(unresolvedFirstCorona.success, true);
const firstCoronaBoundaryKey = polycubeCoronaBoundaryKey(
  unresolvedP9.voxels,
  unresolvedFirstCorona.corona,
  1
);
const rootSymmetry = polycubeSymmetries(unresolvedP9.voxels)[1];
const symmetricFirstCorona = unresolvedFirstCorona.corona.map(placement => ({
  cells: placement.cells.map(cell => [0, 1, 2].map(axis =>
    rootSymmetry.matrix[axis][0] * cell[0]
    + rootSymmetry.matrix[axis][1] * cell[1]
    + rootSymmetry.matrix[axis][2] * cell[2]
    + rootSymmetry.translation[axis]
  ))
}));
assert.equal(
  polycubeCoronaBoundaryKey(unresolvedP9.voxels, symmetricFirstCorona, 1),
  firstCoronaBoundaryKey
);
const firstCoronaContinuation = searchPolycubeCorona(unresolvedP9.voxels, {
  layers: 2,
  fixedPlacements: unresolvedFirstCorona.corona,
  nodeLimit: 100_000,
  timeLimitMs: 5_000
});
const symmetricCoronaContinuation = searchPolycubeCorona(unresolvedP9.voxels, {
  layers: 2,
  fixedPlacements: symmetricFirstCorona,
  nodeLimit: 100_000,
  timeLimitMs: 5_000
});
assert.equal(symmetricCoronaContinuation.success, firstCoronaContinuation.success);
assert.equal(symmetricCoronaContinuation.exhausted, firstCoronaContinuation.exhausted);
const firstPlacementOrbit = polycubePlacementOrbitKeys(
  unresolvedP9.voxels,
  unresolvedFirstCorona.corona[0]
);
assert.equal(firstPlacementOrbit.length, 3);
assert.equal(new Set(firstPlacementOrbit.map(key => polycubeRootContactKey(
  unresolvedP9.voxels,
  { cells: key.split(";").map(cell => cell.split(",").map(Number)) }
))).size, 1);
const forbiddenOrientationKey = polycubeOrientations(unresolvedP9.voxels)[0].key;
const orientationAlternative = searchPolycubeCorona(unresolvedP9.voxels, {
  layers: 1,
  forbiddenOrientationKeys: [forbiddenOrientationKey],
  nodeLimit: 100_000,
  timeLimitMs: 5_000
});
assert.equal(orientationAlternative.success, true);
assert.equal(verifyPolycubeCoronaPatch(
  unresolvedP9.voxels,
  orientationAlternative.corona,
  1,
  { forbiddenOrientationKeys: [forbiddenOrientationKey] }
).verified, true);

const chair = [[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 1, 1], [1, 0, 0], [1, 0, 1], [1, 1, 0]];
const rotatedChair = chair.map(([x, y, z]) => [z, x, y]);
assert.equal(canonicalPolycubeKey(chair), canonicalPolycubeKey(rotatedChair));
const lTricube = [[0, 0, 0], [1, 0, 0], [0, 1, 0]];
assert.equal(findPolycubeCyclicTiling([[0, 0, 0]]).certified, true);
assert.equal(findPolycubePeriodicTiling(lTricube, { maxCopies: 2 }).certified, true);
const exactlyThreeCopyPolycube = [
  [0, 0, 0], [0, 0, 1], [0, 0, 2], [0, 0, 3], [0, 0, 4],
  [0, 0, 5], [0, 0, 6], [0, 1, 0], [0, 1, 3], [1, 0, 3]
];
const exactlyThreeCopyCertificate = findPolycubePeriodicTiling(exactlyThreeCopyPolycube, {
  minCopies: 3,
  maxCopies: 3,
  nodeLimit: 100_000,
  timeLimitMs: 5_000
});
assert.equal(exactlyThreeCopyCertificate.certified, true);
assert.equal(exactlyThreeCopyCertificate.copies, 3);
assert.equal(
  verifyPolycubePeriodicCertificate(exactlyThreeCopyPolycube, exactlyThreeCopyCertificate).verified,
  true,
  "the independent quotient verifier must replay a three-copy complement certificate"
);
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
assert.equal(verifyPolycubeCoronaPatch([[0, 0, 0]], cubeCorona.corona, 1).verified, true);
assert.equal(
  verifyPolycubeCoronaPatch([[0, 0, 0]], [...cubeCorona.corona, cubeCorona.corona[0]], 1).verified,
  false,
  "the independent corona verifier must reject overlap"
);
const forbiddenCubeNeighbor = cubeCorona.corona[0].cells.map(cell => cell.join(",")).sort().join(";");
assert.equal(
  verifyPolycubeCoronaPatch([[0, 0, 0]], cubeCorona.corona, 1, {
    forbiddenPlacementKeys: [forbiddenCubeNeighbor]
  }).verified,
  false,
  "the independent corona verifier must reject a forbidden placement"
);
const cubeCoronaWithoutNeighbor = searchFirstPolycubeCorona([[0, 0, 0]], {
  forbiddenPlacementKeys: [forbiddenCubeNeighbor],
  nodeLimit: 1000,
  timeLimitMs: 1000
});
assert.equal(cubeCoronaWithoutNeighbor.exhausted, true, "forbidding a required cube neighbor must obstruct its first corona");
assert.equal(cubeCoronaWithoutNeighbor.forbidden_placements, 1);
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
const symmetryRejectedCubeCorona = searchPolycubeCorona([[0, 0, 0]], {
  layers: 1,
  nodeLimit: 1000,
  timeLimitMs: 1000,
  nogoods: true,
  symmetryNogoods: true,
  acceptSolution: () => ({ accept: false, nogood_placement_indices: [0] })
});
assert.equal(symmetryRejectedCubeCorona.exhausted, true);
assert.equal(symmetryRejectedCubeCorona.symmetry_nogoods_enabled, true);
assert.equal(symmetryRejectedCubeCorona.nogood_clauses, 6);
assert.equal(symmetryRejectedCubeCorona.symmetry_nogood_clauses, 5);
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
