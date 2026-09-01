import assert from "node:assert/strict";
import { auditModelForceRelaxationEnergyDescent, buildModelForceRelaxationSeed }
  from "./model-force-relaxation-seed.mjs";

const current = [{ position: [0, 0, 0], charge: 1, species: "Na" }];
const added = [{ position: [2.8, 0, 0], charge: -1, species: "Cl" }];
const pairSeed = buildModelForceRelaxationSeed(current, added, {
  displacementCap: .05,
  electrostaticsOptions: { relativePermittivity: 4 },
});
assert.equal(pairSeed.available, true);
assert.ok(pairSeed.offsets[0][0] < 0);
assert.ok(Math.hypot(...pairSeed.offsets[0]) <= .05 + 1e-12);
assert.equal(pairSeed.pairInteractionForceIsNegativeEnergyGradient, true);
assert.equal(pairSeed.forceIntegratedAsTime, false);
assert.equal(pairSeed.energyMinimized, false);
assert.equal(pairSeed.targetUsed, false);
const downhill = auditModelForceRelaxationEnergyDescent(current, added,
  [{ ...added[0], position: [2.79, 0, 0] }], {
    baselineEvaluation: pairSeed.evaluation,
    electrostaticsOptions: { relativePermittivity: 4 },
  });
assert.equal(downhill.available, true);
assert.equal(downhill.accepted, true);
assert.ok(downhill.energyChangeElectronVolt < 0);
assert.equal(downhill.atomIdentityPreserved, true);
assert.equal(downhill.currentConfigurationHeldFixed, true);
assert.equal(downhill.energyMinimized, false);
assert.equal(downhill.forceIntegratedAsTime, false);
const uphill = auditModelForceRelaxationEnergyDescent(current, added,
  [{ ...added[0], position: [2.81, 0, 0] }], {
    baselineEvaluation: pairSeed.evaluation,
    electrostaticsOptions: { relativePermittivity: 4 },
  });
assert.equal(uphill.accepted, false);
assert.ok(uphill.energyChangeElectronVolt > 0);

const incompleteInduction = buildModelForceRelaxationSeed(current, added, {
  displacementCap: .05,
  electrostaticsOptions: { relativePermittivity: 4,
    inductionPolarizabilityAngstrom3: 2, inductionDampingLengthAngstrom: .3 },
});
assert.equal(incompleteInduction.available, false);
assert.match(incompleteInduction.reason, /omitted|force/i);
assert.deepEqual(incompleteInduction.offsets, [[0, 0, 0]]);

const completeInduction = buildModelForceRelaxationSeed(current, added, {
  displacementCap: .05,
  electrostaticsOptions: { relativePermittivity: 4,
    inductionPolarizabilityAngstrom3: 2, inductionDampingLengthAngstrom: .3,
    inductionForceMode: "finite-difference" },
});
assert.equal(completeInduction.available, true);
assert.equal(completeInduction.evaluation.polarizationForceEvaluated, true);
assert.equal(completeInduction.responseConsistent, true);
assert.equal(completeInduction.evaluation.inductionForceEnergyEvaluations, 12);
const inductionDownhill = auditModelForceRelaxationEnergyDescent(current, added,
  [{ ...added[0], position: added[0].position.map((value, axis) =>
    value + completeInduction.offsets[0][axis] * .1) }], {
    baselineEvaluation: completeInduction.evaluation,
    electrostaticsOptions: { relativePermittivity: 4,
      inductionPolarizabilityAngstrom3: 2, inductionDampingLengthAngstrom: .3,
      inductionForceMode: "finite-difference" },
  });
assert.equal(inductionDownhill.responseConsistent, true);
assert.equal(inductionDownhill.accepted, true);

assert.throws(() => buildModelForceRelaxationSeed(current, added,
  { displacementCap: 0 }), /positive displacement cap/);
assert.throws(() => auditModelForceRelaxationEnergyDescent(current, added,
  [{ position: [2.79, 0, 0], charge: 1, species: "Cl" }]), /identity or charge/);

console.log("model-force relaxation seed tests passed");
