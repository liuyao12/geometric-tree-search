import { canonical, cycloAdd, cycloMultiply, embedding } from './cyclotomic-five.js?v=20260908-speed';

export function validateExtent(extent) {
  if (!Number.isFinite(extent) || extent < 0 || extent > 4 || !Number.isInteger(extent * 4)) throw new RangeError('Extent must be 0–4 in quarter steps');
}
const subtract = (a, b) => cycloAdd(a, { ...canonical(b), coeff: canonical(b).coeff.map(n => -n) });
export function extendBar(bar, extent) {
  validateExtent(extent);
  const extra = cycloMultiply(subtract(bar.to, bar.from), { coeff: [extent * 4, 0, 0, 0], denominator: 4 });
  return { ...bar, from: subtract(bar.from, extra), to: cycloAdd(bar.to, extra) };
}
const sine = [[0n, 0n], [2n, 0n], [-1n, 1n], [1n, -1n], [-2n, 0n]];
const sign = (a, b) => {
  if (!b) return a < 0n ? -1 : a > 0n ? 1 : 0;
  if (!a) return b < 0n ? -1 : 1;
  if ((a > 0n) === (b > 0n)) return a > 0n ? 1 : -1;
  const d = a * a - 5n * b * b;
  return a > 0n ? d > 0n ? 1 : -1 : d > 0n ? -1 : 1;
};
// Exact orientation of rational cyclotomic points. Positive denominators drop
// out of the sign, unlike an integer-only corner test.
const exactPoints = new WeakMap();
function exact(point) {
  if (!exactPoints.has(point)) {
    const p = canonical(point);
    exactPoints.set(point, { c: p.coeff.map(BigInt), d: BigInt(p.denominator) });
  }
  return exactPoints.get(point);
}
export function rationalOrientation(a, b, c) {
  a = exact(a); b = exact(b); c = exact(c);
  const u = b.c.map((n, i) => n * a.d - a.c[i] * b.d);
  const v = c.c.map((n, i) => n * a.d - a.c[i] * c.d);
  let x = 0n, y = 0n;
  for (let i = 0; i < 4; i++) for (let j = i + 1; j < 4; j++) {
    const f = u[i] * v[j] - u[j] * v[i], [p, q] = sine[j - i]; x += f * p; y += f * q;
  }
  return sign(x, y);
}

const conjugate = p => {
  p = canonical(p); const coeff = [p.coeff[0], 0, 0, 0, 0];
  for (let i = 1; i < 4; i++) coeff[5 - i] = p.coeff[i];
  return canonical({ coeff, denominator: p.denominator });
};
function between(point, a, b) {
  if (rationalOrientation(a, b, point)) return false;
  const product = cycloMultiply(subtract(point, a), conjugate(subtract(point, b)));
  const c = product.coeff.map(BigInt);
  // Four times the real part: 4c0-c1-c2-c3 + √5(c1-c2-c3).
  return sign(4n * c[0] - c[1] - c[2] - c[3], c[1] - c[2] - c[3]) <= 0;
}
const box = points => {
  const p = points.map(p => embedding(p));
  return { x0: Math.min(...p.map(p => p.x)), x1: Math.max(...p.map(p => p.x)), y0: Math.min(...p.map(p => p.y)), y1: Math.max(...p.map(p => p.y)) };
};
const separated = (a, b) => a.x1 < b.x0 - 1e-8 || b.x1 < a.x0 - 1e-8 || a.y1 < b.y0 - 1e-8 || b.y1 < a.y0 - 1e-8;
const prepared = new WeakMap();
function prepare(tile, state, extent) {
  if (!prepared.has(state)) prepared.set(state, new Map());
  const cache = prepared.get(state);
  if (!cache.has(extent)) {
    const bars = state.bars.map(bar => { const extended = extendBar(bar, extent); return { ...extended, box: box([extended.from, extended.to]) }; });
    cache.set(extent, { points: tile.exactPoints, winding: rationalOrientation(...tile.exactPoints.slice(0, 3)), box: box(tile.exactPoints), bars });
  }
  return cache.get(extent);
}
function conflicts(bar, targetBar, target) {
  if (separated(bar.box, target.box)) return false;
  // In the same direction, equality of the infinite line means all of its
  // intersections with the target tile agree with that tile's stripe.
  if (!rationalOrientation(targetBar.from, targetBar.to, bar.from) && !rationalOrientation(targetBar.from, targetBar.to, bar.to)) return false;
  const sides = target.points.map((p, i) => [
    target.winding * rationalOrientation(p, target.points[(i + 1) % 4], bar.from),
    target.winding * rationalOrientation(p, target.points[(i + 1) % 4], bar.to)
  ]);
  // A non-collinear segment crossing the tile interior disagrees with m=0
  // somewhere there. Strict separating axes detect positive-length overlap.
  const along = target.points.map(p => rationalOrientation(bar.from, bar.to, p));
  if (!sides.some(([a, b]) => a <= 0 && b <= 0) && along.some(n => n < 0) && along.some(n => n > 0)) return true;
  // Include isolated boundary contacts, with no tolerance-based decision.
  for (const [i, p] of [bar.from, bar.to].entries()) {
    if (sides.every(pair => pair[i] >= 0) && rationalOrientation(targetBar.from, targetBar.to, p)) return true;
  }
  return target.points.some(p => between(p, bar.from, bar.to) && rationalOrientation(targetBar.from, targetBar.to, p));
}

// For each family, support is the closed tile plus that family's extended
// segment; value is 1 on the bar and 0 elsewhere in the tile, undefined beyond
// this support. Different families are separate components. Segment/segment
// overlap in one family can only be collinear and therefore agrees (1=1).
function compatible(a, sa, b, sb, extent) {
  validateExtent(extent); if (!extent) return true;
  const pa = prepare(a, sa, extent), pb = prepare(b, sb, extent);
  for (const bar of pa.bars) if (conflicts(bar, pb.bars.find(b => b.family === bar.family), pb)) return false;
  for (const bar of pb.bars) if (conflicts(bar, pa.bars.find(a => a.family === bar.family), pa)) return false;
  return true;
}

const pairs = new WeakMap();
export function extensionStatesCompatible(a, sa, b, sb, extent) {
  validateExtent(extent); if (!extent) return true;
  if (!pairs.has(sa)) pairs.set(sa, new WeakMap());
  const byState = pairs.get(sa);
  if (!byState.has(sb)) byState.set(sb, new Map());
  const byExtent = byState.get(sb);
  if (!byExtent.has(extent)) byExtent.set(extent, compatible(a, sa, b, sb, extent));
  return byExtent.get(extent);
}

// Sample one component-wise marking at an exact point for the hover inspector.
export function markingValue(tile, state, point, extent) {
  const p = prepare(tile, state, extent), pb = box([point]);
  const inside = !separated(pb, p.box) && p.points.every((v, i) => p.winding * rationalOrientation(v, p.points[(i + 1) % 4], point) >= 0);
  const value = Array(5).fill(inside ? 0 : null);
  for (const bar of p.bars) if (!separated(pb, bar.box) && between(point, bar.from, bar.to)) value[bar.family] = 1;
  return value.every(v => v === null) ? null : value;
}
