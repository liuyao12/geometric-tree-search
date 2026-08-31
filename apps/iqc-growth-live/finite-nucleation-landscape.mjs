function settingsKey(edge) {
  return `${edge.freeEnergySettingsSha256 || "missing"}|${edge.chemicalPotentialSettingsSha256 || "missing"}|${edge.temperatureKelvin ?? "missing"}`;
}

function rootSumSquares(values) {
  return Math.sqrt(values.reduce((sum, value) => sum + value * value, 0));
}

function withinThreeSigma(residual, uncertainty) {
  return Number.isFinite(residual) && Number.isFinite(uncertainty)
    && Math.abs(residual) <= 3 * Math.max(uncertainty, 1e-12);
}

function connectedComponents(nodes, edges) {
  const adjacency = new Map(nodes.map((node) => [node, []]));
  edges.forEach((edge) => {
    adjacency.get(edge.lowStateSha256)?.push(edge.highStateSha256);
    adjacency.get(edge.highStateSha256)?.push(edge.lowStateSha256);
  });
  const unseen = new Set(nodes); const components = [];
  while (unseen.size) {
    const start = [...unseen].sort()[0]; const queue = [start]; const component = [];
    unseen.delete(start);
    while (queue.length) {
      const current = queue.shift(); component.push(current);
      for (const next of adjacency.get(current) || []) {
        if (unseen.delete(next)) queue.push(next);
      }
    }
    components.push(component.sort());
  }
  return components;
}

