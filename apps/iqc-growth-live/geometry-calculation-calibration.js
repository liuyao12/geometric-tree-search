function finitePairs(records, xKey, yKey) {
  return records.map((record) => ({ x: record[xKey], y: record[yKey] }))
    .filter(({ x, y }) => Number.isFinite(x) && Number.isFinite(y));
}

/** Geometry-only reference selection. Calculation labels are deliberately not
 * accepted by this API, so they cannot select a reference frame. */
export function geometryReferenceIndices(frameCount, requestedMode = "final") {
  if (!Number.isInteger(frameCount) || frameCount < 1) throw new Error("reference selection requires frames");
  const mode = ["final", "first", "pooled"].includes(requestedMode) ? requestedMode : "final";
  return mode === "pooled" ? Array.from({ length: frameCount }, (_, index) => index)
    : [mode === "first" ? 0 : frameCount - 1];
}

function mean(values) {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length);
}

function pearsonFromPairs(pairs) {
  if (pairs.length < 3) return null;
  const meanX = mean(pairs.map(({ x }) => x));
  const meanY = mean(pairs.map(({ y }) => y));
  let covariance = 0; let varianceX = 0; let varianceY = 0;
  pairs.forEach(({ x, y }) => {
    covariance += (x - meanX) * (y - meanY);
    varianceX += (x - meanX) ** 2; varianceY += (y - meanY) ** 2;
  });
  return varianceX > 1e-24 && varianceY > 1e-24
    ? Math.max(-1, Math.min(1, covariance / Math.sqrt(varianceX * varianceY))) : null;
}

function averageRanks(values) {
  const ordered = values.map((value, index) => ({ value, index }))
    .sort((first, second) => first.value - second.value || first.index - second.index);
  const ranks = new Array(values.length);
  for (let start = 0; start < ordered.length;) {
    let end = start + 1;
    while (end < ordered.length && ordered[end].value === ordered[start].value) end++;
    const rank = (start + end - 1) / 2 + 1;
    for (let index = start; index < end; index++) ranks[ordered[index].index] = rank;
    start = end;
  }
  return ranks;
}

/** Descriptive correlation/regression for one already supplied calculation
 * sequence. It does not claim independent samples, prediction, or causality. */
export function geometryCalculationCalibration(records, xKey, yKey) {
  if (!Array.isArray(records) || !xKey || !yKey) throw new Error("calibration requires records and named fields");
  const pairs = finitePairs(records, xKey, yKey);
  const pearson = pearsonFromPairs(pairs);
  const xRanks = averageRanks(pairs.map(({ x }) => x));
  const yRanks = averageRanks(pairs.map(({ y }) => y));
  const spearman = pearsonFromPairs(pairs.map((_, index) => ({ x: xRanks[index], y: yRanks[index] })));
  const meanX = mean(pairs.map(({ x }) => x)); const meanY = mean(pairs.map(({ y }) => y));
  const varianceX = pairs.reduce((sum, { x }) => sum + (x - meanX) ** 2, 0);
  const covariance = pairs.reduce((sum, { x, y }) => sum + (x - meanX) * (y - meanY), 0);
  const slope = pairs.length >= 3 && varianceX > 1e-24 ? covariance / varianceX : null;
  const intercept = slope === null ? null : meanY - slope * meanX;
  return {
    xKey, yKey, pairedFrames: pairs.length, pearson, spearman, slope, intercept,
    rSquared: pearson === null ? null : pearson * pearson,
    descriptiveOnly: true,
    independentSamplesClaimed: false,
    predictiveValidationPerformed: false,
    physicalCausalityClaimed: false,
  };
}

function solveLinearSystem(matrix, vector) {
  const size = vector.length;
  const augmented = matrix.map((row, index) => [...row, vector[index]]);
  for (let column = 0; column < size; column++) {
    let pivot = column;
    for (let row = column + 1; row < size; row++) {
      if (Math.abs(augmented[row][column]) > Math.abs(augmented[pivot][column])) pivot = row;
    }
    if (Math.abs(augmented[pivot][column]) < 1e-12) return null;
    [augmented[column], augmented[pivot]] = [augmented[pivot], augmented[column]];
    const scale = augmented[column][column];
    for (let index = column; index <= size; index++) augmented[column][index] /= scale;
    for (let row = 0; row < size; row++) {
      if (row === column) continue;
      const factor = augmented[row][column];
      for (let index = column; index <= size; index++) augmented[row][index] -= factor * augmented[column][index];
    }
  }
  return augmented.map((row) => row[size]);
}

