function finite(value) {
  return Number.isFinite(Number(value));
}

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-first-passage-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    equilibriumClaimed: false,
    completeCommittorClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "First-passage equations are solved only on the latest exact directed states and rates observed under one temperature and barrier method. A target-unreachable observed state is an explicit failure state inside this finite catalog. Unobserved exits are omitted, not certified absent; therefore the result is not a complete committor, mechanism-complete MFPT, or macroscopic growth time.",
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
      throw new Error("observed first-passage linear system is singular");
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

function physicalTime(logSeconds) {
  return Number.isFinite(logSeconds) && logSeconds >= -745 && logSeconds <= 709
    ? Math.exp(logSeconds) : null;
}

function reverseReachable(nodes, edges, targetStateSha256) {
  const incoming = new Map(nodes.map((node) => [node.stateSha256, []]));
  edges.forEach((edge) => incoming.get(edge.toStateSha256)?.push(edge.fromStateSha256));
  const reachable = new Set([targetStateSha256]);
  const queue = [targetStateSha256];
  while (queue.length) {
    const state = queue.shift();
    for (const predecessor of incoming.get(state) || []) {
      if (!reachable.has(predecessor)) {
        reachable.add(predecessor); queue.push(predecessor);
      }
    }
  }
  return reachable;
}

