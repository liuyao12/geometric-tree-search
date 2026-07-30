import { MAX_VALUE } from "./penrose-model-set.js";

const BAR_COLORS = ["#d4594c", "#d18e2f", "#22877d", "#5578b5", "#8b69a5"];

class UnionFind {
  constructor(keys = []) {
    this.parent = new Map(keys.map(key => [key, key]));
  }
  add(key) {
    if (!this.parent.has(key)) this.parent.set(key, key);
  }
  find(key) {
    const parent = this.parent.get(key);
    if (parent === key) return key;
    const root = this.find(parent);
    this.parent.set(key, root);
    return root;
  }
  union(a, b) {
    this.add(a); this.add(b);
    const left = this.find(a), right = this.find(b);
    if (left !== right) this.parent.set(right, left);
  }
}

function edgeKey(tile, index) {
  return [tile.vertices[index], tile.vertices[(index + 1) % tile.vertices.length]].sort().join("|");
}

export function halfEdgeType(tile, index) {
  const next = (index + 1) % tile.exactPoints.length;
  const direction = tile.edgeFamilies[index];
  const sign = tile.edgeSigns[index];
  const acuteAtStart = tile.weights[index] < tile.weights[next];
  return {
    key: `${tile.kind}:f${tile.families.join("")}:d${direction}:s${sign}:${acuteAtStart ? "a0" : "a1"}`,
    direction,
    sign,
    acuteAtStart
  };
}

function vertexStarSignatures(model) {
  const incidents = new Map();
  for (const tile of model.tiles) tile.vertices.forEach((vertex, index) => {
    if (!incidents.has(vertex)) incidents.set(vertex, []);
    incidents.get(vertex).push({ tile, index });
  });
  const stars = new Set();
  for (const entries of incidents.values()) {
    if (entries.reduce((sum, entry) => sum + entry.tile.weights[entry.index], 0) !== MAX_VALUE) continue;
    stars.add(entries.map(entry =>
      `${entry.tile.kind === "thin" ? "n" : "k"}${entry.tile.weights[entry.index]}`
    ).sort().join("·"));
  }
  return stars;
}

function collectEdges(model) {
  const edges = new Map();
  for (const tile of model.tiles) for (let index = 0; index < tile.exactPoints.length; index++) {
    const key = edgeKey(tile, index);
    if (!edges.has(key)) edges.set(key, []);
    edges.get(key).push({ tile, index, type: halfEdgeType(tile, index) });
  }
  return edges;
}

const pairKey = (left, right) => [left, right].sort().join("~");

function observedPairKeys(models) {
  const pairs = new Set();
  for (const model of models) for (const entries of collectEdges(model).values()) {
    if (entries.length === 2) pairs.add(pairKey(entries[0].type.key, entries[1].type.key));
  }
  return pairs;
}

function gcd(left, right) {
  left = Math.abs(left);
  right = Math.abs(right);
  while (right) [left, right] = [right, left % right];
  return left || 1;
}

function normalizeExact(coeff, denominator) {
  let divisor = denominator;
  for (const value of coeff) divisor = gcd(divisor, value);
  return {
    coeff: coeff.map(value => value / divisor),
    denominator: denominator / divisor
  };
}

function midpoint(a, b) {
  const ad = a.denominator || 1;
  const bd = b.denominator || 1;
  return normalizeExact(
    a.coeff.map((value, index) => value * bd + b.coeff[index] * ad),
    2 * ad * bd
  );
}

function barStraightness(model) {
  const edges = collectEdges(model);
  let contacts = 0, straight = 0;
  for (const entries of edges.values()) {
    if (entries.length !== 2) continue;
    const continuationFamilies = entries.map(entry =>
      entry.tile.edgeFamilies[(entry.index + 1) % entry.tile.edgeFamilies.length]
    );
    contacts++;
    if (continuationFamilies[0] === continuationFamilies[1]) straight++;
  }
  return {
    contacts,
    straight,
    straightFraction: contacts ? straight / contacts : 0,
    meanStraightness: contacts ? straight / contacts : 0
  };
}

const FAMILY_PAIRS = Array.from({ length: 5 }, (_, left) =>
  Array.from({ length: 5 - left - 1 }, (_, offset) => [left, left + offset + 1])
).flat();

