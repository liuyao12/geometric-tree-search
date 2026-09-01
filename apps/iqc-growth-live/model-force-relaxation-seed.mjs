import { incrementalFinitePointChargeElectrostatics }
  from "./finite-point-charge-electrostatics.mjs?v=20260901-454";
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
    additionalNumericalToleranceElectronVolt = 0,
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
  const baseNumericalToleranceElectronVolt = Math.max(Number(absoluteToleranceElectronVolt),
    Number(relativeTolerance) * Math.max(1, Math.abs(energyChangeElectronVolt),
      Math.abs(simpsonWorkElectronVolt)));
  const additionalTolerance = Number(additionalNumericalToleranceElectronVolt);
  if (!(Number.isFinite(additionalTolerance) && additionalTolerance >= 0)) {
    throw new RangeError("force-energy path closure additional tolerance must be finite and nonnegative");
  }
  const numericalToleranceElectronVolt = baseNumericalToleranceElectronVolt
    + additionalTolerance;
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
    energyProfileElectronVolt: Object.freeze([...energiesElectronVolt]),
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
    baseNumericalToleranceElectronVolt,
    additionalNumericalToleranceElectronVolt: additionalTolerance,
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

/**
 * Prevent equal-and-opposite work/energy errors in distant path regions from
 * cancelling in the aggregate. Every four fine intervals form an independent
 * five-image Simpson panel with its own embedded three-image Simpson rule.
 */
export function auditPanelResolvedForceEnergyPathClosure(fractions,
  energiesElectronVolt, forceFieldsElectronVoltPerAngstrom,
  displacementVectorsAngstrom, options = {}) {
  // Reuse the aggregate audit's strict input validation before slicing panels.
  auditForceEnergyPathClosure(fractions, energiesElectronVolt,
    forceFieldsElectronVoltPerAngstrom, displacementVectorsAngstrom, options);
  const panelIntervalCount = 4;
  const panelFractionSpan = panelIntervalCount / (fractions.length - 1);
  const localFractions = Object.freeze([0, .25, .5, .75, 1]);
  const additionalTolerance = Number(
    options.additionalNumericalToleranceElectronVolt ?? 0);
  const panelDisplacements = displacementVectorsAngstrom.map((vector) =>
    vector.map((value) => value * panelFractionSpan));
  const panels = [];
  for (let start = 0; start < fractions.length - 1;
    start += panelIntervalCount) {
    const closure = auditForceEnergyPathClosure(localFractions,
      energiesElectronVolt.slice(start, start + panelIntervalCount + 1),
      forceFieldsElectronVoltPerAngstrom.slice(start,
        start + panelIntervalCount + 1), panelDisplacements, {
        ...options,
        additionalNumericalToleranceElectronVolt:
          additionalTolerance * panelFractionSpan,
      });
    panels.push(Object.freeze({
      panelIndex: panels.length,
      startImageIndex: start,
      endImageIndex: start + panelIntervalCount,
      startFraction: fractions[start],
      endFraction: fractions[start + panelIntervalCount],
      ...closure,
    }));
  }
  const failedPanelIndices = panels.filter((panel) => !panel.passed)
    .map((panel) => panel.panelIndex);
  const passed = failedPanelIndices.length === 0;
  return Object.freeze({
    available: panels.every((panel) => panel.available),
    passed,
    panelCount: panels.length,
    fineImagesPerPanel: 5,
    coarseImagesPerPanel: 3,
    panelFractionSpan,
    failedPanelIndices: Object.freeze(failedPanelIndices),
    maximumAbsoluteClosureResidualElectronVolt: Math.max(0,
      ...panels.map((panel) => panel.absoluteClosureResidualElectronVolt)),
    panels: Object.freeze(panels),
    targetUsed: false,
    reason: passed
      ? "every local path panel closes independently"
      : `local work-energy closure failed in panel${failedPanelIndices.length === 1 ? "" : "s"} ${failedPanelIndices.join(", ")}`,
    claimBoundary: "Panel-resolved nested-Simpson closure prevents path-local force/energy errors from cancelling in the aggregate. It validates one sampled straight coordinate path, not a Hessian, phonon spectrum, minimum-energy path, thermodynamic work, dynamics, rate, or physical time.",
  });
}

/**
 * Compare the complete projected force at each eligible interior image with an
 * independently differenced local energy derivative. The five-point stencil
 * is the reported estimate; its difference from the centered three-point
 * stencil is retained as a conservative discretization allowance.
 */
export function auditInteriorForceEnergyGradientConsistency(fractions,
  energiesElectronVolt, forceFieldsElectronVoltPerAngstrom,
  displacementVectorsAngstrom, {
    absoluteToleranceElectronVolt = 1e-10,
    relativeTolerance = 1e-10,
    additionalProjectedForceToleranceElectronVolt = 0,
  } = {}) {
  auditForceEnergyPathClosure(fractions, energiesElectronVolt,
    forceFieldsElectronVoltPerAngstrom, displacementVectorsAngstrom, {
      absoluteToleranceElectronVolt,
      relativeTolerance,
    });
  const additionalTolerance = Number(
    additionalProjectedForceToleranceElectronVolt);
  if (!(Number.isFinite(additionalTolerance) && additionalTolerance >= 0)) {
    throw new RangeError("interior force-gradient tolerance must be finite and nonnegative");
  }
  const interval = 1 / (fractions.length - 1);
  const projectedForceElectronVolt = forceFieldsElectronVoltPerAngstrom.map((field) =>
    field.reduce((sum, force, siteIndex) =>
      sum + dotVector(force, displacementVectorsAngstrom[siteIndex]), 0));
  const records = [];
  for (let imageIndex = 2; imageIndex <= fractions.length - 3; imageIndex += 1) {
    const fineEnergyDerivativeElectronVolt = (
      energiesElectronVolt[imageIndex - 2]
      - 8 * energiesElectronVolt[imageIndex - 1]
      + 8 * energiesElectronVolt[imageIndex + 1]
      - energiesElectronVolt[imageIndex + 2]) / (12 * interval);
    const coarseEnergyDerivativeElectronVolt = (
      energiesElectronVolt[imageIndex + 1]
      - energiesElectronVolt[imageIndex - 1]) / (2 * interval);
    const negativeEnergyDerivativeElectronVolt =
      -fineEnergyDerivativeElectronVolt;
    const force = projectedForceElectronVolt[imageIndex];
    const residualElectronVolt = force - negativeEnergyDerivativeElectronVolt;
    const stencilDifferenceElectronVolt = Math.abs(
      fineEnergyDerivativeElectronVolt - coarseEnergyDerivativeElectronVolt);
    const baseToleranceElectronVolt = Math.max(
      Number(absoluteToleranceElectronVolt), Number(relativeTolerance)
      * Math.max(1, Math.abs(force), Math.abs(negativeEnergyDerivativeElectronVolt)));
    const allowedResidualElectronVolt = baseToleranceElectronVolt
      + stencilDifferenceElectronVolt + additionalTolerance;
    const passed = Math.abs(residualElectronVolt) <= allowedResidualElectronVolt;
    records.push(Object.freeze({
      imageIndex,
      fraction: fractions[imageIndex],
      projectedForceElectronVolt: force,
      negativeFineEnergyDerivativeElectronVolt:
        negativeEnergyDerivativeElectronVolt,
      negativeCoarseEnergyDerivativeElectronVolt:
        -coarseEnergyDerivativeElectronVolt,
      residualElectronVolt,
      absoluteResidualElectronVolt: Math.abs(residualElectronVolt),
      stencilDifferenceElectronVolt,
      baseToleranceElectronVolt,
      additionalProjectedForceToleranceElectronVolt: additionalTolerance,
      allowedResidualElectronVolt,
      passed,
    }));
  }
  const failedImageIndices = records.filter((record) => !record.passed)
    .map((record) => record.imageIndex);
  const passed = failedImageIndices.length === 0;
  return Object.freeze({
    available: records.length > 0,
    passed,
    eligibleImageCount: records.length,
    fivePointEnergyDerivative: true,
    threePointEmbeddedComparison: true,
    failedImageIndices: Object.freeze(failedImageIndices),
    maximumAbsoluteResidualElectronVolt: Math.max(0,
      ...records.map((record) => record.absoluteResidualElectronVolt)),
    records: Object.freeze(records),
    targetUsed: false,
    reason: passed
      ? "projected force agrees with the local energy derivative at every eligible image"
      : `local force-energy gradient mismatch at image${failedImageIndices.length === 1 ? "" : "s"} ${failedImageIndices.join(", ")}`,
    claimBoundary: "This compares a projected force with independent five-point and three-point energy derivatives along one sampled straight coordinate path. The stencil difference is numerical allowance, not physical uncertainty. It is a local tangent consistency check—not a full Cartesian gradient, Hessian, force-constant matrix, phonon spectrum, stability proof, minimum-energy path, dynamics, rate, or time.",
  });
}

/** Require every active physical term to close independently of the total. */
export function auditComponentForceEnergyPathClosures(components, fractions,
  displacementVectorsAngstrom, options = {}) {
  if (!Array.isArray(components) || !components.length) {
    throw new Error("component work-energy audit needs at least one declared component");
  }
  const ids = components.map((component) => String(component?.id || ""));
  if (ids.some((id) => !id) || new Set(ids).size !== ids.length) {
    throw new Error("component work-energy audit needs unique nonempty component ids");
  }
  const records = components.map((component, index) => {
    const active = Boolean(component.active);
    if (!active) return Object.freeze({ id: ids[index], active: false,
      available: true, passed: true, reason: "component inactive in the declared model",
      targetUsed: false });
    const closure = auditForceEnergyPathClosure(fractions,
      component.energiesElectronVolt, component.forceFieldsElectronVoltPerAngstrom,
      displacementVectorsAngstrom, { ...options,
        additionalNumericalToleranceElectronVolt:
          component.additionalNumericalToleranceElectronVolt
          ?? options.additionalNumericalToleranceElectronVolt ?? 0 });
    const panelClosure = auditPanelResolvedForceEnergyPathClosure(fractions,
      component.energiesElectronVolt, component.forceFieldsElectronVoltPerAngstrom,
      displacementVectorsAngstrom, { ...options,
        additionalNumericalToleranceElectronVolt:
          component.additionalNumericalToleranceElectronVolt
          ?? options.additionalNumericalToleranceElectronVolt ?? 0 });
    const gradientConsistency = auditInteriorForceEnergyGradientConsistency(
      fractions, component.energiesElectronVolt,
      component.forceFieldsElectronVoltPerAngstrom,
      displacementVectorsAngstrom, { ...options,
        additionalProjectedForceToleranceElectronVolt:
          component.additionalNumericalToleranceElectronVolt
          ?? options.additionalNumericalToleranceElectronVolt ?? 0 });
    return Object.freeze({ id: ids[index], active: true, ...closure,
      passed: closure.passed && panelClosure.passed && gradientConsistency.passed,
      aggregateClosurePassed: closure.passed,
      panelClosurePassed: panelClosure.passed,
      panelClosure,
      interiorGradientConsistencyPassed: gradientConsistency.passed,
      interiorGradientConsistency: gradientConsistency });
  });
  const activeRecords = records.filter((record) => record.active);
  const passed = activeRecords.every((record) => record.passed);
  return Object.freeze({
    available: activeRecords.every((record) => record.available),
    passed,
    componentCount: records.length,
    activeComponentCount: activeRecords.length,
    failedComponentIds: Object.freeze(activeRecords.filter((record) => !record.passed)
      .map((record) => record.id)),
    records: Object.freeze(records),
    targetUsed: false,
    reason: passed ? "every active interaction component closes globally, panel by panel, and at every interior tangent"
      : `component work-energy closure failed: ${activeRecords.filter((record) => !record.passed)
        .map((record) => record.id).join(", ")}`,
    claimBoundary: "Independent component, local-panel, and interior-tangent closure prevents compensating force/energy errors from hiding between terms, path regions, or samples. It validates only the declared decomposition along one sampled coordinate path; it does not prove the components are transferable physical interactions, a full gradient, Hessian, thermodynamic work, dynamics, or time.",
  });
}

