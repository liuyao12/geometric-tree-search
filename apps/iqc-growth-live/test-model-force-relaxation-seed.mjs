import assert from "node:assert/strict";
import { auditCartesianForceEnergyGradient,
  auditComponentForceEnergyPathClosures, auditFiniteReachPathTopology,
  auditEnvironmentReactionForceBalance,
  auditEnvironmentReactionTorqueBalance,
  auditForceEnergyPathClosure,
  auditInteriorForceEnergyGradientConsistency,
  auditPanelResolvedForceEnergyPathClosure,
  auditGroupedForceResiduals,
  auditModelForceRelaxationEnergyDescent,
  auditModelForceRelaxationOutcome, auditModelForceRelaxationPath,
  buildModelForceRelaxationSeed }
  from "./model-force-relaxation-seed.mjs";
import { incrementalFinitePointChargeElectrostatics }
  from "./finite-point-charge-electrostatics.mjs";

const current = [{ position: [0, 0, 0], charge: 1, species: "Na" }];
const added = [{ position: [2.8, 0, 0], charge: -1, species: "Cl" }];
const cutoffCrossing = auditFiniteReachPathTopology(current,
  [{ position: [2, 1, 0] }], [{ position: [2, -1, 0] }], 2.1);
assert.equal(cutoffCrossing.passed, false);
assert.equal(cutoffCrossing.crossingPairs.length, 1);
assert.ok(Math.abs(cutoffCrossing.crossingPairs[0].closestParameter - .5) < 1e-12);
assert.ok(cutoffCrossing.crossingPairs[0].closestDistanceAngstrom < 2.1);
const cutoffSafeOutside = auditFiniteReachPathTopology(current,
  [{ position: [3, 1, 0] }], [{ position: [3, -1, 0] }], 2.1);
assert.equal(cutoffSafeOutside.passed, true);
assert.equal(cutoffSafeOutside.activePairs, 0);
const cutoffSafeInside = auditFiniteReachPathTopology(current,
  [{ position: [1, 1, 0] }], [{ position: [1, -1, 0] }], 2.1);
assert.equal(cutoffSafeInside.passed, true);
assert.equal(cutoffSafeInside.activePairs, 1);
const globalReach = auditFiniteReachPathTopology(current,
  [{ position: [2, 1, 0] }], [{ position: [2, -1, 0] }], "global");
assert.equal(globalReach.passed, true);
assert.equal(globalReach.finiteReach, false);
const fractions = Array.from({ length: 13 }, (_, index) => index / 12);
const consistentClosure = auditForceEnergyPathClosure(fractions,
  fractions.map((fraction) => -fraction - fraction * fraction),
  fractions.map((fraction) => [[1 + 2 * fraction, 0, 0]]), [[1, 0, 0]]);
assert.equal(consistentClosure.passed, true);
assert.ok(Math.abs(consistentClosure.simpsonWorkElectronVolt - 2) < 1e-12);
assert.ok(Math.abs(consistentClosure.energyChangeElectronVolt + 2) < 1e-12);
assert.deepEqual(consistentClosure.energyProfileElectronVolt,
  fractions.map((fraction) => -fraction - fraction * fraction));
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
const compensatingTotalClosure = auditForceEnergyPathClosure(fractions,
  fractions.map((fraction) => -fraction), fractions.map(() => [[1, 0, 0]]),
  [[1, 0, 0]]);
assert.equal(compensatingTotalClosure.passed, true);
const compensatingComponentErrors = auditComponentForceEnergyPathClosures([
  { id: "first", active: true, energiesElectronVolt: fractions.map((fraction) => -fraction),
    forceFieldsElectronVoltPerAngstrom: fractions.map(() => [[.5, 0, 0]]) },
  { id: "second", active: true, energiesElectronVolt: fractions.map(() => 0),
    forceFieldsElectronVoltPerAngstrom: fractions.map(() => [[.5, 0, 0]]) },
], fractions, [[1, 0, 0]]);
assert.equal(compensatingComponentErrors.passed, false);
assert.deepEqual(compensatingComponentErrors.failedComponentIds, ["first", "second"]);
const pathLocalCancellationForces = fractions.map((fraction) =>
  [[1 + Math.sin(2 * Math.PI * fraction), 0, 0]]);
