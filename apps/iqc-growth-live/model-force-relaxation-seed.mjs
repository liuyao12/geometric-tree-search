import { incrementalFinitePointChargeElectrostatics }
  from "./finite-point-charge-electrostatics.mjs?v=20260901-443";
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
const dotVector = (first, second) => first.reduce((sum, value, axis) =>
  sum + value * second[axis], 0);
const zeroMatrix = () => [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
const matrixFrobenius = (matrix) => Math.sqrt(matrix.reduce((sum, row) =>
  sum + row.reduce((inner, value) => inner + value * value, 0), 0));

const linearClosestApproach = (start, end) => {
  const delta = end.map((value, axis) => value - start[axis]);
  const denominator = dotVector(delta, delta);
  const parameter = denominator > 1e-24
    ? Math.max(0, Math.min(1, -dotVector(start, delta) / denominator)) : 0;
  const vector = start.map((value, axis) => value + parameter * delta[axis]);
  return Object.freeze({ parameter, distanceAngstrom: vectorMagnitude(vector) });
};

/** Prove that no evaluated pair enters or leaves a declared hard reach. */
export function auditFiniteReachPathTopology(currentSites, originalAddedSites,
  proposedAddedSites, reachAngstrom, { toleranceAngstrom = 1e-10 } = {}) {
  if (reachAngstrom === "global" || reachAngstrom === Infinity) return Object.freeze({
    available: true, passed: true, finiteReach: false, pairChecks: 0,
    activePairs: null, inactivePairs: null, minimumCutoffClearanceAngstrom: null,
    crossingPairs: Object.freeze([]), analyticClosestApproach: true,
    targetUsed: false,
    reason: "global reach has no finite pair-membership boundary",
  });
  const reach = Number(reachAngstrom);
  if (!(Number.isFinite(reach) && reach > 0)) {
    throw new RangeError("finite reach topology audit needs positive reach or global");
  }
  if (!Array.isArray(currentSites) || !Array.isArray(originalAddedSites)
      || !Array.isArray(proposedAddedSites)
      || originalAddedSites.length !== proposedAddedSites.length) {
    throw new Error("finite reach topology audit needs paired movable sites");
  }
  const pairs = [];
  const addPair = (pairId, firstStart, firstEnd, secondStart, secondEnd) => {
    if (![firstStart, firstEnd, secondStart, secondEnd].every(finiteVector)) {
      throw new Error("finite reach topology audit needs finite Cartesian positions");
    }
    const relativeStart = subtractVector(firstStart, secondStart);
    const relativeEnd = subtractVector(firstEnd, secondEnd);
    const startDistance = vectorMagnitude(relativeStart);
    const endDistance = vectorMagnitude(relativeEnd);
    const closest = linearClosestApproach(relativeStart, relativeEnd);
    const startActive = startDistance <= reach;
    const endActive = endDistance <= reach;
    const stableActive = startActive && endActive
      && reach - Math.max(startDistance, endDistance) > Number(toleranceAngstrom);
    const stableInactive = !startActive && !endActive
      && closest.distanceAngstrom > reach + Number(toleranceAngstrom);
    const stable = stableActive || stableInactive;
    const clearance = stableActive
      ? reach - Math.max(startDistance, endDistance)
      : closest.distanceAngstrom - reach;
    pairs.push(Object.freeze({ pairId, startActive, endActive, stable,
      startDistanceAngstrom: startDistance, endDistanceAngstrom: endDistance,
      closestDistanceAngstrom: closest.distanceAngstrom,
      closestParameter: closest.parameter, cutoffClearanceAngstrom: clearance }));
  };
  originalAddedSites.forEach((site, addedIndex) => currentSites.forEach((neighbor,
    currentIndex) => addPair(`added-${addedIndex}:current-${currentIndex}`,
    site.position, proposedAddedSites[addedIndex].position,
    neighbor.position, neighbor.position)));
  originalAddedSites.forEach((site, firstIndex) => originalAddedSites
    .slice(firstIndex + 1).forEach((neighbor, relativeIndex) => {
      const secondIndex = firstIndex + relativeIndex + 1;
      addPair(`added-${firstIndex}:added-${secondIndex}`,
        site.position, proposedAddedSites[firstIndex].position,
        neighbor.position, proposedAddedSites[secondIndex].position);
    }));
  const crossingPairs = pairs.filter((pair) => !pair.stable);
  const activePairs = pairs.filter((pair) => pair.startActive && pair.endActive).length;
  return Object.freeze({
    available: true,
    passed: crossingPairs.length === 0,
    finiteReach: true,
    reachAngstrom: reach,
    pairChecks: pairs.length,
    activePairs,
    inactivePairs: pairs.length - activePairs,
    minimumCutoffClearanceAngstrom: pairs.length
      ? Math.min(...pairs.map((pair) => pair.cutoffClearanceAngstrom)) : null,
    crossingPairs: Object.freeze(crossingPairs),
    analyticClosestApproach: true,
    targetUsed: false,
    reason: crossingPairs.length
      ? `${crossingPairs.length} pair path${crossingPairs.length === 1 ? "" : "s"} enter or leave the hard interaction reach`
      : "every pair remains continuously inside or outside the hard interaction reach",
    claimBoundary: "This is an analytic membership-continuity certificate for a declared finite hard reach. It does not make a truncated potential smooth at the cutoff, infer a switching function, or establish dynamics or time.",
  });
}

function centeredSymmetricForceMoment(positions, forces, centroid) {
  const matrix = zeroMatrix();
  positions.forEach((position, index) => {
    const radius = subtractVector(position, centroid);
    const force = forces[index];
    for (let row = 0; row < 3; row += 1) {
      for (let column = 0; column < 3; column += 1) {
        matrix[row][column] += .5 * (radius[row] * force[column]
          + force[row] * radius[column]);
      }
    }
  });
  const trace = matrix[0][0] + matrix[1][1] + matrix[2][2];
  const hydrostatic = trace / 3;
  const deviatoric = matrix.map((row, rowIndex) => row.map((value, columnIndex) =>
    value - (rowIndex === columnIndex ? hydrostatic : 0)));
  return Object.freeze({
    matrixElectronVolt: Object.freeze(matrix.map((row) => Object.freeze(row))),
    traceElectronVolt: trace,
    frobeniusElectronVolt: matrixFrobenius(matrix),
    hydrostaticFrobeniusElectronVolt: Math.abs(trace) / Math.sqrt(3),
    deviatoricFrobeniusElectronVolt: matrixFrobenius(deviatoric),
  });
}

/**
 * Integrate the complete movable-site force along one fixed Cartesian path and
 * compare that work with the independently evaluated endpoint energy change.
 * A fine Simpson rule and its embedded half-density Simpson rule provide a
 * Richardson-scaled finite quadrature error estimate. Trapezoid work remains
 * visible as a lower-order diagnostic, never as the acceptance allowance.
 */
export function auditForceEnergyPathClosure(fractions, energiesElectronVolt,
  forceFieldsElectronVoltPerAngstrom, displacementVectorsAngstrom, {
    absoluteToleranceElectronVolt = 1e-10,
    relativeTolerance = 1e-10,
  } = {}) {
  if (!Array.isArray(fractions) || fractions.length < 5
      || (fractions.length - 1) % 4 !== 0
      || !fractions.every(Number.isFinite)) {
    throw new Error("force-energy path closure needs 4k+1 equally spaced images (at least five)");
  }
  if (!Array.isArray(energiesElectronVolt) || energiesElectronVolt.length !== fractions.length
      || !energiesElectronVolt.every(Number.isFinite)) {
    throw new Error("force-energy path closure needs one finite energy per image");
  }
  if (!Array.isArray(displacementVectorsAngstrom)
      || !displacementVectorsAngstrom.every(finiteVector)
      || !Array.isArray(forceFieldsElectronVoltPerAngstrom)
      || forceFieldsElectronVoltPerAngstrom.length !== fractions.length
      || !forceFieldsElectronVoltPerAngstrom.every((field) =>
        Array.isArray(field) && field.length === displacementVectorsAngstrom.length
        && field.every(finiteVector))) {
    throw new Error("force-energy path closure needs complete paired displacement and force vectors");
  }
  const interval = 1 / (fractions.length - 1);
  if (fractions.some((fraction, index) =>
    Math.abs(fraction - index * interval) > 1e-12)) {
    throw new Error("force-energy path closure needs equally spaced fractions from zero to one");
  }
  const forcePathIntegrandElectronVolt = forceFieldsElectronVoltPerAngstrom.map((field) =>
    field.reduce((sum, force, index) =>
      sum + dotVector(force, displacementVectorsAngstrom[index]), 0));
  const lastIndex = forcePathIntegrandElectronVolt.length - 1;
  const trapezoidWorkElectronVolt = interval * forcePathIntegrandElectronVolt.reduce((sum, value, index) =>
    sum + ((index === 0 || index === lastIndex) ? .5 : 1) * value, 0);
  const simpsonWorkElectronVolt = interval / 3 * forcePathIntegrandElectronVolt.reduce(
    (sum, value, index) => sum + (index === 0 || index === lastIndex
      ? 1 : index % 2 === 1 ? 4 : 2) * value, 0);
  const coarseForcePathIntegrandElectronVolt = forcePathIntegrandElectronVolt
    .filter((_, index) => index % 2 === 0);
  const coarseLastIndex = coarseForcePathIntegrandElectronVolt.length - 1;
  const coarseSimpsonWorkElectronVolt = 2 * interval / 3
    * coarseForcePathIntegrandElectronVolt.reduce((sum, value, index) =>
      sum + (index === 0 || index === coarseLastIndex
        ? 1 : index % 2 === 1 ? 4 : 2) * value, 0);
  const energyChangeElectronVolt = energiesElectronVolt[lastIndex] - energiesElectronVolt[0];
  const closureResidualElectronVolt = simpsonWorkElectronVolt + energyChangeElectronVolt;
  const nestedSimpsonDifferenceElectronVolt = Math.abs(
    simpsonWorkElectronVolt - coarseSimpsonWorkElectronVolt);
  const richardsonErrorEstimateElectronVolt = nestedSimpsonDifferenceElectronVolt / 15;
  const numericalToleranceElectronVolt = Math.max(Number(absoluteToleranceElectronVolt),
    Number(relativeTolerance) * Math.max(1, Math.abs(energyChangeElectronVolt),
      Math.abs(simpsonWorkElectronVolt)));
  const allowedClosureResidualElectronVolt = numericalToleranceElectronVolt
    + richardsonErrorEstimateElectronVolt;
  const passed = Math.abs(closureResidualElectronVolt)
    <= allowedClosureResidualElectronVolt;
  return Object.freeze({
    available: true,
    passed,
    reason: passed
      ? "force work closes the endpoint energy change within nested-Simpson Richardson error"
      : "integrated force work does not close the endpoint energy change",
    imageCount: fractions.length,
    forcePathIntegrandElectronVolt: Object.freeze(forcePathIntegrandElectronVolt),
    simpsonWorkElectronVolt,
    coarseSimpsonWorkElectronVolt,
    fineSimpsonImageCount: fractions.length,
    coarseSimpsonImageCount: coarseForcePathIntegrandElectronVolt.length,
    trapezoidWorkElectronVolt,
    energyChangeElectronVolt,
    closureResidualElectronVolt,
    absoluteClosureResidualElectronVolt: Math.abs(closureResidualElectronVolt),
    nestedSimpsonDifferenceElectronVolt,
    richardsonErrorEstimateElectronVolt,
    quadratureDiscrepancyElectronVolt: nestedSimpsonDifferenceElectronVolt,
    numericalToleranceElectronVolt,
    allowedClosureResidualElectronVolt,
    forceWorkSignConvention: "positive work by the finite force; expected W = -delta U",
    equallySpacedCartesianPath: true,
    nestedSimpsonConvergenceAvailable: true,
    richardsonDivisor: 15,
    pathParameterIsPhysicalTime: false,
    targetUsed: false,
    claimBoundary: "This is a nested finite-quadrature consistency check between one declared energy and its complete movable-site force along a fixed Cartesian coordinate path. The fine/coarse Simpson difference divided by 15 is a smooth-integrand numerical error estimate, not physical uncertainty. It is not thermodynamic work, free energy, a minimum-energy path, dynamics, rate, or physical time.",
  });
}

function groupResultant(positions, forces) {
  const count = forces.length;
  const centroid = positions.reduce(addVector, [0, 0, 0]).map((value) => value / count);
  const netForce = forces.reduce(addVector, [0, 0, 0]);
  const torque = positions.reduce((sum, position, index) => addVector(sum,
    crossVector(subtractVector(position, centroid), forces[index])), [0, 0, 0]);
  const rmsRadiusAngstrom = Math.sqrt(positions.reduce((sum, position) =>
    sum + vectorMagnitude(subtractVector(position, centroid)) ** 2, 0) / count);
  const symmetricForceMoment = centeredSymmetricForceMoment(positions, forces, centroid);
  const momentNormalizationAngstrom = count * rmsRadiusAngstrom;
  return Object.freeze({
    netForceElectronVoltPerAngstrom: Object.freeze(netForce),
    netForceMagnitudeElectronVoltPerAngstrom: vectorMagnitude(netForce),
    netForcePerSiteElectronVoltPerAngstrom: vectorMagnitude(netForce) / count,
    centroidalTorqueElectronVolt: Object.freeze(torque),
    centroidalTorqueMagnitudeElectronVolt: vectorMagnitude(torque),
    rmsRadiusAngstrom,
    normalizedTorqueResidualElectronVoltPerAngstrom: rmsRadiusAngstrom > 1e-12
      ? vectorMagnitude(torque) / (count * rmsRadiusAngstrom) : 0,
    centeredSymmetricForceMoment: symmetricForceMoment,
    normalizedSymmetricForceMomentElectronVoltPerAngstrom:
      momentNormalizationAngstrom > 1e-12
        ? symmetricForceMoment.frobeniusElectronVolt / momentNormalizationAngstrom : 0,
    normalizedHydrostaticForceMomentElectronVoltPerAngstrom:
      momentNormalizationAngstrom > 1e-12
        ? symmetricForceMoment.hydrostaticFrobeniusElectronVolt / momentNormalizationAngstrom : 0,
    normalizedDeviatoricForceMomentElectronVoltPerAngstrom:
      momentNormalizationAngstrom > 1e-12
        ? symmetricForceMoment.deviatoricFrobeniusElectronVolt / momentNormalizationAngstrom : 0,
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
    const momentAbsoluteToleranceElectronVolt = beforeResultant
      ? Number(absoluteToleranceElectronVoltPerAngstrom) * indices.length
        * Math.max(1, beforeResultant.rmsRadiusAngstrom) : null;
    const momentMetric = (resultant, name) =>
      resultant.centeredSymmetricForceMoment[name];
    const momentNonIncreasing = beforeResultant ? [
      "frobeniusElectronVolt", "hydrostaticFrobeniusElectronVolt",
      "deviatoricFrobeniusElectronVolt",
    ].every((name) => {
      const beforeValue = momentMetric(beforeResultant, name);
      const afterValue = momentMetric(afterResultant, name);
      const tolerance = Math.max(momentAbsoluteToleranceElectronVolt,
        Number(relativeTolerance) * Math.max(1, Math.abs(beforeValue)));
      return afterValue <= beforeValue + tolerance;
    }) : null;
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
      centeredSymmetricForceMomentNonIncreasing: momentNonIncreasing,
    });
  });
  const residualPassed = groups.every((group) => group.residualNonIncreasing);
  const resultantPassed = positionsSupplied
    ? groups.every((group) => group.resultantNonIncreasing) : null;
  const symmetricForceMomentPassed = positionsSupplied
    ? groups.every((group) => group.centeredSymmetricForceMomentNonIncreasing) : null;
  return Object.freeze({
    available: true,
    passed: residualPassed && (!positionsSupplied
      || (resultantPassed && symmetricForceMomentPassed)),
    residualPassed,
    resultantAvailable: positionsSupplied,
    resultantPassed,
    symmetricForceMomentAvailable: positionsSupplied,
    symmetricForceMomentPassed,
    groups: Object.freeze(groups),
    groupCount: groups.length,
    groupLabelsFrozenBeforeProposal: true,
    targetUsed: false,
    claimBoundary: "This audit prevents a lower aggregate force residual from hiding increased RMS, p90, net-force-per-site, normalized centroidal torque, or centered symmetric force moment in a declared movable population. The force×length moment is not divided by a volume and is therefore not stress, pressure, a virial-stress equilibrium, an elastic response, or dynamics.",
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
    proposedEvaluation = null,
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
  const after = proposedEvaluation || incrementalFinitePointChargeElectrostatics(
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
  const symmetricForceMomentRedistributionPassed = Boolean(
    groupedForceResidual?.symmetricForceMomentPassed);
  const accepted = energyDecreased && forceResidualDecreased
    && forceResidualRedistributionPassed && forceResultantRedistributionPassed
    && symmetricForceMomentRedistributionPassed;
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
                : !symmetricForceMomentRedistributionPassed
                  ? "centered symmetric force moment increased in at least one declared movable population"
            : "finite interaction energy and force residual decreased",
    beforeEnergyElectronVolt: before.deltaEnergyElectronVolt ?? null,
    afterEnergyElectronVolt: after.deltaEnergyElectronVolt ?? null,
    energyChangeElectronVolt,
    requiredDecreaseElectronVolt,
    energyDecreased,
    forceResidualDecreased,
    forceResidualRedistributionPassed,
    forceResultantRedistributionPassed,
    symmetricForceMomentRedistributionPassed,
    forceGroupSymmetricMomentsAvailable: Boolean(
      groupedForceResidual?.symmetricForceMomentAvailable),
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
    claimBoundary: "This is a before/after energy-and-force-residual descent certificate for the declared movable group—emitted sites and, when explicitly enabled, a bounded substrate shell—under one finite interaction hypothesis while every other site is fixed. Its centered symmetric force moment has force×length units and no inferred control volume, so it is not stress or pressure. It is not a total-system force audit, proof of a local or global minimum, force balance, mechanical equilibrium, a relaxation path, or physical time.",
  });
}

