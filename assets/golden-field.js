/** Exact Q(tau), tau^2 = tau + 1, in the positive real embedding.
 * Coefficients accept only bigint or decimal integer strings. No Number
 * coercion, square roots, tolerances, or floating-point geometry are used.
 */
const integer = value => {
  if (typeof value === "bigint") return value;
  if (typeof value === "string" && /^-?\d+$/.test(value)) return BigInt(value);
  throw new TypeError("Exact coefficients must be bigint or decimal integer strings");
};
const abs = n => n < 0n ? -n : n;
const sign = n => n < 0n ? -1 : n > 0n ? 1 : 0;
const gcd = (a, b) => {
  a = abs(a); b = abs(b);
  while (b) [a, b] = [b, a % b];
  return a;
};

export class Golden {
  constructor(a = 0n, b = 0n, d = 1n) {
    a = integer(a); b = integer(b); d = integer(d);
    if (!d) throw new RangeError("Zero denominator");
    if (d < 0n) { a = -a; b = -b; d = -d; }
    const g = gcd(gcd(a, b), d);
    this.a = a / g; this.b = b / g; this.d = d / g;
    Object.freeze(this);
  }
  static from(x) {
    if (x instanceof Golden) return x;
    return new Golden(x);
  }
  static fromJSON(x) {
    if (!Array.isArray(x) || x.length !== 3) throw new TypeError("Expected [a,b,d]");
    return new Golden(...x);
  }
  add(value) {
    const y = Golden.from(value);
    return new Golden(this.a * y.d + y.a * this.d, this.b * y.d + y.b * this.d, this.d * y.d);
  }
  neg() { return new Golden(-this.a, -this.b, this.d); }
  sub(y) { return this.add(Golden.from(y).neg()); }
  mul(value) {
    const y = Golden.from(value), { a, b, d } = this;
    return new Golden(a * y.a + b * y.b, a * y.b + b * y.a + b * y.b, d * y.d);
  }
  conjugate() { return new Golden(this.a + this.b, -this.b, this.d); }
  inv() {
    const { a, b, d } = this;
    const norm = a * a + a * b - b * b;
    if (!norm) throw new RangeError("Division by zero");
    return new Golden(d * (a + b), -d * b, norm);
  }
  div(y) { return this.mul(Golden.from(y).inv()); }
  pow(exponent) {
    let n = integer(exponent), base = this, result = ONE;
    if (n < 0n) { base = base.inv(); n = -n; }
    while (n) {
      if (n & 1n) result = result.mul(base);
      n >>= 1n;
      if (n) base = base.mul(base);
    }
    return result;
  }
  sign() {
    // 2d*x = (2a+b) + b*sqrt(5). Square only opposite-signed terms.
    const u = 2n * this.a + this.b, v = this.b;
    if (!v) return sign(u);
    if (!u || sign(u) === sign(v)) return sign(v);
    return sign(u) * sign(u * u - 5n * v * v);
  }
  compare(y) { return this.sub(y).sign(); }
  equals(value) {
    const y = Golden.from(value);
    return this.a === y.a && this.b === y.b && this.d === y.d;
  }
  abs() { return this.sign() < 0 ? this.neg() : this; }
  floor() {
    // tau lies strictly between 1 and 2. These rational bounds work even
    // for enormous cancelling coefficients, without a numerical estimate.
    const floorDiv = (n, d) => n >= 0n ? n / d : -((-n + d - 1n) / d);
    let lo = floorDiv(this.a + (this.b < 0n ? 2n * this.b : this.b), this.d);
    let hi = floorDiv(this.a + (this.b < 0n ? this.b : 2n * this.b), this.d) + 1n;
    while (hi - lo > 1n) {
      const mid = lo + (hi - lo) / 2n;
      if (this.compare(mid) >= 0) lo = mid; else hi = mid;
    }
    return lo;
  }
  ceil() { return -this.neg().floor(); }
  isInteger() { return this.b === 0n && this.d === 1n; }
  key() { return `${this.a},${this.b},${this.d}`; }
  toJSON() { return [String(this.a), String(this.b), String(this.d)]; }
  toString() { return `(${this.a}+${this.b}*tau)/${this.d}`; }
  valueOf() { throw new TypeError("Implicit numeric conversion of an exact field value is forbidden"); }
}

export const ZERO = new Golden();
export const ONE = new Golden(1n);
export const TAU = new Golden(0n, 1n);

export const vector = (x, y, z) => Object.freeze([x, y, z].map(Golden.from));
const check3 = v => {
  if (!Array.isArray(v) || v.length !== 3 || !v.every(x => x instanceof Golden)) {
    throw new TypeError("Expected a three-dimensional exact vector");
  }
};
export const vadd = (u, v) => { check3(u); check3(v); return vector(...u.map((x, i) => x.add(v[i]))); };
export const vsub = (u, v) => { check3(u); check3(v); return vector(...u.map((x, i) => x.sub(v[i]))); };
export const vscale = (v, s) => { check3(v); return vector(...v.map(x => x.mul(s))); };
export const dot = (u, v) => { check3(u); check3(v); return u.reduce((s, x, i) => s.add(x.mul(v[i])), ZERO); };
export const cross = (u, v) => {
  check3(u); check3(v);
  return vector(u[1].mul(v[2]).sub(u[2].mul(v[1])), u[2].mul(v[0]).sub(u[0].mul(v[2])), u[0].mul(v[1]).sub(u[1].mul(v[0])));
};
export const determinant = (u, v, w) => dot(u, cross(v, w));
export const pointKey = v => { check3(v); return v.map(x => x.key()).join(";"); };

/** Rows of inverse matrix; input matrix is specified by its columns. */
export function inverseColumns(u, v, w) {
  const d = determinant(u, v, w);
  if (!d.sign()) throw new RangeError("Singular matrix");
  return Object.freeze([cross(v, w), cross(w, u), cross(u, v)].map(r => vscale(r, d.inv())));
}

/** Solve dot(normal[i], x) = rhs[i], including exact singularity detection. */
export function intersectPlanes(normals, rhs) {
  if (normals.length !== 3 || rhs.length !== 3) throw new TypeError("Expected three planes");
  const d = determinant(...normals);
  if (!d.sign()) throw new RangeError("Singular plane system");
  return vscale(vadd(vadd(vscale(cross(normals[1], normals[2]), rhs[0]),
    vscale(cross(normals[2], normals[0]), rhs[1])), vscale(cross(normals[0], normals[1]), rhs[2])), d.inv());
}