const pathLocalCancellationAggregate = auditForceEnergyPathClosure(fractions,
  fractions.map((fraction) => -fraction), pathLocalCancellationForces,
  [[1, 0, 0]]);
assert.equal(pathLocalCancellationAggregate.passed, true);
const pathLocalCancellationPanels = auditPanelResolvedForceEnergyPathClosure(
  fractions, fractions.map((fraction) => -fraction),
  pathLocalCancellationForces, [[1, 0, 0]]);
assert.equal(pathLocalCancellationPanels.passed, false);
assert.equal(pathLocalCancellationPanels.panelCount, 3);
assert.ok(pathLocalCancellationPanels.failedPanelIndices.length >= 2);
const pathLocalCancellationComponent = auditComponentForceEnergyPathClosures([{
  id: "locally-inconsistent", active: true,
  energiesElectronVolt: fractions.map((fraction) => -fraction),
  forceFieldsElectronVoltPerAngstrom: pathLocalCancellationForces,
}], fractions, [[1, 0, 0]]);
assert.equal(pathLocalCancellationComponent.passed, false);
assert.equal(pathLocalCancellationComponent.records[0].aggregateClosurePassed, true);
assert.equal(pathLocalCancellationComponent.records[0].panelClosurePassed, false);
const withinPanelErrors = fractions.map(() => 0);
[0, 4, 8].forEach((start) => {
  withinPanelErrors[start + 1] = .2;
  withinPanelErrors[start + 2] = -.4;
});
const withinPanelCancellationForces = withinPanelErrors.map((error) =>
  [[1 + error, 0, 0]]);
const withinPanelCancellationAggregate = auditForceEnergyPathClosure(fractions,
  fractions.map((fraction) => -fraction), withinPanelCancellationForces,
  [[1, 0, 0]]);
const withinPanelCancellationPanels = auditPanelResolvedForceEnergyPathClosure(
  fractions, fractions.map((fraction) => -fraction),
  withinPanelCancellationForces, [[1, 0, 0]]);
assert.equal(withinPanelCancellationAggregate.passed, true);
assert.equal(withinPanelCancellationPanels.passed, true);
const withinPanelGradient = auditInteriorForceEnergyGradientConsistency(
  fractions, fractions.map((fraction) => -fraction),
  withinPanelCancellationForces, [[1, 0, 0]]);
assert.equal(withinPanelGradient.passed, false);
assert.deepEqual(withinPanelGradient.failedImageIndices, [2, 5, 6, 9, 10]);
const withinPanelCancellationComponent = auditComponentForceEnergyPathClosures([{
  id: "interior-inconsistent", active: true,
  energiesElectronVolt: fractions.map((fraction) => -fraction),
  forceFieldsElectronVoltPerAngstrom: withinPanelCancellationForces,
}], fractions, [[1, 0, 0]]);
assert.equal(withinPanelCancellationComponent.records[0].aggregateClosurePassed, true);
assert.equal(withinPanelCancellationComponent.records[0].panelClosurePassed, true);
assert.equal(withinPanelCancellationComponent.records[0]
  .interiorGradientConsistencyPassed, false);
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
const finitePairCartesianGradient = auditCartesianForceEnergyGradient(current,
  added, finitePairSeed.evaluation, finitePairOptions);
