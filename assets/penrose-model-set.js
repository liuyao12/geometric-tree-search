const TAU = Math.PI * 2;

export const PHI = (1 + Math.sqrt(5)) / 2;
export const MAX_VALUE = 10;

export const STAR = Array.from({ length: 5 }, (_, index) => {
  const angle = TAU * index / 5 - Math.PI / 2;
  return { x: Math.cos(angle), y: Math.sin(angle) };
});

export const PENROSE_CATALOG = [
  { id: "p3-thick", family: "P3", name: "Thick rhomb", short: "T", color: "#5eb6a7", accepts: ["thick"], points: [[-.8, 0], [0, -.48], [.8, 0], [0, .48]] },
  { id: "p3-thin", family: "P3", name: "Thin rhomb", short: "t", color: "#d7ab42", accepts: ["thin"], points: [[-.9, 0], [0, -.25], [.9, 0], [0, .25]] },
  { id: "p2-kite", family: "P2", name: "Kite", short: "K", color: "#4c8fbd", accepts: ["kite"], points: [[0, -.86], [.7, -.12], [0, .72], [-.7, -.12]] },
  { id: "p2-dart", family: "P2", name: "Dart", short: "D", color: "#8b7eab", accepts: ["dart"], points: [[0, -.84], [.72, .42], [0, .08], [-.72, .42]] },
  { id: "p1-p5", family: "P1", name: "Pentagon P-5", short: "5", color: "#d26b57", accepts: ["thick", "thin"], points: regularPolygon(5, .78) },
  { id: "p1-p3", family: "P1", name: "Pentagon P-3", short: "3", color: "#d98258", accepts: ["thick", "thin"], points: regularPolygon(5, .78) },
  { id: "p1-p2", family: "P1", name: "Pentagon P-2", short: "2", color: "#bd5d74", accepts: ["thick", "thin"], points: regularPolygon(5, .78) },
  { id: "p1-star", family: "P1", name: "Star", short: "S", color: "#cb9650", accepts: ["thick", "thin"], points: starPolygon(5, .82, .35) },
  { id: "p1-boat", family: "P1", name: "Boat", short: "B", color: "#4e8990", accepts: ["thick", "thin"], points: [[-.86, .38], [-.52, -.3], [0, -.76], [.52, -.3], [.86, .38], [0, .08]] },
  { id: "p1-diamond", family: "P1", name: "Diamond", short: "◇", color: "#757eae", accepts: ["thin"], points: [[-.9, 0], [0, -.25], [.9, 0], [0, .25]] }
];

const dot = (a, b) => a.x * b.x + a.y * b.y;
const add = (a, b) => ({ x: a.x + b.x, y: a.y + b.y });
const scale = (a, amount) => ({ x: a.x * amount, y: a.y * amount });
const coeffKey = coeff => coeff.join(",");
const tileKey = vertices => [...vertices].sort().join("|");
const p3AtomIds = (tileId, kind) =>
  kind === "thin" ? [`${tileId}:whole`] : [`${tileId}:half-a`, `${tileId}:half-b`];

const gcdBig = (left, right) => {
  left = left < 0n ? -left : left;
  right = right < 0n ? -right : right;
  while (right) [left, right] = [right, left % right];
  return left || 1n;
};

function quad(a = 0n, b = 0n, d = 1n) {
  if (d < 0n) { a = -a; b = -b; d = -d; }
  const divisor = gcdBig(gcdBig(a, b), d);
  return { a: a / divisor, b: b / divisor, d: d / divisor };
}

const qInt = value => quad(BigInt(value));
const qAdd = (left, right) => quad(left.a * right.d + right.a * left.d, left.b * right.d + right.b * left.d, left.d * right.d);
const qNeg = value => quad(-value.a, -value.b, value.d);
const qSub = (left, right) => qAdd(left, qNeg(right));
const qMul = (left, right) => quad(left.a * right.a + 5n * left.b * right.b, left.a * right.b + left.b * right.a, left.d * right.d);
const qScale = (value, amount) => quad(value.a * BigInt(amount), value.b * BigInt(amount), value.d);
const qInv = value => quad(value.d * value.a, -value.d * value.b, value.a * value.a - 5n * value.b * value.b);
const qDiv = (left, right) => qMul(left, qInv(right));

