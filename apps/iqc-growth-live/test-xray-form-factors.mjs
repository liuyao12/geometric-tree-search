import assert from "node:assert/strict";
import {
  XRAY_FORM_FACTOR_ELEMENTS,
  finiteDebyeXrayPowderIntensity,
  neutralXrayFormFactor,
  neutralXrayFormFactorSupport,
  periodicBraggXrayPowderIntensity,
} from "./xray-form-factors.mjs";

assert.ok(XRAY_FORM_FACTOR_ELEMENTS.includes("Na"));
assert.ok(XRAY_FORM_FACTOR_ELEMENTS.includes("Cl"));
assert.equal(neutralXrayFormFactorSupport("Ta/V").supported, true);
assert.equal(neutralXrayFormFactorSupport("Au").supported, false);
assert.ok(Math.abs(neutralXrayFormFactor("C", 0) - 5.9992) < 1e-8);
assert.ok(Math.abs(neutralXrayFormFactor("Na", 0) - 10.9924) < 1e-8);
assert.ok(neutralXrayFormFactor("Cl", 5) < neutralXrayFormFactor("Cl", 0));
assert.throws(() => neutralXrayFormFactor("Au", 1), /unavailable/);
assert.throws(() => neutralXrayFormFactor("C", 8 * Math.PI), /restricted/);

const single = finiteDebyeXrayPowderIntensity({ species: ["C"], pairs: [],
  nearestNeighborAngstrom: 1.42, bins: 8 });
assert.equal(single.qDependentFormFactorsUsed, true);
assert.ok(single.values.every((value, index) => index === 0 || value <= single.values[index - 1] + 1e-12));

const pair = finiteDebyeXrayPowderIntensity({ species: ["Na", "Cl"],
  pairs: [{ first: 0, second: 1, distance: 1 }], nearestNeighborAngstrom: 2.82, bins: 12 });
const firstQa = pair.q[0];
const firstPhysicalQ = firstQa / 2.82;
const fNa = neutralXrayFormFactor("Na", firstPhysicalQ);
const fCl = neutralXrayFormFactor("Cl", firstPhysicalQ);
const forwardNorm = neutralXrayFormFactor("Na", 0) ** 2 + neutralXrayFormFactor("Cl", 0) ** 2;
const expectedFirst = (fNa ** 2 + fCl ** 2 + 2 * fNa * fCl * Math.sin(firstQa) / firstQa) / forwardNorm;
assert.ok(Math.abs(pair.values[0] - expectedFirst) < 1e-12);
const reversed = finiteDebyeXrayPowderIntensity({ species: ["Cl", "Na"],
  pairs: [{ first: 0, second: 1, distance: 1 }], nearestNeighborAngstrom: 2.82, bins: 12 });
assert.deepEqual(pair.values, reversed.values);
assert.ok(pair.values.every(value => Number.isFinite(value) && value >= 0));

const damped = finiteDebyeXrayPowderIntensity({ species: ["Na", "Cl"],
  pairs: [{ first: 0, second: 1, distance: 1 }], nearestNeighborAngstrom: 2.82, bins: 12,
  meanSquareDisplacements: [.02, .03], includeIsotropicDisplacement: true });
assert.notDeepEqual(pair.values, damped.values);
assert.equal(damped.coherentDisplacementAttenuation, true);
assert.doesNotThrow(() => finiteDebyeXrayPowderIntensity({ species: ["Na", "Cl"],
  pairs: [{ first: 0, second: 1, distance: 1 }], nearestNeighborAngstrom: 2.82, bins: 8,
  meanSquareDisplacements: [null, .03], includeIsotropicDisplacement: true }));

const simpleCubic = periodicBraggXrayPowderIntensity({ species: ["Si"],
  positionsAngstrom: [[0, 0, 0]],
  cellVectorsAngstrom: [[3, 0, 0], [0, 3, 0], [0, 0, 3]],
  nearestNeighborAngstrom: 3, qMinTimesNearestNeighbor: 4, qMaxTimesNearestNeighbor: 12,
  coherenceLengthAngstrom: 120, bins: 256 });
assert.equal(simpleCubic.periodicTranslationalCoherenceUsed, true);
assert.ok(simpleCubic.reflectionCount > 0);
const firstReciprocalQa = 2 * Math.PI;
const firstPeakIndex = simpleCubic.q.reduce((best, value, index) =>
  Math.abs(value - firstReciprocalQa) < Math.abs(simpleCubic.q[best] - firstReciprocalQa) ? index : best, 0);
assert.ok(Math.abs(simpleCubic.q[firstPeakIndex] - firstReciprocalQa) < .03);
assert.ok(simpleCubic.values[firstPeakIndex] > simpleCubic.values[firstPeakIndex - 4]);
assert.ok(simpleCubic.values[firstPeakIndex] > simpleCubic.values[firstPeakIndex + 4]);

const translated = periodicBraggXrayPowderIntensity({ species: ["Si"],
  positionsAngstrom: [[.37, -.21, .59]],
  cellVectorsAngstrom: [[3, 0, 0], [0, 3, 0], [0, 0, 3]],
  nearestNeighborAngstrom: 3, qMinTimesNearestNeighbor: 4, qMaxTimesNearestNeighbor: 12,
  coherenceLengthAngstrom: 120, bins: 256 });
simpleCubic.values.forEach((value, index) => assert.ok(Math.abs(value - translated.values[index]) < 1e-12));
assert.throws(() => periodicBraggXrayPowderIntensity({ species: ["Si"], positionsAngstrom: [[0, 0, 0]],
  cellVectorsAngstrom: [[1, 0, 0], [2, 0, 0], [0, 0, 1]], nearestNeighborAngstrom: 2 }), /nonzero volume/);

console.log("q-dependent neutral-atom X-ray form factors: all tests passed");