assert.equal(finitePairCartesianGradient.passed, true);
assert.equal(finitePairCartesianGradient.coordinateCount, 3);
assert.equal(finitePairCartesianGradient.probeEvaluationCount, 12);
assert.equal(finitePairCartesianGradient.energyProbeForceMode, "omitted");
assert.equal(finitePairCartesianGradient.branchStable, true);
const transverseForceCorruption = {
  ...finitePairSeed.evaluation,
  addedForceVectorsElectronVoltPerAngstrom:
    finitePairSeed.evaluation.addedForceVectorsElectronVoltPerAngstrom
      .map((vector, index) => vector.map((value, axis) =>
        value + (index === 0 && axis === 1 ? 1 : 0))),
};
const transverseCartesianGradient = auditCartesianForceEnergyGradient(current,
  added, transverseForceCorruption, finitePairOptions);
assert.equal(transverseCartesianGradient.passed, false);
assert.deepEqual(transverseCartesianGradient.failedComponentIds, ["total"]);
assert.deepEqual(transverseCartesianGradient.components.find((component) =>
  component.id === "total").failedCoordinates, ["0:y"]);
const finitePairEnvironmentReaction = auditEnvironmentReactionForceBalance(current,
  added, finitePairSeed.evaluation, finitePairOptions);
assert.equal(finitePairEnvironmentReaction.passed, true);
assert.equal(finitePairEnvironmentReaction.probeEvaluationCount, 12);
assert.equal(finitePairEnvironmentReaction.fixedEnvironmentMovedCollectivelyForProbe, true);
assert.equal(finitePairEnvironmentReaction.fixedEnvironmentRelaxed, false);
assert.equal(finitePairEnvironmentReaction.perFixedSiteForcesResolved, false);
assert.deepEqual(finitePairEnvironmentReaction.failedComponentIds, []);
const transverseReactionFailure = auditEnvironmentReactionForceBalance(current,
  added, transverseForceCorruption, finitePairOptions);
assert.equal(transverseReactionFailure.passed, false);
assert.deepEqual(transverseReactionFailure.failedComponentIds, ["total"]);
assert.deepEqual(transverseReactionFailure.components.find((component) =>
  component.id === "total").failedAxes, ["y"]);
const finitePairEnvironmentTorque = auditEnvironmentReactionTorqueBalance(current,
  added, finitePairSeed.evaluation, finitePairOptions);
assert.equal(finitePairEnvironmentTorque.passed, true);
assert.equal(finitePairEnvironmentTorque.probeEvaluationCount, 12);
assert.equal(finitePairEnvironmentTorque.fixedEnvironmentRotatedCollectivelyForProbe, true);
assert.equal(finitePairEnvironmentTorque.fixedEnvironmentRelaxed, false);
assert.equal(finitePairEnvironmentTorque.perFixedSiteForcesResolved, false);
assert.deepEqual(finitePairEnvironmentTorque.failedComponentIds, []);
const transverseTorqueFailure = auditEnvironmentReactionTorqueBalance(current,
  added, transverseForceCorruption, finitePairOptions);
assert.equal(transverseTorqueFailure.passed, false);
assert.deepEqual(transverseTorqueFailure.failedComponentIds, ["total"]);
assert.deepEqual(transverseTorqueFailure.components.find((component) =>
  component.id === "total").failedAxes, ["z"]);
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
assert.equal(forceSettlingPath.panelWorkEnergyClosurePassed, true);
assert.equal(forceSettlingPath.workEnergyPanelCount, 3);
assert.deepEqual(forceSettlingPath.failedWorkEnergyPanelIndices, []);
assert.equal(forceSettlingPath.interiorGradientConsistencyPassed, true);
assert.equal(forceSettlingPath.interiorGradientEligibleImageCount, 9);
assert.deepEqual(forceSettlingPath.failedInteriorGradientImageIndices, []);
assert.equal(forceSettlingPath.endpointCartesianGradientPassed, true);
assert.equal(forceSettlingPath.cartesianGradientEndpointCount, 2);
assert.equal(forceSettlingPath.cartesianGradientCoordinateCount, 6);
assert.equal(forceSettlingPath.cartesianGradientProbeEvaluationCount, 24);
assert.deepEqual(forceSettlingPath.failedCartesianGradientEndpointImageIndices, []);
assert.equal(forceSettlingPath.endpointEnvironmentReactionPassed, true);
assert.equal(forceSettlingPath.environmentReactionEndpointCount, 2);
assert.equal(forceSettlingPath.environmentReactionCoordinateCount, 6);
assert.equal(forceSettlingPath.environmentReactionProbeEvaluationCount, 24);
assert.deepEqual(forceSettlingPath.failedEnvironmentReactionEndpointImageIndices, []);
assert.equal(forceSettlingPath.endpointEnvironmentTorquePassed, true);
assert.equal(forceSettlingPath.environmentTorqueEndpointCount, 2);
assert.equal(forceSettlingPath.environmentTorqueCoordinateCount, 6);
assert.equal(forceSettlingPath.environmentTorqueProbeEvaluationCount, 24);
assert.deepEqual(forceSettlingPath.failedEnvironmentTorqueEndpointImageIndices, []);
assert.equal(forceSettlingPath.smoothModelBranchPassed, true);
assert.equal(forceSettlingPath.modelStateStableAcrossImages, true);
assert.equal(forceSettlingPath.analyticReachTopologyPassed, true);
assert.equal(forceSettlingPath.componentWorkEnergyClosuresPassed, true);
assert.equal(forceSettlingPath.componentWorkEnergyClosures.records
  .filter((record) => record.active).every((record) => record.panelClosurePassed), true);
