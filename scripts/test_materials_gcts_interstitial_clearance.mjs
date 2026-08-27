import assert from "node:assert/strict";
import { interstitialClearanceAudit } from "../apps/iqc-growth-live/interstitial-clearance.js";

const cubic = [];
for (let x = -2; x <= 2; x++) for (let y = -2; y <= 2; y++) for (let z = -2; z <= 2; z++) cubic.push([x, y, z]);
const transform = ([x, y, z]) => [5 + 2 * (-y), -3 + 2 * x, 9 + 2 * z];
const baseline = interstitialClearanceAudit(cubic, cubic, { maximumAnchors: 32 });
const invariant = interstitialClearanceAudit(cubic.map(transform).reverse(), cubic.map(transform).reverse(), { maximumAnchors: 32 });
assert.equal(baseline.available, true);
assert.equal(baseline.referenceNearestNeighborScale, 1);
assert.ok(baseline.candidateCenters > 0);
assert.equal(baseline.network.nodeCount, baseline.candidateCenters);
assert.ok(baseline.network.edgeCount > 0);
assert.ok(baseline.network.componentCount > 0);
assert.ok(baseline.network.largestComponentFraction > 0);
assert.ok(Math.abs(baseline.medianClearance - invariant.medianClearance) < 1e-10);
assert.ok(Math.abs(baseline.percentile90Clearance - invariant.percentile90Clearance) < 1e-10);
assert.deepEqual(baseline.histogram, invariant.histogram);
for (const key of ["edgeCount", "componentCount", "cycleRank", "largestComponentNodes", "coreToFrontComponentCount"]) {
  assert.equal(baseline.network[key], invariant.network[key]);
}

const expanded = cubic.map(([x, y, z]) => [1.2 * x, 1.2 * y, 1.2 * z]);
const expandedAudit = interstitialClearanceAudit(expanded, cubic, { maximumAnchors: 32 });
assert.ok(expandedAudit.medianClearance > baseline.medianClearance);

const triangular = [];
for (let row = -4; row <= 4; row++) for (let column = -4; column <= 4; column++) {
  triangular.push([column + .5 * (row & 1), row * Math.sqrt(3) / 2, 0]);
}
const planar = interstitialClearanceAudit(triangular, triangular, { dimension: 2, maximumAnchors: 32 });
const rotatePlane = ([x, y]) => [3 + x, -2 + .6 * y, 7 + .8 * y];
const planarInvariant = interstitialClearanceAudit(triangular.map(rotatePlane).reverse(),
  triangular.map(rotatePlane).reverse(), { dimension: 2, maximumAnchors: 32 });
assert.equal(planar.available, true);
assert.ok(planar.candidateCenters > 0);
assert.ok(Number.isFinite(planar.medianClearance));
assert.ok(Math.abs(planar.medianClearance - planarInvariant.medianClearance) < 1e-10);
assert.deepEqual(planar.histogram, planarInvariant.histogram);
assert.equal(planar.pointSitesNoAtomicRadii, true);
assert.ok(planar.network.edgeCount > 0);
assert.equal(planar.porosityInferred, false);
assert.equal(planar.diffusionPathInferred, false);
assert.equal(planar.physicalTransportConnectivityInferred, false);
assert.equal(planar.targetUsed, false);
console.log("finite interstitial-clearance invariants: passed");
