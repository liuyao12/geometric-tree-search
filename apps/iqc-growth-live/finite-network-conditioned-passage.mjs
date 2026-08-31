import { buildFiniteNetworkFirstPassage }
  from "./finite-network-first-passage.mjs?v=20260831-397";

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-conditioned-passage-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    trajectoryEnsembleSampled: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Successful-passage residence and traversal expectations are exact only inside the finite observed directed-rate catalog and condition on reaching the selected target. They are not sampled trajectories, a complete transition-path ensemble, an unconditioned kinetic history, or proof that missing states and exits are absent.",
  };
}

function solveLinearSystem(matrix, rightHandSide, tolerance = 1e-12) {
  const size = rightHandSide.length;
  const augmented = matrix.map((row, index) => [...row, rightHandSide[index]]);
  for (let column = 0; column < size; column += 1) {
    let pivot = column;
    for (let row = column + 1; row < size; row += 1) {
      if (Math.abs(augmented[row][column]) > Math.abs(augmented[pivot][column])) pivot = row;
    }
    if (Math.abs(augmented[pivot][column]) <= tolerance) {
      throw new Error("conditioned residence linear system is singular");
    }
    [augmented[column], augmented[pivot]] = [augmented[pivot], augmented[column]];
    const divisor = augmented[column][column];
    for (let entry = column; entry <= size; entry += 1) augmented[column][entry] /= divisor;
    for (let row = 0; row < size; row += 1) {
      if (row === column) continue;
      const factor = augmented[row][column];
      if (Math.abs(factor) <= tolerance) continue;
      for (let entry = column; entry <= size; entry += 1) {
        augmented[row][entry] -= factor * augmented[column][entry];
      }
    }
  }
  return augmented.map((row) => row[size]);
}

function physicalValueFromLog(logValue) {
  return Number.isFinite(logValue) && logValue >= -745 && logValue <= 709
    ? Math.exp(logValue) : null;
}

function consistentStateAtomCounts(nodes, edges) {
  const counts = new Map();
  let consistent = true;
  const assign = (state, value) => {
    if (!Number.isInteger(value) || value < 0) { consistent = false; return; }
    if (counts.has(state) && counts.get(state) !== value) consistent = false;
    counts.set(state, value);
  };
  edges.forEach((edge) => {
    assign(edge.fromStateSha256, edge.initialAtomCount);
    assign(edge.toStateSha256, edge.finalAtomCount);
  });
  if (nodes.some((node) => !counts.has(node.stateSha256))) consistent = false;
  return { counts, consistent };
}

