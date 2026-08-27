function averageRanks(values) {
  const order = values.map((value, index) => ({ value, index }))
    .sort((first, second) => first.value - second.value || first.index - second.index);
  const ranks = new Array(values.length);
  for (let start = 0; start < order.length;) {
    let end = start + 1;
    while (end < order.length && order[end].value === order[start].value) end++;
    const rank = (start + end - 1) / 2 + 1;
    for (let index = start; index < end; index++) ranks[order[index].index] = rank;
    start = end;
  }
  return ranks;
}

function pearson(first, second) {
  const meanFirst = first.reduce((sum, value) => sum + value, 0) / first.length;
  const meanSecond = second.reduce((sum, value) => sum + value, 0) / second.length;
  let covariance = 0; let varianceFirst = 0; let varianceSecond = 0;
  first.forEach((value, index) => {
    const left = value - meanFirst; const right = second[index] - meanSecond;
    covariance += left * right; varianceFirst += left * left; varianceSecond += right * right;
  });
  const denominator = Math.sqrt(varianceFirst * varianceSecond);
  return denominator > 1e-14 ? covariance / denominator : null;
}

function rounded(value, digits = 5) {
  if (!Number.isFinite(value)) return null;
  const scale = 10 ** digits;
  return Math.round(value * scale) / scale;
}

/** Descriptive monotone association, with one sample per whole-cluster placement. */
export function buildCreationResponseAssociation(records, { minimumSamples = 4 } = {}) {
  if (!Array.isArray(records) || minimumSamples < 3) throw new Error("association needs placement records and a finite sample gate");
  const ids = records.map((record) => String(record.placementId));
  if (new Set(ids).size !== ids.length) throw new Error("each whole-cluster placement must appear exactly once");
  const normalized = records.map((record) => {
    if (!Array.isArray(record.physicsTerms) || !record.outcomes || typeof record.outcomes !== "object") {
      throw new Error("association records need frozen physics terms and aggregated outcomes");
    }
    const terms = Object.fromEntries(record.physicsTerms.filter((term) => term?.id
      && Number.isFinite(term.contribution) && Math.abs(term.weight) > 1e-12)
      .map((term) => [term.id, { label: term.label || term.id, contribution: term.contribution }]));
    const outcomes = Object.fromEntries(Object.entries(record.outcomes).filter(([, value]) => Number.isFinite(value)));
    return { placementId: record.placementId, emittedSites: record.emittedSites, terms, outcomes };
  });
  const termIds = [...new Set(normalized.flatMap((record) => Object.keys(record.terms)))].sort();
  const outcomeIds = [...new Set(normalized.flatMap((record) => Object.keys(record.outcomes)))].sort();
  const associations = [];
  termIds.forEach((termId) => outcomeIds.forEach((outcomeId) => {
    const pairs = normalized.filter((record) => record.terms[termId]
      && Number.isFinite(record.outcomes[outcomeId])).map((record) => ({ placementId: record.placementId,
      x: record.terms[termId].contribution, y: record.outcomes[outcomeId], emittedSites: record.emittedSites }));
    if (pairs.length < minimumSamples) return;
    const rho = pearson(averageRanks(pairs.map((pair) => pair.x)), averageRanks(pairs.map((pair) => pair.y)));
    if (!Number.isFinite(rho)) return;
    associations.push({ termId, termLabel: normalized.find((record) => record.terms[termId])?.terms[termId].label || termId,
      outcomeId, sampleCount: pairs.length, spearmanRho: rounded(rho), points: pairs });
  }));
  associations.sort((first, second) => Math.abs(second.spearmanRho) - Math.abs(first.spearmanRho)
    || first.termId.localeCompare(second.termId) || first.outcomeId.localeCompare(second.outcomeId));
  return {
    available: associations.length > 0,
    placementSamples: normalized.length,
    emittedSitePresentations: normalized.reduce((sum, record) => sum + (record.emittedSites || 0), 0),
    termIds, outcomeIds, associations,
    minimumSamples,
    groupingUnit: "one accepted whole-cluster placement",
    atomLevelPseudoreplicationAvoided: true,
    targetUsed: false, causalEffectInferred: false, independentMaterialSamples: false,
    energyInferred: false, kineticsInferred: false,
  };
}

