import { polycubeKey, polycubeOrientations, polycubeSymmetries } from "./polycube-enumerator.js";

const DIRECTIONS = [
  [1, 0, 0], [-1, 0, 0],
  [0, 1, 0], [0, -1, 0],
  [0, 0, 1], [0, 0, -1]
];
const keyOf = cell => cell.join(",");
const cellOf = key => key.split(",").map(Number);

export function polycubePlacementOrbitKeys(voxels, placement, options = {}) {
  if (!Array.isArray(placement?.cells)) return [];
  const keys = new Set();
  for (const symmetry of polycubeSymmetries(voxels, options)) {
    keys.add(placement.cells.map(cell => [0, 1, 2].map(axis =>
      symmetry.matrix[axis][0] * cell[0]
      + symmetry.matrix[axis][1] * cell[1]
      + symmetry.matrix[axis][2] * cell[2]
      + symmetry.translation[axis]
    ).join(",")).sort().join(";"));
  }
  return [...keys].sort();
}

export function polycubePlacementClauseOrbitKeys(voxels, placementKeys, options = {}) {
  if (!Array.isArray(placementKeys)) return [];
  const placements = placementKeys.map(key => String(key)
    .split(";")
    .filter(Boolean)
    .map(cellOf));
  if (placements.some(cells => cells.length !== voxels.length)) return [];
  const clauses = new Map();
  for (const symmetry of polycubeSymmetries(voxels, options)) {
    const transformed = placements.map(cells => cells.map(cell => [0, 1, 2].map(axis =>
      symmetry.matrix[axis][0] * cell[0]
      + symmetry.matrix[axis][1] * cell[1]
      + symmetry.matrix[axis][2] * cell[2]
      + symmetry.translation[axis]
    ).join(",")).sort().join(";")).sort();
    clauses.set(transformed.join("|"), transformed);
  }
  return [...clauses.values()].sort((left, right) =>
    left.join("|").localeCompare(right.join("|"))
  );
}

export function polycubeCellOrbitKeys(voxels, cellKey, options = {}) {
  const cell = cellOf(String(cellKey));
  if (cell.length !== 3 || cell.some(value => !Number.isInteger(value))) return [];
  const cells = new Set();
  for (const symmetry of polycubeSymmetries(voxels, options)) {
    cells.add([0, 1, 2].map(axis =>
      symmetry.matrix[axis][0] * cell[0]
      + symmetry.matrix[axis][1] * cell[1]
      + symmetry.matrix[axis][2] * cell[2]
      + symmetry.translation[axis]
    ).join(","));
  }
  return [...cells].sort();
}

export function polycubeCellPairOrbitKeys(voxels, pairKeys, options = {}) {
  if (!Array.isArray(pairKeys) || pairKeys.length !== 2) return [];
  const cells = pairKeys.map(key => cellOf(String(key)));
  if (cells.some(cell => cell.length !== 3 || cell.some(value => !Number.isInteger(value)))) return [];
  const pairs = new Set();
  for (const symmetry of polycubeSymmetries(voxels, options)) {
    const transformed = cells.map(cell => [0, 1, 2].map(axis =>
      symmetry.matrix[axis][0] * cell[0]
      + symmetry.matrix[axis][1] * cell[1]
      + symmetry.matrix[axis][2] * cell[2]
      + symmetry.translation[axis]
    ).join(",")).sort();
    pairs.add(transformed.join(";"));
  }
  return [...pairs].sort().map(pair => pair.split(";"));
}

export function polycubeCellTripleOrbitKeys(voxels, tripleKeys, options = {}) {
  if (!Array.isArray(tripleKeys) || tripleKeys.length !== 3) return [];
  const cells = tripleKeys.map(key => cellOf(String(key)));
  if (cells.some(cell => cell.length !== 3 || cell.some(value => !Number.isInteger(value)))) return [];
  const triples = new Set();
  for (const symmetry of polycubeSymmetries(voxels, options)) {
    const transformed = cells.map(cell => [0, 1, 2].map(axis =>
      symmetry.matrix[axis][0] * cell[0]
      + symmetry.matrix[axis][1] * cell[1]
      + symmetry.matrix[axis][2] * cell[2]
      + symmetry.translation[axis]
    ).join(",")).sort();
    triples.add(transformed.join(";"));
  }
  return [...triples].sort().map(triple => triple.split(";"));
}

export function polycubeCellQuadrupleOrbitKeys(voxels, quadrupleKeys, options = {}) {
  if (!Array.isArray(quadrupleKeys) || quadrupleKeys.length !== 4) return [];
  const cells = quadrupleKeys.map(key => cellOf(String(key)));
  if (cells.some(cell => cell.length !== 3 || cell.some(value => !Number.isInteger(value)))) return [];
  const quadruples = new Set();
  for (const symmetry of polycubeSymmetries(voxels, options)) {
    const transformed = cells.map(cell => [0, 1, 2].map(axis =>
      symmetry.matrix[axis][0] * cell[0]
      + symmetry.matrix[axis][1] * cell[1]
      + symmetry.matrix[axis][2] * cell[2]
      + symmetry.translation[axis]
    ).join(",")).sort();
    quadruples.add(transformed.join(";"));
  }
  return [...quadruples].sort().map(quadruple => quadruple.split(";"));
}

export function polycubeRootContactKey(voxels, placement, options = {}) {
  if (!Array.isArray(placement?.cells)) return "";
  const placementSet = new Set(placement.cells.map(keyOf));
  const contacts = [];
  for (const rootCell of voxels) for (const direction of DIRECTIONS) {
    const neighbor = rootCell.map((value, axis) => value + direction[axis]);
    if (placementSet.has(keyOf(neighbor))) contacts.push({ rootCell, direction });
  }
  let best = null;
  for (const symmetry of polycubeSymmetries(voxels, options)) {
    const transformed = contacts.map(({ rootCell, direction }) => {
      const cell = [0, 1, 2].map(axis =>
        symmetry.matrix[axis][0] * rootCell[0]
        + symmetry.matrix[axis][1] * rootCell[1]
        + symmetry.matrix[axis][2] * rootCell[2]
        + symmetry.translation[axis]
      );
      const vector = [0, 1, 2].map(axis =>
        symmetry.matrix[axis][0] * direction[0]
        + symmetry.matrix[axis][1] * direction[1]
        + symmetry.matrix[axis][2] * direction[2]
      );
      return `${keyOf(cell)}:${keyOf(vector)}`;
    }).sort().join(";");
    if (best === null || transformed < best) best = transformed;
  }
  return best ?? "";
}

export function polycubeReciprocalPlacement(voxels, placement, options = {}) {
  if (!Array.isArray(placement?.cells)) return null;
  const orientation = placement.orientation_matrix
    ? {
        matrix: placement.orientation_matrix,
        normalization_translation: placement.orientation_normalization_translation ?? [0, 0, 0]
      }
    : polycubeOrientations(voxels, {
        includeReflections: !!options.includeReflections
      }).find(candidate => candidate.key === (placement.orientation_key ?? placement.orientationKey));
  if (!orientation || !Array.isArray(placement.translation)) return null;
  const totalTranslation = orientation.normalization_translation
    .map((value, axis) => value + placement.translation[axis]);
  const inverse = [0, 1, 2].map(row =>
    [0, 1, 2].map(column => orientation.matrix[column][row])
  );
  const cells = voxels.map(cell => [0, 1, 2].map(axis =>
    inverse[axis][0] * (cell[0] - totalTranslation[0])
    + inverse[axis][1] * (cell[1] - totalTranslation[1])
    + inverse[axis][2] * (cell[2] - totalTranslation[2])
  ));
  return { cells };
}