/** Independently verify every movable Cartesian force component at one state. */
export function auditCartesianForceEnergyGradient(currentSites, addedSites,
  reportedEvaluation, electrostaticsOptions = {}, {
    stepAngstrom = 1e-4,
    maximumMovableSites = 64,
    absoluteToleranceElectronVoltPerAngstrom = 1e-6,
    relativeTolerance = 1e-7,
  } = {}) {
  const step = Number(stepAngstrom);
  if (!(Number.isFinite(step) && step >= 1e-6 && step <= 1e-2)) {
    throw new RangeError("Cartesian gradient audit step must be between 1e-6 and 1e-2 angstrom");
  }
  if (!Array.isArray(addedSites) || !addedSites.length
      || !addedSites.every((site) => finiteVector(site?.position))) {
    throw new Error("Cartesian gradient audit needs movable finite Cartesian sites");
  }
  if (!(Number.isInteger(maximumMovableSites) && maximumMovableSites > 0)
      || addedSites.length > maximumMovableSites) {
    throw new RangeError(`Cartesian gradient audit supports at most ${maximumMovableSites} movable sites`);
  }
  const componentSpecs = [
    { id: "total", active: true, energy: "deltaEnergyElectronVolt",
      forces: "addedForceVectorsElectronVoltPerAngstrom",
      additionalTolerance: Number(reportedEvaluation
        ?.inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom) || 0 },
    { id: "coulomb", active: true, energy: "coulombDeltaEnergyElectronVolt",
      forces: "addedCoulombForceVectorsElectronVoltPerAngstrom", additionalTolerance: 0 },
    { id: "born-mayer", active: Boolean(reportedEvaluation?.bornMayerRepulsionApplied),
      energy: "bornMayerRepulsiveEnergyElectronVolt",
      forces: "addedBornMayerForceVectorsElectronVoltPerAngstrom", additionalTolerance: 0 },
    { id: "dispersion", active: Boolean(reportedEvaluation?.dispersionApplied),
      energy: "dampedDispersionEnergyElectronVolt",
      forces: "addedDispersionForceVectorsElectronVoltPerAngstrom", additionalTolerance: 0 },
    { id: "induction", active: Boolean(reportedEvaluation?.chargeInductionApplied),
      energy: "chargeInductionDeltaEnergyElectronVolt",
      forces: "addedInductionForceVectorsElectronVoltPerAngstrom",
      additionalTolerance: Number(reportedEvaluation
        ?.inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom) || 0 },
  ];
  componentSpecs.filter((spec) => spec.active).forEach((spec) => {
    if (!Number.isFinite(reportedEvaluation?.[spec.energy])
        || !Array.isArray(reportedEvaluation?.[spec.forces])
        || reportedEvaluation[spec.forces].length !== addedSites.length
        || !reportedEvaluation[spec.forces].every(finiteVector)) {
      throw new Error(`Cartesian gradient audit lacks complete ${spec.id} energy/force data`);
    }
  });
  const componentCoordinateRecords = new Map(componentSpecs.map((spec) =>
    [spec.id, []]));
  let branchStable = true;
  let probeEvaluationCount = 0;
  let distanceEvaluationCount = 0;
  const probeOptions = { ...electrostaticsOptions, inductionForceMode: "omitted" };
  const evaluateOffset = (siteIndex, axis, offset) => {
    const sites = addedSites.map((site, index) => ({ ...site,
      position: site.position.map((value, coordinateAxis) => value
        + (index === siteIndex && coordinateAxis === axis ? offset : 0)) }));
    const evaluation = incrementalFinitePointChargeElectrostatics(currentSites,
      sites, probeOptions);
    probeEvaluationCount += 1;
    distanceEvaluationCount += evaluation.distanceEvaluations || 0;
    const sameBranch = Boolean(evaluation.available)
      && evaluation.pairCount === reportedEvaluation.pairCount
      && evaluation.pairInteractionModel === reportedEvaluation.pairInteractionModel
      && evaluation.inductionAppliedResponseModel
        === reportedEvaluation.inductionAppliedResponseModel
      && evaluation.inductionDirectFallbackApplied
        === reportedEvaluation.inductionDirectFallbackApplied;
    branchStable = branchStable && sameBranch;
    return { evaluation, sameBranch };
  };
  addedSites.forEach((_, siteIndex) => [0, 1, 2].forEach((axis) => {
    const plusCoarse = evaluateOffset(siteIndex, axis, step);
    const minusCoarse = evaluateOffset(siteIndex, axis, -step);
    const plusFine = evaluateOffset(siteIndex, axis, step / 2);
    const minusFine = evaluateOffset(siteIndex, axis, -step / 2);
    const coordinateBranchStable = [plusCoarse, minusCoarse, plusFine, minusFine]
      .every((probe) => probe.sameBranch);
    componentSpecs.forEach((spec) => {
      if (!spec.active) return;
      const coarseDerivative = (plusCoarse.evaluation[spec.energy]
        - minusCoarse.evaluation[spec.energy]) / (2 * step);
      const fineDerivative = (plusFine.evaluation[spec.energy]
        - minusFine.evaluation[spec.energy]) / step;
      const numericalForce = -fineDerivative;
      const reportedForce = reportedEvaluation[spec.forces][siteIndex][axis];
      const residual = reportedForce - numericalForce;
      const richardsonError = Math.abs(fineDerivative - coarseDerivative) / 3;
      const baseTolerance = Math.max(Number(absoluteToleranceElectronVoltPerAngstrom),
        Number(relativeTolerance) * Math.max(1, Math.abs(reportedForce),
          Math.abs(numericalForce)));
      const allowedResidual = baseTolerance + richardsonError
        + spec.additionalTolerance;
      const passed = coordinateBranchStable
        && Math.abs(residual) <= allowedResidual;
      componentCoordinateRecords.get(spec.id).push(Object.freeze({
        siteIndex, axis, axisLabel: "xyz"[axis],
        reportedForceElectronVoltPerAngstrom: reportedForce,
        numericalForceElectronVoltPerAngstrom: numericalForce,
        coarseNumericalForceElectronVoltPerAngstrom: -coarseDerivative,
        residualElectronVoltPerAngstrom: residual,
        absoluteResidualElectronVoltPerAngstrom: Math.abs(residual),
        richardsonErrorEstimateElectronVoltPerAngstrom: richardsonError,
        baseToleranceElectronVoltPerAngstrom: baseTolerance,
        additionalToleranceElectronVoltPerAngstrom: spec.additionalTolerance,
        allowedResidualElectronVoltPerAngstrom: allowedResidual,
        branchStable: coordinateBranchStable,
        passed,
      }));
    });
  }));
  const components = componentSpecs.map((spec) => {
    if (!spec.active) return Object.freeze({ id: spec.id, active: false,
      available: true, passed: true, coordinateCount: 0,
      records: Object.freeze([]), targetUsed: false });
    const records = componentCoordinateRecords.get(spec.id);
    const failedCoordinates = records.filter((record) => !record.passed)
      .map((record) => `${record.siteIndex}:${record.axisLabel}`);
    return Object.freeze({
      id: spec.id, active: true, available: records.length === 3 * addedSites.length,
      passed: failedCoordinates.length === 0,
      coordinateCount: records.length,
      failedCoordinates: Object.freeze(failedCoordinates),
      maximumAbsoluteResidualElectronVoltPerAngstrom: Math.max(0,
        ...records.map((record) => record.absoluteResidualElectronVoltPerAngstrom)),
      records: Object.freeze(records), targetUsed: false,
    });
  });
  const activeComponents = components.filter((component) => component.active);
  const failedComponentIds = activeComponents.filter((component) => !component.passed)
    .map((component) => component.id);
  const passed = branchStable && failedComponentIds.length === 0;
  return Object.freeze({
    available: activeComponents.every((component) => component.available),
    passed,
    movableSiteCount: addedSites.length,
    coordinateCount: 3 * addedSites.length,
    activeComponentCount: activeComponents.length,
    failedComponentIds: Object.freeze(failedComponentIds),
    components: Object.freeze(components),
    stepAngstrom: step,
    fineStepAngstrom: step / 2,
    centralDifferenceOrder: 2,
    richardsonDivisor: 3,
    energyProbeForceMode: "omitted",
    branchStable,
    probeEvaluationCount,
    distanceEvaluationCount,
    targetUsed: false,
    reason: passed
      ? "every movable Cartesian force component agrees with independent energy probes"
      : !branchStable ? "one or more Cartesian energy probes changed interaction branch"
        : `Cartesian force-energy gradient mismatch: ${failedComponentIds.join(", ")}`,
    claimBoundary: "This independently finite-differences the declared energy along every movable Cartesian coordinate at one endpoint. Fine and coarse central differences bound numerical error, and polarization-force evaluation is disabled inside the energy probes. It verifies the reported finite force vector at this state—not fixed-site forces, a Hessian, phonons, stability, a minimum-energy path, dynamics, rate, or time.",
  });
}

/**
 * Resolve the incremental central-pair force on a bounded, force-ranked sample
 * of fixed sites and verify it by independent Cartesian energy differences.
 * The complete sparse analytic pair field still supplies the global linear and
 * angular action-reaction checks. Fixed-fixed forces are constant in this
 * incremental energy and induction remains aggregate-only.
 */
