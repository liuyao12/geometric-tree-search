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
  epsilon = DEFAULT_EPSILON,
  candidateSetDigest = null,
} = {}) {
  if (!Array.isArray(candidates) || candidates.length < 2) return null;
  const keys = candidates.map((candidate, index) => String(candidate.candidateKey ?? index));
  if (new Set(keys).size !== keys.length) throw new Error("Identifiability audit requires unique candidate keys");
  const excluded = new Set(excludedTermIds);
  const firstTerms = Array.isArray(candidates[0].scoreTerms) ? candidates[0].scoreTerms : [];
  const withheld = [];
  const terms = [];
  firstTerms.forEach((prototype) => {
    const id = String(prototype.id);
    const rows = candidates.map((candidate) => candidate.scoreTerms?.find((term) => term.id === id));
    const complete = rows.every(Boolean);
    const values = rows.map((row) => finiteNumber(row?.contribution));
    const weights = rows.map((row) => finiteNumber(row?.weight));
    const stats = moments(values);
    const reason = excluded.has(id) ? "excluded-by-target-blind-contract"
      : !complete ? "missing-on-one-or-more-candidates"
        : weights.every((weight) => Math.abs(weight) <= epsilon) ? "inactive-zero-weight"
          : stats.maximum - stats.minimum <= epsilon ? "constant-on-this-frontier" : null;
    const summary = { id, label: String(prototype.label || id), role: prototype.role || "",
      claimBoundary: prototype.claimBoundary || "", values, weights, ...stats };
    if (reason) withheld.push({ id, label: summary.label, reason });
    else terms.push(summary);
  });
  const pairs = [];
  terms.forEach((first, row) => terms.forEach((second, column) => {
    const diagonal = row === column;
    const pearson = diagonal ? 1 : correlation(first.values, second.values, epsilon);
    const spearman = diagonal ? 1
      : correlation(averageRanks(first.values), averageRanks(second.values), epsilon);
    pairs.push({ row, column, firstId: first.id, secondId: second.id,
      firstLabel: first.label, secondLabel: second.label, sampleCount: candidates.length,
      pearson, spearman, classification: pairClass(spearman, diagonal), diagonal });
  }));
  const independentPairs = pairs.filter((pair) => pair.row < pair.column && pair.spearman !== null);
  const strongest = [...independentPairs].sort((first, second) =>
    Math.abs(second.spearman) - Math.abs(first.spearman)
      || first.firstId.localeCompare(second.firstId) || first.secondId.localeCompare(second.secondId))[0] || null;
  const serialized = JSON.stringify({ candidateSetDigest, keys: [...keys].sort(),
    terms: terms.map((term) => term.id),
    pairs: independentPairs.map((pair) => [pair.firstId, pair.secondId,
      Number(pair.pearson.toFixed(12)), Number(pair.spearman.toFixed(12))]) });
  return {
    candidateCount: candidates.length,
    candidateSetDigest,
    auditDigest: fnv1a(serialized),
    terms: terms.map(({ values, weights, ...term }) => term),
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
    interpretation: "local rank identifiability on one frozen frontier; not causal or physical independence",
  };
}