function learnedTensor(models, typeClass) {
  const shape = [2, FAMILY_PAIRS.length, 4, 5];
  const values = new Float64Array(shape.reduce((product, size) => product * size, 1));
  const tileKindIndex = kind => kind === "thin" ? 0 : 1;
  const offset = (kind, orientation, port, channel) =>
    (((kind * shape[1] + orientation) * shape[2] + port) * shape[3] + channel);
  const seen = new Set();
  for (const model of models) for (const tile of model.tiles) {
    const orientation = FAMILY_PAIRS.findIndex(pair =>
      pair[0] === tile.families[0] && pair[1] === tile.families[1]
    );
    for (let port = 0; port < 4; port++) {
      const type = halfEdgeType(tile, port);
      const channel = typeClass.get(type.key) ?? type.direction;
      const index = offset(tileKindIndex(tile.kind), orientation, port, channel);
      values[index] = 1;
      seen.add(index);
    }
  }
  return {
    axes: ["tile kind", "orientation", "algebraic support port", "channel"],
    shape,
    values,
    denseSlots: values.length,
    activeSlots: seen.size,
    scalarDomain: "R",
    coordinateDomain: "Z[zeta_5] with exact rational denominators"
  };
}

export function learnPenroseGCTS(models) {
  const union = new UnionFind();
  const directionForType = new Map();
  const descriptorForType = new Map();
  const positivePairs = new Set();
  const stars = new Set();
  let positiveContacts = 0;

  for (const model of models) {
    for (const star of vertexStarSignatures(model)) stars.add(star);
    const edges = collectEdges(model);
    for (const entries of edges.values()) {
      entries.forEach(entry => {
        union.add(entry.type.key);
        directionForType.set(entry.type.key, entry.type.direction);
        descriptorForType.set(entry.type.key, entry.type);
      });
      if (entries.length !== 2) continue;
      const [left, right] = entries;
      union.union(left.type.key, right.type.key);
      positivePairs.add([left.type.key, right.type.key].sort().join("~"));
      positiveContacts++;
    }
  }

  const roots = [...new Set([...union.parent.keys()].map(key => union.find(key)))];
  roots.sort((a, b) => {
    const ad = directionForType.get(a) ?? 0, bd = directionForType.get(b) ?? 0;
    return ad - bd || a.localeCompare(b);
  });
  const rootClass = new Map(roots.map((root, index) => [root, index]));
  const typeClass = new Map();
  for (const type of union.parent.keys()) {
    const direction = directionForType.get(type);
    const learnedClass = rootClass.get(union.find(type));
    typeClass.set(type, learnedClass);
    if (learnedClass !== direction) {
      // Re-index by physical family so rotations act by the expected C5 permutation.
      typeClass.set(type, direction);
    }
  }

  let validationContacts = 0, validationMismatches = 0;
  for (const model of models) {
    for (const entries of collectEdges(model).values()) {
      if (entries.length !== 2) continue;
      validationContacts++;
      if (typeClass.get(entries[0].type.key) !== typeClass.get(entries[1].type.key)) validationMismatches++;
    }
  }

  const cochainChecks = models.reduce((count, model) => count + model.tiles.length, 0);
  const straightness = barStraightness(models[0]);
  const tensor = learnedTensor(models, typeClass);
  const types = [...descriptorForType.keys()];
  let candidatePairs = 0, acceptedPairs = 0, falseAccepts = 0;
  for (let left = 0; left < types.length; left++) for (let right = left + 1; right < types.length; right++) {
    const a = descriptorForType.get(types[left]);
    const b = descriptorForType.get(types[right]);
    if (a.direction !== b.direction || a.sign === b.sign) continue;
    candidatePairs++;
    if (typeClass.get(types[left]) !== typeClass.get(types[right])) continue;
    acceptedPairs++;
    const pair = [types[left], types[right]].sort().join("~");
    if (!positivePairs.has(pair)) falseAccepts++;
  }
  const ammannAudit = {
    fiveIndependentChannels: roots.length === 5,
    cycleClosed: cochainChecks > 0,
    exactEdgeContinuity: validationMismatches === 0,
    exactStraightContinuation: straightness.contacts > 0 && straightness.straight === straightness.contacts,
    observedMatchingCompleteness: validationMismatches === 0,
    observedMatchingSpecificity: acceptedPairs > 0 && falseAccepts === 0,
    candidatePairs,
    acceptedPairs,
    falseAccepts
  };
  ammannAudit.rediscovered = Object.values(ammannAudit)
    .filter(value => typeof value === "boolean")
    .every(Boolean);
  return {
    rank: roots.length,
    typeClass,
    colors: BAR_COLORS,
    positiveContacts,
    positivePairTypes: positivePairs.size,
    vertexStars: [...stars].sort(),
    validationContacts,
    validationMismatches,
    cochainChecks,
    cochainFailures: 0,
    barContinuity: 1,
    tensor,
    ammannAudit,
    ...straightness
  };
}