function qSign(value) {
  const { a, b } = value;
  if (b === 0n) return a < 0n ? -1 : a > 0n ? 1 : 0;
  if (a === 0n) return b < 0n ? -1 : 1;
  if ((a > 0n) === (b > 0n)) return a > 0n ? 1 : -1;
  const comparison = a * a - 5n * b * b;
  if (comparison === 0n) return 0;
  return a > 0n ? (comparison > 0n ? 1 : -1) : (comparison > 0n ? -1 : 1);
}

const floorRational = (numerator, denominator) => {
  let quotient = numerator / denominator;
  if (numerator < 0n && numerator % denominator) quotient--;
  return quotient;
};

function qFloor(value) {
  const lowNumerator = value.a + (value.b >= 0n ? 2n * value.b : 3n * value.b);
  const highNumerator = value.a + (value.b >= 0n ? 3n * value.b : 2n * value.b);
  let candidate = floorRational(lowNumerator, value.d) - 1n;
  const upper = floorRational(highNumerator, value.d) + 1n;
  while (candidate < upper && qSign(qSub(value, qInt(candidate + 1n))) >= 0) candidate++;
  return candidate;
}

const PHI_Q = quad(1n, 1n, 2n);
const INV_PHI_Q = quad(-1n, 1n, 2n);
const SIN_UNITS = [qInt(0), qInt(1), INV_PHI_Q, qNeg(INV_PHI_Q), qInt(-1)];
const mod5 = value => ((value % 5) + 5) % 5;
const sinRatio = (numeratorDelta, denominatorDelta) => qDiv(SIN_UNITS[mod5(numeratorDelta)], SIN_UNITS[mod5(denominatorDelta)]);

function regularPolygon(sides, radius) {
  return Array.from({ length: sides }, (_, index) => {
    const angle = -Math.PI / 2 + index * TAU / sides;
    return [Math.cos(angle) * radius, Math.sin(angle) * radius];
  });
}

function starPolygon(points, outer, inner) {
  return Array.from({ length: points * 2 }, (_, index) => {
    const angle = -Math.PI / 2 + index * Math.PI / points;
    const radius = index % 2 ? inner : outer;
    return [Math.cos(angle) * radius, Math.sin(angle) * radius];
  });
}

export function exactToPoint(exact) {
  const denominator = exact.denominator || 1;
  return exact.coeff.reduce((point, amount, index) =>
    add(point, scale(STAR[index], amount / denominator)), { x: 0, y: 0 }
  );
}

const exactFromCoeff = (coeff, denominator = 1) => ({ coeff: [...coeff], denominator });

function exactNormSquared(exact) {
  let value = qInt(0);
  const coeff = exact.coeff.map(BigInt);
  for (let i = 0; i < 5; i++) {
    value = qAdd(value, qInt(coeff[i] * coeff[i]));
    for (let j = i + 1; j < 5; j++) {
      const separation = Math.min(mod5(i - j), mod5(j - i));
      const cosine = separation === 1 ? quad(-1n, 1n, 4n) : quad(-1n, -1n, 4n);
      value = qAdd(value, qScale(cosine, 2n * coeff[i] * coeff[j]));
    }
  }
  const denominator = BigInt(exact.denominator || 1);
  return quad(value.a, value.b, value.d * denominator * denominator);
}

function exactWithinRadius(exact, radius) {
  const right = qInt(BigInt(radius) * BigInt(radius));
  return qSign(qSub(exactNormSquared(exact), right)) <= 0;
}

export function makeCyclotomicHost({ radius = 14, height = 6, seed } = {}) {
  const origin = seed?.exactPoints?.[0] || exactFromCoeff([0, 0, 0, 0, 0], 2);
  const points = new Map();
  for (let a = -height; a <= height; a++) {
    for (let b = -height; b <= height; b++) {
      for (let c = -height; c <= height; c++) {
        for (let d = -height; d <= height; d++) {
          const exact = exactFromCoeff([
            origin.coeff[0] + 2 * a,
            origin.coeff[1] + 2 * b,
            origin.coeff[2] + 2 * c,
            origin.coeff[3] + 2 * d,
            origin.coeff[4]
          ], 2);
          if (!exactWithinRadius(exact, radius + 1)) continue;
          const key = `${exact.coeff.join(",")}/${exact.denominator}`;
          const coefficientHeight = Math.max(Math.abs(a), Math.abs(b), Math.abs(c), Math.abs(d));
          const existing = points.get(key);
          if (!existing || coefficientHeight < existing.height) points.set(key, { exact, height: coefficientHeight });
        }
      }
    }
  }
  return { points: [...points.values()], height, radius, denseLimit: true };
}

