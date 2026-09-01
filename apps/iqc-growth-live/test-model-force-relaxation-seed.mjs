import assert from "node:assert/strict";
import { auditForceEnergyPathClosure, auditGroupedForceResiduals,
  auditModelForceRelaxationEnergyDescent,
  auditModelForceRelaxationOutcome, auditModelForceRelaxationPath,
  buildModelForceRelaxationSeed }
  from "./model-force-relaxation-seed.mjs";

const current = [{ position: [0, 0, 0], charge: 1, species: "Na" }];
const added = [{ position: [2.8, 0, 0], charge: -1, species: "Cl" }];
const fractions = Array.from({ length: 13 }, (_, index) => index / 12);
const consistentClosure = auditForceEnergyPathClosure(fractions,
  fractions.map((fraction) => -fraction - fraction * fraction),
  fractions.map((fraction) => [[1 + 2 * fraction, 0, 0]]), [[1, 0, 0]]);
assert.equal(consistentClosure.passed, true);
assert.ok(Math.abs(consistentClosure.simpsonWorkElectronVolt - 2) < 1e-12);
assert.ok(Math.abs(consistentClosure.energyChangeElectronVolt + 2) < 1e-12);
assert.ok(Math.abs(consistentClosure.closureResidualElectronVolt) < 1e-12);
assert.equal(consistentClosure.fineSimpsonImageCount, 13);
assert.equal(consistentClosure.coarseSimpsonImageCount, 7);
assert.equal(consistentClosure.nestedSimpsonConvergenceAvailable, true);
assert.ok(consistentClosure.richardsonErrorEstimateElectronVolt < 1e-12);
assert.equal(consistentClosure.pathParameterIsPhysicalTime, false);
const inconsistentClosure = auditForceEnergyPathClosure(fractions,
  fractions.map((fraction) => -fraction),
  fractions.map(() => [[.5, 0, 0]]), [[1, 0, 0]]);
assert.equal(inconsistentClosure.passed, false);
assert.ok(Math.abs(inconsistentClosure.closureResidualElectronVolt) > .49);
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
const heterogeneousSeed = buildModelForceRelaxationSeed(current, [added[0],
  { ...added[0], position: [0, 2.8, 0] }], {
  displacementCap: .05, displacementCaps: [.05, .01],
  electrostaticsOptions: { relativePermittivity: 4 },
});
assert.equal(heterogeneousSeed.available, true);
assert.equal(heterogeneousSeed.heterogeneousDisplacementCaps, true);
assert.deepEqual(heterogeneousSeed.displacementCaps, [.05, .01]);
assert.ok(Math.hypot(...heterogeneousSeed.offsets[0]) <= .05 + 1e-12);
assert.ok(Math.hypot(...heterogeneousSeed.offsets[1]) <= .01 + 1e-12);
const groupedPass = auditGroupedForceResiduals(
  [[3, 0, 0], [2, 0, 0], [1, 0, 0]],
  [[2, 0, 0], [1.5, 0, 0], [.8, 0, 0]],
  ["fresh", "shell-1", "shell-2"], {
    beforePositions: [[0, 0, 0], [1, 0, 0], [2, 0, 0]],
    afterPositions: [[0, 0, 0], [1.01, 0, 0], [2.01, 0, 0]],
  },
);
assert.equal(groupedPass.passed, true);
assert.equal(groupedPass.groupCount, 3);
assert.equal(groupedPass.groupLabelsFrozenBeforeProposal, true);
assert.equal(groupedPass.resultantAvailable, true);
assert.equal(groupedPass.resultantPassed, true);
assert.equal(groupedPass.symmetricForceMomentAvailable, true);
assert.equal(groupedPass.symmetricForceMomentPassed, true);
const hiddenRedistribution = auditGroupedForceResiduals(
  [[4, 0, 0], [2, 0, 0]],
  [[2, 0, 0], [2.5, 0, 0]],
  ["fresh", "shell-1"],
);
assert.equal(hiddenRedistribution.passed, false);
assert.equal(hiddenRedistribution.groups.find((group) => group.label === "shell-1")
  .residualNonIncreasing, false);
