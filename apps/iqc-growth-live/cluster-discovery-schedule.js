const FAMILY_PRIORITY = Object.freeze({ molecule: 0, support: 1, bridge: 2, gap: 3, residual: 4 });

function proportionalStep(rank, count, start, end) {
  if (count <= 1) return start;
  return start + Math.floor(rank * (end - start) / (count - 1));
}

function placementLexicalKey(placement) {
  return `${placement.family}:${placement.type}:${placement.support.join(",")}:${placement.placementIndex}`;
}

export function evidenceOrderedPlacementSchedule(placements = []) {
  const normalized = placements.map((placement, index) => ({ ...placement,
    placementIndex: Number.isInteger(placement.placementIndex) ? placement.placementIndex : index,
    support: [...new Set(placement.support || [])].sort((first, second) => first - second) }));
  const classFrequency = new Map();
  normalized.forEach((placement) => {
    const key = `${placement.family}:${placement.type}`;
    classFrequency.set(key, (classFrequency.get(key) || 0) + 1);
  });
  const remaining = new Set(normalized.map((placement) => placement.placementIndex));
  const byIndex = new Map(normalized.map((placement) => [placement.placementIndex, placement]));
  const covered = new Set();
  const selected = [];
  while (remaining.size) {
    const ranked = [...remaining].map((placementIndex) => {
      const placement = byIndex.get(placementIndex);
      const uncoveredGain = placement.support.filter((atomIndex) => !covered.has(atomIndex)).length;
      const redundantOverlap = placement.support.length - uncoveredGain;
      return { placement, uncoveredGain, redundantOverlap,
        classFrequency: classFrequency.get(`${placement.family}:${placement.type}`) || 1 };
    }).sort((first, second) => second.uncoveredGain - first.uncoveredGain
      || second.classFrequency - first.classFrequency
      || first.redundantOverlap - second.redundantOverlap
      || (FAMILY_PRIORITY[first.placement.family] ?? 8) - (FAMILY_PRIORITY[second.placement.family] ?? 8)
      || placementLexicalKey(first.placement).localeCompare(placementLexicalKey(second.placement)));
    const choice = ranked[0];
    remaining.delete(choice.placement.placementIndex);
    choice.placement.support.forEach((atomIndex) => covered.add(atomIndex));
    selected.push({ ...choice.placement, selectionRank: selected.length + 1,
      uncoveredGain: choice.uncoveredGain, redundantOverlap: choice.redundantOverlap,
      classFrequency: choice.classFrequency,
      selectionReason: choice.uncoveredGain > 0 ? "maximum-cover-gain" : "recurring-overlap-enrichment" });
  }
  return selected;
}

export function evidenceOrderedClusterDiscoverySchedule({ placements = [], edges = [], totalSteps = 36 } = {}) {
  const decisionStart = 8;
  const decisionEnd = Math.max(decisionStart, totalSteps - 5);
  const orderedPlacements = evidenceOrderedPlacementSchedule(placements).map((placement, rank, selected) => ({
    ...placement, settleStep: proportionalStep(rank, selected.length, decisionStart, decisionEnd),
  }));
  const placementSteps = new Map(orderedPlacements.map((placement) =>
    [placement.placementIndex, placement.settleStep]));
  const firstCoverageStep = new Map();
  orderedPlacements.forEach((placement) => placement.support.forEach((atomIndex) => {
    firstCoverageStep.set(atomIndex, Math.min(firstCoverageStep.get(atomIndex) ?? Infinity, placement.settleStep));
  }));
  const birthOrder = [...edges].sort((first, second) =>
    (first.normalizedDistance ?? first.length) - (second.normalizedDistance ?? second.length)
    || String(first.coloredPair || "").localeCompare(String(second.coloredPair || ""))
    || first.key.localeCompare(second.key));
  const birthRanks = new Map(birthOrder.map((edge, rank) => [edge.key, rank]));
  const scheduledEdges = edges.map((edge) => {
    const birthStep = proportionalStep(birthRanks.get(edge.key) || 0, birthOrder.length, 1, 7);
    const supportingSteps = [...(edge.placementIndices || [])]
      .map((index) => placementSteps.get(index)).filter(Number.isFinite);
    const coverageDecision = Math.max(firstCoverageStep.get(edge.first) ?? decisionEnd,
      firstCoverageStep.get(edge.second) ?? decisionEnd) + 1;
    const decisionStep = edge.final
      ? Math.min(...supportingSteps, decisionEnd)
      : Math.min(decisionEnd, Math.max(birthStep + 1, coverageDecision));
    return { ...edge, birthStep, decisionStep };
  });
  return { totalSteps, edges: scheduledEdges, placements: orderedPlacements,
    orderingAudit: {
      candidateBirthOrder: "colored-distance length then lexical relation key",
      placementOrder: "maximum uncovered support gain → class recurrence → minimum redundant overlap → family → lexical support",
      rejectedDecisionOrder: "after both endpoints acquire selected-cover evidence",
      hashSchedulingUsed: false,
      finalMembershipUsed: true,
      physicalTimeClaimed: false,
    } };
}
