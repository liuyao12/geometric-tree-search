import { makeA2LayeredPrism } from "./a2-layered-prisms.js";

const PERMUTATIONS = [
  [0, 1, 2], [0, 2, 1], [1, 0, 2],
  [1, 2, 0], [2, 0, 1], [2, 1, 0]
];
const A2_LAYER_ISOMETRIES = Object.freeze([1, -1].flatMap(sign =>
  PERMUTATIONS.map(permutation => ({ sign, permutation }))
));

const cellKey = cell => `${cell.q},${cell.r},${cell.k},${cell.kind}`;
const compareCells = (left, right) =>
  left.k - right.k || left.q - right.q || left.r - right.r || left.kind.localeCompare(right.kind);

export function a2PrismCellVertices(cell) {
  const { q, r, k, kind } = cell;
  const axial = kind === "u"
    ? [[q, r], [q + 1, r], [q, r + 1]]
    : [[q + 1, r + 1], [q, r + 1], [q + 1, r]];
  const base = axial.map(([x, y]) => [x + k, y + k, -x - y + k]);
  return [...base, ...base.map(point => point.map(value => value + 1))];
}

const cellFromVertices = vertices => {
  const sums = vertices.map(point => point[0] + point[1] + point[2]);
  const baseSum = Math.min(...sums);
  if (baseSum % 3 !== 0 || Math.max(...sums) - baseSum !== 3) {
    throw new Error("Transformed A2 prism cell left the x+y+z=3k honeycomb");
  }
  const k = baseSum / 3;
  const base = vertices
    .filter((_, index) => sums[index] === baseSum)
    .map(point => [point[0] - k, point[1] - k]);
  const q = Math.min(...base.map(point => point[0]));
  const r = Math.min(...base.map(point => point[1]));
  const hasLowerCorner = base.some(([x, y]) => x === q && y === r);
  return { q, r, k, kind: hasLowerCorner ? "u" : "d" };
};

const transformPoint = (point, isometry) =>
  isometry.permutation.map(index => isometry.sign * point[index]);

const normalizeCells = cells => {
  const minQ = Math.min(...cells.map(cell => cell.q));
  const minR = Math.min(...cells.map(cell => cell.r));
  const minK = Math.min(...cells.map(cell => cell.k));
  return cells.map(cell => ({
    q: cell.q - minQ,
    r: cell.r - minR,
    k: cell.k - minK,
    kind: cell.kind
  })).sort(compareCells);
};

export function canonicalA2LayeredPolyprism(cells, { includeReflections = true } = {}) {
  if (!cells?.length) return { key: "", cells: [] };
  let best = null;
  for (const isometry of A2_LAYER_ISOMETRIES) {
    const determinantSign = isometry.sign * isometry.sign * isometry.sign;
    const inversions = isometry.permutation.reduce((count, value, index, permutation) =>
      count + permutation.slice(index + 1).filter(next => value > next).length, 0);
    const determinant = determinantSign * (inversions % 2 ? -1 : 1);
    if (!includeReflections && determinant !== 1) continue;
    const transformed = normalizeCells(cells.map(cell => cellFromVertices(
      a2PrismCellVertices(cell).map(point => transformPoint(point, isometry))
    )));
    const key = transformed.map(cellKey).join(";");
    if (!best || key < best.key) best = { key, cells: transformed };
  }
  return best;
}

export function a2LayeredCellNeighbors(cell) {
  const { q, r, k, kind } = cell;
  const lateral = kind === "u"
    ? [
        { q, r, k, kind: "d" },
        { q, r: r - 1, k, kind: "d" },
        { q: q - 1, r, k, kind: "d" }
      ]
    : [
        { q, r, k, kind: "u" },
        { q, r: r + 1, k, kind: "u" },
        { q: q + 1, r, k, kind: "u" }
      ];
  return [
    ...lateral,
    { q, r, k: k - 1, kind },
    { q, r, k: k + 1, kind }
  ];
}

export function isProductA2Prism(cells) {
  const layers = new Map();
  for (const cell of normalizeCells(cells)) {
    if (!layers.has(cell.k)) layers.set(cell.k, []);
    layers.get(cell.k).push(`${cell.q},${cell.r},${cell.kind}`);
  }
  const layerIndices = [...layers.keys()].sort((a, b) => a - b);
  if (layerIndices.length < 2) return true;
  if (layerIndices.some((layer, index) => layer !== index)) return false;
  const signatures = layerIndices.map(layer => layers.get(layer).sort().join(";"));
  return signatures.every(signature => signature === signatures[0]);
}

export function enumerateA2LayeredPolyprisms({ size, includeProduct = false } = {}) {
  const target = Math.max(1, Math.floor(Number(size) || 1));
  let current = new Map();
  const seed = canonicalA2LayeredPolyprism([{ q: 0, r: 0, k: 0, kind: "u" }]);
  current.set(seed.key, seed.cells);
  for (let count = 1; count < target; count += 1) {
    const next = new Map();
    for (const cells of current.values()) {
      const occupied = new Set(cells.map(cellKey));
      for (const cell of cells) for (const neighbor of a2LayeredCellNeighbors(cell)) {
        if (occupied.has(cellKey(neighbor))) continue;
        const canonical = canonicalA2LayeredPolyprism([...cells, neighbor]);
        if (!next.has(canonical.key)) next.set(canonical.key, canonical.cells);
      }
    }
    current = next;
  }
  return [...current.entries()]
    .map(([key, cells]) => ({ key, cells, product_prism: isProductA2Prism(cells) }))
    .filter(candidate => includeProduct || !candidate.product_prism)
    .sort((left, right) => left.key.localeCompare(right.key));
}

