const sub = (a, b) => a.map((value, axis) => value - b[axis]);
const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0]
];
const dot = (a, b) => a.reduce((sum, value, axis) => sum + value * b[axis], 0);
const cross2 = (origin, a, b) =>
  (a[0] - origin[0]) * (b[1] - origin[1])
  - (a[1] - origin[1]) * (b[0] - origin[0]);

const convexHull2dIndices = points => {
  const sorted = points
    .map((point, index) => ({ point, index }))
    .sort((left, right) => left.point[0] - right.point[0] || left.point[1] - right.point[1]);
  if (sorted.length <= 2) return sorted.map(item => item.index);
  const half = items => {
    const hull = [];
    for (const item of items) {
      while (hull.length >= 2 && cross2(hull.at(-2).point, hull.at(-1).point, item.point) <= 0) hull.pop();
      hull.push(item);
    }
    return hull;
  };
  const lower = half(sorted);
  const upper = half([...sorted].reverse());
  return [...lower.slice(0, -1), ...upper.slice(0, -1)].map(item => item.index);
};

export function extremeLatticePoints(points) {
  const unique = [...new Map(points.map(point => [point.join(","), point.map(Number)])).values()];
  const extreme = new Set();
  const seenPlanes = new Set();
  for (let i = 0; i < unique.length; i++) for (let j = i + 1; j < unique.length; j++) {
    for (let k = j + 1; k < unique.length; k++) {
      const normal = cross(sub(unique[j], unique[i]), sub(unique[k], unique[i]));
      if (!normal.some(Boolean)) continue;
      const distances = unique.map(point => dot(normal, sub(point, unique[i])));
      if (distances.some(value => value > 0) && distances.some(value => value < 0)) continue;
      const divisor = Math.abs(normal.reduce((g, value) => {
        let a = g, b = Math.abs(value);
        while (b) [a, b] = [b, a % b];
        return a;
      }, 0)) || 1;
      let primitive = normal.map(value => value / divisor);
      const first = primitive.find(value => value !== 0);
      if (first < 0) primitive = primitive.map(value => -value);
      const offset = dot(primitive, unique[i]);
      const planeKey = `${primitive.join(",")}:${offset}`;
      if (seenPlanes.has(planeKey)) continue;
      seenPlanes.add(planeKey);
      const onPlane = unique.map((point, index) => ({ point, index }))
        .filter(item => dot(primitive, item.point) === offset);
      const dropAxis = primitive
        .map((value, axis) => ({ value: Math.abs(value), axis }))
        .sort((left, right) => right.value - left.value)[0].axis;
      const projected = onPlane.map(item => item.point.filter((_, axis) => axis !== dropAxis));
      for (const localIndex of convexHull2dIndices(projected)) extreme.add(onPlane[localIndex].index);
    }
  }
  return [...extreme].sort((a, b) => a - b).map(index => unique[index]);
}

export function parseBlancoSantosLatticePoints(text) {
  const lines = String(text).split(/\r?\n/);
  const records = [];
  for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
    const match = lines[lineIndex].match(/Polytope ID:\s*(\S+)/);
    if (!match) continue;
    const rows = [];
    while (++lineIndex < lines.length && rows.length < 3) {
      const values = lines[lineIndex].trim().split(/\s+/).filter(Boolean).map(Number);
      if (values.length && values.every(Number.isFinite)) rows.push(values);
    }
    if (rows.length !== 3 || new Set(rows.map(row => row.length)).size !== 1) {
      throw new Error(`Malformed lattice-point matrix for ${match[1]}`);
    }
    const latticePoints = Array.from({ length: rows[0].length }, (_, column) => rows.map(row => row[column]));
    records.push({ id: match[1], lattice_points: latticePoints, vertices: extremeLatticePoints(latticePoints) });
  }
  return records;
}

export const BLANCO_SANTOS_CENSUS_URL = size =>
  `https://personales.unican.es/santosf/3polytopes/Size_${size}_latticepoints.txt`;

export const BLANCO_SANTOS_CENSUS_URLS = size => {
  const parts = size === 10 ? 5 : size === 11 ? 16 : 0;
  return parts
    ? Array.from({ length: parts }, (_, index) => `https://personales.unican.es/santosf/3polytopes/Size_${size}_latticepoints_${index + 1}.txt`)
    : [BLANCO_SANTOS_CENSUS_URL(size)];
};

export const POLYDB_FEW_LATTICE_POINTS_COUNTS = Object.freeze({
  12: 503443,
  13: 1502640,
  14: 4227528,
  15: 11294824
});

export const POLYDB_FEW_LATTICE_POINTS_ID_WIDTH = Object.freeze({
  12: 6,
  13: 7,
  14: 7,
  15: 8
});

export const POLYDB_AGGREGATE_URL = "https://polydb.org/rest/query.php";
export const POLYDB_FEW_LATTICE_POINTS_COLLECTION = "Polytopes.Lattice.FewLatticePoints3D";

const rationalNumber = value => {
  if (typeof value === "number") return value;
  const [numerator, denominator = "1"] = String(value).split("/");
  return Number(numerator) / Number(denominator);
};

export function parsePolyDbLatticePolytopes(documents) {
  if (!Array.isArray(documents)) throw new Error("polyDB response must be an array");
  return documents.map(document => {
    if (!document?._id || !Array.isArray(document.VERTICES)) {
      throw new Error("Malformed polyDB lattice-polytope document");
    }
    const vertices = document.VERTICES.map(row => {
      if (!Array.isArray(row) || row.length !== 4 || rationalNumber(row[0]) !== 1) {
        throw new Error(`Expected homogeneous lattice vertices for ${document._id}`);
      }
      const point = row.slice(1).map(rationalNumber);
      if (!point.every(Number.isInteger)) throw new Error(`Non-integral vertex in ${document._id}`);
      return point;
    });
    return {
      id: document._id,
      lattice_points: Number(document.N_LATTICE_POINTS),
      vertices
    };
  });
}

export function polyDbLatticePolytopeAggregateRequest(size, start, end) {
  const total = POLYDB_FEW_LATTICE_POINTS_COUNTS[size];
  const width = POLYDB_FEW_LATTICE_POINTS_ID_WIDTH[size];
  if (!total || !width) throw new Error(`polyDB size ${size} is not configured`);
  const boundedStart = Math.max(0, Math.min(total, Math.floor(start)));
  const boundedEnd = Math.max(boundedStart, Math.min(total, Math.floor(end)));
  const id = index => `${size}_${String(index).padStart(width, "0")}`;
  const query = [
    { $match: { _id: { $gte: id(boundedStart), $lt: id(boundedEnd) }, N_LATTICE_POINTS: size } },
    { $sort: { _id: 1 } },
    { $project: { _id: 1, VERTICES: 1, N_LATTICE_POINTS: 1 } }
  ];
  const url = new URL(POLYDB_AGGREGATE_URL);
  url.searchParams.set("task", "aggregate");
  url.searchParams.set("collection", POLYDB_FEW_LATTICE_POINTS_COLLECTION);
  url.searchParams.set("query", JSON.stringify(query));
  url.searchParams.set("allowDiskUse", "1");
  return { url: url.toString(), start: boundedStart, end: boundedEnd };
}
