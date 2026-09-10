import { distance, cross, dot, norm, sub, scale } from "./geometry.mjs";
const sum = (a) => a.reduce((n, x) => n + x, 0);
const median = (a) => {
  const b = [...a].sort((a, b) => a - b);
  return b.length ? b[Math.floor(b.length / 2)] : null;
};
const volume = (r, d) =>
  d === 2 ? Math.PI * r * r : (4 * Math.PI * r * r * r) / 3;
const overlap = (r, R, d) =>
  d === 2
    ? 2 * R * R * Math.acos(r / (2 * R)) -
      0.5 * r * Math.sqrt(Math.max(0, 4 * R * R - r * r))
    : (Math.PI * (4 * R + r) * (2 * R - r) ** 2) / 12;
function deposit(a, x, value = 1) {
  const i = Math.floor(x),
    f = x - i;
  for (const [k, w] of [
    [i, 1 - f],
    [i + 1, f],
  ])
    a[Math.max(0, Math.min(a.length - 1, k))] += value * w;
}
function normalized(a) {
  const s = sum(a);
  return s ? a.map((v) => v / s) : null;
}
const mismatch = (a, b) =>
  !a || !b
    ? null
    : sum(a.map((v, i) => Math.abs(v - b[i]))) / (sum(a) + sum(b) || 1);
const tv = (a, b) =>
  !a || !b ? null : sum(a.map((v, i) => Math.abs(v - b[i]))) / 2;
