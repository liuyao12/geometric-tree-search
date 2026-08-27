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

/** Predeclared intensive/action-local state; no size, radius, frontier-count, or leap channel. */
export const LOCAL_CREATION_CONTEXT_FEATURE_IDS = Object.freeze([
  "support-sites", "shared-fraction", "novel-fraction",
  "coordination-deficit", "interface-fraction",
]);

/** Coordinate-free, order-invariant evidence payload suitable for receipts and replay. */
export function canonicalCreationResponseDataset(records, { maximumRecords = 256 } = {}) {
  if (!Array.isArray(records) || !Number.isInteger(maximumRecords) || maximumRecords < 1) {
    throw new Error("canonical creation-response data needs records and a positive finite limit");
  }
  const projected = records.map((record) => {
    if (record.placementId === undefined || !Number.isInteger(record.leapIndex)
        || !Array.isArray(record.physicsTerms) || !record.outcomes) {
      throw new Error("canonical creation-response records need placement, leap, terms, and outcomes");
    }
    return {
      placementId: String(record.placementId), leapIndex: record.leapIndex,
      emittedSites: Number.isFinite(record.emittedSites) ? record.emittedSites : 0,
      physicsTerms: record.physicsTerms.filter((term) => term?.id && Number.isFinite(term.contribution)
        && Number.isFinite(term.weight) && Math.abs(term.weight) > 1e-12)
        .map((term) => ({ id: String(term.id), label: term.label || String(term.id),
          weight: rounded(term.weight, 8), contribution: rounded(term.contribution, 8) }))
        .sort((first, second) => first.id.localeCompare(second.id)),
      contextFeatures: (record.contextFeatures || []).filter((feature) => feature?.id
        && Number.isFinite(feature.value)).map((feature) => ({ id: String(feature.id),
        label: feature.label || String(feature.id), value: rounded(feature.value, 8),
        role: feature.role || "target-free creation-time structural context" }))
        .sort((first, second) => first.id.localeCompare(second.id)),
      outcomes: Object.fromEntries(Object.entries(record.outcomes)
        .filter(([, value]) => Number.isFinite(value)).sort(([first], [second]) => first.localeCompare(second))
        .map(([id, value]) => [id, rounded(value, 8)])),
    };
  }).sort((first, second) => first.leapIndex - second.leapIndex
    || first.placementId.localeCompare(second.placementId));
  if (new Set(projected.map((record) => record.placementId)).size !== projected.length) {
    throw new Error("canonical creation-response data requires one record per whole-cluster placement");
  }
  const retained = projected.slice(-maximumRecords);
  return {
    schema: "gcts-creation-response-dataset-v1",
    groupingUnit: "one accepted whole-cluster placement",
    records: retained,
    totalEligiblePlacements: projected.length,
    retainedPlacements: retained.length,
    maximumRecords,
    truncated: projected.length > retained.length,
    coordinatesEmbedded: false, atomIdsEmbedded: false, targetUsed: false,
  };
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

/** Descriptive per-leap stability profile for one already-selected term/outcome pair. */
export function creationResponseLeapProfile(records, termId, outcomeId, { minimumSamples = 4 } = {}) {
  if (!Array.isArray(records) || !termId || !outcomeId || minimumSamples < 3
      || records.some((record) => !Number.isInteger(record.leapIndex))) {
    throw new Error("leap profile needs grouped placement records, term, outcome, and leap identities");
  }
  const leapIndices = [...new Set(records.map((record) => record.leapIndex))]
    .sort((first, second) => first - second);
  const blocks = leapIndices.map((leapIndex) => {
    const blockRecords = records.filter((record) => record.leapIndex === leapIndex);
    const audit = buildCreationResponseAssociation(blockRecords, { minimumSamples });
    const association = audit.associations.find((entry) => entry.termId === termId
      && entry.outcomeId === outcomeId);
    return { leapIndex, placements: blockRecords.length, emittedSitePresentations: audit.emittedSitePresentations,
      available: Boolean(association), spearmanRho: association?.spearmanRho ?? null,
      reason: association ? null : "insufficient support or within-block variation" };
  });
  const available = blocks.filter((block) => block.available);
  const signs = new Set(available.map((block) => Math.sign(block.spearmanRho)));
  return {
    termId, outcomeId, blocks,
    availableBlocks: available.length,
    totalBlocks: blocks.length,
    signConsistentAcrossAvailableBlocks: available.length > 0 && signs.size === 1,
    minimumRho: available.length ? Math.min(...available.map((block) => block.spearmanRho)) : null,
    maximumRho: available.length ? Math.max(...available.map((block) => block.spearmanRho)) : null,
    groupingUnit: "one accepted whole-cluster placement within one complete structural leap",
    descriptiveOnly: true, randomSplitUsed: false, targetUsed: false,
    causalEffectInferred: false, independentMaterialSamples: false,
  };
}

function solveRidgeSystem(matrix, vector) {
  const size = vector.length;
  const augmented = matrix.map((row, index) => [...row, vector[index]]);
  for (let column = 0; column < size; column++) {
    let pivot = column;
    for (let row = column + 1; row < size; row++) {
      if (Math.abs(augmented[row][column]) > Math.abs(augmented[pivot][column])) pivot = row;
    }
    if (Math.abs(augmented[pivot][column]) < 1e-12) return null;
    [augmented[column], augmented[pivot]] = [augmented[pivot], augmented[column]];
    const divisor = augmented[column][column];
    for (let index = column; index <= size; index++) augmented[column][index] /= divisor;
    for (let row = 0; row < size; row++) {
      if (row === column) continue;
      const factor = augmented[row][column];
      for (let index = column; index <= size; index++) augmented[row][index] -= factor * augmented[column][index];
    }
  }
  return augmented.map((row) => row[size]);
}

/** Fixed-ridge multichannel model fit on earlier complete leaps and scored only on later leaps. */
export function blockedCreationResponseSurrogate(records, outcomeId, {
  trainingFraction = 2 / 3, minimumSamplesPerSplit = 12, ridge = 1, maximumFeatures = 12,
  includeStructuralContext = false, maximumContextFeatures = 12, contextFeatureIds = null,
} = {}) {
  if (!Array.isArray(records) || !outcomeId || !(trainingFraction > 0 && trainingFraction < 1)
      || minimumSamplesPerSplit < 4 || !(ridge > 0) || !Number.isInteger(maximumFeatures)
      || maximumFeatures < 1 || !Number.isInteger(maximumContextFeatures) || maximumContextFeatures < 1
      || (contextFeatureIds !== null && (!Array.isArray(contextFeatureIds)
        || contextFeatureIds.some((id) => typeof id !== "string" || !id)))
      || records.some((record) => !Number.isInteger(record.leapIndex))) {
    throw new Error("blocked surrogate needs grouped leap records and fixed finite fit settings");
  }
  const leapIndices = [...new Set(records.map((record) => record.leapIndex))].sort((a, b) => a - b);
  if (leapIndices.length < 3) return { available: false,
    reason: "at least three complete structural-leap blocks are required", targetUsed: false,
    fitUsedHeldout: false };
  const trainingBlockCount = Math.min(leapIndices.length - 1,
    Math.max(1, Math.ceil(leapIndices.length * trainingFraction)));
  const trainingLeaps = leapIndices.slice(0, trainingBlockCount);
  const heldoutLeaps = leapIndices.slice(trainingBlockCount);
  const trainingSet = new Set(trainingLeaps); const heldoutSet = new Set(heldoutLeaps);
  const eligible = records.filter((record) => Number.isFinite(record.outcomes?.[outcomeId]));
  const trainingRecords = eligible.filter((record) => trainingSet.has(record.leapIndex));
  const heldoutRecords = eligible.filter((record) => heldoutSet.has(record.leapIndex));
  const unavailable = (reason) => ({ available: false, reason, trainingLeaps, heldoutLeaps,
    trainingPlacements: trainingRecords.length, heldoutPlacements: heldoutRecords.length,
    fitUsedHeldout: false, featureSelectionUsedOutcome: false, targetUsed: false });
  if (trainingRecords.length < minimumSamplesPerSplit || heldoutRecords.length < minimumSamplesPerSplit) {
    return unavailable("earlier or later leap blocks have insufficient grouped response samples");
  }
  const termMetadata = new Map();
  trainingRecords.forEach((record) => record.physicsTerms?.forEach((term) => {
    if (!term?.id || !Number.isFinite(term.contribution) || !Number.isFinite(term.weight)
        || Math.abs(term.weight) <= 1e-12) return;
    const current = termMetadata.get(term.id) || { id: term.id, sourceId: term.id,
      source: "physics-term", label: term.label || term.id, support: 0 };
    current.support++; termMetadata.set(term.id, current);
  }));
  const termCandidates = [...termMetadata.values()].filter((term) => term.support >= Math.ceil(trainingRecords.length / 2))
    .sort((first, second) => second.support - first.support || first.id.localeCompare(second.id))
    .slice(0, maximumFeatures);
  const contextMetadata = new Map();
  const admittedContextIds = contextFeatureIds === null ? null : new Set(contextFeatureIds);
  if (includeStructuralContext) trainingRecords.forEach((record) => record.contextFeatures?.forEach((feature) => {
    if (!feature?.id || !Number.isFinite(feature.value)
        || (admittedContextIds && !admittedContextIds.has(feature.id))) return;
    const id = `context:${feature.id}`;
    const current = contextMetadata.get(id) || { id, sourceId: feature.id, source: "structural-context",
      label: feature.label || feature.id, support: 0 };
    current.support++; contextMetadata.set(id, current);
  }));
  const contextCandidates = [...contextMetadata.values()]
    .filter((feature) => feature.support >= Math.ceil(trainingRecords.length / 2))
    .sort((first, second) => second.support - first.support || first.id.localeCompare(second.id))
    .slice(0, maximumContextFeatures);
  const candidates = [...termCandidates, ...contextCandidates];
  const termMap = (record) => new Map((record.physicsTerms || []).filter((term) => term?.id
    && Number.isFinite(term.contribution) && Number.isFinite(term.weight) && Math.abs(term.weight) > 1e-12)
    .map((term) => [term.id, term.contribution]));
  const contextMap = (record) => new Map((record.contextFeatures || []).filter((feature) => feature?.id
    && Number.isFinite(feature.value)).map((feature) => [feature.id, feature.value]));
  const candidateValue = (candidate, terms, context) => candidate.source === "structural-context"
    ? context.get(candidate.sourceId) || 0 : terms.get(candidate.sourceId) || 0;
  const rawTraining = trainingRecords.map((record) => {
    const terms = termMap(record); const context = contextMap(record);
    return candidates.map((candidate) => candidateValue(candidate, terms, context));
  });
  const means = candidates.map((_, index) => rawTraining.reduce((sum, row) => sum + row[index], 0) / rawTraining.length);
  const scales = candidates.map((_, index) => Math.sqrt(rawTraining.reduce((sum, row) =>
    sum + (row[index] - means[index]) ** 2, 0) / rawTraining.length));
  const retainedIndices = candidates.map((_, index) => index).filter((index) => scales[index] > 1e-10);
  if (!retainedIndices.length) return unavailable("earlier leap blocks contain no varying supported physics channels");
  const features = retainedIndices.map((index) => candidates[index]);
  const featureMeans = retainedIndices.map((index) => means[index]);
  const featureScales = retainedIndices.map((index) => scales[index]);
  const featureMinimums = retainedIndices.map((index) => Math.min(...rawTraining.map((row) => row[index])));
  const featureMaximums = retainedIndices.map((index) => Math.max(...rawTraining.map((row) => row[index])));
  const featureVector = (record) => {
    const terms = termMap(record); const context = contextMap(record);
    return features.map((feature) => candidateValue(feature, terms, context));
  };
  const standardize = (record) => {
    const vector = featureVector(record);
    return vector.map((value, index) => (value - featureMeans[index]) / featureScales[index]);
  };
  const xTrain = trainingRecords.map(standardize);
  const yTrain = trainingRecords.map((record) => record.outcomes[outcomeId]);
  const targetMean = yTrain.reduce((sum, value) => sum + value, 0) / yTrain.length;
  const xtx = features.map((_, row) => features.map((__, column) => xTrain.reduce((sum, sample) =>
    sum + sample[row] * sample[column], row === column ? ridge : 0)));
  const xty = features.map((_, column) => xTrain.reduce((sum, sample, index) =>
    sum + sample[column] * (yTrain[index] - targetMean), 0));
  const weights = solveRidgeSystem(xtx, xty);
  if (!weights) return unavailable("fixed-ridge system was numerically singular");
  const interactionFeatureCount = Math.min(6, features.length);
  const interactionTerms = [];
  for (let first = 0; first < interactionFeatureCount; first++) {
    interactionTerms.push({ kind: "square", first, second: first,
      id: `${features[first].id}²`, label: `${features[first].label}²` });
    for (let second = first + 1; second < interactionFeatureCount; second++) {
      interactionTerms.push({ kind: "interaction", first, second,
        id: `${features[first].id}×${features[second].id}`,
        label: `${features[first].label} × ${features[second].label}` });
    }
  }
  const rawInteraction = (standardized) => interactionTerms.map((term) =>
    standardized[term.first] * standardized[term.second]);
  const interactionMeans = interactionTerms.map((_, index) => xTrain.reduce((sum, row) =>
    sum + rawInteraction(row)[index], 0) / xTrain.length);
  const quadraticBasis = (standardized) => [...standardized,
    ...rawInteraction(standardized).map((value, index) => value - interactionMeans[index])];
  const quadraticTrain = xTrain.map(quadraticBasis);
  const quadraticSize = features.length + interactionTerms.length;
  const quadraticXtx = Array.from({ length: quadraticSize }, (_, row) =>
    Array.from({ length: quadraticSize }, (__, column) => quadraticTrain.reduce((sum, sample) =>
      sum + sample[row] * sample[column], row === column ? ridge : 0)));
  const quadraticXty = Array.from({ length: quadraticSize }, (_, column) => quadraticTrain.reduce((sum, sample, index) =>
    sum + sample[column] * (yTrain[index] - targetMean), 0));
  const quadraticWeights = solveRidgeSystem(quadraticXtx, quadraticXty);
  if (!quadraticWeights) return unavailable("fixed quadratic-ridge control was numerically singular");
  const predictions = heldoutRecords.map((record) => {
    const rawVector = featureVector(record); const vector = standardize(record);
    const standardizedExcesses = rawVector.map((value, index) => value < featureMinimums[index]
      ? (featureMinimums[index] - value) / featureScales[index]
      : value > featureMaximums[index] ? (value - featureMaximums[index]) / featureScales[index] : 0);
    const predicted = targetMean + vector.reduce((sum, value, index) => sum + value * weights[index], 0);
    const quadraticVector = quadraticBasis(vector);
    const quadraticPredicted = targetMean + quadraticVector.reduce((sum, value, index) =>
      sum + value * quadraticWeights[index], 0);
    return { placementId: record.placementId, leapIndex: record.leapIndex,
      observed: record.outcomes[outcomeId], predicted, quadraticPredicted, baseline: targetMean,
      inTrainingFeatureEnvelope: standardizedExcesses.every((value) => value <= 1e-12),
      maximumStandardizedFeatureExcess: Math.max(...standardizedExcesses) };
  });
  const errors = predictions.map((entry) => entry.predicted - entry.observed);
  const baselineErrors = predictions.map((entry) => entry.baseline - entry.observed);
  const quadraticErrors = predictions.map((entry) => entry.quadraticPredicted - entry.observed);
  const supportedPredictions = predictions.filter((entry) => entry.inTrainingFeatureEnvelope);
  const unsupportedPredictions = predictions.filter((entry) => !entry.inTrainingFeatureEnvelope);
  const subsetMae = (subset) => subset.length ? subset.reduce((sum, entry) =>
    sum + Math.abs(entry.predicted - entry.observed), 0) / subset.length : null;
  const subsetSkill = (subset) => {
    if (subset.length < minimumSamplesPerSplit) return null;
    const model = subset.reduce((sum, entry) => sum + (entry.predicted - entry.observed) ** 2, 0);
    const baseline = subset.reduce((sum, entry) => sum + (entry.baseline - entry.observed) ** 2, 0);
    return baseline > 1e-14 ? 1 - model / baseline : null;
  };
  const squared = errors.reduce((sum, error) => sum + error * error, 0);
  const baselineSquared = baselineErrors.reduce((sum, error) => sum + error * error, 0);
  const quadraticSquared = quadraticErrors.reduce((sum, error) => sum + error * error, 0);
  const predictedRanks = averageRanks(predictions.map((entry) => entry.predicted));
  const observedRanks = averageRanks(predictions.map((entry) => entry.observed));
  const quadraticPredictedRanks = averageRanks(predictions.map((entry) => entry.quadraticPredicted));
  const interpolationState = supportedPredictions.length === predictions.length ? "full-interpolation"
    : supportedPredictions.length ? "mixed-domain" : "extrapolation-only";
  const supportedSubsetSkill = subsetSkill(supportedPredictions);
  const unsupportedSubsetSkill = subsetSkill(unsupportedPredictions);
  return {
    available: true, outcomeId, trainingLeaps, heldoutLeaps,
    trainingPlacements: trainingRecords.length, heldoutPlacements: heldoutRecords.length,
    ridge, maximumFeatures, maximumContextFeatures, includeStructuralContext,
    contextFeatureIds: contextFeatureIds === null ? null : [...contextFeatureIds],
    contextFeatureScope: contextFeatureIds === null ? "all target-free creation-time state"
      : "predeclared local/intensive attachment state",
    featureSelectionRule: "physics and optional structural-context vocabularies selected separately on training support >= half; support descending then stable ID; response not inspected",
    features: features.map((term, index) => ({ id: term.id, label: term.label,
      source: term.source,
      trainingSupport: term.support, mean: rounded(featureMeans[index], 8),
      scale: rounded(featureScales[index], 8), minimum: rounded(featureMinimums[index], 8),
      maximum: rounded(featureMaximums[index], 8), standardizedWeight: rounded(weights[index], 8) })),
    trainingTargetMean: rounded(targetMean, 8),
    heldoutMeanAbsoluteError: rounded(errors.reduce((sum, error) => sum + Math.abs(error), 0) / errors.length, 8),
    baselineMeanAbsoluteError: rounded(baselineErrors.reduce((sum, error) => sum + Math.abs(error), 0) / baselineErrors.length, 8),
    heldoutRootMeanSquaredError: rounded(Math.sqrt(squared / errors.length), 8),
    baselineRootMeanSquaredError: rounded(Math.sqrt(baselineSquared / baselineErrors.length), 8),
    heldoutSkillVersusTrainingMean: baselineSquared > 1e-14 ? rounded(1 - squared / baselineSquared, 8) : null,
    heldoutSpearman: rounded(pearson(predictedRanks, observedRanks), 8),
    quadraticControl: {
      role: "predeclared second-order channel-coupling control; not selected on held blocks",
      baseFeatureCount: features.length,
      interactionFeatureCount,
      basisTerms: quadraticSize,
      maximumInteractingBaseFeatures: 6,
      ridge,
      coefficients: [...features.map((term, index) => ({ id: term.id, label: term.label,
        kind: "linear", standardizedWeight: rounded(quadraticWeights[index], 8) })),
      ...interactionTerms.map((term, index) => ({ id: term.id, label: term.label, kind: term.kind,
        trainingMean: rounded(interactionMeans[index], 8),
        standardizedWeight: rounded(quadraticWeights[features.length + index], 8) }))],
      heldoutMeanAbsoluteError: rounded(quadraticErrors.reduce((sum, error) => sum + Math.abs(error), 0)
        / quadraticErrors.length, 8),
      heldoutRootMeanSquaredError: rounded(Math.sqrt(quadraticSquared / quadraticErrors.length), 8),
      heldoutSkillVersusTrainingMean: baselineSquared > 1e-14
        ? rounded(1 - quadraticSquared / baselineSquared, 8) : null,
      heldoutSpearman: rounded(pearson(quadraticPredictedRanks, observedRanks), 8),
      modelSelectedUsingHeldout: false,
      fitUsedHeldout: false,
      featureSelectionUsedOutcome: false,
    },
    heldoutFeatureSupportCoverage: rounded(supportedPredictions.length / predictions.length, 8),
    supportedHeldoutPlacements: supportedPredictions.length,
    unsupportedHeldoutPlacements: unsupportedPredictions.length,
    supportedHeldoutMeanAbsoluteError: rounded(subsetMae(supportedPredictions), 8),
    unsupportedHeldoutMeanAbsoluteError: rounded(subsetMae(unsupportedPredictions), 8),
    supportedHeldoutSkillVersusTrainingMean: rounded(supportedSubsetSkill, 8),
    unsupportedHeldoutSkillVersusTrainingMean: rounded(unsupportedSubsetSkill, 8),
    interpolationReadiness: {
      state: interpolationState,
      aggregateSkillIsInterpolationTest: interpolationState === "full-interpolation",
      supportedSubsetSkillAvailable: Number.isFinite(supportedSubsetSkill),
      minimumSupportedPlacementsForSubsetSkill: minimumSamplesPerSplit,
      supportedPlacements: supportedPredictions.length,
      unsupportedPlacements: unsupportedPredictions.length,
      featureEnvelopeChosenUsingHeldout: false,
      interpretation: interpolationState === "full-interpolation"
        ? "aggregate held-block skill is entirely inside the earlier-block feature envelope"
        : interpolationState === "mixed-domain"
          ? "aggregate skill mixes interpolation and extrapolation; use the supported-only result only when its sample gate passes"
          : "aggregate held-block skill is extrapolation-only and is not an interpolation test",
    },
    maximumStandardizedFeatureExcess: rounded(Math.max(...predictions
      .map((entry) => entry.maximumStandardizedFeatureExcess)), 8),
    featureSupportDefinition: "axis-aligned min/max envelope of earlier-block active score contributions and any enabled target-free structural context; normalized excess uses earlier-block scale",
    predictions: predictions.map((entry) => ({ ...entry, predicted: rounded(entry.predicted, 8),
      quadraticPredicted: rounded(entry.quadraticPredicted, 8),
      observed: rounded(entry.observed, 8), baseline: rounded(entry.baseline, 8),
      maximumStandardizedFeatureExcess: rounded(entry.maximumStandardizedFeatureExcess, 8) })),
    fitBlockedByCompleteStructuralLeap: true, randomSplitUsed: false,
    fitUsedHeldout: false, featureSelectionUsedOutcome: false, targetUsed: false,
    causalEffectInferred: false, independentMaterialSamples: false,
    physicalTimeModeled: false, calibratedMaterialForecastClaimed: false,
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