export function auditFixedEnvironmentPairForceGradient(currentSites, addedSites,
  reportedEvaluation, electrostaticsOptions = {}, {
    stepAngstrom = 1e-4,
    maximumSampledFixedSites = 8,
    absoluteToleranceElectronVoltPerAngstrom = 1e-6,
    relativeTolerance = 1e-7,
  } = {}) {
  const step = Number(stepAngstrom);
  if (!(Number.isFinite(step) && step >= 1e-6 && step <= 1e-2)) {
    throw new RangeError("fixed-site gradient audit step must be between 1e-6 and 1e-2 angstrom");
  }
  if (!(Number.isInteger(maximumSampledFixedSites) && maximumSampledFixedSites > 0
      && maximumSampledFixedSites <= 64)) {
    throw new RangeError("fixed-site gradient audit supports 1..64 sampled fixed sites");
  }
  if (!Array.isArray(currentSites) || !currentSites.length
      || !currentSites.every((site) => finiteVector(site?.position))
      || !Array.isArray(addedSites) || !addedSites.length
      || !addedSites.every((site) => finiteVector(site?.position))) {
    throw new Error("fixed-site gradient audit needs finite current and movable sites");
  }
  const fixedRecords = reportedEvaluation?.currentIncrementalPairForceRecords;
  if (!Array.isArray(fixedRecords)
      || fixedRecords.some((record) => !Number.isInteger(record.currentIndex)
        || record.currentIndex < 0 || record.currentIndex >= currentSites.length)) {
    throw new Error("fixed-site gradient audit lacks a sparse incremental pair-force field");
  }
  const componentSpecs = [
    { id: "pair-total", active: true, energy: "pairDeltaEnergyElectronVolt",
      fixedForce: "pairForceVectorElectronVoltPerAngstrom",
      movableForces: "addedPairForceVectorsElectronVoltPerAngstrom" },
    { id: "coulomb", active: true, energy: "coulombDeltaEnergyElectronVolt",
      fixedForce: "coulombForceVectorElectronVoltPerAngstrom",
      movableForces: "addedCoulombForceVectorsElectronVoltPerAngstrom" },
    { id: "born-mayer", active: Boolean(reportedEvaluation?.bornMayerRepulsionApplied),
      energy: "bornMayerRepulsiveEnergyElectronVolt",
      fixedForce: "bornMayerForceVectorElectronVoltPerAngstrom",
      movableForces: "addedBornMayerForceVectorsElectronVoltPerAngstrom" },
    { id: "dispersion", active: Boolean(reportedEvaluation?.dispersionApplied),
      energy: "dampedDispersionEnergyElectronVolt",
      fixedForce: "dispersionForceVectorElectronVoltPerAngstrom",
      movableForces: "addedDispersionForceVectorsElectronVoltPerAngstrom" },
  ];
  const activeSpecs = componentSpecs.filter((spec) => spec.active);
  activeSpecs.forEach((spec) => {
    if (!Number.isFinite(reportedEvaluation?.[spec.energy])
        || !Array.isArray(reportedEvaluation?.[spec.movableForces])
        || reportedEvaluation[spec.movableForces].length !== addedSites.length
        || !reportedEvaluation[spec.movableForces].every(finiteVector)
        || fixedRecords.some((record) => !finiteVector(record[spec.fixedForce]))) {
      throw new Error(`fixed-site gradient audit lacks complete ${spec.id} pair data`);
    }
  });
  if (!fixedRecords.length) {
    const components = componentSpecs.map((spec) => Object.freeze({ id: spec.id,
      active: spec.active, available: true, passed: true, sampledSiteCount: 0,
      coordinateCount: 0, failedCoordinates: Object.freeze([]),
      maximumAbsoluteResidualElectronVoltPerAngstrom: 0,
      netForceResidualVectorElectronVoltPerAngstrom: Object.freeze([0, 0, 0]),
      netForceResidualMagnitudeElectronVoltPerAngstrom: 0,
      forceConservationToleranceElectronVoltPerAngstrom: 1e-10,
      torqueResidualVectorElectronVolt: Object.freeze([0, 0, 0]),
      torqueResidualMagnitudeElectronVolt: 0,
      torqueConservationToleranceElectronVolt: 1e-10,
      conservationPassed: true, records: Object.freeze([]), targetUsed: false }));
    return Object.freeze({ available: true, passed: true,
      affectedFixedSiteCount: 0, sampledFixedSiteCount: 0,
      sampledCurrentIndices: Object.freeze([]), coordinateCount: 0,
      componentCount: components.length,
      activeComponentCount: components.filter((component) => component.active).length,
      failedComponentIds: Object.freeze([]), components: Object.freeze(components),
      stepAngstrom: step, fineStepAngstrom: step / 2,
      centralDifferenceOrder: 2, richardsonDivisor: 3, branchStable: true,
      probeEvaluationCount: 0, distanceEvaluationCount: 0,
      energyProbeForceMode: "omitted", inductionExcludedFromPairEnergyProbes: true,
      sampleSelectionPolicy: "no fixed site was touched by an active incremental pair",
      fullSparsePairFieldConservationChecked: true,
      currentCurrentForceFieldOmittedAsConstant: true,
      perFixedSitePairForcesResolved: true,
      perFixedSiteInductionForcesResolved: false,
      fixedEnvironmentRelaxed: false, targetUsed: false,
      reason: "no fixed site carries an incremental central-pair reaction at this endpoint",
      claimBoundary: "No active movable-fixed central pair exists at this endpoint; the empty fixed-side incremental reaction field is exact. Fixed-fixed forces remain constant and per-fixed-site induction remains unresolved." });
  }
  const rankedByComponent = activeSpecs.map((spec) => [...fixedRecords]
    .sort((first, second) => vectorMagnitude(second[spec.fixedForce])
      - vectorMagnitude(first[spec.fixedForce]) || first.currentIndex - second.currentIndex));
  const sampledIndices = [];
  const sampledSet = new Set();
  for (let rank = 0; sampledIndices.length < maximumSampledFixedSites
      && rank < fixedRecords.length; rank += 1) {
    rankedByComponent.forEach((records) => {
      const index = records[rank]?.currentIndex;
      if (index !== undefined && !sampledSet.has(index)
          && sampledIndices.length < maximumSampledFixedSites) {
        sampledSet.add(index);
        sampledIndices.push(index);
      }
    });
  }
  const fixedRecordByIndex = new Map(fixedRecords.map((record) =>
    [record.currentIndex, record]));
  const probeOptions = { ...electrostaticsOptions,
    inductionPolarizabilityAngstrom3: 0, inductionForceMode: "omitted" };
  let probeEvaluationCount = 0;
  let distanceEvaluationCount = 0;
  let branchStable = true;
  const evaluateOffset = (currentIndex, axis, offset) => {
    const sites = currentSites.map((site, index) => ({ ...site,
      position: site.position.map((value, coordinateAxis) => value
        + (index === currentIndex && coordinateAxis === axis ? offset : 0)) }));
    const evaluation = incrementalFinitePointChargeElectrostatics(sites,
      addedSites, probeOptions);
    probeEvaluationCount += 1;
    distanceEvaluationCount += evaluation.distanceEvaluations || 0;
    const sameBranch = Boolean(evaluation.available)
      && evaluation.pairCount === reportedEvaluation.pairCount
      && evaluation.reachAngstrom === reportedEvaluation.reachAngstrom
      && evaluation.bornMayerPairPolicy === reportedEvaluation.bornMayerPairPolicy
      && evaluation.bornMayerPairMatrixFallbackCount
        === reportedEvaluation.bornMayerPairMatrixFallbackCount;
    branchStable = branchStable && sameBranch;
    return { evaluation, sameBranch };
  };
  const coordinateProbes = sampledIndices.flatMap((currentIndex) => [0, 1, 2]
    .map((axis) => Object.freeze({ currentIndex, axis,
      plusCoarse: evaluateOffset(currentIndex, axis, step),
      minusCoarse: evaluateOffset(currentIndex, axis, -step),
      plusFine: evaluateOffset(currentIndex, axis, step / 2),
      minusFine: evaluateOffset(currentIndex, axis, -step / 2) })));
  const systemCentroid = [0, 1, 2].map((axis) => [...currentSites, ...addedSites]
    .reduce((sum, site) => sum + site.position[axis], 0)
      / (currentSites.length + addedSites.length));
  const sumVectors = (vectors) => vectors.reduce(addVector, [0, 0, 0]);
  const torque = (sites, vectors) => sites.reduce((sum, site, index) =>
    addVector(sum, crossVector(subtractVector(site.position, systemCentroid),
      vectors[index])), [0, 0, 0]);
  const components = componentSpecs.map((spec) => {
    if (!spec.active) return Object.freeze({ id: spec.id, active: false,
      available: true, passed: true, sampledSiteCount: 0, coordinateCount: 0,
      records: Object.freeze([]), targetUsed: false });
    const records = coordinateProbes.map((probe) => {
      const coarseDerivative = (probe.plusCoarse.evaluation[spec.energy]
        - probe.minusCoarse.evaluation[spec.energy]) / (2 * step);
      const fineDerivative = (probe.plusFine.evaluation[spec.energy]
        - probe.minusFine.evaluation[spec.energy]) / step;
      const numericalForce = -fineDerivative;
      const analyticForce = fixedRecordByIndex.get(probe.currentIndex)
        [spec.fixedForce][probe.axis];
      const residual = analyticForce - numericalForce;
      const richardsonError = Math.abs(fineDerivative - coarseDerivative) / 3;
      const baseTolerance = Math.max(Number(absoluteToleranceElectronVoltPerAngstrom),
        Number(relativeTolerance) * Math.max(1, Math.abs(analyticForce),
          Math.abs(numericalForce)));
      const allowedResidual = baseTolerance + richardsonError;
      const coordinateBranchStable = [probe.plusCoarse, probe.minusCoarse,
        probe.plusFine, probe.minusFine].every((item) => item.sameBranch);
      return Object.freeze({ currentIndex: probe.currentIndex, axis: probe.axis,
        axisLabel: "xyz"[probe.axis],
        analyticForceElectronVoltPerAngstrom: analyticForce,
        numericalForceElectronVoltPerAngstrom: numericalForce,
        coarseNumericalForceElectronVoltPerAngstrom: -coarseDerivative,
        residualElectronVoltPerAngstrom: residual,
        absoluteResidualElectronVoltPerAngstrom: Math.abs(residual),
        richardsonErrorEstimateElectronVoltPerAngstrom: richardsonError,
        baseToleranceElectronVoltPerAngstrom: baseTolerance,
        allowedResidualElectronVoltPerAngstrom: allowedResidual,
        branchStable: coordinateBranchStable,
        passed: coordinateBranchStable && Math.abs(residual) <= allowedResidual });
    });
    const fixedVectors = fixedRecords.map((record) => record[spec.fixedForce]);
    const fixedSites = fixedRecords.map((record) => currentSites[record.currentIndex]);
    const movableVectors = reportedEvaluation[spec.movableForces];
    const netForceResidual = addVector(sumVectors(fixedVectors),
      sumVectors(movableVectors));
    const torqueResidual = addVector(torque(fixedSites, fixedVectors),
      torque(addedSites, movableVectors));
    const conservationScale = Math.max(1,
      ...fixedVectors.map(vectorMagnitude), ...movableVectors.map(vectorMagnitude));
    const forceConservationTolerance = Math.max(1e-10,
      Number(relativeTolerance) * conservationScale);
    const leverScale = Math.max(1, ...[...fixedSites, ...addedSites].map((site) =>
      vectorMagnitude(subtractVector(site.position, systemCentroid))));
    const torqueConservationTolerance = forceConservationTolerance * leverScale
      * Math.max(1, fixedVectors.length + movableVectors.length);
    const conservationPassed = vectorMagnitude(netForceResidual)
      <= forceConservationTolerance
      && vectorMagnitude(torqueResidual) <= torqueConservationTolerance;
    const failedCoordinates = records.filter((record) => !record.passed)
      .map((record) => `${record.currentIndex}:${record.axisLabel}`);
    return Object.freeze({ id: spec.id, active: true, available: true,
      passed: failedCoordinates.length === 0 && conservationPassed,
      sampledSiteCount: sampledIndices.length, coordinateCount: records.length,
      failedCoordinates: Object.freeze(failedCoordinates),
      maximumAbsoluteResidualElectronVoltPerAngstrom: Math.max(0,
        ...records.map((record) => record.absoluteResidualElectronVoltPerAngstrom)),
      netForceResidualVectorElectronVoltPerAngstrom: Object.freeze(netForceResidual),
      netForceResidualMagnitudeElectronVoltPerAngstrom: vectorMagnitude(netForceResidual),
      forceConservationToleranceElectronVoltPerAngstrom: forceConservationTolerance,
      torqueResidualVectorElectronVolt: Object.freeze(torqueResidual),
      torqueResidualMagnitudeElectronVolt: vectorMagnitude(torqueResidual),
      torqueConservationToleranceElectronVolt: torqueConservationTolerance,
      conservationPassed, records: Object.freeze(records), targetUsed: false });
  });
  const activeComponents = components.filter((component) => component.active);
  const failedComponentIds = activeComponents.filter((component) => !component.passed)
    .map((component) => component.id);
  const passed = branchStable && failedComponentIds.length === 0;
  return Object.freeze({ available: activeComponents.every((component) => component.available),
    passed, affectedFixedSiteCount: fixedRecords.length,
    sampledFixedSiteCount: sampledIndices.length,
    sampledCurrentIndices: Object.freeze(sampledIndices),
    coordinateCount: 3 * sampledIndices.length,
    componentCount: components.length, activeComponentCount: activeComponents.length,
    failedComponentIds: Object.freeze(failedComponentIds),
    components: Object.freeze(components), stepAngstrom: step,
    fineStepAngstrom: step / 2, centralDifferenceOrder: 2,
    richardsonDivisor: 3, branchStable, probeEvaluationCount,
    distanceEvaluationCount, energyProbeForceMode: "omitted",
    inductionExcludedFromPairEnergyProbes: true,
    sampleSelectionPolicy: "round-robin largest force magnitude across active central-pair components",
    fullSparsePairFieldConservationChecked: true,
    currentCurrentForceFieldOmittedAsConstant: true,
    perFixedSitePairForcesResolved: true,
    perFixedSiteInductionForcesResolved: false,
    fixedEnvironmentRelaxed: false, targetUsed: false,
    reason: passed
      ? "sampled fixed-site central-pair forces match independent energy gradients and the complete sparse pair field conserves force and torque"
      : !branchStable ? "one or more fixed-site energy probes changed interaction branch"
        : `fixed-site pair-force audit failed: ${failedComponentIds.join(", ")}`,
    claimBoundary: "This resolves the incremental central-pair reaction field caused by the movable group, verifies a bounded force-ranked sample of fixed-site Cartesian gradients, and checks force/torque conservation over the complete sparse pair field. Fixed-fixed forces are constant and omitted; per-fixed-site induction forces remain unresolved and only their aggregate reaction is certified. This is not a complete material force field, stress, traction, equilibrium, dynamics, or time." });
}