export function geometryDimension(atoms, tolerance = 0.03) {
  if (atoms.length < 3) return { dimension: null, normal: null };
  const p = atoms[0].position,
    v = atoms
      .map((a) => sub(a.position, p))
      .sort((a, b) => norm(b) - norm(a))[0];
  const n = atoms
    .map((a) => cross(v, sub(a.position, p)))
    .sort((a, b) => norm(b) - norm(a))[0];
  if (norm(n) < 1e-9) return { dimension: 1, normal: null };
  const normal = scale(n, 1 / norm(n));
  return {
    dimension: atoms.every(
      (a) => Math.abs(dot(normal, sub(a.position, p))) <= tolerance,
    )
      ? 2
      : 3,
    normal,
  };
}
function profile(
  atoms,
  { radius, rmax, bins, dimension, labels, coordCutoff },
) {
  const rows = atoms.filter((a) => norm(a.position) <= radius + 1e-8),
    N = rows.length,
    V = volume(radius, dimension),
    dr = rmax / bins;
  const counts = Object.fromEntries(
    labels.map((s) => [s, rows.filter((a) => a.species === s).length]),
  );
  const raw = Array(bins).fill(0),
    pairCounts = Array(bins).fill(0),
    partials = {};
  for (let a = 0; a < labels.length; a++)
    for (let b = a; b < labels.length; b++)
      partials[JSON.stringify([labels[a], labels[b]])] = Array(bins).fill(0);
  const neighbors = rows.map(() => []);
  for (let i = 0; i < N; i++)
    for (let j = i + 1; j < N; j++) {
      const d = distance(rows[i].position, rows[j].position);
      neighbors[i].push({ j, d });
      neighbors[j].push({ j: i, d });
      if (d >= rmax) continue;
      const weight = V / overlap(d, radius, dimension),
        x = d / dr - 0.5;
      deposit(raw, x, weight);
      deposit(pairCounts, x);
      deposit(
        partials[JSON.stringify([rows[i].species, rows[j].species].sort())],
        x,
        weight,
      );
    }
  const shells = raw.map(
    (_, i) => volume((i + 1) * dr, dimension) - volume(i * dr, dimension),
  );
  const rdf =
    N >= 2 ? raw.map((v, i) => (2 * V * v) / (N * (N - 1) * shells[i])) : null;
  for (const [key, hist] of Object.entries(partials)) {
    const [a, b] = JSON.parse(key),
      den = a === b ? counts[a] * (counts[a] - 1) : counts[a] * counts[b];
    partials[key] = den
      ? hist.map((v, i) => ((a === b ? 2 : 1) * V * v) / (den * shells[i]))
      : null;
  }
  const angleCounts = Array(36).fill(0),
    nearest = [],
    coordination = [];
  for (let i = 0; i < N; i++) {
    neighbors[i].sort((a, b) => a.d - b.d);
    if (neighbors[i].length) nearest.push(neighbors[i][0].d);
    coordination.push(neighbors[i].filter((n) => n.d <= coordCutoff).length);
    const near = neighbors[i].slice(0, 4).filter((n) => n.d > 1e-10);
    for (let a = 0; a < near.length; a++)
      for (let b = a + 1; b < near.length; b++) {
        const u = sub(rows[near[a].j].position, rows[i].position),
          v = sub(rows[near[b].j].position, rows[i].position);
        deposit(
          angleCounts,
          (Math.acos(
            Math.max(-1, Math.min(1, dot(u, v) / (norm(u) * norm(v)))),
          ) /
            Math.PI) *
            36 -
            0.5,
        );
      }
  }
  return {
    atoms: N,
    counts,
    density: N / V,
    rdf,
    partials,
    pairPDF: normalized(pairCounts),
    nearMedian: median(nearest),
    coordinationMean: N ? sum(coordination) / N : null,
    angles: normalized(angleCounts),
    pairSamples: sum(pairCounts),
  };
}
/** Evaluation only. Never imported into the search/learning decision path. */
export function compareStructure(
  reference,
  generated,
  { bins = 64, minimumAtoms = 24, tolerance = 0.03 } = {},
) {
  const base = {
    scope: "finite-window structural comparison, not a correctness certificate",
    normalization:
      "translation-edge-corrected disk/ball g(r); both patches use the same window and bins; no periodic wrapping",
    warnings: [
      "Finite surfaces, incomplete frontiers and anisotropy affect the estimate.",
      "Agreement with the training patch is not held-out validation.",
      "RDF discards angular information; no single score proves structure identity.",
    ],
  };
  if (reference.length > 50000 || generated.length > 50000)
    return { ...base, status: "metric budget reached", rdfError: null };
  if (reference.length < minimumAtoms || generated.length < minimumAtoms)
    return {
      ...base,
      status: `insufficient data: need at least ${minimumAtoms} atoms in each patch`,
      rdfError: null,
    };
  const geom = geometryDimension(reference, tolerance),
    dimension = geom.dimension;
  if (![2, 3].includes(dimension))
    return {
      ...base,
      status: "RDF unavailable for a line-like reference",
      rdfError: null,
    };
  if (geometryDimension(generated, tolerance).dimension !== dimension)
    return {
      ...base,
      status:
        "dimension mismatch: reference and generated affine dimensions differ",
      rdfError: null,
    };
  const radii = (a) => a.map((x) => norm(x.position)).sort((a, b) => a - b),
    rr = radii(reference),
    gr = radii(generated);
  const radius = Math.min(
      rr[Math.floor(rr.length * 0.9)],
      gr[Math.floor(gr.length * 0.9)],
    ),
    rmax = 0.6 * radius;
  if (!(radius > tolerance * 4))
    return { ...base, status: "insufficient spatial extent", rdfError: null };
  const nn = reference.map((a, i) =>
    Math.min(
      ...reference
        .filter((_, j) => i !== j)
        .map((b) => distance(a.position, b.position)),
    ),
  );
  const labels = [
      ...new Set([...reference, ...generated].map((a) => a.species)),
    ].sort(),
    coordCutoff = 1.25 * median(nn);
  if (labels.length > 12)
    return {
      ...base,
      status: "partial-RDF channel budget reached (12 labels)",
      rdfError: null,
    };
  if (
    [reference, generated].some(
      (a) => a.filter((a) => norm(a.position) <= radius + 1e-8).length > 1500,
    )
  )
    return {
      ...base,
      status: "metric budget reached inside common window",
      rdfError: null,
    };
  const options = { radius, rmax, bins, dimension, labels, coordCutoff },
    ref = profile(reference, options),
    grown = profile(generated, options);
  if (ref.atoms < minimumAtoms || grown.atoms < minimumAtoms)
    return {
      ...base,
      status: "insufficient atoms in common radial window",
      rdfError: null,
      reference: ref,
      generated: grown,
    };
  const partialErrors = Object.fromEntries(
    Object.keys(ref.partials).map((key) => [
      key,
      mismatch(ref.partials[key], grown.partials[key]),
    ]),
  );
  return {
    ...base,
    status: "measured",
    dimension,
    radius,
    rmax,
    bins,
    coordCutoff,
    reference: ref,
    generated: grown,
    partialErrors,
    r: ref.rdf.map((_, i) => ((i + 0.5) * rmax) / bins),
    rdfError: mismatch(ref.rdf, grown.rdf),
    pairDistanceTV: tv(ref.pairPDF, grown.pairPDF),
    compositionTV:
      sum(
        labels.map((s) =>
          Math.abs(ref.counts[s] / ref.atoms - grown.counts[s] / grown.atoms),
        ),
      ) / 2,
    angleTV: tv(ref.angles, grown.angles),
  };
}
