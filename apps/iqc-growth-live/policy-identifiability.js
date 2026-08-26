const DEFAULT_EPSILON = 1e-12;

function finiteNumber(value) {
  return Number.isFinite(value) ? Number(value) : 0;
}

function mean(values) {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length);
}

function moments(values) {
  const center = mean(values);
  const variance = values.reduce((sum, value) => sum + (value - center) ** 2, 0)
    / Math.max(1, values.length);
  return { mean: center, variance, standardDeviation: Math.sqrt(variance),
    minimum: Math.min(...values), maximum: Math.max(...values) };
}

function averageRanks(values) {
  const ordered = values.map((value, index) => ({ value, index }))
    .sort((first, second) => first.value - second.value || first.index - second.index);
  const ranks = new Array(values.length);
  for (let start = 0; start < ordered.length;) {
    let end = start + 1;
    while (end < ordered.length && ordered[end].value === ordered[start].value) end++;
    const averageRank = (start + 1 + end) / 2;
    for (let cursor = start; cursor < end; cursor++) ranks[ordered[cursor].index] = averageRank;
    start = end;
  }
  return ranks;
}

function correlation(first, second, epsilon = DEFAULT_EPSILON) {
  if (first.length !== second.length || first.length < 2) return null;
  const firstMean = mean(first); const secondMean = mean(second);
  let covariance = 0; let firstSquare = 0; let secondSquare = 0;
  for (let index = 0; index < first.length; index++) {
    const x = first[index] - firstMean; const y = second[index] - secondMean;
    covariance += x * y; firstSquare += x * x; secondSquare += y * y;
  }
  const denominator = Math.sqrt(firstSquare * secondSquare);
  if (denominator <= epsilon) return null;
  return Math.max(-1, Math.min(1, covariance / denominator));
}

function orthonormalBasis(variables, epsilon = DEFAULT_EPSILON) {
  const basis = [];
  const records = variables.map((variable) => {
    let vector = variable.values.map(finiteNumber);
    const center = mean(vector); vector = vector.map((value) => value - center);
    basis.forEach((axis) => {
      const projection = vector.reduce((sum, value, index) => sum + value * axis[index], 0);
      vector = vector.map((value, index) => value - projection * axis[index]);
    });
    const norm = Math.sqrt(vector.reduce((sum, value) => sum + value * value, 0));
    const accepted = norm > epsilon;
    if (accepted) basis.push(vector.map((value) => value / norm));
    return { id: variable.id, label: variable.label, accepted,
      reason: accepted ? "used" : "constant-or-collinear" };
  });
  return { basis, records };
}

function residualize(values, basis) {
  const center = mean(values);
  let residuals = values.map((value) => value - center);
  basis.forEach((axis) => {
    const projection = residuals.reduce((sum, value, index) => sum + value * axis[index], 0);
    residuals = residuals.map((value, index) => value - projection * axis[index]);
  });
  return residuals;
}

function pairClass(spearman, diagonal) {
  if (diagonal) return "self";
  if (spearman === null) return "unresolved";
  const magnitude = Math.abs(spearman);
  if (magnitude >= .9) return spearman >= 0 ? "near-redundant" : "opposed-rank";
  if (magnitude >= .5) return spearman >= 0 ? "related" : "opposed";
  if (magnitude <= .2) return "locally-distinct";
  return "partially-related";
}

