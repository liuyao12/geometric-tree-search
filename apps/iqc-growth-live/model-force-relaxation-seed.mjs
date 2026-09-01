import { incrementalFinitePointChargeElectrostatics }
  from "./finite-point-charge-electrostatics.mjs?v=20260901-431";
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
