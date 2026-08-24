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
  if (unsupported.length) return {
    accepted: false, reason: "unsupported chemistry metadata", unsupported,
    edges: [], components: [], types: [], atomCount: species.length,
    covalentEdges: 0, componentCount: 0, largestComponent: 0, typeCount: 0,
    materialLabelUsed: false, expectedFormulaUsed: false,
  };

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
    return {
      accepted: false, reason: "extended covalent network", unsupported: [], edges, components, types: [],
      atomCount: species.length, covalentEdges: edges.length, componentCount: components.length,
      largestComponent: largest, typeCount: 0, materialLabelUsed: false, expectedFormulaUsed: false,
    };
  }
  if (components.some((component) => component.length < 2)) {
    return {
      accepted: false, reason: "unbonded residual components", unsupported: [], edges, components, types: [],
      atomCount: species.length, covalentEdges: edges.length, componentCount: components.length,
      largestComponent: largest, typeCount: 0, materialLabelUsed: false, expectedFormulaUsed: false,
    };
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
    return {
      accepted: false, reason: "nonrecurrent molecular component", unsupported: [], edges, components, types,
      atomCount: species.length, covalentEdges: edges.length, componentCount: components.length,
      largestComponent: largest, typeCount: types.length, materialLabelUsed: false, expectedFormulaUsed: false,
    };
  }
  return {
    accepted: true,
    reason: "recurrent finite covalent components",
    unsupported: [],
    edges,
    components,
    types,
    atomCount: species.length,
    covalentEdges: edges.length,
    componentCount: components.length,
    largestComponent: largest,
    typeCount: types.length,
    coveredAtoms: components.reduce((sum, component) => sum + component.length, 0),
    materialLabelUsed: false,
    expectedFormulaUsed: false,
  };
}

function componentSeparation(first, second, distance) {
  let minimum = Infinity;
  first.forEach((firstAtom) => second.forEach((secondAtom) => {
    minimum = Math.min(minimum, distance(firstAtom, secondAtom));
  }));
  return minimum;
}

function canonicalCycle(sequence) {
  const rotations = [];
  const forward = sequence.slice();
  const reverse = sequence.slice().reverse();
  [forward, reverse].forEach((order) => order.forEach((_, index) => rotations.push([...order.slice(index), ...order.slice(0, index)])));
  return rotations.sort((first, second) => JSON.stringify(first).localeCompare(JSON.stringify(second)))[0];
}

function chordlessCycles(vertexCount, edges, maximumSize) {
  const adjacency = Array.from({ length: vertexCount }, () => new Set());
  edges.forEach(([first, second]) => { adjacency[first].add(second); adjacency[second].add(first); });
  const cycles = new Map();
  for (let start = 0; start < vertexCount; start++) {
    const stack = [[start, [start]]];
    while (stack.length) {
      const [current, path] = stack.pop();
      [...adjacency[current]].sort((first, second) => second - first).forEach((neighbor) => {
        if (neighbor === start && path.length >= 3) {
          const cycle = canonicalCycle(path);
          let graphEdges = 0;
          for (let first = 0; first < cycle.length - 1; first++) {
            for (let second = first + 1; second < cycle.length; second++) {
              if (adjacency[cycle[first]].has(cycle[second])) graphEdges++;
            }
          }
          if (graphEdges === cycle.length) cycles.set(cycle.join(":"), cycle);
          return;
        }
        if (path.length >= maximumSize || neighbor <= start || path.includes(neighbor)) return;
        stack.push([neighbor, [...path, neighbor]]);
      });
    }
  }
  const minimumByEdge = new Map();
  cycles.forEach((cycle) => cycle.forEach((first, index) => {
    const second = cycle[(index + 1) % cycle.length];
    const edge = first < second ? `${first}:${second}` : `${second}:${first}`;
    minimumByEdge.set(edge, Math.min(minimumByEdge.get(edge) || Infinity, cycle.length));
  }));
  return [...cycles.values()].filter((cycle) => cycle.every((first, index) => {
    const second = cycle[(index + 1) % cycle.length];
    const edge = first < second ? `${first}:${second}` : `${second}:${first}`;
    return minimumByEdge.get(edge) === cycle.length;
  })).sort((first, second) => first.length - second.length || first.join(":").localeCompare(second.join(":")));
}

