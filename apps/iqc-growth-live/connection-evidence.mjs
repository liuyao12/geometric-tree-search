function integer(value, label) {
  if (!Number.isInteger(value) || value < 0) throw new Error(`${label} must be a non-negative integer`);
  return value;
}

function placementType(placement, index) {
  if (!placement || !Number.isInteger(placement.type)) throw new Error(`placement ${index} needs an integer type`);
  return placement.type;
}

/**
 * Audit how an exact cover becomes (or fails to become) a finite continuation
 * grammar. This function deliberately uses only the frozen occurrence graph:
 * it reports residual-mediated topology, but never promotes it to a growth rule.
 */
export function auditCoverConnectionEvidence({ placements, edges, rules = [] }) {
  if (!Array.isArray(placements) || !Array.isArray(edges) || !Array.isArray(rules)) {
    throw new Error("connection evidence requires placements, edges, and rules arrays");
  }
  const types = placements.map(placementType);
  const residual = placements.map((placement) => Boolean(placement.residual));
  const supportNeighborsByTerminal = new Map();
  const supportDegree = new Array(placements.length).fill(0);
  let directSupportEdges = 0;
  let supportTerminalEdges = 0;
  let terminalTerminalEdges = 0;
  edges.forEach((edge, edgeIndex) => {
    const first = integer(edge?.first, `edge ${edgeIndex} first`);
    const second = integer(edge?.second, `edge ${edgeIndex} second`);
    if (first >= placements.length || second >= placements.length || first === second) {
      throw new Error(`edge ${edgeIndex} references an invalid occurrence`);
    }
    if (!residual[first] && !residual[second]) {
      directSupportEdges++;
      supportDegree[first]++;
      supportDegree[second]++;
      return;
    }
    if (residual[first] && residual[second]) {
      terminalTerminalEdges++;
      return;
    }
    supportTerminalEdges++;
    const terminal = residual[first] ? first : second;
    const support = residual[first] ? second : first;
    const neighbors = supportNeighborsByTerminal.get(terminal) || new Set();
    neighbors.add(support);
    supportNeighborsByTerminal.set(terminal, neighbors);
  });

  let terminalBridgeOccurrencePairs = 0;
  const bridgeTopologyCounts = new Map();
  supportNeighborsByTerminal.forEach((neighbors) => {
    const ordered = [...neighbors].sort((a, b) => a - b);
    for (let first = 0; first < ordered.length; first++) {
      for (let second = first + 1; second < ordered.length; second++) {
        terminalBridgeOccurrencePairs++;
        const firstType = types[ordered[first]], secondType = types[ordered[second]];
        const key = firstType <= secondType ? `${firstType}:${secondType}` : `${secondType}:${firstType}`;
        bridgeTopologyCounts.set(key, (bridgeTopologyCounts.get(key) || 0) + 1);
      }
    }
  });
  const recurringBridgeTopologies = [...bridgeTopologyCounts.values()].filter((count) => count >= 2).length;
  const directRuleClasses = rules.length;
  const recurringDirectRules = rules.filter((rule) => (rule.count || 0) >= 2).length;
  const oneShotDirectRules = directRuleClasses - recurringDirectRules;
  const promotableOccurrences = residual.filter((value) => !value).length;
  const directIncidentOccurrences = supportDegree.filter((degree, index) => !residual[index] && degree > 0).length;
  const isolatedPromotableOccurrences = promotableOccurrences - directIncidentOccurrences;

  let verdict = "no-shared-interface";
  if (recurringDirectRules > 0) verdict = "direct-recurrent";
  else if (directRuleClasses > 0 || directSupportEdges > 0) verdict = "direct-one-shot";
  else if (terminalBridgeOccurrencePairs > 0) verdict = "terminal-mediated";
  else if (supportTerminalEdges > 0) verdict = "terminal-touched";

  return Object.freeze({
    promotableOccurrences,
    terminalOccurrences: placements.length - promotableOccurrences,
    directSupportEdges,
    supportTerminalEdges,
    terminalTerminalEdges,
    directRuleClasses,
    recurringDirectRules,
    oneShotDirectRules,
    directIncidentOccurrences,
    isolatedPromotableOccurrences,
    terminalBridgeOccurrencePairs,
    terminalBridgeTypePairs: bridgeTopologyCounts.size,
    recurringBridgeTopologies,
    verdict,
  });
}

export function connectionEvidenceNarrative(audit, { molecular = false } = {}) {
  if (!audit) return {
    label: "evidence unavailable",
    summary: "The current backend did not expose its occurrence-edge decomposition.",
    implication: "No continuation claim can be made from the displayed counts.",
  };
  if (molecular) return {
    label: "molecular anchor path",
    summary: "Molecular covers preserve complete molecules and exact gap terminals; their certified anchor backend is audited separately.",
    implication: "Absence of generic cluster ports here does not erase the molecular continuation certificate.",
  };
  if (audit.verdict === "direct-recurrent") return {
    label: "compressed continuation supported",
    summary: `${audit.recurringDirectRules} direct relative-pose classes recur between promotable supports.`,
    implication: "These witnessed proper-pose classes may supply target-free candidates; marking still only ranks them.",
  };
  if (audit.verdict === "direct-one-shot") return {
    label: "direct geometry, insufficient recurrence",
    summary: `${audit.directSupportEdges} support-to-support overlaps exist, but none yet establish a recurring direct rule.`,
    implication: "The window can be reconstructed, but extrapolating its one-off poses would memorize the sample.",
  };
  if (audit.verdict === "terminal-mediated") return {
    label: "connections mediated by exact terminals",
    summary: `${audit.terminalBridgeOccurrencePairs} support pairs meet only through residual/gap terminals across ${audit.terminalBridgeTypePairs} type-pair topologies; ${audit.recurrentTerminalBridgePoseClasses ?? 0} directed proper-pose classes recur at independent terminals.`,
    implication: "This is a representation frontier: even a recurrent composed pose remains diagnostic until terminal emission and frozen transfer are certified.",
  };
  if (audit.verdict === "terminal-touched") return {
    label: "terminal-dominated cover",
    summary: `${audit.supportTerminalEdges} support-to-terminal contacts occur without a complete support-to-support bridge.`,
    implication: "The recurring supports do not yet form a connected growth grammar.",
  };
  return {
    label: "no shared-interface evidence",
    summary: "The fitted promotable supports have no repeated shared interface in this observation window.",
    implication: "For an amorphous control this is a valid failure of compression; for a structured sample it calls for a richer cover or larger window.",
  };
}
