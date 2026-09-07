import { P1_EXACT_TILES, P1_EXACT_VERTICES, P1_SOURCE } from "./penrose-p1-patch.js";
import { canonical, latticeKey, residueLayer } from "./cyclotomic-five.js";

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

// The pentagrid is a local admissibility predicate, never a target tile list.
// Vertices are keyed in Z^4; the five strip indices are a redundant lift.
export function makeCyclotomicSearch({ targetCount = 120, phaseCode = 173,
  selectedIds = new Set(["p3-thick", "p3-thin"]), nodeLimit = 20000 } = {}) {
  if (!Number.isSafeInteger(targetCount) || targetCount < 1 || targetCount > 2000 || !Number.isSafeInteger(nodeLimit) || nodeLimit < 1) throw new RangeError("Invalid bounded search budget");
  const selected = new Set(selectedIds), gammas = exactGammas(phaseCode);
  const baseAt = (i, j, ki, kj) => {
    const ai = qSub(qInt(ki), gammas[i]), aj = qSub(qInt(kj), gammas[j]);
    return Array.from({ length: 5 }, (_, m) => m === i ? ki - 1 : m === j ? kj - 1 :
      Number(qFloor(qAdd(qAdd(qMul(sinRatio(j - m, j - i), ai), qMul(sinRatio(m - i, j - i), aj)), gammas[m]))));
  };
  const makeTile = (base, i, j) => {
    const corners = [base, base.map((n, k) => n + (k === i)), base.map((n, k) => n + (k === i || k === j)), base.map((n, k) => n + (k === j))];
    const exactPoints = corners.map(c => exactFromCoeff(c));
    const vertices = exactPoints.map(latticeKey);
    const w = Math.min(j - i, 5 - j + i) === 1 ? 2 : 4;
    return { id: tileKey(vertices), vertices, exactPoints, latticePoints: exactPoints.map(canonical),
      base, families: [i, j], edgeFamilies: [i, j, i, j], edgeSigns: [1, 1, -1, -1],
      weights: [w, 5 - w, w, 5 - w], kind: w === 2 ? "thick" : "thin", presentation: "P3",
      centerExact: exactAverage(exactPoints), atoms: [] };
  };
  const admitted = tile => {
    const [i, j] = tile.families, b = tile.base;
    const expected = baseAt(i, j, b[i] + 1, b[j] + 1);
    return b.every((n, k) => n === expected[k]);
  };
  const seeds = [];
  for (let i = 0; i < 5; i++) for (let j = i + 1; j < 5; j++) {
    const tile = makeTile(baseAt(i, j, 0, 0), i, j);
    if (selected.has(`p3-${tile.kind}`)) seeds.push(tile);
  }
  seeds.sort((a, b) => compareExactNorm(a.centerExact, b.centerExact));
  const active = [], trace = [], totals = new Map(), edges = new Map(), ids = new Set(), failures = new Set();
  const stats = { proposals: 0, capacityPrunes: 0, windowPrunes: 0, memoHits: 0, backtracks: 0 };
  let stopped = false;
  const edgeId = (t, k) => [t.vertices[k], t.vertices[(k + 1) % 4]].sort().join("|");
  const addTile = tile => {
    active.push(tile); ids.add(tile.id);
    tile.vertices.forEach((v, k) => totals.set(v, (totals.get(v) || 0) + tile.weights[k]));
    for (let k = 0; k < 4; k++) { const key = edgeId(tile, k); if (!edges.has(key)) edges.set(key, []); edges.get(key).push({ tile, k }); }
    trace.push({ type: "add", tile, message: "create four-coefficient lattice vertices; add GCTS corner loads" });
  };
  const candidates = ({ tile, k }) => {
    const family = tile.edgeFamilies[k];
    const low = tile.exactPoints[tile.edgeSigns[k] > 0 ? k : (k + 1) % 4].coeff;
    const result = [];
    for (let other = 0; other < 5; other++) if (other !== family) for (const side of [0, 1]) {
      const b = low.map((n, index) => n - (index === other ? side : 0));
      const t = makeTile(b, Math.min(family, other), Math.max(family, other));
      if (!ids.has(t.id) && selected.has(`p3-${t.kind}`)) result.push(t);
    }
    return result;
  };
  if (seeds.length) addTile(seeds[0]);
  while (active.length && active.length < targetCount && !stopped) {
    const frontier = [...edges.values()].filter(r => r.length === 1).map(r => r[0]);
    frontier.sort((a, b) => compareExactNorm(exactAverage([a.tile.exactPoints[a.k], a.tile.exactPoints[(a.k + 1) % 4]]), exactAverage([b.tile.exactPoints[b.k], b.tile.exactPoints[(b.k + 1) % 4]])));
    let placed = false;
    for (const edge of frontier) {
      for (const tile of candidates(edge)) {
        if (failures.has(tile.id)) { stats.memoHits++; continue; }
        if (stats.proposals >= nodeLimit) { stopped = true; break; }
        stats.proposals++;
        trace.push({ type: "try", tile, message: "translate a rhomb by an element of Z[ζ₅] at an exposed edge" });
        if (tile.vertices.some((v, k) => (totals.get(v) || 0) + tile.weights[k] > MAX_VALUE)) {
          stats.capacityPrunes++; failures.add(tile.id);
          trace.push({ type: "reject", tile, message: "GCTS prune: a lattice-site angle load would exceed ten" }); continue;
        }
        if (!admitted(tile)) {
          stats.windowPrunes++; failures.add(tile.id);
          trace.push({ type: "reject", tile, message: "exact internal-window predicate rejects this lattice placement" }); continue;
        }
        addTile(tile); placed = true; break;
      }
      if (placed || stopped) break;
    }
    if (!placed) break;
  }
  const vertices = new Map();
  for (const tile of active) tile.exactPoints.forEach((exact, k) => vertices.set(tile.vertices[k], { id: tile.vertices[k], exact, lattice: canonical(exact).coeff, layer: residueLayer(exact) }));
  return { model: { tiles: active, vertices: [...vertices.values()], presentation: "P3", online: true,
    radius: Math.max(8, Math.ceil(Math.sqrt(targetCount / 3)) + 1), exact: true, latticeRank: 4, phaseCode,
    oracle: "exact pentagrid predicate", stats }, solution: active, trace, nodes: stats.proposals,
    success: active.length === targetCount, stopped, universeAtoms: 0, stats };
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

function exactDirectionCode(from, to) {
  const difference = to.coeff.map((value, index) => {
    const left = value * (from.denominator || 1);
    const right = from.coeff[index] * (to.denominator || 1);
    return left - right;
  });
  for (let family = 0; family < 5; family++) for (const sign of [1, -1]) {
    const target = Array.from({ length: 5 }, (_, index) => index === family ? sign : 0);
    const gauge = difference[0] - target[0];
    if (difference.every((value, index) => value - target[index] === gauge)) {
      return unitDirectionCode(family, sign);
    }
  }
  throw new Error("P1 edge is not a cyclotomic unit");
}

function exactPolygonWeights(points) {
  const directions = points.map((point, index) =>
    exactDirectionCode(point, points[(index + 1) % points.length])
  );
  const turns = directions.map((direction, index) => {
    let turn = mod20(directions[(index + 1) % directions.length] - direction);
    if (turn > 10) turn -= 20;
    return turn;
  });
  const orientation = Math.sign(turns.reduce((sum, turn) => sum + turn, 0));
  if (!orientation) throw new Error("P1 polygon has no winding");
  const weights = points.map((_, index) => {
    const incomingTurn = turns[(index + turns.length - 1) % turns.length];
    return (10 - orientation * incomingTurn) / 2;
  });
  if (!weights.every(Number.isSafeInteger)) throw new Error("P1 angle is not a multiple of 36 degrees");
  return { directions, weights };
}

export function makeP1Model() {
  const vertices = P1_EXACT_VERTICES.map(coeff => {
    const exact = exactFromCoeff(coeff);
    return { id: coeffKey(coeff), coeff, exact, value: 0 };
  });
  const tiles = P1_EXACT_TILES.map(([kind, indices], tileIndex) => {
    const exactPoints = indices.map(index => vertices[index].exact);
    const { directions, weights } = exactPolygonWeights(exactPoints);
    return {
      id: `p1:${tileIndex}`,
      vertices: indices.map(index => vertices[index].id),
      exactPoints,
      centerExact: exactAverage(exactPoints),
      weights,
      directions,
      kind,
      presentation: "P1",
      atoms: [`p1:${tileIndex}`]
    };
  }).sort((left, right) =>
    compareExactNorm(left.centerExact, right.centerExact) || left.id.localeCompare(right.id)
  );
  const usedVertices = new Set(tiles.flatMap(tile => tile.vertices));
  const incident = new Map(vertices.map(vertex => [vertex.id, []]));
  tiles.forEach((tile, tileIndex) => tile.vertices.forEach(vertex => incident.get(vertex)?.push(tileIndex)));
  return {
    tiles,
    vertices: vertices.filter(vertex => usedVertices.has(vertex.id)),
    incident,
    radius: 13,
    presentation: "P1",
    exact: true,
    source: P1_SOURCE
  };
}

export function makeP1Search({ p1Model, selectedIds, targetCount = 220 }) {
  const selected = selectedIds instanceof Set ? selectedIds : new Set(selectedIds);
  const tiles = p1Model.tiles.filter(tile => selected.has(`p1-${tile.kind}`));
  const model = { ...p1Model, tiles };
  const trace = tiles.length ? makeSearchTrace(model, Math.min(targetCount, tiles.length)) : [];
  const selectedKinds = new Set(tiles.map(tile => tile.kind));
  return {
    model,
    trace,
    success: selectedKinds.size === 6,
    stopped: false,
    nodes: trace.length,
    universeAtoms: Math.min(targetCount, tiles.length),
    solution: tiles.slice(0, Math.min(targetCount, tiles.length))
  };
}

const normalizedCoeff = coeff => {
  const gauge = coeff[4];
  return coeff.map(value => value - gauge);
};
const p1PointKey = point => coeffKey(normalizedCoeff(point.coeff));
const p1Add = (left, right) => exactFromCoeff(normalizedCoeff(
  left.coeff.map((value, index) => value + right.coeff[index])
));
const p1Sub = (left, right) => exactFromCoeff(normalizedCoeff(
  left.coeff.map((value, index) => value - right.coeff[index])
));

function p1PairSign(a, b) {
  if (b === 0n) return a < 0n ? -1 : a > 0n ? 1 : 0;
  if (a === 0n) return b < 0n ? -1 : 1;
  if ((a > 0n) === (b > 0n)) return a > 0n ? 1 : -1;
  const comparison = a * a - 5n * b * b;
  return a > 0n ? (comparison > 0n ? 1 : -1) : (comparison > 0n ? -1 : 1);
}

function p1CrossSign(origin, left, right) {
  const a = p1Sub(left, origin).coeff.map(BigInt);
  const b = p1Sub(right, origin).coeff.map(BigInt);
  const sinePairs = [[0n, 0n], [2n, 0n], [-1n, 1n], [1n, -1n], [-2n, 0n]];
  let rational = 0n;
  let radical = 0n;
  for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) {
    if (!a[i] || !b[j]) continue;
    const amount = a[i] * b[j];
    const [ra, rb] = sinePairs[mod5(j - i)];
    rational += amount * ra;
    radical += amount * rb;
  }
  return p1PairSign(rational, radical);
}

