import assert from "node:assert/strict";
import { Golden, ZERO, ONE, TAU, vector, vadd, vsub, vscale, dot, cross,
  determinant, inverseColumns, intersectPlanes, pointKey } from "../assets/golden-field.js";
import { STAR, TRIPLES, ORIENTATIONS, DEFAULT_SHIFTS, projectLift, makeRhombohedron,
  containsPoint, interiorsOverlap, vertexCandidates, certifyRegularShifts,
  tileAtIntersection, makeIcosahedralPatch, INTERNAL_STAR, classifyWindow, internalPoint } from "../assets/icosahedral-exact.js";

assert(TAU.mul(TAU).equals(TAU.add(ONE)));
assert(TAU.inv().equals(TAU.sub(ONE)));
assert(TAU.conjugate().equals(ONE.sub(TAU)));
assert.equal(new Golden(6n, 9n, -3n).key(), "-2,-3,1");
assert.equal(new Golden(0n, 0n, 987n).key(), "0,0,1");
assert.throws(() => new Golden(1), TypeError);
assert.throws(() => new Golden("0.1"), TypeError);
assert.throws(() => new Golden(1n, 0n, 0n), RangeError);
assert.throws(() => ZERO.inv(), RangeError);
assert.throws(() => Number(TAU), TypeError);
assert.throws(() => Golden.fromJSON(["1", "2"]), TypeError);

// An independent ordering oracle: bracket sqrt(5) by rational decimal
// endpoints, using only integers. None of these test values straddles zero.
const scale = 10n ** 40n;
const lower = 22360679774997896964091736687312762354406n;
assert(lower * lower < 5n * scale * scale);
assert((lower + 1n) ** 2n > 5n * scale * scale);
let scalarCases = 0;
for (let a = -8n; a <= 8n; a++) for (let b = -8n; b <= 8n; b++) for (const d of [1n, 3n, 11n]) {
  const x = new Golden(a, b, d);
  const p = (2n * a + b) * scale + b * lower;
  const q = p + b;
  const expected = a === 0n && b === 0n ? 0 : p > 0n && q > 0n ? 1 : p < 0n && q < 0n ? -1 : null;
  assert.notEqual(expected, null);
  assert.equal(x.sign(), expected);
  const f = x.floor();
  assert(x.compare(f) >= 0 && x.compare(f + 1n) < 0);
  assert.equal(x.ceil(), x.isInteger() ? f : f + 1n);
  assert(x.add(x.neg()).equals(ZERO));
  assert(x.conjugate().conjugate().equals(x));
  if (x.sign()) assert(x.mul(x.inv()).equals(ONE));
  const y = new Golden(b - 2n, a + 1n, 7n);
  assert(x.mul(y).conjugate().equals(x.conjugate().mul(y.conjugate())));
  assert(Golden.fromJSON(JSON.parse(JSON.stringify(x))).equals(x));
  scalarCases++;
}

// Severe cancellation: far beyond IEEE precision, with a known sign from
// the negative conjugate of tau. Floor and ceil must not round it to zero.
const n = 1000n, fib = [0n, 1n];
for (let i = 0n; i < n; i++) [fib[0], fib[1]] = [fib[1], fib[0] + fib[1]];
const tiny = new Golden(-fib[1], fib[0]);
assert.equal(tiny.sign(), -1);
assert.equal(tiny.floor(), -1n);
assert.equal(tiny.ceil(), 0n);
assert(TAU.pow(-1000n).mul(TAU.pow(1000n)).equals(ONE));

