export const add = (a, b) => a.map((v, i) => v + b[i]);
export const sub = (a, b) => a.map((v, i) => v - b[i]);
export const scale = (a, s) => a.map((v) => v * s);
export const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
export const norm = (a) => Math.hypot(...a);
export const distance = (a, b) => norm(sub(a, b));
export const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];
export const I = [
  [1, 0, 0],
  [0, 1, 0],
  [0, 0, 1],
];
export const transpose = (r) => r[0].map((_, i) => r.map((row) => row[i]));
export const rotate = (r, p) => r.map((row) => dot(row, p));
export const product = (a, b) =>
  a.map((row) => transpose(b).map((col) => dot(row, col)));
export const transform = (pose, p) => add(rotate(pose.r, p), pose.t);
export const compose = (a, b) => ({
  r: product(a.r, b.r),
  t: transform(a, b.t),
});
export const inverse = (a) => {
  const r = transpose(a.r);
  return { r, t: scale(rotate(r, a.t), -1) };
};
export const axisAngle = (axis, theta) => {
  const u = scale(axis, 1 / norm(axis)),
    c = Math.cos(theta),
    s = Math.sin(theta);
  return I.map((row, i) =>
    row.map(
      (_, j) =>
        (i === j ? c : 0) +
        (1 - c) * u[i] * u[j] +
        s *
          [
            [0, -u[2], u[1]],
            [u[2], 0, -u[0]],
            [-u[1], u[0], 0],
          ][i][j],
    ),
  );
};
function frame(a, b) {
  const x = scale(a, 1 / norm(a)),
    off = sub(b, scale(x, dot(b, x)));
  if (norm(off) < 1e-8) return null;
  const y = scale(off, 1 / norm(off));
  return transpose([x, y, cross(x, y)]);
}