export function enumeratePolycubeCoronaPlacements(voxels, layers = 1, options = {}) {
  const normalizedLayers = Math.max(1, Math.floor(Number(layers) || 1));
  const rootSet = new Set(voxels.map(keyOf));
  const orientations = polycubeOrientations(voxels, {
    includeReflections: !!options.includeReflections
  });
  const placements = new Map();
  for (const targetKey of buildTarget(rootSet, normalizedLayers)) {
    const pivot = cellOf(targetKey);
    for (const orientation of orientations) for (const anchor of orientation.voxels) {
      const translation = pivot.map((value, axis) => value - anchor[axis]);
      const cells = orientation.voxels.map(cell =>
        cell.map((value, axis) => value + translation[axis])
      );
      const cellKeys = cells.map(keyOf);
      if (cellKeys.some(key => rootSet.has(key))) continue;
      const key = cellKeys.slice().sort().join(";");
      if (!placements.has(key)) placements.set(key, {
        key,
        cells,
        orientation_key: orientation.key,
        orientation_matrix: orientation.matrix.map(row => row.slice()),
        orientation_normalization_translation: orientation.normalization_translation.slice(),
        translation
      });
    }
  }
  return [...placements.values()].sort((left, right) => left.key.localeCompare(right.key));
}

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

export function polycubeCoronaRingCellKeys(voxels, layer) {
  const normalizedLayer = Math.max(1, Math.floor(Number(layer) || 1));
  const rootSet = new Set(voxels.map(keyOf));
  const inner = normalizedLayer > 1
    ? new Set(buildTarget(rootSet, normalizedLayer - 1))
    : new Set();
  return buildTarget(rootSet, normalizedLayer).filter(key => !inner.has(key));
}

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

export function verifyPolycubeCoronaPatch(voxels, placements, layers, options = {}) {
  const fail = reason => ({ verified: false, reason });
  if (!Array.isArray(placements)) return fail("invalid_placements");
  const normalizedLayers = Math.max(1, Math.floor(Number(layers) || 1));
  const rootSet = new Set(voxels.map(keyOf));
  const occupied = new Set(rootSet);
  const orientationKeys = new Set(polycubeOrientations(voxels, {
    includeReflections: !!options.includeReflections
  }).map(orientation => orientation.key));
  const forbidden = new Set(options.forbiddenPlacementKeys ?? []);
  const forbiddenOrientations = new Set(options.forbiddenOrientationKeys ?? []);
  for (const [index, placement] of placements.entries()) {
    if (!Array.isArray(placement?.cells) || placement.cells.length !== voxels.length) {
      return fail(`placement_${index}_wrong_cell_count`);
    }
    const normalizedOrientationKey = polycubeKey(placement.cells);
    if (!orientationKeys.has(normalizedOrientationKey)) {
      return fail(`placement_${index}_not_congruent`);
    }
    if (forbiddenOrientations.has(normalizedOrientationKey)) {
      return fail(`placement_${index}_forbidden_orientation`);
    }
    const placementKey = placement.cells.map(keyOf).sort().join(";");
    if (forbidden.has(placementKey)) return fail(`placement_${index}_forbidden`);
    for (const cell of placement.cells) {
      const key = keyOf(cell);
      if (occupied.has(key)) return fail(`placement_${index}_overlap`);
      occupied.add(key);
    }
  }
  const missing = buildTarget(rootSet, normalizedLayers).filter(key => !occupied.has(key));
  if (missing.length) return fail("target_not_covered");
  return {
    verified: true,
    placements: placements.length,
    occupied_cells: occupied.size,
    target_cells: rootSet.size + buildTarget(rootSet, normalizedLayers).length,
    method: "independent_corona_patch_occupancy"
  };
}

export function polycubeCoronaIncompatibleTargetPairDetails(voxels, placements, outerLayers, options = {}) {
  if (!Array.isArray(placements)) return [];
  const normalizedOuterLayers = Math.max(1, Math.floor(Number(outerLayers) || 1));
  const rootSet = new Set(voxels.map(keyOf));
  const outerTarget = new Set(buildTarget(rootSet, normalizedOuterLayers));
  const nextRing = buildTarget(rootSet, normalizedOuterLayers + 1)
    .filter(key => !outerTarget.has(key));
  const fixedKeys = new Set(placements.map(placement =>
    placement.cells.map(keyOf).sort().join(";")
  ));
  const occupied = new Set(rootSet);
  for (const placement of placements) for (const cell of placement.cells ?? []) {
    occupied.add(keyOf(cell));
  }
  const choices = new Map(nextRing.map(key => [key, []]));
  for (const placement of enumeratePolycubeCoronaPlacements(
    voxels,
    normalizedOuterLayers + 1,
    options
  )) {
    const placementKey = placement.cells.map(keyOf).sort().join(";");
    const fixed = fixedKeys.has(placementKey);
    if (!fixed && placement.cells.some(cell => occupied.has(keyOf(cell)))) continue;
    const cellKeys = new Set(placement.cells.map(keyOf));
    const choice = { key: placementKey, cellKeys };
    for (const cellKey of cellKeys) if (choices.has(cellKey)) choices.get(cellKey).push(choice);
  }
  const incompatible = [];
  for (let leftIndex = 0; leftIndex < nextRing.length; leftIndex += 1) {
    const leftKey = nextRing[leftIndex];
    const leftChoices = choices.get(leftKey);
    for (let rightIndex = leftIndex + 1; rightIndex < nextRing.length; rightIndex += 1) {
      const rightKey = nextRing[rightIndex];
      const rightChoices = choices.get(rightKey);
      let compatible = false;
      pairSearch: for (const left of leftChoices) for (const right of rightChoices) {
        if (left.key === right.key
          || [...left.cellKeys].every(cellKey => !right.cellKeys.has(cellKey))) {
          compatible = true;
          break pairSearch;
        }
      }
      if (!compatible) incompatible.push({
        target_cells: [leftKey, rightKey],
        left_choices: leftChoices.length,
        right_choices: rightChoices.length,
        candidate_pairs_blocked: leftChoices.length * rightChoices.length
      });
    }
  }
  return incompatible;
}

export function polycubeCoronaIncompatibleTargetPairs(voxels, placements, outerLayers, options = {}) {
  return polycubeCoronaIncompatibleTargetPairDetails(voxels, placements, outerLayers, options)
    .map(detail => detail.target_cells);
}

