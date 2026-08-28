export function channelValidationMetricsFromCounts(confusion) {
  const ratio = (numerator, denominator) => denominator ? numerator / denominator : null;
  const precision = ratio(confusion.tp, confusion.tp + confusion.fp);
  const recall = ratio(confusion.tp, confusion.tp + confusion.fn);
  const specificity = ratio(confusion.tn, confusion.tn + confusion.fp);
  const labels = confusion.tp + confusion.fp + confusion.fn + confusion.tn;
  return {
    labels,
    accuracy: ratio(confusion.tp + confusion.tn, labels),
    precision,
    recall,
    specificity,
    balancedAccuracy: Number.isFinite(recall) && Number.isFinite(specificity)
      ? .5 * (recall + specificity) : null,
  };
}

export function validationOccurrenceJackknife(records) {
  const sampleIndices = [...new Set(records.map((record) => record.sampleIndex))].sort((a, b) => a - b);
  const metricsFor = (selected) => {
    const confusion = selected.reduce((counts, record) => {
      const key = record.observedCompatible
        ? record.predictedCompatible ? "tp" : "fn"
        : record.predictedCompatible ? "fp" : "tn";
      counts[key]++;
      return counts;
    }, { tp: 0, fp: 0, fn: 0, tn: 0 });
    return channelValidationMetricsFromCounts(confusion);
  };
  const estimate = metricsFor(records).balancedAccuracy;
  const replicates = sampleIndices.map((excluded) => metricsFor(records
    .filter((record) => record.sampleIndex !== excluded)).balancedAccuracy).filter(Number.isFinite);
  const mean = replicates.reduce((sum, value) => sum + value, 0) / Math.max(1, replicates.length);
  const variance = replicates.length >= 2
    ? (replicates.length - 1) / replicates.length
      * replicates.reduce((sum, value) => sum + (value - mean) ** 2, 0)
    : null;
  const standardError = Number.isFinite(variance) ? Math.sqrt(variance) : null;
  const lower = Number.isFinite(estimate) && Number.isFinite(standardError)
    ? Math.max(0, estimate - 1.96 * standardError) : null;
  const upper = Number.isFinite(estimate) && Number.isFinite(standardError)
    ? Math.min(1, estimate + 1.96 * standardError) : null;
  return {
    method: "delete-one-heldout-occurrence jackknife",
    nominalCoverage: .95,
    occurrenceBlocks: sampleIndices.length,
    sectorLabels: records.length,
    finiteReplicates: replicates.length,
    estimate,
    standardError,
    lower,
    upper,
    groupingUnit: "cluster occurrence; channel sectors within an occurrence remain correlated",
    interpretation: "descriptive occurrence-block sensitivity; not an independent-material population confidence interval",
  };
}
