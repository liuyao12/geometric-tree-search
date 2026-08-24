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
    const upperContact = quantile(nearestValues, .95) || typicalContact;
    const contactScale = Math.max(typicalContact * .08, (upperContact - lowerContact) / 2);
    const exclusion = Math.min(minimumObserved * minimumContactFraction,
      lowerContact * lowerContactFraction);
    records.push({
      key,
      species: [symbols[first], symbols[second]],
      minimumObserved,
      lowerContact,
      typicalContact,
      upperContact,
      contactScale,
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

function orderedKey(center, neighbor) {
  return `${center}>${neighbor}`;
}

/**
 * Learn causal upper coordination capacities on top of the unordered contact
 * geometry.  Counts are ordered (O->H is not H->O), and maxima—not means—are
 * enforced so every supplied local environment remains admissible.  Lower
 * coordination is intentionally unconstrained because a growing frontier is
 * incomplete until later actions arrive.
 */
export function learnColoredCoordinationEnvelopes(species, distance, distanceModel, {
  contactExpansion = 1.18,
} = {}) {
  if (!distanceModel?.records?.length) throw new Error("coordination envelopes require colored distance envelopes");
  if (!(Number.isFinite(contactExpansion) && contactExpansion > 1)) throw new Error("contact expansion must exceed one");
  const symbols = [...new Set(species)].sort();
  const records = [];
  symbols.forEach((centerSpecies) => symbols.forEach((neighborSpecies) => {
    const pair = distanceModel.byKey[pairKey(centerSpecies, neighborSpecies)];
    if (!pair) return;
    const contactCutoff = pair.lowerContact * contactExpansion;
    const counts = species.map((symbol, center) => {
      if (symbol !== centerSpecies) return null;
      let count = 0;
      for (let neighbor = 0; neighbor < species.length; neighbor++) {
        if (neighbor === center || species[neighbor] !== neighborSpecies) continue;
        if (distance(center, neighbor) <= contactCutoff) count++;
      }
      return count;
    }).filter(Number.isInteger).sort((a, b) => a - b);
    if (!counts.length) return;
    records.push({
      key: orderedKey(centerSpecies, neighborSpecies),
      centerSpecies,
      neighborSpecies,
      contactCutoff,
      medianObserved: quantile(counts, .5),
      upperObserved: quantile(counts, .95),
      maximumObserved: counts.at(-1),
      centerObservations: counts.length,
    });
  }));
  return {
    records,
    byKey: Object.fromEntries(records.map((record) => [record.key, record])),
    maximumCutoff: Math.max(...records.map((record) => record.contactCutoff)),
    config: { contactExpansion },
  };
}

export function coordinationEnvelopeFor(model, centerSpecies, neighborSpecies) {
  return model?.byKey?.[orderedKey(centerSpecies, neighborSpecies)] || null;
}

/**
 * Dimensionless local coordination deficit relative to the observed bulk
 * median. This is a geometric surface-completion observable, not bond energy:
 * frontier centers may remain deficient and overcoordination is handled by the
 * separate hard capacity test.
 */
export function coloredCoordinationDeficit(species, distance, coordinationModel,
  centerIndices = species.map((_, index) => index)) {
  const terms = [];
  [...new Set(centerIndices)].forEach((center) => {
    coordinationModel.records.filter((record) => record.centerSpecies === species[center])
      .forEach((record) => {
        const count = species.reduce((total, neighborSpecies, neighbor) => {
          if (neighbor === center || neighborSpecies !== record.neighborSpecies) return total;
          return total + (distance(center, neighbor) <= record.contactCutoff ? 1 : 0);
        }, 0);
        const target = record.medianObserved;
        if (!(target > 0)) return;
        terms.push({
          center,
          centerSpecies: record.centerSpecies,
          neighborSpecies: record.neighborSpecies,
          count,
          target,
          deficit: Math.max(0, target - count) / target,
        });
      });
  });
  return {
    mean: terms.reduce((sum, term) => sum + term.deficit, 0) / Math.max(1, terms.length),
    terms: terms.length,
    deficientTerms: terms.filter((term) => term.deficit > 0).length,
    records: terms,
  };
}

function angularKey(center, firstNeighbor, secondNeighbor) {
  const [first, second] = [firstNeighbor, secondNeighbor].sort();
  return `${first}<${center}>${second}`;
}

function vectorComponents(vector) {
  if (Array.isArray(vector)) return vector;
  return [vector.x, vector.y, vector.z];
}

function angleDegrees(firstVector, secondVector) {
  const first = vectorComponents(firstVector);
  const second = vectorComponents(secondVector);
  const firstNorm = Math.hypot(...first);
  const secondNorm = Math.hypot(...second);
  if (!(firstNorm > 1e-9 && secondNorm > 1e-9)) return null;
  const cosine = first.reduce((sum, value, axis) => sum + value * second[axis], 0) / (firstNorm * secondNorm);
  return Math.acos(Math.max(-1, Math.min(1, cosine))) * 180 / Math.PI;
}

function angleBands(values, mergeGapDegrees, toleranceDegrees) {
  const groups = [];
  values.forEach((value) => {
    const group = groups.at(-1);
    if (!group || value - group.at(-1) > mergeGapDegrees) groups.push([value]);
    else group.push(value);
  });
  return groups.map((group) => ({
    minimum: Math.max(0, group[0] - toleranceDegrees),
    maximum: Math.min(180, group.at(-1) + toleranceDegrees),
    observedMinimum: group[0],
    observedMaximum: group.at(-1),
    observations: group.length,
  }));
}

/**
 * Learn colored three-body admissibility from every pair of observed contact
 * neighbors.  Neighbor colors are unordered, the central color is not.  A
 * multimodal crystal (for example 90/180 degree octahedral angles) retains
 * separate bands instead of filling the physically absent angles between
 * modes.  Each observed band is padded, so the supplied structure is always
 * admissible and mild geometric noise does not turn into a brittle rule.
 */
export function learnColoredAngularEnvelopes(species, displacement, coordinationModel, {
  mergeGapDegrees = 18,
  toleranceDegrees = 8,
} = {}) {
  if (!coordinationModel?.records?.length) throw new Error("angular envelopes require coordination envelopes");
  if (typeof displacement !== "function") throw new Error("angular envelopes require a displacement callback");
  if (!(Number.isFinite(mergeGapDegrees) && mergeGapDegrees > 0
    && Number.isFinite(toleranceDegrees) && toleranceDegrees > 0 && toleranceDegrees < 45)) {
    throw new Error("angular envelope widths must be finite positive bounds");
  }
  const observations = new Map();
  const centerSets = new Map();
  species.forEach((centerSpecies, center) => {
    const neighbors = [];
    species.forEach((neighborSpecies, neighbor) => {
      if (neighbor === center) return;
      const envelope = coordinationEnvelopeFor(coordinationModel, centerSpecies, neighborSpecies);
      if (!envelope) return;
      const vector = displacement(center, neighbor);
      const norm = Math.hypot(...vectorComponents(vector));
      if (norm <= envelope.contactCutoff) neighbors.push({ neighbor, neighborSpecies, vector });
    });
    for (let first = 0; first < neighbors.length - 1; first++) for (let second = first + 1; second < neighbors.length; second++) {
      const value = angleDegrees(neighbors[first].vector, neighbors[second].vector);
      if (!Number.isFinite(value)) continue;
      const key = angularKey(centerSpecies, neighbors[first].neighborSpecies, neighbors[second].neighborSpecies);
      const values = observations.get(key) || [];
      values.push(value);
      observations.set(key, values);
      const centers = centerSets.get(key) || new Set();
      centers.add(center);
      centerSets.set(key, centers);
    }
  });
  const records = [...observations.entries()].sort(([first], [second]) => first.localeCompare(second))
    .map(([key, values]) => {
      values.sort((first, second) => first - second);
      const [firstNeighbor, centerAndSecond] = key.split("<");
      const [center, secondNeighbor] = centerAndSecond.split(">");
      return {
        key,
        centerSpecies: center,
        neighborSpecies: [firstNeighbor, secondNeighbor],
        bands: angleBands(values, mergeGapDegrees, toleranceDegrees),
        medianObservedDegrees: quantile(values, .5),
        angleObservations: values.length,
        centerObservations: centerSets.get(key).size,
      };
    });
  return {
    records,
    byKey: Object.fromEntries(records.map((record) => [record.key, record])),
    config: { mergeGapDegrees, toleranceDegrees },
  };
}

export function angularEnvelopeFor(model, centerSpecies, firstNeighbor, secondNeighbor) {
  return model?.byKey?.[angularKey(centerSpecies, firstNeighbor, secondNeighbor)] || null;
}

export function angleAllowed(record, degrees) {
  return !record || record.bands.some((band) => degrees >= band.minimum && degrees <= band.maximum);
}

/** Evaluate only the requested centers in a projected colored point set. */
export function coloredAngularViolations(species, displacement, coordinationModel, angularModel,
  centerIndices = species.map((_, index) => index)) {
  const violations = [];
  [...new Set(centerIndices)].forEach((center) => {
    const neighbors = species.map((neighborSpecies, neighbor) => {
      if (neighbor === center) return null;
      const coordination = coordinationEnvelopeFor(coordinationModel, species[center], neighborSpecies);
      if (!coordination) return null;
      const vector = displacement(center, neighbor);
      return Math.hypot(...vectorComponents(vector)) <= coordination.contactCutoff
        ? { neighbor, neighborSpecies, vector } : null;
    }).filter(Boolean);
    for (let first = 0; first < neighbors.length - 1; first++) for (let second = first + 1; second < neighbors.length; second++) {
      const envelope = angularEnvelopeFor(angularModel, species[center],
        neighbors[first].neighborSpecies, neighbors[second].neighborSpecies);
      if (!envelope) continue;
      const degrees = angleDegrees(neighbors[first].vector, neighbors[second].vector);
      if (Number.isFinite(degrees) && !angleAllowed(envelope, degrees)) violations.push({
        center,
        neighbors: [neighbors[first].neighbor, neighbors[second].neighbor],
        centerSpecies: species[center],
        neighborSpecies: [neighbors[first].neighborSpecies, neighbors[second].neighborSpecies].sort(),
        degrees,
        allowedBands: envelope.bands,
      });
    }
  });
  return violations;
}

function boundedSquare(value) {
  return Math.min(16, value * value);
}

/**
 * A dimensionless geometric misfit for ranking already-enumerated actions.
 * It is deliberately not an energy: no force, temperature, probability, or
 * time scale is inferred.  Exact collision and envelope checks remain the
 * authority for admission.
 */
export function coloredGeometricStrain(species, displacement, distanceModel, coordinationModel,
  angularModel, centerIndices = species.map((_, index) => index)) {
  const centers = [...new Set(centerIndices)];
  const contactPairs = new Set();
  const distanceTerms = [];
  const angleTerms = [];
  centers.forEach((center) => {
    const neighbors = species.map((neighborSpecies, neighbor) => {
      if (neighbor === center) return null;
      const coordination = coordinationEnvelopeFor(coordinationModel, species[center], neighborSpecies);
      if (!coordination) return null;
      const vector = displacement(center, neighbor);
      const norm = Math.hypot(...vectorComponents(vector));
      return norm <= coordination.contactCutoff ? { neighbor, neighborSpecies, vector, norm } : null;
    }).filter(Boolean);
    neighbors.forEach(({ neighbor, norm }) => {
      const pair = center < neighbor ? `${center}:${neighbor}` : `${neighbor}:${center}`;
      if (contactPairs.has(pair)) return;
      contactPairs.add(pair);
      const envelope = distanceModel?.byKey?.[pairKey(species[center], species[neighbor])];
      if (!envelope) return;
      distanceTerms.push(boundedSquare((norm - envelope.typicalContact) / envelope.contactScale));
    });
    for (let first = 0; first < neighbors.length - 1; first++) for (let second = first + 1; second < neighbors.length; second++) {
      const envelope = angularEnvelopeFor(angularModel, species[center],
        neighbors[first].neighborSpecies, neighbors[second].neighborSpecies);
      if (!envelope) continue;
      const degrees = angleDegrees(neighbors[first].vector, neighbors[second].vector);
      if (!Number.isFinite(degrees)) continue;
      const normalized = Math.min(...envelope.bands.map((band) => {
        const mode = (band.observedMinimum + band.observedMaximum) / 2;
        const scale = Math.max(angularModel.config.toleranceDegrees,
          (band.observedMaximum - band.observedMinimum) / 2 + angularModel.config.toleranceDegrees);
        return Math.abs(degrees - mode) / scale;
      }));
      angleTerms.push(boundedSquare(normalized));
    }
  });
  const distance = distanceTerms.reduce((sum, value) => sum + value, 0) / Math.max(1, distanceTerms.length);
  const angle = angleTerms.reduce((sum, value) => sum + value, 0) / Math.max(1, angleTerms.length);
  return {
    total: .55 * distance + .45 * angle,
    distance,
    angle,
    contactTerms: distanceTerms.length,
    angleTerms: angleTerms.length,
  };
}
