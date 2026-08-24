function seededRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 4294967296;
  };
}

function wrap(value, length) {
  return value - Math.floor((value + length / 2) / length) * length;
}

function displacement(first, second, length) {
  return [
    wrap(second[0] - first[0], length),
    wrap(second[1] - first[1], length),
    wrap(second[2] - first[2], length),
  ];
}

function norm(vector) {
  return Math.hypot(...vector);
}

function periodicNearestDistances(positions, length) {
  return positions.map((position, first) => {
    let nearest = Infinity;
    positions.forEach((other, second) => {
      if (first === second) return;
      nearest = Math.min(nearest, norm(displacement(position, other, length)));
    });
    return nearest;
  });
}

function median(values) {
  const sorted = values.slice().sort((first, second) => first - second);
  return sorted[Math.floor(sorted.length / 2)] || 1;
}

function pairExclusion(first, second) {
  if (first === "Zr" && second === "Zr") return .86;
  if (first !== second) return .82;
  return .78;
}

/**
 * Deterministic dense binary hard-core packing for the browser's amorphous
 * negative control.  Positions begin from a continuous random process—not a
 * perturbed lattice—and are relaxed only to remove unphysical close contacts.
 * No target RDF, crystal cell, or structural label enters the relaxation.
 */
export function generateAmorphousMixture({
  count = 216,
  copperFraction = .64,
  targetNearestAngstrom = 2.72,
  seed = 0x51a7c0de,
  iterations = 180,
} = {}) {
  if (!Number.isInteger(count) || count < 8) throw new Error("amorphous mixture requires at least eight atoms");
  if (!(copperFraction > 0 && copperFraction < 1)) throw new Error("binary fraction must lie strictly between zero and one");
  if (!(targetNearestAngstrom > 0)) throw new Error("target nearest-neighbor scale must be positive");
  const random = seededRandom(seed);
  const length = Math.cbrt(count / .43);
  const positions = Array.from({ length: count }, () => [
    (random() - .5) * length,
    (random() - .5) * length,
    (random() - .5) * length,
  ]);
  const copperCount = Math.round(count * copperFraction);
  const species = Array.from({ length: count }, (_, index) => index < copperCount ? "Cu" : "Zr");
  for (let index = species.length - 1; index > 0; index--) {
    const other = Math.floor(random() * (index + 1));
    [species[index], species[other]] = [species[other], species[index]];
  }

  for (let step = 0; step < iterations; step++) {
    const corrections = Array.from({ length: count }, () => [0, 0, 0]);
    for (let first = 0; first < count; first++) for (let second = first + 1; second < count; second++) {
      let vector = displacement(positions[first], positions[second], length);
      let distance = norm(vector);
      const exclusion = pairExclusion(species[first], species[second]);
      if (distance >= exclusion) continue;
      if (distance < 1e-8) {
        vector = [random() - .5, random() - .5, random() - .5];
        distance = norm(vector);
      }
      const amount = .24 * (exclusion - distance) / distance;
      for (let axis = 0; axis < 3; axis++) {
        const shift = vector[axis] * amount;
        corrections[first][axis] -= shift;
        corrections[second][axis] += shift;
      }
    }
    const thermal = .008 * Math.max(0, 1 - step / (iterations * .72));
    positions.forEach((position, index) => {
      for (let axis = 0; axis < 3; axis++) {
        position[axis] = wrap(position[axis] + corrections[index][axis]
          + (random() - .5) * thermal, length);
      }
    });
  }

  const rawNearest = periodicNearestDistances(positions, length);
  const scale = targetNearestAngstrom / median(rawNearest);
  const scaledPositions = positions.map((position) => position.map((value) => value * scale));
  const cellLengthAngstrom = length * scale;
  const nearest = periodicNearestDistances(scaledPositions, cellLengthAngstrom);
  return {
    positions: scaledPositions,
    species,
    cellLengthAngstrom,
    audit: {
      seed,
      count,
      composition: { Cu: copperCount, Zr: count - copperCount },
      medianNearestAngstrom: median(nearest),
      minimumNearestAngstrom: Math.min(...nearest),
      sourceProcess: "continuous random initialization + species-dependent hard-core relaxation",
      targetRdfUsed: false,
      latticeSitesUsed: false,
    },
  };
}

export function periodicPairRdf(positions, species, cellLength, bins = 48, maximumRadius = cellLength / 2) {
  const pairCounts = new Map();
  const all = new Array(bins).fill(0);
  for (let first = 0; first < positions.length; first++) for (let second = first + 1; second < positions.length; second++) {
    const distance = norm(displacement(positions[first], positions[second], cellLength));
    if (distance >= maximumRadius) continue;
    const bin = Math.min(bins - 1, Math.floor(distance / maximumRadius * bins));
    all[bin]++;
    const key = [species[first], species[second]].sort().join("|");
    if (!pairCounts.has(key)) pairCounts.set(key, new Array(bins).fill(0));
    pairCounts.get(key)[bin]++;
  }
  const volume = cellLength ** 3;
  const populations = species.reduce((counts, symbol) => ({ ...counts, [symbol]: (counts[symbol] || 0) + 1 }), {});
  const normalize = (counts, pair = null) => counts.map((value, bin) => {
    const inner = bin / bins * maximumRadius;
    const outer = (bin + 1) / bins * maximumRadius;
    const shell = 4 / 3 * Math.PI * (outer ** 3 - inner ** 3);
    const ideal = !pair
      ? positions.length * (positions.length - 1) / (2 * volume) * shell
      : pair[0] === pair[1]
        ? populations[pair[0]] * (populations[pair[0]] - 1) / (2 * volume) * shell
        : populations[pair[0]] * populations[pair[1]] / volume * shell;
    return ideal > 0 ? value / ideal : 0;
  });
  return {
    all: normalize(all),
    byPair: Object.fromEntries([...pairCounts].map(([key, counts]) => [key, normalize(counts, key.split("|"))])),
  };
}
