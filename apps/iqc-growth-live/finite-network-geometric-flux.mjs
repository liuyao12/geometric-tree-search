function finite(value) {
  return Number.isFinite(Number(value));
}

function unavailable(reason) {
  return {
    schema: "gcts-finite-network-geometric-flux-v1",
    available: false,
    reason,
    targetUsed: false,
    equilibriumClaimed: false,
    steadyStateClaimed: false,
    claimBoundary: "Probability current and atom drift are instantaneous derivatives on one conditional finite observed-state generator. Unobserved states and exits remain unknown. The result is not a macroscopic interface velocity, steady state, equilibrium flux, mechanism-complete growth rate, or transport coefficient.",
  };
}

function undirectedKey(first, second) {
  return [first, second].sort().join("<->");
}

function populationClass(delta) {
  return delta > 0 ? "growth" : delta < 0 ? "shrinkage" : "count-preserving";
}

function physicalRate(valuePerObservedTimescale, logUniformizationRatePerSecond) {
  if (valuePerObservedTimescale === 0) return { valuePerSecond: 0, logAbsolutePerSecond: null };
  const sign = Math.sign(valuePerObservedTimescale);
  const logAbsolutePerSecond = Math.log(Math.abs(valuePerObservedTimescale))
    + logUniformizationRatePerSecond;
  return {
    valuePerSecond: logAbsolutePerSecond > 709 || logAbsolutePerSecond < -745
      ? null : sign * Math.exp(logAbsolutePerSecond),
    logAbsolutePerSecond,
  };
}

