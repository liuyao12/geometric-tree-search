const DEFAULT_HORIZON_MULTIPLIERS = Object.freeze([0, 0.1, 0.3, 1, 3, 10, 30]);

function finite(value) {
  return Number.isFinite(Number(value));
}

function unavailable(reason) {
  return {
    schema: "gcts-finite-network-population-dynamics-v1",
    available: false,
    reason,
    targetUsed: false,
    equilibriumClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Transient probabilities are propagated only on the exact directed states and rates already observed. Missing states and exits are treated as absent from this conditional calculation, not proven physically absent. This is not an equilibrium ensemble, a complete master equation, an MFPT, or a long-time growth law.",
  };
}

function multiplyRowVector(vector, matrix) {
  const result = Array(vector.length).fill(0);
  vector.forEach((value, row) => matrix[row].forEach((entry, column) => {
    result[column] += value * entry;
  }));
  return result;
}

function uniformizedDistribution(initial, transition, multiplier, tolerance = 1e-12) {
  if (multiplier === 0) return { probabilities: [...initial], poissonTerms: 1,
    truncatedTailProbability: 0 };
  let power = [...initial];
  let weight = Math.exp(-multiplier);
  let cumulativeWeight = weight;
  const probabilities = power.map((value) => weight * value);
  let term = 0;
  const maximumTerms = Math.max(200, Math.ceil(multiplier + 20 * Math.sqrt(multiplier + 1)));
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

function physicalSeconds(logUniformizationRatePerSecond, multiplier) {
  if (multiplier === 0) return 0;
  const logSeconds = Math.log(multiplier) - logUniformizationRatePerSecond;
  return logSeconds > 709 || logSeconds < -745 ? null : Math.exp(logSeconds);
}

function stateAtomCounts(nodes, edges) {
  const counts = new Map();
  const assign = (state, count) => {
    if (!Number.isInteger(count) || count < 0) return false;
    if (counts.has(state) && counts.get(state) !== count) return false;
    counts.set(state, count); return true;
  };
  for (const edge of edges) {
    if (!assign(edge.fromStateSha256, edge.initialAtomCount)
        || !assign(edge.toStateSha256, edge.finalAtomCount)) return null;
  }
  return nodes.every((node) => counts.has(node.stateSha256)) ? counts : null;
}

export function buildFiniteNetworkPopulationDynamics(network, {
  initialStateSha256 = null,
  horizonMultipliers = DEFAULT_HORIZON_MULTIPLIERS,
  poissonTailTolerance = 1e-12,
} = {}) {
  const nodes = Array.isArray(network?.nodes) ? network.nodes : [];
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  if (nodes.length < 2 || edges.length < 1) {
    return unavailable("At least two exact states and one finite-rate directed edge are required.");
  }
  if (edges.some((edge) => !finite(edge.logRatePerSecond))) {
    return unavailable("Every retained directed edge needs one finite method-bound rate.");
  }
  const temperatures = new Set(edges.map((edge) => Number(edge.temperatureKelvin)));
  const methods = new Set(edges.map((edge) => edge.methodSettingsSha256));
  if (temperatures.size !== 1 || [...temperatures].some((value) => !finite(value) || value <= 0)
      || methods.size !== 1 || [...methods].some((value) => typeof value !== "string" || !value)) {
    return unavailable("All retained rates must share one temperature and one barrier-method settings digest.");
  }
  const nodeIndex = new Map(nodes.map((node, index) => [node.stateSha256, index]));
  if (edges.some((edge) => !nodeIndex.has(edge.fromStateSha256)
      || !nodeIndex.has(edge.toStateSha256))) {
    return unavailable("Every directed edge must connect states retained in the exact-state graph.");
  }
  const atomCounts = stateAtomCounts(nodes, edges);
  if (!atomCounts) return unavailable("Exact atom counts are missing or inconsistent for one retained state.");
  const initialHash = nodeIndex.has(initialStateSha256)
    ? initialStateSha256 : nodes[0].stateSha256;
  const multipliers = [...new Set((Array.isArray(horizonMultipliers)
    ? horizonMultipliers : DEFAULT_HORIZON_MULTIPLIERS).map(Number))]
    .filter((value) => Number.isFinite(value) && value >= 0).sort((a, b) => a - b);
  if (!multipliers.length || multipliers.at(-1) > 100) {
    return unavailable("The dimensionless observed-network horizon must contain finite values from 0 through 100.");
  }

  const maximumLogRate = Math.max(...edges.map((edge) => Number(edge.logRatePerSecond)));
  const scaledRates = edges.map((edge) => ({ edge,
    rate: Math.exp(Number(edge.logRatePerSecond) - maximumLogRate) }));
  const scaledExitRates = Array(nodes.length).fill(0);
  scaledRates.forEach(({ edge, rate }) => {
    scaledExitRates[nodeIndex.get(edge.fromStateSha256)] += rate;
  });
  const maximumScaledExitRate = Math.max(...scaledExitRates);
  if (!(maximumScaledExitRate > 0)) return unavailable("No positive observed exit rate is available.");
  const logUniformizationRatePerSecond = maximumLogRate + Math.log(maximumScaledExitRate);
  const transition = Array.from({ length: nodes.length }, () => Array(nodes.length).fill(0));
  scaledRates.forEach(({ edge, rate }) => {
    const from = nodeIndex.get(edge.fromStateSha256);
    const to = nodeIndex.get(edge.toStateSha256);
    transition[from][to] += rate / maximumScaledExitRate;
  });
  transition.forEach((row, index) => {
    row[index] += 1 - scaledExitRates[index] / maximumScaledExitRate;
    const sum = row.reduce((total, value) => total + value, 0);
    if (Math.abs(sum - 1) > 1e-10 || row.some((value) => value < -1e-12)) {
      throw new Error("uniformized observed-network transition matrix is not stochastic");
    }
  });

  const initial = Array(nodes.length).fill(0);
  initial[nodeIndex.get(initialHash)] = 1;
  const initialAtomCount = atomCounts.get(initialHash);
  const timeline = multipliers.map((multiplier) => {
    const propagated = uniformizedDistribution(initial, transition, multiplier,
      poissonTailTolerance);
    const stateProbabilities = nodes.map((node, index) => ({
      stateId: node.stateId,
      stateSha256: node.stateSha256,
      shortHash: node.shortHash,
      atomCount: atomCounts.get(node.stateSha256),
      probability: propagated.probabilities[index],
    }));
    const expectedAtomCount = stateProbabilities.reduce((sum, state) =>
      sum + state.probability * state.atomCount, 0);
    const occupancyEntropyNat = -stateProbabilities.reduce((sum, state) =>
      state.probability > 0 ? sum + state.probability * Math.log(state.probability) : sum, 0);
    return {
      observedTimescaleMultiplier: multiplier,
      elapsedSeconds: physicalSeconds(logUniformizationRatePerSecond, multiplier),
      logElapsedSeconds: multiplier === 0 ? null
        : Math.log(multiplier) - logUniformizationRatePerSecond,
      stateProbabilities,
      expectedAtomCount,
      expectedAtomCountChange: expectedAtomCount - initialAtomCount,
      occupancyEntropyNat,
      mostProbableState: [...stateProbabilities].sort((first, second) =>
        second.probability - first.probability || first.stateId.localeCompare(second.stateId))[0],
      poissonTerms: propagated.poissonTerms,
      truncatedTailProbability: propagated.truncatedTailProbability,
    };
  });
  const observedDeadEndStateCount = scaledExitRates.filter((value) => value === 0).length;
  return {
    schema: "gcts-finite-network-population-dynamics-v1",
    available: true,
    model: "continuous-time Markov master equation by uniformization",
    conditioning: "latest exact committed observation per directed edge",
    initialStateSha256: initialHash,
    initialStateId: nodes[nodeIndex.get(initialHash)].stateId,
    initialAtomCount,
    temperatureKelvin: [...temperatures][0],
    methodSettingsSha256: [...methods][0],
    stateCount: nodes.length,
    directedEdgeCount: edges.length,
    observedDeadEndStateCount,
    logUniformizationRatePerSecond,
    characteristicObservedExitTimeSeconds: physicalSeconds(logUniformizationRatePerSecond, 1),
    horizonMultipliers: multipliers,
    timeline,
    probabilityConserved: timeline.every((sample) => Math.abs(sample.stateProbabilities.reduce(
      (sum, state) => sum + state.probability, 0) - 1) <= 1e-10),
    nonnegativeProbabilities: timeline.every((sample) =>
      sample.stateProbabilities.every((state) => state.probability >= -1e-12)),
    exactStateGeometryChanged: false,
    targetUsed: false,
    equilibriumClaimed: false,
    steadyStateInferred: false,
    mechanismCatalogComplete: false,
    missingExitRatesAssumedZeroForConditionalProjection: true,
    claimBoundary: "Uniformization solves the continuous-time master equation only on the latest exact directed edges already observed at one shared temperature and barrier method. Unobserved states and exits are assigned zero rate for this conditional projection, not asserted physically absent. Long-horizon convergence is not equilibrium, an MFPT, mechanism completeness, or a macroscopic growth law.",
  };
}
