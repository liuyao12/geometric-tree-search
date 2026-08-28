function median(values) {
  if (!values.length) return null;
  const ordered = [...values].sort((first, second) => first - second);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
}

export function runBlockedStateReplication(records, {
  termId,
  outcomeId,
  observableId,
  minimumRuns = 3,
  zeroTolerance = 1e-12,
} = {}) {
  if (!Array.isArray(records)) throw new Error("records must be an array");
  if (!termId || !outcomeId || !observableId) {
    throw new Error("termId, outcomeId, and observableId are required");
  }
  if (!Number.isInteger(minimumRuns) || minimumRuns < 2) {
    throw new Error("minimumRuns must be an integer of at least two");
  }
  const unique = new Map();
  records.forEach((record) => {
    if (!record?.receiptSha256 || unique.has(record.receiptSha256)) return;
    unique.set(record.receiptSha256, record);
  });
  const matching = [...unique.values()].filter((record) => record.termId === termId
    && record.outcomeId === outcomeId);
  const eligible = [];
  let unresolvedRuns = 0;
  let targetTaintedRuns = 0;
  matching.forEach((record) => {
    const row = record.rows?.find((entry) => entry.observableId === observableId);
    if (record.targetUsed !== false) {
      targetTaintedRuns += 1;
      return;
    }
    if (!row?.resolved || !Number.isFinite(row.normalizedDifference)) {
      unresolvedRuns += 1;
      return;
    }
    const direction = row.normalizedDifference > zeroTolerance ? 1
      : row.normalizedDifference < -zeroTolerance ? -1 : 0;
    eligible.push({
      receiptSha256: record.receiptSha256,
      inputIdentity: record.inputIdentity || record.inputStructureSha256 || "unknown input",
      inputStructureSha256: record.inputStructureSha256 || null,
      scenarioId: record.scenarioId || null,
      material: record.material || "saved run",
      direction,
      normalizedDifference: row.normalizedDifference,
      difference: Number.isFinite(row.difference) ? row.difference : null,
      changedCount: row.changedCount,
      stableCount: row.stableCount,
    });
  });
  const positiveRuns = eligible.filter((run) => run.direction > 0).length;
  const negativeRuns = eligible.filter((run) => run.direction < 0).length;
  const neutralRuns = eligible.filter((run) => run.direction === 0).length;
  const directionalRuns = positiveRuns + negativeRuns;
  const dominantDirection = positiveRuns === negativeRuns ? 0 : positiveRuns > negativeRuns ? 1 : -1;
  const directionAgreement = directionalRuns ? Math.max(positiveRuns, negativeRuns) / directionalRuns : 0;
  const distinctInputs = new Set(eligible.map((run) => run.inputIdentity)).size;
  const distinctScenarios = new Set(eligible.map((run) => run.scenarioId).filter(Boolean)).size;
  const enoughRuns = eligible.length >= minimumRuns;
  const sameNonzeroDirection = enoughRuns && neutralRuns === 0 && directionAgreement === 1;
  const status = !enoughRuns ? "insufficient-runs"
    : !sameNonzeroDirection ? "heterogeneous"
      : distinctInputs >= 2 ? "cross-input-consistent" : "repeat-run-consistent";
  return {
    schema: 1,
    termId,
    outcomeId,
    observableId,
    minimumRuns,
    uniqueReceiptCount: unique.size,
    matchingRunCount: matching.length,
    eligibleRunCount: eligible.length,
    unresolvedRuns,
    targetTaintedRuns,
    positiveRuns,
    negativeRuns,
    neutralRuns,
    dominantDirection,
    directionAgreement,
    medianNormalizedDifference: median(eligible.map((run) => run.normalizedDifference)),
    minimumNormalizedDifference: eligible.length
      ? Math.min(...eligible.map((run) => run.normalizedDifference)) : null,
    maximumNormalizedDifference: eligible.length
      ? Math.max(...eligible.map((run) => run.normalizedDifference)) : null,
    distinctInputs,
    distinctScenarios,
    status,
    replicatedDirection: sameNonzeroDirection,
    runs: eligible,
    analysisUnit: "one resolved coordinate-free contrast per unique saved-run receipt",
    frontierRowsPooledAcrossRuns: false,
    exactDuplicateReceiptsIgnored: records.length - unique.size,
    pValueComputed: false,
    statisticalIndependenceAssumed: false,
    causalEffectInferred: false,
    physicalTimeModeled: false,
  };
}
