import { buildFiniteNetworkFirstPassage }
  from "./finite-network-first-passage.mjs?v=20260901-410";

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-first-passage-uncertainty-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    confidenceIntervalClaimed: false,
    posteriorClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "The uncertainty ensemble perturbs only supplied finite-catalog log rates while exact states, edges, and geometry remain fixed. Independent Gaussian edge errors are an explicit diagnostic assumption. Quantile bands are not confidence or credible intervals, and omitted mechanisms are not sampled.",
  };
}

function isPrime(value) {
  if (value < 2) return false;
  for (let divisor = 2; divisor * divisor <= value; divisor += 1) {
    if (value % divisor === 0) return false;
  }
  return true;
}

function firstPrimes(count) {
  const primes = [];
  for (let candidate = 2; primes.length < count; candidate += 1) {
    if (isPrime(candidate)) primes.push(candidate);
  }
  return primes;
}

function radicalInverse(index, base) {
  let value = index;
  let fraction = 1 / base;
  let result = 0;
  while (value > 0) {
    result += fraction * (value % base);
    value = Math.floor(value / base);
    fraction /= base;
  }
  return result;
}

// Acklam's inverse-normal approximation; inputs are clamped away from singular endpoints.
function inverseNormal(probability) {
  const p = Math.max(1e-12, Math.min(1 - 1e-12, probability));
  const a = [-39.69683028665376, 220.9460984245205, -275.9285104469687,
    138.357751867269, -30.66479806614716, 2.506628277459239];
  const b = [-54.47609879822406, 161.5858368580409, -155.6989798598866,
    66.80131188771972, -13.28068155288572];
  const c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838,
    -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996,
    3.754408661907416];
  const lower = 0.02425;
  if (p < lower) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
      / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p > 1 - lower) {
    const q = Math.sqrt(-2 * Math.log(1 - p));
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
      / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  const q = p - .5;
  const r = q * q;
  return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
    / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
}

function quantile(values, probability) {
  const ordered = [...values].filter(Number.isFinite).sort((first, second) => first - second);
  if (!ordered.length) return null;
  const position = (ordered.length - 1) * probability;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  return lower === upper ? ordered[lower]
    : ordered[lower] * (upper - position) + ordered[upper] * (position - lower);
}

function summary(values) {
  return {
    minimum: Math.min(...values),
    q05: quantile(values, .05),
    median: quantile(values, .5),
    q95: quantile(values, .95),
    maximum: Math.max(...values),
  };
}

