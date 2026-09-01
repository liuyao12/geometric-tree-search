import { buildFiniteNetworkFirstPassage }
  from "./finite-network-first-passage.mjs?v=20260901-431";
import { buildFiniteNetworkConditionedPassage }
  from "./finite-network-conditioned-passage.mjs?v=20260901-431";

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-conditioned-heterogeneity-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    trajectoryEnsembleSampled: false,
    rateUncertaintyPropagated: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Path heterogeneity is exact only for successful passages through the finite observed directed-rate catalog. It is variability among paths at fixed supplied rates, not rate uncertainty, sampled trajectories, a complete transition-path ensemble, or evidence that missing states and exits are absent.",
  };
}

function solveLinearSystem(matrix, rightHandSide, tolerance = 1e-12) {
  const size = rightHandSide.length;
  if (!size) return [];
  const augmented = matrix.map((row, index) => [...row, rightHandSide[index]]);
  for (let column = 0; column < size; column += 1) {
    let pivot = column;
    for (let row = column + 1; row < size; row += 1) {
      if (Math.abs(augmented[row][column]) > Math.abs(augmented[pivot][column])) pivot = row;
    }
    if (Math.abs(augmented[pivot][column]) <= tolerance) {
      throw new Error("conditioned heterogeneity linear system is singular");
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

function maximumResidual(matrix, solution, rightHandSide) {
  return matrix.reduce((maximum, row, index) => Math.max(maximum, Math.abs(
    row.reduce((sum, value, column) => sum + value * solution[column], 0)
      - rightHandSide[index])), 0);
}

function physicalValueFromLog(logValue) {
  if (logValue === -Infinity) return 0;
  return Number.isFinite(logValue) && logValue >= -745 && logValue <= 709
    ? Math.exp(logValue) : null;
}

function nonnegative(value, tolerance = 1e-10) {
  return value < 0 && value >= -tolerance ? 0 : value;
}

function rewardMoment(name, edges, transitionMatrix, transientMatrix,
  transientIndex, sourceIndex, rewardOf) {
  const rewards = edges.map((edge) => edge.conditionedScaledRate > 0 ? rewardOf(edge) : 0);
  if (edges.some((edge, index) => edge.conditionedScaledRate > 0
      && !Number.isFinite(rewards[index]))) return null;
  const meanRight = transitionMatrix.map((rowEdges) => rowEdges.reduce((sum, item) =>
    sum + item.probability * rewards[item.edgeIndex], 0));
  const meanByState = solveLinearSystem(transientMatrix, meanRight);
  const secondRight = transitionMatrix.map((rowEdges) => rowEdges.reduce((sum, item) => {
    const reward = rewards[item.edgeIndex];
    const continuation = transientIndex.has(item.edge.toStateSha256)
      ? meanByState[transientIndex.get(item.edge.toStateSha256)] : 0;
    return sum + item.probability * (reward * reward + 2 * reward * continuation);
  }, 0));
  const secondByState = solveLinearSystem(transientMatrix, secondRight);
  const mean = meanByState[sourceIndex];
  const secondRawMoment = secondByState[sourceIndex];
  const variance = nonnegative(secondRawMoment - mean * mean);
  return {
    name,
    mean,
    secondRawMoment,
    variance,
    standardDeviation: Math.sqrt(Math.max(0, variance)),
    coefficientOfVariation: Math.abs(mean) > 1e-14
      ? Math.sqrt(Math.max(0, variance)) / Math.abs(mean) : null,
    meanEquationResidual: maximumResidual(transientMatrix, meanByState, meanRight),
    secondMomentEquationResidual:
      maximumResidual(transientMatrix, secondByState, secondRight),
  };
}

export function buildFiniteNetworkConditionedHeterogeneity(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
} = {}) {
  const nodes = Array.isArray(network?.nodes) ? network.nodes : [];
  const sourceEdges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  const firstPassage = buildFiniteNetworkFirstPassage(network,
    { sourceStateSha256, targetStateSha256 });
  const conditionedPassage = buildFiniteNetworkConditionedPassage(network,
    { sourceStateSha256, targetStateSha256 });
  if (!firstPassage.available || !conditionedPassage.available) {
    return unavailable(conditionedPassage.reason || firstPassage.reason
      || "A finite successful source-to-target passage is required.",
    { firstPassage, conditionedPassage });
  }
  const hitting = new Map(firstPassage.states.map((state) =>
    [state.stateSha256, state.targetHittingProbability]));
  const transient = nodes.filter((node) => node.stateSha256 !== targetStateSha256
    && (hitting.get(node.stateSha256) || 0) > 1e-14);
  const transientIndex = new Map(transient.map((node, index) => [node.stateSha256, index]));
  const sourceIndex = transientIndex.get(sourceStateSha256);
  if (sourceIndex == null) return unavailable("The source is not a positive-probability transient state.");
  const maximumLogRatePerSecond = firstPassage.maximumLogRatePerSecond;
  const edges = sourceEdges.map((edge, edgeIndex) => {
    const sourceProbability = hitting.get(edge.fromStateSha256) || 0;
    const destinationProbability = hitting.get(edge.toStateSha256) || 0;
    const scaledRate = Math.exp(edge.logRatePerSecond - maximumLogRatePerSecond);
    const conditionedScaledRate = sourceProbability > 0 && destinationProbability > 0
      && edge.fromStateSha256 !== targetStateSha256
      ? scaledRate * destinationProbability / sourceProbability : 0;
    return { ...edge, edgeIndex, scaledRate, conditionedScaledRate };
  });
  const transitionMatrix = transient.map((node) => {
    const outgoing = edges.filter((edge) => edge.fromStateSha256 === node.stateSha256
      && edge.conditionedScaledRate > 0);
    const exitRate = outgoing.reduce((sum, edge) => sum + edge.conditionedScaledRate, 0);
    return outgoing.map((edge) => ({ edge, edgeIndex: edge.edgeIndex,
      probability: edge.conditionedScaledRate / exitRate }));
  });
  if (transitionMatrix.some((row) => !row.length)) {
    return unavailable("Every conditioned transient state needs a positive outgoing rate.");
  }
  const embeddedMatrix = Array.from({ length: transient.length }, (_, row) => {
    const values = Array(transient.length).fill(0); values[row] = 1;
    transitionMatrix[row].forEach((item) => {
      const column = transientIndex.get(item.edge.toStateSha256);
      if (column != null) values[column] -= item.probability;
    });
    return values;
  });
  const rateMatrix = Array.from({ length: transient.length }, (_, row) => {
    const values = Array(transient.length).fill(0);
    transitionMatrix[row].forEach((item) => {
      values[row] += item.edge.conditionedScaledRate;
      const column = transientIndex.get(item.edge.toStateSha256);
      if (column != null) values[column] -= item.edge.conditionedScaledRate;
    });
    return values;
  });
  let scaledTimeMean;
  let scaledTimeSecondRawMoment;
  let jumpMoment;
  try {
    scaledTimeMean = solveLinearSystem(rateMatrix, Array(transient.length).fill(1));
    scaledTimeSecondRawMoment = solveLinearSystem(rateMatrix,
      scaledTimeMean.map((value) => 2 * value));
    jumpMoment = rewardMoment("observed jumps", edges, transitionMatrix, embeddedMatrix,
      transientIndex, sourceIndex, () => 1);
  } catch (error) {
    return unavailable(error.message, { firstPassage, conditionedPassage });
  }
  const sourceScaledTimeMean = scaledTimeMean[sourceIndex];
  const sourceScaledTimeSecondRawMoment = scaledTimeSecondRawMoment[sourceIndex];
  const sourceScaledTimeVariance = nonnegative(sourceScaledTimeSecondRawMoment
    - sourceScaledTimeMean * sourceScaledTimeMean);
  const sourceScaledTimeStandardDeviation = Math.sqrt(Math.max(0, sourceScaledTimeVariance));
  const sourcePassageTimeStandardDeviationLogSeconds = sourceScaledTimeStandardDeviation > 0
    ? Math.log(sourceScaledTimeStandardDeviation) - maximumLogRatePerSecond : -Infinity;
  const passageTime = {
    meanScaledTime: sourceScaledTimeMean,
    secondRawMomentScaledTimeSquared: sourceScaledTimeSecondRawMoment,
    varianceScaledTimeSquared: sourceScaledTimeVariance,
    standardDeviationScaledTime: sourceScaledTimeStandardDeviation,
    standardDeviationLogSeconds: sourcePassageTimeStandardDeviationLogSeconds,
    standardDeviationSeconds: physicalValueFromLog(sourcePassageTimeStandardDeviationLogSeconds),
    coefficientOfVariation: sourceScaledTimeMean > 0
      ? sourceScaledTimeStandardDeviation / sourceScaledTimeMean : null,
    meanEquationResidual: maximumResidual(rateMatrix, scaledTimeMean,
      Array(transient.length).fill(1)),
    secondMomentEquationResidual: maximumResidual(rateMatrix,
      scaledTimeSecondRawMoment, scaledTimeMean.map((value) => 2 * value)),
  };
  const geometryOf = (edge) => edge.geometricPathObservable || {};
  const rewardMoments = {
    observedJumps: jumpMoment,
    atomCountDelta: rewardMoment("atom-count change", edges, transitionMatrix,
      embeddedMatrix, transientIndex, sourceIndex, (edge) =>
        Number.isInteger(edge.initialAtomCount) && Number.isInteger(edge.finalAtomCount)
          ? edge.finalAtomCount - edge.initialAtomCount : null),
    netContactDelta: rewardMoment("net contact change", edges, transitionMatrix,
      embeddedMatrix, transientIndex, sourceIndex, (edge) =>
        geometryOf(edge).netContactDelta),
    meanDynamicCoordinationDelta: rewardMoment("dynamic coordination change", edges,
      transitionMatrix, embeddedMatrix, transientIndex, sourceIndex, (edge) =>
        geometryOf(edge).meanDynamicCoordinationDelta),
    maximumDisplacementExposureAngstrom: rewardMoment("maximum-displacement exposure",
      edges, transitionMatrix, embeddedMatrix, transientIndex, sourceIndex, (edge) =>
        geometryOf(edge).maximumAdjacentDisplacementAngstrom),
  };
  const expectedCount = new Map(conditionedPassage.edgeTraversals.map((edge) =>
    [edge.edgeKey, edge.expectedTraversalCount]));
  const stateId = new Map(nodes.map((node) => [node.stateSha256, node.stateId]));
  let edgeUse;
  try {
    edgeUse = edges.map((edge) => {
      if (!(edge.conditionedScaledRate > 0)) return {
        edgeKey: edge.key, fromStateSha256: edge.fromStateSha256,
        toStateSha256: edge.toStateSha256, fromStateId: stateId.get(edge.fromStateSha256),
        toStateId: stateId.get(edge.toStateSha256), eventDirection: edge.eventDirection,
        geometricCharacter: geometryOf(edge).geometricCharacter || null,
        probabilityEverUsed: 0, expectedTraversalCount: 0,
        expectedTraversalsConditionalOnUse: null,
      };
      const sourceRow = transientIndex.get(edge.fromStateSha256);
      const probability = transitionMatrix[sourceRow].find((item) =>
        item.edgeIndex === edge.edgeIndex)?.probability || 0;
      const edgeMatrix = embeddedMatrix.map((row) => [...row]);
      const destinationColumn = transientIndex.get(edge.toStateSha256);
      if (destinationColumn != null) edgeMatrix[sourceRow][destinationColumn] += probability;
      const right = Array(transient.length).fill(0); right[sourceRow] = probability;
      const useByState = solveLinearSystem(edgeMatrix, right);
      const probabilityEverUsed = Math.max(0, Math.min(1, useByState[sourceIndex]));
      const expectedTraversalCount = expectedCount.get(edge.key) || 0;
      return {
        edgeKey: edge.key,
        fromStateSha256: edge.fromStateSha256,
        toStateSha256: edge.toStateSha256,
        fromStateId: stateId.get(edge.fromStateSha256),
        toStateId: stateId.get(edge.toStateSha256),
        eventDirection: edge.eventDirection,
        geometricCharacter: geometryOf(edge).geometricCharacter || null,
        probabilityEverUsed,
        expectedTraversalCount,
        expectedTraversalsConditionalOnUse: probabilityEverUsed > 1e-14
          ? expectedTraversalCount / probabilityEverUsed : null,
        useProbabilityEquationResidual: maximumResidual(edgeMatrix, useByState, right),
      };
    });
  } catch (error) {
    return unavailable(error.message, { firstPassage, conditionedPassage });
  }
  const rankedEdgeUse = [...edgeUse].filter((edge) => edge.probabilityEverUsed > 1e-14)
    .sort((first, second) => second.probabilityEverUsed - first.probabilityEverUsed
      || second.expectedTraversalCount - first.expectedTraversalCount
      || first.edgeKey.localeCompare(second.edgeKey));
  const expectedJumps = jumpMoment.mean;
  const trafficWeights = edgeUse.filter((edge) => edge.expectedTraversalCount > 1e-14)
    .map((edge) => edge.expectedTraversalCount / expectedJumps);
  const trafficEntropyNats = -trafficWeights.reduce((sum, weight) =>
    sum + weight * Math.log(weight), 0);
  const effectiveTrafficEdgeCount = Math.exp(trafficEntropyNats);
  const optionalRecrossingEdges = rankedEdgeUse.filter((edge) =>
    edge.probabilityEverUsed < 1 - 1e-9
      && edge.expectedTraversalsConditionalOnUse > 1 + 1e-9);
  const momentResiduals = [passageTime.meanEquationResidual,
    passageTime.secondMomentEquationResidual,
    ...Object.values(rewardMoments).filter(Boolean).flatMap((moment) =>
      [moment.meanEquationResidual, moment.secondMomentEquationResidual]),
    ...edgeUse.map((edge) => edge.useProbabilityEquationResidual || 0)];
  const meanIdentityResiduals = [passageTime.meanScaledTime
    - firstPassage.sourceConditionalMeanFirstPassageScaledTime,
  jumpMoment.mean - conditionedPassage.expectedTotalTraversals];
  if (rewardMoments.atomCountDelta && conditionedPassage.expectedCumulativeAtomCountDelta != null) {
    meanIdentityResiduals.push(rewardMoments.atomCountDelta.mean
      - conditionedPassage.expectedCumulativeAtomCountDelta);
  }
  const maximumMomentEquationResidual = Math.max(0, ...momentResiduals.map(Math.abs));
  const maximumMeanIdentityResidual = Math.max(0, ...meanIdentityResiduals.map(Math.abs));
  const maximumUseProbabilityBoundResidual = Math.max(0, ...edgeUse.map((edge) =>
    Math.max(-edge.probabilityEverUsed,
      edge.probabilityEverUsed - 1,
      edge.probabilityEverUsed - edge.expectedTraversalCount)));
  const atomCountTelescopeVariancePassed = !conditionedPassage.atomCountEvidenceConsistent
    || !rewardMoments.atomCountDelta
    || rewardMoments.atomCountDelta.variance <= 1e-8;
  const identitiesPassed = maximumMomentEquationResidual <= 1e-8
    && maximumMeanIdentityResidual <= 1e-8
    && maximumUseProbabilityBoundResidual <= 1e-8
    && atomCountTelescopeVariancePassed;
  return {
    schema: "gcts-finite-network-conditioned-heterogeneity-v1",
    available: true,
    model: "Doob-conditioned continuous-time and embedded-chain exact first and second moments with edge hitting probabilities",
    sourceStateSha256,
    targetStateSha256,
    temperatureKelvin: firstPassage.temperatureKelvin,
    methodSettingsSha256: firstPassage.methodSettingsSha256,
    transientStateCount: transient.length,
    directedEdgeCount: edges.length,
    passageTime,
    rewardMoments,
    edgeUse,
    rankedEdgeUse,
    optionalRecrossingEdges,
    trafficEntropyNats,
    effectiveTrafficEdgeCount,
    maximumMomentEquationResidual,
    maximumMeanIdentityResidual,
    maximumUseProbabilityBoundResidual,
    atomCountTelescopeVariancePassed,
    identitiesPassed,
    conditionedPassage,
    exactStatesChanged: false,
    edgeTopologyChanged: false,
    trajectoryEnsembleSampled: false,
    rateUncertaintyPropagated: false,
    targetUsed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Second moments and edge-use probabilities are exact for successful source-to-target paths inside the finite observed fixed-rate graph. They separate path branching and recrossing from rate uncertainty, but do not sample trajectories, certify a complete mechanism catalog, include missing exits, or predict bulk growth fluctuations.",
  };
}
