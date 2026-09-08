import {canonical} from './cyclotomic-five.js?v=20260908-speed';
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
