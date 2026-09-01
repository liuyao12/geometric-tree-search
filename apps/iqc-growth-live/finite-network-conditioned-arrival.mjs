import { buildFiniteNetworkFirstPassage }
  from "./finite-network-first-passage.mjs?v=20260901-412";
import { buildFiniteNetworkConditionedHeterogeneity }
  from "./finite-network-conditioned-heterogeneity.mjs?v=20260901-412";

const DEFAULT_TAIL_TOLERANCE = 1e-12;

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-conditioned-arrival-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    trajectoryEnsembleSampled: false,
    rateUncertaintyPropagated: false,
    mechanismCatalogComplete: false,
    claimBoundary: "The arrival distribution is a deterministic matrix-exponential solution for successful passage through the finite observed fixed-rate catalog. It is not a sampled trajectory ensemble, rate-uncertainty interval, complete mechanism distribution, or bulk growth-time distribution.",
  };
}

function multiplyRowVector(vector, matrix) {
  const result = Array(vector.length).fill(0);
  vector.forEach((value, row) => matrix[row].forEach((entry, column) => {
    result[column] += value * entry;
  }));
  return result;
}

function uniformizedStep(initial, transition, multiplier, tolerance) {
  if (multiplier === 0) return { probabilities: [...initial], poissonTerms: 1,
    truncatedTailProbability: 0 };
  let power = [...initial];
  let weight = Math.exp(-multiplier);
  let cumulativeWeight = weight;
  const probabilities = power.map((value) => weight * value);
  let term = 0;
  const maximumTerms = Math.max(200,
    Math.ceil(multiplier + 20 * Math.sqrt(multiplier + 1)));
  while (1 - cumulativeWeight > tolerance && term < maximumTerms) {
    term += 1;
    power = multiplyRowVector(power, transition);
    weight *= multiplier / term;
    cumulativeWeight += weight;
    power.forEach((value, index) => { probabilities[index] += weight * value; });
  }
  const normalizer = probabilities.reduce((sum, value) => sum + value, 0);
  return {
    probabilities: probabilities.map((value) => value / normalizer),
    poissonTerms: term + 1,
    truncatedTailProbability: Math.max(0, 1 - cumulativeWeight),
  };
}

function propagate(initial, transition, multiplier, tolerance) {
  const segmentCount = Math.max(1, Math.ceil(multiplier / 20));
  const segmentMultiplier = multiplier / segmentCount;
  let probabilities = [...initial];
  let poissonTerms = 0;
  let accumulatedTailBound = 0;
  for (let segment = 0; segment < segmentCount; segment += 1) {
    const result = uniformizedStep(probabilities, transition, segmentMultiplier,
      tolerance / segmentCount);
    probabilities = result.probabilities;
    poissonTerms += result.poissonTerms;
    accumulatedTailBound += result.truncatedTailProbability;
  }
  return { probabilities, poissonTerms, accumulatedTailBound, segmentCount };
}

function physicalValueFromLog(logValue) {
  return Number.isFinite(logValue) && logValue >= -745 && logValue <= 709
    ? Math.exp(logValue) : null;
}

function logPhysicalSeconds(scaledTime, maximumLogRatePerSecond) {
  return scaledTime > 0 ? Math.log(scaledTime) - maximumLogRatePerSecond : -Infinity;
}