assert.equal(TRIPLES.length, 20);
assert.equal(ORIENTATIONS.filter(t => t.kind === "oblate").length, 10);
assert.equal(ORIENTATIONS.filter(t => t.kind === "prolate").length, 10);
const edgeSquared = TAU.add(2n);
for (const u of STAR) assert(dot(u, u).equals(edgeSquared));
for (let i = 0; i < 6; i++) for (let j = i + 1; j < 6; j++) {
  assert(dot(STAR[i], STAR[j]).abs().equals(TAU));
  // Face diagonal squared-length ratio is tau^2, without taking roots.
  const plus = dot(vadd(STAR[i], STAR[j]), vadd(STAR[i], STAR[j]));
  const minus = dot(vsub(STAR[i], STAR[j]), vsub(STAR[i], STAR[j]));
  assert((plus.compare(minus) > 0 ? plus.div(minus) : minus.div(plus)).equals(TAU.pow(2n)));
}
const prolate = ORIENTATIONS.find(t => t.kind === "prolate");
const oblate = ORIENTATIONS.find(t => t.kind === "oblate");
assert.equal(makeRhombohedron([0, 1, 4]).kind, "prolate");
assert.equal(makeRhombohedron([0, 1, 2]).kind, "oblate");
assert(prolate.volume.div(oblate.volume).equals(TAU));

for (const t of ORIENTATIONS) {
  const inverse = inverseColumns(...t.edges);
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) assert(dot(inverse[i], t.edges[j]).equals(i === j ? ONE : ZERO));
  const center = vscale(t.edges.reduce(vadd, t.origin), new Golden(1n, 0n, 2n));
  assert(containsPoint(t, center, { strict: true }));
  for (const vertex of t.vertices) {
    assert(containsPoint(t, vertex));
    assert(!containsPoint(t, vertex, { strict: true }));
  }
  assert(!containsPoint(t, vscale(t.edges[0], 2n)));
  for (const face of t.faces) {
    const [a, b, , d] = face.map(i => t.vertices[i]);
    const normal = cross(vsub(b, a), vsub(d, a));
    assert(dot(normal, vsub(center, a)).sign() < 0, "Outward face orientation");
  }
  assert(interiorsOverlap(t, t));
  assert(interiorsOverlap(t, makeRhombohedron(t.axes, vscale(t.edges[0], new Golden(1n, 0n, 2n)))));
  assert(!interiorsOverlap(t, makeRhombohedron(t.axes, t.edges[0])), "Shared face must be legal");
  assert(!interiorsOverlap(t, makeRhombohedron(t.axes, vscale(t.edges[0], 2n))));
}
assert.throws(() => intersectPlanes([STAR[0], STAR[0], STAR[1]], [ONE, ONE, ONE]), RangeError);
assert.throws(() => makeRhombohedron([0, 0, 1]), TypeError);
assert.throws(() => projectLift([0, 0, 0, 0, 0, 0]), TypeError);
const candidates = vertexCandidates(vector(0n, 0n, 0n));
assert.equal(candidates.length, 160);
assert.equal(new Set(candidates.map(t => t.id)).size, 160);
assert(candidates.every(t => t.vertices.some(p => pointKey(p) === pointKey(vector(0n, 0n, 0n)))));

assert(certifyRegularShifts(DEFAULT_SHIFTS).certified);
assert(!certifyRegularShifts(Array(6).fill(ZERO)).certified);
assert.throws(() => makeIcosahedralPatch({ radius: 0, shifts: Array(6).fill(ZERO) }), /Singular multigrid/);
assert.throws(() => makeIcosahedralPatch({ radius: -1 }), RangeError);
assert.throws(() => tileAtIntersection([1, 0, 2], [0n, 0n, 0n]), /sorted/);
const patch = makeIcosahedralPatch({ radius: 1 });
assert.equal(patch.tiles.length, 540);
assert.equal(patch.counts.oblate, 270);
assert.equal(patch.counts.prolate, 270);
assert.equal(new Set(patch.tiles.map(t => t.id)).size, 540);
for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
  assert(STAR.reduce((s, u, k) => s.add(u[i].mul(INTERNAL_STAR[k][j])), ZERO).equals(ZERO));
}
const facetNormal = cross(INTERNAL_STAR[0], INTERNAL_STAR[1]);
const facetPoint = INTERNAL_STAR.reduce((s, u) => dot(facetNormal, u).sign() > 0 ? vadd(s, u) : s, vector(0n, 0n, 0n));
assert.equal(classifyWindow(facetPoint), 0);
assert.equal(classifyWindow(vector(100n, 100n, 100n)), -1);
assert.equal(classifyWindow(vscale(INTERNAL_STAR.reduce(vadd, vector(0n, 0n, 0n)), new Golden(1n, 0n, 2n))), 1);
assert.deepEqual(makeIcosahedralPatch({ radius: 0 }).tiles.map(t => t.id),
  patch.tiles.filter(t => t.levels.every(k => k === 0n)).map(t => t.id));