export function buildFiniteNucleationLandscape(network) {
  if (!network || network.schema !== "gcts-finite-transition-network-v1") {
    throw new Error("a finite exact-state transition network is required");
  }
  const directedByKey = new Map(network.directedEdges.map((edge) => [edge.key, edge]));
  const eligible = network.pairedEdges.map((pair) => {
    const forward = directedByKey.get(`${pair.lowStateSha256}->${pair.highStateSha256}`);
    if (!forward || !pair.pairAudit?.grandCanonicalEvidenceComplete
        || !pair.pairAudit?.grandPotentialCyclePassed
        || !Number.isInteger(forward.initialAtomCount)
        || !Number.isInteger(forward.finalAtomCount)
        || !Number.isFinite(pair.grandPotentialDeltaElectronVolt)
        || !Number.isFinite(pair.grandPotentialDeltaUncertaintyElectronVolt)
        || !forward.freeEnergySettingsSha256 || !forward.chemicalPotentialSettingsSha256
        || !Number.isFinite(forward.temperatureKelvin)) return null;
    return { ...pair, lowAtomCount: forward.initialAtomCount,
      highAtomCount: forward.finalAtomCount, settingsKey: settingsKey(forward) };
  }).filter(Boolean);
  const groups = new Map();
  eligible.forEach((edge) => {
    const group = groups.get(edge.settingsKey) || []; group.push(edge);
    groups.set(edge.settingsKey, group);
  });
  const candidates = [];
  groups.forEach((edges, key) => {
    const counts = new Map(); let countConsistent = true;
    edges.forEach((edge) => {
      [[edge.lowStateSha256, edge.lowAtomCount],
        [edge.highStateSha256, edge.highAtomCount]].forEach(([hash, count]) => {
        if (counts.has(hash) && counts.get(hash) !== count) countConsistent = false;
        counts.set(hash, count);
      });
    });
    if (!countConsistent) return;
    connectedComponents([...counts.keys()], edges).forEach((component) => {
      const componentSet = new Set(component);
      const componentEdges = edges.filter((edge) => componentSet.has(edge.lowStateSha256)
        && componentSet.has(edge.highStateSha256));
      candidates.push({ key, component, edges: componentEdges, counts });
    });
  });
  candidates.sort((first, second) => second.component.length - first.component.length
    || second.edges.length - first.edges.length || first.key.localeCompare(second.key)
    || first.component[0].localeCompare(second.component[0]));
  const selected = candidates[0] || null;
  if (!selected) return {
    schema: "gcts-finite-nucleation-landscape-v1", states: [], edges: [],
    eligiblePairCount: eligible.length, evidenceAvailable: false,
    criticalSizeCandidateObserved: false, finiteProfileConsistencyPassed: false,
    targetUsed: false, surfaceEnergyInferred: false, nucleationRateInferred: false,
    claimBoundary: "No connected exact-state component has reversible, uncertainty-bearing grand-potential evidence and verified atom counts under one thermodynamic method.",
  };
  const root = [...selected.component].sort((first, second) =>
    selected.counts.get(first) - selected.counts.get(second) || first.localeCompare(second))[0];
  const adjacency = new Map(selected.component.map((hash) => [hash, []]));
  selected.edges.forEach((edge) => {
    adjacency.get(edge.lowStateSha256).push({ to: edge.highStateSha256,
      delta: edge.grandPotentialDeltaElectronVolt,
      sigma: edge.grandPotentialDeltaUncertaintyElectronVolt, edge });
    adjacency.get(edge.highStateSha256).push({ to: edge.lowStateSha256,
      delta: -edge.grandPotentialDeltaElectronVolt,
      sigma: edge.grandPotentialDeltaUncertaintyElectronVolt, edge });
  });
  adjacency.forEach((entries) => entries.sort((first, second) => first.to.localeCompare(second.to)));
  const potential = new Map([[root, { omega: 0, variance: 0, path: [] }]]);
  const queue = [root];
  while (queue.length) {
    const current = queue.shift(); const state = potential.get(current);
    for (const step of adjacency.get(current)) {
      if (potential.has(step.to)) continue;
      potential.set(step.to, { omega: state.omega + step.delta,
        variance: state.variance + step.sigma ** 2,
        path: [...state.path, step.edge.key] });
      queue.push(step.to);
    }
  }
  const edgeAudits = selected.edges.map((edge) => {
    const low = potential.get(edge.lowStateSha256); const high = potential.get(edge.highStateSha256);
    const residual = high.omega - low.omega - edge.grandPotentialDeltaElectronVolt;
    const uncertainty = rootSumSquares([Math.sqrt(low.variance), Math.sqrt(high.variance),
      edge.grandPotentialDeltaUncertaintyElectronVolt]);
    return { edgeKey: edge.key, residualElectronVolt: residual,
      uncertaintyElectronVolt: uncertainty,
      closurePassed: withinThreeSigma(residual, uncertainty) };
  });
  const states = selected.component.map((stateSha256) => {
    const value = potential.get(stateSha256);
    return { stateSha256, atomCount: selected.counts.get(stateSha256),
      relativeGrandPotentialElectronVolt: value.omega,
      uncertaintyElectronVolt: Math.sqrt(value.variance), pathEdgeKeys: value.path };
  }).sort((first, second) => first.atomCount - second.atomCount
    || first.stateSha256.localeCompare(second.stateSha256));
  const distinctCounts = [...new Set(states.map((state) => state.atomCount))].sort((a, b) => a - b);
  const critical = states.reduce((highest, state) => !highest
    || state.relativeGrandPotentialElectronVolt > highest.relativeGrandPotentialElectronVolt
    ? state : highest, null);
  const criticalSizeCandidateObserved = distinctCounts.length >= 3
    && critical.atomCount > distinctCounts[0] && critical.atomCount < distinctCounts.at(-1);
  return {
    schema: "gcts-finite-nucleation-landscape-v1",
    thermodynamicSettingsKey: selected.key,
    referenceStateSha256: root,
    temperatureKelvin: Number(selected.key.split("|").at(-1)),
    states,
    edges: edgeAudits,
    eligiblePairCount: eligible.length,
    evidenceAvailable: true,
    atomCountConsistent: true,
    finiteProfileConsistencyPassed: edgeAudits.every((edge) => edge.closurePassed),
    criticalSizeCandidateObserved,
    criticalStateSha256: criticalSizeCandidateObserved ? critical.stateSha256 : null,
    criticalAtomCount: criticalSizeCandidateObserved ? critical.atomCount : null,
    observedFormationBarrierElectronVolt: criticalSizeCandidateObserved
      ? critical.relativeGrandPotentialElectronVolt : null,
    surfaceEnergyInferred: false,
    bulkDrivingForceInferred: false,
    classicalNucleationTheoryFit: false,
    nucleationRateInferred: false,
    targetUsed: false,
    claimBoundary: "This is a relative grand-potential profile on one finite connected component of exact reversible states under one external T,V,mu method. An interior observed maximum is only a finite critical-size candidate. No surface/interfacial free energy, bulk driving force, CNT fit, nucleus shape ensemble, attachment kinetics, Zeldovich factor, nucleation rate, or macroscopic phase stability is inferred.",
  };
}