export function buildFiniteNetworkConditionedArrival(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
  poissonTailTolerance = DEFAULT_TAIL_TOLERANCE,
  timelineSampleCount = 61,
} = {}) {
  if (!(poissonTailTolerance > 0 && poissonTailTolerance <= 1e-8)) {
    return unavailable("The Poisson-tail tolerance must lie in (0, 10⁻⁸].");
  }
  if (!Number.isInteger(timelineSampleCount) || timelineSampleCount < 21
      || timelineSampleCount > 201) {
    return unavailable("The deterministic arrival timeline needs 21–201 samples.");
  }
  const nodes = Array.isArray(network?.nodes) ? network.nodes : [];
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  const firstPassage = buildFiniteNetworkFirstPassage(network,
    { sourceStateSha256, targetStateSha256 });
  const heterogeneity = buildFiniteNetworkConditionedHeterogeneity(network,
    { sourceStateSha256, targetStateSha256 });
  if (!firstPassage.available || !heterogeneity.available) {
    return unavailable(heterogeneity.reason || firstPassage.reason
      || "A finite successful source-to-target passage is required.",
    { firstPassage, heterogeneity });
  }
  const hitting = new Map(firstPassage.states.map((state) =>
    [state.stateSha256, state.targetHittingProbability]));
  const transient = nodes.filter((node) => node.stateSha256 !== targetStateSha256
    && (hitting.get(node.stateSha256) || 0) > 1e-14);
  const transientIndex = new Map(transient.map((node, index) => [node.stateSha256, index]));
  const sourceIndex = transientIndex.get(sourceStateSha256);
  if (sourceIndex == null) return unavailable("The source is not a conditioned transient state.");
  const maximumLogRatePerSecond = firstPassage.maximumLogRatePerSecond;
  const conditionedEdges = edges.map((edge) => {
    const sourceProbability = hitting.get(edge.fromStateSha256) || 0;
    const destinationProbability = hitting.get(edge.toStateSha256) || 0;
    const scaledRate = Math.exp(edge.logRatePerSecond - maximumLogRatePerSecond);
    return { ...edge, conditionedScaledRate: sourceProbability > 0
      && destinationProbability > 0 && edge.fromStateSha256 !== targetStateSha256
      ? scaledRate * destinationProbability / sourceProbability : 0 };
  });
  const scaledExitRates = transient.map((node) => conditionedEdges.filter((edge) =>
    edge.fromStateSha256 === node.stateSha256).reduce((sum, edge) =>
    sum + edge.conditionedScaledRate, 0));
  const uniformizationScaledRate = Math.max(...scaledExitRates);
  if (!(uniformizationScaledRate > 0)) return unavailable("No conditioned exit rate is available.");
  const targetIndex = transient.length;
  const transition = Array.from({ length: transient.length + 1 }, () =>
    Array(transient.length + 1).fill(0));
  conditionedEdges.forEach((edge) => {
    if (!(edge.conditionedScaledRate > 0)) return;
    const row = transientIndex.get(edge.fromStateSha256);
    const column = edge.toStateSha256 === targetStateSha256
      ? targetIndex : transientIndex.get(edge.toStateSha256);
    if (row != null && column != null) {
      transition[row][column] += edge.conditionedScaledRate / uniformizationScaledRate;
    }
  });
  transient.forEach((_, row) => {
    transition[row][row] += 1 - scaledExitRates[row] / uniformizationScaledRate;
  });
  transition[targetIndex][targetIndex] = 1;
  const maximumStochasticResidual = Math.max(...transition.map((row) => Math.abs(
    row.reduce((sum, value) => sum + value, 0) - 1)));
  if (maximumStochasticResidual > 1e-10
      || transition.some((row) => row.some((value) => value < -1e-12))) {
    return unavailable("The conditioned uniformization matrix is not stochastic.");
  }
  const initial = Array(transient.length + 1).fill(0); initial[sourceIndex] = 1;
  const stateId = new Map(nodes.map((node) => [node.stateSha256, node.stateId]));
  const meanScaledTime = heterogeneity.passageTime.meanScaledTime;
  const meanUniformizationMultiplier = meanScaledTime * uniformizationScaledRate;
  const targetRatesByTransient = transient.map((node) => conditionedEdges.filter((edge) =>
    edge.fromStateSha256 === node.stateSha256
      && edge.toStateSha256 === targetStateSha256).reduce((sum, edge) =>
    sum + edge.conditionedScaledRate, 0));
  const cache = new Map();
  const evaluate = (relativeToMean) => {
    const cacheKey = relativeToMean.toPrecision(15);
    if (cache.has(cacheKey)) return cache.get(cacheKey);
    const propagated = propagate(initial, transition,
      relativeToMean * meanUniformizationMultiplier, poissonTailTolerance);
    const survivalProbability = propagated.probabilities.slice(0, targetIndex)
      .reduce((sum, value) => sum + value, 0);
    const cumulativeArrivalProbability = Math.max(0, Math.min(1,
      propagated.probabilities[targetIndex]));
    const densityScaled = propagated.probabilities.slice(0, targetIndex)
      .reduce((sum, value, index) => sum + value * targetRatesByTransient[index], 0);
    const scaledTime = relativeToMean * meanScaledTime;
    const logElapsedSeconds = logPhysicalSeconds(scaledTime, maximumLogRatePerSecond);
    const result = {
      relativeToConditionalMean: relativeToMean,
      scaledTime,
      logElapsedSeconds,
      elapsedSeconds: relativeToMean === 0 ? 0 : physicalValueFromLog(logElapsedSeconds),
      survivalProbability,
      cumulativeArrivalProbability,
      normalizedArrivalDensityPerMeanTime: densityScaled * meanScaledTime,
      normalizedHazardPerMeanTime: survivalProbability > 1e-15
        ? densityScaled * meanScaledTime / survivalProbability : null,
      probabilityComplementResidual: survivalProbability
        + cumulativeArrivalProbability - 1,
      poissonTerms: propagated.poissonTerms,
      uniformizationSegments: propagated.segmentCount,
      accumulatedPoissonTailBound: propagated.accumulatedTailBound,
      conditionedStateProbabilities: [
        ...transient.map((node, index) => ({ stateId: node.stateId,
          stateSha256: node.stateSha256, probability: propagated.probabilities[index],
          absorbedTarget: false })),
        { stateId: stateId.get(targetStateSha256), stateSha256: targetStateSha256,
          probability: propagated.probabilities[targetIndex], absorbedTarget: true },
      ],
    };
    cache.set(cacheKey, result); return result;
  };
  const quantile = (probability) => {
    let lower = 0, upper = 1;
    while (evaluate(upper).cumulativeArrivalProbability < probability && upper < 1e9) {
      lower = upper; upper *= 2;
    }
    if (evaluate(upper).cumulativeArrivalProbability < probability) return null;
    for (let iteration = 0; iteration < 64; iteration += 1) {
      const middle = (lower + upper) / 2;
      if (evaluate(middle).cumulativeArrivalProbability < probability) lower = middle;
      else upper = middle;
    }
    const relativeToConditionalMean = (lower + upper) / 2;
    const scaledTime = relativeToConditionalMean * meanScaledTime;
    const logSeconds = logPhysicalSeconds(scaledTime, maximumLogRatePerSecond);
    return { probability, relativeToConditionalMean, scaledTime,
      logSeconds, seconds: physicalValueFromLog(logSeconds) };
  };
  const q05 = quantile(.05), median = quantile(.5), q95 = quantile(.95), q99 = quantile(.99);
  if (![q05, median, q95, q99].every(Boolean)) {
    return unavailable("The conditioned arrival quantiles did not converge within 10⁹ mean times.");
  }
  const minimumPositiveRatio = Math.max(1e-5, q05.relativeToConditionalMean / 4);
  const maximumRatio = Math.max(2, q99.relativeToConditionalMean * 1.25);
  const timeline = [{ ...evaluate(0) }];
  for (let index = 0; index < timelineSampleCount - 1; index += 1) {
    const fraction = index / (timelineSampleCount - 2);
    const ratio = Math.exp(Math.log(minimumPositiveRatio)
      + fraction * (Math.log(maximumRatio) - Math.log(minimumPositiveRatio)));
    timeline.push({ ...evaluate(ratio) });
  }
  timeline.sort((first, second) =>
    first.relativeToConditionalMean - second.relativeToConditionalMean);
  const monotonicArrivalPassed = timeline.every((sample, index) => !index
    || sample.cumulativeArrivalProbability + 1e-11
      >= timeline[index - 1].cumulativeArrivalProbability);
  const maximumProbabilityComplementResidual = Math.max(...timeline.map((sample) =>
    Math.abs(sample.probabilityComplementResidual)));
  const maximumAccumulatedPoissonTailBound = Math.max(...timeline.map((sample) =>
    sample.accumulatedPoissonTailBound));
  const q05Check = evaluate(q05.relativeToConditionalMean).cumulativeArrivalProbability;
  const medianCheck = evaluate(median.relativeToConditionalMean).cumulativeArrivalProbability;
  const q95Check = evaluate(q95.relativeToConditionalMean).cumulativeArrivalProbability;
  const maximumQuantileProbabilityResidual = Math.max(Math.abs(q05Check - .05),
    Math.abs(medianCheck - .5), Math.abs(q95Check - .95));
  const identitiesPassed = maximumStochasticResidual <= 1e-10
    && maximumProbabilityComplementResidual <= 1e-10
    && maximumQuantileProbabilityResidual <= 1e-9
    && monotonicArrivalPassed;
  return {
    schema: "gcts-finite-network-conditioned-arrival-v1",
    available: true,
    model: "Doob-conditioned phase-type arrival distribution by segmented uniformization",
    sourceStateSha256,
    targetStateSha256,
    temperatureKelvin: firstPassage.temperatureKelvin,
    methodSettingsSha256: firstPassage.methodSettingsSha256,
    transientStateCount: transient.length,
    directedEdgeCount: edges.length,
    maximumLogRatePerSecond,
    uniformizationScaledRate,
    meanUniformizationMultiplier,
    conditionalMeanFirstPassageLogSeconds:
      firstPassage.sourceConditionalMeanFirstPassageLogSeconds,
    conditionalMeanFirstPassageSeconds:
      firstPassage.sourceConditionalMeanFirstPassageSeconds,
    conditionalTimeCoefficientOfVariation:
      heterogeneity.passageTime.coefficientOfVariation,
    quantiles: { q05, median, q95, q99 },
    centralNinetyPercentTimeRatio: q95.relativeToConditionalMean
      / q05.relativeToConditionalMean,
    timeline,
    poissonTailTolerance,
    maximumAccumulatedPoissonTailBound,
    maximumStochasticResidual,
    maximumProbabilityComplementResidual,
    maximumQuantileProbabilityResidual,
    monotonicArrivalPassed,
    identitiesPassed,
    exactStatesChanged: false,
    edgeTopologyChanged: false,
    trajectoryEnsembleSampled: false,
    rateUncertaintyPropagated: false,
    targetUsed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "The phase-type curve and quantiles are deterministic segmented-uniformization solutions for successful paths in the finite observed fixed-rate graph. They are not sampled trajectories, barrier/rate uncertainty, confidence intervals, a mechanism-complete first-passage distribution, or a bulk solid-growth time law.",
  };
}
