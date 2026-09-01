import { buildFiniteNetworkConditionedStructuralDispersion }
  from "./finite-network-conditioned-structural-dispersion.mjs?v=20260901-430";

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-conditioned-scattering-path-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    trajectorySampled: false,
    experimentalIntensityClaimed: false,
    phaseClassified: false,
    mechanismCatalogComplete: false,
    claimBoundary: "A successful-path powder signature requires one reproducible unit-weight finite-window Debye fingerprint for every relevant exact state. The result is scale-normalized geometric scattering on a q·dₙₙ grid—not experimental X-ray or neutron intensity, a structure refinement, a phase label, a sampled trajectory, or proof that the observed mechanism catalog is complete.",
  };
}

function arraysEqual(first, second, tolerance = 1e-10) {
  return Array.isArray(first) && Array.isArray(second) && first.length === second.length
    && first.every((value, index) => Number.isFinite(value)
      && Number.isFinite(second[index]) && Math.abs(value - second[index]) <= tolerance);
}

function signature(descriptor) {
  return descriptor?.dimensionlessPowderScattering || null;
}

function rootMeanSquare(values) {
  return Math.sqrt(values.reduce((sum, value) => sum + value * value, 0)
    / Math.max(1, values.length));
}

function spectrumMoments(rows, qCount) {
  const normalization = rows.reduce((sum, row) => sum + row.weight, 0);
  if (!(normalization > 1e-15)) return null;
  const mean = Array(qCount).fill(0);
  rows.forEach((row) => row.intensity.forEach((value, index) => {
    mean[index] += row.weight * value / normalization;
  }));
  const variance = Array(qCount).fill(0);
  rows.forEach((row) => row.intensity.forEach((value, index) => {
    variance[index] += row.weight * (value - mean[index]) ** 2 / normalization;
  }));
  const standardDeviation = variance.map((value) => Math.sqrt(Math.max(0, value)));
  return { normalization, mean, variance, standardDeviation,
    rmsStandardDeviation: rootMeanSquare(standardDeviation) };
}