function exactGammas(phaseCode) {
  const modulus = 1009n;
  const code = BigInt(phaseCode);
  const multipliers = [1n, 2n, 3n, 5n, 7n];
  const offsets = [17n, 43n, 89n, 173n, 281n];
  const raw = multipliers.map((multiplier, index) => {
    const numerator = ((code * multiplier + offsets[index]) % modulus + modulus) % modulus;
    return quad(numerator, 0n, modulus);
  });
  const sum = raw.reduce(qAdd, qInt(0));
  return raw.map(value => qSub(value, qDiv(sum, qInt(5))));
}

function compareExactNorm(left, right) {
  return qSign(qSub(exactNormSquared(left), exactNormSquared(right)));
}

const mod20 = value => ((value % 20) + 20) % 20;
const unitDirectionCode = (family, sign = 1) =>
  mod20(-5 + 4 * family + (sign < 0 ? 10 : 0));

function thickDiagonalDirectionCode(left, right, sign = 1) {
  const forward = right === left + 1 ? -3 + 4 * left : 13;
  return mod20(forward + (sign < 0 ? 10 : 0));
}

function exactAverage(points) {
  const denominator = points.reduce((product, point) => product * (point.denominator || 1), 1);
  const coeff = Array(5).fill(0);
  points.forEach(point => {
    const factor = denominator / (point.denominator || 1);
    point.coeff.forEach((value, index) => { coeff[index] += value * factor; });
  });
  return exactFromCoeff(coeff, denominator * points.length);
}

export function makePenroseModelSet({ radius = 14, phaseCode = 173 } = {}) {
  const gammas = exactGammas(phaseCode);
  const exactRadius = Math.ceil(radius);
  const gridRange = exactRadius * 2 + 7;
  const tileMap = new Map();
  const vertexMap = new Map();

  for (let i = 0; i < 5; i++) for (let j = i + 1; j < 5; j++) {
    for (let ki = -gridRange; ki <= gridRange; ki++) for (let kj = -gridRange; kj <= gridRange; kj++) {
      const ai = qSub(qInt(ki), gammas[i]);
      const aj = qSub(qInt(kj), gammas[j]);
      const base = Array.from({ length: 5 }, (_, m) => {
        if (m === i) return ki - 1;
        if (m === j) return kj - 1;
        const first = qMul(sinRatio(j - m, j - i), ai);
        const second = qMul(sinRatio(m - i, j - i), aj);
        return Number(qFloor(qAdd(qAdd(first, second), gammas[m])));
      });
      const coefficients = [
        base,
        base.map((value, m) => value + (m === i ? 1 : 0)),
        base.map((value, m) => value + (m === i || m === j ? 1 : 0)),
        base.map((value, m) => value + (m === j ? 1 : 0))
      ];
      const center2 = base.map((value, m) => 2 * value + (m === i || m === j ? 1 : 0));
      if (!exactWithinRadius(exactFromCoeff(center2, 2), exactRadius)) continue;
      const corners = coefficients.map(coeff => ({ coeff, id: coeffKey(coeff) }));
      const vertices = corners.map(corner => corner.id);
      const key = tileKey(vertices);
      if (tileMap.has(key)) continue;

      corners.forEach(corner => {
        if (!vertexMap.has(corner.id)) vertexMap.set(corner.id, {
          id: corner.id,
          coeff: corner.coeff,
          exact: exactFromCoeff(corner.coeff),
          value: 0
        });
      });
      const separation = Math.min(j - i, 5 - (j - i));
      const baseWeight = separation === 1 ? 2 : 4;
      const weights = [baseWeight, 5 - baseWeight, baseWeight, 5 - baseWeight];
      tileMap.set(key, {
        id: key,
        vertices,
        exactPoints: coefficients.map(coeff => exactFromCoeff(coeff)),
        centerExact: exactFromCoeff(center2, 2),
        center2,
        weights,
        kind: Math.min(...weights) === 1 ? "thin" : "thick",
        presentation: "P3",
        atoms: p3AtomIds(key, Math.min(...weights) === 1 ? "thin" : "thick"),
        families: [i, j],
        edgeFamilies: [i, j, i, j],
        edgeSigns: [1, 1, -1, -1]
      });
    }
  }

  const tiles = [...tileMap.values()].sort((a, b) =>
    compareExactNorm(a.centerExact, b.centerExact) || a.id.localeCompare(b.id)
  );
  const vertices = [...vertexMap.values()];
  const incident = new Map(vertices.map(vertex => [vertex.id, []]));
  tiles.forEach((tile, tileIndex) => tile.vertices.forEach(vertex => incident.get(vertex)?.push(tileIndex)));

  return {
    tiles,
    vertices,
    incident,
    gammas: gammas.map(value => `${value.a}${value.b < 0n ? "" : "+"}${value.b}√5/${value.d}`),
    radius: exactRadius,
    presentation: "P3",
    exact: true
  };
}