/** Verify that the fixed environment carries the opposite net reaction force. */
export function auditEnvironmentReactionForceBalance(currentSites, addedSites,
  reportedEvaluation, electrostaticsOptions = {}, {
    stepAngstrom = 1e-4,
    absoluteToleranceElectronVoltPerAngstrom = 1e-6,
    relativeTolerance = 1e-7,
  } = {}) {
  const step = Number(stepAngstrom);
  if (!(Number.isFinite(step) && step >= 1e-6 && step <= 1e-2)) {
    throw new RangeError("environment reaction audit step must be between 1e-6 and 1e-2 angstrom");
  }
  if (!Array.isArray(currentSites) || !currentSites.length
      || !currentSites.every((site) => finiteVector(site?.position))
      || !Array.isArray(addedSites) || !addedSites.length
      || !addedSites.every((site) => finiteVector(site?.position))) {
    throw new Error("environment reaction audit needs finite current and movable sites");
  }
  const inductionTolerance = Number(reportedEvaluation
    ?.inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom) || 0;
  const componentSpecs = [
    { id: "total", active: true, energy: "deltaEnergyElectronVolt",
      forces: "addedForceVectorsElectronVoltPerAngstrom",
      additionalTolerance: inductionTolerance },
    { id: "coulomb", active: true, energy: "coulombDeltaEnergyElectronVolt",
      forces: "addedCoulombForceVectorsElectronVoltPerAngstrom", additionalTolerance: 0 },
    { id: "born-mayer", active: Boolean(reportedEvaluation?.bornMayerRepulsionApplied),
      energy: "bornMayerRepulsiveEnergyElectronVolt",
      forces: "addedBornMayerForceVectorsElectronVoltPerAngstrom", additionalTolerance: 0 },
    { id: "dispersion", active: Boolean(reportedEvaluation?.dispersionApplied),
      energy: "dampedDispersionEnergyElectronVolt",
      forces: "addedDispersionForceVectorsElectronVoltPerAngstrom", additionalTolerance: 0 },
    { id: "induction", active: Boolean(reportedEvaluation?.chargeInductionApplied),
      energy: "chargeInductionDeltaEnergyElectronVolt",
      forces: "addedInductionForceVectorsElectronVoltPerAngstrom",
      additionalTolerance: inductionTolerance },
  ];
  componentSpecs.filter((spec) => spec.active).forEach((spec) => {
    if (!Number.isFinite(reportedEvaluation?.[spec.energy])
        || !Array.isArray(reportedEvaluation?.[spec.forces])
        || reportedEvaluation[spec.forces].length !== addedSites.length
        || !reportedEvaluation[spec.forces].every(finiteVector)) {
      throw new Error(`environment reaction audit lacks complete ${spec.id} energy/force data`);
    }
  });
  const probeOptions = { ...electrostaticsOptions, inductionForceMode: "omitted" };
  let probeEvaluationCount = 0;
  let distanceEvaluationCount = 0;
  let branchStable = true;
  const evaluateShift = (axis, offset) => {
    const shiftedCurrent = currentSites.map((site) => ({ ...site,
      position: site.position.map((value, coordinateAxis) =>
        value + (coordinateAxis === axis ? offset : 0)) }));
    const evaluation = incrementalFinitePointChargeElectrostatics(shiftedCurrent,
      addedSites, probeOptions);
    probeEvaluationCount += 1;
    distanceEvaluationCount += evaluation.distanceEvaluations || 0;
    const sameBranch = Boolean(evaluation.available)
      && evaluation.pairCount === reportedEvaluation.pairCount
      && evaluation.pairInteractionModel === reportedEvaluation.pairInteractionModel
      && evaluation.inductionAppliedResponseModel
        === reportedEvaluation.inductionAppliedResponseModel
      && evaluation.inductionDirectFallbackApplied
        === reportedEvaluation.inductionDirectFallbackApplied;
    branchStable = branchStable && sameBranch;
    return { evaluation, sameBranch };
  };
  const probes = [0, 1, 2].map((axis) => Object.freeze({
    axis,
    plusCoarse: evaluateShift(axis, step),
    minusCoarse: evaluateShift(axis, -step),
    plusFine: evaluateShift(axis, step / 2),
    minusFine: evaluateShift(axis, -step / 2),
  }));
  const components = componentSpecs.map((spec) => {
    if (!spec.active) return Object.freeze({ id: spec.id, active: false,
      available: true, passed: true, coordinateCount: 0,
      records: Object.freeze([]), targetUsed: false });
    const records = probes.map((probe) => {
      const coarseDerivative = (probe.plusCoarse.evaluation[spec.energy]
        - probe.minusCoarse.evaluation[spec.energy]) / (2 * step);
      const fineDerivative = (probe.plusFine.evaluation[spec.energy]
        - probe.minusFine.evaluation[spec.energy]) / step;
      const environmentReaction = -fineDerivative;
      const movableNetForce = reportedEvaluation[spec.forces]
        .reduce((sum, vector) => sum + vector[probe.axis], 0);
      const residual = movableNetForce + environmentReaction;
      const richardsonError = Math.abs(fineDerivative - coarseDerivative) / 3;
      const baseTolerance = Math.max(Number(absoluteToleranceElectronVoltPerAngstrom),
        Number(relativeTolerance) * Math.max(1, Math.abs(movableNetForce),
          Math.abs(environmentReaction)));
      const allowedResidual = baseTolerance + richardsonError
        + spec.additionalTolerance;
      const coordinateBranchStable = [probe.plusCoarse, probe.minusCoarse,
        probe.plusFine, probe.minusFine].every((record) => record.sameBranch);
      return Object.freeze({ axis: probe.axis, axisLabel: "xyz"[probe.axis],
        movableNetForceElectronVoltPerAngstrom: movableNetForce,
        environmentReactionForceElectronVoltPerAngstrom: environmentReaction,
        coarseEnvironmentReactionForceElectronVoltPerAngstrom: -coarseDerivative,
        totalSystemForceResidualElectronVoltPerAngstrom: residual,
        absoluteResidualElectronVoltPerAngstrom: Math.abs(residual),
        richardsonErrorEstimateElectronVoltPerAngstrom: richardsonError,
        baseToleranceElectronVoltPerAngstrom: baseTolerance,
        additionalToleranceElectronVoltPerAngstrom: spec.additionalTolerance,
        allowedResidualElectronVoltPerAngstrom: allowedResidual,
        branchStable: coordinateBranchStable,
        passed: coordinateBranchStable && Math.abs(residual) <= allowedResidual });
    });
    return Object.freeze({ id: spec.id, active: true, available: true,
      passed: records.every((record) => record.passed), coordinateCount: 3,
      failedAxes: Object.freeze(records.filter((record) => !record.passed)
        .map((record) => record.axisLabel)),
      maximumAbsoluteResidualElectronVoltPerAngstrom: Math.max(0,
        ...records.map((record) => record.absoluteResidualElectronVoltPerAngstrom)),
      records: Object.freeze(records), targetUsed: false });
  });
  const activeComponents = components.filter((component) => component.active);
  const failedComponentIds = activeComponents.filter((component) => !component.passed)
    .map((component) => component.id);
  const passed = branchStable && failedComponentIds.length === 0;
  return Object.freeze({ available: activeComponents.every((component) => component.available),
    passed, componentCount: components.length,
    activeComponentCount: activeComponents.length,
    failedComponentIds: Object.freeze(failedComponentIds),
    components: Object.freeze(components), stepAngstrom: step,
    fineStepAngstrom: step / 2, centralDifferenceOrder: 2,
    richardsonDivisor: 3, energyProbeForceMode: "omitted",
    branchStable, probeEvaluationCount, distanceEvaluationCount,
    fixedEnvironmentMovedCollectivelyForProbe: true,
    fixedEnvironmentRelaxed: false, perFixedSiteForcesResolved: false,
    targetUsed: false,
    reason: passed
      ? "the independently differentiated fixed-environment reaction balances the movable net force"
      : !branchStable ? "one or more environment-translation probes changed interaction branch"
        : `environment reaction-force balance failed: ${failedComponentIds.join(", ")}`,
    claimBoundary: "This collectively translates the fixed environment to derive its net reaction from independent energy probes, then checks it against the reported movable-site net force for the total and every active component. It is a translational-invariance and momentum-balance certificate—not per-fixed-atom forces, fixed-solid relaxation, traction, stress, pressure, mechanical equilibrium, dynamics, or physical time." });
}