function fitStandardizedRidge(rows, featureKeys, targetKey, ridge) {
  const featureMeans = featureKeys.map((key) => mean(rows.map((row) => row.record[key])));
  const featureMinimums = featureKeys.map((key) => Math.min(...rows.map((row) => row.record[key])));
  const featureMaximums = featureKeys.map((key) => Math.max(...rows.map((row) => row.record[key])));
  const featureScales = featureKeys.map((key, feature) => {
    const variance = mean(rows.map((row) => (row.record[key] - featureMeans[feature]) ** 2));
    return Math.sqrt(variance) > 1e-12 ? Math.sqrt(variance) : 1;
  });
  const targetMean = mean(rows.map((row) => row.record[targetKey]));
  const targetScale = Math.sqrt(mean(rows.map((row) => (row.record[targetKey] - targetMean) ** 2))) || 1;
  const normalized = rows.map(({ record }) => featureKeys.map((key, feature) =>
    (record[key] - featureMeans[feature]) / featureScales[feature]));
  const matrix = featureKeys.map((_, first) => featureKeys.map((__, second) =>
    normalized.reduce((sum, row) => sum + row[first] * row[second], 0) + (first === second ? ridge : 0)));
  const vector = featureKeys.map((_, feature) => normalized.reduce((sum, row, index) =>
    sum + row[feature] * (rows[index].record[targetKey] - targetMean), 0));
  const coefficients = solveLinearSystem(matrix, vector);
  if (!coefficients) return null;
  return {
    featureMeans, featureScales, featureMinimums, featureMaximums,
    standardizedCoefficients: coefficients, targetMean, targetScale,
    predict: (record) => targetMean + coefficients.reduce((sum, coefficient, feature) =>
      sum + coefficient * (record[featureKeys[feature]] - featureMeans[feature]) / featureScales[feature], 0),
  };
}

/** Fixed low-capacity geometry-to-calculation preflight. Every prediction is
 * leave-one-frame-out, but frames from one archive remain correlated and are
 * not claimed as independent validation. */
export function geometryCalculationSurrogate(records, featureKeys, targetKey, {
  ridge = 1,
  minimumPairs = 5,
} = {}) {
  if (!Array.isArray(records) || !Array.isArray(featureKeys) || !featureKeys.length || !targetKey) {
    throw new Error("surrogate requires records, geometric feature names, and a calculation target");
  }
  if (!(Number.isFinite(ridge) && ridge > 0) || !Number.isInteger(minimumPairs) || minimumPairs < 3) {
    throw new Error("surrogate ridge and minimum pair count must be fixed positive values");
  }
  const rows = records.map((record, recordIndex) => ({ record, recordIndex }))
    .filter(({ record }) => featureKeys.every((key) => Number.isFinite(record[key]))
      && Number.isFinite(record[targetKey]));
  const requiredPairs = Math.max(minimumPairs, featureKeys.length + 2);
  const base = {
    featureKeys: [...featureKeys], targetKey, pairedFrames: rows.length, requiredPairs, ridge,
    crossValidationKind: "leave-one-frame-out",
    calculationLabelsUsedForSurrogateFit: true,
    geometryEnvelopeFitUsesCalculationLabels: false,
    correlatedArchiveFrames: true,
    independentValidationClaimed: false,
    physicalCausalityClaimed: false,
    usedForGrowth: false,
  };
  if (rows.length < requiredPairs) return { ...base, available: false, reason: "insufficient paired frames" };
  const predictions = [];
  for (let heldout = 0; heldout < rows.length; heldout++) {
    const training = rows.filter((_, index) => index !== heldout);
    const model = fitStandardizedRidge(training, featureKeys, targetKey, ridge);
    if (!model) return { ...base, available: false, reason: "singular geometric design" };
    predictions.push({
      recordIndex: rows[heldout].recordIndex,
      observed: rows[heldout].record[targetKey],
      predicted: model.predict(rows[heldout].record),
    });
  }
  const fullModel = fitStandardizedRidge(rows, featureKeys, targetKey, ridge);
  const residuals = predictions.map((prediction) => prediction.predicted - prediction.observed);
  const observedMean = mean(predictions.map((prediction) => prediction.observed));
  const squaredError = residuals.reduce((sum, value) => sum + value * value, 0);
  const totalSquares = predictions.reduce((sum, prediction) => sum
    + (prediction.observed - observedMean) ** 2, 0);
  const association = geometryCalculationCalibration(predictions, "predicted", "observed");
  return {
    ...base, available: true, predictions,
    meanAbsoluteError: mean(residuals.map(Math.abs)),
    rootMeanSquaredError: Math.sqrt(mean(residuals.map((value) => value * value))),
    crossValidatedQSquared: totalSquares > 1e-24 ? 1 - squaredError / totalSquares : null,
    predictionPearson: association.pearson,
    predictionSpearman: association.spearman,
    fullModel: {
      featureMeans: fullModel.featureMeans,
      featureScales: fullModel.featureScales,
      featureMinimums: fullModel.featureMinimums,
      featureMaximums: fullModel.featureMaximums,
      standardizedCoefficients: fullModel.standardizedCoefficients,
      targetMean: fullModel.targetMean,
      targetScale: fullModel.targetScale,
    },
  };
}