export function polycubeCoronaIncompatibleTargetTripleDetails(voxels, placements, outerLayers, options = {}) {
  if (!Array.isArray(placements)) return [];
  const normalizedOuterLayers = Math.max(1, Math.floor(Number(outerLayers) || 1));
  const maximumCellDistance = Math.max(1, Math.floor(Number(options.maximumCellDistance) || 3));
  const limit = Math.max(1, Math.floor(Number(options.limit) || 1));
  const rootSet = new Set(voxels.map(keyOf));
  const outerTarget = new Set(buildTarget(rootSet, normalizedOuterLayers));
  const nextRing = buildTarget(rootSet, normalizedOuterLayers + 1)
    .filter(key => !outerTarget.has(key));
  const fixedKeys = new Set(placements.map(placement =>
    placement.cells.map(keyOf).sort().join(";")
  ));
  const occupied = new Set(rootSet);
  for (const placement of placements) for (const cell of placement.cells ?? []) {
    occupied.add(keyOf(cell));
  }
  const choices = new Map(nextRing.map(key => [key, []]));
  for (const placement of enumeratePolycubeCoronaPlacements(
    voxels,
    normalizedOuterLayers + 1,
    options
  )) {
    const placementKey = placement.cells.map(keyOf).sort().join(";");
    const fixed = fixedKeys.has(placementKey);
    if (!fixed && placement.cells.some(cell => occupied.has(keyOf(cell)))) continue;
    const cellKeys = new Set(placement.cells.map(keyOf));
    const choice = { key: placementKey, cellKeys };
    for (const cellKey of cellKeys) if (choices.has(cellKey)) choices.get(cellKey).push(choice);
  }
  const distance = (leftKey, rightKey) => {
    const left = cellOf(leftKey);
    const right = cellOf(rightKey);
    return left.reduce((sum, value, axis) => sum + Math.abs(value - right[axis]), 0);
  };
  const compatible = (left, right) => left.key === right.key
    || [...left.cellKeys].every(cellKey => !right.cellKeys.has(cellKey));
  const incompatible = [];
  for (let diameter = 1; diameter <= maximumCellDistance; diameter += 1) {
    for (let leftIndex = 0; leftIndex < nextRing.length; leftIndex += 1) {
      const leftKey = nextRing[leftIndex];
      for (let middleIndex = leftIndex + 1; middleIndex < nextRing.length; middleIndex += 1) {
        const middleKey = nextRing[middleIndex];
        const leftMiddleDistance = distance(leftKey, middleKey);
        if (leftMiddleDistance > diameter) continue;
        for (let rightIndex = middleIndex + 1; rightIndex < nextRing.length; rightIndex += 1) {
          const rightKey = nextRing[rightIndex];
          const tripleDiameter = Math.max(
            leftMiddleDistance,
            distance(leftKey, rightKey),
            distance(middleKey, rightKey)
          );
          if (tripleDiameter !== diameter) continue;
          const cellChoices = [choices.get(leftKey), choices.get(middleKey), choices.get(rightKey)];
          let available = false;
          tripleSearch: for (const left of cellChoices[0]) for (const middle of cellChoices[1]) {
            if (!compatible(left, middle)) continue;
            for (const right of cellChoices[2]) {
              if (compatible(left, right) && compatible(middle, right)) {
                available = true;
                break tripleSearch;
              }
            }
          }
          if (available) continue;
          incompatible.push({
            target_cells: [leftKey, middleKey, rightKey],
            diameter: tripleDiameter,
            choice_counts: cellChoices.map(cellChoice => cellChoice.length),
            candidate_triples_blocked: cellChoices.reduce((product, cellChoice) =>
              product * cellChoice.length, 1)
          });
          if (incompatible.length >= limit) return incompatible;
        }
      }
    }
  }
  return incompatible;
}

export function polycubeCoronaIncompatibleTargetQuadrupleDetails(voxels, placements, outerLayers, options = {}) {
  if (!Array.isArray(placements)) return [];
  const normalizedOuterLayers = Math.max(1, Math.floor(Number(outerLayers) || 1));
  const maximumCellDistance = Math.max(1, Math.floor(Number(options.maximumCellDistance) || 6));
  const limit = Math.max(1, Math.floor(Number(options.limit) || 1));
  const rootSet = new Set(voxels.map(keyOf));
  const outerTarget = new Set(buildTarget(rootSet, normalizedOuterLayers));
  const nextRing = buildTarget(rootSet, normalizedOuterLayers + 1)
    .filter(key => !outerTarget.has(key));
  const fixedKeys = new Set(placements.map(placement =>
    placement.cells.map(keyOf).sort().join(";")
  ));
  const occupied = new Set(rootSet);
  for (const placement of placements) for (const cell of placement.cells ?? []) occupied.add(keyOf(cell));
  const choices = new Map(nextRing.map(key => [key, []]));
  for (const placement of enumeratePolycubeCoronaPlacements(
    voxels,
    normalizedOuterLayers + 1,
    options
  )) {
    const placementKey = placement.cells.map(keyOf).sort().join(";");
    if (!fixedKeys.has(placementKey) && placement.cells.some(cell => occupied.has(keyOf(cell)))) continue;
    const cellKeys = new Set(placement.cells.map(keyOf));
    const choice = { key: placementKey, cellKeys };
    for (const cellKey of cellKeys) if (choices.has(cellKey)) choices.get(cellKey).push(choice);
  }
  const cellByKey = new Map(nextRing.map(key => [key, cellOf(key)]));
  const distance = (leftKey, rightKey) => cellByKey.get(leftKey).reduce((sum, value, axis) =>
    sum + Math.abs(value - cellByKey.get(rightKey)[axis]), 0
  );
  const compatible = (left, right) => left.key === right.key
    || [...left.cellKeys].every(cellKey => !right.cellKeys.has(cellKey));
  const incompatible = [];
  for (let diameter = 1; diameter <= maximumCellDistance; diameter += 1) {
    for (let firstIndex = 0; firstIndex < nextRing.length; firstIndex += 1) {
      const firstKey = nextRing[firstIndex];
      for (let secondIndex = firstIndex + 1; secondIndex < nextRing.length; secondIndex += 1) {
        const secondKey = nextRing[secondIndex];
        const firstSecondDistance = distance(firstKey, secondKey);
        if (firstSecondDistance > diameter) continue;
        for (let thirdIndex = secondIndex + 1; thirdIndex < nextRing.length; thirdIndex += 1) {
          const thirdKey = nextRing[thirdIndex];
          const firstThreeDiameter = Math.max(
            firstSecondDistance,
            distance(firstKey, thirdKey),
            distance(secondKey, thirdKey)
          );
          if (firstThreeDiameter > diameter) continue;
          for (let fourthIndex = thirdIndex + 1; fourthIndex < nextRing.length; fourthIndex += 1) {
            const fourthKey = nextRing[fourthIndex];
            const quadrupleDiameter = Math.max(
              firstThreeDiameter,
              distance(firstKey, fourthKey),
              distance(secondKey, fourthKey),
              distance(thirdKey, fourthKey)
            );
            if (quadrupleDiameter !== diameter) continue;
            const cellChoices = [
              choices.get(firstKey),
              choices.get(secondKey),
              choices.get(thirdKey),
              choices.get(fourthKey)
            ];
            let available = false;
            quadrupleSearch: for (const first of cellChoices[0]) for (const second of cellChoices[1]) {
              if (!compatible(first, second)) continue;
              for (const third of cellChoices[2]) {
                if (!compatible(first, third) || !compatible(second, third)) continue;
                for (const fourth of cellChoices[3]) {
                  if (compatible(first, fourth)
                    && compatible(second, fourth)
                    && compatible(third, fourth)) {
                    available = true;
                    break quadrupleSearch;
                  }
                }
              }
            }
            if (available) continue;
            incompatible.push({
              target_cells: [firstKey, secondKey, thirdKey, fourthKey],
              diameter: quadrupleDiameter,
              choice_counts: cellChoices.map(cellChoice => cellChoice.length),
              candidate_quadruples_blocked: cellChoices.reduce((product, cellChoice) =>
                product * cellChoice.length, 1)
            });
            if (incompatible.length >= limit) return incompatible;
          }
        }
      }
    }
  }
  return incompatible;
}