/** Verify that the fixed environment carries the opposite common-origin torque. */
export function auditEnvironmentReactionTorqueBalance(currentSites, addedSites,
  reportedEvaluation, electrostaticsOptions = {}, {
    stepRadians = 1e-5,
    absoluteToleranceElectronVolt = 1e-6,
    relativeTolerance = 1e-7,
  } = {}) {
  const step = Number(stepRadians);
  if (!(Number.isFinite(step) && step >= 1e-7 && step <= 1e-2)) {
    throw new RangeError("environment reaction torque step must be between 1e-7 and 1e-2 radians");
  }
  if (!Array.isArray(currentSites) || !currentSites.length
      || !currentSites.every((site) => finiteVector(site?.position))
      || !Array.isArray(addedSites) || !addedSites.length
      || !addedSites.every((site) => finiteVector(site?.position))) {
    throw new Error("environment reaction torque audit needs finite current and movable sites");
  }
  const allSites = [...currentSites, ...addedSites];
  const torqueOriginAngstrom = [0, 1, 2].map((axis) => allSites
    .reduce((sum, site) => sum + site.position[axis], 0) / allSites.length);
  const movableLeverArmSumAngstrom = addedSites.reduce((sum, site) =>
    sum + vectorMagnitude(subtractVector(site.position, torqueOriginAngstrom)), 0);
  const inductionForceTolerance = Number(reportedEvaluation
    ?.inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom) || 0;
  const inductionTorqueTolerance = inductionForceTolerance
    * movableLeverArmSumAngstrom;
  const componentSpecs = [
    { id: "total", active: true, energy: "deltaEnergyElectronVolt",
      forces: "addedForceVectorsElectronVoltPerAngstrom",
      additionalTolerance: inductionTorqueTolerance },
    { id: "coulomb", active: true, energy: "coulombDeltaEnergyElectronVolt",
      forces: "addedCoulombForceVectorsElectronVoltPerAngstrom", additionalTolerance: 0 },
    { id: "born-mayer", active: Boolean(reportedEvaluation?.bornMayerRepulsionApplied),
      energy: "bornMayerRepulsiveEnergyElectronVolt",
      forces: "addedBornMayerForceVectorsElectronVoltPerAngstrom", additionalTolerance: 0 },
    { id: "dispersion", active: Boolean(reportedEvaluation?.dispersionApplied),
      energy: "dampedDispersionEnergyElectronVolt",
      forces: "addedDispersionForceVectorsElectronVoltPerAngstrom", additionalTolerance: 0 },
    { id: "induction", active: Boolean(reportedEvaluation?.chargeInductionApplied),
      energy: "chargeInductionDeltaEnergyElectronVolt",
      forces: "addedInductionForceVectorsElectronVoltPerAngstrom",
      additionalTolerance: inductionTorqueTolerance },
  ];
  componentSpecs.filter((spec) => spec.active).forEach((spec) => {
    if (!Number.isFinite(reportedEvaluation?.[spec.energy])
        || !Array.isArray(reportedEvaluation?.[spec.forces])
        || reportedEvaluation[spec.forces].length !== addedSites.length
        || !reportedEvaluation[spec.forces].every(finiteVector)) {
      throw new Error(`environment reaction torque audit lacks complete ${spec.id} energy/force data`);
    }
  });
  const probeOptions = { ...electrostaticsOptions, inductionForceMode: "omitted" };
  let probeEvaluationCount = 0;
  let distanceEvaluationCount = 0;
  let branchStable = true;
  const rotateCurrent = (axis, angle) => {
    const unitAxis = [0, 1, 2].map((coordinate) => coordinate === axis ? 1 : 0);
    const cosine = Math.cos(angle);
    const sine = Math.sin(angle);
    return currentSites.map((site) => {
      const relative = subtractVector(site.position, torqueOriginAngstrom);
      const rotated = relative.map((component, coordinate) =>
        component * cosine
        + crossVector(unitAxis, relative)[coordinate] * sine
        + unitAxis[coordinate] * dotVector(unitAxis, relative) * (1 - cosine));
      return { ...site, position: addVector(torqueOriginAngstrom, rotated) };
    });
  };
  const evaluateRotation = (axis, angle) => {
    const evaluation = incrementalFinitePointChargeElectrostatics(
      rotateCurrent(axis, angle), addedSites, probeOptions);
    probeEvaluationCount += 1;
    distanceEvaluationCount += evaluation.distanceEvaluations || 0;
    const sameBranch = Boolean(evaluation.available)
      && evaluation.pairCount === reportedEvaluation.pairCount
      && evaluation.pairInteractionModel === reportedEvaluation.pairInteractionModel
      && evaluation.inductionAppliedResponseModel
        === reportedEvaluation.inductionAppliedResponseModel
      && evaluation.inductionDirectFallbackApplied
        === reportedEvaluation.inductionDirectFallbackApplied;
    branchStable = branchStable && sameBranch;
    return { evaluation, sameBranch };
  };
  const probes = [0, 1, 2].map((axis) => Object.freeze({ axis,
    plusCoarse: evaluateRotation(axis, step),
    minusCoarse: evaluateRotation(axis, -step),
    plusFine: evaluateRotation(axis, step / 2),
    minusFine: evaluateRotation(axis, -step / 2) }));
  const components = componentSpecs.map((spec) => {
    if (!spec.active) return Object.freeze({ id: spec.id, active: false,
      available: true, passed: true, coordinateCount: 0,
      records: Object.freeze([]), targetUsed: false });
    const movableTorque = addedSites.reduce((sum, site, siteIndex) => addVector(sum,
      crossVector(subtractVector(site.position, torqueOriginAngstrom),
        reportedEvaluation[spec.forces][siteIndex])), [0, 0, 0]);
    const records = probes.map((probe) => {
      const coarseDerivative = (probe.plusCoarse.evaluation[spec.energy]
        - probe.minusCoarse.evaluation[spec.energy]) / (2 * step);
      const fineDerivative = (probe.plusFine.evaluation[spec.energy]
        - probe.minusFine.evaluation[spec.energy]) / step;
      const environmentReactionTorque = -fineDerivative;
      const residual = movableTorque[probe.axis] + environmentReactionTorque;
      const richardsonError = Math.abs(fineDerivative - coarseDerivative) / 3;
      const baseTolerance = Math.max(Number(absoluteToleranceElectronVolt),
        Number(relativeTolerance) * Math.max(1, Math.abs(movableTorque[probe.axis]),
          Math.abs(environmentReactionTorque)));
      const allowedResidual = baseTolerance + richardsonError
        + spec.additionalTolerance;
      const coordinateBranchStable = [probe.plusCoarse, probe.minusCoarse,
        probe.plusFine, probe.minusFine].every((record) => record.sameBranch);
      return Object.freeze({ axis: probe.axis, axisLabel: "xyz"[probe.axis],
        movableTorqueElectronVolt: movableTorque[probe.axis],
        environmentReactionTorqueElectronVolt: environmentReactionTorque,
        coarseEnvironmentReactionTorqueElectronVolt: -coarseDerivative,
        totalSystemTorqueResidualElectronVolt: residual,
        absoluteResidualElectronVolt: Math.abs(residual),
        richardsonErrorEstimateElectronVolt: richardsonError,
        baseToleranceElectronVolt: baseTolerance,
        additionalToleranceElectronVolt: spec.additionalTolerance,
        allowedResidualElectronVolt: allowedResidual,
        branchStable: coordinateBranchStable,
        passed: coordinateBranchStable && Math.abs(residual) <= allowedResidual });
    });
    return Object.freeze({ id: spec.id, active: true, available: true,
      passed: records.every((record) => record.passed), coordinateCount: 3,
      movableTorqueVectorElectronVolt: Object.freeze(movableTorque),
      failedAxes: Object.freeze(records.filter((record) => !record.passed)
        .map((record) => record.axisLabel)),
      maximumAbsoluteResidualElectronVolt: Math.max(0,
        ...records.map((record) => record.absoluteResidualElectronVolt)),
      records: Object.freeze(records), targetUsed: false });
  });
  const activeComponents = components.filter((component) => component.active);
  const failedComponentIds = activeComponents.filter((component) => !component.passed)
    .map((component) => component.id);
  const passed = branchStable && failedComponentIds.length === 0;
  return Object.freeze({ available: activeComponents.every((component) => component.available),
    passed, componentCount: components.length,
    activeComponentCount: activeComponents.length,
    failedComponentIds: Object.freeze(failedComponentIds),
    components: Object.freeze(components), stepRadians: step,
    fineStepRadians: step / 2, centralDifferenceOrder: 2,
    richardsonDivisor: 3, energyProbeForceMode: "omitted",
    torqueOriginAngstrom: Object.freeze(torqueOriginAngstrom),
    movableLeverArmSumAngstrom, inductionTorqueToleranceElectronVolt:
      inductionTorqueTolerance,
    branchStable, probeEvaluationCount, distanceEvaluationCount,
    fixedEnvironmentRotatedCollectivelyForProbe: true,
    fixedEnvironmentRelaxed: false, perFixedSiteForcesResolved: false,
    targetUsed: false,
    reason: passed
      ? "the independently differentiated fixed-environment reaction torque balances the movable torque"
      : !branchStable ? "one or more environment-rotation probes changed interaction branch"
        : `environment reaction-torque balance failed: ${failedComponentIds.join(", ")}`,
    claimBoundary: "This rigidly rotates the fixed environment about one declared common origin to derive its net reaction torque from independent energy probes, then checks it against the reported movable-site torque for the total and every active component. It is a rotational-invariance and angular-momentum-balance certificate—not per-fixed-atom forces, fixed-solid relaxation, couple stress, traction, stress, mechanical equilibrium, dynamics, or physical time." });
}

