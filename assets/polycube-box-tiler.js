import { polycubeOrientations } from "./polycube-enumerator.js";

const factorBoxes = volume => {
  const boxes = [];
  for (let x = 1; x <= Math.cbrt(volume); x++) {
    if (volume % x !== 0) continue;
    for (let y = x; y * y <= volume / x; y++) {
      if (volume % (x * y) !== 0) continue;
      boxes.push([x, y, volume / (x * y)]);
    }
  }
  return boxes.sort((left, right) =>
    (left[2] - left[0]) - (right[2] - right[0])
    || left[2] - right[2]
    || left[1] - right[1]
  );
};

const cellIndex = ([x, y, z], dims) => x + dims[0] * (y + dims[1] * z);

const permutations = [
  [0, 1, 2], [0, 2, 1], [1, 0, 2],
  [1, 2, 0], [2, 0, 1], [2, 1, 0]
];

const boxPointGroup = dims => {
  const maps = [];
  for (const permutation of permutations) {
    if (permutation.some((source, output) => dims[source] !== dims[output])) continue;
    for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
      maps.push({ permutation, signs: [sx, sy, sz] });
    }
  }
  return maps;
};

const isohedralBoxCertificate = (solution, dims) => {
  if (solution.length === 1) return {
    certified: true,
    tile_orbits: 1,
    automorphisms: 1
  };
  const maskToTile = new Map(solution.map((placement, index) => [placement.mask, index]));
  const parent = solution.map((_, index) => index);
  const find = index => parent[index] === index ? index : (parent[index] = find(parent[index]));
  const join = (left, right) => {
    left = find(left);
    right = find(right);
    if (left !== right) parent[right] = left;
  };
  let automorphisms = 0;
  const isLatticeTranslate = (cells, targetCells) => {
    const targetSet = new Set(targetCells.map(cell => cell.join(",")));
    for (const targetAnchor of targetCells) {
      const shift = cells[0].map((value, axis) => value - targetAnchor[axis]);
      if (shift.some((value, axis) => value % dims[axis] !== 0)) continue;
      if (cells.every(cell => targetSet.has(cell.map((value, axis) => value - shift[axis]).join(",")))) {
        return true;
      }
    }
    return false;
  };
  for (const { permutation, signs } of boxPointGroup(dims)) {
    for (let tx = 0; tx < dims[0]; tx++) for (let ty = 0; ty < dims[1]; ty++) {
      for (let tz = 0; tz < dims[2]; tz++) {
        const translation = [tx, ty, tz];
        const image = [];
        let valid = true;
        for (const placement of solution) {
          let mask = 0n;
          const transformedCells = [];
          for (const cell of placement.cells) {
            const transformed = [0, 1, 2].map(axis =>
              signs[axis] * cell[permutation[axis]] + translation[axis]
            );
            transformedCells.push(transformed);
            const quotientCell = transformed.map((value, axis) =>
              ((value % dims[axis]) + dims[axis]) % dims[axis]
            );
            mask |= 1n << BigInt(cellIndex(quotientCell, dims));
          }
          const target = maskToTile.get(mask);
          if (target === undefined || !isLatticeTranslate(transformedCells, solution[target].cells)) {
            valid = false;
            break;
          }
          image.push(target);
        }
        if (!valid || new Set(image).size !== solution.length) continue;
        automorphisms += 1;
        image.forEach((target, source) => join(source, target));
      }
    }
  }
  const tileOrbits = new Set(solution.map((_, index) => find(index))).size;
  return { certified: tileOrbits === 1, tile_orbits: tileOrbits, automorphisms };
};

