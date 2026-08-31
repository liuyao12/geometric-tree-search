function logSumExp(values) {
  if (!values.length || values.some((value) => !Number.isFinite(value))) return null;
  const maximum = Math.max(...values);
  return maximum + Math.log(values.reduce((sum, value) =>
    sum + Math.exp(value - maximum), 0));
}

function rootSumSquares(values) {
  return Math.sqrt(values.reduce((sum, value) => sum + value * value, 0));
}

function pathIdentity(edgeKeys) {
  return edgeKeys.join("|");
}

function betterLabel(candidate, incumbent) {
  if (!incumbent) return true;
  if (candidate.bottleneckLogRate !== incumbent.bottleneckLogRate) {
    return candidate.bottleneckLogRate > incumbent.bottleneckLogRate;
  }
  if (candidate.edgeKeys.length !== incumbent.edgeKeys.length) {
    return candidate.edgeKeys.length < incumbent.edgeKeys.length;
  }
  return pathIdentity(candidate.edgeKeys).localeCompare(pathIdentity(incumbent.edgeKeys)) < 0;
}

function summarizePath(network, sourceStateSha256, targetStateSha256, label) {
  if (!label) return null;
  const edgeByKey = new Map(network.directedEdges.map((edge) => [edge.key, edge]));
  const edges = label.edgeKeys.map((key) => edgeByKey.get(key));
  const bottleneckEdge = edges.reduce((slowest, edge) =>
    !slowest || edge.logRatePerSecond < slowest.logRatePerSecond ? edge : slowest, null);
  const barrierEvidenceComplete = edges.length > 0 && edges.every((edge) =>
    Number.isFinite(edge.barrierElectronVolt)
      && Number.isFinite(edge.barrierUncertaintyElectronVolt));
  const temperatures = new Set(edges.map((edge) => edge.temperatureKelvin));
  const methods = new Set(edges.map((edge) => edge.methodSettingsSha256));
  const thermodynamicSettings = new Set(edges.map((edge) =>
    `${edge.freeEnergySettingsSha256 || "missing"}|${edge.chemicalPotentialSettingsSha256 || "missing"}|${edge.temperatureKelvin ?? "missing"}`));
  const commonTemperatureKelvin = temperatures.size === 1
    && Number.isFinite(edges[0]?.temperatureKelvin) ? edges[0].temperatureKelvin : null;
  const commonBarrierMethod = methods.size === 1 && !methods.has(null)
    && !methods.has(undefined);
  const commonThermodynamicSettings = thermodynamicSettings.size === 1
    && edges.every((edge) => edge.freeEnergySettingsSha256
      && edge.chemicalPotentialSettingsSha256);
  const kineticConditionsComparable = Number.isFinite(commonTemperatureKelvin)
    && commonBarrierMethod;
  const grandPotentialEvidenceComplete = commonThermodynamicSettings && edges.every((edge) =>
    Number.isFinite(edge.grandPotentialDeltaElectronVolt)
      && Number.isFinite(edge.grandPotentialDeltaUncertaintyElectronVolt));
  const logConditionalSerialWaitingTimeSeconds = logSumExp(edges.map((edge) =>
    -edge.logRatePerSecond));
  return {
    pathId: `path:${sourceStateSha256.slice(0, 10)}:${targetStateSha256.slice(0, 10)}:${pathIdentity(label.edgeKeys)}`,
    sourceStateSha256,
    targetStateSha256,
    stateHashes: label.stateHashes,
    edgeKeys: label.edgeKeys,
    stepCount: edges.length,
    bottleneckEdgeKey: bottleneckEdge?.key || null,
    bottleneckLogRatePerSecond: bottleneckEdge?.logRatePerSecond ?? null,
    bottleneckLogRateUncertainty: bottleneckEdge?.logRateUncertainty ?? null,
    barrierEvidenceComplete,
    maximumBarrierElectronVolt: barrierEvidenceComplete
      ? Math.max(...edges.map((edge) => edge.barrierElectronVolt)) : null,
    logConditionalSerialWaitingTimeSeconds,
    conditionalSerialWaitingTimeSeconds: Number.isFinite(logConditionalSerialWaitingTimeSeconds)
      && logConditionalSerialWaitingTimeSeconds < 700
      ? Math.exp(logConditionalSerialWaitingTimeSeconds) : null,
    grandPotentialEvidenceComplete,
    grandPotentialDeltaElectronVolt: grandPotentialEvidenceComplete
      ? edges.reduce((sum, edge) => sum + edge.grandPotentialDeltaElectronVolt, 0) : null,
    grandPotentialDeltaUncertaintyElectronVolt: grandPotentialEvidenceComplete
      ? rootSumSquares(edges.map((edge) =>
        edge.grandPotentialDeltaUncertaintyElectronVolt)) : null,
    commonTemperatureKelvin,
    commonBarrierMethod,
    commonThermodynamicSettings,
    kineticConditionsComparable,
    selectionCriterion: "maximize the minimum observed directed log rate; then fewer edges; then canonical edge order",
    targetUsed: false,
  };
}