export function buildFiniteNetworkFirstPassage(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
} = {}) {
  const nodes = Array.isArray(network?.nodes) ? network.nodes : [];
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  if (nodes.length < 2 || edges.length < 1) {
    return unavailable("At least two exact states and one finite-rate directed edge are required.");
  }
  const nodeIndex = new Map(nodes.map((node, index) => [node.stateSha256, index]));
  if (!nodeIndex.has(sourceStateSha256) || !nodeIndex.has(targetStateSha256)
      || sourceStateSha256 === targetStateSha256) {
    return unavailable("Choose two distinct exact states as source and target.");
  }
  if (edges.some((edge) => !nodeIndex.has(edge.fromStateSha256)
      || !nodeIndex.has(edge.toStateSha256) || edge.fromStateSha256 === edge.toStateSha256
      || !finite(edge.logRatePerSecond))) {
    return unavailable("Every retained edge must connect two distinct exact states with a finite rate.");
  }
  const temperatures = new Set(edges.map((edge) => Number(edge.temperatureKelvin)));
  const methods = new Set(edges.map((edge) => edge.methodSettingsSha256));
  if (temperatures.size !== 1 || [...temperatures].some((value) => !(value > 0))
      || methods.size !== 1 || [...methods].some((value) => typeof value !== "string" || !value)) {
    return unavailable("All retained rates must share one temperature and one barrier-method settings digest.");
  }

  const maximumLogRatePerSecond = Math.max(...edges.map((edge) => Number(edge.logRatePerSecond)));
  const scaledEdges = edges.map((edge) => ({ ...edge,
    scaledRate: Math.exp(Number(edge.logRatePerSecond) - maximumLogRatePerSecond) }));
  const targetReachable = reverseReachable(nodes, scaledEdges, targetStateSha256);
  const failureStates = nodes.filter((node) => !targetReachable.has(node.stateSha256));
  const unknownStates = nodes.filter((node) => targetReachable.has(node.stateSha256)
    && node.stateSha256 !== targetStateSha256);
  const unknownIndex = new Map(unknownStates.map((node, index) => [node.stateSha256, index]));
  const outgoing = new Map(nodes.map((node) => [node.stateSha256, []]));
  scaledEdges.forEach((edge) => outgoing.get(edge.fromStateSha256)?.push(edge));

  const hittingMatrix = Array.from({ length: unknownStates.length }, () =>
    Array(unknownStates.length).fill(0));
  const hittingRight = Array(unknownStates.length).fill(0);
  unknownStates.forEach((node, row) => {
    const exits = outgoing.get(node.stateSha256) || [];
    const exitRate = exits.reduce((sum, edge) => sum + edge.scaledRate, 0);
    hittingMatrix[row][row] = exitRate;
    exits.forEach((edge) => {
      if (edge.toStateSha256 === targetStateSha256) hittingRight[row] += edge.scaledRate;
      else if (unknownIndex.has(edge.toStateSha256)) {
        hittingMatrix[row][unknownIndex.get(edge.toStateSha256)] -= edge.scaledRate;
      }
    });
  });
  let hittingSolution;
  try {
    hittingSolution = solveLinearSystem(hittingMatrix, hittingRight);
  } catch (error) {
    return unavailable(error.message, { targetReachableStateCount: targetReachable.size });
  }
  const hittingProbability = new Map(nodes.map((node) => [node.stateSha256,
    node.stateSha256 === targetStateSha256 ? 1
      : unknownIndex.has(node.stateSha256)
        ? Math.max(0, Math.min(1, hittingSolution[unknownIndex.get(node.stateSha256)])) : 0]));
  const positiveStates = unknownStates.filter((node) => hittingProbability.get(node.stateSha256) > 1e-14);
  const positiveIndex = new Map(positiveStates.map((node, index) => [node.stateSha256, index]));
  const timeMatrix = Array.from({ length: positiveStates.length }, () =>
    Array(positiveStates.length).fill(0));
  const timeRight = Array(positiveStates.length).fill(1);
  const jumpRight = Array(positiveStates.length).fill(0);
  positiveStates.forEach((node, row) => {
    const sourceProbability = hittingProbability.get(node.stateSha256);
    let transformedExitRate = 0;
    for (const edge of outgoing.get(node.stateSha256) || []) {
      const destinationProbability = hittingProbability.get(edge.toStateSha256) || 0;
      if (!(destinationProbability > 0)) continue;
      const transformedRate = edge.scaledRate * destinationProbability / sourceProbability;
      transformedExitRate += transformedRate;
      if (positiveIndex.has(edge.toStateSha256)) {
        timeMatrix[row][positiveIndex.get(edge.toStateSha256)] -= transformedRate;
      }
    }
    timeMatrix[row][row] += transformedExitRate;
    jumpRight[row] = transformedExitRate;
  });
  let conditionalScaledTime = [];
  let conditionalJumps = [];
  try {
    conditionalScaledTime = solveLinearSystem(timeMatrix, timeRight);
    conditionalJumps = solveLinearSystem(timeMatrix, jumpRight);
  } catch (error) {
    return unavailable(error.message, { targetReachableStateCount: targetReachable.size });
  }
  const timeByState = new Map(nodes.map((node) => [node.stateSha256,
    node.stateSha256 === targetStateSha256 ? 0 : positiveIndex.has(node.stateSha256)
      ? conditionalScaledTime[positiveIndex.get(node.stateSha256)] : null]));
  const jumpsByState = new Map(nodes.map((node) => [node.stateSha256,
    node.stateSha256 === targetStateSha256 ? 0 : positiveIndex.has(node.stateSha256)
      ? conditionalJumps[positiveIndex.get(node.stateSha256)] : null]));
  const sourceHittingProbability = hittingProbability.get(sourceStateSha256);
  const sourceScaledTime = timeByState.get(sourceStateSha256);
  const sourceLogTimeSeconds = Number.isFinite(sourceScaledTime) && sourceScaledTime > 0
    ? Math.log(sourceScaledTime) - maximumLogRatePerSecond : null;
  const states = nodes.map((node) => {
    const scaledTime = timeByState.get(node.stateSha256);
    const logTimeSeconds = Number.isFinite(scaledTime) && scaledTime > 0
      ? Math.log(scaledTime) - maximumLogRatePerSecond
      : node.stateSha256 === targetStateSha256 ? -Infinity : null;
    return {
      stateId: node.stateId,
      stateSha256: node.stateSha256,
      shortHash: node.shortHash,
      targetHittingProbability: hittingProbability.get(node.stateSha256),
      targetReachable: targetReachable.has(node.stateSha256),
      conditionalMeanFirstPassageScaledTime: scaledTime,
      conditionalMeanFirstPassageLogSeconds: logTimeSeconds,
      conditionalMeanFirstPassageSeconds: logTimeSeconds === -Infinity ? 0
        : physicalTime(logTimeSeconds),
      conditionalExpectedObservedJumps: jumpsByState.get(node.stateSha256),
    };
  });
  const hittingResidual = maximumResidual(hittingMatrix, hittingSolution, hittingRight);
  const timeResidual = maximumResidual(timeMatrix, conditionalScaledTime, timeRight);
  const jumpResidual = maximumResidual(timeMatrix, conditionalJumps, jumpRight);
  return {
    schema: "gcts-finite-network-first-passage-v1",
    available: true,
    model: "finite observed-network backward equation with target-unreachable failure states and Doob-conditioned passage time",
    sourceStateSha256,
    targetStateSha256,
    temperatureKelvin: [...temperatures][0],
    methodSettingsSha256: [...methods][0],
    stateCount: nodes.length,
    directedEdgeCount: edges.length,
    targetReachableStateCount: targetReachable.size,
    observedFailureStateCount: failureStates.length,
    observedFailureStateSha256: failureStates.map((node) => node.stateSha256),
    sourceTargetHittingProbability: sourceHittingProbability,
    sourceTargetHitCertainInsideObservedCatalog: Math.abs(sourceHittingProbability - 1) <= 1e-10,
    sourceConditionalMeanFirstPassageScaledTime: sourceScaledTime,
    sourceConditionalMeanFirstPassageLogSeconds: sourceLogTimeSeconds,
    sourceConditionalMeanFirstPassageSeconds: physicalTime(sourceLogTimeSeconds),
    sourceConditionalExpectedObservedJumps: jumpsByState.get(sourceStateSha256),
    states,
    maximumLogRatePerSecond,
    backwardEquationHittingProbabilityResidual: hittingResidual,
    backwardEquationConditionalTimeResidual: timeResidual,
    backwardEquationConditionalJumpResidual: jumpResidual,
    numericalIdentitiesPassed: Math.max(hittingResidual, timeResidual, jumpResidual) <= 1e-9,
    targetUsed: false,
    exactStateGeometryChanged: false,
    missingExitRatesAssumedZeroForConditionalProjection: true,
    targetUnreachableObservedStatesTreatedAsFailure: true,
    equilibriumClaimed: false,
    completeCommittorClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "The target-hitting probability and target-conditioned mean passage time solve backward equations on the latest exact observed rates at one temperature and method. Target-unreachable observed states are explicit failures. Unobserved states and exits are omitted, not certified absent; the hitting probability is therefore a finite-catalog reachability statistic and the conditional time is not a mechanism-complete MFPT, bulk growth time, or experimental clock prediction.",
  };
}
