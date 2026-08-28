export function finiteStateContrast(samples, { minimumPerGroup = 3 } = {}) {
  if (!Number.isInteger(minimumPerGroup) || minimumPerGroup < 1) {
    throw new Error("minimumPerGroup must be a positive integer");
  }
  if (!Array.isArray(samples)) throw new Error("samples must be an array");
  const valid = samples.filter((sample) => Number.isFinite(sample?.value)
    && typeof sample?.changed === "boolean");
  const changedValues = valid.filter((sample) => sample.changed).map((sample) => sample.value);
  const stableValues = valid.filter((sample) => !sample.changed).map((sample) => sample.value);
  const mean = (values) => values.reduce((sum, value) => sum + value, 0) / values.length;
  const changedMean = changedValues.length ? mean(changedValues) : null;
  const stableMean = stableValues.length ? mean(stableValues) : null;
  const difference = changedMean !== null && stableMean !== null ? changedMean - stableMean : null;
  const values = valid.map((sample) => sample.value);
  const observedMinimum = values.length ? Math.min(...values) : null;
  const observedMaximum = values.length ? Math.max(...values) : null;
  const observedRange = observedMinimum !== null ? observedMaximum - observedMinimum : null;
  const normalizedDifference = difference !== null && observedRange > 1e-12
    ? Math.max(-1, Math.min(1, difference / observedRange)) : difference !== null ? 0 : null;
  return {
    sampleCount: valid.length,
    changedCount: changedValues.length,
    stableCount: stableValues.length,
    changedMean,
    stableMean,
    difference,
    observedMinimum,
    observedMaximum,
    observedRange,
    normalizedDifference,
    resolved: changedValues.length >= minimumPerGroup && stableValues.length >= minimumPerGroup,
    supportNeeded: {
      changed: Math.max(0, minimumPerGroup - changedValues.length),
      stable: Math.max(0, minimumPerGroup - stableValues.length),
    },
  };
}
