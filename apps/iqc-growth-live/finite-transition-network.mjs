import { auditMicroscopicInversePair, normalizedCommittedTransition }
  from "./reversible-transition-lineage.mjs?v=20260831-352";

const BOLTZMANN_ELECTRON_VOLT_PER_KELVIN = 8.617333262145e-5;

function rootSumSquares(values) {
  return Math.sqrt(values.filter(Number.isFinite).reduce((sum, value) => sum + value * value, 0));
}

function directedKey(from, to) {
  return `${from}->${to}`;
}

function undirectedKey(first, second) {
  return [first, second].sort().join("<->");
}

function rateLogUncertainty(record) {
  if (!Number.isFinite(record.temperatureKelvin)
      || !Number.isFinite(record.barrierUncertaintyElectronVolt)
      || !Number.isFinite(record.attemptFrequencyUncertaintyLog10)) return null;
  const inverseThermalEnergy = 1
    / (BOLTZMANN_ELECTRON_VOLT_PER_KELVIN * record.temperatureKelvin);
  return rootSumSquares([record.barrierUncertaintyElectronVolt * inverseThermalEnergy,
    record.attemptFrequencyUncertaintyLog10 * Math.LN10]);
}

function withinThreeSigma(residual, uncertainty) {
  return Number.isFinite(residual) && Number.isFinite(uncertainty)
    && Math.abs(residual) <= 3 * Math.max(uncertainty, 1e-12);
}

function findTreePath(adjacency, start, goal) {
  const queue = [start];
  const previous = new Map([[start, null]]);
  while (queue.length) {
    const current = queue.shift();
    if (current === goal) break;
    for (const next of adjacency.get(current) || []) {
      if (previous.has(next)) continue;
      previous.set(next, current); queue.push(next);
    }
  }
  if (!previous.has(goal)) return null;
  const nodes = [];
  for (let cursor = goal; cursor != null; cursor = previous.get(cursor)) nodes.push(cursor);
  return nodes.reverse();
}

function orientedEdgeValue(edge, from, field) {
  const sign = edge.lowStateSha256 === from ? 1 : -1;
  const value = edge[field];
  return Number.isFinite(value) ? sign * value : null;
}