export function frozenGeometrySurrogateArtifact(surrogate) {
  if (!surrogate?.available || !surrogate.fullModel) throw new Error("only an available fitted surrogate can be frozen");
  return {
    schema: "gcts-frozen-geometry-calculation-surrogate-v3",
    featureKeys: [...surrogate.featureKeys], targetKey: surrogate.targetKey,
    ridge: surrogate.ridge, sourcePairedFrames: surrogate.pairedFrames,
    featureMeans: [...surrogate.fullModel.featureMeans],
    featureScales: [...surrogate.fullModel.featureScales],
    featureMinimums: [...surrogate.fullModel.featureMinimums],
    featureMaximums: [...surrogate.fullModel.featureMaximums],
    standardizedCoefficients: [...surrogate.fullModel.standardizedCoefficients],
    targetMean: surrogate.fullModel.targetMean,
    targetScale: surrogate.fullModel.targetScale,
    geometryOnlyAtEvaluation: true,
  };
}

function validateFrozenArtifact(artifact) {
  const supportedSchema = artifact?.schema === "gcts-frozen-geometry-calculation-surrogate-v1"
    || artifact?.schema === "gcts-frozen-geometry-calculation-surrogate-v2"
    || artifact?.schema === "gcts-frozen-geometry-calculation-surrogate-v3";
  if (!supportedSchema || !Array.isArray(artifact.featureKeys) || !artifact.featureKeys.length
      || !Array.isArray(artifact.featureMeans) || !Array.isArray(artifact.featureScales)
      || !Array.isArray(artifact.standardizedCoefficients)
      || [artifact.featureMeans, artifact.featureScales, artifact.standardizedCoefficients]
        .some((values) => values.length !== artifact.featureKeys.length)
      || !artifact.featureMeans.every(Number.isFinite) || !artifact.featureScales.every((value) => value > 0)
      || !artifact.standardizedCoefficients.every(Number.isFinite) || !Number.isFinite(artifact.targetMean)
      || (!artifact.schema.endsWith("-v1") && !(Number.isFinite(artifact.targetScale) && artifact.targetScale > 0))
      || (artifact.schema.endsWith("-v3") && (!Array.isArray(artifact.featureMinimums)
        || !Array.isArray(artifact.featureMaximums)
        || artifact.featureMinimums.length !== artifact.featureKeys.length
        || artifact.featureMaximums.length !== artifact.featureKeys.length
        || !artifact.featureMinimums.every(Number.isFinite)
        || !artifact.featureMaximums.every(Number.isFinite)
        || artifact.featureMinimums.some((value, index) => value > artifact.featureMaximums[index])))) {
    throw new Error("invalid frozen geometry surrogate artifact");
  }
}

export const GEOMETRY_SURROGATE_SUPPORT_MARGIN_STANDARD_DEVIATIONS = .25;

/** Frozen axis-aligned source support with a small predeclared numerical margin.
 * This is an abstention boundary, not a probability or uncertainty estimate. */