export function createPolycubeCoronaPairObstructionOracle(voxels, outerLayers, options = {}) {
  const normalizedOuterLayers = Math.max(1, Math.floor(Number(outerLayers) || 1));
  const rootSet = new Set(voxels.map(keyOf));
  const outerTarget = new Set(buildTarget(rootSet, normalizedOuterLayers));
  const nextRing = buildTarget(rootSet, normalizedOuterLayers + 1)
    .filter(key => !outerTarget.has(key));
  const choices = new Map(nextRing.map(key => [key, []]));
  for (const placement of enumeratePolycubeCoronaPlacements(
    voxels,
    normalizedOuterLayers + 1,
    options
  )) {
    const placementKey = placement.cells.map(keyOf).sort().join(";");
    const cellKeys = new Set(placement.cells.map(keyOf));
    const choice = { key: placementKey, cellKeys };
    for (const cellKey of cellKeys) if (choices.has(cellKey)) choices.get(cellKey).push(choice);
  }
  const greedyHittingSet = blockerSets => {
    if (!blockerSets.length) return [];
    if (blockerSets.some(blockers => !blockers.size)) return null;
    const uncovered = new Set(blockerSets.map((_, index) => index));
    const selected = [];
    while (uncovered.size) {
      const frequencies = new Map();
      for (const index of uncovered) for (const blocker of blockerSets[index]) {
        frequencies.set(blocker, (frequencies.get(blocker) ?? 0) + 1);
      }
      let best = null;
      let bestCount = -1;
      for (const [blocker, count] of frequencies) {
        if (count > bestCount || (count === bestCount && blocker < best)) {
          best = blocker;
          bestCount = count;
        }
      }
      if (best === null) return null;
      selected.push(best);
      for (const index of [...uncovered]) {
        if (blockerSets[index].has(best)) uncovered.delete(index);
      }
    }
    for (let index = selected.length - 1; index >= 0; index -= 1) {
      const without = selected.filter((_, candidateIndex) => candidateIndex !== index);
      if (blockerSets.every(blockers => without.some(blocker => blockers.has(blocker)))) {
        selected.splice(index, 1);
      }
    }
    return selected.sort((left, right) => left - right);
  };
  return placements => {
    if (!Array.isArray(placements)) return null;
    const fixedByKey = new Map();
    const occupiedOwner = new Map([...rootSet].map(key => [key, -1]));
    placements.forEach((placement, index) => {
      const placementKey = placement.cells.map(keyOf).sort().join(";");
      fixedByKey.set(placementKey, index);
      for (const cell of placement.cells ?? []) occupiedOwner.set(keyOf(cell), index);
    });
    const blockerCache = new Map();
    const blockersFor = choice => {
      if (blockerCache.has(choice)) return blockerCache.get(choice);
      const blockers = new Set();
      if (!fixedByKey.has(choice.key)) {
        for (const cellKey of choice.cellKeys) {
          const owner = occupiedOwner.get(cellKey);
          if (owner >= 0) blockers.add(owner);
        }
      }
      blockerCache.set(choice, blockers);
      return blockers;
    };
    const choicesAreCompatible = (left, right) => left.key === right.key
      || [...left.cellKeys].every(cellKey => !right.cellKeys.has(cellKey));
    for (let leftIndex = 0; leftIndex < nextRing.length; leftIndex += 1) {
      const leftKey = nextRing[leftIndex];
      for (let rightIndex = leftIndex + 1; rightIndex < nextRing.length; rightIndex += 1) {
        const rightKey = nextRing[rightIndex];
        let available = false;
        for (const left of choices.get(leftKey)) for (const right of choices.get(rightKey)) {
          if (choicesAreCompatible(left, right)
            && !blockersFor(left).size
            && !blockersFor(right).size) {
            available = true;
            break;
          }
        }
        if (available) continue;
        const blockerSets = [];
        for (const left of choices.get(leftKey)) for (const right of choices.get(rightKey)) {
          if (!choicesAreCompatible(left, right)) continue;
          blockerSets.push(new Set([...blockersFor(left), ...blockersFor(right)]));
        }
        const fixedIndices = greedyHittingSet(blockerSets);
        if (fixedIndices === null) continue;
        return {
          kind: "incompatible_target_pair",
          target_cells: [leftKey, rightKey],
          candidate_pairs_blocked: blockerSets.length,
          fixed_placement_indices: fixedIndices,
          fixed_placement_keys: fixedIndices.map(index =>
            placements[index].cells.map(keyOf).sort().join(";")
          )
        };
      }
    }
    return null;
  };
}

export function polycubeCoronaPairObstruction(voxels, placements, outerLayers, options = {}) {
  return createPolycubeCoronaPairObstructionOracle(voxels, outerLayers, options)(placements);
}