export function findPolycubeBoxTiling(voxels, options = {}) {
  const includeReflections = !!options.includeReflections;
  const maxCopies = Math.max(1, Math.floor(Number(options.maxCopies) || 4));
  const maxSide = Math.max(1, Math.floor(Number(options.maxSide) || Infinity));
  const nodeLimit = Math.max(1, Math.floor(Number(options.nodeLimit) || 100000));
  const timeLimitMs = Math.max(1, Number(options.timeLimitMs) || 1000);
  const startedAt = performance.now();
  const orientations = polycubeOrientations(voxels, { includeReflections });
  let nodes = 0;
  let stoppedBy = null;

  const overBudget = () => {
    if (nodes >= nodeLimit) { stoppedBy = "node_limit"; return true; }
    if (performance.now() - startedAt >= timeLimitMs) { stoppedBy = "time_limit"; return true; }
    return false;
  };

  for (let copies = 1; copies <= maxCopies; copies++) {
    const volume = voxels.length * copies;
    for (const dims of factorBoxes(volume)) {
      if (dims[2] > maxSide || overBudget()) continue;
      const allMask = (1n << BigInt(volume)) - 1n;
      const placementsByMask = new Map();
      for (let orientationIndex = 0; orientationIndex < orientations.length; orientationIndex++) {
        const orientation = orientations[orientationIndex];
        const bounds = [0, 1, 2].map(axis =>
          Math.max(...orientation.voxels.map(cell => cell[axis])) + 1
        );
        if (bounds.some((bound, axis) => bound > dims[axis])) continue;
        for (let tx = 0; tx <= dims[0] - bounds[0]; tx++) {
          for (let ty = 0; ty <= dims[1] - bounds[1]; ty++) {
            for (let tz = 0; tz <= dims[2] - bounds[2]; tz++) {
              const translation = [tx, ty, tz];
              const cells = orientation.voxels.map(cell =>
                cell.map((value, axis) => value + translation[axis])
              );
              let mask = 0n;
              for (const cell of cells) mask |= 1n << BigInt(cellIndex(cell, dims));
              if (!placementsByMask.has(mask)) placementsByMask.set(mask, {
                mask,
                cells,
                orientation_index: orientationIndex,
                orientation_key: orientation.key,
                translation
              });
            }
          }
        }
      }
      const placements = [...placementsByMask.values()];
      const byCell = Array.from({ length: volume }, () => []);
      for (const placement of placements) {
        for (let index = 0; index < volume; index++) {
          if (placement.mask & (1n << BigInt(index))) byCell[index].push(placement);
        }
      }
      const failed = new Set();
      const chosen = [];
      const search = remaining => {
        if (remaining === 0n) return chosen.slice();
        if (overBudget()) return null;
        nodes += 1;
        if (failed.has(remaining)) return null;
        let pivotOptions = null;
        for (let index = 0; index < volume; index++) {
          const bit = 1n << BigInt(index);
          if (!(remaining & bit)) continue;
          const optionsForCell = byCell[index].filter(placement =>
            (placement.mask & remaining) === placement.mask
          );
          if (!optionsForCell.length) { failed.add(remaining); return null; }
          if (!pivotOptions || optionsForCell.length < pivotOptions.length) pivotOptions = optionsForCell;
        }
        for (const placement of pivotOptions ?? []) {
          chosen.push(placement);
          const solution = search(remaining ^ placement.mask);
          if (solution) return solution;
          chosen.pop();
        }
        if (!stoppedBy) failed.add(remaining);
        return null;
      };
      const solution = search(allMask);
      if (solution) return {
        kind: "box_tiling_certificate",
        certified: true,
        can_tile: true,
        copies,
        box: dims,
        period_vectors: [[dims[0], 0, 0], [0, dims[1], 0], [0, 0, dims[2]]],
        placements: solution.map(({ mask: _mask, ...placement }) => placement),
        isohedral: isohedralBoxCertificate(solution, dims),
        nodes,
        milliseconds: Math.round(performance.now() - startedAt)
      };
      if (stoppedBy) break;
    }
    if (stoppedBy) break;
  }
  return {
    kind: "box_tiling_search",
    certified: false,
    can_tile: null,
    stopped_by: stoppedBy,
    nodes,
    milliseconds: Math.round(performance.now() - startedAt)
  };
}