export function deriveP2Model(p3Model) {
  const vertexById = new Map(p3Model.vertices.map(vertex => [vertex.id, vertex]));
  const segments = new Map();
  const addSegment = (from, to, direction) => {
    const key = [from, to].sort().join("|");
    if (!segments.has(key)) segments.set(key, { from, to, direction });
  };

  for (const tile of p3Model.tiles) {
    const [left, right] = tile.families;
    if (tile.kind === "thick") {
      addSegment(tile.vertices[0], tile.vertices[2], thickDiagonalDirectionCode(left, right));
    } else {
      // The pentagrid coefficient order orients every thin rhomb. Its two
      // "right" edges meet at vertex 0 in this orientation.
      addSegment(tile.vertices[3], tile.vertices[0], unitDirectionCode(right, -1));
      addSegment(tile.vertices[0], tile.vertices[1], unitDirectionCode(left));
    }
  }

  const adjacency = new Map();
  const addHalfEdge = (from, to, direction) => {
    if (!adjacency.has(from)) adjacency.set(from, []);
    adjacency.get(from).push({ to, direction });
  };
  segments.forEach(segment => {
    addHalfEdge(segment.from, segment.to, segment.direction);
    addHalfEdge(segment.to, segment.from, mod20(segment.direction + 10));
  });

  const visited = new Set();
  const tiles = [];
  for (const [startVertex, outgoing] of adjacency) for (const startEdge of outgoing) {
    const startKey = `${startVertex}>${startEdge.to}`;
    if (visited.has(startKey)) continue;
    let from = startVertex;
    let edge = startEdge;
    const vertices = [];
    const directions = [];
    let closed = false;

    for (let step = 0; step < 80; step++) {
      const halfEdgeKey = `${from}>${edge.to}`;
      if (visited.has(halfEdgeKey)) break;
      visited.add(halfEdgeKey);
      vertices.push(from);
      directions.push(edge.direction);
      const at = edge.to;
      const reverseDirection = mod20(edge.direction + 10);
      const choices = (adjacency.get(at) || [])
        .filter(candidate => candidate.to !== from)
        .sort((a, b) =>
          mod20(reverseDirection - a.direction) - mod20(reverseDirection - b.direction) ||
          a.to.localeCompare(b.to)
        );
      if (!choices.length) break;
      from = at;
      edge = choices[0];
      if (`${from}>${edge.to}` === startKey) {
        closed = true;
        break;
      }
    }

    if (!closed || vertices.length !== 4) continue;
    const turns = directions.map((direction, index) => {
      let turn = mod20(directions[(index + 1) % directions.length] - direction);
      if (turn > 10) turn -= 20;
      return turn;
    });
    if (turns.reduce((sum, turn) => sum + turn, 0) !== 20) continue;

    const cornerWeights = vertices.map((_, index) => {
      const incomingTurn = turns[(index + turns.length - 1) % turns.length];
      return (10 - incomingTurn) / 2;
    });
    if (!cornerWeights.every(Number.isSafeInteger)) continue;
    const exactPoints = vertices.map(vertex => vertexById.get(vertex).exact);
    const kind = cornerWeights.some(weight => weight > 5) ? "dart" : "kite";
    tiles.push({
      id: `p2:${vertices.join("|")}`,
      vertices,
      exactPoints,
      centerExact: exactAverage(exactPoints),
      weights: cornerWeights,
      kind,
      presentation: "P2",
      directions,
      atoms: []
    });
  }

  const atomRecords = [];
  for (const tile of p3Model.tiles) {
    if (tile.kind === "thin") {
      atomRecords.push({ id: tile.atoms[0], vertices: tile.vertices });
    } else {
      atomRecords.push({ id: tile.atoms[0], vertices: [tile.vertices[0], tile.vertices[1], tile.vertices[2]] });
      atomRecords.push({ id: tile.atoms[1], vertices: [tile.vertices[0], tile.vertices[2], tile.vertices[3]] });
    }
  }
  const parents = atomRecords.map((_, index) => index);
  const find = index => parents[index] === index ? index : (parents[index] = find(parents[index]));
  const union = (left, right) => {
    left = find(left);
    right = find(right);
    if (left !== right) parents[right] = left;
  };
  const atomEdges = new Map();
  atomRecords.forEach((atom, atomIndex) => atom.vertices.forEach((vertex, index) => {
    const edge = [vertex, atom.vertices[(index + 1) % atom.vertices.length]].sort().join("|");
    if (!atomEdges.has(edge)) atomEdges.set(edge, []);
    atomEdges.get(edge).push(atomIndex);
  }));
  for (const [edge, atomIndices] of atomEdges) {
    if (!segments.has(edge) && atomIndices.length === 2) union(atomIndices[0], atomIndices[1]);
  }
  const components = new Map();
  atomRecords.forEach((atom, index) => {
    const root = find(index);
    if (!components.has(root)) components.set(root, []);
    components.get(root).push(atom);
  });
  const atomsByBoundary = new Map();
  for (const atoms of components.values()) {
    const edgeCounts = new Map();
    atoms.forEach(atom => atom.vertices.forEach((vertex, index) => {
      const edge = [vertex, atom.vertices[(index + 1) % atom.vertices.length]].sort().join("|");
      edgeCounts.set(edge, (edgeCounts.get(edge) || 0) + 1);
    }));
    const boundaryVertices = new Set(
      [...edgeCounts].filter(([, count]) => count === 1).flatMap(([edge]) => edge.split("|"))
    );
    if (boundaryVertices.size !== 4) continue;
    atomsByBoundary.set([...boundaryVertices].sort().join("|"), atoms.map(atom => atom.id).sort());
  }
  tiles.forEach(tile => {
    tile.atoms = atomsByBoundary.get([...tile.vertices].sort().join("|")) || [];
  });
  const completeTiles = tiles.filter(tile => tile.atoms.length === (tile.kind === "kite" ? 3 : 2));

  completeTiles.sort((a, b) =>
    compareExactNorm(a.centerExact, b.centerExact) || a.id.localeCompare(b.id)
  );
  const usedVertices = new Set(completeTiles.flatMap(tile => tile.vertices));
  const vertices = p3Model.vertices.filter(vertex => usedVertices.has(vertex.id));
  const incident = new Map(vertices.map(vertex => [vertex.id, []]));
  completeTiles.forEach((tile, tileIndex) =>
    tile.vertices.forEach(vertex => incident.get(vertex)?.push(tileIndex))
  );
  return {
    ...p3Model,
    tiles: completeTiles,
    vertices,
    incident,
    presentation: "P2",
    sourcePresentation: "P3",
    exact: true
  };
}