// Proper rigid least-squares fit (Horn quaternion eigensystem, Jacobi). No
// axis-aligned grid or discrete angular bin is used.
export function fitRigid(source, target) {
  const center = (a) =>
    scale(
      a.reduce((s, p) => add(s, p), [0, 0, 0]),
      1 / a.length,
    );
  const a = center(source),
    b = center(target),
    s = I.map((row) => row.map(() => 0));
  source.forEach((p, i) => {
    const x = sub(p, a),
      y = sub(target[i], b);
    for (let k = 0; k < 3; k++)
      for (let j = 0; j < 3; j++) s[k][j] += x[k] * y[j];
  });
  const [[xx, xy, xz], [yx, yy, yz], [zx, zy, zz]] = s;
  const m = [
    [xx + yy + zz, yz - zy, zx - xz, xy - yx],
    [yz - zy, xx - yy - zz, xy + yx, zx + xz],
    [zx - xz, xy + yx, -xx + yy - zz, yz + zy],
    [xy - yx, zx + xz, yz + zy, -xx - yy + zz],
  ];
  const v = Array.from({ length: 4 }, (_, i) =>
    Array.from({ length: 4 }, (_, j) => +(i === j)),
  );
  for (let iteration = 0; iteration < 60; iteration++) {
    let p = 0,
      q = 1;
    for (let i = 0; i < 4; i++)
      for (let j = i + 1; j < 4; j++)
        if (Math.abs(m[i][j]) > Math.abs(m[p][q])) {
          p = i;
          q = j;
        }
    if (Math.abs(m[p][q]) < 1e-12) break;
    const angle = 0.5 * Math.atan2(2 * m[p][q], m[q][q] - m[p][p]),
      c = Math.cos(angle),
      s = Math.sin(angle);
    const pp = m[p][p],
      qq = m[q][q],
      pq = m[p][q];
    for (let k = 0; k < 4; k++)
      if (k !== p && k !== q) {
        const x = m[k][p],
          y = m[k][q];
        m[k][p] = m[p][k] = c * x - s * y;
        m[k][q] = m[q][k] = s * x + c * y;
      }
    m[p][p] = c * c * pp - 2 * s * c * pq + s * s * qq;
    m[q][q] = s * s * pp + 2 * s * c * pq + c * c * qq;
    m[p][q] = m[q][p] = 0;
    for (let k = 0; k < 4; k++) {
      const x = v[k][p],
        y = v[k][q];
      v[k][p] = c * x - s * y;
      v[k][q] = s * x + c * y;
    }
  }
  const best = [0, 1, 2, 3].sort((i, j) => m[j][j] - m[i][i])[0],
    [w, x, y, z] = v.map((row) => row[best]);
  const r = [
    [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
    [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
    [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
  ];
  return { r, t: sub(b, rotate(r, a)) };
}
export function register(source, target, epsilon, { subset = false } = {}) {
  if (
    (subset
      ? source.length > target.length
      : source.length !== target.length) ||
    source[0].species !== target[0].species
  )
    return null;
  const origin = source[0].position,
    a = source.findIndex((s, i) => i && distance(s.position, origin) > epsilon);
  if (a < 0) return null;
  const b = source.findIndex(
    (s, i) =>
      i !== a &&
      norm(cross(sub(source[a].position, origin), sub(s.position, origin))) >
        epsilon,
  );
  if (b < 0) return null;
  const basis = frame(
    sub(source[a].position, origin),
    sub(source[b].position, origin),
  );
  let best = null;
  for (let j = 1; j < target.length; j++) {
    if (
      target[j].species !== source[a].species ||
      Math.abs(
        distance(target[0].position, target[j].position) -
          distance(origin, source[a].position),
      ) >
        epsilon * 2
    )
      continue;
    for (let k = 1; k < target.length; k++) {
      if (j === k || target[k].species !== source[b].species) continue;
      const tb = frame(
        sub(target[j].position, target[0].position),
        sub(target[k].position, target[0].position),
      );
      if (!tb) continue;
      const r = product(tb, transpose(basis)),
        pose = { r, t: sub(target[0].position, rotate(r, origin)) };
      const used = new Set(),
        mapping = [];
      let valid = true;
      for (const [si, s] of source.entries()) {
        const p = transform(pose, s.position);
        let index = -1,
          d = Infinity;
        target.forEach((t, i) => {
          if (
            (si === 0 ? i === 0 : i !== 0) &&
            !used.has(i) &&
            s.species === t.species &&
            distance(p, t.position) < d
          ) {
            index = i;
            d = distance(p, t.position);
          }
        });
        if (d > epsilon * 4) {
          valid = false;
          break;
        }
        used.add(index);
        mapping.push(index);
      }
      if (!valid) continue;
      const fitted = fitRigid(
        source.map((s) => s.position),
        mapping.map((i) => target[i].position),
      );
      const residuals = source.map((s, i) =>
          distance(transform(fitted, s.position), target[mapping[i]].position),
        ),
        max = Math.max(...residuals);
      if (max <= epsilon && (!best || max < best.max))
        best = {
          pose: fitted,
          mapping,
          max,
          rms: Math.hypot(...residuals) / Math.sqrt(residuals.length),
        };
    }
  }
  return best;
}

// The registry is an approximate geometric adapter, not exact arithmetic.
// No transitive snapping: every match must be within epsilon of a fixed anchor.
export class PointRegistry {
  constructor(epsilon) {
    this.epsilon = epsilon;
    this.points = [];
    this.cells = new Map();
  }
  intern(position) {
    const c = position.map((v) => Math.floor(v / this.epsilon)),
      found = [];
    for (let x = -1; x <= 1; x++)
      for (let y = -1; y <= 1; y++)
        for (let z = -1; z <= 1; z++)
          for (const p of this.cells.get(
            [c[0] + x, c[1] + y, c[2] + z].join(),
          ) || [])
            if (distance(position, p.position) <= this.epsilon) found.push(p);
    if (found.length > 1)
      throw Error(
        "Ambiguous point correspondence: reduce positional error or inspect the input",
      );
    if (found.length) return found[0].id;
    const p = { id: "p" + this.points.length, position: [...position] };
    this.points.push(p);
    const key = c.join();
    if (!this.cells.has(key)) this.cells.set(key, []);
    this.cells.get(key).push(p);
    return p.id;
  }
}