export function frozenGeometryFeatureSupport(record, artifact) {
  validateFrozenArtifact(artifact);
  if (!artifact.schema.endsWith("-v3")) return {
    available: false, inSupport: false, reason: "artifact lacks frozen source feature bounds",
    maximumStandardizedExcess: null,
  };
  if (!record || !artifact.featureKeys.every((key) => Number.isFinite(record[key]))) {
    throw new Error("feature-support audit requires every geometric feature");
  }
  const excesses = artifact.featureKeys.map((key, feature) => {
    const margin = GEOMETRY_SURROGATE_SUPPORT_MARGIN_STANDARD_DEVIATIONS * artifact.featureScales[feature];
    const lower = artifact.featureMinimums[feature] - margin;
    const upper = artifact.featureMaximums[feature] + margin;
    return record[key] < lower ? (lower - record[key]) / artifact.featureScales[feature]
      : record[key] > upper ? (record[key] - upper) / artifact.featureScales[feature] : 0;
  });
  const maximumStandardizedExcess = Math.max(...excesses);
  return { available: true, inSupport: maximumStandardizedExcess <= 1e-12,
    maximumStandardizedExcess, featureExcesses: excesses,
    marginStandardDeviations: GEOMETRY_SURROGATE_SUPPORT_MARGIN_STANDARD_DEVIATIONS,
    axisAlignedBoundingBox: true, uncertaintyProbabilityClaimed: false };
}

/** Predict from geometry alone with an already frozen archive artifact. */
export function predictFrozenGeometrySurrogate(record, artifact) {
  validateFrozenArtifact(artifact);
  if (!record || !artifact.featureKeys.every((key) => Number.isFinite(record[key]))) {
    throw new Error("frozen geometry surrogate prediction requires every geometric feature");
  }
  return artifact.targetMean + artifact.standardizedCoefficients.reduce((sum, coefficient, feature) =>
    sum + coefficient * (record[artifact.featureKeys[feature]] - artifact.featureMeans[feature])
      / artifact.featureScales[feature], 0);
}

export const GEOMETRY_SURROGATE_PROMOTION_GATE = Object.freeze({
  minimumTargetFrames: 5,
  minimumSupportedTargetFrames: 5,
  minimumFeatureSupportCoverage: .8,
  minimumPredictionSpearman: .8,
  minimumPredictiveQSquared: 0,
});

/** A predeclared, no-refit cross-archive gate. Passing makes the artifact
 * eligible for opt-in ranking; it does not validate a potential or kinetics. */
export function assessGeometrySurrogatePromotion(transfer) {
  const checks = {
    frozenEvaluationAvailable: Boolean(transfer?.available),
    noRefit: transfer?.refitPerformed === false,
    predictionDidNotUseTargetValues: transfer?.targetValuesUsedForPrediction === false,
    enoughTargetFrames: Number.isInteger(transfer?.pairedFrames)
      && transfer.pairedFrames >= GEOMETRY_SURROGATE_PROMOTION_GATE.minimumTargetFrames,
    enoughSupportedTargetFrames: Number.isInteger(transfer?.supportedFrames)
      && transfer.supportedFrames >= GEOMETRY_SURROGATE_PROMOTION_GATE.minimumSupportedTargetFrames,
    featureSupportTransfer: Number.isFinite(transfer?.featureSupportCoverage)
      && transfer.featureSupportCoverage >= GEOMETRY_SURROGATE_PROMOTION_GATE.minimumFeatureSupportCoverage,
    rankTransfer: Number.isFinite(transfer?.predictionSpearman)
      && transfer.predictionSpearman >= GEOMETRY_SURROGATE_PROMOTION_GATE.minimumPredictionSpearman,
    positivePredictiveSkill: Number.isFinite(transfer?.predictiveQSquared)
      && transfer.predictiveQSquared > GEOMETRY_SURROGATE_PROMOTION_GATE.minimumPredictiveQSquared,
  };
  const failedChecks = Object.entries(checks).filter(([, passed]) => !passed).map(([name]) => name);
  return {
    eligible: failedChecks.length === 0,
    checks,
    failedChecks,
    thresholds: { ...GEOMETRY_SURROGATE_PROMOTION_GATE },
    role: "eligibility gate for an opt-in soft ranking hypothesis over an unchanged candidate set",
    physicalPotentialValidated: false,
    kineticsValidated: false,
  };
}