assert.equal(forceSettlingPath.componentWorkEnergyClosures.records
  .filter((record) => record.active)
  .every((record) => record.interiorGradientConsistencyPassed), true);
assert.equal(forceSettlingPath.activeWorkEnergyComponentCount, 2);
assert.deepEqual(forceSettlingPath.componentWorkEnergyClosures.records
  .filter((record) => record.active).map((record) => record.id), ["coulomb", "born-mayer"]);
const finiteReachSettlingPath = auditModelForceRelaxationPath(current, added,
  [{ ...added[0], position: [2.79, 0, 0] }], {
    imageCount: 13,
    forceGroupLabels: ["fresh"],
    electrostaticsOptions: { ...finitePairOptions, reachAngstrom: 3 },
  });
assert.equal(finiteReachSettlingPath.accepted, true);
assert.equal(finiteReachSettlingPath.smoothModelBranchPassed, true);
assert.equal(finiteReachSettlingPath.smoothModelBranch.reachTopology.finiteReach, true);
assert.equal(finiteReachSettlingPath.analyticReachPairChecks, 1);
assert.ok(Math.abs(finiteReachSettlingPath.analyticReachMinimumClearanceAngstrom - .2)
  < 1e-12);
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
const inductionPath = auditModelForceRelaxationPath(current, added,
  [{ ...added[0], position: added[0].position.map((value, axis) =>
    value + completeInduction.offsets[0][axis] * .1) }], {
    imageCount: 13,
    electrostaticsOptions: { relativePermittivity: 4,
      bornMayerAmplitudeElectronVolt: 1000, bornMayerDecayAngstrom: .3,
      inductionPolarizabilityAngstrom3: 2, inductionDampingLengthAngstrom: .3,
      inductionForceMode: "finite-difference" },
  });
assert.equal(inductionPath.accepted, true);
assert.equal(inductionPath.componentWorkEnergyClosuresPassed, true);
assert.equal(inductionPath.activeWorkEnergyComponentCount, 3);
assert.ok(inductionPath.inductionForceWorkNumericalUncertaintyElectronVolt > 0);
assert.equal(inductionPath.componentWorkEnergyClosures.records
  .find((record) => record.id === "induction").passed, true);
assert.equal(inductionPath.endpointEnvironmentReactionPassed, true);
assert.equal(inductionPath.endpointEnvironmentReactionAudit.records
  .every((record) => record.components.find((component) =>
    component.id === "induction").passed), true);
assert.equal(inductionPath.endpointEnvironmentTorquePassed, true);
assert.equal(inductionPath.endpointEnvironmentTorqueAudit.records
  .every((record) => record.components.find((component) =>
    component.id === "induction").passed), true);

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
