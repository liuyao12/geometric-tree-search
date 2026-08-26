import assert from "node:assert/strict";
import { incrementalIonicPairGeometry, incrementalIonicPairReachProfile,
  rankIonicPairReachProfiles } from "../apps/iqc-growth-live/ionic-pair-geometry.js";

const current = [
  { position: [-1, 0, 0], charge: 1 },
  { position: [1, 0, 0], charge: -1 },
  { position: [0, 2, 0], charge: 1 },
];
const added = [{ position: [0, 0, 0], charge: -1 }, { position: [0, -2, 0], charge: 1 }];
const audit = incrementalIonicPairGeometry(current, added,
  { nearestNeighborScale: 1, reachNearestNeighborUnits: "global" });
assert.equal(audit.available, true);
assert.equal(audit.pairCount, 7);
assert.equal(audit.distanceEvaluations, 7);
assert.ok(audit.score >= -1 && audit.score <= 1);
assert.equal(audit.incrementalPairsOnly, true);
assert.equal(audit.currentCurrentConstantOmitted, true);
assert.equal(audit.coulombKernelUsed, true);
assert.equal(audit.coulombPrefactorApplied, false);
assert.equal(audit.dielectricConstantApplied, false);
assert.equal(audit.ewaldSummationUsed, false);
assert.equal(audit.electrostaticEnergyInferred, false);
assert.equal(audit.electronicStructureModeled, false);

const transform = ([x, y, z]) => [4 * (-y) + 8, 4 * x - 3, 4 * z + 5];
const transformed = incrementalIonicPairGeometry(
  [...current].reverse().map((site) => ({ position: transform(site.position), charge: site.charge })),
  [...added].reverse().map((site) => ({ position: transform(site.position), charge: site.charge })),
  { nearestNeighborScale: 4, reachNearestNeighborUnits: "global" });
assert.ok(Math.abs(audit.score - transformed.score) < 1e-12);
assert.ok(Math.abs(audit.signedPairSum - transformed.signedPairSum) < 1e-12);
assert.equal(audit.pairCount, transformed.pairCount);

const finite = incrementalIonicPairGeometry(current, added,
  { nearestNeighborScale: 1, reachNearestNeighborUnits: 1.1 });
assert.ok(finite.pairCount < audit.pairCount);
assert.ok(finite.distanceEvaluations === audit.distanceEvaluations);
assert.equal(incrementalIonicPairGeometry([], added,
  { nearestNeighborScale: 1, reachNearestNeighborUnits: 4 }).available, false);
assert.equal(incrementalIonicPairGeometry(current, [],
  { nearestNeighborScale: 1, reachNearestNeighborUnits: 4 }).available, false);

const profile = incrementalIonicPairReachProfile(current, added, {
  nearestNeighborScale: 1,
  reaches: [2, 4, 8, "global"],
});
assert.equal(profile.available, true);
assert.deepEqual(profile.reaches, [2, 4, 8, "global"]);
assert.equal(profile.samples.length, 4);
assert.equal(profile.samples.at(-1).score, audit.score);
assert.ok(profile.samples[0].pairCount <= profile.samples[1].pairCount);
assert.ok(profile.samples[1].pairCount <= profile.samples[2].pairCount);
assert.ok(profile.samples[2].pairCount <= profile.samples[3].pairCount);
assert.equal(profile.candidateSetChanged, false);
assert.equal(profile.targetUsed, false);
assert.equal(profile.dielectricOrEwaldConvergenceInferred, false);

const competing = incrementalIonicPairReachProfile(current,
  [{ position: [0, 0, 0], charge: 1 }, { position: [0, -2, 0], charge: -1 }],
  { nearestNeighborScale: 1, reaches: [2, 4, 8, "global"] });
const ranked = rankIonicPairReachProfiles([
  { candidateKey: "b", profile: competing }, { candidateKey: "a", profile },
]);
const permutedRanked = rankIonicPairReachProfiles([
  { candidateKey: "a", profile }, { candidateKey: "b", profile: competing },
]);
assert.equal(ranked.available, true);
assert.deepEqual(ranked.reaches, [2, 4, 8, "global"]);
assert.deepEqual(ranked.winners, permutedRanked.winners);
assert.deepEqual(ranked.candidates, permutedRanked.candidates);
assert.equal(ranked.candidateSetChanged, false);
assert.equal(ranked.targetUsed, false);

console.log("ionic pair geometry: passed");