export function buildFiniteNetworkFirstPassageUncertainty(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
  sampleCount = 64,
} = {}) {
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  const count = Number(sampleCount);
  if (!Number.isInteger(count) || count < 16 || count > 256 || count % 2) {
    return unavailable("The deterministic uncertainty ensemble needs an even 16–256 samples.");
  }
  const nominal = buildFiniteNetworkFirstPassage(network,
    { sourceStateSha256, targetStateSha256 });
  if (!nominal.available) return unavailable(nominal.reason, { nominal });
  if (!edges.length || edges.some((edge) => !Number.isFinite(edge.logRateUncertainty)
      || edge.logRateUncertainty < 0)) {
    return unavailable("Every retained directed edge needs a finite nonnegative one-sigma log-rate uncertainty.",
      { nominal, uncertaintyCompleteEdgeCount: edges.filter((edge) =>
        Number.isFinite(edge.logRateUncertainty) && edge.logRateUncertainty >= 0).length,
      directedEdgeCount: edges.length });
  }
  const orderedEdges = [...edges].sort((first, second) => first.key.localeCompare(second.key));
  const edgeDimension = new Map(orderedEdges.map((edge, index) => [edge.key, index]));
  const primes = firstPrimes(orderedEdges.length);
  const samples = [];
  for (let pair = 0; pair < count / 2; pair += 1) {
    const positive = orderedEdges.map((edge, dimension) => inverseNormal(
      radicalInverse(pair + 1, primes[dimension])));
    for (const sign of [1, -1]) {
      const perturbedNetwork = { ...network, directedEdges: edges.map((edge) => ({ ...edge,
        logRatePerSecond: edge.logRatePerSecond + sign * edge.logRateUncertainty
          * positive[edgeDimension.get(edge.key)] })) };
      const result = buildFiniteNetworkFirstPassage(perturbedNetwork,
        { sourceStateSha256, targetStateSha256 });
      if (!result.available || !Number.isFinite(result.sourceTargetHittingProbability)
          || !Number.isFinite(result.sourceConditionalMeanFirstPassageLogSeconds)
          || !Number.isFinite(result.sourceConditionalExpectedObservedJumps)) {
        return unavailable("A perturbed finite-rate realization could not be solved without changing topology.",
          { nominal, failedSampleOrdinal: samples.length });
      }
      samples.push({
        ordinal: samples.length,
        sourceTargetHittingProbability: result.sourceTargetHittingProbability,
        sourceConditionalMeanFirstPassageLogSeconds:
          result.sourceConditionalMeanFirstPassageLogSeconds,
        sourceConditionalExpectedObservedJumps: result.sourceConditionalExpectedObservedJumps,
        numericalIdentitiesPassed: result.numericalIdentitiesPassed,
      });
    }
  }
  const hitting = summary(samples.map((sample) => sample.sourceTargetHittingProbability));
  const logTime = summary(samples.map((sample) =>
    sample.sourceConditionalMeanFirstPassageLogSeconds));
  const jumps = summary(samples.map((sample) => sample.sourceConditionalExpectedObservedJumps));
  const probabilityThreshold = .5;
  const nominalHitting = nominal.sourceTargetHittingProbability;
  return {
    schema: "gcts-finite-network-first-passage-uncertainty-v1",
    available: true,
    model: "antithetic Halton Gaussian propagation of independent supplied edge log-rate uncertainties",
    sourceStateSha256,
    targetStateSha256,
    sampleCount: count,
    edgeCount: edges.length,
    uncertaintyCompleteEdgeCount: edges.length,
    uncertaintyAssumption: "independent Gaussian one-sigma errors in directed log rates",
    samplingDesign: "deterministic antithetic Halton sequence transformed to standard normal",
    samples,
    nominal: {
      sourceTargetHittingProbability: nominalHitting,
      sourceConditionalMeanFirstPassageLogSeconds:
        nominal.sourceConditionalMeanFirstPassageLogSeconds,
      sourceConditionalExpectedObservedJumps: nominal.sourceConditionalExpectedObservedJumps,
    },
    sourceTargetHittingProbability: hitting,
    sourceConditionalMeanFirstPassageLogSeconds: logTime,
    sourceConditionalMeanFirstPassageTimeRatioQ95ToQ05: Math.exp(logTime.q95 - logTime.q05),
    sourceConditionalExpectedObservedJumps: jumps,
    fractionAboveFiftyPercentTargetHit: samples.filter((sample) =>
      sample.sourceTargetHittingProbability > probabilityThreshold).length / count,
    fiftyPercentTargetHitConclusionRobust: hitting.q05 > probabilityThreshold
      || hitting.q95 < probabilityThreshold,
    nominalValuesInsideQ05Q95: nominalHitting >= hitting.q05 && nominalHitting <= hitting.q95
      && nominal.sourceConditionalMeanFirstPassageLogSeconds >= logTime.q05
      && nominal.sourceConditionalMeanFirstPassageLogSeconds <= logTime.q95,
    allSampleIdentitiesPassed: samples.every((sample) => sample.numericalIdentitiesPassed),
    exactStatesChanged: false,
    edgeTopologyChanged: false,
    candidateSelectionChanged: false,
    targetUsed: false,
    confidenceIntervalClaimed: false,
    posteriorClaimed: false,
    edgeUncertaintyCorrelationLearned: false,
    mechanismCatalogComplete: false,
    omittedMechanismsSampled: false,
    claimBoundary: "The ensemble propagates every supplied directed log-rate one-sigma value through the finite-catalog backward equations while exact states and edge topology remain frozen. Samples use an explicit independent-Gaussian edge assumption and deterministic antithetic Halton design. The 5–95% diagnostic quantiles are neither confidence nor credible intervals; shared systematic error, learned correlations, and omitted mechanisms are absent.",
  };
}