export function buildFiniteNetworkGeometricFlux(network, dynamics, {
  horizonMultiplier = 3,
} = {}) {
  if (!dynamics?.available) return unavailable(dynamics?.reason
    || "Finite-network population dynamics are unavailable.");
  const nodes = Array.isArray(network?.nodes) ? network.nodes : [];
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  const sample = dynamics.timeline?.reduce((best, candidate) =>
    Math.abs(candidate.observedTimescaleMultiplier - Number(horizonMultiplier))
      < Math.abs(best.observedTimescaleMultiplier - Number(horizonMultiplier))
      ? candidate : best, dynamics.timeline?.[0]);
  if (!sample || nodes.length !== sample.stateProbabilities.length) {
    return unavailable("The selected population sample does not match the exact-state graph.");
  }
  const probabilityByState = new Map(sample.stateProbabilities.map((state) =>
    [state.stateSha256, state.probability]));
  const atomCountByState = new Map(sample.stateProbabilities.map((state) =>
    [state.stateSha256, state.atomCount]));
  if (edges.some((edge) => !probabilityByState.has(edge.fromStateSha256)
      || !probabilityByState.has(edge.toStateSha256) || !finite(edge.logRatePerSecond))) {
    return unavailable("Every retained directed rate must connect a populated exact state.");
  }
  const nodeDerivative = new Map(nodes.map((node) => [node.stateSha256, 0]));
  const directedFluxes = edges.map((edge) => {
    const normalizedRate = Math.exp(Number(edge.logRatePerSecond)
      - dynamics.logUniformizationRatePerSecond);
    const sourceProbability = probabilityByState.get(edge.fromStateSha256);
    const probabilityTrafficPerObservedTimescale = sourceProbability * normalizedRate;
    const atomCountDelta = atomCountByState.get(edge.toStateSha256)
      - atomCountByState.get(edge.fromStateSha256);
    nodeDerivative.set(edge.fromStateSha256, nodeDerivative.get(edge.fromStateSha256)
      - probabilityTrafficPerObservedTimescale);
    nodeDerivative.set(edge.toStateSha256, nodeDerivative.get(edge.toStateSha256)
      + probabilityTrafficPerObservedTimescale);
    return {
      edgeKey: edge.key,
      eventId: edge.eventId,
      candidateId: edge.candidateId,
      eventDirection: edge.eventDirection,
      fromStateSha256: edge.fromStateSha256,
      toStateSha256: edge.toStateSha256,
      sourceProbability,
      normalizedRatePerObservedTimescale: normalizedRate,
      probabilityTrafficPerObservedTimescale,
      atomCountDelta,
      populationClass: populationClass(atomCountDelta),
      expectedAtomDriftContributionPerObservedTimescale:
        probabilityTrafficPerObservedTimescale * atomCountDelta,
    };
  });
  const byUndirected = new Map();
  directedFluxes.forEach((flux) => {
    const key = undirectedKey(flux.fromStateSha256, flux.toStateSha256);
    const records = byUndirected.get(key) || [];
    records.push(flux); byUndirected.set(key, records);
  });
  const netEdgeCurrents = [...byUndirected.entries()].sort(([first], [second]) =>
    first.localeCompare(second)).map(([key, records]) => {
    const [lowStateSha256, highStateSha256] = key.split("<->");
    const lowToHigh = records.find((record) => record.fromStateSha256 === lowStateSha256) || null;
    const highToLow = records.find((record) => record.fromStateSha256 === highStateSha256) || null;
    const lowToHighTraffic = lowToHigh?.probabilityTrafficPerObservedTimescale || 0;
    const highToLowTraffic = highToLow?.probabilityTrafficPerObservedTimescale || 0;
    const netProbabilityCurrentPerObservedTimescale = lowToHighTraffic - highToLowTraffic;
    const atomCountDeltaLowToHigh = atomCountByState.get(highStateSha256)
      - atomCountByState.get(lowStateSha256);
    return {
      key,
      lowStateSha256,
      highStateSha256,
      lowToHighEdgeKey: lowToHigh?.edgeKey || null,
      highToLowEdgeKey: highToLow?.edgeKey || null,
      bidirectionalObserved: Boolean(lowToHigh && highToLow),
      lowToHighTrafficPerObservedTimescale: lowToHighTraffic,
      highToLowTrafficPerObservedTimescale: highToLowTraffic,
      netProbabilityCurrentPerObservedTimescale,
      absoluteNetProbabilityCurrentPerObservedTimescale:
        Math.abs(netProbabilityCurrentPerObservedTimescale),
      atomCountDeltaLowToHigh,
      expectedAtomDriftContributionPerObservedTimescale:
        netProbabilityCurrentPerObservedTimescale * atomCountDeltaLowToHigh,
    };
  });
  const totalTransitionActivityPerObservedTimescale = directedFluxes.reduce((sum, flux) =>
    sum + flux.probabilityTrafficPerObservedTimescale, 0);
  const expectedAtomDriftPerObservedTimescale = directedFluxes.reduce((sum, flux) =>
    sum + flux.expectedAtomDriftContributionPerObservedTimescale, 0);
  const physicalDrift = physicalRate(expectedAtomDriftPerObservedTimescale,
    dynamics.logUniformizationRatePerSecond);
  const physicalActivity = physicalRate(totalTransitionActivityPerObservedTimescale,
    dynamics.logUniformizationRatePerSecond);
  const activityByPopulationClass = Object.fromEntries(["growth", "shrinkage", "count-preserving"]
    .map((kind) => [kind, directedFluxes.filter((flux) => flux.populationClass === kind)
      .reduce((sum, flux) => sum + flux.probabilityTrafficPerObservedTimescale, 0)]));
  const probabilityDerivativeResidualPerObservedTimescale = [...nodeDerivative.values()]
    .reduce((sum, value) => sum + value, 0);
  const expectedAtomDriftFromStateDerivativePerObservedTimescale = [...nodeDerivative.entries()]
    .reduce((sum, [state, derivative]) => sum + atomCountByState.get(state) * derivative, 0);
  const dominantCurrentEdge = [...netEdgeCurrents].sort((first, second) =>
    second.absoluteNetProbabilityCurrentPerObservedTimescale
      - first.absoluteNetProbabilityCurrentPerObservedTimescale || first.key.localeCompare(second.key))[0] || null;
  const dominantAtomDriftEdge = [...netEdgeCurrents].sort((first, second) =>
    Math.abs(second.expectedAtomDriftContributionPerObservedTimescale)
      - Math.abs(first.expectedAtomDriftContributionPerObservedTimescale)
      || first.key.localeCompare(second.key))[0] || null;
  return {
    schema: "gcts-finite-network-geometric-flux-v1",
    available: true,
    model: "instantaneous exact-edge probability current",
    initialStateSha256: dynamics.initialStateSha256,
    temperatureKelvin: dynamics.temperatureKelvin,
    methodSettingsSha256: dynamics.methodSettingsSha256,
    observedTimescaleMultiplier: sample.observedTimescaleMultiplier,
    elapsedSeconds: sample.elapsedSeconds,
    logElapsedSeconds: sample.logElapsedSeconds,
    directedFluxes,
    netEdgeCurrents,
    totalTransitionActivityPerObservedTimescale,
    expectedTransitionsPerSecond: physicalActivity.valuePerSecond,
    logExpectedTransitionsPerSecond: physicalActivity.logAbsolutePerSecond,
    expectedAtomDriftPerObservedTimescale,
    expectedAtomDriftPerSecond: physicalDrift.valuePerSecond,
    logAbsoluteExpectedAtomDriftPerSecond: physicalDrift.logAbsolutePerSecond,
    activityByPopulationClass,
    dominantCurrentEdge,
    dominantAtomDriftEdge,
    stateProbabilityDerivativesPerObservedTimescale: nodes.map((node) => ({
      stateId: node.stateId,
      stateSha256: node.stateSha256,
      derivative: nodeDerivative.get(node.stateSha256),
    })),
    probabilityConservationResidualPerObservedTimescale:
      probabilityDerivativeResidualPerObservedTimescale,
    expectedAtomDriftIdentityResidualPerObservedTimescale:
      expectedAtomDriftPerObservedTimescale
        - expectedAtomDriftFromStateDerivativePerObservedTimescale,
    probabilityCurrentAudited: true,
    exactStateGeometryChanged: false,
    targetUsed: false,
    equilibriumClaimed: false,
    steadyStateClaimed: false,
    macroscopicInterfaceVelocityClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Probability traffic p_i k_ij, antisymmetric edge current, and d<E[N]>/dt are evaluated only on the latest exact directed edges of the conditional observed-state generator. Unobserved states and exits remain unknown. Atom drift is not a macroscopic interface velocity, steady-state flux, equilibrium current, transport coefficient, or mechanism-complete growth rate.",
  };
}