/** Lower predicted target values are preferred. The source-target standard
 * deviation makes this dimensionless and the clamp prevents one fitted model
 * from overwhelming the structural grammar. */
export function frozenGeometrySurrogatePreference(record, artifact) {
  validateFrozenArtifact(artifact);
  if (!(Number.isFinite(artifact.targetScale) && artifact.targetScale > 0)) {
    throw new Error("dimensionless growth preference requires a v2 artifact target scale");
  }
  const predicted = predictFrozenGeometrySurrogate(record, artifact);
  const support = frozenGeometryFeatureSupport(record, artifact);
  const standardized = (artifact.targetMean - predicted) / artifact.targetScale;
  return { predicted, standardized, score: support.inSupport ? Math.max(-3, Math.min(3, standardized)) : 0,
    featureSupport: support, inFeatureSupport: support.inSupport, abstained: !support.inSupport,
    lowerPredictedTargetPreferred: true, hardAdmissionChanged: false, candidateGeometryChanged: false };
}

/** Score a separately supplied archive with one already frozen artifact. No
 * target value participates in prediction and no coefficient is refitted. */
export function evaluateFrozenGeometrySurrogate(records, artifact) {
  validateFrozenArtifact(artifact);
  const rows = records.map((record, recordIndex) => ({ record, recordIndex }))
    .filter(({ record }) => artifact.featureKeys.every((key) => Number.isFinite(record[key]))
      && Number.isFinite(record[artifact.targetKey]));
  const predictions = rows.map(({ record, recordIndex }) => ({
    recordIndex,
    observed: record[artifact.targetKey],
    predicted: predictFrozenGeometrySurrogate(record, artifact),
    featureSupport: frozenGeometryFeatureSupport(record, artifact),
  }));
  if (!predictions.length) return {
    available: false, reason: "no compatible target pairs", pairedFrames: 0,
    refitPerformed: false, targetValuesUsedForPrediction: false,
  };
  const residuals = predictions.map((prediction) => prediction.predicted - prediction.observed);
  const observedMean = mean(predictions.map((prediction) => prediction.observed));
  const squaredError = residuals.reduce((sum, value) => sum + value * value, 0);
  const totalSquares = predictions.reduce((sum, prediction) => sum
    + (prediction.observed - observedMean) ** 2, 0);
  const association = geometryCalculationCalibration(predictions, "predicted", "observed");
  const supportedFrames = predictions.filter((prediction) => prediction.featureSupport.inSupport).length;
  return {
    available: true, pairedFrames: predictions.length, predictions,
    supportedFrames, featureSupportCoverage: supportedFrames / predictions.length,
    meanAbsoluteError: mean(residuals.map(Math.abs)),
    rootMeanSquaredError: Math.sqrt(mean(residuals.map((value) => value * value))),
    predictionPearson: association.pearson,
    predictionSpearman: association.spearman,
    predictiveQSquared: totalSquares > 1e-24 ? 1 - squaredError / totalSquares : null,
    refitPerformed: false,
    targetValuesUsedForPrediction: false,
    targetValuesUsedForPosthocScoring: true,
    physicalCausalityClaimed: false,
    usedForGrowth: false,
  };
}

export const GEOMETRY_SURROGATE_COMPATIBILITY_FIELDS = Object.freeze([
  "targetMode", "targetKey", "referenceMode", "featureSchema", "reducedComposition",
  "periodicAxes", "programName", "programVersion", "methodCanonicalJson", "energyUnit", "forceUnit",
]);

export function geometrySurrogateCompatibilityKey(record) {
  if (!record || GEOMETRY_SURROGATE_COMPATIBILITY_FIELDS.some((field) =>
    record[field] === null || record[field] === undefined || record[field] === "")) {
    throw new Error("complete geometry surrogate provenance is required");
  }
  return JSON.stringify(Object.fromEntries(GEOMETRY_SURROGATE_COMPATIBILITY_FIELDS
    .map((field) => [field, record[field]])));
}

export function geometrySurrogateCompatibilityDifferences(source, target) {
  return GEOMETRY_SURROGATE_COMPATIBILITY_FIELDS.filter((field) => source?.[field] !== target?.[field]);
}