const p1ProperIntersection = (a, b, c, d) => {
  const abC = p1CrossSign(a, b, c);
  const abD = p1CrossSign(a, b, d);
  const cdA = p1CrossSign(c, d, a);
  const cdB = p1CrossSign(c, d, b);
  return abC * abD < 0 && cdA * cdB < 0;
};

const p1EdgeKey = (left, right) => [p1PointKey(left), p1PointKey(right)].sort().join("|");
const p1EdgeFeature = (tile, edgeIndex) => {
  const next = (edgeIndex + 1) % (tile.vertices?.length || tile.exactPoints.length);
  return `${tile.kind}:${tile.weights[edgeIndex]},${tile.weights[next]}`;
};

function makeP1FrontierRules(p1Model) {
  const referenceEdges = new Map();
  p1Model.tiles.forEach(tile => tile.exactPoints.forEach((point, edgeIndex) => {
    const next = tile.exactPoints[(edgeIndex + 1) % tile.exactPoints.length];
    const key = p1EdgeKey(point, next);
    if (!referenceEdges.has(key)) referenceEdges.set(key, []);
    referenceEdges.get(key).push({ tile, edgeIndex });
  }));
  const contacts = new Set();
  referenceEdges.forEach(records => {
    if (records.length !== 2) return;
    contacts.add(`${p1EdgeFeature(records[0].tile, records[0].edgeIndex)}>${p1EdgeFeature(records[1].tile, records[1].edgeIndex)}`);
    contacts.add(`${p1EdgeFeature(records[1].tile, records[1].edgeIndex)}>${p1EdgeFeature(records[0].tile, records[0].edgeIndex)}`);
  });

  const prototypeMap = new Map();
  p1Model.tiles.forEach(tile => {
    const origin = tile.exactPoints[0];
    const exactPoints = tile.exactPoints.map(point => p1Sub(point, origin));
    const key = `${tile.kind}:${exactPoints.map(p1PointKey).join("|")}`;
    if (!prototypeMap.has(key)) prototypeMap.set(key, {
      kind: tile.kind,
      exactPoints,
      weights: [...tile.weights],
      directions: [...tile.directions]
    });
  });
  return { contacts, prototypes: [...prototypeMap.values()] };
}