const hiddenNetForce = auditGroupedForceResiduals(
  [[1, 0, 0], [-1, 0, 0]],
  [[.8, 0, 0], [.8, 0, 0]],
  ["shell-1", "shell-1"], {
    beforePositions: [[-1, 0, 0], [1, 0, 0]],
    afterPositions: [[-1, 0, 0], [1, 0, 0]],
  },
);
assert.equal(hiddenNetForce.residualPassed, true);
assert.equal(hiddenNetForce.resultantPassed, false);
assert.equal(hiddenNetForce.groups[0].netForceNonIncreasing, false);
const hiddenTorque = auditGroupedForceResiduals(
  [[0, 1, 0], [0, 1, 0]],
  [[0, .8, 0], [0, -.8, 0]],
  ["shell-2", "shell-2"], {
    beforePositions: [[-1, 0, 0], [1, 0, 0]],
    afterPositions: [[-1, 0, 0], [1, 0, 0]],
  },
);
assert.equal(hiddenTorque.residualPassed, true);
assert.equal(hiddenTorque.groups[0].netForceNonIncreasing, true);
assert.equal(hiddenTorque.groups[0].normalizedTorqueNonIncreasing, false);
assert.equal(hiddenTorque.passed, false);
const hiddenSymmetricMoment = auditGroupedForceResiduals(
  [[.5, 0, 0], [-.5, 0, 0]],
  [[.4, 0, 0], [-.4, 0, 0]],
  ["shell-2", "shell-2"], {
    beforePositions: [[-1, 0, 0], [1, 0, 0]],
    afterPositions: [[-2, 0, 0], [2, 0, 0]],
  },
);
assert.equal(hiddenSymmetricMoment.residualPassed, true);
assert.equal(hiddenSymmetricMoment.resultantPassed, true);
assert.equal(hiddenSymmetricMoment.symmetricForceMomentPassed, false);
assert.equal(hiddenSymmetricMoment.groups[0].centeredSymmetricForceMomentNonIncreasing, false);
assert.ok(hiddenSymmetricMoment.groups[0].afterResultant.centeredSymmetricForceMoment
  .frobeniusElectronVolt > hiddenSymmetricMoment.groups[0].beforeResultant
  .centeredSymmetricForceMoment.frobeniusElectronVolt);
assert.equal(hiddenSymmetricMoment.passed, false);
const rotateProper = ([x, y, z]) => [y, z, x];
const translate = ([x, y, z]) => [x + 4, y - 3, z + 2];
const rotatedSymmetricMoment = auditGroupedForceResiduals(
  [[.5, 0, 0], [-.5, 0, 0]].map(rotateProper),
  [[.4, 0, 0], [-.4, 0, 0]].map(rotateProper),
  ["shell-2", "shell-2"], {
    beforePositions: [[-1, 0, 0], [1, 0, 0]].map(rotateProper).map(translate),
    afterPositions: [[-2, 0, 0], [2, 0, 0]].map(rotateProper).map(translate),
  },
);
assert.equal(rotatedSymmetricMoment.symmetricForceMomentPassed, false);
assert.ok(Math.abs(rotatedSymmetricMoment.groups[0].beforeResultant
  .centeredSymmetricForceMoment.frobeniusElectronVolt
  - hiddenSymmetricMoment.groups[0].beforeResultant.centeredSymmetricForceMoment
    .frobeniusElectronVolt) < 1e-12);
assert.ok(Math.abs(rotatedSymmetricMoment.groups[0].afterResultant
  .centeredSymmetricForceMoment.deviatoricFrobeniusElectronVolt
  - hiddenSymmetricMoment.groups[0].afterResultant.centeredSymmetricForceMoment
    .deviatoricFrobeniusElectronVolt) < 1e-12);
const downhill = auditModelForceRelaxationEnergyDescent(current, added,
  [{ ...added[0], position: [2.79, 0, 0] }], {
    baselineEvaluation: pairSeed.evaluation,
    electrostaticsOptions: { relativePermittivity: 4 },
  });
assert.equal(downhill.available, true);
assert.equal(downhill.accepted, false);
assert.ok(downhill.energyChangeElectronVolt < 0);
assert.equal(downhill.energyDecreased, true);
assert.equal(downhill.forceResidualDecreased, false);
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