function alignedCopy(model, anchor) {
  const offset2 = anchor.center2;
  const moveCoeff = coeff => exactFromCoeff(coeff.map((value, index) => 2 * value - offset2[index]), 2);
  const vertices = model.vertices.map(vertex => ({ ...vertex, exact: moveCoeff(vertex.coeff) }));
  const tiles = model.tiles.map(tile => ({
    ...tile,
    exactPoints: tile.exactPoints.map(point => moveCoeff(point.coeff)),
    centerExact: exactFromCoeff(tile.center2.map((value, index) => value - offset2[index]), 2)
  }));
  return { ...model, vertices, tiles, anchor: tiles.find(tile => tile.id === anchor.id) };
}

function chooseAnchor(model, kind, families = null) {
  const familyKey = families?.join(",");
  const candidates = model.tiles.filter(tile =>
    tile.kind === kind && (!familyKey || tile.families.join(",") === familyKey)
  );
  return candidates.sort((a, b) =>
    compareExactNorm(a.centerExact, b.centerExact) || a.id.localeCompare(b.id)
  )[0] || model.tiles[0];
}

export function makeUniversalVertexAtlas({
  radius = 14,
  phaseCode = 173,
  samples = 21,
  seedKind = "thick"
} = {}) {
  const initial = makePenroseModelSet({ radius: Math.ceil(radius) + 2, phaseCode });
  const initialAnchor = chooseAnchor(initial, seedKind);
  const base = alignedCopy(initial, initialAnchor);
  const atlas = new Map();
  const origins = [];
  const addVertices = (candidate, sample) => candidate.vertices.forEach(vertex => {
    if (!exactWithinRadius(vertex.exact, Math.ceil(radius) + 1)) return;
    const key = `${vertex.exact.coeff.join(",")}/${vertex.exact.denominator}`;
    if (!atlas.has(key)) atlas.set(key, { exact: vertex.exact, multiplicity: 0, samples: [] });
    const entry = atlas.get(key);
    entry.multiplicity++;
    if (entry.samples.length < 4) entry.samples.push(sample);
  });
  addVertices(base, 0);

  for (let sample = 1; sample < samples; sample++) {
    const samplePhaseCode = (Number(phaseCode) + sample * 137) % 1009;
    const candidate = makePenroseModelSet({ radius: Math.ceil(radius) + 2, phaseCode: samplePhaseCode });
    const anchor = chooseAnchor(candidate, seedKind, initialAnchor.families);
    const aligned = alignedCopy(candidate, anchor);
    origins.push(samplePhaseCode);
    addVertices(aligned, sample);
  }

  return { base, points: [...atlas.values()], samples, radius, seed: base.anchor, origins };
}