export function selectObservedTransitionPath(network, sourceStateSha256,
  targetStateSha256, { excludedEdgeKeys = [] } = {}) {
  if (!network || network.schema !== "gcts-finite-transition-network-v1") {
    throw new Error("a finite exact-state transition network is required");
  }
  const nodeHashes = new Set(network.nodes.map((node) => node.stateSha256));
  if (!nodeHashes.has(sourceStateSha256) || !nodeHashes.has(targetStateSha256)) return null;
  if (sourceStateSha256 === targetStateSha256) {
    return summarizePath(network, sourceStateSha256, targetStateSha256,
      { bottleneckLogRate: Infinity, stateHashes: [sourceStateSha256], edgeKeys: [] });
  }
  const excluded = new Set(excludedEdgeKeys);
  const adjacency = new Map(network.nodes.map((node) => [node.stateSha256, []]));
  network.directedEdges.filter((edge) => Number.isFinite(edge.logRatePerSecond)
    && !excluded.has(edge.key)).forEach((edge) => adjacency.get(edge.fromStateSha256)?.push(edge));
  adjacency.forEach((edges) => edges.sort((first, second) => first.key.localeCompare(second.key)));
  const best = new Map([[sourceStateSha256, { bottleneckLogRate: Infinity,
    stateHashes: [sourceStateSha256], edgeKeys: [] }]]);
  const pending = new Set([sourceStateSha256]);
  while (pending.size) {
    const current = [...pending].sort((first, second) => {
      const firstLabel = best.get(first); const secondLabel = best.get(second);
      if (firstLabel.bottleneckLogRate !== secondLabel.bottleneckLogRate) {
        return secondLabel.bottleneckLogRate - firstLabel.bottleneckLogRate;
      }
      return pathIdentity(firstLabel.edgeKeys).localeCompare(pathIdentity(secondLabel.edgeKeys));
    })[0];
    pending.delete(current);
    const label = best.get(current);
    for (const edge of adjacency.get(current) || []) {
      if (label.stateHashes.includes(edge.toStateSha256)) continue;
      const candidate = { bottleneckLogRate: Math.min(label.bottleneckLogRate,
        edge.logRatePerSecond), stateHashes: [...label.stateHashes, edge.toStateSha256],
      edgeKeys: [...label.edgeKeys, edge.key] };
      if (betterLabel(candidate, best.get(edge.toStateSha256))) {
        best.set(edge.toStateSha256, candidate); pending.add(edge.toStateSha256);
      }
    }
  }
  return summarizePath(network, sourceStateSha256, targetStateSha256,
    best.get(targetStateSha256));
}

export function auditCompetingObservedTransitionPaths(network, sourceStateSha256,
  targetStateSha256) {
  const primary = selectObservedTransitionPath(network, sourceStateSha256,
    targetStateSha256);
  const alternatives = primary ? primary.edgeKeys.map((edgeKey) =>
    selectObservedTransitionPath(network, sourceStateSha256, targetStateSha256,
      { excludedEdgeKeys: [edgeKey] })).filter(Boolean) : [];
  const unique = [...new Map(alternatives.map((path) => [pathIdentity(path.edgeKeys), path])).values()]
    .filter((path) => path.pathId !== primary?.pathId).sort((first, second) => {
      if (first.bottleneckLogRatePerSecond !== second.bottleneckLogRatePerSecond) {
        return second.bottleneckLogRatePerSecond - first.bottleneckLogRatePerSecond;
      }
      return first.pathId.localeCompare(second.pathId);
    });
  const competing = unique[0] || null;
  return {
    schema: "gcts-finite-transition-pathway-audit-v1",
    sourceStateSha256,
    targetStateSha256,
    primary,
    competing,
    distinctCompetingPathAvailable: Boolean(competing),
    competingPathComparisonEligible: Boolean(primary?.kineticConditionsComparable
      && competing?.kineticConditionsComparable
      && primary.commonTemperatureKelvin === competing.commonTemperatureKelvin),
    bottleneckLogRateSeparation: primary && competing
      ? primary.bottleneckLogRatePerSecond - competing.bottleneckLogRatePerSecond : null,
    observedStateCount: network?.nodes?.length || 0,
    observedDirectedEdgeCount: network?.directedEdges?.length || 0,
    networkCompletenessCertified: false,
    globalFastestPathCertified: false,
    meanFirstPassageTimeClaimed: false,
    mechanismCompletenessClaimed: false,
    targetUsed: false,
    claimBoundary: "The selected route is widest only within the exact directed edges observed: it maximizes the slowest supplied rate. Cross-edge kinetic comparison additionally requires one temperature and barrier method. The alternative differs by at least one excluded primary edge but need not be fully edge-disjoint. The reported serial waiting time conditions on traversing that path without branching or recrossing. Missing mechanisms remain open; this is not a global fastest path, committor, mean first-passage time, transition-path ensemble, or complete mechanism.",
  };
}
