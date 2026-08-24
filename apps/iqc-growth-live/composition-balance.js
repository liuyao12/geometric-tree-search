function greatestCommonDivisor(first, second) {
  let a = Math.abs(first), b = Math.abs(second);
  while (b) [a, b] = [b, a % b];
  return a || 1;
}

function countSpecies(species) {
  const counts = new Map();
  species.forEach((symbol) => counts.set(symbol, (counts.get(symbol) || 0) + 1));
  return counts;
}

/** Learn an arbitrary-component composition target without oxidation states. */
export function learnCompositionTarget(species) {
  if (!Array.isArray(species) || !species.length) throw new Error("composition target requires species");
  const counts = countSpecies(species);
  const symbols = [...counts.keys()].sort();
  const divisor = symbols.map((symbol) => counts.get(symbol)).reduce(greatestCommonDivisor);
  return {
    symbols,
    counts: Object.fromEntries(symbols.map((symbol) => [symbol, counts.get(symbol)])),
    fractions: Object.fromEntries(symbols.map((symbol) => [symbol, counts.get(symbol) / species.length])),
    reducedRatio: Object.fromEntries(symbols.map((symbol) => [symbol, counts.get(symbol) / divisor])),
    observations: species.length,
  };
}

export function compositionDrift(species, target) {
  if (!species.length) return { totalVariation: 0, maximumFractionError: 0, fractions: {} };
  const counts = countSpecies(species);
  const symbols = [...new Set([...target.symbols, ...counts.keys()])].sort();
  const fractions = Object.fromEntries(symbols.map((symbol) => [symbol, (counts.get(symbol) || 0) / species.length]));
  const errors = symbols.map((symbol) => Math.abs(fractions[symbol] - (target.fractions[symbol] || 0)));
  return {
    totalVariation: .5 * errors.reduce((sum, value) => sum + value, 0),
    maximumFractionError: Math.max(...errors),
    fractions,
  };
}

/**
 * Report whether one exact action moves a finite frontier toward or away from
 * the observed reservoir composition. The square-root size scaling keeps the
 * soft signal visible without turning a surface fluctuation into a hard law.
 */
export function compositionBalanceDelta(currentSpecies, freshSpecies, target) {
  const before = compositionDrift(currentSpecies, target);
  const projectedSpecies = [...currentSpecies, ...freshSpecies];
  const after = compositionDrift(projectedSpecies, target);
  return {
    before: before.totalVariation,
    after: after.totalVariation,
    delta: after.totalVariation - before.totalVariation,
    scaledDelta: (after.totalVariation - before.totalVariation) * Math.sqrt(Math.max(1, projectedSpecies.length)),
    maximumFractionError: after.maximumFractionError,
    projectedFractions: after.fractions,
    added: freshSpecies.length,
  };
}
