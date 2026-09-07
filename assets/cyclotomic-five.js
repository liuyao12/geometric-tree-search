// Q(zeta_5), in the independent basis 1,zeta,zeta²,zeta³.
// Rational denominators are for decoration ports/centres, not lattice vertices.
const gcd = (a, b) => { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) [a, b] = [b, a % b]; return a; };
const safe = n => { const value = Number(n); if (!Number.isSafeInteger(value)) throw new RangeError("Cyclotomic coefficient overflow"); return value; };
export function canonical(point) {
  if (![4, 5].includes(point.coeff.length) || !point.coeff.every(Number.isSafeInteger) || !Number.isSafeInteger(point.denominator ?? 1) || (point.denominator ?? 1) <= 0) throw new TypeError("Expected exact cyclotomic coefficients and a positive denominator");
  const gauge = BigInt(point.coeff[4] ?? 0);
  const coeff = point.coeff.slice(0, 4).map(n => BigInt(n) - gauge);
  const d = BigInt(point.denominator ?? 1);
  const g = coeff.reduce(gcd, d);
  return { coeff: coeff.map(n => safe(n / g)), denominator: safe(d / g) };
}
export const latticeKey = p => { const q = canonical(p); return `${q.coeff.join(",")}/${q.denominator}`; };
export const asFive = p => { const q = canonical(p); return { coeff: [...q.coeff, 0], denominator: q.denominator }; };
export function cycloAdd(a, b) {
  a = canonical(a); b = canonical(b);
  return canonical({ coeff: a.coeff.map((n, i) => safe(BigInt(n) * BigInt(b.denominator) + BigInt(b.coeff[i]) * BigInt(a.denominator))), denominator: safe(BigInt(a.denominator) * BigInt(b.denominator)) });
}
export function cycloMultiply(a, b) {
  a = canonical(a); b = canonical(b);
  const c = Array(7).fill(0n);
  a.coeff.forEach((x, i) => b.coeff.forEach((y, j) => { c[i + j] += BigInt(x) * BigInt(y); }));
  for (let i = 6; i >= 4; i--) for (let j = 1; j <= 4; j++) c[i - j] -= c[i];
  return canonical({ coeff: c.slice(0, 4).map(safe), denominator: safe(BigInt(a.denominator) * BigInt(b.denominator)) });
}
export function starMap(point) {
  const q = canonical(point), c = Array(5).fill(0);
  q.coeff.forEach((n, i) => { c[(2 * i) % 5] = n; });
  return canonical({ coeff: c, denominator: q.denominator });
}
export function residueLayer(point) {
  const q = canonical(point);
  if (q.denominator !== 1) throw new TypeError("Residue layers require an algebraic integer");
  return Number((q.coeff.reduce((s, n) => s + BigInt(n), 0n) % 5n + 5n) % 5n);
}
// The only approximate operation: render one of the two complex embeddings.
export function embedding(point, internal = false) {
  const q = internal ? starMap(point) : canonical(point);
  return q.coeff.reduce((p, n, i) => {
    const angle = 2 * Math.PI * i / 5 - Math.PI / 2;
    return { x: p.x + n / q.denominator * Math.cos(angle), y: p.y + n / q.denominator * Math.sin(angle) };
  }, { x: 0, y: 0 });
}
export const GOLDEN_PORTS = [
  { name: "1−φ/2", value: { coeff: [2, 0, 1, 1], denominator: 2 } },
  { name: "φ/2", value: { coeff: [0, 0, -1, -1], denominator: 2 } }
];
// φ = -zeta²-zeta³. The two complementary edge parameters sum to one.
export function edgePort(a, b, t) {
  const minusA = { ...canonical(a), coeff: canonical(a).coeff.map(n => -n) };
  return asFive(cycloAdd(a, cycloMultiply(t, cycloAdd(b, minusA))));
}
