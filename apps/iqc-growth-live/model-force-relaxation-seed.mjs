import { incrementalFinitePointChargeElectrostatics }
  from "./finite-point-charge-electrostatics.mjs?v=20260901-433";
import { boundedForceSeedOffset, forceMagnitudeP90 }
  from "./force-seed-geometry.js?v=20260827-1";

const finiteVector = (value) => Array.isArray(value) && value.length === 3
  && value.every(Number.isFinite);

/**
 * Convert a complete finite interaction gradient into a bounded geometric
 * seed. This proposes coordinates only; the caller must still minimize its
 * declared local objective and re-run every hard geometric certificate.
 */
export function buildModelForceRelaxationSeed(currentSites, addedSites, {
  displacementCap,
  electrostaticsOptions = {},
} = {}) {
  if (!(Number.isFinite(displacementCap) && displacementCap > 0)) {
    throw new RangeError("model-force relaxation needs a positive displacement cap");
  }
  const evaluation = incrementalFinitePointChargeElectrostatics(currentSites, addedSites,
    electrostaticsOptions);
  const vectors = evaluation.addedForceVectorsElectronVoltPerAngstrom || [];
  const unavailable = (reason) => Object.freeze({
    available: false,
    reason,
    offsets: addedSites.map(() => Object.freeze([0, 0, 0])),
    forceScaleElectronVoltPerAngstrom: null,
    forceVectorsElectronVoltPerAngstrom: vectors.map((vector) => Object.freeze([...vector])),
    evaluation,
    responseConsistent: false,
    targetUsed: false,
  });
  if (!evaluation.available) return unavailable(evaluation.reason || "finite interaction unavailable");
  if (!evaluation.pairInteractionForceIsNegativeEnergyGradient) {
    return unavailable(evaluation.inductionForceFailureReason
      || "selected force omits a term in the interaction energy");
  }
  if (vectors.length !== addedSites.length || !vectors.every(finiteVector)) {
    return unavailable("finite interaction returned an incomplete force vector field");
  }
  const scale = forceMagnitudeP90(vectors);
  if (!(scale > 0)) return unavailable("finite interaction force field is zero");
  const offsets = vectors.map((vector) => Object.freeze(
    boundedForceSeedOffset(vector, scale, displacementCap)));
  return Object.freeze({
    available: true,
    reason: "complete model-energy gradient converted to a bounded geometric seed",
    offsets: Object.freeze(offsets),
    forceScaleElectronVoltPerAngstrom: scale,
    forceVectorsElectronVoltPerAngstrom: Object.freeze(vectors.map((vector) =>
      Object.freeze([...vector]))),
    evaluation,
    responseConsistent: evaluation.inductionPolarizabilityAngstrom3 === 0
      || evaluation.inductionForceResponseConsistent,
    pairInteractionForceIsNegativeEnergyGradient: true,
    displacementCap,
    exactCandidateGeometryUsed: true,
    candidateGeometryChanged: false,
    forceIntegratedAsTime: false,
    energyMinimized: false,
    targetUsed: false,
    claimBoundary: "The complete finite interaction gradient supplies only a bounded initial geometric direction. Acceptance still requires a lower learned contact/angle objective and unchanged hard certificates; this is not force integration, energy minimization, relaxation time, or a validated material force field.",
  });
}

