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
  const featureScales = featureKeys.map((key, feature) => {
    const variance = mean(rows.map((row) => (row.record[key] - featureMeans[feature]) ** 2));
    return Math.sqrt(variance) > 1e-12 ? Math.sqrt(variance) : 1;
  });
  const targetMean = mean(rows.map((row) => row.record[targetKey]));
  const normalized = rows.map(({ record }) => featureKeys.map((key, feature) =>
    (record[key] - featureMeans[feature]) / featureScales[feature]));
  const matrix = featureKeys.map((_, first) => featureKeys.map((__, second) =>
    normalized.reduce((sum, row) => sum + row[first] * row[second], 0) + (first === second ? ridge : 0)));
  const vector = featureKeys.map((_, feature) => normalized.reduce((sum, row, index) =>
    sum + row[feature] * (rows[index].record[targetKey] - targetMean), 0));
  const coefficients = solveLinearSystem(matrix, vector);
  if (!coefficients) return null;
  return {
    featureMeans, featureScales, standardizedCoefficients: coefficients, targetMean,
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
      standardizedCoefficients: fullModel.standardizedCoefficients,
      targetMean: fullModel.targetMean,
    },
  };
}