// Backward-compatible name retained for receipts and saved research notebooks.
export const auditModelForceRelaxationEnergyDescent = auditModelForceRelaxationOutcome;

/**
 * Resolve the endpoint leap into a small, fixed set of geometric images. Every
 * consecutive image must pass the same energy, complete-force, population,
 * resultant, torque, and centered symmetric force-moment audit. The image
 * parameter is not interpreted as time.
 */
export function auditModelForceRelaxationPath(
  currentSites, originalAddedSites, proposedAddedSites, {
    imageCount = 7,
    forceGroupLabels = null,
    electrostaticsOptions = {},
    ...auditOptions
  } = {}) {
  if (!(Number.isInteger(imageCount) && imageCount >= 5 && imageCount <= 17
      && (imageCount - 1) % 4 === 0)) {
    throw new RangeError("model-force response path needs 5, 9, 13, or 17 images");
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
  const imageEvaluations = images.map((image) =>
    incrementalFinitePointChargeElectrostatics(currentSites, image.sites,
      electrostaticsOptions));
  const branchRecords = imageEvaluations.map((evaluation, imageIndex) => Object.freeze({
    imageIndex,
    fraction: images[imageIndex].fraction,
    available: Boolean(evaluation.available),
    pairCount: evaluation.pairCount ?? null,
    pairInteractionModel: evaluation.pairInteractionModel || null,
    reachAngstrom: evaluation.reachAngstrom ?? null,
    bornMayerPairPolicy: evaluation.bornMayerPairPolicy || null,
    bornMayerPairMatrixFallbackCount:
      evaluation.bornMayerPairMatrixFallbackCount ?? null,
    bornMayerPairParameterUsage: Object.freeze(
      (evaluation.bornMayerPairParameterUsage || []).map((record) =>
        Object.freeze({ key: record.key, pairCount: record.pairCount }))),
    inductionAppliedResponseModel: evaluation.inductionAppliedResponseModel || null,
    inductionDirectFallbackApplied: Boolean(evaluation.inductionDirectFallbackApplied),
    inductionForceModeApplied: evaluation.inductionForceModeApplied || null,
    completeForceGradient: Boolean(evaluation.pairInteractionForceIsNegativeEnergyGradient),
  }));
  const branchSignatures = branchRecords.map((record) => JSON.stringify({
    available: record.available,
    pairCount: record.pairCount,
    pairInteractionModel: record.pairInteractionModel,
    reachAngstrom: record.reachAngstrom,
    bornMayerPairPolicy: record.bornMayerPairPolicy,
    bornMayerPairMatrixFallbackCount: record.bornMayerPairMatrixFallbackCount,
    bornMayerPairParameterUsage: record.bornMayerPairParameterUsage,
    inductionAppliedResponseModel: record.inductionAppliedResponseModel,
    inductionDirectFallbackApplied: record.inductionDirectFallbackApplied,
    inductionForceModeApplied: record.inductionForceModeApplied,
    completeForceGradient: record.completeForceGradient,
  }));
  const uniqueBranchSignatures = [...new Set(branchSignatures)];
  const reachTopology = auditFiniteReachPathTopology(currentSites,
    originalAddedSites, proposedAddedSites,
    imageEvaluations[0]?.reachAngstrom ?? electrostaticsOptions.reachAngstrom ?? "global");
  const evaluatedPairCountMatchesTopology = !reachTopology.finiteReach
    || imageEvaluations.every((evaluation) =>
      evaluation.pairCount === reachTopology.activePairs);
  const smoothModelBranchAvailable = branchRecords.every((record) => record.available
    && record.completeForceGradient) && reachTopology.available;
  const smoothModelBranch = Object.freeze({
    available: smoothModelBranchAvailable,
    passed: smoothModelBranchAvailable && uniqueBranchSignatures.length === 1
      && reachTopology.passed
      && evaluatedPairCountMatchesTopology,
    imageCount: branchRecords.length,
    uniqueStateCount: uniqueBranchSignatures.length,
    stateStableAcrossImages: uniqueBranchSignatures.length === 1,
    evaluatedPairCountMatchesTopology,
    records: Object.freeze(branchRecords),
    reachTopology,
    targetUsed: false,
    reason: !smoothModelBranchAvailable
      ? "complete finite interaction branch unavailable at one or more path images"
      : uniqueBranchSignatures.length !== 1
        ? "finite interaction or response state changed between path images"
        : !reachTopology.passed ? reachTopology.reason
          : !evaluatedPairCountMatchesTopology
            ? "evaluated pair count disagrees with analytic reach topology"
            : "one finite interaction/response state and pair topology spans the full path",
    claimBoundary: "This certifies one sampled interaction/response state plus analytic hard-reach membership continuity over the straight coordinate path. It does not prove higher differentiability, a switching function, transferable smoothness, dynamics, or time.",
  });
  const segments = [];
  for (let index = 0; index < images.length - 1; index++) {
    const audit = auditModelForceRelaxationOutcome(currentSites,
      images[index].sites, images[index + 1].sites, {
        ...auditOptions,
        electrostaticsOptions,
        forceGroupLabels,
        baselineEvaluation: imageEvaluations[index],
        proposedEvaluation: imageEvaluations[index + 1],
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
      symmetricForceMomentRedistributionPassed:
        audit.symmetricForceMomentRedistributionPassed,
      responseConsistent: audit.responseConsistent,
      completeForceGradient: audit.completeForceGradient,
      forceGroupResiduals: audit.forceGroupResiduals,
    }));
  }
  const everySegmentEnergyForceDescent = segments.every((segment) => segment.accepted);
  const firstFailure = segments.find((segment) => !segment.accepted) || null;
  const displacementVectorsAngstrom = originalAddedSites.map((site, index) =>
    proposedAddedSites[index].position.map((value, axis) => value - site.position[axis]));
  let workEnergyClosure;
  try {
    workEnergyClosure = auditForceEnergyPathClosure(
      images.map((image) => image.fraction),
      imageEvaluations.map((evaluation) => evaluation.deltaEnergyElectronVolt),
      imageEvaluations.map((evaluation) =>
        evaluation.addedForceVectorsElectronVoltPerAngstrom),
      displacementVectorsAngstrom, {
        absoluteToleranceElectronVolt: auditOptions.absoluteToleranceElectronVolt,
        relativeTolerance: auditOptions.relativeTolerance,
      });
  } catch (error) {
    workEnergyClosure = Object.freeze({ available: false, passed: false,
      reason: error?.message || "force-energy path closure unavailable",
      targetUsed: false });
  }
  const accepted = everySegmentEnergyForceDescent && smoothModelBranch.passed
    && workEnergyClosure.passed;
  return Object.freeze({
    available: segments.every((segment) => segment.completeForceGradient
      && segment.responseConsistent) && smoothModelBranch.available
      && workEnergyClosure.available,
    accepted,
    reason: !everySegmentEnergyForceDescent
      ? `response-path segment ${firstFailure?.segmentIndex ?? "?"} failed: ${firstFailure?.reason || "unavailable"}`
      : !smoothModelBranch.passed ? smoothModelBranch.reason
        : !workEnergyClosure.passed ? workEnergyClosure.reason
        : "every bounded response-path segment passed energy, force, population, resultant, torque, symmetric-moment, and work-energy closure gates",
    imageCount,
    segmentCount: segments.length,
    fractions: Object.freeze(images.map((image) => image.fraction)),
    segments: Object.freeze(segments),
    everySegmentEnergyForceDescent,
    smoothModelBranchPassed: smoothModelBranch.passed,
    smoothModelBranch,
    modelStateStableAcrossImages: smoothModelBranch.stateStableAcrossImages,
    analyticReachTopologyPassed: reachTopology.passed,
    analyticReachPairChecks: reachTopology.pairChecks,
    analyticReachMinimumClearanceAngstrom:
      reachTopology.minimumCutoffClearanceAngstrom,
    workEnergyClosurePassed: workEnergyClosure.passed,
    workEnergyClosure,
    forceWorkSimpsonElectronVolt: workEnergyClosure.simpsonWorkElectronVolt ?? null,
    forceWorkCoarseSimpsonElectronVolt:
      workEnergyClosure.coarseSimpsonWorkElectronVolt ?? null,
    forceWorkTrapezoidElectronVolt: workEnergyClosure.trapezoidWorkElectronVolt ?? null,
    endpointEnergyChangeElectronVolt: workEnergyClosure.energyChangeElectronVolt ?? null,
    workEnergyClosureResidualElectronVolt:
      workEnergyClosure.closureResidualElectronVolt ?? null,
    workEnergyClosureToleranceElectronVolt:
      workEnergyClosure.allowedClosureResidualElectronVolt ?? null,
    workEnergyQuadratureDiscrepancyElectronVolt:
      workEnergyClosure.quadratureDiscrepancyElectronVolt ?? null,
    workEnergyRichardsonErrorEstimateElectronVolt:
      workEnergyClosure.richardsonErrorEstimateElectronVolt ?? null,
    workEnergyNestedSimpsonConvergenceAvailable:
      workEnergyClosure.nestedSimpsonConvergenceAvailable || false,
    groupLabelsFrozenBeforePath: true,
    straightLineCartesianImages: true,
    pathParameterIsPhysicalTime: false,
    targetUsed: false,
    claimBoundary: "The fixed Cartesian image sequence is a bounded continuity, monotonicity, and force-work/energy consistency check between two coordinate sets. The embedded fine/coarse Simpson difference divided by 15 is a smooth-integrand Richardson error estimate, not physical uncertainty. This is not thermodynamic work, a free-energy calculation, minimum-energy path, transition state, dynamics, rate, or elapsed physical time.",
  });
}
