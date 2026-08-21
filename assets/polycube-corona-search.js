import { polycubeKey, polycubeOrientations, polycubeSymmetries } from "./polycube-enumerator.js";

const DIRECTIONS = [
  [1, 0, 0], [-1, 0, 0],
  [0, 1, 0], [0, -1, 0],
  [0, 0, 1], [0, 0, -1]
];
const keyOf = cell => cell.join(",");
const cellOf = key => key.split(",").map(Number);

const buildTarget = (rootSet, layers) => {
  const target = new Set();
  let frontier = new Set(rootSet);
  for (let layer = 1; layer <= layers; layer++) {
    const next = new Set();
    for (const key of frontier) {
      const cell = cellOf(key);
      for (const direction of DIRECTIONS) {
        const neighborKey = keyOf(cell.map((value, axis) => value + direction[axis]));
        if (rootSet.has(neighborKey) || target.has(neighborKey)) continue;
        target.add(neighborKey);
        next.add(neighborKey);
      }
    }
    frontier = next;
  }
  return [...target].sort();
};

export function polycubeCoronaBoundaryKey(voxels, placements, layers, options = {}) {
  const rootSet = new Set(voxels.map(keyOf));
  const normalizedLayers = Math.max(1, Math.floor(Number(layers) || 1));
  const coreSet = new Set([...rootSet, ...buildTarget(rootSet, normalizedLayers)]);
  const exterior = new Set();
  for (const placement of placements ?? []) for (const cell of placement.cells ?? []) {
    const key = keyOf(cell);
    if (!coreSet.has(key)) exterior.add(key);
  }
  const exteriorCells = [...exterior].map(cellOf);
  let best = null;
  for (const symmetry of polycubeSymmetries(voxels, options)) {
    const key = exteriorCells.map(cell => [0, 1, 2].map(axis =>
      symmetry.matrix[axis][0] * cell[0]
      + symmetry.matrix[axis][1] * cell[1]
      + symmetry.matrix[axis][2] * cell[2]
      + symmetry.translation[axis]
    ).join(",")).sort().join(";");
    if (best === null || key < best) best = key;
  }
  return best ?? "";
}

/**
 * Decide whether a fixed root copy can be extended to cover every lattice cell
 * at face-distance at most `layers` from it. Exhaustion is a rigorous finite
 * obstruction to an infinite tiling; success is only a surviving finite patch.
 */
