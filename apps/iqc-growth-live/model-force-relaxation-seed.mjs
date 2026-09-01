import { incrementalFinitePointChargeElectrostatics }
  from "./finite-point-charge-electrostatics.mjs?v=20260901-439";
import { boundedForceSeedOffset, forceMagnitudeP90 }
  from "./force-seed-geometry.js?v=20260827-1";

const finiteVector = (value) => Array.isArray(value) && value.length === 3
  && value.every(Number.isFinite);

const vectorRms = (vectors) => Math.sqrt(vectors.reduce((sum, vector) =>
  sum + vector.reduce((inner, value) => inner + value * value, 0), 0)
  / Math.max(1, vectors.length));
const addVector = (first, second) => first.map((value, axis) => value + second[axis]);
const subtractVector = (first, second) => first.map((value, axis) => value - second[axis]);
const crossVector = (first, second) => [
  first[1] * second[2] - first[2] * second[1],
  first[2] * second[0] - first[0] * second[2],
  first[0] * second[1] - first[1] * second[0],
];
const vectorMagnitude = (vector) => Math.hypot(...vector);

function groupResultant(positions, forces) {
  const count = forces.length;
  const centroid = positions.reduce(addVector, [0, 0, 0]).map((value) => value / count);
  const netForce = forces.reduce(addVector, [0, 0, 0]);
  const torque = positions.reduce((sum, position, index) => addVector(sum,
    crossVector(subtractVector(position, centroid), forces[index])), [0, 0, 0]);
  const rmsRadiusAngstrom = Math.sqrt(positions.reduce((sum, position) =>
    sum + vectorMagnitude(subtractVector(position, centroid)) ** 2, 0) / count);
  return Object.freeze({
    netForceElectronVoltPerAngstrom: Object.freeze(netForce),
    netForceMagnitudeElectronVoltPerAngstrom: vectorMagnitude(netForce),
    netForcePerSiteElectronVoltPerAngstrom: vectorMagnitude(netForce) / count,
    centroidalTorqueElectronVolt: Object.freeze(torque),
    centroidalTorqueMagnitudeElectronVolt: vectorMagnitude(torque),
    rmsRadiusAngstrom,
    normalizedTorqueResidualElectronVoltPerAngstrom: rmsRadiusAngstrom > 1e-12
      ? vectorMagnitude(torque) / (count * rmsRadiusAngstrom) : 0,
  });
}

/**
 * Check that a lower aggregate residual was not obtained by exporting force
 * into one declared movable population. Group labels carry no geometry and are
 * fixed before the proposed coordinates are evaluated.
 */
