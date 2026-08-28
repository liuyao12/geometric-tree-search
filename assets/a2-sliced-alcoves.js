const PERMUTATIONS = [
  [0, 1, 2], [0, 2, 1], [1, 0, 2],
  [1, 2, 0], [2, 0, 1], [2, 1, 0]
];

const permutationParity = permutation => {
  let inversions = 0;
  for (let i = 0; i < 3; i += 1) for (let j = i + 1; j < 3; j += 1) {
    if (permutation[i] > permutation[j]) inversions += 1;
  }
  return inversions % 2 ? -1 : 1;
};

// The proper cubic rotations preserving the unoriented foliation x+y+z=k.
const A2_LAYER_ISOMETRIES = Object.freeze([1, -1].flatMap(sign =>
  PERMUTATIONS
    .filter(permutation => sign * permutationParity(permutation) === 1)
    .map(permutation => ({ sign, permutation }))
));

const unit = axis => [0, 1, 2].map(index => Number(index === axis));
const add = (left, right) => left.map((value, axis) => value + right[axis]);
const pointKey = point => point.join(",");
const orderKey = order => order.join("");
const cellKey = cell => `${cell.base.join(",")}:${orderKey(cell.order)}`;
const compareCells = (left, right) => cellKey(left).localeCompare(cellKey(right));

export function a2SlicedAlcoveVertices(cell) {
  const [first, second] = cell.order;
  return [
    cell.base.slice(),
    add(cell.base, unit(first)),
    add(add(cell.base, unit(first)), unit(second)),
    add(cell.base, [1, 1, 1])
  ];
}

const cellFromVertices = vertices => {
  const base = [0, 1, 2].map(axis => Math.min(...vertices.map(point => point[axis])));
  const ranked = vertices
    .map(point => ({ point, rank: point.reduce((sum, value, axis) => sum + value - base[axis], 0) }))
    .sort((left, right) => left.rank - right.rank);
  if (ranked.map(entry => entry.rank).join(",") !== "0,1,2,3") {
    throw new Error("Transformed tetrahedron left the A2-sliced alcove honeycomb");
  }
  const first = ranked[1].point.findIndex((value, axis) => value - base[axis] === 1);
  const second = ranked[2].point.findIndex((value, axis) =>
    value - ranked[1].point[axis] === 1);
  const third = 3 - first - second;
  if (new Set([first, second, third]).size !== 3) {
    throw new Error("Could not recover the alcove coordinate order");
  }
  return { base, order: [first, second, third] };
};

const transformPoint = (point, isometry) =>
  isometry.permutation.map(index => isometry.sign * point[index]);

const normalizeCells = cells => {
  const minima = [0, 1, 2].map(axis => Math.min(...cells.map(cell => cell.base[axis])));
  return cells.map(cell => ({
    base: cell.base.map((value, axis) => value - minima[axis]),
    order: cell.order.slice()
  })).sort(compareCells);
};

export function canonicalA2SlicedAlcoves(cells) {
  if (!cells?.length) return { key: "", cells: [] };
  let best = null;
  for (const isometry of A2_LAYER_ISOMETRIES) {
    const transformed = normalizeCells(cells.map(cell => cellFromVertices(
      a2SlicedAlcoveVertices(cell).map(point => transformPoint(point, isometry))
    )));
    const key = transformed.map(cellKey).join(";");
    if (!best || key < best.key) best = { key, cells: transformed };
  }
  return best;
}

export function a2SlicedAlcoveNeighbors(cell) {
  const [a, b, c] = cell.order;
  return [
    { base: add(cell.base, unit(a)), order: [b, c, a] },
    { base: add(cell.base, unit(c).map(value => -value)), order: [c, a, b] },
    { base: cell.base.slice(), order: [b, a, c] },
    { base: cell.base.slice(), order: [a, c, b] }
  ];
}

