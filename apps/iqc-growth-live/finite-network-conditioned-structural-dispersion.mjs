import { buildFiniteNetworkConditionedStructuralPath }
  from "./finite-network-conditioned-structural-path.mjs?v=20260901-438";

const FIELDS = Object.freeze([
  "atomCount", "meanCoordination", "steinhardtQ4", "steinhardtQ6",
]);

const STRUCTURAL_KEYS = Object.freeze({
  atomCount: "expectedAtomCount",
  meanCoordination: "expectedMeanCoordination",
  steinhardtQ4: "expectedSteinhardtQ4",
  steinhardtQ6: "expectedSteinhardtQ6",
});

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-conditioned-structural-dispersion-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    trajectorySampled: false,
    thermalFluctuationClaimed: false,
    bulkVarianceClaimed: false,
    claimBoundary: "Structural dispersion requires exact successful-passage state probabilities and one consistent finite-window geometric descriptor per state. It measures discrete path-ensemble heterogeneity inside the observed fixed-rate network—not coordinate noise, thermal fluctuations within a state, uncertainty in rates, a trajectory sample, a bulk susceptibility, or a complete mechanism catalog.",
  };
}

function weightedQuantile(rows, field, probability, normalization) {
  if (!(normalization > 1e-15)) return null;
  const ordered = rows.map((row) => ({ value: row.descriptor[field],
    weight: row.weight / normalization }))
    .sort((first, second) => first.value - second.value);
  let cumulative = 0;
  for (const row of ordered) {
    cumulative += row.weight;
    if (cumulative + 1e-14 >= probability) return row.value;
  }
  return ordered.at(-1)?.value ?? null;
}

function weightedMoments(rows) {
  const normalization = rows.reduce((sum, row) => sum + row.weight, 0);
  if (!(normalization > 1e-15)) return null;
  const fields = Object.fromEntries(FIELDS.map((field) => {
    const mean = rows.reduce((sum, row) =>
      sum + row.weight * row.descriptor[field], 0) / normalization;
    const variance = Math.max(0, rows.reduce((sum, row) => {
      const delta = row.descriptor[field] - mean;
      return sum + row.weight * delta * delta;
    }, 0) / normalization);
    return [field, { mean, variance, standardDeviation: Math.sqrt(variance),
      q10: weightedQuantile(rows, field, .1, normalization),
      median: weightedQuantile(rows, field, .5, normalization),
      q90: weightedQuantile(rows, field, .9, normalization) }];
  }));
  const correlations = {};
  for (let first = 0; first < FIELDS.length; first += 1) {
    for (let second = first + 1; second < FIELDS.length; second += 1) {
      const firstField = FIELDS[first];
      const secondField = FIELDS[second];
      const covariance = rows.reduce((sum, row) => sum + row.weight
        * (row.descriptor[firstField] - fields[firstField].mean)
        * (row.descriptor[secondField] - fields[secondField].mean), 0)
        / normalization;
      const denominator = fields[firstField].standardDeviation
        * fields[secondField].standardDeviation;
      correlations[`${firstField}:${secondField}`] = {
        covariance,
        correlation: denominator > 1e-15 ? Math.max(-1, Math.min(1,
          covariance / denominator)) : null,
      };
    }
  }
  const probabilities = rows.map((row) => row.weight / normalization)
    .filter((weight) => weight > 1e-15);
  const entropyNats = -probabilities.reduce((sum, weight) =>
    sum + weight * Math.log(weight), 0);
  return {
    normalization,
    fields,
    correlations,
    entropyNats,
    effectiveStateCount: Math.exp(entropyNats),
    occupiedStateCount: probabilities.length,
  };
}

