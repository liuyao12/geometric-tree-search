import { buildFiniteNetworkFirstPassage }
  from "./finite-network-first-passage.mjs?v=20260901-434";

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-passage-control-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    causalMechanismClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Rate-control elasticities differentiate the finite observed-network calculation while exact states, edges, and geometry remain fixed. They describe model sensitivity, not experimental causality, mechanism completeness, or a guarantee that changing one physical barrier leaves all others unchanged.",
  };
}

function perturbedNetwork(network, edgeKey, delta) {
  return { ...network, directedEdges: network.directedEdges.map((edge) => edge.key === edgeKey
    ? { ...edge, logRatePerSecond: edge.logRatePerSecond + delta } : { ...edge }) };
}

function derivative(plus, minus, step) {
  return (plus - minus) / (2 * step);
}

export function buildFiniteNetworkPassageControl(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
  logarithmicRateStep = 1e-4,
} = {}) {
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  const step = Number(logarithmicRateStep);
  if (!(step >= 1e-6 && step <= 1e-2)) {
    return unavailable("The central log-rate sensitivity step must lie between 1e-6 and 1e-2.");
  }
  const nominal = buildFiniteNetworkFirstPassage(network,
    { sourceStateSha256, targetStateSha256 });
  if (!nominal.available) return unavailable(nominal.reason, { nominal });
  if (!(nominal.sourceTargetHittingProbability > 0)
      || !Number.isFinite(nominal.sourceConditionalMeanFirstPassageLogSeconds)
      || !(nominal.sourceConditionalExpectedObservedJumps > 0)) {
    return unavailable("The selected source needs nonzero target reachability and finite conditional passage observables.",
      { nominal });
  }
  const sensitivities = [];
  for (const edge of [...edges].sort((first, second) => first.key.localeCompare(second.key))) {
    const plus = buildFiniteNetworkFirstPassage(perturbedNetwork(network, edge.key, step),
      { sourceStateSha256, targetStateSha256 });
    const minus = buildFiniteNetworkFirstPassage(perturbedNetwork(network, edge.key, -step),
      { sourceStateSha256, targetStateSha256 });
    if (!plus.available || !minus.available
        || !Number.isFinite(plus.sourceConditionalMeanFirstPassageLogSeconds)
        || !Number.isFinite(minus.sourceConditionalMeanFirstPassageLogSeconds)
        || !(plus.sourceConditionalExpectedObservedJumps > 0)
        || !(minus.sourceConditionalExpectedObservedJumps > 0)) {
      return unavailable(`Edge ${edge.key} could not be differentiated without changing finite-catalog solvability.`);
    }
    const targetProbabilityElasticity = derivative(plus.sourceTargetHittingProbability,
      minus.sourceTargetHittingProbability, step);
    const logPassageTimeElasticity = derivative(
      plus.sourceConditionalMeanFirstPassageLogSeconds,
      minus.sourceConditionalMeanFirstPassageLogSeconds, step);
    const logExpectedJumpsElasticity = derivative(
      Math.log(plus.sourceConditionalExpectedObservedJumps),
      Math.log(minus.sourceConditionalExpectedObservedJumps), step);
    const logRateUncertainty = Number.isFinite(edge.logRateUncertainty)
      ? edge.logRateUncertainty : null;
    const geometry = edge.geometricPathObservable || null;
    sensitivities.push({
      edgeKey: edge.key,
      fromStateSha256: edge.fromStateSha256,
      toStateSha256: edge.toStateSha256,
      eventDirection: edge.eventDirection,
      initialAtomCount: edge.initialAtomCount,
      finalAtomCount: edge.finalAtomCount,
      atomCountDelta: Number.isInteger(edge.initialAtomCount) && Number.isInteger(edge.finalAtomCount)
        ? edge.finalAtomCount - edge.initialAtomCount : null,
      logRatePerSecond: edge.logRatePerSecond,
      logRateUncertainty,
      targetProbabilityElasticity,
      logPassageTimeElasticity,
      logExpectedJumpsElasticity,
      oneSigmaLogPassageTimeContribution: logRateUncertainty == null ? null
        : logPassageTimeElasticity * logRateUncertainty,
      oneSigmaTargetProbabilityContribution: logRateUncertainty == null ? null
        : targetProbabilityElasticity * logRateUncertainty,
      geometricCharacter: geometry?.geometricCharacter || null,
      contactReach: geometry?.contactReach ?? null,
      netContactDelta: geometry?.netContactDelta ?? null,
      meanDynamicCoordinationDelta: geometry?.meanDynamicCoordinationDelta ?? null,
      maximumAdjacentDisplacementAngstrom: geometry?.maximumAdjacentDisplacementAngstrom ?? null,
      increasesRateWould: logPassageTimeElasticity < -1e-9
        ? "shorten conditional passage" : logPassageTimeElasticity > 1e-9
          ? "lengthen conditional passage" : "leave conditional passage locally unchanged",
    });
  }
  const ranked = [...sensitivities].sort((first, second) =>
    Math.abs(second.logPassageTimeElasticity) - Math.abs(first.logPassageTimeElasticity)
      || Math.abs(second.targetProbabilityElasticity) - Math.abs(first.targetProbabilityElasticity)
      || first.edgeKey.localeCompare(second.edgeKey));
  const sum = (field) => sensitivities.reduce((total, edge) => total + edge[field], 0);
  const commonModeTargetProbabilityDerivative = sum("targetProbabilityElasticity");
  const commonModeLogPassageTimeDerivative = sum("logPassageTimeElasticity");
  const commonModeLogExpectedJumpsDerivative = sum("logExpectedJumpsElasticity");
  const uncertaintyResolved = sensitivities.filter((edge) =>
    Number.isFinite(edge.logRateUncertainty));
  const independentLinearizedLogTimeSigma = uncertaintyResolved.length === sensitivities.length
    ? Math.sqrt(sensitivities.reduce((total, edge) => total
      + edge.oneSigmaLogPassageTimeContribution ** 2, 0)) : null;
  return {
    schema: "gcts-finite-network-passage-control-v1",
    available: true,
    model: "central finite-difference elasticities of finite-catalog target passage",
    sourceStateSha256,
    targetStateSha256,
    logarithmicRateStep: step,
    stateCount: network.nodes.length,
    directedEdgeCount: sensitivities.length,
    geometryResolvedEdgeCount: sensitivities.filter((edge) => edge.geometricCharacter).length,
    uncertaintyResolvedEdgeCount: uncertaintyResolved.length,
    nominal: {
      sourceTargetHittingProbability: nominal.sourceTargetHittingProbability,
      sourceConditionalMeanFirstPassageLogSeconds:
        nominal.sourceConditionalMeanFirstPassageLogSeconds,
      sourceConditionalExpectedObservedJumps: nominal.sourceConditionalExpectedObservedJumps,
    },
    edgeSensitivities: sensitivities,
    rankedByConditionalTimeControl: ranked,
    dominantConditionalTimeControlEdge: ranked[0] || null,
    commonModeTargetProbabilityDerivative,
    commonModeLogPassageTimeDerivative,
    commonModeLogExpectedJumpsDerivative,
    commonModeIdentitiesPassed: Math.abs(commonModeTargetProbabilityDerivative) <= 1e-7
      && Math.abs(commonModeLogPassageTimeDerivative + 1) <= 1e-7
      && Math.abs(commonModeLogExpectedJumpsDerivative) <= 1e-7,
    independentLinearizedLogTimeSigma,
    exactStatesChanged: false,
    edgeTopologyChanged: false,
    geometryChanged: false,
    targetUsed: false,
    causalMechanismClaimed: false,
    independentEdgePerturbationPhysicallyRealizableClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Each elasticity is a symmetric derivative with respect to one observed directed log rate, holding every exact state, other rate, and path geometry fixed. Common-mode identities require target probability and expected jump count to be rate-scale invariant and passage time to scale as k^-1. The ranking is finite-catalog model sensitivity, not causal proof, a reaction coordinate, or a guarantee that one physical barrier can vary independently.",
  };
}