export function auditGroupedForceResiduals(beforeVectors, afterVectors, groupLabels, {
  absoluteToleranceElectronVoltPerAngstrom = 1e-10,
  relativeTolerance = 1e-10,
  beforePositions = null,
  afterPositions = null,
} = {}) {
  if (!Array.isArray(beforeVectors) || !Array.isArray(afterVectors)
      || beforeVectors.length !== afterVectors.length
      || !beforeVectors.every(finiteVector) || !afterVectors.every(finiteVector)) {
    throw new Error("grouped force audit requires complete paired finite force vectors");
  }
  if (!Array.isArray(groupLabels) || groupLabels.length !== beforeVectors.length) {
    throw new Error("grouped force audit requires one frozen group label per force vector");
  }
  const positionsSupplied = beforePositions != null || afterPositions != null;
  if (positionsSupplied && (!Array.isArray(beforePositions) || !Array.isArray(afterPositions)
      || beforePositions.length !== beforeVectors.length
      || afterPositions.length !== afterVectors.length
      || !beforePositions.every(finiteVector) || !afterPositions.every(finiteVector))) {
    throw new Error("grouped force-resultant audit requires complete paired finite positions");
  }
  const labels = groupLabels.map((label) => String(label));
  if (labels.some((label) => !label.length)) throw new Error("force group labels must be nonempty");
  const uniqueLabels = [...new Set(labels)].sort();
  const groups = uniqueLabels.map((label) => {
    const indices = labels.map((candidate, index) => candidate === label ? index : -1)
      .filter((index) => index >= 0);
    const before = indices.map((index) => beforeVectors[index]);
    const after = indices.map((index) => afterVectors[index]);
    const beforeRms = vectorRms(before);
    const afterRms = vectorRms(after);
    const beforeP90 = forceMagnitudeP90(before);
    const afterP90 = forceMagnitudeP90(after);
    const rmsTolerance = Math.max(Number(absoluteToleranceElectronVoltPerAngstrom),
      Number(relativeTolerance) * Math.max(1, Math.abs(beforeRms)));
    const p90Tolerance = Math.max(Number(absoluteToleranceElectronVoltPerAngstrom),
      Number(relativeTolerance) * Math.max(1, Math.abs(beforeP90)));
    const beforeResultant = positionsSupplied
      ? groupResultant(indices.map((index) => beforePositions[index]), before) : null;
    const afterResultant = positionsSupplied
      ? groupResultant(indices.map((index) => afterPositions[index]), after) : null;
    const netForceTolerance = beforeResultant ? Math.max(
      Number(absoluteToleranceElectronVoltPerAngstrom), Number(relativeTolerance)
        * Math.max(1, beforeResultant.netForcePerSiteElectronVoltPerAngstrom)) : null;
    const torqueTolerance = beforeResultant ? Math.max(
      Number(absoluteToleranceElectronVoltPerAngstrom), Number(relativeTolerance)
        * Math.max(1, beforeResultant.normalizedTorqueResidualElectronVoltPerAngstrom)) : null;
    const netForceNonIncreasing = beforeResultant ? afterResultant.netForcePerSiteElectronVoltPerAngstrom
      <= beforeResultant.netForcePerSiteElectronVoltPerAngstrom + netForceTolerance : null;
    const normalizedTorqueNonIncreasing = beforeResultant
      ? afterResultant.normalizedTorqueResidualElectronVoltPerAngstrom
        <= beforeResultant.normalizedTorqueResidualElectronVoltPerAngstrom + torqueTolerance
      : null;
    return Object.freeze({
      label,
      sites: indices.length,
      beforeRmsElectronVoltPerAngstrom: beforeRms,
      afterRmsElectronVoltPerAngstrom: afterRms,
      beforeP90ElectronVoltPerAngstrom: beforeP90,
      afterP90ElectronVoltPerAngstrom: afterP90,
      rmsChangeElectronVoltPerAngstrom: afterRms - beforeRms,
      p90ChangeElectronVoltPerAngstrom: afterP90 - beforeP90,
      rmsNonIncreasing: afterRms <= beforeRms + rmsTolerance,
      p90NonIncreasing: afterP90 <= beforeP90 + p90Tolerance,
      residualNonIncreasing: afterRms <= beforeRms + rmsTolerance
        && afterP90 <= beforeP90 + p90Tolerance,
      beforeResultant,
      afterResultant,
      netForcePerSiteChangeElectronVoltPerAngstrom: beforeResultant
        ? afterResultant.netForcePerSiteElectronVoltPerAngstrom
          - beforeResultant.netForcePerSiteElectronVoltPerAngstrom : null,
      normalizedTorqueChangeElectronVoltPerAngstrom: beforeResultant
        ? afterResultant.normalizedTorqueResidualElectronVoltPerAngstrom
          - beforeResultant.normalizedTorqueResidualElectronVoltPerAngstrom : null,
      netForceNonIncreasing,
      normalizedTorqueNonIncreasing,
      resultantNonIncreasing: beforeResultant
        ? netForceNonIncreasing && normalizedTorqueNonIncreasing : null,
    });
  });
  const residualPassed = groups.every((group) => group.residualNonIncreasing);
  const resultantPassed = positionsSupplied
    ? groups.every((group) => group.resultantNonIncreasing) : null;
  return Object.freeze({
    available: true,
    passed: residualPassed && (!positionsSupplied || resultantPassed),
    residualPassed,
    resultantAvailable: positionsSupplied,
    resultantPassed,
    groups: Object.freeze(groups),
    groupCount: groups.length,
    groupLabelsFrozenBeforeProposal: true,
    targetUsed: false,
    claimBoundary: "This audit prevents a lower aggregate force residual from hiding increased RMS, p90, net-force-per-site, or normalized centroidal torque in a declared movable population. It is not atomwise force balance, virial stress equilibrium, an elastic response, or dynamics.",
  });
}

