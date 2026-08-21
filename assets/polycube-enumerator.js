const DIRECTIONS_3D = Object.freeze([
  [1, 0, 0], [-1, 0, 0],
  [0, 1, 0], [0, -1, 0],
  [0, 0, 1], [0, 0, -1]
]);

const permutations = values => {
  if (values.length <= 1) return [values.slice()];
  const out = [];
  for (let index = 0; index < values.length; index++) {
    const rest = values.slice(0, index).concat(values.slice(index + 1));
    for (const suffix of permutations(rest)) out.push([values[index], ...suffix]);
  }
  return out;
};

const determinant3 = matrix =>
  matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
  - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
  + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);

const signedPermutationMatrices = (() => {
  const out = [];
  for (const permutation of permutations([0, 1, 2])) {
    for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
      const signs = [sx, sy, sz];
      const matrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
      for (let row = 0; row < 3; row++) matrix[row][permutation[row]] = signs[row];
      out.push({ matrix, determinant: determinant3(matrix) });
    }
  }
  return out;
})();

const properCubeRotations = signedPermutationMatrices.filter(item => item.determinant === 1);

const transformVoxel = (voxel, matrix) => [
  matrix[0][0] * voxel[0] + matrix[0][1] * voxel[1] + matrix[0][2] * voxel[2],
  matrix[1][0] * voxel[0] + matrix[1][1] * voxel[1] + matrix[1][2] * voxel[2],
  matrix[2][0] * voxel[0] + matrix[2][1] * voxel[1] + matrix[2][2] * voxel[2]
];

const normalizeVoxels = voxels => {
  const mins = [0, 1, 2].map(axis => Math.min(...voxels.map(voxel => voxel[axis])));
  return voxels
    .map(voxel => voxel.map((value, axis) => value - mins[axis]))
    .sort((left, right) => left[0] - right[0] || left[1] - right[1] || left[2] - right[2]);
};

export const polycubeKey = voxels => normalizeVoxels(voxels)
  .map(voxel => voxel.join(","))
  .join(";");

export const voxelsFromPolycubeKey = key => String(key)
  .split(";")
  .filter(Boolean)
  .map(voxel => voxel.split(",").map(Number));

export function canonicalPolycubeKey(voxels, { includeReflections = false } = {}) {
  if (!Array.isArray(voxels) || !voxels.length) throw new Error("A polycube needs at least one voxel");
  const transforms = includeReflections ? signedPermutationMatrices : properCubeRotations;
  let best = null;
  for (const { matrix } of transforms) {
    const key = polycubeKey(voxels.map(voxel => transformVoxel(voxel, matrix)));
    if (best === null || key < best) best = key;
  }
  return best;
}

export function polycubeOrientations(voxels, { includeReflections = false } = {}) {
  const transforms = includeReflections ? signedPermutationMatrices : properCubeRotations;
  const orientations = new Map();
  for (const { matrix, determinant } of transforms) {
    const transformed = normalizeVoxels(voxels.map(voxel => transformVoxel(voxel, matrix)));
    const key = polycubeKey(transformed);
    if (!orientations.has(key)) orientations.set(key, { key, voxels: transformed, determinant });
  }
  return [...orientations.values()].sort((left, right) => left.key.localeCompare(right.key));
}

export function polycubeSymmetries(voxels, { includeReflections = false } = {}) {
  const transforms = includeReflections ? signedPermutationMatrices : properCubeRotations;
  const targetSet = new Set(voxels.map(voxel => voxel.join(",")));
  const symmetries = [];
  const seen = new Set();
  for (const { matrix, determinant } of transforms) {
    const transformed = voxels.map(voxel => transformVoxel(voxel, matrix));
    for (const targetAnchor of voxels) {
      const translation = targetAnchor.map((value, axis) => value - transformed[0][axis]);
      if (!transformed.every(cell => targetSet.has(
        cell.map((value, axis) => value + translation[axis]).join(",")
      ))) continue;
      const key = `${matrix.flat().join(",")}|${translation.join(",")}`;
      if (!seen.has(key)) {
        seen.add(key);
        symmetries.push({
          matrix: matrix.map(row => row.slice()),
          translation,
          determinant
        });
      }
      break;
    }
  }
  return symmetries;
}

export function enumeratePolycubes(size, { includeReflections = false } = {}) {
  const targetSize = Math.floor(Number(size));
  if (!Number.isFinite(targetSize) || targetSize < 1) throw new Error("Polycube size must be a positive integer");
  let generation = new Map([["0,0,0", [[0, 0, 0]]]]);
  for (let volume = 2; volume <= targetSize; volume++) {
    const next = new Map();
    for (const voxels of generation.values()) {
      const occupied = new Set(voxels.map(voxel => voxel.join(",")));
      for (const voxel of voxels) for (const direction of DIRECTIONS_3D) {
        const neighbor = voxel.map((value, axis) => value + direction[axis]);
        if (occupied.has(neighbor.join(","))) continue;
        const candidate = [...voxels, neighbor];
        const key = canonicalPolycubeKey(candidate, { includeReflections });
        if (!next.has(key)) next.set(key, voxelsFromPolycubeKey(key));
      }
    }
    generation = next;
  }
  return [...generation.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, voxels], index) => ({
      id: `p${targetSize}-${String(index + 1).padStart(String(generation.size).length, "0")}`,
      key,
      voxels
    }));
}

export function isChiralPolycube(voxels) {
  const mirror = voxels.map(([x, y, z]) => [-x, y, z]);
  return canonicalPolycubeKey(voxels) !== canonicalPolycubeKey(mirror);
}

export const POLYCUBE_ROTATION_COUNT = properCubeRotations.length;
export const POLYCUBE_ISOMETRY_COUNT = signedPermutationMatrices.length;
