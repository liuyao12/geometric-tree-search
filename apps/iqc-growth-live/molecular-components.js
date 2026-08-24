// Generic finite molecular-component discovery from species and metric
// distances. No material name, expected formula, lattice family, or ring size
// enters this learner. Extended covalent networks fail closed so the caller can
// fall back to the irregular support learner.

export const DEFAULT_COVALENT_RADII_A = Object.freeze({
  H: .31, B: .84, C: .76, N: .71, O: .66, F: .57,
  Si: 1.11, P: 1.07, S: 1.05, Cl: 1.02,
  Ge: 1.20, As: 1.19, Se: 1.20, Br: 1.20, I: 1.39,
});

export const DEFAULT_VALENCE_BOUNDS = Object.freeze({
  H: 1, B: 3, C: 4, N: 3, O: 2, F: 1,
  Si: 4, P: 5, S: 6, Cl: 1,
  Ge: 4, As: 5, Se: 6, Br: 1, I: 1,
});

function formulaFor(species, members) {
  const counts = new Map();
  members.forEach((index) => counts.set(species[index], (counts.get(species[index]) || 0) + 1));
  return [...counts.entries()].sort(([first], [second]) => first.localeCompare(second));
}

function coloredMetricSignature(species, distance, members, tolerance) {
  const pairs = [];
  members.forEach((second, offset) => members.slice(0, offset).forEach((first) => {
    const chemistry = [species[first], species[second]].sort().join("|");
    pairs.push(`${chemistry}:${Math.round(distance(first, second) / tolerance)}`);
  }));
  return JSON.stringify([formulaFor(species, members), pairs.sort()]);
}

function connectedComponents(atomCount, edges) {
  const adjacency = Array.from({ length: atomCount }, () => []);
  edges.forEach(([first, second]) => { adjacency[first].push(second); adjacency[second].push(first); });
  const unseen = new Set(Array.from({ length: atomCount }, (_, index) => index));
  const components = [];
  while (unseen.size) {
    const start = Math.min(...unseen);
    const stack = [start];
    const component = [];
    unseen.delete(start);
    while (stack.length) {
      const current = stack.pop();
      component.push(current);
      adjacency[current].forEach((neighbor) => {
        if (!unseen.has(neighbor)) return;
        unseen.delete(neighbor);
        stack.push(neighbor);
      });
    }
    components.push(component.sort((first, second) => first - second));
  }
  return components;
}

export function discoverFiniteMolecularComponents({
  species,
  distance,
  covalentRadii = DEFAULT_COVALENT_RADII_A,
  valenceBounds = DEFAULT_VALENCE_BOUNDS,
  bondFactor = 1.25,
  descriptorToleranceA = .03,
  maximumMoleculeFraction = .25,
  minimumTypeOccurrences = 2,
}) {
  if (!Array.isArray(species) || !species.length || typeof distance !== "function") {
    throw new Error("Molecular discovery requires nonempty species and a metric distance callback");
  }
  if (!(bondFactor > 1 && bondFactor < 2) || !(descriptorToleranceA > 0)
    || !(maximumMoleculeFraction > 0 && maximumMoleculeFraction < 1)) {
    throw new Error("Invalid molecular discovery tolerances");
  }
  const unsupported = [...new Set(species)].filter((element) => !(element in covalentRadii) || !(element in valenceBounds)).sort();
  if (unsupported.length) return { accepted: false, reason: "unsupported chemistry metadata", unsupported, edges: [], components: [], types: [] };

  const candidates = [];
  for (let first = 0; first < species.length - 1; first++) {
    for (let second = first + 1; second < species.length; second++) {
      const separation = distance(first, second);
      const reference = covalentRadii[species[first]] + covalentRadii[species[second]];
      const normalized = separation / reference;
      if (normalized <= bondFactor) candidates.push({ first, second, separation, normalized });
    }
  }
  candidates.sort((first, second) => first.normalized - second.normalized
    || first.separation - second.separation || first.first - second.first || first.second - second.second);
  const degree = Array(species.length).fill(0);
  const edges = [];
  candidates.forEach((candidate) => {
    if (degree[candidate.first] >= valenceBounds[species[candidate.first]]
      || degree[candidate.second] >= valenceBounds[species[candidate.second]]) return;
    degree[candidate.first] += 1;
    degree[candidate.second] += 1;
    edges.push([candidate.first, candidate.second]);
  });
  const components = connectedComponents(species.length, edges);
  const largest = Math.max(...components.map((component) => component.length));
  if (largest > species.length * maximumMoleculeFraction) {
    return { accepted: false, reason: "extended covalent network", unsupported: [], edges, components, types: [] };
  }
  if (components.some((component) => component.length < 2)) {
    return { accepted: false, reason: "unbonded residual components", unsupported: [], edges, components, types: [] };
  }

  const grouped = new Map();
  components.forEach((members) => {
    const signature = coloredMetricSignature(species, distance, members, descriptorToleranceA);
    const records = grouped.get(signature) || [];
    records.push(members);
    grouped.set(signature, records);
  });
  const types = [...grouped.entries()].sort(([first], [second]) => first.localeCompare(second))
    .map(([signature, occurrences], type) => ({
      type,
      signature,
      formula: formulaFor(species, occurrences[0]),
      occurrences: occurrences.map((members) => members.slice()),
    }));
  if (types.some((type) => type.occurrences.length < minimumTypeOccurrences)) {
    return { accepted: false, reason: "nonrecurrent molecular component", unsupported: [], edges, components, types };
  }
  return {
    accepted: true,
    reason: "recurrent finite covalent components",
    unsupported: [],
    edges,
    components,
    types,
    coveredAtoms: components.reduce((sum, component) => sum + component.length, 0),
    materialLabelUsed: false,
    expectedFormulaUsed: false,
  };
}