/** Select a term on earlier complete leap blocks, then score it on later blocks. */
export function blockedCreationResponseValidation(records, outcomeId, {
  trainingFraction = 2 / 3, minimumSamplesPerSplit = 8,
} = {}) {
  if (!Array.isArray(records) || !outcomeId || !(trainingFraction > 0 && trainingFraction < 1)
      || minimumSamplesPerSplit < 3 || records.some((record) => !Number.isInteger(record.leapIndex))) {
    throw new Error("blocked validation needs placement records with finite structural-leap identities");
  }
  const leapIndices = [...new Set(records.map((record) => record.leapIndex))].sort((first, second) => first - second);
  if (leapIndices.length < 3) return { available: false,
    reason: "at least three complete structural-leap blocks are required", leapBlocks: leapIndices.length,
    selectionUsedHeldout: false, targetUsed: false };
  const trainingBlockCount = Math.min(leapIndices.length - 1,
    Math.max(1, Math.ceil(leapIndices.length * trainingFraction)));
  const trainingLeaps = leapIndices.slice(0, trainingBlockCount);
  const heldoutLeaps = leapIndices.slice(trainingBlockCount);
  const trainingSet = new Set(trainingLeaps); const heldoutSet = new Set(heldoutLeaps);
  const trainingRecords = records.filter((record) => trainingSet.has(record.leapIndex));
  const heldoutRecords = records.filter((record) => heldoutSet.has(record.leapIndex));
  const trainingAudit = buildCreationResponseAssociation(trainingRecords,
    { minimumSamples: minimumSamplesPerSplit });
  const candidates = trainingAudit.associations.filter((entry) => entry.outcomeId === outcomeId)
    .sort((first, second) => Math.abs(second.spearmanRho) - Math.abs(first.spearmanRho)
      || first.termId.localeCompare(second.termId));
  const selected = candidates[0];
  if (!selected) return { available: false,
    reason: "earlier leap blocks have insufficient varying grouped samples",
    trainingLeaps, heldoutLeaps, trainingPlacements: trainingRecords.length,
    heldoutPlacements: heldoutRecords.length, selectionUsedHeldout: false, targetUsed: false };
  const heldoutAudit = buildCreationResponseAssociation(heldoutRecords,
    { minimumSamples: minimumSamplesPerSplit });
  const heldout = heldoutAudit.associations.find((entry) => entry.outcomeId === outcomeId
    && entry.termId === selected.termId);
  if (!heldout) return { available: false,
    reason: "frozen term has insufficient variation or support in later leap blocks",
    termId: selected.termId, termLabel: selected.termLabel, trainingRho: selected.spearmanRho,
    trainingLeaps, heldoutLeaps, trainingPlacements: trainingRecords.length,
    heldoutPlacements: heldoutRecords.length, selectionUsedHeldout: false, targetUsed: false };
  return {
    available: true, outcomeId, termId: selected.termId, termLabel: selected.termLabel,
    trainingRho: selected.spearmanRho, heldoutRho: heldout.spearmanRho,
    signRetained: Math.sign(selected.spearmanRho) === Math.sign(heldout.spearmanRho),
    trainingLeaps, heldoutLeaps, trainingPlacements: trainingRecords.length,
    heldoutPlacements: heldoutRecords.length,
    trainingSampleCount: selected.sampleCount, heldoutSampleCount: heldout.sampleCount,
    blockedByCompleteStructuralLeap: true, randomSplitUsed: false,
    selectionUsedHeldout: false, targetUsed: false,
    causalEffectInferred: false, independentMaterialSamples: false,
  };
}