/** Verify scalar-energy invariance and vector-force equivariance under one proper SE(3) transform. */
export function auditFiniteInteractionRigidMotionCovariance(currentSites, addedSites,
  reportedEvaluation, electrostaticsOptions = {}, {
    rotationAngleRadians = .731,
    translationAngstrom = [.371, -.229, .193],
    absoluteEnergyToleranceElectronVolt = 1e-8,
    absoluteForceToleranceElectronVoltPerAngstrom = 1e-6,
    absoluteVirialToleranceElectronVolt = 1e-7,
    relativeTolerance = 1e-8,
  } = {}) {
  const angle = Number(rotationAngleRadians);
  if (!(Number.isFinite(angle) && Math.abs(angle) >= .1
      && Math.abs(angle) <= Math.PI - .1)) {
    throw new RangeError("rigid-motion covariance angle must be nontrivial and proper");
  }
  if (!finiteVector(translationAngstrom)
      || !Array.isArray(currentSites) || !currentSites.length
      || !currentSites.every((site) => finiteVector(site?.position))
      || !Array.isArray(addedSites) || !addedSites.length
      || !addedSites.every((site) => finiteVector(site?.position))) {
    throw new Error("rigid-motion covariance needs finite sites and translation");
  }
  const axisNorm = Math.sqrt(14);
  const axis = [1 / axisNorm, 2 / axisNorm, 3 / axisNorm];
  const cosine = Math.cos(angle);
  const sine = Math.sin(angle);
  const rotationMatrix = [0, 1, 2].map((row) => [0, 1, 2].map((column) =>
    (row === column ? cosine : 0)
    + axis[row] * axis[column] * (1 - cosine)
    + sine * [[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]],
      [-axis[1], axis[0], 0]][row][column]));
  const rotate = (vector) => rotationMatrix.map((row) => dotVector(row, vector));
  const rotateTensor = (tensor) => rotationMatrix.map((row) =>
    rotationMatrix.map((column) => row.reduce((sum, leftValue, leftIndex) =>
      sum + leftValue * tensor[leftIndex].reduce((inner, tensorValue, rightIndex) =>
        inner + tensorValue * column[rightIndex], 0), 0)));
  const validTensor = (tensor) => Array.isArray(tensor) && tensor.length === 3
    && tensor.every(finiteVector);
  const transformSite = (site) => ({ ...site,
    position: rotate(site.position).map((value, coordinate) =>
      value + Number(translationAngstrom[coordinate])) });
  const transformedEvaluation = incrementalFinitePointChargeElectrostatics(
    currentSites.map(transformSite), addedSites.map(transformSite),
    electrostaticsOptions);
  const branchStable = Boolean(transformedEvaluation.available)
    && transformedEvaluation.pairCount === reportedEvaluation.pairCount
    && transformedEvaluation.pairInteractionModel === reportedEvaluation.pairInteractionModel
    && transformedEvaluation.inductionAppliedResponseModel
      === reportedEvaluation.inductionAppliedResponseModel
    && transformedEvaluation.inductionDirectFallbackApplied
      === reportedEvaluation.inductionDirectFallbackApplied
    && transformedEvaluation.inductionForceModeApplied
      === reportedEvaluation.inductionForceModeApplied;
  const inductionForceTolerance = Math.max(Number(reportedEvaluation
    ?.inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom) || 0,
  Number(transformedEvaluation
    ?.inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom) || 0);
  const componentSpecs = [
    { id: "total", active: true, energy: "deltaEnergyElectronVolt",
      forces: "addedForceVectorsElectronVoltPerAngstrom",
      virial: "pairVirialTensorElectronVolt",
      additionalForceTolerance: inductionForceTolerance },
    { id: "coulomb", active: true, energy: "coulombDeltaEnergyElectronVolt",
      forces: "addedCoulombForceVectorsElectronVoltPerAngstrom",
      virial: "coulombVirialTensorElectronVolt",
      additionalForceTolerance: 0 },
    { id: "born-mayer", active: Boolean(reportedEvaluation?.bornMayerRepulsionApplied),
      energy: "bornMayerRepulsiveEnergyElectronVolt",
      forces: "addedBornMayerForceVectorsElectronVoltPerAngstrom",
      virial: "bornMayerVirialTensorElectronVolt",
      additionalForceTolerance: 0 },
    { id: "dispersion", active: Boolean(reportedEvaluation?.dispersionApplied),
      energy: "dampedDispersionEnergyElectronVolt",
      forces: "addedDispersionForceVectorsElectronVoltPerAngstrom",
      virial: "dispersionVirialTensorElectronVolt",
      additionalForceTolerance: 0 },
    { id: "induction", active: Boolean(reportedEvaluation?.chargeInductionApplied),
      energy: "chargeInductionDeltaEnergyElectronVolt",
      forces: "addedInductionForceVectorsElectronVoltPerAngstrom",
      virial: null,
      additionalForceTolerance: inductionForceTolerance },
  ];
  const components = componentSpecs.map((spec) => {
    if (!spec.active) return Object.freeze({ id: spec.id, active: false,
      available: true, passed: true, siteCount: 0,
      forceRecords: Object.freeze([]), targetUsed: false });
    const sourceEnergy = reportedEvaluation?.[spec.energy];
    const transformedEnergy = transformedEvaluation?.[spec.energy];
    const sourceForces = reportedEvaluation?.[spec.forces];
    const transformedForces = transformedEvaluation?.[spec.forces];
    const sourceVirial = spec.virial ? reportedEvaluation?.[spec.virial] : null;
    const transformedVirial = spec.virial
      ? transformedEvaluation?.[spec.virial] : null;
    if (!Number.isFinite(sourceEnergy) || !Number.isFinite(transformedEnergy)
        || !Array.isArray(sourceForces) || !Array.isArray(transformedForces)
        || sourceForces.length !== addedSites.length
        || transformedForces.length !== addedSites.length
        || !sourceForces.every(finiteVector) || !transformedForces.every(finiteVector)
        || spec.virial && (!validTensor(sourceVirial)
          || !validTensor(transformedVirial))) {
      return Object.freeze({ id: spec.id, active: true, available: false,
        passed: false, siteCount: 0, forceRecords: Object.freeze([]),
        reason: "complete transformed energy/force data unavailable", targetUsed: false });
    }
    const energyResidual = transformedEnergy - sourceEnergy;
    const energyAllowance = Math.max(Number(absoluteEnergyToleranceElectronVolt),
      Number(relativeTolerance) * Math.max(1, Math.abs(sourceEnergy),
        Math.abs(transformedEnergy)));
    const forceRecords = sourceForces.map((sourceForce, siteIndex) => {
      const expectedForce = rotate(sourceForce);
      const actualForce = transformedForces[siteIndex];
      const residualVector = actualForce.map((value, coordinate) =>
        value - expectedForce[coordinate]);
      const residualMagnitude = vectorMagnitude(residualVector);
      const allowance = Math.max(Number(absoluteForceToleranceElectronVoltPerAngstrom),
        Number(relativeTolerance) * Math.max(1, vectorMagnitude(expectedForce),
          vectorMagnitude(actualForce))) + spec.additionalForceTolerance;
      return Object.freeze({ siteIndex,
        expectedRotatedForceElectronVoltPerAngstrom: Object.freeze(expectedForce),
        transformedForceElectronVoltPerAngstrom: Object.freeze([...actualForce]),
        residualVectorElectronVoltPerAngstrom: Object.freeze(residualVector),
        residualMagnitudeElectronVoltPerAngstrom: residualMagnitude,
        allowedResidualElectronVoltPerAngstrom: allowance,
        passed: residualMagnitude <= allowance });
    });
    const energyPassed = Math.abs(energyResidual) <= energyAllowance;
    const forcePassed = forceRecords.every((record) => record.passed);
    const expectedVirial = spec.virial ? rotateTensor(sourceVirial) : null;
    const virialResidualTensor = spec.virial ? transformedVirial.map((row, rowIndex) =>
      row.map((value, columnIndex) => value
        - expectedVirial[rowIndex][columnIndex])) : null;
    const virialResidualFrobenius = spec.virial
      ? matrixFrobenius(virialResidualTensor) : null;
    const virialAllowance = spec.virial
      ? Math.max(Number(absoluteVirialToleranceElectronVolt),
        Number(relativeTolerance) * Math.max(1, matrixFrobenius(expectedVirial),
          matrixFrobenius(transformedVirial))) : null;
    const virialPassed = !spec.virial
      || virialResidualFrobenius <= virialAllowance;
    return Object.freeze({ id: spec.id, active: true, available: true,
      passed: branchStable && energyPassed && forcePassed && virialPassed,
      energyPassed, forcePassed, virialPassed,
      pairVirialCovarianceChecked: Boolean(spec.virial),
      pairVirialScope: spec.virial ? "incremental central-pair contribution" : null,
      siteCount: forceRecords.length,
      sourceEnergyElectronVolt: sourceEnergy,
      transformedEnergyElectronVolt: transformedEnergy,
      energyResidualElectronVolt: energyResidual,
      allowedEnergyResidualElectronVolt: energyAllowance,
      maximumForceResidualElectronVoltPerAngstrom: Math.max(0,
        ...forceRecords.map((record) => record.residualMagnitudeElectronVoltPerAngstrom)),
      maximumAllowedForceResidualElectronVoltPerAngstrom: Math.max(0,
        ...forceRecords.map((record) => record.allowedResidualElectronVoltPerAngstrom)),
      sourcePairVirialTensorElectronVolt: spec.virial
        ? Object.freeze(sourceVirial.map((row) => Object.freeze([...row]))) : null,
      expectedRotatedPairVirialTensorElectronVolt: spec.virial
        ? Object.freeze(expectedVirial.map((row) => Object.freeze([...row]))) : null,
      transformedPairVirialTensorElectronVolt: spec.virial
        ? Object.freeze(transformedVirial.map((row) => Object.freeze([...row]))) : null,
      pairVirialResidualTensorElectronVolt: spec.virial
        ? Object.freeze(virialResidualTensor.map((row) => Object.freeze([...row]))) : null,
      pairVirialResidualFrobeniusElectronVolt: virialResidualFrobenius,
      allowedPairVirialResidualElectronVolt: virialAllowance,
      failedSiteIndices: Object.freeze(forceRecords.filter((record) => !record.passed)
        .map((record) => record.siteIndex)),
      forceRecords: Object.freeze(forceRecords), targetUsed: false });
  });
  const activeComponents = components.filter((component) => component.active);
  const failedComponentIds = activeComponents.filter((component) => !component.passed)
    .map((component) => component.id);
  const determinant = rotationMatrix[0][0]
    * (rotationMatrix[1][1] * rotationMatrix[2][2]
      - rotationMatrix[1][2] * rotationMatrix[2][1])
    - rotationMatrix[0][1] * (rotationMatrix[1][0] * rotationMatrix[2][2]
      - rotationMatrix[1][2] * rotationMatrix[2][0])
    + rotationMatrix[0][2] * (rotationMatrix[1][0] * rotationMatrix[2][1]
      - rotationMatrix[1][1] * rotationMatrix[2][0]);
  const passed = branchStable && Math.abs(determinant - 1) <= 1e-12
    && failedComponentIds.length === 0;
  return Object.freeze({ available: activeComponents.every((component) => component.available),
    passed, properRotation: Math.abs(determinant - 1) <= 1e-12,
    rotationDeterminant: determinant,
    rotationAngleRadians: angle,
    rotationAxis: Object.freeze(axis),
    rotationMatrix: Object.freeze(rotationMatrix.map((row) => Object.freeze(row))),
    translationAngstrom: Object.freeze(translationAngstrom.map(Number)),
    branchStable, componentCount: components.length,
    activeComponentCount: activeComponents.length,
    failedComponentIds: Object.freeze(failedComponentIds),
    components: Object.freeze(components),
    evaluationCount: 1,
    distanceEvaluationCount: transformedEvaluation.distanceEvaluations || 0,
    targetUsed: false,
    reason: passed
      ? "energies are invariant, movable forces are equivariant, and resolved pair virials are tensor-covariant under the declared proper SE(3) transform"
      : !branchStable ? "the rigid transform changed the finite interaction branch"
        : `rigid-motion covariance failed: ${failedComponentIds.join(", ")}`,
    claimBoundary: "This applies one predeclared proper rotation and translation to the complete finite system, then checks scalar-energy invariance, movable-force vector equivariance, and second-rank covariance of every resolved central-pair virial. The pair virial is not divided by volume and is not stress or pressure; induction has no resolved per-site pair virial. This is a frame-covariance metamorphic certificate—not transfer across materials, periodic images, a fitted potential, complete fixed-site forces, Hessian, equilibrium, dynamics, or time." });
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
    imageCount = 13,
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
  const totalDisplacementNormAngstrom = displacementVectorsAngstrom.reduce((sum, vector) =>
    sum + vectorMagnitude(vector), 0);
  const maximumInductionForceRichardsonErrorElectronVoltPerAngstrom = Math.max(0,
    ...imageEvaluations.map((evaluation) => Number(
      evaluation.inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom) || 0));
  const inductionForceWorkNumericalUncertaintyElectronVolt =
    maximumInductionForceRichardsonErrorElectronVoltPerAngstrom
    * totalDisplacementNormAngstrom;
  const commonClosureOptions = {
    absoluteToleranceElectronVolt: auditOptions.absoluteToleranceElectronVolt,
    relativeTolerance: auditOptions.relativeTolerance,
  };
  let workEnergyClosure;
  let panelWorkEnergyClosure;
  let interiorGradientConsistency;
  try {
    workEnergyClosure = auditForceEnergyPathClosure(
      images.map((image) => image.fraction),
      imageEvaluations.map((evaluation) => evaluation.deltaEnergyElectronVolt),
      imageEvaluations.map((evaluation) =>
        evaluation.addedForceVectorsElectronVoltPerAngstrom),
      displacementVectorsAngstrom, { ...commonClosureOptions,
        additionalNumericalToleranceElectronVolt:
          inductionForceWorkNumericalUncertaintyElectronVolt });
    panelWorkEnergyClosure = auditPanelResolvedForceEnergyPathClosure(
      images.map((image) => image.fraction),
      imageEvaluations.map((evaluation) => evaluation.deltaEnergyElectronVolt),
      imageEvaluations.map((evaluation) =>
        evaluation.addedForceVectorsElectronVoltPerAngstrom),
      displacementVectorsAngstrom, { ...commonClosureOptions,
        additionalNumericalToleranceElectronVolt:
          inductionForceWorkNumericalUncertaintyElectronVolt });
    interiorGradientConsistency = auditInteriorForceEnergyGradientConsistency(
      images.map((image) => image.fraction),
      imageEvaluations.map((evaluation) => evaluation.deltaEnergyElectronVolt),
      imageEvaluations.map((evaluation) =>
        evaluation.addedForceVectorsElectronVoltPerAngstrom),
      displacementVectorsAngstrom, { ...commonClosureOptions,
        additionalProjectedForceToleranceElectronVolt:
          inductionForceWorkNumericalUncertaintyElectronVolt });
  } catch (error) {
    workEnergyClosure = Object.freeze({ available: false, passed: false,
      reason: error?.message || "force-energy path closure unavailable",
      targetUsed: false });
    panelWorkEnergyClosure = Object.freeze({ available: false, passed: false,
      panelCount: 0, panels: Object.freeze([]), failedPanelIndices: Object.freeze([]),
      reason: error?.message || "panel-resolved force-energy path closure unavailable",
      targetUsed: false });
    interiorGradientConsistency = Object.freeze({ available: false, passed: false,
      eligibleImageCount: 0, records: Object.freeze([]),
      failedImageIndices: Object.freeze([]),
      reason: error?.message || "interior force-energy gradient consistency unavailable",
      targetUsed: false });
  }
  let componentWorkEnergyClosures;
  try {
    const firstEvaluation = imageEvaluations[0] || {};
    componentWorkEnergyClosures = auditComponentForceEnergyPathClosures([
      { id: "coulomb", active: true,
        energiesElectronVolt: imageEvaluations.map((evaluation) =>
          evaluation.coulombDeltaEnergyElectronVolt),
        forceFieldsElectronVoltPerAngstrom: imageEvaluations.map((evaluation) =>
          evaluation.addedCoulombForceVectorsElectronVoltPerAngstrom) },
      { id: "born-mayer", active: Boolean(firstEvaluation.bornMayerRepulsionApplied),
        energiesElectronVolt: imageEvaluations.map((evaluation) =>
          evaluation.bornMayerRepulsiveEnergyElectronVolt),
        forceFieldsElectronVoltPerAngstrom: imageEvaluations.map((evaluation) =>
          evaluation.addedBornMayerForceVectorsElectronVoltPerAngstrom) },
      { id: "dispersion", active: Boolean(firstEvaluation.dispersionApplied),
        energiesElectronVolt: imageEvaluations.map((evaluation) =>
          evaluation.dampedDispersionEnergyElectronVolt),
        forceFieldsElectronVoltPerAngstrom: imageEvaluations.map((evaluation) =>
          evaluation.addedDispersionForceVectorsElectronVoltPerAngstrom) },
      { id: "induction", active: Boolean(firstEvaluation.chargeInductionApplied),
        energiesElectronVolt: imageEvaluations.map((evaluation) =>
          evaluation.chargeInductionDeltaEnergyElectronVolt),
        forceFieldsElectronVoltPerAngstrom: imageEvaluations.map((evaluation) =>
          evaluation.addedInductionForceVectorsElectronVoltPerAngstrom),
        additionalNumericalToleranceElectronVolt:
          inductionForceWorkNumericalUncertaintyElectronVolt },
    ], images.map((image) => image.fraction), displacementVectorsAngstrom,
    commonClosureOptions);
  } catch (error) {
    componentWorkEnergyClosures = Object.freeze({ available: false, passed: false,
      componentCount: 4, activeComponentCount: 0, records: Object.freeze([]),
      failedComponentIds: Object.freeze([]),
      reason: error?.message || "component force-energy closures unavailable",
      targetUsed: false });
  }
  let endpointCartesianGradientAudit;
  try {
    const endpointImageIndices = [0, images.length - 1];
    const records = endpointImageIndices.map((imageIndex) => Object.freeze({
      imageIndex,
      fraction: images[imageIndex].fraction,
      ...auditCartesianForceEnergyGradient(currentSites, images[imageIndex].sites,
        imageEvaluations[imageIndex], electrostaticsOptions, {
          stepAngstrom: auditOptions.cartesianGradientStepAngstrom,
          maximumMovableSites:
            auditOptions.cartesianGradientMaximumMovableSites,
          absoluteToleranceElectronVoltPerAngstrom:
            auditOptions.cartesianGradientAbsoluteToleranceElectronVoltPerAngstrom,
          relativeTolerance: auditOptions.relativeTolerance,
        }),
    }));
    endpointCartesianGradientAudit = Object.freeze({
      available: records.every((record) => record.available),
      passed: records.every((record) => record.passed),
      endpointCount: records.length,
      coordinateCount: records.reduce((sum, record) =>
        sum + record.coordinateCount, 0),
      probeEvaluationCount: records.reduce((sum, record) =>
        sum + record.probeEvaluationCount, 0),
      distanceEvaluationCount: records.reduce((sum, record) =>
        sum + record.distanceEvaluationCount, 0),
      failedEndpointImageIndices: Object.freeze(records
        .filter((record) => !record.passed).map((record) => record.imageIndex)),
      records: Object.freeze(records),
      targetUsed: false,
      reason: records.every((record) => record.passed)
        ? "both endpoint force vectors match independent Cartesian energy gradients"
        : "one or both endpoint Cartesian force-energy gradients failed",
    });
  } catch (error) {
    endpointCartesianGradientAudit = Object.freeze({ available: false, passed: false,
      endpointCount: 0, coordinateCount: 0, probeEvaluationCount: 0,
      distanceEvaluationCount: 0, failedEndpointImageIndices: Object.freeze([]),
      records: Object.freeze([]),
      reason: error?.message || "endpoint Cartesian gradient audit unavailable",
      targetUsed: false });
  }
  let endpointFixedSitePairGradientAudit;
  try {
    const endpointImageIndices = [0, images.length - 1];
    const records = endpointImageIndices.map((imageIndex) => Object.freeze({
      imageIndex,
      fraction: images[imageIndex].fraction,
      ...auditFixedEnvironmentPairForceGradient(currentSites,
        images[imageIndex].sites, imageEvaluations[imageIndex],
        electrostaticsOptions, {
          stepAngstrom: auditOptions.fixedSiteGradientStepAngstrom,
          maximumSampledFixedSites:
            auditOptions.fixedSiteGradientMaximumSampledSites ?? 8,
          absoluteToleranceElectronVoltPerAngstrom:
            auditOptions.fixedSiteGradientAbsoluteToleranceElectronVoltPerAngstrom,
          relativeTolerance: auditOptions.relativeTolerance,
        }),
    }));
    endpointFixedSitePairGradientAudit = Object.freeze({
      available: records.every((record) => record.available),
      passed: records.every((record) => record.passed),
      endpointCount: records.length,
      affectedFixedSiteCount: Math.max(0,
        ...records.map((record) => record.affectedFixedSiteCount || 0)),
      sampledFixedSiteCount: records.reduce((sum, record) =>
        sum + record.sampledFixedSiteCount, 0),
      coordinateCount: records.reduce((sum, record) =>
        sum + record.coordinateCount, 0),
      probeEvaluationCount: records.reduce((sum, record) =>
        sum + record.probeEvaluationCount, 0),
      distanceEvaluationCount: records.reduce((sum, record) =>
        sum + record.distanceEvaluationCount, 0),
      failedEndpointImageIndices: Object.freeze(records
        .filter((record) => !record.passed).map((record) => record.imageIndex)),
      records: Object.freeze(records), targetUsed: false,
      reason: records.every((record) => record.passed)
        ? "both endpoint fixed-site pair-force samples close their energy gradients and complete sparse conservation laws"
        : "one or both endpoint fixed-site pair-force audits failed",
    });
  } catch (error) {
    endpointFixedSitePairGradientAudit = Object.freeze({ available: false, passed: false,
      endpointCount: 0, affectedFixedSiteCount: 0, sampledFixedSiteCount: 0,
      coordinateCount: 0, probeEvaluationCount: 0, distanceEvaluationCount: 0,
      failedEndpointImageIndices: Object.freeze([]), records: Object.freeze([]),
      reason: error?.message || "endpoint fixed-site pair gradient unavailable",
      targetUsed: false });
  }
  let endpointEnvironmentReactionAudit;
  try {
    const endpointImageIndices = [0, images.length - 1];
    const records = endpointImageIndices.map((imageIndex) => Object.freeze({
      imageIndex,
      fraction: images[imageIndex].fraction,
      ...auditEnvironmentReactionForceBalance(currentSites,
        images[imageIndex].sites, imageEvaluations[imageIndex],
        electrostaticsOptions, {
          stepAngstrom: auditOptions.environmentReactionStepAngstrom,
          absoluteToleranceElectronVoltPerAngstrom:
            auditOptions.environmentReactionAbsoluteToleranceElectronVoltPerAngstrom,
          relativeTolerance: auditOptions.relativeTolerance,
        }),
    }));
    endpointEnvironmentReactionAudit = Object.freeze({
      available: records.every((record) => record.available),
      passed: records.every((record) => record.passed),
      endpointCount: records.length,
      coordinateCount: records.reduce((sum, record) =>
        sum + (record.components.find((component) => component.id === "total")
          ?.coordinateCount || 0), 0),
      probeEvaluationCount: records.reduce((sum, record) =>
        sum + record.probeEvaluationCount, 0),
      distanceEvaluationCount: records.reduce((sum, record) =>
        sum + record.distanceEvaluationCount, 0),
      failedEndpointImageIndices: Object.freeze(records
        .filter((record) => !record.passed).map((record) => record.imageIndex)),
      records: Object.freeze(records), targetUsed: false,
      reason: records.every((record) => record.passed)
        ? "both fixed-environment endpoint reactions balance the movable net force"
        : "one or both endpoint environment reaction-force balances failed",
    });
  } catch (error) {
    endpointEnvironmentReactionAudit = Object.freeze({ available: false, passed: false,
      endpointCount: 0, coordinateCount: 0, probeEvaluationCount: 0,
      distanceEvaluationCount: 0, failedEndpointImageIndices: Object.freeze([]),
      records: Object.freeze([]),
      reason: error?.message || "endpoint environment reaction audit unavailable",
      targetUsed: false });
  }
  let endpointEnvironmentTorqueAudit;
  try {
    const endpointImageIndices = [0, images.length - 1];
    const records = endpointImageIndices.map((imageIndex) => Object.freeze({
      imageIndex,
      fraction: images[imageIndex].fraction,
      ...auditEnvironmentReactionTorqueBalance(currentSites,
        images[imageIndex].sites, imageEvaluations[imageIndex],
        electrostaticsOptions, {
          stepRadians: auditOptions.environmentReactionTorqueStepRadians,
          absoluteToleranceElectronVolt:
            auditOptions.environmentReactionTorqueAbsoluteToleranceElectronVolt,
          relativeTolerance: auditOptions.relativeTolerance,
        }),
    }));
    endpointEnvironmentTorqueAudit = Object.freeze({
      available: records.every((record) => record.available),
      passed: records.every((record) => record.passed),
      endpointCount: records.length,
      coordinateCount: records.reduce((sum, record) =>
        sum + (record.components.find((component) => component.id === "total")
          ?.coordinateCount || 0), 0),
      probeEvaluationCount: records.reduce((sum, record) =>
        sum + record.probeEvaluationCount, 0),
      distanceEvaluationCount: records.reduce((sum, record) =>
        sum + record.distanceEvaluationCount, 0),
      failedEndpointImageIndices: Object.freeze(records
        .filter((record) => !record.passed).map((record) => record.imageIndex)),
      records: Object.freeze(records), targetUsed: false,
      reason: records.every((record) => record.passed)
        ? "both fixed-environment endpoint reaction torques balance the movable torque"
        : "one or both endpoint environment reaction-torque balances failed",
    });
  } catch (error) {
    endpointEnvironmentTorqueAudit = Object.freeze({ available: false, passed: false,
      endpointCount: 0, coordinateCount: 0, probeEvaluationCount: 0,
      distanceEvaluationCount: 0, failedEndpointImageIndices: Object.freeze([]),
      records: Object.freeze([]),
      reason: error?.message || "endpoint environment reaction torque audit unavailable",
      targetUsed: false });
  }
  let endpointRigidMotionCovarianceAudit;
  try {
    const endpointImageIndices = [0, images.length - 1];
    const records = endpointImageIndices.map((imageIndex) => Object.freeze({
      imageIndex,
      fraction: images[imageIndex].fraction,
      ...auditFiniteInteractionRigidMotionCovariance(currentSites,
        images[imageIndex].sites, imageEvaluations[imageIndex],
        electrostaticsOptions, {
          rotationAngleRadians: auditOptions.rigidCovarianceRotationAngleRadians,
          translationAngstrom: auditOptions.rigidCovarianceTranslationAngstrom,
          absoluteEnergyToleranceElectronVolt:
            auditOptions.rigidCovarianceAbsoluteEnergyToleranceElectronVolt,
          absoluteForceToleranceElectronVoltPerAngstrom:
            auditOptions.rigidCovarianceAbsoluteForceToleranceElectronVoltPerAngstrom,
          relativeTolerance: auditOptions.relativeTolerance,
        }),
    }));
    endpointRigidMotionCovarianceAudit = Object.freeze({
      available: records.every((record) => record.available),
      passed: records.every((record) => record.passed),
      endpointCount: records.length,
      evaluationCount: records.reduce((sum, record) =>
        sum + record.evaluationCount, 0),
      distanceEvaluationCount: records.reduce((sum, record) =>
        sum + record.distanceEvaluationCount, 0),
      failedEndpointImageIndices: Object.freeze(records
        .filter((record) => !record.passed).map((record) => record.imageIndex)),
      records: Object.freeze(records), targetUsed: false,
      reason: records.every((record) => record.passed)
        ? "both endpoint interaction states are proper-SE(3) covariant"
        : "one or both endpoint rigid-motion covariance gates failed",
    });
  } catch (error) {
    endpointRigidMotionCovarianceAudit = Object.freeze({ available: false, passed: false,
      endpointCount: 0, evaluationCount: 0, distanceEvaluationCount: 0,
      failedEndpointImageIndices: Object.freeze([]), records: Object.freeze([]),
      reason: error?.message || "endpoint rigid-motion covariance unavailable",
      targetUsed: false });
  }
  const accepted = everySegmentEnergyForceDescent && smoothModelBranch.passed
    && workEnergyClosure.passed && panelWorkEnergyClosure.passed
    && interiorGradientConsistency.passed
    && endpointCartesianGradientAudit.passed
    && endpointFixedSitePairGradientAudit.passed
    && endpointEnvironmentReactionAudit.passed
    && endpointEnvironmentTorqueAudit.passed
    && endpointRigidMotionCovarianceAudit.passed
    && componentWorkEnergyClosures.passed;
  return Object.freeze({
    available: segments.every((segment) => segment.completeForceGradient
      && segment.responseConsistent) && smoothModelBranch.available
      && workEnergyClosure.available && panelWorkEnergyClosure.available
      && interiorGradientConsistency.available
      && endpointCartesianGradientAudit.available
      && endpointFixedSitePairGradientAudit.available
      && endpointEnvironmentReactionAudit.available
      && endpointEnvironmentTorqueAudit.available
      && endpointRigidMotionCovarianceAudit.available
      && componentWorkEnergyClosures.available,
    accepted,
    reason: !everySegmentEnergyForceDescent
      ? `response-path segment ${firstFailure?.segmentIndex ?? "?"} failed: ${firstFailure?.reason || "unavailable"}`
      : !smoothModelBranch.passed ? smoothModelBranch.reason
        : !workEnergyClosure.passed ? workEnergyClosure.reason
          : !panelWorkEnergyClosure.passed ? panelWorkEnergyClosure.reason
            : !interiorGradientConsistency.passed
              ? interiorGradientConsistency.reason
              : !endpointCartesianGradientAudit.passed
                ? endpointCartesianGradientAudit.reason
                : !endpointFixedSitePairGradientAudit.passed
                  ? endpointFixedSitePairGradientAudit.reason
                  : !endpointEnvironmentReactionAudit.passed
                    ? endpointEnvironmentReactionAudit.reason
                    : !endpointEnvironmentTorqueAudit.passed
                      ? endpointEnvironmentTorqueAudit.reason
                      : !endpointRigidMotionCovarianceAudit.passed
                        ? endpointRigidMotionCovarianceAudit.reason
              : !componentWorkEnergyClosures.passed ? componentWorkEnergyClosures.reason
                : "every bounded response-path segment passed energy, force, population, resultant, torque, symmetric-moment, aggregate-work, local-panel-work, interior-tangent, movable- and sampled-fixed-site endpoint gradients, fixed-environment-force/torque-reaction, proper-SE(3)-covariance, and component-work closure gates",
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
    panelWorkEnergyClosurePassed: panelWorkEnergyClosure.passed,
    panelWorkEnergyClosure,
    workEnergyPanelCount: panelWorkEnergyClosure.panelCount || 0,
    failedWorkEnergyPanelIndices:
      panelWorkEnergyClosure.failedPanelIndices || Object.freeze([]),
    maximumPanelWorkEnergyClosureResidualElectronVolt:
      panelWorkEnergyClosure.maximumAbsoluteClosureResidualElectronVolt ?? null,
    interiorGradientConsistencyPassed: interiorGradientConsistency.passed,
    interiorGradientConsistency,
    interiorGradientEligibleImageCount:
      interiorGradientConsistency.eligibleImageCount || 0,
    failedInteriorGradientImageIndices:
      interiorGradientConsistency.failedImageIndices || Object.freeze([]),
    maximumInteriorGradientResidualElectronVolt:
      interiorGradientConsistency.maximumAbsoluteResidualElectronVolt ?? null,
    endpointCartesianGradientPassed: endpointCartesianGradientAudit.passed,
    endpointCartesianGradientAudit,
    cartesianGradientEndpointCount:
      endpointCartesianGradientAudit.endpointCount || 0,
    cartesianGradientCoordinateCount:
      endpointCartesianGradientAudit.coordinateCount || 0,
    cartesianGradientProbeEvaluationCount:
      endpointCartesianGradientAudit.probeEvaluationCount || 0,
    cartesianGradientDistanceEvaluationCount:
      endpointCartesianGradientAudit.distanceEvaluationCount || 0,
    failedCartesianGradientEndpointImageIndices:
      endpointCartesianGradientAudit.failedEndpointImageIndices || Object.freeze([]),
    endpointFixedSitePairGradientPassed: endpointFixedSitePairGradientAudit.passed,
    endpointFixedSitePairGradientAudit,
    fixedSitePairGradientEndpointCount:
      endpointFixedSitePairGradientAudit.endpointCount || 0,
    fixedSitePairGradientAffectedSiteCount:
      endpointFixedSitePairGradientAudit.affectedFixedSiteCount || 0,
    fixedSitePairGradientSampledSiteCount:
      endpointFixedSitePairGradientAudit.sampledFixedSiteCount || 0,
    fixedSitePairGradientCoordinateCount:
      endpointFixedSitePairGradientAudit.coordinateCount || 0,
    fixedSitePairGradientProbeEvaluationCount:
      endpointFixedSitePairGradientAudit.probeEvaluationCount || 0,
    fixedSitePairGradientDistanceEvaluationCount:
      endpointFixedSitePairGradientAudit.distanceEvaluationCount || 0,
    failedFixedSitePairGradientEndpointImageIndices:
      endpointFixedSitePairGradientAudit.failedEndpointImageIndices || Object.freeze([]),
    endpointEnvironmentReactionPassed: endpointEnvironmentReactionAudit.passed,
    endpointEnvironmentReactionAudit,
    environmentReactionEndpointCount:
      endpointEnvironmentReactionAudit.endpointCount || 0,
    environmentReactionCoordinateCount:
      endpointEnvironmentReactionAudit.coordinateCount || 0,
    environmentReactionProbeEvaluationCount:
      endpointEnvironmentReactionAudit.probeEvaluationCount || 0,
    environmentReactionDistanceEvaluationCount:
      endpointEnvironmentReactionAudit.distanceEvaluationCount || 0,
    failedEnvironmentReactionEndpointImageIndices:
      endpointEnvironmentReactionAudit.failedEndpointImageIndices || Object.freeze([]),
    endpointEnvironmentTorquePassed: endpointEnvironmentTorqueAudit.passed,
    endpointEnvironmentTorqueAudit,
    environmentTorqueEndpointCount:
      endpointEnvironmentTorqueAudit.endpointCount || 0,
    environmentTorqueCoordinateCount:
      endpointEnvironmentTorqueAudit.coordinateCount || 0,
    environmentTorqueProbeEvaluationCount:
      endpointEnvironmentTorqueAudit.probeEvaluationCount || 0,
    environmentTorqueDistanceEvaluationCount:
      endpointEnvironmentTorqueAudit.distanceEvaluationCount || 0,
    failedEnvironmentTorqueEndpointImageIndices:
      endpointEnvironmentTorqueAudit.failedEndpointImageIndices || Object.freeze([]),
    endpointRigidMotionCovariancePassed:
      endpointRigidMotionCovarianceAudit.passed,
    endpointRigidMotionCovarianceAudit,
    rigidMotionCovarianceEndpointCount:
      endpointRigidMotionCovarianceAudit.endpointCount || 0,
    rigidMotionCovarianceEvaluationCount:
      endpointRigidMotionCovarianceAudit.evaluationCount || 0,
    rigidMotionCovarianceDistanceEvaluationCount:
      endpointRigidMotionCovarianceAudit.distanceEvaluationCount || 0,
    failedRigidMotionCovarianceEndpointImageIndices:
      endpointRigidMotionCovarianceAudit.failedEndpointImageIndices || Object.freeze([]),
    endpointPairVirialCovariancePassed: endpointRigidMotionCovarianceAudit.passed
      && endpointRigidMotionCovarianceAudit.records.every((record) =>
        record.components.filter((component) => component.active
          && component.pairVirialCovarianceChecked)
          .every((component) => component.virialPassed)),
    pairVirialEndpointCount: endpointRigidMotionCovarianceAudit.records.length,
    pairVirialActiveComponentCount: Math.max(0,
      ...endpointRigidMotionCovarianceAudit.records.map((record) =>
        record.components.filter((component) => component.active
          && component.pairVirialCovarianceChecked).length)),
    componentWorkEnergyClosuresPassed: componentWorkEnergyClosures.passed,
    componentWorkEnergyClosures,
    activeWorkEnergyComponentCount:
      componentWorkEnergyClosures.activeComponentCount || 0,
    failedWorkEnergyComponentIds:
      componentWorkEnergyClosures.failedComponentIds || Object.freeze([]),
    inductionForceWorkNumericalUncertaintyElectronVolt,
    maximumInductionForceRichardsonErrorElectronVoltPerAngstrom,
    groupLabelsFrozenBeforePath: true,
    straightLineCartesianImages: true,
    pathParameterIsPhysicalTime: false,
    targetUsed: false,
    claimBoundary: "The fixed Cartesian image sequence is a bounded continuity, monotonicity, force-work/energy, subsystem-reaction, and reference-frame consistency check between two coordinate sets. Aggregate work, every local five-image panel, every eligible interior force-versus-energy tangent, both movable-site endpoint Cartesian gradients, bounded force-ranked samples of fixed-site central-pair gradients, complete sparse pair force/torque conservation, collectively differentiated fixed-environment reactions, endpoint proper-SE(3) energy/force covariance, and every active interaction component must close independently. Per-fixed-site induction and fixed-fixed forces remain unresolved; the latter are constant in this incremental energy. These checks do not establish transfer between materials, a complete fixed-solid force field, relaxation, traction, stress, couple stress, an all-image Cartesian gradient, or a Hessian. This is not thermodynamic work, a free-energy calculation, minimum-energy path, transition state, dynamics, rate, or elapsed physical time.",
  });
}
