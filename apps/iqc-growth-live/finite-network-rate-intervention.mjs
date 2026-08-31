import { buildFiniteNetworkFirstPassage }
  from "./finite-network-first-passage.mjs?v=20260831-388";
import { buildFiniteNetworkPassageControl }
  from "./finite-network-passage-control.mjs?v=20260831-388";

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-rate-intervention-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    networkMutated: false,
    physicalInterventionClaimed: false,
    causalMechanismClaimed: false,
    claimBoundary: "A virtual intervention changes one supplied observed-edge rate inside a copied finite catalog and resolves the complete backward equation. It is a nonlinear model what-if, not a physical perturbation, causal intervention, barrier prediction, or claim that one experimental control changes only that rate.",
  };
}

function networkWithRateMultiplier(network, edgeKey, multiplier) {
  const logarithmicShift = Math.log(multiplier);
  return {
    ...network,
    directedEdges: network.directedEdges.map((edge) => edge.key === edgeKey
      ? { ...edge, logRatePerSecond: edge.logRatePerSecond + logarithmicShift }
      : { ...edge }),
  };
}

function finiteRatio(logNumerator, logDenominator) {
  const difference = logNumerator - logDenominator;
  return Number.isFinite(difference) && difference >= -745 && difference <= 709
    ? Math.exp(difference) : null;
}

export function buildFiniteNetworkRateIntervention(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
  edgeKey = null,
  rateMultiplier = 2,
  responseMultipliers = [.25, .5, 1, 2, 4],
} = {}) {
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  const edge = edges.find((candidate) => candidate.key === edgeKey);
  if (!edge) return unavailable("Choose one observed directed edge for the virtual intervention.");
  const multiplier = Number(rateMultiplier);
  if (!(multiplier >= .05 && multiplier <= 20)) {
    return unavailable("The virtual rate multiplier must lie between 0.05× and 20×.");
  }
  const factors = [...new Set((Array.isArray(responseMultipliers) ? responseMultipliers : [])
    .map(Number).filter((value) => value >= .05 && value <= 20))].sort((a, b) => a - b);
  if (!factors.includes(1)) factors.push(1);
  if (!factors.includes(multiplier)) factors.push(multiplier);
  factors.sort((a, b) => a - b);
  const nominal = buildFiniteNetworkFirstPassage(network,
    { sourceStateSha256, targetStateSha256 });
  if (!nominal.available || !(nominal.sourceTargetHittingProbability > 0)
      || !Number.isFinite(nominal.sourceConditionalMeanFirstPassageLogSeconds)) {
    return unavailable(nominal.reason || "A finite nominal source-to-target passage is required.",
      { nominal });
  }
  const control = buildFiniteNetworkPassageControl(network,
    { sourceStateSha256, targetStateSha256 });
  if (!control.available) return unavailable(control.reason, { nominal, control });
  const sensitivity = control.edgeSensitivities.find((candidate) => candidate.edgeKey === edgeKey);
  if (!sensitivity) return unavailable("The selected edge has no finite local control derivative.");
  const responses = [];
  for (const factor of factors) {
    const solved = buildFiniteNetworkFirstPassage(
      networkWithRateMultiplier(network, edgeKey, factor),
      { sourceStateSha256, targetStateSha256 });
    if (!solved.available || !Number.isFinite(solved.sourceConditionalMeanFirstPassageLogSeconds)) {
      return unavailable(`The ${factor}× intervention makes the finite-catalog passage unsolvable.`);
    }
    const logarithmicFactor = Math.log(factor);
    const exactLogPassageTimeChange = solved.sourceConditionalMeanFirstPassageLogSeconds
      - nominal.sourceConditionalMeanFirstPassageLogSeconds;
    const exactConditionalPassageTimeRatio = finiteRatio(
      solved.sourceConditionalMeanFirstPassageLogSeconds,
      nominal.sourceConditionalMeanFirstPassageLogSeconds);
    responses.push({
      rateMultiplier: factor,
      logarithmicRateChange: logarithmicFactor,
      targetHittingProbability: solved.sourceTargetHittingProbability,
      targetHittingProbabilityChange: solved.sourceTargetHittingProbability
        - nominal.sourceTargetHittingProbability,
      conditionalMeanFirstPassageLogSeconds: solved.sourceConditionalMeanFirstPassageLogSeconds,
      exactLogPassageTimeChange,
      exactConditionalPassageTimeRatio,
      conditionalExpectedObservedJumps: solved.sourceConditionalExpectedObservedJumps,
      exactExpectedJumpRatio: solved.sourceConditionalExpectedObservedJumps
        / nominal.sourceConditionalExpectedObservedJumps,
      localLinearTargetProbabilityChange: sensitivity.targetProbabilityElasticity
        * logarithmicFactor,
      localLinearLogPassageTimeChange: sensitivity.logPassageTimeElasticity
        * logarithmicFactor,
      localLinearPassageTimeRatio: Math.exp(sensitivity.logPassageTimeElasticity
        * logarithmicFactor),
      nonlinearLogTimeDepartureFromLocalTangent: exactLogPassageTimeChange
        - sensitivity.logPassageTimeElasticity * logarithmicFactor,
    });
  }
  const selectedResponse = responses.find((response) => response.rateMultiplier === multiplier);
  const geometry = edge.geometricPathObservable || null;
  return {
    schema: "gcts-finite-network-rate-intervention-v1",
    available: true,
    model: "exact finite-catalog backward-equation response to one copied edge-rate multiplier",
    sourceStateSha256,
    targetStateSha256,
    edgeKey,
    fromStateSha256: edge.fromStateSha256,
    toStateSha256: edge.toStateSha256,
    eventDirection: edge.eventDirection,
    nominalLogRatePerSecond: edge.logRatePerSecond,
    rateMultiplier: multiplier,
    responseMultipliers: factors,
    responses,
    selectedResponse,
    localElasticity: sensitivity,
    geometricCharacter: geometry?.geometricCharacter || null,
    contactReach: geometry?.contactReach ?? null,
    netContactDelta: geometry?.netContactDelta ?? null,
    meanDynamicCoordinationDelta: geometry?.meanDynamicCoordinationDelta ?? null,
    maximumAdjacentDisplacementAngstrom: geometry?.maximumAdjacentDisplacementAngstrom ?? null,
    exactStatesChanged: false,
    edgeTopologyChanged: false,
    geometryChanged: false,
    otherRatesChanged: false,
    networkMutated: false,
    targetUsed: false,
    physicalInterventionClaimed: false,
    causalMechanismClaimed: false,
    claimBoundary: "The selected observed rate is multiplied only in a copied finite-state calculation. Every exact state, edge, other rate, and path geometry is frozen. The exact nonlinear response can falsify the local tangent over a finite factor, but it neither identifies a realizable physical control nor accounts for unobserved mechanisms, correlated barrier changes, relaxation, or feedback of geometry on rates.",
  };
}