export function describeA2SlicedAlcoves(cells) {
  const canonical = canonicalA2SlicedAlcoves(cells).cells;
  const occupancy = new Map();
  const weights = [1, 3, 3, 1];
  for (const cell of canonical) a2SlicedAlcoveVertices(cell).forEach((point, rank) => {
    occupancy.set(pointKey(point), (occupancy.get(pointKey(point)) ?? 0) + weights[rank]);
  });
  const levels = new Map();
  for (const [key, weight] of occupancy) {
    const point = key.split(",").map(Number);
    const level = point[0] + point[1] + point[2];
    if (!levels.has(level)) levels.set(level, []);
    levels.get(level).push(`${key}:${weight}`);
  }
  const indices = [...levels.keys()].sort((a, b) => a - b);
  const signatures = indices.map(level => levels.get(level).sort().join(";"));
  const weightProfile = indices.map(level => levels.get(level).reduce(
    (sum, entry) => sum + Number(entry.slice(entry.lastIndexOf(":") + 1)), 0
  ));
  return Object.freeze({
    layer_equation: "x+y+z=k",
    layer_count: indices.length,
    layer_span: indices.length ? indices.at(-1) - indices[0] + 1 : 0,
    layer_weight_profile: Object.freeze(weightProfile),
    distinct_lattice_sections: new Set(signatures).size,
    all_integer_layers_used: indices.every((level, index) => level === indices[0] + index),
    polycube: false,
    cell_complex: "affine_A3_Coxeter_alcoves",
    transverse_profile_asymmetric: weightProfile.some((weight, index) =>
      weight !== weightProfile[weightProfile.length - 1 - index])
  });
}

export function enumerateA2SlicedAlcoves({ size, requireTransverseProfileAsymmetry = false } = {}) {
  const target = Math.max(1, Math.floor(Number(size) || 1));
  let current = new Map();
  const seed = canonicalA2SlicedAlcoves([{ base: [0, 0, 0], order: [0, 1, 2] }]);
  current.set(seed.key, seed.cells);
  for (let count = 1; count < target; count += 1) {
    const next = new Map();
    for (const cells of current.values()) {
      const occupied = new Set(cells.map(cellKey));
      for (const cell of cells) for (const neighbor of a2SlicedAlcoveNeighbors(cell)) {
        if (occupied.has(cellKey(neighbor))) continue;
        const canonical = canonicalA2SlicedAlcoves([...cells, neighbor]);
        if (!next.has(canonical.key)) next.set(canonical.key, canonical.cells);
      }
    }
    current = next;
  }
  return [...current.entries()].map(([key, cells]) => ({
    key, cells, morphology: describeA2SlicedAlcoves(cells)
  })).filter(candidate => !requireTransverseProfileAsymmetry
    || candidate.morphology.transverse_profile_asymmetric)
    .sort((left, right) => left.key.localeCompare(right.key));
}

export function makeA2SlicedAlcoveUnion(cells) {
  const canonical = canonicalA2SlicedAlcoves(cells);
  if (!canonical.cells.length) throw new Error("A2-sliced tile needs at least one alcove");
  const vertices = [];
  const vertexIndices = new Map();
  const faces = new Map();
  const occupancy = new Map();
  const weights = [1, 3, 3, 1];
  const indexOf = point => {
    const key = pointKey(point);
    if (!vertexIndices.has(key)) {
      vertexIndices.set(key, vertices.length);
      vertices.push(point.slice());
    }
    return vertexIndices.get(key);
  };
  for (const cell of canonical.cells) {
    const points = a2SlicedAlcoveVertices(cell);
    points.forEach((point, rank) => {
      const key = pointKey(point);
      occupancy.set(key, { point: point.slice(), weight: (occupancy.get(key)?.weight ?? 0) + weights[rank] });
    });
    for (let omitted = 0; omitted < 4; omitted += 1) {
      const face = points.filter((_, index) => index !== omitted);
      const key = face.map(pointKey).sort().join("|");
      if (faces.has(key)) faces.delete(key);
      else faces.set(key, face);
    }
  }
  if ([...occupancy.values()].some(entry => entry.weight > 48)) {
    throw new Error("A2-sliced occupancy exceeds one full solid angle");
  }
  const faceData = [...faces.values()].map(face => ({ v: face.map(indexOf), type: "A2_SLICE" }));
  for (const entry of occupancy.values()) indexOf(entry.point);
  return {
    v: vertices,
    f_data: faceData,
    occ: [...occupancy.values()].map(entry => [entry.point, entry.weight, null, null,
      entry.weight === 48 ? "interior" : "vertex"]),
    skip_winding: true,
    solid_angle: { kind: "rational", max_value: 48 },
    geometry_model: "lattice_function",
    lattice_symmetry: "a2_layers",
    layer_normal: [1, 1, 1],
    layer_sums: [...new Set([...occupancy.values()].map(entry =>
      entry.point[0] + entry.point[1] + entry.point[2]))].sort((a, b) => a - b),
    source_alcoves: canonical.cells.map(cell => ({ base: cell.base.slice(), order: cell.order.slice() }))
  };
}