/**
 * Convert a complete finite interaction gradient into a bounded geometric
 * seed. This proposes coordinates only; the caller must still minimize its
 * declared local objective and re-run every hard geometric certificate.
 */
export function buildModelForceRelaxationSeed(currentSites, addedSites, {
  displacementCap,
  displacementCaps = null,
  electrostaticsOptions = {},
} = {}) {
  if (!(Number.isFinite(displacementCap) && displacementCap > 0)) {
    throw new RangeError("model-force relaxation needs a positive displacement cap");
  }
  const caps = displacementCaps == null ? addedSites.map(() => displacementCap)
    : displacementCaps.map(Number);
  if (caps.length !== addedSites.length || caps.some((cap) =>
    !(Number.isFinite(cap) && cap > 0 && cap <= displacementCap))) {
    throw new RangeError("model-force per-site caps must be positive, complete, and no larger than the global cap");
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
    displacementCaps: Object.freeze([...caps]),
    heterogeneousDisplacementCaps: new Set(caps).size > 1,
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
  const offsets = vectors.map((vector, index) => Object.freeze(
    boundedForceSeedOffset(vector, scale, caps[index])));
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
    displacementCaps: Object.freeze([...caps]),
    heterogeneousDisplacementCaps: new Set(caps).size > 1,
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
    forceGroupLabels = null,
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
  const groupedForceResidual = evaluationsAvailable && responseConsistent
    ? auditGroupedForceResiduals(beforeVectors, afterVectors,
      forceGroupLabels || originalAddedSites.map(() => "movable"), {
        absoluteToleranceElectronVoltPerAngstrom:
          absoluteForceToleranceElectronVoltPerAngstrom,
        relativeTolerance: relativeForceTolerance,
        beforePositions: originalAddedSites.map((site) => site.position),
        afterPositions: proposedAddedSites.map((site) => site.position),
      }) : null;
  const forceResidualRedistributionPassed = Boolean(groupedForceResidual?.residualPassed);
  const forceResultantRedistributionPassed = Boolean(groupedForceResidual?.resultantPassed);
  const accepted = energyDecreased && forceResidualDecreased
    && forceResidualRedistributionPassed && forceResultantRedistributionPassed;
  return Object.freeze({
    available: evaluationsAvailable && responseConsistent,
    accepted,
    reason: !before.available || !after.available ? "before/after finite interaction unavailable"
      : !completeForceGradient ? "before/after complete finite interaction gradient unavailable"
      : !responseConsistent ? `induction response changed from ${before.inductionAppliedResponseModel} to ${after.inductionAppliedResponseModel}`
        : !energyDecreased ? "finite interaction energy did not decrease beyond numerical tolerance"
          : !forceResidualDecreased ? "finite interaction force residual did not decrease in both RMS and p90"
            : !forceResidualRedistributionPassed
              ? "force residual increased in at least one declared movable population"
              : !forceResultantRedistributionPassed
                ? "net force or normalized centroidal torque increased in at least one declared movable population"
            : "finite interaction energy and force residual decreased",
    beforeEnergyElectronVolt: before.deltaEnergyElectronVolt ?? null,
    afterEnergyElectronVolt: after.deltaEnergyElectronVolt ?? null,
    energyChangeElectronVolt,
    requiredDecreaseElectronVolt,
    energyDecreased,
    forceResidualDecreased,
    forceResidualRedistributionPassed,
    forceResultantRedistributionPassed,
    forceGroupResultantsAvailable: Boolean(groupedForceResidual?.resultantAvailable),
    forceGroupResiduals: groupedForceResidual?.groups || Object.freeze([]),
    forceGroupCount: groupedForceResidual?.groupCount || 0,
    forceGroupLabelsFrozenBeforeProposal:
      groupedForceResidual?.groupLabelsFrozenBeforeProposal || false,
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
    claimBoundary: "This is a before/after energy-and-force-residual descent certificate for the declared movable group—emitted sites and, when explicitly enabled, a bounded substrate shell—under one finite interaction hypothesis while every other site is fixed. It is not a total-system force audit, proof of a local or global minimum, force balance, mechanical equilibrium, a relaxation path, or physical time.",
  });
}

// Backward-compatible name retained for receipts and saved research notebooks.
export const auditModelForceRelaxationEnergyDescent = auditModelForceRelaxationOutcome;

/**
 * Resolve the endpoint leap into a small, fixed set of geometric images. Every
 * consecutive image must pass the same energy, complete-force, population,
 * resultant, and torque audit. The image parameter is not interpreted as time.
 */
export function auditModelForceRelaxationPath(
  currentSites, originalAddedSites, proposedAddedSites, {
    imageCount = 7,
    forceGroupLabels = null,
    electrostaticsOptions = {},
    ...auditOptions
  } = {}) {
  if (!(Number.isInteger(imageCount) && imageCount >= 3 && imageCount <= 17)) {
    throw new RangeError("model-force response path needs 3 to 17 images");
  }
  if (originalAddedSites.length !== proposedAddedSites.length) {
    throw new Error("model-force response path needs paired movable sites");
  }
  const images = Array.from({ length: imageCount }, (_, imageIndex) => {
    const fraction = imageIndex / (imageCount - 1);
    const sites = originalAddedSites.map((site, siteIndex) => {
      const proposed = proposedAddedSites[siteIndex];
      if (String(site.species) !== String(proposed.species)
          || Number(site.charge) !== Number(proposed.charge)) {
        throw new Error("model-force response path cannot change movable-site identity or charge");
      }
      return Object.freeze({ ...site, position: Object.freeze(site.position.map((value, axis) =>
        value + fraction * (proposed.position[axis] - value))) });
    });
    return Object.freeze({ imageIndex, fraction, sites: Object.freeze(sites) });
  });
  const segments = [];
  for (let index = 0; index < images.length - 1; index++) {
    const audit = auditModelForceRelaxationOutcome(currentSites,
      images[index].sites, images[index + 1].sites, {
        ...auditOptions,
        electrostaticsOptions,
        forceGroupLabels,
      });
    segments.push(Object.freeze({
      segmentIndex: index,
      fromFraction: images[index].fraction,
      toFraction: images[index + 1].fraction,
      accepted: audit.accepted,
      reason: audit.reason,
      beforeEnergyElectronVolt: audit.beforeEnergyElectronVolt,
      afterEnergyElectronVolt: audit.afterEnergyElectronVolt,
      beforeForceRmsElectronVoltPerAngstrom: audit.beforeForceRmsElectronVoltPerAngstrom,
      afterForceRmsElectronVoltPerAngstrom: audit.afterForceRmsElectronVoltPerAngstrom,
      beforeForceP90ElectronVoltPerAngstrom: audit.beforeForceP90ElectronVoltPerAngstrom,
      afterForceP90ElectronVoltPerAngstrom: audit.afterForceP90ElectronVoltPerAngstrom,
      forceResidualRedistributionPassed: audit.forceResidualRedistributionPassed,
      forceResultantRedistributionPassed: audit.forceResultantRedistributionPassed,
      responseConsistent: audit.responseConsistent,
      completeForceGradient: audit.completeForceGradient,
      forceGroupResiduals: audit.forceGroupResiduals,
    }));
  }
  const accepted = segments.every((segment) => segment.accepted);
  const firstFailure = segments.find((segment) => !segment.accepted) || null;
  return Object.freeze({
    available: segments.every((segment) => segment.completeForceGradient
      && segment.responseConsistent),
    accepted,
    reason: accepted
      ? "every bounded response-path segment passed energy, force, population, resultant, and torque descent"
      : `response-path segment ${firstFailure?.segmentIndex ?? "?"} failed: ${firstFailure?.reason || "unavailable"}`,
    imageCount,
    segmentCount: segments.length,
    fractions: Object.freeze(images.map((image) => image.fraction)),
    segments: Object.freeze(segments),
    everySegmentEnergyForceDescent: accepted,
    groupLabelsFrozenBeforePath: true,
    straightLineCartesianImages: true,
    pathParameterIsPhysicalTime: false,
    targetUsed: false,
    claimBoundary: "The fixed Cartesian image sequence is a bounded continuity and monotonicity check between two coordinate sets. It is not a minimum-energy path, transition state, dynamics, rate, or elapsed physical time.",
  });
}
