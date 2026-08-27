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
for (const key of ["minimumThroatClearance", "percentile10ThroatClearance", "medianThroatClearance",
  "widestCoreToFrontClearance"]) {
  assert.ok(Number.isFinite(baseline.network[key]));
  assert.ok(Math.abs(baseline.network[key] - invariant.network[key]) < 1e-10);
}
assert.ok(baseline.network.edges.every((edge) => edge.throatClearance > 0
  && edge.throatToEndpointRatio > 0 && edge.throatToEndpointRatio <= 1));
const closedThreshold = interstitialClearanceAudit(cubic, cubic, { maximumAnchors: 32, declaredThreshold: .8 });
assert.equal(closedThreshold.network.thresholdEdgeCount, 0);
assert.equal(closedThreshold.network.thresholdCoreToFrontComponentCount, 0);
assert.ok(baseline.network.thresholdEdgeCount > closedThreshold.network.thresholdEdgeCount);
const carbonSpecies = cubic.map(() => "C");
const steric = interstitialClearanceAudit(cubic, cubic, { maximumAnchors: 32,
  currentSpecies: carbonSpecies, referenceSpecies: carbonSpecies, covalentRadiiAngstrom: { C: .2 },
  fittedContactRadiiAngstrom: { C: .3 } });
const rigid = ([x, y, z]) => [5 - y, -3 + x, 9 + z];
const stericInvariant = interstitialClearanceAudit(cubic.map(rigid).reverse(), cubic.map(rigid).reverse(), {
  maximumAnchors: 32, currentSpecies: [...carbonSpecies].reverse(), referenceSpecies: [...carbonSpecies].reverse(),
  covalentRadiiAngstrom: { C: .2 }, fittedContactRadiiAngstrom: { C: .3 },
});
assert.equal(steric.covalentRadiusStericModelAvailable, true);
assert.equal(steric.fittedContactRadiusStericModelAvailable, true);
assert.ok(steric.network.medianStericThroatClearance < steric.network.medianThroatClearance);
assert.ok(steric.network.medianFittedStericThroatClearance < steric.network.medianStericThroatClearance);
assert.ok(Math.abs(steric.network.medianStericThroatClearance
  - stericInvariant.network.medianStericThroatClearance) < 1e-10);
assert.ok(Math.abs(steric.network.medianFittedStericThroatClearance
  - stericInvariant.network.medianFittedStericThroatClearance) < 1e-10);
assert.equal(steric.covalentRadiusStericUniformCoordinateScalingInvariant, false);
const displayScaledSteric = interstitialClearanceAudit(cubic.map(transform), cubic.map(transform), {
  maximumAnchors: 32, currentSpecies: carbonSpecies, referenceSpecies: carbonSpecies,
  covalentRadiiAngstrom: { C: .2 }, physicalNearestNeighborAngstrom: 1,
});
assert.equal(displayScaledSteric.covalentRadiusNormalizationScaleAngstrom, 1);
assert.ok(Math.abs(steric.network.medianStericThroatClearance
  - displayScaledSteric.network.medianStericThroatClearance) < 1e-10);

const periodicCube = [];
for (let x = -1.5; x <= 1.5; x++) for (let y = -1.5; y <= 1.5; y++) {
  for (let z = -1.5; z <= 1.5; z++) periodicCube.push([x, y, z]);
}
const periodicSpecies = periodicCube.map(() => "C");
const periodic = interstitialClearanceAudit(periodicCube, periodicCube, { maximumAnchors: 32,
  currentSpecies: periodicSpecies, referenceSpecies: periodicSpecies, covalentRadiiAngstrom: { C: .2 },
  fittedContactRadiiAngstrom: { C: .3 },
  physicalNearestNeighborAngstrom: 1, periodicCellVectorsAngstrom: [[4, 0, 0], [0, 4, 0], [0, 0, 4]],
  periodicAxes: [true, true, true], includePeriodicReference: true });