export function buildFiniteTransitionNetwork(rawHistory) {
  const observations = (Array.isArray(rawHistory) ? rawHistory : [])
    .map((record, ordinal) => ({ ...normalizedCommittedTransition(record), ordinal }));
  const eligible = observations.filter((record) => record.exactFinalGeometryReproduced
    && record.finalGeometrySha256 === record.committedStateSha256);
  const byDirection = new Map();
  eligible.forEach((record) => {
    const key = directedKey(record.initialGeometrySha256, record.finalGeometrySha256);
    const records = byDirection.get(key) || [];
    records.push(record); byDirection.set(key, records);
  });
  const activeDirected = new Map([...byDirection.entries()].map(([key, records]) =>
    [key, records.sort((first, second) => first.ordinal - second.ordinal).at(-1)]));
  const directedEdges = [...activeDirected.entries()].sort(([first], [second]) =>
    first.localeCompare(second)).map(([key, record]) => ({
    key,
    fromStateSha256: record.initialGeometrySha256,
    toStateSha256: record.finalGeometrySha256,
    eventId: record.eventId,
    candidateId: record.candidateId,
    eventDirection: record.eventDirection,
    initialAtomCount: record.initialAtomCount,
    finalAtomCount: record.finalAtomCount,
    logRatePerSecond: record.logRatePerSecond,
    logRateUncertainty: rateLogUncertainty(record),
    barrierElectronVolt: record.barrierElectronVolt,
    barrierUncertaintyElectronVolt: record.barrierUncertaintyElectronVolt,
    grandPotentialDeltaElectronVolt: record.grandPotentialDeltaElectronVolt,
    grandPotentialDeltaUncertaintyElectronVolt:
      record.grandPotentialDeltaUncertaintyElectronVolt,
    temperatureKelvin: record.temperatureKelvin,
    methodSettingsSha256: record.methodSettingsSha256,
    freeEnergySettingsSha256: record.freeEnergySettingsSha256,
    chemicalPotentialSettingsSha256: record.chemicalPotentialSettingsSha256,
  }));
  const stateHashes = [...new Set(eligible.flatMap((record) =>
    [record.initialGeometrySha256, record.finalGeometrySha256]))].sort();
  const pairKeys = [...new Set(eligible.map((record) =>
    undirectedKey(record.initialGeometrySha256, record.finalGeometrySha256)))].sort();
  const pairedEdges = [];
  const unpairedEdges = [];
  pairKeys.forEach((key) => {
    const [lowStateSha256, highStateSha256] = key.split("<->");
    const lowToHigh = activeDirected.get(directedKey(lowStateSha256, highStateSha256)) || null;
    const highToLow = activeDirected.get(directedKey(highStateSha256, lowStateSha256)) || null;
    if (!lowToHigh || !highToLow) {
      unpairedEdges.push({ key, lowStateSha256, highStateSha256,
        availableDirection: lowToHigh ? "low-to-high" : "high-to-low",
        eventId: (lowToHigh || highToLow)?.eventId || null });
      return;
    }
    const pairAudit = auditMicroscopicInversePair(lowToHigh, highToLow);
    const firstSigma = rateLogUncertainty(lowToHigh);
    const secondSigma = rateLogUncertainty(highToLow);
    pairedEdges.push({
      key, lowStateSha256, highStateSha256,
      lowToHighEventId: lowToHigh.eventId, highToLowEventId: highToLow.eventId,
      rateAffinityLog: Number.isFinite(lowToHigh.logRatePerSecond)
        && Number.isFinite(highToLow.logRatePerSecond)
        ? lowToHigh.logRatePerSecond - highToLow.logRatePerSecond : null,
      rateAffinityUncertainty: Number.isFinite(firstSigma) && Number.isFinite(secondSigma)
        ? rootSumSquares([firstSigma, secondSigma]) : null,
      grandPotentialDeltaElectronVolt: lowToHigh.grandPotentialDeltaElectronVolt,
      grandPotentialDeltaUncertaintyElectronVolt:
        lowToHigh.grandPotentialDeltaUncertaintyElectronVolt,
      temperatureKelvin: lowToHigh.temperatureKelvin === highToLow.temperatureKelvin
        ? lowToHigh.temperatureKelvin : null,
      methodSettingsMatched: lowToHigh.methodSettingsSha256 === highToLow.methodSettingsSha256,
      thermodynamicSettingsMatched: lowToHigh.freeEnergySettingsSha256 != null
        && lowToHigh.freeEnergySettingsSha256 === highToLow.freeEnergySettingsSha256
        && lowToHigh.chemicalPotentialSettingsSha256
          === highToLow.chemicalPotentialSettingsSha256,
      pairAudit,
    });
  });

  const parent = new Map(stateHashes.map((hash) => [hash, hash]));
  const find = (hash) => {
    let cursor = hash;
    while (parent.get(cursor) !== cursor) cursor = parent.get(cursor);
    let compress = hash;
    while (parent.get(compress) !== compress) {
      const next = parent.get(compress); parent.set(compress, cursor); compress = next;
    }
    return cursor;
  };
  const union = (first, second) => {
    const firstRoot = find(first); const secondRoot = find(second);
    if (firstRoot === secondRoot) return false;
    parent.set(secondRoot, firstRoot); return true;
  };
  const treeEdges = [];
  const nonTreeEdges = [];
  pairedEdges.forEach((edge) => {
    (union(edge.lowStateSha256, edge.highStateSha256) ? treeEdges : nonTreeEdges).push(edge);
  });
  const treeAdjacency = new Map(stateHashes.map((hash) => [hash, []]));
  treeEdges.forEach((edge) => {
    treeAdjacency.get(edge.lowStateSha256).push(edge.highStateSha256);
    treeAdjacency.get(edge.highStateSha256).push(edge.lowStateSha256);
  });
  treeAdjacency.forEach((neighbors) => neighbors.sort());
  const edgeByKey = new Map(pairedEdges.map((edge) => [edge.key, edge]));
  const cycles = nonTreeEdges.map((closingEdge, cycleIndex) => {
    const path = findTreePath(treeAdjacency, closingEdge.highStateSha256,
      closingEdge.lowStateSha256);
    const segments = [{ from: closingEdge.lowStateSha256,
      to: closingEdge.highStateSha256, edge: closingEdge }];
    for (let index = 0; index < path.length - 1; index++) {
      segments.push({ from: path[index], to: path[index + 1],
        edge: edgeByKey.get(undirectedKey(path[index], path[index + 1])) });
    }
    const rateValues = segments.map(({ edge, from }) =>
      orientedEdgeValue(edge, from, "rateAffinityLog"));
    const rateUncertainties = segments.map(({ edge }) => edge.rateAffinityUncertainty);
    const grandValues = segments.map(({ edge, from }) =>
      orientedEdgeValue(edge, from, "grandPotentialDeltaElectronVolt"));
    const grandUncertainties = segments.map(({ edge }) =>
      edge.grandPotentialDeltaUncertaintyElectronVolt);
    const rateEvidenceComplete = rateValues.every(Number.isFinite)
      && rateUncertainties.every(Number.isFinite);
    const grandPotentialEvidenceComplete = grandValues.every(Number.isFinite)
      && grandUncertainties.every(Number.isFinite);
    const rateCycleAffinityLog = rateEvidenceComplete
      ? rateValues.reduce((sum, value) => sum + value, 0) : null;
    const rateCycleUncertainty = rateEvidenceComplete
      ? rootSumSquares(rateUncertainties) : null;
    const grandPotentialCycleResidualElectronVolt = grandPotentialEvidenceComplete
      ? grandValues.reduce((sum, value) => sum + value, 0) : null;
    const grandPotentialCycleUncertaintyElectronVolt = grandPotentialEvidenceComplete
      ? rootSumSquares(grandUncertainties) : null;
    return {
      cycleId: `cycle-${cycleIndex + 1}`,
      stateHashes: segments.map((segment) => segment.from),
      edgeKeys: segments.map((segment) => segment.edge.key),
      rateEvidenceComplete,
      grandPotentialEvidenceComplete,
      rateCycleAffinityLog,
      rateCycleUncertainty,
      kineticKolmogorovCyclePassed: withinThreeSigma(rateCycleAffinityLog,
        rateCycleUncertainty),
      grandPotentialCycleResidualElectronVolt,
      grandPotentialCycleUncertaintyElectronVolt,
      grandPotentialIntegrabilityPassed: withinThreeSigma(
        grandPotentialCycleResidualElectronVolt,
        grandPotentialCycleUncertaintyElectronVolt),
    };
  });
  cycles.forEach((cycle) => {
    cycle.cycleConsistencyPassed = cycle.kineticKolmogorovCyclePassed
      && cycle.grandPotentialIntegrabilityPassed;
  });
  const pairedComponents = new Set(stateHashes.filter((hash) =>
    pairedEdges.some((edge) => edge.lowStateSha256 === hash || edge.highStateSha256 === hash))
    .map(find));
  const everyPairLocallyBalanced = pairedEdges.length > 0
    && pairedEdges.every((edge) => edge.pairAudit.finitePairLocalBalancePassed);
  const finiteObservedNetworkCycleConsistencyPassed = cycles.length > 0
    && unpairedEdges.length === 0 && everyPairLocallyBalanced
    && cycles.every((cycle) => cycle.cycleConsistencyPassed);
  return {
    schema: "gcts-finite-transition-network-v1",
    nodes: stateHashes.map((stateSha256, index) => ({ stateId: `S${index + 1}`,
      stateSha256, shortHash: stateSha256.slice(0, 10) })),
    directedEdges,
    pairedEdges,
    unpairedEdges,
    cycles,
    committedObservationCount: observations.length,
    exactObservationCount: eligible.length,
    excludedPostStateDivergenceCount: observations.length - eligible.length,
    repeatedDirectedObservationCount: eligible.length - activeDirected.size,
    activeObservationPolicy: "latest exact committed observation per directed edge",
    uniqueDirectedEdgeCount: activeDirected.size,
    pairedEdgeCount: pairedEdges.length,
    unpairedEdgeCount: unpairedEdges.length,
    pairedConnectedComponentCount: pairedComponents.size,
    independentCycleCount: cycles.length,
    everyPairLocallyBalanced,
    kineticKolmogorovCycleConsistencyPassed: cycles.length > 0
      && cycles.every((cycle) => cycle.kineticKolmogorovCyclePassed),
    grandPotentialIntegrabilityPassed: cycles.length > 0
      && cycles.every((cycle) => cycle.grandPotentialIntegrabilityPassed),
    finiteObservedNetworkCycleConsistencyPassed,
    networkCompletenessCertified: false,
    globalDetailedBalanceCertified: false,
    ergodicityCertified: false,
    equilibriumEnsembleClaimed: false,
    targetUsed: false,
    claimBoundary: "Cycle closure tests Kolmogorov rate affinity and grand-potential integrability only on the exact bidirectional state graph actually observed. Missing states and mechanisms remain unknown; finite observed-network consistency is not global detailed balance, ergodicity, phase equilibrium, or an equilibrium ensemble.",
  };
}