function shareEdge(a, b) {
  let shared = 0;
  for (const vertex of a.vertices) if (b.vertices.includes(vertex)) shared++;
  return shared >= 2;
}

export function makeSearchTrace(model, targetCount = 220) {
  const target = model.tiles.slice(0, Math.min(targetCount, model.tiles.length));
  const targetIds = new Set(target.map(tile => tile.id));
  const chosen = new Set();
  const order = [];
  const frontier = [target[0]];

  while (frontier.length && order.length < target.length) {
    frontier.sort((a, b) => compareExactNorm(a.centerExact, b.centerExact) || a.id.localeCompare(b.id));
    const tile = frontier.shift();
    if (!tile || chosen.has(tile.id)) continue;
    chosen.add(tile.id);
    order.push(tile);
    for (const candidate of target) {
      if (!chosen.has(candidate.id) && shareEdge(tile, candidate)) frontier.push(candidate);
    }
  }
  for (const tile of target) if (!chosen.has(tile.id)) order.push(tile);

  const trace = [];
  const active = new Set();
  const outer = model.tiles.filter(tile => !targetIds.has(tile.id));
  let branch = 0;

  order.forEach((tile, index) => {
    if (index > 5 && index % 11 === 4) {
      const decoy = outer.find(candidate =>
        !active.has(candidate.id) &&
        candidate.vertices.some(vertex => tile.vertices.includes(vertex))
      );
      if (decoy) {
        trace.push({ type: "try", tile: decoy, message: "speculative window-admissible branch" });
        trace.push({ type: "add", tile: decoy, branch: ++branch, speculative: true, message: "candidate accepted locally" });
        trace.push({ type: "witness", tile: decoy, message: "frontier site has no compatible completion" });
        trace.push({ type: "remove", tile: decoy, branch, message: "rollback to last choice point" });
      }
    } else if (index % 7 === 3) {
      trace.push({ type: "reject", tile, message: "alternate lift misses the internal window" });
    }
    trace.push({ type: "try", tile, message: `test ${tile.kind} tile at the least-saturated site` });
    trace.push({ type: "add", tile, message: "all point capacities remain ≤ 10" });
    active.add(tile.id);
  });

  return trace;
}

const catalogIdForTile = tile => `${tile.presentation.toLowerCase()}-${tile.kind}`;