export function buildFiniteNetworkConditionedPassage(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
} = {}) {
  const nodes = Array.isArray(network?.nodes) ? network.nodes : [];
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  const firstPassage = buildFiniteNetworkFirstPassage(network,
    { sourceStateSha256, targetStateSha256 });
  if (!firstPassage.available || !(firstPassage.sourceTargetHittingProbability > 0)
      || !Number.isFinite(firstPassage.sourceConditionalMeanFirstPassageLogSeconds)) {
    return unavailable(firstPassage.reason
      || "The selected source needs a finite nonzero target-conditioned passage.",
    { firstPassage });
  }
  const hitting = new Map(firstPassage.states.map((state) =>
    [state.stateSha256, state.targetHittingProbability]));
  const transient = nodes.filter((node) => node.stateSha256 !== targetStateSha256
    && (hitting.get(node.stateSha256) || 0) > 1e-14);
  const transientIndex = new Map(transient.map((node, index) => [node.stateSha256, index]));
  if (!transientIndex.has(sourceStateSha256)) {
    return unavailable("The selected source is not a positive-probability transient state.");
  }
  const maximumLogRatePerSecond = Math.max(...edges.map((edge) => edge.logRatePerSecond));
  const transformedEdges = edges.map((edge) => {
    const sourceProbability = hitting.get(edge.fromStateSha256) || 0;
    const destinationProbability = hitting.get(edge.toStateSha256) || 0;
    const scaledRate = Math.exp(edge.logRatePerSecond - maximumLogRatePerSecond);
    const conditionedScaledRate = sourceProbability > 0 && destinationProbability > 0
      && edge.fromStateSha256 !== targetStateSha256
      ? scaledRate * destinationProbability / sourceProbability : 0;
    return { ...edge, scaledRate, conditionedScaledRate };
  });
  const matrix = Array.from({ length: transient.length }, () =>
    Array(transient.length).fill(0));
  transformedEdges.forEach((edge) => {
    const row = transientIndex.get(edge.fromStateSha256);
    if (row == null || !(edge.conditionedScaledRate > 0)) return;
    matrix[row][row] += edge.conditionedScaledRate;
    const column = transientIndex.get(edge.toStateSha256);
    if (column != null) matrix[row][column] -= edge.conditionedScaledRate;
  });
  const transpose = matrix.map((_, row) => matrix.map((matrixRow) => matrixRow[row]));
  const sourceVector = transient.map((node) =>
    node.stateSha256 === sourceStateSha256 ? 1 : 0);
  let scaledResidence;
  try {
    scaledResidence = solveLinearSystem(transpose, sourceVector);
  } catch (error) {
    return unavailable(error.message, { firstPassage });
  }
  const totalScaledResidence = scaledResidence.reduce((sum, value) => sum + value, 0);
  const stateId = new Map(nodes.map((node) => [node.stateSha256, node.stateId]));
  const edgeTraversals = transformedEdges.map((edge) => {
    const sourceIndex = transientIndex.get(edge.fromStateSha256);
    const expectedTraversalCount = sourceIndex == null ? 0
      : scaledResidence[sourceIndex] * edge.conditionedScaledRate;
    const geometry = edge.geometricPathObservable || null;
    return {
      edgeKey: edge.key,
      fromStateSha256: edge.fromStateSha256,
      toStateSha256: edge.toStateSha256,
      fromStateId: stateId.get(edge.fromStateSha256),
      toStateId: stateId.get(edge.toStateSha256),
      eventDirection: edge.eventDirection,
      expectedTraversalCount,
      traversalFractionOfExpectedJumps: expectedTraversalCount
        / firstPassage.sourceConditionalExpectedObservedJumps,
      initialAtomCount: edge.initialAtomCount,
      finalAtomCount: edge.finalAtomCount,
      atomCountDelta: Number.isInteger(edge.initialAtomCount)
        && Number.isInteger(edge.finalAtomCount)
        ? edge.finalAtomCount - edge.initialAtomCount : null,
      geometricCharacter: geometry?.geometricCharacter || null,
      netContactDelta: geometry?.netContactDelta ?? null,
      meanDynamicCoordinationDelta: geometry?.meanDynamicCoordinationDelta ?? null,
      maximumAdjacentDisplacementAngstrom:
        geometry?.maximumAdjacentDisplacementAngstrom ?? null,
    };
  });
  const inflow = new Map(transient.map((node) => [node.stateSha256, 0]));
  const outflow = new Map(transient.map((node) => [node.stateSha256, 0]));
  edgeTraversals.forEach((edge) => {
    if (inflow.has(edge.toStateSha256)) inflow.set(edge.toStateSha256,
      inflow.get(edge.toStateSha256) + edge.expectedTraversalCount);
    if (outflow.has(edge.fromStateSha256)) outflow.set(edge.fromStateSha256,
      outflow.get(edge.fromStateSha256) + edge.expectedTraversalCount);
  });
  const stateResidence = transient.map((node, index) => {
    const scaled = scaledResidence[index];
    const logSeconds = scaled > 0 ? Math.log(scaled) - maximumLogRatePerSecond : null;
    const expectedArrivals = inflow.get(node.stateSha256)
      + (node.stateSha256 === sourceStateSha256 ? 1 : 0);
    const expectedDepartures = outflow.get(node.stateSha256);
    return {
      stateId: node.stateId,
      stateSha256: node.stateSha256,
      expectedScaledResidence: scaled,
      expectedResidenceLogSeconds: logSeconds,
      expectedResidenceSeconds: physicalValueFromLog(logSeconds),
      fractionOfConditionalPassageTime: scaled / totalScaledResidence,
      expectedArrivals,
      expectedDepartures,
      flowConservationResidual: expectedArrivals - expectedDepartures,
    };
  });
  const expectedTotalTraversals = edgeTraversals.reduce((sum, edge) =>
    sum + edge.expectedTraversalCount, 0);
  const expectedTargetEntries = edgeTraversals.filter((edge) =>
    edge.toStateSha256 === targetStateSha256).reduce((sum, edge) =>
    sum + edge.expectedTraversalCount, 0);
  const maximumFlowConservationResidual = Math.max(0, ...stateResidence.map((state) =>
    Math.abs(state.flowConservationResidual)));
  const residenceIdentityResidual = totalScaledResidence
    - firstPassage.sourceConditionalMeanFirstPassageScaledTime;
  const jumpIdentityResidual = expectedTotalTraversals
    - firstPassage.sourceConditionalExpectedObservedJumps;
  const atomCounts = consistentStateAtomCounts(nodes, edges);
  const expectedCumulativeAtomCountDelta = edgeTraversals.every((edge) =>
    edge.atomCountDelta != null) ? edgeTraversals.reduce((sum, edge) =>
      sum + edge.expectedTraversalCount * edge.atomCountDelta, 0) : null;
  const endpointAtomCountDelta = atomCounts.consistent
    ? atomCounts.counts.get(targetStateSha256) - atomCounts.counts.get(sourceStateSha256) : null;
  const atomCountTelescopingResidual = expectedCumulativeAtomCountDelta == null
    || endpointAtomCountDelta == null ? null
    : expectedCumulativeAtomCountDelta - endpointAtomCountDelta;
  const positiveTraversal = edgeTraversals.filter((edge) => edge.expectedTraversalCount > 1e-14);
  const geometryResolvedExpectedTraversals = positiveTraversal.filter((edge) =>
    edge.geometricCharacter).reduce((sum, edge) => sum + edge.expectedTraversalCount, 0);
  const expectedTraversalCountByGeometricCharacter = Object.fromEntries([...new Set(
    positiveTraversal.map((edge) => edge.geometricCharacter || "geometry unresolved"))]
    .sort().map((character) => [character, positiveTraversal.filter((edge) =>
      (edge.geometricCharacter || "geometry unresolved") === character)
      .reduce((sum, edge) => sum + edge.expectedTraversalCount, 0)]));
  const completeGeometry = positiveTraversal.every((edge) => edge.geometricCharacter
    && Number.isFinite(edge.netContactDelta)
    && Number.isFinite(edge.meanDynamicCoordinationDelta)
    && Number.isFinite(edge.maximumAdjacentDisplacementAngstrom));
  const expectedCumulativeNetContactDelta = completeGeometry
    ? positiveTraversal.reduce((sum, edge) => sum
      + edge.expectedTraversalCount * edge.netContactDelta, 0) : null;
  const expectedCumulativeMeanDynamicCoordinationDelta = completeGeometry
    ? positiveTraversal.reduce((sum, edge) => sum
      + edge.expectedTraversalCount * edge.meanDynamicCoordinationDelta, 0) : null;
  const expectedCumulativeMaximumDisplacementExposureAngstrom = completeGeometry
    ? positiveTraversal.reduce((sum, edge) => sum
      + edge.expectedTraversalCount * edge.maximumAdjacentDisplacementAngstrom, 0) : null;
  const identitiesPassed = Math.max(Math.abs(residenceIdentityResidual),
    Math.abs(jumpIdentityResidual), Math.abs(expectedTargetEntries - 1),
    maximumFlowConservationResidual,
    atomCountTelescopingResidual == null ? 0 : Math.abs(atomCountTelescopingResidual)) <= 1e-8;
  return {
    schema: "gcts-finite-network-conditioned-passage-v1",
    available: true,
    model: "Doob-conditioned finite-state fundamental matrix with exact expected residence and edge traversals",
    sourceStateSha256,
    targetStateSha256,
    temperatureKelvin: firstPassage.temperatureKelvin,
    methodSettingsSha256: firstPassage.methodSettingsSha256,
    sourceTargetHittingProbability: firstPassage.sourceTargetHittingProbability,
    transientStateCount: transient.length,
    directedEdgeCount: edges.length,
    maximumLogRatePerSecond,
    stateResidence,
    rankedStateResidence: [...stateResidence].sort((first, second) =>
      second.fractionOfConditionalPassageTime - first.fractionOfConditionalPassageTime
      || first.stateId.localeCompare(second.stateId)),
    edgeTraversals,
    rankedEdgeTraversals: [...edgeTraversals].filter((edge) =>
      edge.expectedTraversalCount > 1e-14).sort((first, second) =>
      second.expectedTraversalCount - first.expectedTraversalCount
      || first.edgeKey.localeCompare(second.edgeKey)),
    expectedTotalTraversals,
    expectedTargetEntries,
    conditionalMeanFirstPassageLogSeconds:
      firstPassage.sourceConditionalMeanFirstPassageLogSeconds,
    conditionalMeanFirstPassageSeconds:
      firstPassage.sourceConditionalMeanFirstPassageSeconds,
    expectedCumulativeAtomCountDelta,
    endpointAtomCountDelta,
    atomCountTelescopingResidual,
    atomCountEvidenceConsistent: atomCounts.consistent,
    geometryResolvedExpectedTraversals,
    geometryResolvedTraversalFraction: expectedTotalTraversals > 0
      ? geometryResolvedExpectedTraversals / expectedTotalTraversals : 0,
    expectedTraversalCountByGeometricCharacter,
    expectedCumulativeNetContactDelta,
    expectedCumulativeMeanDynamicCoordinationDelta,
    expectedCumulativeMaximumDisplacementExposureAngstrom,
    residenceIdentityResidual,
    jumpIdentityResidual,
    targetAbsorptionIdentityResidual: expectedTargetEntries - 1,
    maximumFlowConservationResidual,
    identitiesPassed,
    exactStatesChanged: false,
    edgeTopologyChanged: false,
    trajectoryEnsembleSampled: false,
    targetUsed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "The fundamental matrix gives exact expected state residence and directed-edge traversal counts for successful source-to-target passages in the finite observed rate graph. Target-unreachable observed states enter through the conditioning probability. Missing states and exits remain unknown; these expectations are not sampled trajectories, an unconditioned history, a complete transition-path ensemble, or a macroscopic growth mechanism.",
  };
}
