// Coordinates remain Cartesian; quantization is only a congruence tolerance.
export const add = (a, b) => a.map((v, i) => v + b[i]);
export const sub = (a, b) => a.map((v, i) => v - b[i]);
export const mul = (a, s) => a.map((v) => v * s);
export const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
export const norm = (a) => Math.hypot(...a);
export const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];
export const distance = (a, b) => norm(sub(a, b));
export const I = [
  [1, 0, 0],
  [0, 1, 0],
  [0, 0, 1],
];
export const transpose = (m) => m[0].map((_, i) => m.map((r) => r[i]));
export const rotate = (r, p) => r.map((row) => dot(row, p));
export const product = (a, b) =>
  a.map((row) => transpose(b).map((col) => dot(row, col)));
export const posePoint = (pose, p) => add(rotate(pose.r, p), pose.t);
export const compose = (a, b) => ({
  r: product(a.r, b.r),
  t: posePoint(a, b.t),
});
export const relative = (a, b) => ({
  r: product(transpose(a.r), b.r),
  t: rotate(transpose(a.r), sub(b.t, a.t)),
});
export const keyPoint = (p, tol = 1e-4) =>
  p.map((v) => Math.round(v / tol)).join(",");
export const keySites = (sites, tol = 1e-4) =>
  sites
    .map((s) => `${s.species}:${keyPoint(s.position, tol)}`)
    .sort()
    .join("|");
export const freeze = (object) => {
  if (object && typeof object === "object" && !Object.isFrozen(object)) {
    Object.values(object).forEach(freeze);
    Object.freeze(object);
  }
  return object;
};

export function validateAtoms(atoms) {
  if (!Array.isArray(atoms) || atoms.length < 3)
    throw Error("At least three atoms are required.");
  const keys = new Set();
  return atoms.map((s) => {
    if (
      typeof s.species !== "string" ||
      !Array.isArray(s.position) ||
      s.position.length !== 3 ||
      !s.position.every(Number.isFinite)
    )
      throw Error(
        "Each atom needs a species and three finite Cartesian coordinates.",
      );
    if (
      (s.occupancy != null && s.occupancy !== 1) ||
      s.occupancyAlternatives?.length > 1 ||
      s.occupationalAlternatives?.length > 1
    )
      throw Error(
        "Resolve occupational disorder in the research console before fitting this exact colored grammar.",
      );
    const k = keyPoint(s.position, 1e-6);
    if (keys.has(k))
      throw Error("Coincident atoms must be resolved before clustering.");
    keys.add(k);
    return { species: s.species, position: [...s.position] };
  });
}

// Full colored point-set canonicalization over intrinsic proper frames.
// Planar supports are allowed; collinear supports have a continuous stabilizer
// and remain residual atoms instead of receiving invented discrete rotations.
export function canonicalSupport(sites, tol = 1e-4) {
  const center = mul(
    sites.reduce((s, a) => add(s, a.position), [0, 0, 0]),
    1 / sites.length,
  );
  const points = sites.map((s) => sub(s.position, center));
  const fingerprints = sites.map(
    (s, i) =>
      s.species +
      "|" +
      sites
        .map(
          (t, j) =>
            `${t.species}:${Math.round(distance(points[i], points[j]) / tol)}`,
        )
        .sort()
        .join(";"),
  );
  const first = fingerprints.filter((_, i) => norm(points[i]) >= tol).sort()[0];
  let best = null;
  for (let i = 0; i < points.length; i++) {
    if (fingerprints[i] !== first || norm(points[i]) < tol) continue;
    const x = mul(points[i], 1 / norm(points[i]));
    for (let j = 0; j < points.length; j++) {
      const off = sub(points[j], mul(x, dot(points[j], x)));
      if (norm(off) < tol) continue;
      const y = mul(off, 1 / norm(off)),
        z = cross(x, y),
        r = transpose([x, y, z]);
      const local = sites.map((s, k) => ({
        species: s.species,
        position: rotate(transpose(r), points[k]),
      }));
      const key = keySites(local, tol);
      if (!best || key < best.key)
        best = { key, sites: local, pose: { r, t: center }, frames: [r] };
      else if (
        key === best.key &&
        !best.frames.some((q) =>
          q.flat().every((v, k) => Math.abs(v - r.flat()[k]) < 1e-7),
        )
      )
        best.frames.push(r);
    }
  }
  return best;
}

export class SpatialSites {
  constructor(tolerance, exclusion) {
    this.tolerance = tolerance;
    this.exclusion = exclusion;
    this.width = Math.max(tolerance, exclusion);
    this.cells = new Map();
    this.records = [];
  }
  cell(p) {
    return p.map((v) => Math.floor(v / this.width));
  }
  nearby(p, radius = this.width) {
    const c = this.cell(p),
      out = [],
      reach = Math.ceil(radius / this.width);
    for (let x = -reach; x <= reach; x++)
      for (let y = -reach; y <= reach; y++)
        for (let z = -reach; z <= reach; z++)
          out.push(
            ...(this.cells.get([c[0] + x, c[1] + y, c[2] + z].join(",")) || []),
          );
    return out;
  }
  inspect(site) {
    for (const record of this.nearby(site.position)) {
      const d = distance(site.position, record.position);
      if (d <= this.tolerance)
        return record.species === site.species
          ? { match: record }
          : { conflict: true };
      if (d < this.exclusion) return { conflict: true };
    }
    return {};
  }
  insert(site) {
    const k = this.cell(site.position).join(",");
    const record = { species: site.species, position: [...site.position] };
    if (!this.cells.has(k)) this.cells.set(k, []);
    this.cells.get(k).push(record);
    this.records.push(record);
    return record;
  }
  truncate(n) {
    while (this.records.length > n) {
      const r = this.records.pop(),
        k = this.cell(r.position).join(","),
        cell = this.cells.get(k);
      cell.splice(cell.indexOf(r), 1);
      if (!cell.length) this.cells.delete(k);
    }
  }
}