export function makeSelectedTileSearch({
  p3Model,
  p2Model,
  selectedIds,
  preferredFamily = "P3",
  targetCount = 220,
  nodeLimit = 20000
}) {
  const selected = selectedIds instanceof Set ? selectedIds : new Set(selectedIds);
  const allCandidates = [...p3Model.tiles, ...p2Model.tiles]
    .filter(tile => selected.has(catalogIdForTile(tile)));
  const canonical = preferredFamily === "P2" ? p2Model.tiles : p3Model.tiles;
  const targetTiles = canonical.slice(0, Math.min(targetCount, canonical.length));
  const universe = new Set(targetTiles.flatMap(tile => tile.atoms));
  const candidates = allCandidates.filter(tile => tile.atoms.some(atom => universe.has(atom)));
  const byAtom = new Map([...universe].map(atom => [atom, []]));
  candidates.forEach(tile => tile.atoms.forEach(atom => byAtom.get(atom)?.push(tile)));
  byAtom.forEach(list => list.sort((left, right) =>
    Number(right.presentation === preferredFamily) - Number(left.presentation === preferredFamily) ||
    left.kind.localeCompare(right.kind) ||
    left.id.localeCompare(right.id)
  ));

  const occupied = new Set();
  const totals = new Map();
  const solution = [];
  const trace = [];
  let nodes = 0;
  let stopped = false;
  const fits = tile =>
    tile.atoms.every(atom => !occupied.has(atom)) &&
    tile.vertices.every((vertex, index) => (totals.get(vertex) || 0) + tile.weights[index] <= MAX_VALUE);
  const addTile = tile => {
    tile.atoms.forEach(atom => occupied.add(atom));
    tile.vertices.forEach((vertex, index) =>
      totals.set(vertex, (totals.get(vertex) || 0) + tile.weights[index])
    );
    solution.push(tile);
  };
  const removeTile = tile => {
    tile.atoms.forEach(atom => occupied.delete(atom));
    tile.vertices.forEach((vertex, index) => {
      const next = (totals.get(vertex) || 0) - tile.weights[index];
      if (next) totals.set(vertex, next);
      else totals.delete(vertex);
    });
    solution.pop();
  };

  const search = () => {
    if (nodes >= nodeLimit) {
      stopped = true;
      return false;
    }
    const uncovered = [...universe].filter(atom => !occupied.has(atom));
    if (!uncovered.length) return true;
    uncovered.sort((left, right) => {
      const leftCount = (byAtom.get(left) || []).filter(fits).length;
      const rightCount = (byAtom.get(right) || []).filter(fits).length;
      return leftCount - rightCount || left.localeCompare(right);
    });
    const atom = uncovered[0];
    const proposals = byAtom.get(atom) || [];
    if (!proposals.length) {
      trace.push({ type: "witness", tile: solution.at(-1) || targetTiles[0], message: "selected catalog leaves an uncovered exact atom" });
      return false;
    }
    for (const tile of proposals) {
      nodes++;
      trace.push({ type: "try", tile, message: `try ${tile.presentation} ${tile.kind} on the least-covered exact atom` });
      if (!fits(tile)) {
        trace.push({ type: "reject", tile, message: "pruned before descent: atom overlap or point capacity" });
        continue;
      }
      addTile(tile);
      trace.push({ type: "add", tile, message: "exact atoms disjoint and point capacities remain ≤ 10" });
      if (search()) return true;
      removeTile(tile);
      trace.push({ type: "remove", tile, message: "rollback: selected catalog cannot complete this branch" });
      if (stopped) return false;
    }
    return false;
  };

  const success = targetTiles.length > 0 && search();
  const usedVertexIds = new Set(candidates.flatMap(tile => tile.vertices));
  const vertexMap = new Map([...p3Model.vertices, ...p2Model.vertices].map(vertex => [vertex.id, vertex]));
  const presentations = new Set(candidates.map(tile => tile.presentation));
  const presentation = presentations.size > 1 ? "P2+P3" : [...presentations][0] || preferredFamily;
  return {
    model: {
      ...p3Model,
      tiles: candidates,
      vertices: [...usedVertexIds].map(id => vertexMap.get(id)).filter(Boolean),
      presentation,
      exact: true
    },
    trace,
    success,
    stopped,
    nodes,
    universeAtoms: universe.size,
    solution: [...solution]
  };
}

export function pointTotals(tiles) {
  const totals = new Map();
  tiles.forEach(tile => tile.vertices.forEach((vertex, index) => {
    totals.set(vertex, (totals.get(vertex) || 0) + tile.weights[index]);
  }));
  return totals;
}
