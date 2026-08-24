function mean(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}

function dot(first, second) {
  return first.reduce((sum, value, index) => sum + value * second[index], 0);
}

function cross(first, second) {
  return [
    first[1] * second[2] - first[2] * second[1],
    first[2] * second[0] - first[0] * second[2],
    first[0] * second[1] - first[1] * second[0],
  ];
}

function norm(vector) {
  return Math.hypot(...vector);
}

/**
 * A permutation-invariant pseudoscalar of a colored local connection.
 * Tokens must contain only proper-rotation invariants (species, radii, and
 * internal distances). Equal-token pairs are omitted because their ordering
 * is symmetry-degenerate. The result is invariant under translation and
 * proper rotation and changes sign under a mirror.
 */
export function coloredConnectionChirality(translation, sites) {
  const translationNorm = norm(translation);
  if (!(translationNorm > 1e-12) || sites.length < 2) return 0;
  const ordered = sites.slice().sort((first, second) => first.token.localeCompare(second.token));
  const terms = [];
  for (let first = 0; first < ordered.length - 1; first++) {
    for (let second = first + 1; second < ordered.length; second++) {
      if (ordered[first].token === ordered[second].token) continue;
      const firstNorm = norm(ordered[first].vector);
      const secondNorm = norm(ordered[second].vector);
      if (!(firstNorm > 1e-12 && secondNorm > 1e-12)) continue;
      terms.push(dot(translation, cross(ordered[first].vector, ordered[second].vector))
        / (translationNorm * firstNorm * secondNorm));
    }
  }
  return Math.max(-1, Math.min(1, mean(terms)));
}

/** Aggregate the same frozen candidate through genuinely different readouts. */
export function aggregateMarkingReadout({
  representation,
  forward,
  reverse,
  siteValues = [],
  chiralityAffinity = 0,
}) {
  const port = .5 * (forward + reverse) - Math.abs(forward - reverse)
    - Math.max(0, -.08 - forward) - Math.max(0, -.08 - reverse);
  const siteMean = mean(siteValues);
  const siteMinimum = siteValues.length ? Math.min(...siteValues) : port;
  if (representation === "sites") return .20 * port + .30 * siteMean + .50 * siteMinimum;
  if (representation === "halo") return .55 * port + .45 * siteMean;
  if (representation === "chiral-halo") return .50 * port + .40 * siteMean + .10 * chiralityAffinity;
  if (representation === "whole") return .35 * port + .55 * siteMean + .10 * siteMinimum;
  return port;
}
