import assert from "node:assert/strict";
import { incrementalIonicPairGeometry } from "../apps/iqc-growth-live/ionic-pair-geometry.js";

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

console.log("ionic pair geometry: passed");