export function buildFiniteNetworkConditionedStructuralDispersion(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
} = {}) {
  const structuralPath = buildFiniteNetworkConditionedStructuralPath(network,
    { sourceStateSha256, targetStateSha256 });
  if (!structuralPath.available) return unavailable(structuralPath.reason,
    { structuralPath });
  const descriptorByState = new Map(structuralPath.stateDescriptors.map((record) =>
    [record.stateSha256, record.descriptor]));
  const timeline = structuralPath.arrival.timeline.map((arrivalSample, sampleIndex) => {
    const rows = arrivalSample.conditionedStateProbabilities.map((state) => ({
      ...state,
      weight: state.probability,
      descriptor: descriptorByState.get(state.stateSha256),
    }));
    if (rows.some((row) => !row.descriptor)) {
      throw new Error("conditioned structural dispersion lost an exact-state descriptor");
    }
    const targetInclusive = weightedMoments(rows);
    const surviving = weightedMoments(rows.filter((row) => !row.absorbedTarget));
    const structuralSample = structuralPath.timeline[sampleIndex];
    const meanConsistencyResidual = Math.max(...FIELDS.map((field) =>
      Math.abs(targetInclusive.fields[field].mean
        - structuralSample[STRUCTURAL_KEYS[field]])));
    const atomSpan = Math.abs(structuralPath.targetDescriptor.atomCount
      - structuralPath.sourceDescriptor.atomCount);
    return {
      relativeToConditionalMean: arrivalSample.relativeToConditionalMean,
      logElapsedSeconds: arrivalSample.logElapsedSeconds,
      elapsedSeconds: arrivalSample.elapsedSeconds,
      cumulativeArrivalProbability: arrivalSample.cumulativeArrivalProbability,
      targetInclusive,
      surviving,
      normalizedTargetInclusiveAtomCountStandardDeviation: atomSpan
        ? targetInclusive.fields.atomCount.standardDeviation / atomSpan : null,
      normalizedSurvivingAtomCountStandardDeviation: atomSpan && surviving
        ? surviving.fields.atomCount.standardDeviation / atomSpan : null,
      meanConsistencyResidual,
    };
  });
  const medianRegion = timeline.reduce((best, sample) =>
    Math.abs(sample.cumulativeArrivalProbability - .5)
      < Math.abs(best.cumulativeArrivalProbability - .5) ? sample : best);
  const peakSurvivorDiversity = timeline.filter((sample) => sample.surviving)
    .reduce((best, sample) => sample.surviving.effectiveStateCount
      > best.surviving.effectiveStateCount ? sample : best);
  const maximumMeanConsistencyResidual = Math.max(...timeline.map((sample) =>
    sample.meanConsistencyResidual));
  const initialVarianceResidual = Math.max(...FIELDS.map((field) =>
    timeline[0].targetInclusive.fields[field].variance));
  const minimumVariance = Math.min(...timeline.flatMap((sample) => [
    ...FIELDS.map((field) => sample.targetInclusive.fields[field].variance),
    ...(sample.surviving ? FIELDS.map((field) =>
      sample.surviving.fields[field].variance) : []),
  ]));
  const identitiesPassed = structuralPath.identitiesPassed
    && maximumMeanConsistencyResidual <= 1e-10
    && initialVarianceResidual <= 1e-10
    && minimumVariance >= 0;
  return {
    schema: "gcts-finite-network-conditioned-structural-dispersion-v1",
    available: true,
    model: "Exact conditioned finite-state structural moments and discrete weighted quantiles",
    sourceStateSha256,
    targetStateSha256,
    temperatureKelvin: structuralPath.temperatureKelvin,
    methodSettingsSha256: structuralPath.methodSettingsSha256,
    contactReach: structuralPath.contactReach,
    relevantStateCount: structuralPath.relevantStateCount,
    timeline,
    medianRegion,
    peakSurvivorDiversity,
    maximumMeanConsistencyResidual,
    initialVarianceResidual,
    minimumVariance,
    identitiesPassed,
    structuralPath,
    finiteObservationBoundaryIncluded: true,
    periodicImagesAdded: false,
    exactStatesChanged: false,
    targetUsed: false,
    trajectorySampled: false,
    thermalFluctuationClaimed: false,
    rateUncertaintyIncluded: false,
    bulkVarianceClaimed: false,
    phaseClassified: false,
    mechanismCatalogComplete: false,
    claimBoundary: "At each exact phase-type time, this audit takes second moments and weighted 10/50/90% quantiles of atom count, finite-window coordination, and Q4/Q6 over the successful-path state distribution. Survivor-conditioned statistics exclude already absorbed target paths; target-inclusive statistics retain them. The spread is discrete mechanism/path heterogeneity inside one observed fixed-rate finite network—not within-state coordinate noise, thermal fluctuations, uncertain barriers or rates, sampled trajectories, a bulk susceptibility, a phase label, or a complete growth mechanism.",
  };
}