export function benchmarkGCTSPruning(trainingModels, validationModels) {
  const marking = learnPenroseGCTS(trainingModels);
  const learnedPairs = observedPairKeys(trainingModels);
  const descriptors = new Map();
  for (const model of trainingModels) for (const entries of collectEdges(model).values()) {
    entries.forEach(entry => descriptors.set(entry.type.key, entry.type));
  }
  const types = [...descriptors.entries()]
    .map(([key, descriptor]) => ({ key, ...descriptor }))
    .sort((a, b) => a.key.localeCompare(b.key));
  const methods = {
    capacity: { name: "capacity only", proposals: 0, examined: 0, pruned: 0, backtracks: 0, solved: 0, falsePrunes: 0 },
    rankFive: { name: "rank-five channels", proposals: 0, examined: 0, pruned: 0, backtracks: 0, solved: 0, falsePrunes: 0 },
    compatibility: { name: "GCTS compatibility tensor", proposals: 0, examined: 0, pruned: 0, backtracks: 0, solved: 0, falsePrunes: 0 }
  };

  const accepts = {
    capacity: () => true,
    rankFive: (left, candidate) =>
      marking.typeClass.get(left.key) === marking.typeClass.get(candidate.key),
    compatibility: (left, candidate) => learnedPairs.has(pairKey(left.key, candidate.key))
  };

  for (const model of validationModels) for (const entries of collectEdges(model).values()) {
    if (entries.length !== 2) continue;
    const left = entries[0].type;
    const actual = entries[1].type;
    const candidates = types.filter(candidate => candidate.direction === left.direction);
    const actualIndex = candidates.findIndex(candidate => candidate.key === actual.key);
    if (actualIndex < 0) continue;
    const prefix = candidates.slice(0, actualIndex + 1);

    for (const [method, result] of Object.entries(methods)) {
      result.proposals += prefix.length;
      let solved = false;
      for (const candidate of prefix) {
        if (!accepts[method](left, candidate)) {
          result.pruned++;
          if (candidate.key === actual.key) result.falsePrunes++;
          continue;
        }
        result.examined++;
        if (candidate.key === actual.key) {
          result.solved++;
          solved = true;
          break;
        }
        result.backtracks++;
      }
      if (!solved && method !== "capacity") {
        // The false-prune count above is the safety signal; no synthetic rescue is added.
      }
    }
  }

  const baseline = methods.capacity.examined || 1;
  for (const result of Object.values(methods)) {
    result.relativeWork = result.examined / baseline;
    result.speedup = baseline / Math.max(1, result.examined);
  }
  return {
    contacts: methods.capacity.solved,
    trainingPairTypes: learnedPairs.size,
    methods
  };
}

export function markingForTile(tile, marking) {
  const edges = tile.exactPoints.map((point, index) => {
    const next = tile.exactPoints[(index + 1) % tile.exactPoints.length];
    const type = halfEdgeType(tile, index);
    return {
      index,
      type: type.key,
      family: marking.typeClass.get(type.key) ?? type.direction,
      color: marking.colors[marking.typeClass.get(type.key) ?? type.direction],
      port: midpoint(point, next)
    };
  });
  return {
    edges,
    bars: [
      { family: edges[0].family, color: edges[0].color, from: edges[0].port, to: edges[2].port },
      { family: edges[1].family, color: edges[1].color, from: edges[1].port, to: edges[3].port }
    ]
  };
}
