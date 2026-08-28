const finiteVector = (value) => Array.isArray(value) && value.length === 3
  && value.every(Number.isFinite);

function normalized(value) {
  if (!finiteVector(value)) return [0, 0, 0];
  const norm = Math.hypot(...value);
  return norm > 1e-12 ? value.map((component) => component / norm) : [0, 0, 0];
}

const dot = (first, second) => first.reduce((sum, value, index) => sum + value * second[index], 0);

export function screenedCoherencyGraphField({
  adjacency,
  sources,
  startIds,
  candidateAxis,
  screeningLengthHops,
}) {
  if (!adjacency || typeof adjacency !== "object") throw new Error("coherency graph adjacency is required");
  if (!Array.isArray(sources) || !Array.isArray(startIds)) throw new Error("coherency graph sources and starts must be arrays");
  if (!(Number.isFinite(screeningLengthHops) && screeningLengthHops > 0)) {
    throw new Error("coherency screening length must be positive");
  }
  const starts = [...new Set(startIds.filter((id) => id !== null && id !== undefined)
    .map(String))].sort();
  const distance = new Map(starts.map((id) => [id, 0]));
  let frontier = starts;
  while (frontier.length) {
    const next = new Set();
    frontier.forEach((id) => {
      const neighbors = Array.isArray(adjacency[id]) ? adjacency[id] : [];
      neighbors.map(String).sort().forEach((neighbor) => {
        if (!distance.has(neighbor)) {
          distance.set(neighbor, distance.get(id) + 1);
          next.add(neighbor);
        }
      });
    });
    frontier = [...next].sort();
  }
  const axis = normalized(candidateAxis);
  const weighted = sources.map((source) => {
    const id = String(source.id);
    const hop = distance.get(id);
    if (!Number.isInteger(hop) || !Number.isFinite(source.mismatch)) return null;
    const weight = Math.exp(-hop / screeningLengthHops);
    return { id, hop, weight, mismatch: Math.max(0, source.mismatch),
      axisAgreement: Math.abs(dot(axis, normalized(source.axis))) };
  }).filter(Boolean).sort((first, second) => first.hop - second.hop || first.id.localeCompare(second.id));
  const totalWeight = weighted.reduce((sum, source) => sum + source.weight, 0);
  const squaredWeight = weighted.reduce((sum, source) => sum + source.weight ** 2, 0);
  const inheritedMismatch = totalWeight ? weighted.reduce((sum, source) =>
    sum + source.weight * source.mismatch, 0) / totalWeight : 0;
  const orientationAgreement = totalWeight ? weighted.reduce((sum, source) =>
    sum + source.weight * source.axisAgreement, 0) / totalWeight : 0;
  const shellMap = new Map();
  [...distance.values()].forEach((hop) => {
    const shell = shellMap.get(hop) || { hop, graphNodes: 0, sourceMarks: 0, sourceWeight: 0 };
    shell.graphNodes += 1; shellMap.set(hop, shell);
  });
  weighted.forEach((source) => {
    const shell = shellMap.get(source.hop);
    shell.sourceMarks += 1; shell.sourceWeight += source.weight;
  });
  const shells = [...shellMap.values()].sort((first, second) => first.hop - second.hop)
    .map((shell) => ({ ...shell, sourceWeight: Number(shell.sourceWeight.toFixed(12)) }));
  return Object.freeze({
    kernel: "exp(-graph_hop/screening_length)",
    screeningLengthHops,
    connectedGraphNodes: distance.size,
    sourceMarks: weighted.length,
    farthestGraphHop: distance.size ? Math.max(...distance.values()) : 0,
    totalKernelWeight: totalWeight,
    effectiveSourceCount: squaredWeight ? totalWeight ** 2 / squaredWeight : 0,
    inheritedMismatch,
    orientationAgreement,
    hotspot: weighted.length ? Math.max(...weighted.map((source) => source.mismatch)) : 0,
    shells,
    acceptedHistoryOnly: true,
    targetUsed: false,
    physicalTimeModeled: false,
    stressInferred: false,
    elasticEnergyInferred: false,
    forceBalanceSolved: false,
  });
}