function graphConnected(vertexCount, edges) {
  if (vertexCount <= 1) return true;
  const adjacency = Array.from({ length: vertexCount }, () => []);
  edges.forEach(([first, second]) => { adjacency[first].push(second); adjacency[second].push(first); });
  const seen = new Set([0]);
  const stack = [0];
  while (stack.length) adjacency[stack.pop()].forEach((neighbor) => {
    if (seen.has(neighbor)) return;
    seen.add(neighbor);
    stack.push(neighbor);
  });
  return seen.size === vertexCount;
}

export function discoverMolecularConnectionTopology({
  discovery,
  species,
  distance,
  contactShellFactor = 1.16,
  descriptorToleranceA = .03,
  maximumVoidCycle = 8,
}) {
  if (!discovery?.accepted) throw new Error("Connection topology requires accepted finite molecular components");
  if (!(contactShellFactor > 1 && contactShellFactor < 2) || maximumVoidCycle < 3) {
    throw new Error("Invalid molecular connection topology controls");
  }
  const components = discovery.components;
  const nearest = components.map((component, first) => Math.min(...components
    .map((other, second) => first === second ? Infinity : componentSeparation(component, other, distance))));
  const componentEdges = [];
  for (let first = 0; first < components.length - 1; first++) {
    for (let second = first + 1; second < components.length; second++) {
      const separation = componentSeparation(components[first], components[second], distance);
      if (separation <= nearest[first] * contactShellFactor + 1e-9
        || separation <= nearest[second] * contactShellFactor + 1e-9) componentEdges.push([first, second]);
    }
  }
  const componentType = new Map();
  discovery.types.forEach((type) => type.occurrences.forEach((members) => componentType.set(members.join(":"), type.type)));
  const typeForComponent = components.map((component) => componentType.get(component.join(":")));
  const rawConnections = componentEdges.map(([first, second]) => {
    const members = [...new Set([...components[first], ...components[second]])].sort((a, b) => a - b);
    const signature = JSON.stringify([
      [typeForComponent[first], typeForComponent[second]].sort((a, b) => a - b),
      coloredMetricSignature(species, distance, members, descriptorToleranceA),
    ]);
    return { components: [first, second], members, signature };
  });
  const connectionSignatures = [...new Set(rawConnections.map((record) => record.signature))].sort();
  const connectionType = new Map(connectionSignatures.map((signature, index) => [signature, index]));
  const connections = rawConnections.map((record, occurrence) => ({
    occurrence, type: connectionType.get(record.signature), ...record,
  }));

  const cycles = chordlessCycles(components.length, componentEdges, maximumVoidCycle);
  const rawVoids = cycles.map((cycle) => {
    const members = [...new Set(cycle.flatMap((component) => components[component]))].sort((a, b) => a - b);
    const edgeLengths = cycle.map((first, index) => Math.round(componentSeparation(
      components[first], components[cycle[(index + 1) % cycle.length]], distance) / descriptorToleranceA)).sort((a, b) => a - b);
    const signature = JSON.stringify([cycle.length, canonicalCycle(cycle.map((component) => typeForComponent[component])), edgeLengths]);
    return { components: cycle, members, signature };
  });
  const voidSignatures = [...new Set(rawVoids.map((record) => record.signature))].sort();
  const voidType = new Map(voidSignatures.map((signature, index) => [signature, index]));
  const voids = rawVoids.map((record, occurrence) => ({ occurrence, type: voidType.get(record.signature), ...record }));
  return {
    componentEdges,
    connections,
    voids,
    connectionTypeCount: connectionSignatures.length,
    voidTypeCount: voidSignatures.length,
    componentGraphConnected: graphConnected(components.length, componentEdges),
    expectedRingSizeUsed: false,
    materialLabelUsed: false,
  };
}
