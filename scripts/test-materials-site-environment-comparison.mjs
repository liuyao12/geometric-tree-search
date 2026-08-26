import assert from "node:assert/strict";
import { compareSiteEnvironments } from "../apps/iqc-growth-live/site-environment-comparison.js";

const snapshot = (species, counts, shells, angles = [], order = [], depth = 0,
  origin = "supplied observation / fitted seed") => ({
  species, origin, positionAngstrom: [999, 999, 999],
  localEnvironment: { coordination: counts.reduce((sum, entry) => sum + entry[1], 0),
    speciesCounts: counts, distanceShells: shells, angleShells: angles,
    orientationalOrder: order, orientationalDimension: 3,
    orientationalDefinition: "Steinhardt q_l magnitude" },
  lineage: { causalDepth: depth, interfaceSite: false },
});
const constraint = (contactAngleMismatch, coordinationDeficit) => ({ summary: {
  contactAngleMismatch, distanceMismatch: contactAngleMismatch / 2,
  angleMismatch: contactAngleMismatch / 2, coordinationDeficit, hardConflicts: 0,
} });

const comparison = compareSiteEnvironments({
  first: snapshot("Na", [["Cl", 2], ["Na", 1]], [["Cl", [1, 1.1]], ["Na", [1.5]]],
    [["Cl|Cl", [90, 180]]], [[4, .2], [6, .4], [12, .6]]),
  second: snapshot("Na", [["Cl", 3]], [["Cl", [1.02, 1.08, 1.6]]],
    [["Cl|Cl", [60, 92, 170]]], [[4, .3], [6, .35], [12, .8]], 2, "GCTS-emitted structural site"),
  firstConstraint: constraint(.1, 0), secondConstraint: constraint(.35, .2),
});
assert.equal(comparison.centerChemistry.sameSpecies, true);
assert.equal(comparison.coordination.l1Difference, 2);
assert.equal(comparison.radialShells.matchedDistances, 2);
assert.equal(comparison.radialShells.unmatchedDistances, 2);
assert.equal(comparison.radialShells.rmsDistanceDeltaAngstrom, .02);
assert.equal(comparison.angularShells.matchedAngles, 2);
assert.equal(comparison.angularShells.unmatchedAngles, 1);
assert.equal(comparison.angularShells.rmsAngleDeltaDegrees, 7.2111);
assert.equal(comparison.orientationalOrder.channels[0].delta, .1);
assert.equal(comparison.orientationalOrder.channels[1].delta, -.05);
assert.equal(comparison.constraintDelta.contactAngleMismatch, .25);
assert.equal(comparison.lineage.depthDelta, 2);
assert.equal(comparison.audit.targetUsed, false);
assert.equal(comparison.audit.absoluteCoordinatesUsed, false);
assert.equal(comparison.audit.globalRotationIndependent, true);
assert.equal(JSON.stringify(comparison).includes("999"), false);
assert.match(comparison.comparisonDigest, /^[0-9a-f]{8}$/);

const chemistry = compareSiteEnvironments({ first: snapshot("O", [], []), second: snapshot("H", [], []) });
assert.equal(chemistry.centerChemistry.sameSpecies, false);
assert.equal(chemistry.radialShells.rmsDistanceDeltaAngstrom, null);
assert.throws(() => compareSiteEnvironments({ first: {} }), /required/);
console.log("materials site environment comparison: passed");
