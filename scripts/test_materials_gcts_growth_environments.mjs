import assert from "node:assert/strict";
import {
  GROWTH_ENVIRONMENT_IDS,
  growthEnvironmentAudit,
  growthEnvironmentContains,
  growthEnvironmentSignedMargin,
  growthEnvironmentSpec,
  scaledGrowthEnvironmentSpec,
} from "../apps/iqc-growth-live/growth-environments.js";

assert.deepEqual(GROWTH_ENVIRONMENT_IDS, ["box", "sphere", "cylinder", "slab", "substrate", "hourglass"]);
GROWTH_ENVIRONMENT_IDS.forEach((id) => {
  assert.equal(growthEnvironmentContains(id, [0, 0, 0]), true, `${id} must contain the growth seed`);
  const audit = growthEnvironmentAudit(id);
  assert.equal(audit.id, id);
  assert.equal(audit.admissionRole, "hard target-independent public-boundary gate");
  assert.equal(audit.affectsCandidateGeometry, false);
  assert.equal(audit.affectsCandidateAdmission, true);
  assert.equal(audit.physicalPotentialUsed, false);
  assert.equal(audit.surfaceEnergyModeled, false);
  assert.equal(audit.periodicImagesImplied, false);
});

assert.equal(growthEnvironmentContains("box", [8.35, 0, 0]), true);
assert.equal(growthEnvironmentContains("box", [8.351, 0, 0]), false);
assert.equal(growthEnvironmentContains("sphere", [0, 0, 8.8]), true);
assert.equal(growthEnvironmentContains("sphere", [0, 0, 8.801]), false);
assert.equal(growthEnvironmentContains("cylinder", [8.35, 7.8, 0]), true);
assert.equal(growthEnvironmentContains("cylinder", [8.351, 0, 0]), false);
assert.equal(growthEnvironmentContains("slab", [8, 8, 3.2]), true);
assert.equal(growthEnvironmentContains("slab", [0, 0, 3.201]), false);
assert.equal(growthEnvironmentContains("substrate", [0, 0, -3.2]), true);
assert.equal(growthEnvironmentContains("substrate", [0, 0, -3.201]), false);
assert.equal(growthEnvironmentContains("substrate", [0, 0, 8.351]), false);
assert.equal(growthEnvironmentContains("hourglass", [0, 2.25, 0]), true);
assert.equal(growthEnvironmentContains("hourglass", [0, 2.251, 0]), false);
assert.equal(growthEnvironmentContains("hourglass", [8, 6.8, 0]), true);

assert.match(growthEnvironmentSpec("substrate").note, /No substrate atoms/);
assert.deepEqual(scaledGrowthEnvironmentSpec("box", 2).parameters.halfExtents, [16.7, 16.7, 16.7]);
assert.equal(growthEnvironmentContains("box", [12, 0, 0], 1), false);
assert.equal(growthEnvironmentContains("box", [12, 0, 0], 2), true);
assert.equal(growthEnvironmentSignedMargin("sphere", [10, 0, 0], 2), 7.600000000000001);
assert.equal(growthEnvironmentAudit("box", 4).publicReachScale, 4);
assert.throws(() => growthEnvironmentSpec("unknown"), /Unknown growth environment/);
assert.throws(() => growthEnvironmentContains("box", [0, Number.NaN, 0]), /three finite coordinates/);

console.log("growth environment geometry: passed");
