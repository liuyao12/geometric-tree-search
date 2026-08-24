function pairKey(first, second) {
  return first < second ? `${first}|${second}` : `${second}|${first}`;
}

function quantile(sorted, fraction) {
  if (!sorted.length) return 0;
  return sorted[Math.min(sorted.length - 1, Math.max(0, Math.floor((sorted.length - 1) * fraction)))];
}

/**
 * Learn species-pair geometric contact/exclusion envelopes from one observed
 * colored point set.  The exclusion lies strictly below the shortest observed
 * contact, so the input is preserved exactly; the nearest-by-species
 * distribution supplies a more robust typical-contact audit.  These are hard
 * geometric constraints, not a fitted pair potential or an energy surface.
 */
export function learnColoredDistanceEnvelopes(species, distance, {
  minimumContactFraction = .88,
  lowerContactFraction = .80,
  lowerQuantile = .05,
  fallbackExclusion = .46,
} = {}) {
  if (!Array.isArray(species) || species.length < 2) throw new Error("colored envelopes require at least two atoms");
  if (typeof distance !== "function") throw new Error("colored envelopes require a distance callback");
  if (![minimumContactFraction, lowerContactFraction, lowerQuantile, fallbackExclusion].every(Number.isFinite)
    || !(minimumContactFraction > 0 && minimumContactFraction < 1)
    || !(lowerContactFraction > 0 && lowerContactFraction < 1)
    || !(lowerQuantile >= 0 && lowerQuantile <= 1)
    || !(fallbackExclusion > 0)) throw new Error("colored envelope fractions and fallback must be finite positive bounds");
  const symbols = [...new Set(species)].sort();
  const allDistances = new Map();
  const nearest = Array.from({ length: species.length }, () => new Map(symbols.map((symbol) => [symbol, Infinity])));
  for (let first = 0; first < species.length; first++) for (let second = first + 1; second < species.length; second++) {
    const value = distance(first, second);
    if (!(value > 1e-9) || !Number.isFinite(value)) continue;
    const key = pairKey(species[first], species[second]);
    const values = allDistances.get(key) || [];
    values.push(value);
    allDistances.set(key, values);
    nearest[first].set(species[second], Math.min(nearest[first].get(species[second]), value));
    nearest[second].set(species[first], Math.min(nearest[second].get(species[first]), value));
  }
  const records = [];
  for (let first = 0; first < symbols.length; first++) for (let second = first; second < symbols.length; second++) {
    const key = pairKey(symbols[first], symbols[second]);
    const values = (allDistances.get(key) || []).slice().sort((a, b) => a - b);
    if (!values.length) continue;
    const nearestValues = nearest.flatMap((row, atomIndex) => {
      const own = species[atomIndex];
      if (own !== symbols[first] && own !== symbols[second]) return [];
      const other = own === symbols[first] ? symbols[second] : symbols[first];
      const value = row.get(other);
      return Number.isFinite(value) ? [value] : [];
    }).sort((a, b) => a - b);
    const minimumObserved = values[0];
    const lowerContact = quantile(nearestValues, lowerQuantile) || minimumObserved;
    const typicalContact = quantile(nearestValues, .5) || lowerContact;
    const exclusion = Math.min(minimumObserved * minimumContactFraction,
      lowerContact * lowerContactFraction);
    records.push({
      key,
      species: [symbols[first], symbols[second]],
      minimumObserved,
      lowerContact,
      typicalContact,
      exclusion,
      pairObservations: values.length,
      nearestObservations: nearestValues.length,
    });
  }
  const byKey = Object.fromEntries(records.map((record) => [record.key, record]));
  return {
    records,
    byKey,
    fallbackExclusion,
    maximumExclusion: Math.max(fallbackExclusion, ...records.map((record) => record.exclusion)),
    config: { minimumContactFraction, lowerContactFraction, lowerQuantile },
    pairKey,
  };
}

export function exclusionForPair(model, first, second) {
  return model?.byKey?.[pairKey(first, second)]?.exclusion ?? model?.fallbackExclusion ?? .46;
}