export function makeA2LayeredPolyprism(cells) {
  const canonical = canonicalA2LayeredPolyprism(cells, { includeReflections: false });
  if (!canonical.cells.length) throw new Error("A2 layered polyprism needs at least one cell");
  const vertices = [];
  const vertexIndex = new Map();
  const faceStacks = new Map();
  const occupancy = new Map();
  const indexOfVertex = point => {
    const key = point.join(",");
    if (!vertexIndex.has(key)) {
      vertexIndex.set(key, vertices.length);
      vertices.push(point.slice());
    }
    return vertexIndex.get(key);
  };
  for (const cell of canonical.cells) {
    const layerShift = [cell.k, cell.k, cell.k];
    const triangle = a2PrismCellVertices(cell).slice(0, 3).map(point =>
      point.map((value, axis) => value - layerShift[axis])
    );
    const baseData = makeA2LayeredPrism(triangle);
    const data = {
      ...baseData,
      v: baseData.v.map(point => point.map((value, axis) => value + layerShift[axis])),
      occ: baseData.occ.map(([point, ...rest]) => [
        point.map((value, axis) => value + layerShift[axis]),
        ...rest
      ])
    };
    for (const [point, weight, symbolic, displaySymbolic, kind] of data.occ) {
      const key = point.join(",");
      const entry = occupancy.get(key) ?? { point: point.slice(), weight: 0, symbolic, displaySymbolic, kind };
      entry.weight += weight;
      if (entry.weight > 48) throw new Error(`A2 layered occupancy exceeds one full solid angle at ${key}`);
      entry.kind = entry.weight === 48 ? "interior" : entry.kind;
      occupancy.set(key, entry);
    }
    for (const face of data.f_data) {
      const points = face.v.map(index => data.v[index]);
      const key = points.map(point => point.join(",")).sort().join("|");
      if (faceStacks.has(key)) {
        faceStacks.delete(key);
      } else {
        faceStacks.set(key, { points, type: face.type });
      }
    }
  }
  const faceData = [...faceStacks.values()].map(face => ({
    v: face.points.map(indexOfVertex),
    type: face.type
  }));
  for (const entry of occupancy.values()) indexOfVertex(entry.point);
  const layerSums = [...new Set(vertices.map(point => point[0] + point[1] + point[2]))].sort((a, b) => a - b);
  return {
    v: vertices,
    f_data: faceData,
    occ: [...occupancy.values()].map(entry => [
      entry.point, entry.weight, entry.symbolic, entry.displaySymbolic, entry.kind
    ]),
    skip_winding: true,
    solid_angle: { kind: "rational", max_value: 48 },
    geometry_model: "lattice_function",
    lattice_symmetry: "a2_layers",
    layer_normal: [1, 1, 1],
    layer_sums: layerSums,
    source_cells: canonical.cells.map(cell => ({ ...cell }))
  };
}

// First survivor of the complete size-five non-product screen.  The bounded
// lanes have not certified either tiling or non-tiling, so this is a benchmark
// lead rather than an aperiodicity claim.
export const A2_LAYERED_POLYPRISM_CANDIDATES = Object.freeze([
  Object.freeze({
    id: "a2lp_5_00003",
    kind: "a2_layered_polyprism_census",
    registry_id: "a2_layered_5_00003",
    name: "A2 Layered 5-cell Candidate 00003",
    lattice_points: 16,
    survivor_priority: 1,
    survivor_count: 1,
    cells: Object.freeze([
      Object.freeze({ q: 0, r: 0, k: 0, kind: "d" }),
      Object.freeze({ q: 0, r: 0, k: 0, kind: "u" }),
      Object.freeze({ q: 0, r: 0, k: 1, kind: "d" }),
      Object.freeze({ q: 0, r: 0, k: 2, kind: "d" }),
      Object.freeze({ q: 0, r: 0, k: 2, kind: "u" })
    ]),
    description: "The sole bounded-unresolved non-product survivor among the 45 size-five A2-layer polyprisms; 44 peers have exact two-tile translational quotients.",
    screening: Object.freeze({
      status: "inconclusive",
      certificate: null,
      census_stage: "a2_layered_size5_2026_08_27",
      source_pool_size: 45,
      translational_long_seconds: 30,
      translational_largest_motif_size_attempted: 3,
      translational_largest_patch_tiles: 37,
      isohedral_long_seconds: 30,
      isohedral_patch_sizes_tried: Object.freeze([26, 34]),
      report: "data/a2-layered-size5-screen.ndjson"
    }),
    shell_screening: Object.freeze({ robust_completed_shell: 0, deepest_completed_shell: 0 })
  })
]);