const periodicRigid = interstitialClearanceAudit(periodicCube.map(rigid).reverse(), periodicCube.map(rigid).reverse(), {
  maximumAnchors: 32, currentSpecies: [...periodicSpecies].reverse(), referenceSpecies: [...periodicSpecies].reverse(),
  covalentRadiiAngstrom: { C: .2 }, physicalNearestNeighborAngstrom: 1,
  fittedContactRadiiAngstrom: { C: .3 },
  periodicCellVectorsAngstrom: [[0, 4, 0], [-4, 0, 0], [0, 0, 4]], periodicAxes: [true, true, true],
  includePeriodicReference: true,
});
assert.equal(periodic.periodicReferenceQuotientAvailable, true);
assert.equal(periodic.referencePeriodic.candidateCenters, 64);
assert.equal(periodic.referencePeriodic.network.edgeCount, 192);
assert.equal(periodic.referencePeriodic.network.wrappedEdgeCount, 48);
assert.equal(periodic.referencePeriodic.network.windingRank, 3);
assert.deepEqual(periodic.referencePeriodic.network.percolatingAxes, [0, 1, 2]);
assert.equal(periodic.referencePeriodic.network.thresholdWindingRank, 3);
assert.ok(Math.abs(periodic.referencePeriodic.network.widestPeriodicClearance - Math.SQRT1_2) < 1e-10);
assert.ok(periodic.referencePeriodic.network.widestFittedStericPeriodicClearance
  < periodic.referencePeriodic.network.widestStericPeriodicClearance);
for (const key of ["candidateCenters"]) assert.equal(periodic.referencePeriodic[key], periodicRigid.referencePeriodic[key]);
for (const key of ["edgeCount", "wrappedEdgeCount", "windingRank", "thresholdWindingRank"]) {
  assert.equal(periodic.referencePeriodic.network[key], periodicRigid.referencePeriodic.network[key]);
}
assert.deepEqual(periodic.referencePeriodic.network.percolatingAxes,
  periodicRigid.referencePeriodic.network.percolatingAxes);
const periodicClosed = interstitialClearanceAudit(periodicCube, periodicCube, { maximumAnchors: 32,
  physicalNearestNeighborAngstrom: 1, periodicCellVectorsAngstrom: [[4, 0, 0], [0, 4, 0], [0, 0, 4]],
  periodicAxes: [true, true, true], includePeriodicReference: true, declaredThreshold: .8 });
assert.equal(periodicClosed.referencePeriodic.network.thresholdWindingRank, 0);
const periodicOneAxis = interstitialClearanceAudit(periodicCube, periodicCube, { maximumAnchors: 32,
  physicalNearestNeighborAngstrom: 1, periodicCellVectorsAngstrom: [[4, 0, 0], [0, 4, 0], [0, 0, 4]],
  periodicAxes: [true, false, false], includePeriodicReference: true });
assert.equal(periodicOneAxis.referencePeriodic.network.windingRank, 1);
assert.deepEqual(periodicOneAxis.referencePeriodic.network.percolatingAxes, [0]);
const finiteDegenerateSeed = [[0, 0, 0], [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
const periodicDespiteFiniteSeed = interstitialClearanceAudit(finiteDegenerateSeed, periodicCube, {
  maximumAnchors: 32, currentSpecies: finiteDegenerateSeed.map(() => "C"), referenceSpecies: periodicSpecies,
  fittedContactRadiiAngstrom: { C: .3 }, physicalNearestNeighborAngstrom: 1,
  periodicCellVectorsAngstrom: [[4, 0, 0], [0, 4, 0], [0, 0, 4]],
  periodicAxes: [true, true, true], includePeriodicReference: true,
});
assert.equal(periodicDespiteFiniteSeed.available, true,
  "a degenerate finite nucleus must not suppress an independently valid periodic input quotient");
assert.equal(periodicDespiteFiniteSeed.finiteCurrentNetworkAvailable, false);
assert.equal(periodicDespiteFiniteSeed.referencePeriodic.network.windingRank, 3);

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
assert.equal(planar.probeAccessibleNetworkInferred, false);
assert.equal(planar.targetUsed, false);
console.log("finite interstitial-clearance invariants: passed");