export function buildFiniteNetworkConditionedScatteringPath(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
} = {}) {
  const structuralDispersion = buildFiniteNetworkConditionedStructuralDispersion(network,
    { sourceStateSha256, targetStateSha256 });
  if (!structuralDispersion.available) return unavailable(structuralDispersion.reason,
    { structuralDispersion });
  const relevant = new Set(structuralDispersion.structuralPath.stateDescriptors.map((record) =>
    record.stateSha256));
  const observations = new Map([...relevant].map((stateSha256) => [stateSha256, []]));
  (network?.directedEdges || []).forEach((edge) => {
    if (relevant.has(edge.fromStateSha256)) observations.get(edge.fromStateSha256)
      .push(signature(edge.initialStateGeometricDescriptor));
    if (relevant.has(edge.toStateSha256)) observations.get(edge.toStateSha256)
      .push(signature(edge.finalStateGeometricDescriptor));
  });
  const missingStateSha256 = [...relevant].filter((stateSha256) =>
    !observations.get(stateSha256).length
      || observations.get(stateSha256).some((record) => !record));
  if (missingStateSha256.length) return unavailable(
    `${missingStateSha256.length} successful-passage states lack a finite powder signature.`,
    { structuralDispersion, missingStateSha256 });
  const inconsistentStateSha256 = [...relevant].filter((stateSha256) => {
    const records = observations.get(stateSha256);
    return records.slice(1).some((record) =>
      !arraysEqual(records[0].qTimesMedianNearestNeighbor,
        record.qTimesMedianNearestNeighbor)
      || !arraysEqual(records[0].unitWeightIntensity, record.unitWeightIntensity));
  });
  if (inconsistentStateSha256.length) return unavailable(
    `${inconsistentStateSha256.length} successful-passage state hashes have inconsistent powder signatures.`,
    { structuralDispersion, inconsistentStateSha256 });
  const signatureByState = new Map([...relevant].map((stateSha256) =>
    [stateSha256, observations.get(stateSha256)[0]]));
  const qGrid = signatureByState.get(sourceStateSha256).qTimesMedianNearestNeighbor;
  const incompatibleGridStateSha256 = [...relevant].filter((stateSha256) =>
    !arraysEqual(qGrid, signatureByState.get(stateSha256).qTimesMedianNearestNeighbor));
  if (incompatibleGridStateSha256.length) return unavailable(
    `${incompatibleGridStateSha256.length} successful-passage states use a different q·dₙₙ grid.`,
    { structuralDispersion, incompatibleGridStateSha256 });
  const timeline = structuralDispersion.structuralPath.arrival.timeline.map((sample) => {
    const rows = sample.conditionedStateProbabilities.map((state) => ({
      ...state,
      weight: state.probability,
      intensity: signatureByState.get(state.stateSha256).unitWeightIntensity,
    }));
    return {
      relativeToConditionalMean: sample.relativeToConditionalMean,
      logElapsedSeconds: sample.logElapsedSeconds,
      elapsedSeconds: sample.elapsedSeconds,
      cumulativeArrivalProbability: sample.cumulativeArrivalProbability,
      targetInclusive: spectrumMoments(rows, qGrid.length),
      surviving: spectrumMoments(rows.filter((row) => !row.absorbedTarget), qGrid.length),
    };
  });
  const sourceIntensity = signatureByState.get(sourceStateSha256).unitWeightIntensity;
  const targetIntensity = signatureByState.get(targetStateSha256).unitWeightIntensity;
  const sourceTargetDifference = targetIntensity.map((value, index) =>
    value - sourceIntensity[index]);
  const contrastIndices = qGrid.map((q, index) => ({ q, index,
    absoluteContrast: Math.abs(sourceTargetDifference[index]) }))
    .sort((first, second) => second.absoluteContrast - first.absoluteContrast
      || first.q - second.q).slice(0, 4).sort((first, second) => first.q - second.q);
  const medianRegion = timeline.reduce((best, sample) =>
    Math.abs(sample.cumulativeArrivalProbability - .5)
      < Math.abs(best.cumulativeArrivalProbability - .5) ? sample : best);
  const peakSpectralDispersion = timeline.filter((sample) => sample.surviving)
    .reduce((best, sample) => sample.surviving.rmsStandardDeviation
      > best.surviving.rmsStandardDeviation ? sample : best);
  const initialMeanResidual = Math.max(...timeline[0].targetInclusive.mean.map((value, index) =>
    Math.abs(value - sourceIntensity[index])));
  const initialVarianceResidual = Math.max(...timeline[0].targetInclusive.variance);
  const finalTargetResidual = Math.max(...timeline.at(-1).targetInclusive.mean.map((value, index) =>
    Math.abs(value - targetIntensity[index])));
  const minimumVariance = Math.min(...timeline.flatMap((sample) => [
    ...sample.targetInclusive.variance,
    ...(sample.surviving?.variance || []),
  ]));
  const identitiesPassed = structuralDispersion.identitiesPassed
    && initialMeanResidual <= 1e-10 && initialVarianceResidual <= 1e-10
    && minimumVariance >= 0;
  return {
    schema: "gcts-finite-network-conditioned-scattering-path-v1",
    available: true,
    model: "Exact conditioned state mixture of scale-normalized finite-window Debye signatures",
    sourceStateSha256,
    targetStateSha256,
    temperatureKelvin: structuralDispersion.temperatureKelvin,
    methodSettingsSha256: structuralDispersion.methodSettingsSha256,
    qTimesMedianNearestNeighbor: [...qGrid],
    sourceIntensity: [...sourceIntensity],
    targetIntensity: [...targetIntensity],
    sourceTargetRmsDifference: rootMeanSquare(sourceTargetDifference),
    contrastIndices,
    timeline,
    medianRegion,
    peakSpectralDispersion,
    initialMeanResidual,
    initialVarianceResidual,
    finalTargetResidual,
    minimumVariance,
    identitiesPassed,
    structuralDispersion,
    finiteObservationBoundaryIncluded: true,
    periodicImagesAdded: false,
    scaleNormalizedByStateNearestNeighbor: true,
    scatteringWeights: "one per site",
    qDependentFormFactorsUsed: false,
    DebyeWallerDampingUsed: false,
    instrumentResponseUsed: false,
    exactStatesChanged: false,
    targetUsed: false,
    trajectorySampled: false,
    experimentalIntensityClaimed: false,
    phaseClassified: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Every spectrum is the unit-weight finite Debye orientational average of one exact finite colored point set, divided by atom count and evaluated on a fixed dimensionless q·dₙₙ grid. Exact conditioned state probabilities produce the target-inclusive and still-in-flight mean and variance. This is a scale-normalized geometric powder signature—not experimental X-ray or neutron intensity, q-dependent form factors, Debye–Waller damping, instrument broadening, a structure refinement, a phase label, sampled dynamics, or a mechanism-complete bulk scattering law.",
  };
}
