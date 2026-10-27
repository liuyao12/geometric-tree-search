/** Exact geometry and regular six-grid dual construction.
 * This is a specialized geometric construction, not the GCTS point-value
 * baseline and not an implementation of Ammann's decorated matching rules.
 */
import { Golden, ZERO, ONE, TAU, vector, vadd, vsub, vscale, dot, cross,
  determinant, inverseColumns, intersectPlanes, pointKey } from "./golden-field.js";

export const STAR = Object.freeze([
  vector(0n, 1n, TAU), vector(0n, -1n, TAU),
  vector(1n, TAU, 0n), vector(-1n, TAU, 0n),
  vector(TAU, 0n, 1n), vector(TAU, 0n, -1n)
]);
export const DEFAULT_SHIFTS = Object.freeze([11n, 13n, 17n, 19n, 23n, 29n].map(p => new Golden(1n, 0n, p)));
export const TRIPLES = Object.freeze(Array.from({ length: 6 }, (_, i) =>
  Array.from({ length: 5 - i }, (_, d) => {
    const j = i + d + 1;
    return Array.from({ length: 5 - j }, (_, e) => Object.freeze([i, j, j + e + 1]));
  }).flat()).flat());

export function projectLift(lift) {
  if (!Array.isArray(lift) || lift.length !== 6 || !lift.every(x => typeof x === "bigint")) {
    throw new TypeError("Expected six bigint lift coordinates");
  }
  return lift.reduce((sum, n, i) => vadd(sum, vscale(STAR[i], n)), vector(0n, 0n, 0n));
}

export function makeRhombohedron(axes, origin = vector(0n, 0n, 0n)) {
  if (!Array.isArray(axes) || axes.length !== 3 ||
    !axes.every(i => Number.isInteger(i) && i >= 0 && i < 6) || new Set(axes).size !== 3) {
    throw new TypeError("Expected three distinct star-axis indices");
  }
  pointKey(origin); // Validate and take an immutable copy of caller-owned data.
  origin = vector(...origin);
  axes = [...axes].sort((a, b) => a - b);
  const edges = axes.map(i => STAR[i]);
  const volume = determinant(...edges).abs();
  const kind = volume.equals(TAU.mul(2n)) ? "oblate" : "prolate";
  if (!volume.equals(TAU.mul(2n)) && !volume.equals(TAU.add(ONE).mul(2n))) throw new Error("Unexpected volume");
  const vertices = Array.from({ length: 8 }, (_, mask) => edges.reduce((p, e, i) =>
    mask & (1 << i) ? vadd(p, e) : p, origin));
  const faces = [];
  for (let axis = 0; axis < 3; axis++) for (let side = 0; side < 2; side++) {
    const [a, b] = [0, 1, 2].filter(i => i !== axis);
    const base = side << axis;
    let indices = [base, base | (1 << a), base | (1 << a) | (1 << b), base | (1 << b)];
    const normal = cross(vsub(vertices[indices[1]], vertices[base]), vsub(vertices[indices[3]], vertices[base]));
    if (dot(normal, edges[axis]).sign() !== (side ? 1 : -1)) indices = indices.reverse();
    faces.push(Object.freeze(indices));
  }
  return Object.freeze({ axes: Object.freeze(axes), kind, origin, edges: Object.freeze(edges),
    volume, vertices: Object.freeze(vertices), faces: Object.freeze(faces),
    inverse: inverseColumns(...edges), id: vertices.map(pointKey).sort().join("|") });
}

export const ORIENTATIONS = Object.freeze(TRIPLES.map(axes => makeRhombohedron(axes)));

export const INTERNAL_STAR = Object.freeze(STAR.map(v => vector(...v.map(x => x.conjugate()))));
const WINDOW_CENTER = vscale(INTERNAL_STAR.reduce(vadd, vector(0n, 0n, 0n)), new Golden(1n, 0n, 2n));
const WINDOW_SLABS = Object.freeze(INTERNAL_STAR.flatMap((u, i) => INTERNAL_STAR.slice(i + 1).map(v => {
  const normal = cross(u, v);
  const halfWidth = INTERNAL_STAR.reduce((s, w) => s.add(dot(normal, w).abs()), ZERO).div(2n);
  return Object.freeze({ normal, halfWidth });
})));

/** -1 outside, 0 on the boundary, +1 strictly inside the internal-space
 * zonotope sum_i [0,1]*conjugate(STAR[i]). No convex-hull tolerance.
 */
export function classifyWindow(point) {
  const centered = vsub(point, WINDOW_CENTER);
  let boundary = false;
  for (const { normal, halfWidth } of WINDOW_SLABS) {
    const comparison = dot(normal, centered).abs().compare(halfWidth);
    if (comparison > 0) return -1;
    if (comparison === 0) boundary = true;
  }
  return boundary ? 0 : 1;
}

export function internalPoint(lift, shifts = DEFAULT_SHIFTS) {
  projectLift(lift); // Validate the integer lift before using it.
  checkShifts(shifts);
  return INTERNAL_STAR.reduce((s, u, i) => vadd(s, vscale(u, new Golden(lift[i]).sub(shifts[i]))), vector(0n, 0n, 0n));
}