/** Audit the bounded projection against the same finite interaction model. */
export function auditModelForceRelaxationOutcome(
  currentSites, originalAddedSites, proposedAddedSites, {
    baselineEvaluation = null,
    electrostaticsOptions = {},
    absoluteToleranceElectronVolt = 1e-10,
    relativeTolerance = 1e-10,
    absoluteForceToleranceElectronVoltPerAngstrom = 1e-10,
    relativeForceTolerance = 1e-10,
  } = {}) {
  if (originalAddedSites.length !== proposedAddedSites.length) {
    throw new Error("energy-descent audit requires one proposed site per original added site");
  }
  originalAddedSites.forEach((site, index) => {
    const proposed = proposedAddedSites[index];
    if (String(site.species) !== String(proposed.species)
        || Number(site.charge) !== Number(proposed.charge)) {
      throw new Error("energy-descent audit cannot change added-site identity or charge");
    }
  });
  const before = baselineEvaluation || incrementalFinitePointChargeElectrostatics(
    currentSites, originalAddedSites, electrostaticsOptions);
  const after = incrementalFinitePointChargeElectrostatics(
    currentSites, proposedAddedSites, electrostaticsOptions);
  const inductionActive = Number(before.inductionPolarizabilityAngstrom3) > 0;
  const responseConsistent = !inductionActive
    || before.inductionAppliedResponseModel === after.inductionAppliedResponseModel;
  const beforeVectors = before.addedForceVectorsElectronVoltPerAngstrom || [];
  const afterVectors = after.addedForceVectorsElectronVoltPerAngstrom || [];
  const completeForceGradient = Boolean(before.pairInteractionForceIsNegativeEnergyGradient
    && after.pairInteractionForceIsNegativeEnergyGradient
    && beforeVectors.length === originalAddedSites.length && beforeVectors.every(finiteVector)
    && afterVectors.length === proposedAddedSites.length && afterVectors.every(finiteVector));
  const evaluationsAvailable = Boolean(before.available && after.available && completeForceGradient);
  const energyChangeElectronVolt = evaluationsAvailable
    ? after.deltaEnergyElectronVolt - before.deltaEnergyElectronVolt : null;
  const requiredDecreaseElectronVolt = Math.max(Number(absoluteToleranceElectronVolt),
    Number(relativeTolerance) * Math.max(1, Math.abs(before.deltaEnergyElectronVolt || 0)));
  const energyDecreased = evaluationsAvailable && responseConsistent
    && energyChangeElectronVolt < -requiredDecreaseElectronVolt;
  const beforeForceRms = evaluationsAvailable
    ? before.rmsAddedForceElectronVoltPerAngstrom : null;
  const afterForceRms = evaluationsAvailable
    ? after.rmsAddedForceElectronVoltPerAngstrom : null;
  const beforeForceP90 = evaluationsAvailable ? forceMagnitudeP90(beforeVectors) : null;
  const afterForceP90 = evaluationsAvailable ? forceMagnitudeP90(afterVectors) : null;
  const requiredRmsForceDecrease = Math.max(
    Number(absoluteForceToleranceElectronVoltPerAngstrom),
    Number(relativeForceTolerance) * Math.max(1, Math.abs(beforeForceRms || 0)));
  const requiredP90ForceDecrease = Math.max(
    Number(absoluteForceToleranceElectronVoltPerAngstrom),
    Number(relativeForceTolerance) * Math.max(1, Math.abs(beforeForceP90 || 0)));
  const rmsForceDecreased = evaluationsAvailable && responseConsistent
    && afterForceRms < beforeForceRms - requiredRmsForceDecrease;
  const p90ForceDecreased = evaluationsAvailable && responseConsistent
    && afterForceP90 < beforeForceP90 - requiredP90ForceDecrease;
  const forceResidualDecreased = rmsForceDecreased && p90ForceDecreased;
  const accepted = energyDecreased && forceResidualDecreased;
  return Object.freeze({
    available: evaluationsAvailable && responseConsistent,
    accepted,
    reason: !before.available || !after.available ? "before/after finite interaction unavailable"
      : !completeForceGradient ? "before/after complete finite interaction gradient unavailable"
      : !responseConsistent ? `induction response changed from ${before.inductionAppliedResponseModel} to ${after.inductionAppliedResponseModel}`
        : !energyDecreased ? "finite interaction energy did not decrease beyond numerical tolerance"
          : !forceResidualDecreased ? "finite interaction force residual did not decrease in both RMS and p90"
            : "finite interaction energy and force residual decreased",
    beforeEnergyElectronVolt: before.deltaEnergyElectronVolt ?? null,
    afterEnergyElectronVolt: after.deltaEnergyElectronVolt ?? null,
    energyChangeElectronVolt,
    requiredDecreaseElectronVolt,
    energyDecreased,
    forceResidualDecreased,
    rmsForceDecreased,
    p90ForceDecreased,
    beforeForceRmsElectronVoltPerAngstrom: beforeForceRms,
    afterForceRmsElectronVoltPerAngstrom: afterForceRms,
    beforeForceP90ElectronVoltPerAngstrom: beforeForceP90,
    afterForceP90ElectronVoltPerAngstrom: afterForceP90,
    requiredRmsForceDecreaseElectronVoltPerAngstrom: requiredRmsForceDecrease,
    requiredP90ForceDecreaseElectronVoltPerAngstrom: requiredP90ForceDecrease,
    completeForceGradient,
    responseConsistent,
    beforeAppliedResponseModel: before.inductionAppliedResponseModel || null,
    afterAppliedResponseModel: after.inductionAppliedResponseModel || null,
    beforePairCount: before.pairCount || 0,
    afterPairCount: after.pairCount || 0,
    pairCountChanged: (before.pairCount || 0) !== (after.pairCount || 0),
    proposedEnergyDistanceEvaluations: after.distanceEvaluations || 0,
    proposedEnergyMutualTensorEvaluations: after.inductionMutualTensorEvaluations || 0,
    proposedForceEnergyEvaluations: after.inductionForceEnergyEvaluations || 0,
    atomIdentityPreserved: true,
    currentConfigurationHeldFixed: true,
    energyMinimized: false,
    forceIntegratedAsTime: false,
    targetUsed: false,
    claimBoundary: "This is a before/after energy-and-force-residual descent certificate for the movable emitted sites under one declared finite interaction hypothesis while the existing configuration is fixed. It is not a total-system force audit, proof of a local or global minimum, force balance, mechanical equilibrium, a relaxation path, or physical time.",
  });
}

// Backward-compatible name retained for receipts and saved research notebooks.
export const auditModelForceRelaxationEnergyDescent = auditModelForceRelaxationOutcome;