// Independently realize all eight cells adjacent to each triple intersection.
// Choose an exact perturbation smaller than every other grid-plane distance,
// then recover the six cell labels by ceiling. This detects floor/ceil shifts
// and incorrect base vertices without relying on the tile constructor.
for (const t of patch.tiles) for (let mask = 0; mask < 8; mask++) {
  const direction = intersectPlanes(t.axes.map(i => STAR[i]), t.axes.map((_, j) => new Golden(mask & (1 << j) ? 1n : -1n)));
  let epsilon = new Golden(1n, 0n, 4n);
  for (let j = 0; j < 6; j++) if (!t.axes.includes(j)) {
    const q = dot(STAR[j], t.intersection).add(DEFAULT_SHIFTS[j]);
    const dl = q.sub(q.floor()), dh = new Golden(q.ceil()).sub(q);
    const speed = dot(STAR[j], direction).abs();
    if (speed.sign()) {
      const safe = (dl.compare(dh) < 0 ? dl : dh).div(speed.mul(2n));
      if (safe.compare(epsilon) < 0) epsilon = safe;
    }
  }
  const p = vadd(t.intersection, vscale(direction, epsilon));
  const labels = STAR.map((u, i) => dot(u, p).add(DEFAULT_SHIFTS[i]).ceil());
  const expectedLift = [...t.lift];
  t.axes.forEach((axis, j) => { if (mask & (1 << j)) expectedLift[axis]++; });
  assert.deepEqual(labels, expectedLift);
  assert.equal(pointKey(projectLift(labels)), pointKey(t.vertices[mask]));
  assert.equal(classifyWindow(internalPoint(labels)), 1, "Independent internal-space window check");
}

// Exhaustive pair checks on the whole crop, independent of grid labels.
// An exact axis-aligned interval prefilter avoids expensive SAT when disjoint.
const boxes = patch.tiles.map(t => [0, 1, 2].map(axis => {
  const sorted = t.vertices.map(v => v[axis]).sort((a, b) => a.compare(b));
  return [sorted[0], sorted.at(-1)];
}));
let pairs = 0;
for (let i = 0; i < patch.tiles.length; i++) for (let j = i + 1; j < patch.tiles.length; j++) {
  pairs++;
  if (boxes[i].some(([low, high], k) => high.compare(boxes[j][k][0]) <= 0 || boxes[j][k][1].compare(low) <= 0)) continue;
  assert(!interiorsOverlap(patch.tiles[i], patch.tiles[j]), `Overlap ${i},${j}`);
}
const faces = new Map();
for (const t of patch.tiles) for (const face of t.faces) {
  const id = face.map(i => pointKey(t.vertices[i])).sort().join("|");
  const owners = faces.get(id) ?? [];
  owners.push(t); faces.set(id, owners);
}
assert([...faces.values()].every(owners => owners.length <= 2));
assert([...faces.values()].some(owners => owners.length === 2));
console.log(`ok: ${scalarCases} scalar cases, 1000th Fibonacci cancellation, 20 orientations, 540 tiles, 4320 dual-cell/window witnesses, ${pairs} pair checks`);
