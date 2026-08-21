import { polycubeOrientations } from "./polycube-enumerator.js";

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
  const startedAt = performance.now();
  const root = voxels.map(cell => cell.slice());
  const rootSet = new Set(root.map(keyOf));
  const targetKeys = buildTarget(rootSet, layers);
  const targetSet = new Set(targetKeys);
  const orientations = polycubeOrientations(root, { includeReflections });
  const placementByKey = new Map();
  const candidateKeysByTarget = new Map(targetKeys.map(key => [key, new Set()]));

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
        if (cellKeys.some(key => rootSet.has(key))) continue;
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
        candidateKeysByTarget.get(targetKey).add(placementKey);
      }
    }
  }

  const candidatesByTarget = new Map([...candidateKeysByTarget].map(([key, placementKeys]) => [
    key,
    [...placementKeys].map(placementKey => placementByKey.get(placementKey))
  ]));
  const allCellKeys = new Set(rootSet);
  for (const key of targetKeys) allCellKeys.add(key);
  for (const placement of placementByKey.values()) {
    for (const key of placement.cellKeys) allCellKeys.add(key);
  }
  const cellIndex = new Map([...allCellKeys].sort().map((key, index) => [key, index]));
  const maskOf = keys => {
    let mask = 0n;
    for (const key of keys) mask |= 1n << BigInt(cellIndex.get(key));
    return mask;
  };
  const rootMask = maskOf(rootSet);
  const targetMask = maskOf(targetKeys);
  const exteriorMask = [...allCellKeys].reduce((mask, key) =>
    rootSet.has(key) || targetSet.has(key)
      ? mask
      : mask | (1n << BigInt(cellIndex.get(key))), 0n);
  const targetBit = new Map(targetKeys.map(key => [key, 1n << BigInt(cellIndex.get(key))]));
  for (const placement of placementByKey.values()) {
    placement.cellMask = maskOf(placement.cellKeys);
    placement.coverageMask = placement.cellMask & targetMask;
  }
  const chosen = [];
  const failedStates = new Set();
  let nodes = 0;
  let memoHits = 0;
  let stoppedBy = null;

  const overBudget = () => {
    if (nodes >= nodeLimit) { stoppedBy = "node_limit"; return true; }
    if (performance.now() - startedAt >= timeLimitMs) { stoppedBy = "time_limit"; return true; }
    return false;
  };
  const compatible = (placement, occupiedMask) => !(placement.cellMask & occupiedMask);
  const stateKey = (occupiedMask, remainingMask) =>
    `${remainingMask.toString(36)}|${(occupiedMask & exteriorMask).toString(36)}`;

  const search = (occupiedMask, remainingMask) => {
    if (overBudget()) return null;
    nodes += 1;
    if (!remainingMask) return chosen.slice();
    const memoKey = stateKey(occupiedMask, remainingMask);
    if (failedStates.has(memoKey)) { memoHits += 1; return null; }

    let pivot = null;
    let optionsForPivot = null;
    for (const targetKey of targetKeys) {
      if (!(remainingMask & targetBit.get(targetKey))) continue;
      const candidates = candidatesByTarget.get(targetKey)
        .filter(placement => compatible(placement, occupiedMask));
      if (!candidates.length) {
        failedStates.add(memoKey);
        return null;
      }
      if (!optionsForPivot || candidates.length < optionsForPivot.length) {
        pivot = targetKey;
        optionsForPivot = candidates;
        if (candidates.length === 1) break;
      }
    }
    void pivot;
    optionsForPivot.sort((left, right) => {
      const leftCoverage = (left.targetCoverage
        .filter(key => remainingMask & targetBit.get(key))).length;
      const rightCoverage = (right.targetCoverage
        .filter(key => remainingMask & targetBit.get(key))).length;
      return rightCoverage - leftCoverage || left.key.localeCompare(right.key);
    });

    for (const placement of optionsForPivot) {
      if (overBudget()) return null;
      chosen.push(placement);
      const solution = search(
        occupiedMask | placement.cellMask,
        remainingMask & ~placement.coverageMask
      );
      if (solution) return solution;
      chosen.pop();
    }
    if (!stoppedBy) failedStates.add(memoKey);
    return null;
  };

  const solution = search(rootMask, targetMask);
  const exhausted = !solution && !stoppedBy;
  return {
    success: !!solution,
    exhausted,
    certified_non_tiler: exhausted,
    stopped_by: stoppedBy,
    layers,
    target_cells: targetKeys.length,
    orientations: orientations.length,
    placements_considered: placementByKey.size,
    nodes,
    memo_hits: memoHits,
    failed_states: failedStates.size,
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