export function searchPolycubeCorona(voxels, options = {}) {
  const includeReflections = !!options.includeReflections;
  const layers = Math.max(1, Math.floor(Number(options.layers) || 1));
  const nodeLimit = Number.isFinite(Number(options.nodeLimit))
    ? Math.max(1, Math.floor(Number(options.nodeLimit)))
    : Infinity;
  const timeLimitMs = Number.isFinite(Number(options.timeLimitMs))
    ? Math.max(1, Number(options.timeLimitMs))
    : Infinity;
  const seed = Math.floor(Number(options.seed) || 0);
  const acceptSolution = typeof options.acceptSolution === "function"
    ? options.acceptSolution
    : null;
  const seededHash = value => {
    let hash = (2166136261 ^ seed) >>> 0;
    for (let index = 0; index < value.length; index++) {
      hash ^= value.charCodeAt(index);
      hash = Math.imul(hash, 16777619) >>> 0;
    }
    return hash;
  };
  const startedAt = performance.now();
  const root = voxels.map(cell => cell.slice());
  const rootSet = new Set(root.map(keyOf));
  const orientations = polycubeOrientations(root, { includeReflections });
  const orientationKeys = new Set(orientations.map(orientation => orientation.key));
  const fixedPlacements = (options.fixedPlacements ?? []).map((placement, index) => {
    if (!Array.isArray(placement?.cells) || placement.cells.length !== root.length) {
      throw new Error(`Fixed corona placement ${index} has the wrong cell count`);
    }
    const cells = placement.cells.map(cell => cell.slice());
    if (!orientationKeys.has(polycubeKey(cells))) {
      throw new Error(`Fixed corona placement ${index} is not a congruent tile copy`);
    }
    return {
      key: cells.map(keyOf).sort().join(";"),
      cells,
      cellKeys: cells.map(keyOf),
      orientationIndex: placement.orientation_index ?? placement.orientationIndex ?? null,
      orientationKey: placement.orientation_key ?? placement.orientationKey ?? null,
      translation: placement.translation?.slice() ?? null,
      targetCoverage: []
    };
  });
  const blockedSet = new Set(rootSet);
  for (const [placementIndex, placement] of fixedPlacements.entries()) {
    for (const key of placement.cellKeys) {
      if (blockedSet.has(key)) throw new Error(`Fixed corona placement ${placementIndex} overlaps an earlier tile`);
      blockedSet.add(key);
    }
  }
  const allTargetKeys = buildTarget(rootSet, layers);
  const targetKeys = allTargetKeys.filter(key => !blockedSet.has(key));
  const targetSet = new Set(targetKeys);
  const placementByKey = new Map();

  for (const targetKey of targetKeys) {
    const pivot = cellOf(targetKey);
    for (let orientationIndex = 0; orientationIndex < orientations.length; orientationIndex++) {
      const orientation = orientations[orientationIndex];
      for (const anchor of orientation.voxels) {
        const translation = pivot.map((value, axis) => value - anchor[axis]);
        const cells = orientation.voxels.map(cell =>
          cell.map((value, axis) => value + translation[axis])
        );
        const cellKeys = cells.map(keyOf);
        if (cellKeys.some(key => blockedSet.has(key))) continue;
        const placementKey = cellKeys.slice().sort().join(";");
        if (!placementByKey.has(placementKey)) {
          placementByKey.set(placementKey, {
            key: placementKey,
            cells,
            cellKeys,
            orientationIndex,
            orientationKey: orientation.key,
            translation,
            targetCoverage: cellKeys.filter(key => targetSet.has(key))
          });
        }
      }
    }
  }

  // Generalized dancing links: target cells are primary columns that must be
  // covered exactly once; cells outside the requested corona are secondary
  // columns that may be unused but can never overlap. Root-overlapping rows
  // were already discarded above.
  const allCellKeys = new Set(targetKeys);
  for (const placement of placementByKey.values()) {
    for (const key of placement.cellKeys) allCellKeys.add(key);
  }
  const header = { key: "__primary_header__", primary: false };
  header.left = header.right = header;
  const columns = new Map();
  for (const key of [...allCellKeys].sort()) {
    const column = { key, primary: targetSet.has(key), size: 0 };
    column.up = column.down = column;
    column.left = column.right = column;
    if (column.primary) {
      column.left = header.left;
      column.right = header;
      header.left.right = column;
      header.left = column;
    }
    columns.set(key, column);
  }
  const orderedPlacements = [...placementByKey.values()].sort((left, right) =>
    right.targetCoverage.length - left.targetCoverage.length
    || (left.cellKeys.length - left.targetCoverage.length)
      - (right.cellKeys.length - right.targetCoverage.length)
    || (seed ? seededHash(left.key) - seededHash(right.key) : left.key.localeCompare(right.key))
  );
  for (const placement of orderedPlacements) {
    let first = null;
    for (const key of placement.cellKeys) {
      const column = columns.get(key);
      const node = { column, placement };
      node.up = column.up;
      node.down = column;
      column.up.down = node;
      column.up = node;
      column.size += 1;
      if (!first) {
        first = node;
        node.left = node.right = node;
      } else {
        node.left = first.left;
        node.right = first;
        first.left.right = node;
        first.left = node;
      }
    }
  }
  const chosen = fixedPlacements.slice();
  let nodes = 0;
  let deadEnds = 0;
  let solutionsRejected = 0;
  let stoppedBy = null;

  const overBudget = () => {
    if (nodes >= nodeLimit) { stoppedBy = "node_limit"; return true; }
    if ((nodes === 0 || (nodes & 1023) === 0)
      && performance.now() - startedAt >= timeLimitMs) {
      stoppedBy = "time_limit";
      return true;
    }
    return false;
  };
  const cover = column => {
    if (column.primary) {
      column.right.left = column.left;
      column.left.right = column.right;
    }
    for (let row = column.down; row !== column; row = row.down) {
      for (let node = row.right; node !== row; node = node.right) {
        node.down.up = node.up;
        node.up.down = node.down;
        node.column.size -= 1;
      }
    }
  };
  const uncover = column => {
    for (let row = column.up; row !== column; row = row.up) {
      for (let node = row.left; node !== row; node = node.left) {
        node.column.size += 1;
        node.down.up = node;
        node.up.down = node;
      }
    }
    if (column.primary) {
      column.right.left = column;
      column.left.right = column;
    }
  };

  const search = () => {
    if (header.right === header) {
      const solution = chosen.slice();
      if (!acceptSolution || acceptSolution(solution)) return solution;
      solutionsRejected += 1;
      return null;
    }
    if (overBudget()) return null;
    nodes += 1;
    let pivot = header.right;
    for (let column = pivot.right; column !== header; column = column.right) {
      if (column.size < pivot.size
        || (seed && column.size === pivot.size
          && seededHash(column.key) < seededHash(pivot.key))) pivot = column;
      if (pivot.size <= 1) break;
    }
    if (!pivot.size) { deadEnds += 1; return null; }
    cover(pivot);
    for (let row = pivot.down; row !== pivot; row = row.down) {
      chosen.push(row.placement);
      for (let node = row.right; node !== row; node = node.right) cover(node.column);
      const solution = search();
      if (solution) return solution;
      for (let node = row.left; node !== row; node = node.left) uncover(node.column);
      chosen.pop();
      if (stoppedBy) break;
    }
    uncover(pivot);
    if (!stoppedBy) deadEnds += 1;
    return null;
  };

  const solution = search();
  const exhausted = !solution && !stoppedBy;
  return {
    success: !!solution,
    exhausted,
    certified_non_tiler: exhausted,
    stopped_by: stoppedBy,
    layers,
    target_cells: allTargetKeys.length,
    remaining_target_cells: targetKeys.length,
    fixed_placements: fixedPlacements.length,
    orientations: orientations.length,
    placements_considered: placementByKey.size,
    nodes,
    memo_hits: 0,
    failed_states: deadEnds,
    solutions_rejected: solutionsRejected,
    algorithm: "generalized_dancing_links",
    seed,
    milliseconds: Math.round(performance.now() - startedAt),
    corona: solution?.map(placement => ({
      orientation_index: placement.orientationIndex,
      orientation_key: placement.orientationKey,
      translation: placement.translation,
      cells: placement.cells
    })) ?? null
  };
}

export function searchFirstPolycubeCorona(voxels, options = {}) {
  return searchPolycubeCorona(voxels, { ...options, layers: 1 });
}