const finitePairOptions = { relativePermittivity: 4,
  bornMayerAmplitudeElectronVolt: 1000, bornMayerDecayAngstrom: .3 };
const finitePairSeed = buildModelForceRelaxationSeed(current, added, {
  displacementCap: .05, electrostaticsOptions: finitePairOptions,
});
assert.equal(finitePairSeed.available, true);
const forceSettling = auditModelForceRelaxationOutcome(current, added,
  [{ ...added[0], position: [2.79, 0, 0] }], {
    baselineEvaluation: finitePairSeed.evaluation,
    electrostaticsOptions: finitePairOptions,
  });
assert.equal(forceSettling.accepted, true);
assert.equal(forceSettling.energyDecreased, true);
assert.equal(forceSettling.forceResidualDecreased, true);
assert.equal(forceSettling.rmsForceDecreased, true);
assert.equal(forceSettling.p90ForceDecreased, true);
assert.ok(forceSettling.afterForceRmsElectronVoltPerAngstrom
  < forceSettling.beforeForceRmsElectronVoltPerAngstrom);
const forceSettlingPath = auditModelForceRelaxationPath(current, added,
  [{ ...added[0], position: [2.79, 0, 0] }], {
    imageCount: 13,
    forceGroupLabels: ["fresh"],
    electrostaticsOptions: finitePairOptions,
  });
assert.equal(forceSettlingPath.accepted, true);
assert.equal(forceSettlingPath.segmentCount, 12);
assert.equal(forceSettlingPath.everySegmentEnergyForceDescent, true);
assert.equal(forceSettlingPath.workEnergyClosurePassed, true);
assert.ok(Math.abs(forceSettlingPath.workEnergyClosureResidualElectronVolt)
  <= forceSettlingPath.workEnergyClosureToleranceElectronVolt);
assert.equal(forceSettlingPath.workEnergyClosure.pathParameterIsPhysicalTime, false);
assert.equal(forceSettlingPath.workEnergyNestedSimpsonConvergenceAvailable, true);
assert.equal(forceSettlingPath.workEnergyClosure.coarseSimpsonImageCount, 7);
assert.equal(forceSettlingPath.pathParameterIsPhysicalTime, false);
assert.equal(forceSettlingPath.targetUsed, false);
const uphillPath = auditModelForceRelaxationPath(current, added,
  [{ ...added[0], position: [2.81, 0, 0] }], {
    imageCount: 5,
    forceGroupLabels: ["fresh"],
    electrostaticsOptions: finitePairOptions,
  });
assert.equal(uphillPath.accepted, false);
assert.match(uphillPath.reason, /segment 0 failed/);

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
    bornMayerAmplitudeElectronVolt: 1000, bornMayerDecayAngstrom: .3,
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
      bornMayerAmplitudeElectronVolt: 1000, bornMayerDecayAngstrom: .3,
      inductionPolarizabilityAngstrom3: 2, inductionDampingLengthAngstrom: .3,
      inductionForceMode: "finite-difference" },
  });
assert.equal(inductionDownhill.responseConsistent, true);
assert.equal(inductionDownhill.accepted, true);
assert.equal(inductionDownhill.forceResidualDecreased, true);

assert.throws(() => buildModelForceRelaxationSeed(current, added,
  { displacementCap: 0 }), /positive displacement cap/);
assert.throws(() => buildModelForceRelaxationSeed(current, added,
  { displacementCap: .05, displacementCaps: [.06] }), /per-site caps/);
assert.throws(() => auditModelForceRelaxationEnergyDescent(current, added,
  [{ position: [2.79, 0, 0], charge: 1, species: "Cl" }]), /identity or charge/);
assert.throws(() => auditGroupedForceResiduals([[1, 0, 0]], [[.5, 0, 0]], []),
  /one frozen group label/);
assert.throws(() => auditModelForceRelaxationPath(current, added, added,
  { imageCount: 2 }), /5, 9, 13, or 17 images/);
assert.throws(() => auditModelForceRelaxationPath(current, added, added,
  { imageCount: 7 }), /5, 9, 13, or 17 images/);

console.log("model-force relaxation seed tests passed");