export function containsPoint(tile, point, { strict = false } = {}) {
  const delta = vsub(point, tile.origin);
  return tile.inverse.every(row => {
    const x = dot(row, delta);
    return strict ? x.sign() > 0 && x.compare(ONE) < 0 : x.sign() >= 0 && x.compare(ONE) <= 0;
  });
}

/** Positive-volume overlap of parallelepipeds by the complete separating
 * axis test: face normals of both solids and all edge cross products.
 * Shared vertices, edges and faces are legal (no interior overlap).
 */
export function interiorsOverlap(a, b) {
  const axes = [a, b].flatMap(t => [cross(t.edges[0], t.edges[1]), cross(t.edges[1], t.edges[2]), cross(t.edges[2], t.edges[0])]);
  for (const u of a.edges) for (const v of b.edges) axes.push(cross(u, v));
  for (const axis of axes) {
    if (!axis.some(x => x.sign())) continue;
    const interval = t => {
      let low = dot(axis, t.origin), high = low;
      for (const e of t.edges) {
        const d = dot(axis, e);
        if (d.sign() < 0) low = low.add(d); else high = high.add(d);
      }
      return [low, high];
    };
    const [al, ah] = interval(a), [bl, bh] = interval(b);
    if (ah.compare(bl) <= 0 || bh.compare(al) <= 0) return false;
  }
  return true;
}

/** Complete vertex alignments within the explicitly declared 20 undeco-
 * rated orientations. This does not test capacity or impose matching rules.
 */
export function vertexCandidates(point) {
  const result = new Map();
  for (const t of ORIENTATIONS) for (const vertex of t.vertices) {
    const placed = makeRhombohedron(t.axes, vsub(point, vertex));
    result.set(placed.id, placed);
  }
  return [...result.values()];
}

/** A sufficient GLOBAL regularity certificate for rational shifts.
 * A four-plane dependency has cofactor coefficients c in Z[tau]. If
 * sum(c_i*shift_i) is not in Z[tau], it cannot equal sum(c_i*k_i).
 * Failure to certify is inconclusive; the generator still rejects every
 * singular intersection it actually encounters.
 */
export function certifyRegularShifts(shifts) {
  checkShifts(shifts);
  const obstructions = [];
  for (let i = 0; i < 3; i++) for (let j = i + 1; j < 4; j++)
    for (let k = j + 1; k < 5; k++) for (let l = k + 1; l < 6; l++) {
      const indices = [i, j, k, l];
      const residue = indices.reduce((sum, index, n) => {
        const cofactor = determinant(...indices.filter((_, m) => m !== n).map(m => STAR[m]));
        return sum.add(cofactor.mul(n % 2 ? shifts[index].neg() : shifts[index]));
      }, ZERO);
      if (residue.d === 1n) obstructions.push(indices);
    }
  return { certified: obstructions.length === 0, inconclusiveQuadruples: obstructions };
}

function checkShifts(shifts) {
  if (!Array.isArray(shifts) || shifts.length !== 6 || !shifts.every(s => s instanceof Golden)) {
    throw new TypeError("Expected six exact grid shifts");
  }
}

export function tileAtIntersection(axes, levels, shifts = DEFAULT_SHIFTS) {
  checkShifts(shifts);
  const prototype = makeRhombohedron(axes);
  // Reject reordered input rather than silently permuting the levels.
  if (axes.some((a, i) => a !== prototype.axes[i])) throw new TypeError("Grid axes must be sorted");
  if (!Array.isArray(levels) || levels.length !== 3 || !levels.every(k => typeof k === "bigint")) {
    throw new TypeError("Expected three bigint plane levels");
  }
  const intersection = intersectPlanes(axes.map(i => STAR[i]), levels.map((k, j) => new Golden(k).sub(shifts[axes[j]])));
  const lift = STAR.map((normal, i) => {
    const slot = axes.indexOf(i);
    if (slot >= 0) return levels[slot];
    const value = dot(normal, intersection).add(shifts[i]);
    if (value.isInteger()) throw new RangeError("Singular multigrid: four or more planes meet; choose regular shifts");
    return value.ceil();
  });
  const tile = makeRhombohedron(axes, projectLift(lift));
  return Object.freeze({ ...tile, lift: Object.freeze(lift), levels: Object.freeze([...levels]), intersection });
}

/** Enumerate ALL triple intersections with each selected plane level in
 * [-radius,radius]. This is a grid-index crop, not a filled ball or a target
 * exact-cover search. It can have a jagged boundary or disconnected pieces.
 */
export function makeIcosahedralPatch({ radius = 1, shifts = DEFAULT_SHIFTS } = {}) {
  if (!Number.isSafeInteger(radius) || radius < 0) throw new RangeError("Radius must be a nonnegative safe integer");
  checkShifts(shifts);
  const r = BigInt(radius), tiles = [];
  for (const axes of TRIPLES) for (let a = -r; a <= r; a++)
    for (let b = -r; b <= r; b++) for (let c = -r; c <= r; c++) {
      tiles.push(tileAtIntersection(axes, [a, b, c], shifts));
    }
  const counts = { oblate: 0, prolate: 0 };
  for (const tile of tiles) counts[tile.kind]++;
  return { format: "icosahedral-six-grid-v1", arithmetic: "Q(tau); tau^2=tau+1; bigint",
    result: "finite patch of a specialized multigrid construction",
    radius, shifts: [...shifts], regularity: certifyRegularShifts(shifts), counts, tiles };
}