function fnv1a(serialized) {
  let hash = 0x811c9dc5;
  for (let index = 0; index < serialized.length; index++) {
    hash ^= serialized.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}

/**
 * Audit local score-term identifiability on an already frozen candidate set.
 * Candidate coordinates and target labels are neither accepted nor returned.
 */
export function policyIdentifiabilityAudit(candidates, {
  excludedTermIds = ["known-window-gain", "exploration"],
  conditioningVariables = [],
  mode = "raw",
  epsilon = DEFAULT_EPSILON,
  candidateSetDigest = null,
} = {}) {
  if (!Array.isArray(candidates) || candidates.length < 2) return null;
  if (!["raw", "conditional"].includes(mode)) throw new Error(`Unknown identifiability mode ${mode}`);
  const keys = candidates.map((candidate, index) => String(candidate.candidateKey ?? index));
  if (new Set(keys).size !== keys.length) throw new Error("Identifiability audit requires unique candidate keys");
  const excluded = new Set(excludedTermIds);
  const controls = conditioningVariables.map((variable) => {
    if (!variable?.id || !Array.isArray(variable.values) || variable.values.length !== candidates.length) {
      throw new Error("Every conditioning variable requires an id and one value per candidate");
    }
    return { id: String(variable.id), label: String(variable.label || variable.id),
      values: variable.values.map(finiteNumber) };
  });
  const rawProjection = orthonormalBasis(controls, epsilon);
  const rankProjection = orthonormalBasis(controls.map((control) => ({ ...control,
    values: averageRanks(control.values) })), epsilon);
  const conditioningIds = new Set(controls.map((control) => control.id));
  const firstTerms = Array.isArray(candidates[0].scoreTerms) ? candidates[0].scoreTerms : [];
  const withheld = [];
  const terms = [];
  firstTerms.forEach((prototype) => {
    const id = String(prototype.id);
    const rows = candidates.map((candidate) => candidate.scoreTerms?.find((term) => term.id === id));
    const complete = rows.every(Boolean);
    const rawValues = rows.map((row) => finiteNumber(row?.contribution));
    const weights = rows.map((row) => finiteNumber(row?.weight));
    const values = mode === "conditional" ? residualize(rawValues, rawProjection.basis) : rawValues;
    const rankValues = mode === "conditional"
      ? residualize(averageRanks(rawValues), rankProjection.basis) : averageRanks(rawValues);
    const stats = moments(values);
    const reason = excluded.has(id) ? "excluded-by-target-blind-contract"
      : !complete ? "missing-on-one-or-more-candidates"
        : weights.every((weight) => Math.abs(weight) <= epsilon) ? "inactive-zero-weight"
          : mode === "conditional" && conditioningIds.has(id) ? "conditioning-variable"
            : stats.maximum - stats.minimum <= epsilon ? mode === "conditional"
              ? "explained-by-conditioning" : "constant-on-this-frontier" : null;
    const summary = { id, label: String(prototype.label || id), role: prototype.role || "",
      claimBoundary: prototype.claimBoundary || "", values, rankValues, weights,
      rawMean: mean(rawValues), rawStandardDeviation: moments(rawValues).standardDeviation, ...stats };
    if (reason) withheld.push({ id, label: summary.label, reason });
    else terms.push(summary);
  });
  const pairs = [];
  terms.forEach((first, row) => terms.forEach((second, column) => {
    const diagonal = row === column;
    const pearson = diagonal ? 1 : correlation(first.values, second.values, epsilon);
    const spearman = diagonal ? 1 : correlation(first.rankValues, second.rankValues, epsilon);
    pairs.push({ row, column, firstId: first.id, secondId: second.id,
      firstLabel: first.label, secondLabel: second.label, sampleCount: candidates.length,
      pearson, spearman, classification: pairClass(spearman, diagonal), diagonal });
  }));
  const independentPairs = pairs.filter((pair) => pair.row < pair.column && pair.spearman !== null);
  const strongest = [...independentPairs].sort((first, second) =>
    Math.abs(second.spearman) - Math.abs(first.spearman)
      || first.firstId.localeCompare(second.firstId) || first.secondId.localeCompare(second.secondId))[0] || null;
  const serialized = JSON.stringify({ candidateSetDigest, mode, keys: [...keys].sort(),
    conditioning: controls.map((control) => control.id),
    terms: terms.map((term) => term.id),
    pairs: independentPairs.map((pair) => [pair.firstId, pair.secondId,
      Number(pair.pearson.toFixed(12)), Number(pair.spearman.toFixed(12))]) });
  return {
    candidateCount: candidates.length,
    candidateSetDigest,
    auditDigest: fnv1a(serialized),
    mode,
    conditioningVariables: mode === "conditional" ? rawProjection.records.map((record, index) => ({
      ...record, rankAccepted: rankProjection.records[index].accepted,
      rankReason: rankProjection.records[index].reason,
    })) : [],
    terms: terms.map(({ values, rankValues, weights, ...term }) => term),
    pairs,
    withheld,
    strongestPair: strongest,
    nearRedundantPairs: independentPairs.filter((pair) => Math.abs(pair.spearman) >= .9).length,
    locallyDistinctPairs: independentPairs.filter((pair) => Math.abs(pair.spearman) <= .2).length,
    targetAwareTermsExcluded: withheld.filter((term) => term.reason === "excluded-by-target-blind-contract")
      .map((term) => term.id),
    candidateSetChanged: false,
    hardAdmissionChanged: false,
    candidateGeometryChanged: false,
    coordinatesEmbedded: false,
    targetUsed: false,
    executed: false,
    interpretation: mode === "conditional"
      ? "local residual identifiability after linear projection of declared structural controls; not causal or physical independence"
      : "local rank identifiability on one frozen frontier; not causal or physical independence",
  };
}

export function policyIdentifiabilityTrajectory(records, { firstId, secondId } = {}) {
  if (!Array.isArray(records) || !firstId || !secondId || firstId === secondId) return null;
  const points = records.map((record, historyIndex) => {
    const audit = record?.audit || null;
    const pair = audit?.pairs?.find((entry) => !entry.diagonal
      && ((entry.firstId === firstId && entry.secondId === secondId)
        || (entry.firstId === secondId && entry.secondId === firstId)));
    return {
      historyIndex,
      frontierIndex: record?.frontierIndex ?? historyIndex,
      candidateSetDigest: audit?.candidateSetDigest || record?.candidateSetDigest || null,
      auditDigest: audit?.auditDigest || null,
      candidateCount: audit?.candidateCount || 0,
      available: Boolean(pair && pair.pearson !== null && pair.spearman !== null),
      pearson: pair?.pearson ?? null,
      spearman: pair?.spearman ?? null,
      classification: pair?.classification || "unavailable",
    };
  });
  const available = points.filter((point) => point.available);
  let signChanges = 0;
  for (let index = 1; index < available.length; index++) {
    if (Math.sign(available[index - 1].spearman) !== Math.sign(available[index].spearman)) signChanges++;
  }
  let longestNearRedundantRun = 0; let currentRun = 0; let previousHistoryIndex = null;
  points.forEach((point) => {
    if (point.available && Math.abs(point.spearman) >= .9
        && (previousHistoryIndex === null || point.historyIndex === previousHistoryIndex + 1)) currentRun++;
    else currentRun = point.available && Math.abs(point.spearman) >= .9 ? 1 : 0;
    longestNearRedundantRun = Math.max(longestNearRedundantRun, currentRun);
    previousHistoryIndex = point.available ? point.historyIndex : null;
  });
  return {
    firstId, secondId, points,
    storedFrontiers: points.length,
    availableFrontiers: available.length,
    unavailableFrontiers: points.length - available.length,
    nearRedundantFrontiers: available.filter((point) => Math.abs(point.spearman) >= .9).length,
    locallyDistinctFrontiers: available.filter((point) => Math.abs(point.spearman) <= .2).length,
    signChanges,
    longestNearRedundantRun,
    candidateSetsChanged: false,
    candidatesRegenerated: false,
    searchReplayed: false,
    coordinatesEmbedded: false,
    targetUsed: false,
    executed: false,
    interpretation: "descriptive identifiability history over immutable frozen frontiers; not temporal dynamics or mechanism persistence",
  };
}

function compactPair(mode, firstId, secondId) {
  return mode?.pairs?.find((entry) => (entry.firstId === firstId && entry.secondId === secondId)
    || (entry.firstId === secondId && entry.secondId === firstId)) || null;
}

function conditioningSignature(mode) {
  return JSON.stringify((mode?.conditioningVariables || []).map((entry) => ({
    id: entry.id, accepted: entry.accepted, rankAccepted: entry.rankAccepted,
  })));
}

/**
 * Compare one preselected pair across independently frozen receipt summaries.
 * Candidate rows are never pooled and this function accepts no coordinates or labels.
 */
export function policyIdentifiabilityAcrossArms(arms, { firstId, secondId, mode = "conditional" } = {}) {
  if (!Array.isArray(arms) || arms.length < 2 || !firstId || !secondId || firstId === secondId) return null;
  if (!["raw", "conditional"].includes(mode)) throw new Error(`Unknown identifiability mode ${mode}`);
  const records = arms.map((arm) => {
    const modeAudit = arm?.identifiability?.latest?.modes?.[mode] || null;
    const pair = compactPair(modeAudit, firstId, secondId);
    return {
      armId: String(arm?.armId || ""), label: String(arm?.label || arm?.armId || "arm"),
      material: String(arm?.material || "unspecified material"),
      receiptSha256: arm?.receiptSha256 || null,
      frontierIndex: arm?.identifiability?.latest?.frontierIndex ?? null,
      candidateSetDigest: arm?.identifiability?.latest?.candidateSetDigest || null,
      auditDigest: modeAudit?.auditDigest || null,
      candidateCount: modeAudit?.candidateCount || 0,
      conditioningSignature: conditioningSignature(modeAudit),
      available: Boolean(pair && pair.pearson !== null && pair.spearman !== null),
      pearson: pair?.pearson ?? null, spearman: pair?.spearman ?? null,
      classification: pair?.classification || "unavailable",
    };
  });
  const referenceSignature = records[0].conditioningSignature;
  const compatibleConditioning = records.every((record) => record.conditioningSignature === referenceSignature);
  const available = records.filter((record) => record.available);
  const comparable = compatibleConditioning && available.length === records.length;
  const coefficients = available.map((record) => record.spearman);
  const range = comparable ? Math.max(...coefficients) - Math.min(...coefficients) : null;
  const signContrast = comparable && new Set(coefficients.map((value) => Math.sign(value))).size > 1;
  const serialized = JSON.stringify({ firstId, secondId, mode, compatibleConditioning,
    records: records.map((record) => [record.armId, record.receiptSha256, record.candidateSetDigest,
      record.auditDigest, record.candidateCount, record.spearman]) });
  return {
    firstId, secondId, mode, records, comparable, compatibleConditioning,
    coefficientRange: range, signContrast,
    comparisonDigest: fnv1a(serialized),
    candidateSetsPooled: false, candidatesRegenerated: false, searchReplayed: false,
    coordinatesEmbedded: false, targetUsed: false, executed: false,
    causalEffectInferred: false, crossMaterialUniversalityInferred: false,
    interpretation: comparable
      ? "descriptive contrast of the same preselected score-channel pair across separately frozen receipt frontiers; not a pooled estimate, causal effect, or universality claim"
      : "comparison withheld until every arm contains the same pair under a compatible frozen conditioning schema",
  };
}
