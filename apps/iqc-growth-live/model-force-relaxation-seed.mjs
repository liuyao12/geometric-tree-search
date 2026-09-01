import { incrementalFinitePointChargeElectrostatics }
  from "./finite-point-charge-electrostatics.mjs?v=20260901-432";
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
export function auditModelForceRelaxationEnergyDescent(
  currentSites, originalAddedSites, proposedAddedSites, {
    baselineEvaluation = null,
    electrostaticsOptions = {},
    absoluteToleranceElectronVolt = 1e-10,
    relativeTolerance = 1e-10,
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
  const energyOptions = { ...electrostaticsOptions, inductionForceMode: "omitted" };
  const before = baselineEvaluation || incrementalFinitePointChargeElectrostatics(
    currentSites, originalAddedSites, energyOptions);
  const after = incrementalFinitePointChargeElectrostatics(
    currentSites, proposedAddedSites, energyOptions);
  const inductionActive = Number(before.inductionPolarizabilityAngstrom3) > 0;
  const responseConsistent = !inductionActive
    || before.inductionAppliedResponseModel === after.inductionAppliedResponseModel;
  const evaluationsAvailable = Boolean(before.available && after.available);
  const energyChangeElectronVolt = evaluationsAvailable
    ? after.deltaEnergyElectronVolt - before.deltaEnergyElectronVolt : null;
  const requiredDecreaseElectronVolt = Math.max(Number(absoluteToleranceElectronVolt),
    Number(relativeTolerance) * Math.max(1, Math.abs(before.deltaEnergyElectronVolt || 0)));
  const energyDecreased = evaluationsAvailable && responseConsistent
    && energyChangeElectronVolt < -requiredDecreaseElectronVolt;
  return Object.freeze({
    available: evaluationsAvailable && responseConsistent,
    accepted: energyDecreased,
    reason: !evaluationsAvailable ? "before/after finite interaction energy unavailable"
      : !responseConsistent ? `induction response changed from ${before.inductionAppliedResponseModel} to ${after.inductionAppliedResponseModel}`
        : energyDecreased ? "finite interaction energy decreased"
          : "finite interaction energy did not decrease beyond numerical tolerance",
    beforeEnergyElectronVolt: before.deltaEnergyElectronVolt ?? null,
    afterEnergyElectronVolt: after.deltaEnergyElectronVolt ?? null,
    energyChangeElectronVolt,
    requiredDecreaseElectronVolt,
    responseConsistent,
    beforeAppliedResponseModel: before.inductionAppliedResponseModel || null,
    afterAppliedResponseModel: after.inductionAppliedResponseModel || null,
    beforePairCount: before.pairCount || 0,
    afterPairCount: after.pairCount || 0,
    pairCountChanged: (before.pairCount || 0) !== (after.pairCount || 0),
    proposedEnergyDistanceEvaluations: after.distanceEvaluations || 0,
    proposedEnergyMutualTensorEvaluations: after.inductionMutualTensorEvaluations || 0,
    atomIdentityPreserved: true,
    currentConfigurationHeldFixed: true,
    energyMinimized: false,
    forceIntegratedAsTime: false,
    targetUsed: false,
    claimBoundary: "This is a before/after descent certificate for one bounded proposal under the same declared finite interaction hypothesis. It is not proof of a local or global minimum, force balance, mechanical equilibrium, a relaxation path, or physical time.",
  });
}