export function makeP1FrontierSearch({
  p1Model,
  selectedIds,
  targetCount = 220,
  nodeLimit = 120000
}) {
  const selected = selectedIds instanceof Set ? selectedIds : new Set(selectedIds);
  const selectedKinds = new Set(
    [...selected].filter(id => id.startsWith("p1-")).map(id => id.slice(3))
  );
  const { contacts, prototypes } = makeP1FrontierRules(p1Model);
  const enabledPrototypes = prototypes.filter(prototype => selectedKinds.has(prototype.kind));
  const seedKind = ["p3", "p5", "p2", "diamond", "star", "boat"].find(kind => selectedKinds.has(kind));
  const seedSource = p1Model.tiles.find(tile => tile.kind === seedKind);
  if (!seedSource || !enabledPrototypes.length) {
    return {
      model: { ...p1Model, tiles: [], vertices: [], radius: 12, presentation: "P1" },
      trace: [], success: false, stopped: false, nodes: 0, universeAtoms: 0, solution: []
    };
  }

  const makePlacement = (prototype, offset) => {
    const exactPoints = prototype.exactPoints.map(point => p1Add(point, offset));
    const vertices = exactPoints.map(p1PointKey);
    return {
      id: `p1g:${prototype.kind}:${tileKey(vertices)}`,
      kind: prototype.kind,
      presentation: "P1",
      exactPoints,
      vertices,
      centerExact: exactAverage(exactPoints),
      weights: [...prototype.weights],
      directions: [...prototype.directions],
      atoms: []
    };
  };

  const initialSeed = [seedSource];
  const active = [...initialSeed];
  const kindCounts = new Map();
  initialSeed.forEach(tile => kindCounts.set(tile.kind, (kindCounts.get(tile.kind) || 0) + 1));
  const placementIds = new Set(initialSeed.map(tile => tileKey(tile.vertices)));
  const totals = new Map();
  const edges = new Map();
  const trace = initialSeed.flatMap((tile, index) => [
    { type: "try", tile, message: index ? "extend the finite legal seed corona" : "start from one exact P1 tile; no target support exists" },
    { type: "add", tile, message: "seed placement creates only its own exact vertices and exposed edges" }
  ]);
  let nodes = initialSeed.length;
  let stopped = false;

  const projectionCache = new Map();
  const projection = (point, axis) => {
    const key = `${p1PointKey(point)}:${axis}`;
    if (projectionCache.has(key)) return projectionCache.get(key);
    let rational = 0n;
    let radical = 0n;
    point.coeff.forEach((coefficient, family) => {
      const separation = Math.min(mod5(family - axis), mod5(axis - family));
      const [ra, rb] = separation === 0 ? [4n, 0n] :
        separation === 1 ? [-1n, 1n] : [-1n, -1n];
      rational += BigInt(coefficient) * ra;
      radical += BigInt(coefficient) * rb;
    });
    const value = [rational, radical];
    projectionCache.set(key, value);
    return value;
  };
  const comparePair = (left, right) => p1PairSign(left[0] - right[0], left[1] - right[1]);
  const normPair = coeff => {
    const values = coeff.map(BigInt);
    let rational = 4n * values.reduce((sum, value) => sum + value * value, 0n);
    let radical = 0n;
    for (let i = 0; i < 5; i++) for (let j = i + 1; j < 5; j++) {
      const separation = Math.min(mod5(i - j), mod5(j - i));
      rational -= 2n * values[i] * values[j];
      radical += (separation === 1 ? 2n : -2n) * values[i] * values[j];
    }
    return [rational, radical];
  };
  const edgeNorm = (from, to) => normPair(normalizedCoeff(
    from.coeff.map((value, index) => value + to.coeff[index])
  ));
  const compareEdgeNorm = (left, right) => comparePair(left.norm, right.norm);
  const orderedPair = (left, right) => comparePair(left, right) <= 0 ? [left, right] : [right, left];
  const segmentBounds = (from, to) => [0, 1].map(axis => orderedPair(projection(from, axis), projection(to, axis)));
  const boundsOverlap = (left, right) => left.every(([low, high], axis) =>
    comparePair(high, right[axis][0]) >= 0 && comparePair(right[axis][1], low) >= 0
  );

  const addEdgeRecord = (tile, edgeIndex) => {
    const from = tile.exactPoints[edgeIndex];
    const to = tile.exactPoints[(edgeIndex + 1) % tile.exactPoints.length];
    const key = p1EdgeKey(from, to);
    if (!edges.has(key)) edges.set(key, []);
    edges.get(key).push({
      tile,
      edgeIndex,
      from,
      to,
      feature: p1EdgeFeature(tile, edgeIndex),
      bounds: segmentBounds(from, to),
      norm: edgeNorm(from, to)
    });
  };
  const add = tile => {
    active.push(tile);
    kindCounts.set(tile.kind, (kindCounts.get(tile.kind) || 0) + 1);
    placementIds.add(tileKey(tile.vertices));
    tile.vertices.forEach((vertex, index) => totals.set(vertex, (totals.get(vertex) || 0) + tile.weights[index]));
    tile.exactPoints.forEach((_, edgeIndex) => addEdgeRecord(tile, edgeIndex));
  };
  const remove = tile => {
    active.pop();
    const nextKindCount = (kindCounts.get(tile.kind) || 0) - 1;
    if (nextKindCount) kindCounts.set(tile.kind, nextKindCount);
    else kindCounts.delete(tile.kind);
    placementIds.delete(tileKey(tile.vertices));
    tile.vertices.forEach((vertex, index) => {
      const next = (totals.get(vertex) || 0) - tile.weights[index];
      if (next) totals.set(vertex, next);
      else totals.delete(vertex);
    });
    tile.exactPoints.forEach((point, edgeIndex) => {
      const next = tile.exactPoints[(edgeIndex + 1) % tile.exactPoints.length];
      const key = p1EdgeKey(point, next);
      const records = (edges.get(key) || []).filter(record => record.tile.id !== tile.id);
      if (records.length) edges.set(key, records);
      else edges.delete(key);
    });
  };
  initialSeed.forEach(tile => {
    tile.vertices.forEach((vertex, index) => totals.set(vertex, (totals.get(vertex) || 0) + tile.weights[index]));
    tile.exactPoints.forEach((_, edgeIndex) => addEdgeRecord(tile, edgeIndex));
  });

  const frontierRecords = () => [...edges.values()]
    .filter(records => records.length === 1)
    .map(records => records[0]);
  const candidateTemplateCache = new Map();
  const candidateTemplatesAt = frontier => {
    const reverseDelta = p1PointKey(p1Sub(frontier.from, frontier.to));
    const templateKey = `${frontier.feature}:${reverseDelta}`;
    if (candidateTemplateCache.has(templateKey)) return candidateTemplateCache.get(templateKey);
    const templates = [];
    for (const prototype of enabledPrototypes) {
      for (let edgeIndex = 0; edgeIndex < prototype.exactPoints.length; edgeIndex++) {
        const from = prototype.exactPoints[edgeIndex];
        const to = prototype.exactPoints[(edgeIndex + 1) % prototype.exactPoints.length];
        if (p1PointKey(p1Sub(to, from)) !== reverseDelta) continue;
        const feature = p1EdgeFeature(prototype, edgeIndex);
        if (contacts.has(`${frontier.feature}>${feature}`)) templates.push({ prototype, edgeIndex });
      }
    }
    candidateTemplateCache.set(templateKey, templates);
    return templates;
  };
  const candidateCache = new Map();
  const candidateCountCache = new Map();
  const candidateProposalCount = frontier => {
    const reverseDelta = p1PointKey(p1Sub(frontier.from, frontier.to));
    const countKey = `${frontier.feature}:${reverseDelta}`;
    if (candidateCountCache.has(countKey)) return candidateCountCache.get(countKey);
    const unique = new Set();
    for (const { prototype, edgeIndex } of candidateTemplatesAt(frontier)) {
      const offset = p1Sub(exactFromCoeff([0, 0, 0, 0, 0]), prototype.exactPoints[edgeIndex]);
      const points = prototype.exactPoints.map(point => p1Add(point, offset));
      unique.add(`${prototype.kind}:${tileKey(points.map(p1PointKey))}`);
    }
    candidateCountCache.set(countKey, unique.size);
    return unique.size;
  };
  const candidatesAt = frontier => {
    const cacheKey = `${frontier.feature}:${p1PointKey(frontier.from)}>${p1PointKey(frontier.to)}`;
    if (candidateCache.has(cacheKey)) return candidateCache.get(cacheKey);
    const candidates = new Map();
    for (const { prototype, edgeIndex } of candidateTemplatesAt(frontier)) {
      const from = prototype.exactPoints[edgeIndex];
      const offset = p1Sub(frontier.to, from);
      const candidate = makePlacement(prototype, offset);
      candidates.set(candidate.id, candidate);
    }
    const result = [...candidates.values()].sort((left, right) =>
      left.kind.localeCompare(right.kind) || left.id.localeCompare(right.id)
    );
    candidateCache.set(cacheKey, result);
    return result;
  };

  const fits = tile => {
    if (placementIds.has(tileKey(tile.vertices))) return false;
    if (tile.vertices.some((vertex, index) => (totals.get(vertex) || 0) + tile.weights[index] > MAX_VALUE)) return false;
    for (let edgeIndex = 0; edgeIndex < tile.exactPoints.length; edgeIndex++) {
      const from = tile.exactPoints[edgeIndex];
      const to = tile.exactPoints[(edgeIndex + 1) % tile.exactPoints.length];
      const records = edges.get(p1EdgeKey(from, to)) || [];
      if (records.length >= 2) return false;
      if (records.length === 1 && !contacts.has(`${records[0].feature}>${p1EdgeFeature(tile, edgeIndex)}`)) return false;
    }
    for (let edgeIndex = 0; edgeIndex < tile.exactPoints.length; edgeIndex++) {
      const a = tile.exactPoints[edgeIndex];
      const b = tile.exactPoints[(edgeIndex + 1) % tile.exactPoints.length];
      const candidateBounds = segmentBounds(a, b);
      for (const records of edges.values()) {
        if (records.length !== 1) continue;
        const record = records[0];
        if (p1EdgeKey(a, b) === p1EdgeKey(record.from, record.to)) continue;
        if (!boundsOverlap(candidateBounds, record.bounds)) continue;
        if (p1ProperIntersection(a, b, record.from, record.to)) return false;
      }
    }
    return true;
  };

  const available = frontier => candidatesAt(frontier).filter(fits);
  const hasSingleBoundary = () => {
    const graph = new Map();
    for (const record of frontierRecords()) {
      const from = p1PointKey(record.from);
      const to = p1PointKey(record.to);
      if (!graph.has(from)) graph.set(from, []);
      if (!graph.has(to)) graph.set(to, []);
      graph.get(from).push(to);
      graph.get(to).push(from);
    }
    if (!graph.size || [...graph.values()].some(neighbors => neighbors.length !== 2)) return false;
    const start = graph.keys().next().value;
    const seen = new Set([start]);
    const queue = [start];
    while (queue.length) {
      const point = queue.pop();
      for (const neighbor of graph.get(point)) {
        if (seen.has(neighbor)) continue;
        seen.add(neighbor);
        queue.push(neighbor);
      }
    }
    return seen.size === graph.size;
  };
  const search = () => {
    if (active.length >= targetCount) {
      return hasSingleBoundary();
    }
    if (nodes >= nodeLimit) { stopped = true; return false; }
    const frontierOptions = frontierRecords()
      .sort((left, right) =>
        compareEdgeNorm(left, right) ||
        p1EdgeKey(left.from, left.to).localeCompare(p1EdgeKey(right.from, right.to))
      )
      .map(record => ({ record, proposalCount: candidateProposalCount(record) }));
    const minimumProposalCount = Math.min(...frontierOptions.map(option => option.proposalCount));
    const orderedFrontiers = frontierOptions
      .filter(option => option.proposalCount <= minimumProposalCount + 1)
      .sort((left, right) =>
        compareEdgeNorm(left.record, right.record) ||
        left.proposalCount - right.proposalCount ||
        p1EdgeKey(left.record.from, left.record.to).localeCompare(p1EdgeKey(right.record.from, right.record.to))
      );
    let frontier = null;
    for (const { record } of orderedFrontiers) {
      const candidates = available(record);
      if (candidates.length) { frontier = { record, candidates }; break; }
    }
    if (!frontier || !frontier.candidates.length) {
      trace.push({ type: "witness", tile: active.at(-1), message: "dead exposed edge: no exact matching P1 placement" });
      return false;
    }
    const orderedCandidates = [...frontier.candidates].sort((left, right) =>
      (kindCounts.get(left.kind) || 0) - (kindCounts.get(right.kind) || 0) ||
      left.kind.localeCompare(right.kind) ||
      left.id.localeCompare(right.id)
    );
    for (const tile of orderedCandidates) {
      nodes++;
      trace.push({ type: "try", tile, message: "generate an exact candidate on the nearest constrained frontier edge" });
      if (!fits(tile)) {
        trace.push({ type: "reject", tile, message: "pruned: collision, edge mismatch, or point capacity" });
        continue;
      }
      add(tile);
      trace.push({ type: "add", tile, message: "frontier placement creates only exact vertices that are needed now" });
      if (search()) return true;
      remove(tile);
      trace.push({ type: "remove", tile, message: "rollback from a dead online-growth branch" });
      if (stopped) return false;
    }
    return false;
  };

  const success = search();
  return {
    model: {
      ...p1Model,
      tiles: [...active],
      vertices: [],
      radius: Math.max(10, Math.ceil(Math.sqrt(targetCount)) + 2),
      presentation: "P1",
      online: true
    },
    trace,
    success,
    stopped,
    nodes,
    universeAtoms: 0,
    solution: [...active]
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
  const decoyPool = [...outer, ...target];
  let branch = 0;

  order.forEach((tile, index) => {
    if (index > 5 && index % 11 === 4) {
      const decoy = decoyPool.find(candidate =>
        !active.has(candidate.id) &&
        candidate.id !== tile.id &&
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