export function verifyPolycubeCoronaPairObstruction(
  voxels,
  placements,
  outerLayers,
  obstruction,
  options = {}
) {
  const fail = reason => ({ verified: false, reason });
  if (!Array.isArray(placements) || !Array.isArray(obstruction?.target_cells)) {
    return fail("invalid_obstruction");
  }
  const fixedIndices = obstruction.fixed_placement_indices ?? [];
  if (!fixedIndices.length || fixedIndices.some(index => !Number.isInteger(index) || !placements[index])) {
    return fail("invalid_fixed_indices");
  }
  const normalizedOuterLayers = Math.max(1, Math.floor(Number(outerLayers) || 1));
  const rootSet = new Set(voxels.map(keyOf));
  const outerTarget = new Set(buildTarget(rootSet, normalizedOuterLayers));
  const nextRing = new Set(buildTarget(rootSet, normalizedOuterLayers + 1)
    .filter(key => !outerTarget.has(key)));
  const [leftTarget, rightTarget] = obstruction.target_cells.map(String);
  if (leftTarget === rightTarget || !nextRing.has(leftTarget) || !nextRing.has(rightTarget)) {
    return fail("invalid_target_pair");
  }
  const fixedKeys = new Set();
  const occupiedOwner = new Map();
  for (const index of fixedIndices) {
    const placement = placements[index];
    const placementKey = placement.cells.map(keyOf).sort().join(";");
    fixedKeys.add(placementKey);
    for (const cell of placement.cells ?? []) {
      const cellKey = keyOf(cell);
      if (occupiedOwner.has(cellKey)) return fail("fixed_clause_overlap");
      occupiedOwner.set(cellKey, index);
    }
  }
  if (Array.isArray(obstruction.fixed_placement_keys)) {
    const reportedKeys = [...new Set(obstruction.fixed_placement_keys.map(String))].sort();
    if (reportedKeys.join("|") !== [...fixedKeys].sort().join("|")) {
      return fail("fixed_key_mismatch");
    }
  }
  const choices = new Map([[leftTarget, []], [rightTarget, []]]);
  for (const placement of enumeratePolycubeCoronaPlacements(
    voxels,
    normalizedOuterLayers + 1,
    options
  )) {
    const key = placement.cells.map(keyOf).sort().join(";");
    const cellKeys = new Set(placement.cells.map(keyOf));
    const blockers = new Set();
    if (!fixedKeys.has(key)) {
      for (const cellKey of cellKeys) {
        const owner = occupiedOwner.get(cellKey);
        if (owner !== undefined) blockers.add(owner);
      }
    }
    const choice = { key, cellKeys, blockers };
    for (const target of choices.keys()) if (cellKeys.has(target)) choices.get(target).push(choice);
  }
  let candidatePairs = 0;
  for (const left of choices.get(leftTarget)) for (const right of choices.get(rightTarget)) {
    if (left.key !== right.key
      && [...left.cellKeys].some(cellKey => right.cellKeys.has(cellKey))) continue;
    candidatePairs += 1;
    if (!left.blockers.size && !right.blockers.size) return fail("unblocked_candidate_pair");
  }
  if (!candidatePairs) return fail("no_candidate_pairs");
  if (Number.isFinite(Number(obstruction.candidate_pairs_blocked))
    && candidatePairs !== Number(obstruction.candidate_pairs_blocked)) {
    return fail("candidate_pair_count_mismatch");
  }
  return {
    verified: true,
    method: "independent_pair_clause_enumeration",
    target_cells: [leftTarget, rightTarget],
    fixed_placements: fixedIndices.length,
    candidate_pairs_blocked: candidatePairs
  };
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
  const timeBudgetMode = options.timeBudgetMode === "cpu" && typeof process !== "undefined"
    && typeof process.cpuUsage === "function" ? "cpu" : "wall";
  const seed = Math.floor(Number(options.seed) || 0);
  const acceptSolution = typeof options.acceptSolution === "function"
    ? options.acceptSolution
    : null;
  const nogoodLimit = Number.isFinite(Number(options.nogoodLimit))
    ? Math.max(0, Math.floor(Number(options.nogoodLimit)))
    : 50_000;
  const nogoodsEnabled = options.nogoods === true && nogoodLimit > 0;
  const forbiddenPlacementKeys = new Set(options.forbiddenPlacementKeys ?? []);
  const forbiddenOrientationKeys = new Set(options.forbiddenOrientationKeys ?? []);
  const preferredPlacementKeys = new Set(options.preferredPlacementKeys ?? []);
  const placementOrdering = String(options.placementOrdering ?? "compact");
  if (!["compact", "expansive", "seeded"].includes(placementOrdering)) {
    throw new Error("placementOrdering must be compact, expansive, or seeded");
  }
  const seededHash = value => {
    let hash = (2166136261 ^ seed) >>> 0;
    for (let index = 0; index < value.length; index++) {
      hash ^= value.charCodeAt(index);
      hash = Math.imul(hash, 16777619) >>> 0;
    }
    return hash;
  };
  const startedAt = performance.now();
  const cpuStartedAt = timeBudgetMode === "cpu" ? process.cpuUsage() : null;
  const budgetElapsedMilliseconds = () => {
    if (timeBudgetMode !== "cpu") return performance.now() - startedAt;
    const elapsed = process.cpuUsage(cpuStartedAt);
    return (elapsed.user + elapsed.system) / 1000;
  };
  const root = voxels.map(cell => cell.slice());
  const rootSet = new Set(root.map(keyOf));
  const orientations = polycubeOrientations(root, { includeReflections });
  const orientationKeys = new Set(orientations.map(orientation => orientation.key));
  const fixedPlacements = (options.fixedPlacements ?? []).map((placement, index) => {
    if (!Array.isArray(placement?.cells) || placement.cells.length !== root.length) {
      throw new Error(`Fixed corona placement ${index} has the wrong cell count`);
    }
    const cells = placement.cells.map(cell => cell.slice());
    const normalizedOrientationKey = polycubeKey(cells);
    if (!orientationKeys.has(normalizedOrientationKey)) {
      throw new Error(`Fixed corona placement ${index} is not a congruent tile copy`);
    }
    if (forbiddenOrientationKeys.has(normalizedOrientationKey)) {
      throw new Error(`Fixed corona placement ${index} has an explicitly forbidden orientation`);
    }
    const key = cells.map(keyOf).sort().join(";");
    if (forbiddenPlacementKeys.has(key)) {
      throw new Error(`Fixed corona placement ${index} is explicitly forbidden`);
    }
    return {
      key,
      cells,
      cellKeys: cells.map(keyOf),
      orientationIndex: placement.orientation_index ?? placement.orientationIndex ?? null,
      orientationKey: placement.orientation_key ?? placement.orientationKey ?? null,
      translation: placement.translation?.slice() ?? null,
      targetCoverage: []
    };
  });
  const conflictExplanationsEnabled = (fixedPlacements.length > 0
    && options.explainFixedObstruction !== false)
    || options.conflictBackjumping === true;
  const symmetryNogoodsEnabled = options.symmetryNogoods === true
    && fixedPlacements.length === 0
    && forbiddenPlacementKeys.size === 0
    && forbiddenOrientationKeys.size === 0;
  const nextLayerCoverabilityEnabled = options.nextLayerCoverability === true;
  const nextLayerCoverabilityMinPlacements = Number.isFinite(Number(
    options.nextLayerCoverabilityMinPlacements
  ))
    ? Math.max(0, Math.floor(Number(options.nextLayerCoverabilityMinPlacements)))
    : 0;
  const blockedSet = new Set(rootSet);
  const fixedOwnerByCell = new Map();
  for (const [placementIndex, placement] of fixedPlacements.entries()) {
    for (const key of placement.cellKeys) {
      if (blockedSet.has(key)) throw new Error(`Fixed corona placement ${placementIndex} overlaps an earlier tile`);
      blockedSet.add(key);
      fixedOwnerByCell.set(key, placementIndex);
    }
  }
  const allTargetKeys = buildTarget(rootSet, layers);
  const targetKeys = allTargetKeys.filter(key => !blockedSet.has(key));
  const targetSet = new Set(targetKeys);
  const placementByKey = new Map();
  const fixedBlockedRowsByTarget = new Map(targetKeys.map(key => [key, new Map()]));

  for (const targetKey of targetKeys) {
    const pivot = cellOf(targetKey);
    for (let orientationIndex = 0; orientationIndex < orientations.length; orientationIndex++) {
      const orientation = orientations[orientationIndex];
      if (forbiddenOrientationKeys.has(orientation.key)) continue;
      for (const anchor of orientation.voxels) {
        const translation = pivot.map((value, axis) => value - anchor[axis]);
        const cells = orientation.voxels.map(cell =>
          cell.map((value, axis) => value + translation[axis])
        );
        const cellKeys = cells.map(keyOf);
        if (cellKeys.some(key => rootSet.has(key))) continue;
        const placementKey = cellKeys.slice().sort().join(";");
        if (forbiddenPlacementKeys.has(placementKey)) continue;
        const fixedBlockers = new Set(cellKeys
          .map(key => fixedOwnerByCell.get(key))
          .filter(index => index !== undefined));
        if (fixedBlockers.size) {
          if (!fixedBlockedRowsByTarget.get(targetKey).has(placementKey)) {
            fixedBlockedRowsByTarget.get(targetKey).set(placementKey, fixedBlockers);
          }
          continue;
        }
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
  const geometricPlacementOrder = (left, right, expansive = false) => {
    const targetDifference = expansive
      ? left.targetCoverage.length - right.targetCoverage.length
      : right.targetCoverage.length - left.targetCoverage.length;
    if (targetDifference) return targetDifference;
    const leftExterior = left.cellKeys.length - left.targetCoverage.length;
    const rightExterior = right.cellKeys.length - right.targetCoverage.length;
    return expansive ? rightExterior - leftExterior : leftExterior - rightExterior;
  };
  const orderedPlacements = [...placementByKey.values()].sort((left, right) => {
    const preferredDifference = Number(preferredPlacementKeys.has(right.key))
      - Number(preferredPlacementKeys.has(left.key));
    if (preferredDifference) return preferredDifference;
    if (placementOrdering === "seeded") {
      return seededHash(left.key) - seededHash(right.key)
        || geometricPlacementOrder(left, right)
        || left.key.localeCompare(right.key);
    }
    return geometricPlacementOrder(left, right, placementOrdering === "expansive")
      || (seed ? seededHash(left.key) - seededHash(right.key) : left.key.localeCompare(right.key));
  });
  const placementsByTarget = new Map(targetKeys.map(key => [key, []]));
  for (let placementId = 0; placementId < orderedPlacements.length; placementId++) {
    const placement = orderedPlacements[placementId];
    placement.id = placementId;
    for (const key of placement.targetCoverage) placementsByTarget.get(key).push(placement);
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
  const fixedObstructions = (() => {
    if (!fixedPlacements.length) return [];
    const obstructions = [];
    for (const targetKey of targetKeys) {
      if (placementsByTarget.get(targetKey).length) continue;
      const blockerSets = [...fixedBlockedRowsByTarget.get(targetKey).values()];
      const uncovered = new Set(blockerSets.map((_, index) => index));
      const selected = [];
      while (uncovered.size) {
        const frequencies = new Map();
        for (const index of uncovered) for (const fixedIndex of blockerSets[index]) {
          frequencies.set(fixedIndex, (frequencies.get(fixedIndex) ?? 0) + 1);
        }
        let bestIndex = null;
        let bestCount = -1;
        for (const [fixedIndex, count] of frequencies) {
          if (count > bestCount || (count === bestCount && fixedIndex < bestIndex)) {
            bestIndex = fixedIndex;
            bestCount = count;
          }
        }
        if (bestIndex === null) break;
        selected.push(bestIndex);
        for (const index of [...uncovered]) {
          if (blockerSets[index].has(bestIndex)) uncovered.delete(index);
        }
      }
      if (uncovered.size) continue;
      for (let index = selected.length - 1; index >= 0; index--) {
        const without = selected.filter((_, candidateIndex) => candidateIndex !== index);
        if (blockerSets.every(blockers => without.some(fixedIndex => blockers.has(fixedIndex)))) {
          selected.splice(index, 1);
        }
      }
      const obstruction = {
        target_cell: cellOf(targetKey),
        fixed_placement_indices: selected.slice().sort((left, right) => left - right),
        candidate_rows_blocked: blockerSets.length
      };
      obstruction.fixed_placement_keys = obstruction.fixed_placement_indices
        .map(index => fixedPlacements[index].key);
      obstructions.push(obstruction);
    }
    obstructions.sort((left, right) =>
      left.fixed_placement_indices.length - right.fixed_placement_indices.length
      || keyOf(left.target_cell).localeCompare(keyOf(right.target_cell)));
    return obstructions;
  })();
  const minimumFixedObstruction = fixedObstructions[0] ?? null;
  const chosen = fixedPlacements.slice();
  let nodes = 0;
  let deadEnds = 0;
  let solutionsRejected = 0;
  let nogoodPrunes = 0;
  let nogoodCells = 0;
  let nogoodMaxSize = 0;
  let maximumDepth = fixedPlacements.length;
  let nogoodSaturated = false;
  const violatedNogoods = new Set();
  const selectedPlacementIds = new Set();
  const selectedOwnerByCell = new Map();
  const nogoods = [];
  const nogoodKeys = new Set();
  const nogoodsByPlacement = new Map();
  let initialNogoodClauses = 0;
  let lastConflict = null;
  let stoppedBy = null;
  let symmetryNogoodClauses = 0;
  let conflictBackjumps = 0;
  const placementIdByKey = new Map(orderedPlacements.map(placement => [placement.key, placement.id]));

  // Exact necessary-condition lookahead.  A partial radius-L patch can only
  // extend to radius L+1 if every cell in the next ring still has at least one
  // congruent placement compatible with the already selected rows.  Maintain
  // those availability counts incrementally so doomed outer branches are cut
  // before a complete corona is proposed.
  const allTargetKeySet = new Set(allTargetKeys);
  const nextLayerTargetKeys = nextLayerCoverabilityEnabled
    ? buildTarget(rootSet, layers + 1).filter(key => !allTargetKeySet.has(key))
    : [];
  const nextLayerTargetSet = new Set(nextLayerTargetKeys);
  const fixedPlacementKeys = new Set(fixedPlacements.map(placement => placement.key));
  const selectedLookaheadKeys = new Set(fixedPlacementKeys);
  const lookaheadChoicesByTarget = new Map(nextLayerTargetKeys.map(key => [key, []]));
  const lookaheadChoicesByCell = new Map();
  const nextLayerAvailableCounts = new Map(nextLayerTargetKeys.map(key => [key, 0]));
  const deadNextLayerTargets = new Set();
  const lookaheadChoices = [];
  if (nextLayerCoverabilityEnabled) {
    for (const placement of enumeratePolycubeCoronaPlacements(root, layers + 1, {
      includeReflections
    })) {
      if (forbiddenPlacementKeys.has(placement.key)
        || forbiddenOrientationKeys.has(placement.orientation_key)) continue;
      const cellKeys = placement.cells.map(keyOf);
      const targetCoverage = cellKeys.filter(key => nextLayerTargetSet.has(key));
      if (!targetCoverage.length) continue;
      const fixedSelected = fixedPlacementKeys.has(placement.key);
      const permanentlyBlocked = !fixedSelected
        && cellKeys.some(key => fixedOwnerByCell.has(key));
      const choice = {
        key: placement.key,
        cellKeys,
        targetCoverage,
        fixedSelected,
        permanentlyBlocked,
        dynamicBlockers: 0
      };
      lookaheadChoices.push(choice);
      for (const key of targetCoverage) lookaheadChoicesByTarget.get(key).push(choice);
      for (const key of cellKeys) {
        if (!lookaheadChoicesByCell.has(key)) lookaheadChoicesByCell.set(key, []);
        lookaheadChoicesByCell.get(key).push(choice);
      }
      if (fixedSelected || !permanentlyBlocked) {
        for (const key of targetCoverage) {
          nextLayerAvailableCounts.set(key, nextLayerAvailableCounts.get(key) + 1);
        }
      }
    }
  }
  const lookaheadChoiceAvailable = choice => choice.fixedSelected
    || selectedLookaheadKeys.has(choice.key)
    || (!choice.permanentlyBlocked && choice.dynamicBlockers === 0);
  const updateLookaheadForPlacementNow = (placement, adding) => {
    if (!placement.lookaheadAffectedChoices) {
      const affected = new Set();
      for (const key of placement.cellKeys) {
        for (const choice of lookaheadChoicesByCell.get(key) ?? []) affected.add(choice);
      }
      placement.lookaheadAffectedChoices = [...affected];
    }
    const priorAvailability = placement.lookaheadAffectedChoices.map(choice =>
      lookaheadChoiceAvailable(choice)
    );
    if (adding) selectedLookaheadKeys.add(placement.key);
    else selectedLookaheadKeys.delete(placement.key);
    for (let choiceIndex = 0; choiceIndex < placement.lookaheadAffectedChoices.length; choiceIndex += 1) {
      const choice = placement.lookaheadAffectedChoices[choiceIndex];
      choice.dynamicBlockers += adding ? 1 : -1;
      if (choice.dynamicBlockers < 0) {
        throw new Error("Next-layer coverability blocker count became negative");
      }
      const wasAvailable = priorAvailability[choiceIndex];
      const isAvailable = lookaheadChoiceAvailable(choice);
      if (wasAvailable === isAvailable) continue;
      const delta = isAvailable ? 1 : -1;
      for (const key of choice.targetCoverage) {
        const previous = nextLayerAvailableCounts.get(key);
        const current = previous + delta;
        nextLayerAvailableCounts.set(key, current);
        if (previous === 0 && current > 0) deadNextLayerTargets.delete(key);
        else if (previous > 0 && current === 0) deadNextLayerTargets.add(key);
      }
    }
  };
  for (const [key, count] of nextLayerAvailableCounts) {
    if (count === 0) deadNextLayerTargets.add(key);
  }
  let nextLayerLookaheadActive = nextLayerCoverabilityEnabled
    && fixedPlacements.length >= nextLayerCoverabilityMinPlacements;
  const activateNextLayerLookahead = () => {
    if (nextLayerLookaheadActive || !nextLayerCoverabilityEnabled) return;
    nextLayerLookaheadActive = true;
    for (const placement of chosen.slice(fixedPlacements.length)) {
      updateLookaheadForPlacementNow(placement, true);
    }
  };
  const deactivateNextLayerLookahead = () => {
    if (!nextLayerLookaheadActive || !nextLayerCoverabilityEnabled) return;
    for (const placement of chosen.slice(fixedPlacements.length).reverse()) {
      updateLookaheadForPlacementNow(placement, false);
    }
    nextLayerLookaheadActive = false;
  };
  let nextLayerPrunes = 0;
  let nextLayerNogoodClauses = 0;

  const fixedToken = index => `f:${index}`;
  const placementToken = id => `p:${id}`;
  const fixedConditionedConflict = ids => new Set([
    ...fixedPlacements.map((_, index) => fixedToken(index)),
    ...ids.map(placementToken)
  ]);
  const greedyHittingSet = blockerSets => {
    const uncovered = new Set(blockerSets.map((_, index) => index));
    const selected = [];
    while (uncovered.size) {
      const frequencies = new Map();
      for (const index of uncovered) for (const token of blockerSets[index]) {
        frequencies.set(token, (frequencies.get(token) ?? 0) + 1);
      }
      let bestToken = null;
      let bestCount = -1;
      for (const [token, count] of frequencies) {
        if (count > bestCount || (count === bestCount && String(token) < String(bestToken))) {
          bestToken = token;
          bestCount = count;
        }
      }
      if (bestToken === null) return null;
      selected.push(bestToken);
      for (const index of [...uncovered]) {
        if (blockerSets[index].has(bestToken)) uncovered.delete(index);
      }
    }
    for (let index = selected.length - 1; index >= 0; index--) {
      const without = selected.filter((_, candidateIndex) => candidateIndex !== index);
      if (blockerSets.every(blockers => without.some(token => blockers.has(token)))) {
        selected.splice(index, 1);
      }
    }
    return selected;
  };

  const explainPivotFailure = (pivot, branchResiduals = new Map()) => {
    if (!conflictExplanationsEnabled) return null;
    const conflict = new Set();
    const blockerSets = [];
    for (const blockers of fixedBlockedRowsByTarget.get(pivot.key)?.values() ?? []) {
      blockerSets.push(new Set([...blockers].map(fixedToken)));
    }
    for (const placement of placementsByTarget.get(pivot.key) ?? []) {
      const blockers = new Set();
      for (const key of placement.cellKeys) {
        const owner = selectedOwnerByCell.get(key);
        if (owner !== undefined) blockers.add(placementToken(owner));
      }
      if (blockers.size) {
        blockerSets.push(blockers);
        continue;
      }
      const residual = branchResiduals.get(placement.id);
      if (!residual) return null;
      for (const token of residual) conflict.add(token);
    }
    const blockers = greedyHittingSet(blockerSets);
    if (blockers === null) return null;
    for (const token of blockers) conflict.add(token);
    return conflict;
  };

  const addSelectedPlacement = placement => {
    selectedPlacementIds.add(placement.id);
    for (const key of placement.cellKeys) selectedOwnerByCell.set(key, placement.id);
    if (nextLayerLookaheadActive) updateLookaheadForPlacementNow(placement, true);
    else if (chosen.length >= nextLayerCoverabilityMinPlacements) activateNextLayerLookahead();
    for (const nogood of nogoodsByPlacement.get(placement.id) ?? []) {
      nogood.selected += 1;
      if (nogood.selected === nogood.ids.length) violatedNogoods.add(nogood);
    }
  };
  const removeSelectedPlacement = placement => {
    for (const nogood of nogoodsByPlacement.get(placement.id) ?? []) {
      if (nogood.selected === nogood.ids.length) violatedNogoods.delete(nogood);
      nogood.selected -= 1;
    }
    if (nextLayerLookaheadActive
      && chosen.length - 1 < nextLayerCoverabilityMinPlacements) {
      deactivateNextLayerLookahead();
    } else if (nextLayerLookaheadActive) {
      updateLookaheadForPlacementNow(placement, false);
    }
    for (const key of placement.cellKeys) selectedOwnerByCell.delete(key);
    selectedPlacementIds.delete(placement.id);
  };
  const learnNogoodExact = ids => {
    if (!nogoodsEnabled || nogoods.length >= nogoodLimit) {
      if (nogoodsEnabled && nogoods.length >= nogoodLimit) nogoodSaturated = true;
      return null;
    }
    const sortedIds = [...new Set(ids)].sort((left, right) => left - right);
    // If an already learned clause is a subset, it prunes every state this
    // clause could prune. Clauses are tiny here, so exact subset enumeration
    // is cheaper than carrying redundant memberships through every decision.
    if (sortedIds.length < 20) {
      const subsetCount = 1 << sortedIds.length;
      for (let mask = 0; mask < subsetCount - 1; mask++) {
        const subset = [];
        for (let index = 0; index < sortedIds.length; index++) {
          if (mask & (1 << index)) subset.push(sortedIds[index]);
        }
        if (nogoodKeys.has(subset.join(","))) return null;
      }
    }
    const key = sortedIds.join(",");
    if (nogoodKeys.has(key)) return null;
    const nogood = {
      ids: sortedIds,
      selected: sortedIds.reduce((sum, id) => sum + Number(selectedPlacementIds.has(id)), 0)
    };
    nogoodKeys.add(key);
    nogoods.push(nogood);
    nogoodCells += sortedIds.length;
    nogoodMaxSize = Math.max(nogoodMaxSize, sortedIds.length);
    for (const id of sortedIds) {
      if (!nogoodsByPlacement.has(id)) nogoodsByPlacement.set(id, []);
      nogoodsByPlacement.get(id).push(nogood);
    }
    if (nogood.selected === nogood.ids.length) violatedNogoods.add(nogood);
    return nogood;
  };
  const learnNogood = ids => {
    const learned = learnNogoodExact(ids);
    if (!symmetryNogoodsEnabled) return learned;
    const keys = [...new Set(ids)].map(id => orderedPlacements[id]?.key);
    if (keys.some(key => !key)) return learned;
    let firstLearned = learned;
    for (const clauseKeys of polycubePlacementClauseOrbitKeys(root, keys, { includeReflections })) {
      const transformedIds = clauseKeys.map(key => placementIdByKey.get(key));
      if (transformedIds.some(id => !Number.isInteger(id))) continue;
      const transformed = learnNogoodExact(transformedIds);
      if (transformed && transformed !== learned) symmetryNogoodClauses += 1;
      if (!firstLearned && transformed) firstLearned = transformed;
    }
    return firstLearned;
  };
  const learnDeadColumnNogood = pivot => {
    if (!nogoodsEnabled) return null;
    const blockerSets = [];
    for (const placement of placementsByTarget.get(pivot.key) ?? []) {
      const blockers = new Set();
      for (const key of placement.cellKeys) {
        const owner = selectedOwnerByCell.get(key);
        if (owner !== undefined) blockers.add(owner);
      }
      // A row with no selected blocker should still be active. Refuse to learn
      // rather than turn an internal inconsistency into an unsound clause.
      if (!blockers.size) return null;
      blockerSets.push(blockers);
    }
    if (!blockerSets.length) return learnNogood([]);
    const uncovered = new Set(blockerSets.map((_, index) => index));
    const selected = [];
    while (uncovered.size) {
      const frequencies = new Map();
      for (const index of uncovered) for (const id of blockerSets[index]) {
        frequencies.set(id, (frequencies.get(id) ?? 0) + 1);
      }
      let bestId = null;
      let bestCount = -1;
      for (const [id, count] of frequencies) {
        if (count > bestCount || (count === bestCount && id < bestId)) {
          bestId = id;
          bestCount = count;
        }
      }
      if (bestId === null) return null;
      selected.push(bestId);
      for (const index of [...uncovered]) {
        if (blockerSets[index].has(bestId)) uncovered.delete(index);
      }
    }
    // Greedy hitting sets can contain a choice made redundant by a later,
    // broader blocker. Remove every such choice before storing the clause.
    for (let index = selected.length - 1; index >= 0; index--) {
      const without = selected.filter((_, candidateIndex) => candidateIndex !== index);
      if (blockerSets.every(blockers => without.some(id => blockers.has(id)))) {
        selected.splice(index, 1);
      }
    }
    return learnNogood(selected);
  };
  if (nogoodsEnabled) {
    for (const clauseKeys of options.initialNogoodPlacementKeys ?? []) {
      if (!Array.isArray(clauseKeys)) continue;
      const ids = clauseKeys.map(key => placementIdByKey.get(key));
      if (ids.some(id => !Number.isInteger(id))) continue;
      if (learnNogood(ids)) initialNogoodClauses += 1;
    }
  }

  const nextLayerDeadTargetConflict = targetKey => {
    const blockerSets = [];
    for (const choice of lookaheadChoicesByTarget.get(targetKey) ?? []) {
      if (lookaheadChoiceAvailable(choice)) return null;
      const blockers = new Set();
      if (!fixedPlacementKeys.has(choice.key)) {
        for (const key of choice.cellKeys) {
          const fixedOwner = fixedOwnerByCell.get(key);
          if (fixedOwner !== undefined) blockers.add(fixedToken(fixedOwner));
          const selectedOwner = selectedOwnerByCell.get(key);
          if (selectedOwner !== undefined) blockers.add(placementToken(selectedOwner));
        }
      }
      if (!blockers.size) return null;
      blockerSets.push(blockers);
    }
    return greedyHittingSet(blockerSets);
  };
  const pruneDeadNextLayerTarget = () => {
    if (!nextLayerLookaheadActive) return false;
    const targetKey = deadNextLayerTargets.values().next().value;
    if (!targetKey) return false;
    nextLayerPrunes += 1;
    const conflict = nextLayerDeadTargetConflict(targetKey);
    lastConflict = conflictExplanationsEnabled ? conflict : null;
    if (conflict && [...conflict].every(token => token.startsWith("p:"))) {
      const ids = [...conflict].map(token => Number(token.slice(2)));
      if (learnNogood(ids)) nextLayerNogoodClauses += 1;
    }
    return true;
  };

  const overBudget = () => {
    if (nodes >= nodeLimit) { stoppedBy = "node_limit"; return true; }
    if ((nodes === 0 || (nodes & 1023) === 0)
      && budgetElapsedMilliseconds() >= timeLimitMs) {
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
    if (violatedNogoods.size) {
      nogoodPrunes += 1;
      if (conflictExplanationsEnabled) {
        const violated = violatedNogoods.values().next().value;
        lastConflict = violated
          ? fixedConditionedConflict(violated.ids)
          : null;
      }
      return null;
    }
    if (pruneDeadNextLayerTarget()) return null;
    if (header.right === header) {
      const solution = chosen.slice();
      if (!acceptSolution) return solution;
      const decision = acceptSolution(solution);
      if (decision === true || decision?.accept === true) return solution;
      lastConflict = null;
      if (decision?.nogood_placement_indices?.length) {
        const ids = decision.nogood_placement_indices
          .map(index => solution[index]?.id)
          .filter(id => Number.isInteger(id));
        if (ids.length === decision.nogood_placement_indices.length) {
          learnNogood(ids);
          if (conflictExplanationsEnabled) lastConflict = fixedConditionedConflict(ids);
        }
      } else if (decision?.nogood_placement_keys?.length) {
        const idsByKey = new Map(solution.map(placement => [placement.key, placement.id]));
        const ids = decision.nogood_placement_keys
          .map(key => idsByKey.get(key))
          .filter(id => Number.isInteger(id));
        if (ids.length === decision.nogood_placement_keys.length) {
          learnNogood(ids);
          if (conflictExplanationsEnabled) lastConflict = fixedConditionedConflict(ids);
        }
      }
      solutionsRejected += 1;
      return null;
    }
    if (overBudget()) {
      lastConflict = null;
      return null;
    }
    nodes += 1;
    let pivot = header.right;
    for (let column = pivot.right; column !== header; column = column.right) {
      if (column.size < pivot.size
        || (seed && column.size === pivot.size
          && seededHash(column.key) < seededHash(pivot.key))) pivot = column;
      if (pivot.size <= 1) break;
    }
    if (!pivot.size) {
      deadEnds += 1;
      learnDeadColumnNogood(pivot);
      lastConflict = explainPivotFailure(pivot);
      return null;
    }
    const branchResiduals = conflictExplanationsEnabled ? new Map() : null;
    cover(pivot);
    for (let row = pivot.down; row !== pivot; row = row.down) {
      chosen.push(row.placement);
      addSelectedPlacement(row.placement);
      maximumDepth = Math.max(maximumDepth, chosen.length);
      for (let node = row.right; node !== row; node = node.right) cover(node.column);
      const solution = search();
      if (solution) return solution;
      const childConflict = lastConflict;
      for (let node = row.left; node !== row; node = node.left) uncover(node.column);
      removeSelectedPlacement(row.placement);
      chosen.pop();
      if (conflictExplanationsEnabled) {
        if (!childConflict) {
          lastConflict = null;
        } else {
          const rowToken = placementToken(row.placement.id);
          if (!childConflict.has(rowToken)) {
            conflictBackjumps += 1;
            uncover(pivot);
            lastConflict = childConflict;
            return null;
          }
          const residual = new Set(childConflict);
          residual.delete(rowToken);
          branchResiduals.set(row.placement.id, residual);
        }
      }
      if (stoppedBy || violatedNogoods.size) break;
    }
    uncover(pivot);
    if (conflictExplanationsEnabled && !stoppedBy) {
      lastConflict = explainPivotFailure(pivot, branchResiduals);
    }
    if (!stoppedBy) deadEnds += 1;
    return null;
  };

  const solution = search();
  const exhausted = !solution && !stoppedBy;
  const resolvedFixedIndices = exhausted && lastConflict
    && [...lastConflict].every(token => token.startsWith("f:"))
    ? [...lastConflict]
        .map(token => Number(token.slice(2)))
        .sort((left, right) => left - right)
    : null;
  const resolvedFixedConflict = resolvedFixedIndices
    ? {
        kind: "resolved_subtree_conflict",
        target_cell: null,
        fixed_placement_indices: resolvedFixedIndices,
        candidate_rows_blocked: null,
        fixed_placement_keys: resolvedFixedIndices
          .map(index => fixedPlacements[index]?.key)
          .filter(Boolean)
      }
    : null;
  return {
    success: !!solution,
    exhausted,
    certified_non_tiler: exhausted,
    stopped_by: stoppedBy,
    layers,
    target_cells: allTargetKeys.length,
    remaining_target_cells: targetKeys.length,
    fixed_placements: fixedPlacements.length,
    forbidden_placements: forbiddenPlacementKeys.size,
    forbidden_orientations: forbiddenOrientationKeys.size,
    preferred_placements_requested: preferredPlacementKeys.size,
    preferred_placements_matched: orderedPlacements.reduce((count, placement) =>
      count + Number(preferredPlacementKeys.has(placement.key)), 0),
    placement_ordering: placementOrdering,
    orientations: orientations.length,
    placements_considered: placementByKey.size,
    nodes,
    memo_hits: 0,
    failed_states: deadEnds,
    nogoods_enabled: nogoodsEnabled,
    nogood_limit: nogoodLimit,
    nogood_saturated: nogoodSaturated,
    symmetry_nogoods_enabled: symmetryNogoodsEnabled,
    symmetry_nogood_clauses: symmetryNogoodClauses,
    next_layer_coverability_enabled: nextLayerCoverabilityEnabled,
    next_layer_coverability_min_placements: nextLayerCoverabilityMinPlacements,
    next_layer_target_cells: nextLayerTargetKeys.length,
    next_layer_lookahead_placements: lookaheadChoices.length,
    next_layer_coverability_prunes: nextLayerPrunes,
    next_layer_coverability_nogood_clauses: nextLayerNogoodClauses,
    conflict_backjumping_enabled: options.conflictBackjumping === true,
    conflict_backjumps: conflictBackjumps,
    initial_nogood_clauses: initialNogoodClauses,
    nogood_clauses: nogoods.length,
    nogood_prunes: nogoodPrunes,
    nogood_average_size: nogoods.length ? nogoodCells / nogoods.length : 0,
    nogood_max_size: nogoodMaxSize,
    maximum_depth: maximumDepth,
    fixed_obstruction_nogood: minimumFixedObstruction ?? resolvedFixedConflict,
    fixed_obstruction_nogoods: fixedObstructions,
    resolved_fixed_conflict: resolvedFixedConflict,
    nogood_clause_keys: options.returnNogoods
      ? nogoods.map(nogood => nogood.ids.map(id => orderedPlacements[id].key))
      : null,
    solutions_rejected: solutionsRejected,
    algorithm: "generalized_dancing_links",
    seed,
    time_budget_clock: timeBudgetMode,
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
