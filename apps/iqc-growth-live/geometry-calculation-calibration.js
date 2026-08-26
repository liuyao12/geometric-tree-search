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
