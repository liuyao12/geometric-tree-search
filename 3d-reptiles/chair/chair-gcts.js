export const CANONICAL_CHILDREN = [
  [[0, 0, 0], [1, 1, 1]],
  [[0, 0, 2], [1, 1, 0]],
  [[0, 2, 0], [1, 0, 1]],
  [[0, 2, 2], [1, 0, 0]],
  [[1, 1, 1], [1, 1, 1]],
  [[2, 0, 0], [0, 1, 1]],
  [[2, 0, 2], [0, 1, 0]],
  [[2, 2, 0], [0, 0, 1]]
];

export const FACE_DIRECTIONS = [
  [0, 0, -1], [0, 0, 1],
  [0, -1, 0], [0, 1, 0],
  [-1, 0, 0], [1, 0, 0]
];

const add = (left, right) => left.map((value, axis) => value + right[axis]);
const subtract = (left, right) => left.map((value, axis) => value - right[axis]);
const pointKey = point => point.join(",");
const faceKey = (cell, direction) => `${pointKey(cell)}|${pointKey(direction)}`;
const opposite = direction => direction.map(value => -value);

function transformedChild(origin4, missing, parentMissing, childSize, parentSize) {
  const factor = childSize / 2;
  const childOrigin = origin4.map(coordinate => coordinate * factor);
  const childMissing = [...missing];
  for (let axis = 0; axis < 3; axis += 1) {
    if (parentMissing[axis] === 0) {
      childOrigin[axis] = parentSize - childSize - childOrigin[axis];
      childMissing[axis] = 1 - childMissing[axis];
    }
  }
  return [childOrigin, childMissing];
}

export function chairLeaves(level, origin = [0, 0, 0], missingCorner = [1, 1, 1], path = []) {
  if (level === 0) return [{ origin, missingCorner, path }];
  const parentSize = 2 ** (level + 1);
  const childSize = parentSize / 2;
  return CANONICAL_CHILDREN.flatMap(([canonicalOrigin, canonicalMissing], childIndex) => {
    const [relativeOrigin, childMissing] = transformedChild(
      canonicalOrigin,
      canonicalMissing,
      missingCorner,
      childSize,
      parentSize
    );
    return chairLeaves(level - 1, add(origin, relativeOrigin), childMissing, [...path, childIndex]);
  });
}

export function localCells(missingCorner) {
  const cells = [];
  for (let x = 0; x < 2; x += 1) {
    for (let y = 0; y < 2; y += 1) {
      for (let z = 0; z < 2; z += 1) {
        if (x !== missingCorner[0] || y !== missingCorner[1] || z !== missingCorner[2]) cells.push([x, y, z]);
      }
    }
  }
  return cells;
}

function commonPrefixLength(left, right) {
  let length = 0;
  while (length < left.length && left[length] === right[length]) length += 1;
  return length;
}

function connectorChannel(left, right, leftLocal, rightLocal, direction) {
  const prefix = commonPrefixLength(left.path, right.path);
  const leftCode = `${left.path.join("")}:${pointKey(leftLocal)}`;
  const rightCode = `${right.path.join("")}:${pointKey(rightLocal)}`;
  const ordered = leftCode < rightCode ? [leftCode, rightCode] : [rightCode, leftCode];
  const axis = direction.findIndex(value => value !== 0);
  return `h${left.path.length - prefix}:a${axis}:${ordered[0]}~${ordered[1]}`;
}

function variantSignature(variant) {
  const marks = variant.marks
    .map(mark => `${pointKey(mark.cell)}|${pointKey(mark.direction)}|${mark.channel}|${mark.polarity}`)
    .sort()
    .join(";");
  return `${pointKey(variant.missingCorner)}::${marks}`;
}

export function buildCollaredCatalog(level = 2) {
  const leaves = chairLeaves(level).map((leaf, id) => ({ ...leaf, id, marks: [] }));
  const occupied = new Map();
  for (const leaf of leaves) {
    for (const cell of localCells(leaf.missingCorner)) occupied.set(pointKey(add(leaf.origin, cell)), leaf.id);
  }

  for (const left of leaves) {
    for (const leftLocal of localCells(left.missingCorner)) {
      const worldCell = add(left.origin, leftLocal);
      for (const direction of FACE_DIRECTIONS) {
        const rightId = occupied.get(pointKey(add(worldCell, direction)));
        if (rightId === undefined || rightId <= left.id) continue;
        const right = leaves[rightId];
        const rightLocal = subtract(add(worldCell, direction), right.origin);
        const channel = connectorChannel(left, right, leftLocal, rightLocal, direction);
        left.marks.push({ cell: leftLocal, direction, channel, polarity: 1 });
        right.marks.push({ cell: rightLocal, direction: opposite(direction), channel, polarity: -1 });
      }
    }
  }

  const variants = [];
  const signatureToId = new Map();
  const multiplicities = [];
  const occurrenceVariantIds = [];
  for (const leaf of leaves) {
    const draft = {
      id: -1,
      missingCorner: leaf.missingCorner,
      cells: localCells(leaf.missingCorner),
      marks: leaf.marks
    };
    const signature = variantSignature(draft);
    let id = signatureToId.get(signature);
    if (id === undefined) {
      id = variants.length;
      signatureToId.set(signature, id);
      variants.push({ ...draft, id });
      multiplicities.push(0);
    }
    multiplicities[id] += 1;
    occurrenceVariantIds.push(id);
  }

  const center = (2 ** (level + 1)) / 2;
  const seedOccurrence = leaves.reduce((best, leaf) => {
    const chairCenter = leaf.origin.map(value => value + 1);
    const distance = chairCenter.reduce((sum, value) => sum + (value - center) ** 2, 0);
    return distance < best.distance ? { id: leaf.id, distance } : best;
  }, { id: 0, distance: Infinity }).id;

  return {
    level,
    targetCount: leaves.length,
    variants,
    multiplicities,
    seedVariantId: occurrenceVariantIds[seedOccurrence],
    connectorCount: new Set(variants.flatMap(variant => variant.marks.map(mark => mark.channel))).size
  };
}

function placementCells(placement, variant) {
  return variant.cells.map(cell => add(placement.origin, cell));
}

function placementMarkMap(placement, variant) {
  return new Map(variant.marks.map(mark => [
    faceKey(add(placement.origin, mark.cell), mark.direction),
    mark
  ]));
}

function stateIndex(state) {
  const occupied = new Map();
  const faceMarks = new Map();
  state.placements.forEach((placement, placementIndex) => {
    const variant = state.catalog.variants[placement.variantId];
    for (const cell of placementCells(placement, variant)) occupied.set(pointKey(cell), placementIndex);
    for (const [key, mark] of placementMarkMap(placement, variant)) faceMarks.set(key, mark);
  });
  return { occupied, faceMarks };
}

function remainingVariantCount(state, variantId) {
  const used = state.placements.reduce((count, placement) => count + (placement.variantId === variantId ? 1 : 0), 0);
  return state.catalog.multiplicities[variantId] - used;
}

function validateCandidate(state, candidate, index) {
  const variant = state.catalog.variants[candidate.variantId];
  const cells = placementCells(candidate, variant);
  if (cells.some(cell => index.occupied.has(pointKey(cell)))) return false;
  const candidateMarks = placementMarkMap(candidate, variant);
  let contacts = 0;
  for (const cell of cells) {
    for (const direction of FACE_DIRECTIONS) {
      const neighbor = add(cell, direction);
      if (!index.occupied.has(pointKey(neighbor))) continue;
      contacts += 1;
      const mark = candidateMarks.get(faceKey(cell, direction));
      const mate = index.faceMarks.get(faceKey(neighbor, opposite(direction)));
      if (!mark || !mate || mark.channel !== mate.channel || mark.polarity === mate.polarity) return false;
    }
  }
  return contacts > 0;
}

export function enumerateGrowthCandidates(state) {
  const index = stateIndex(state);
  const frontier = [];
  for (const placement of state.placements) {
    const variant = state.catalog.variants[placement.variantId];
    for (const mark of variant.marks) {
      const worldCell = add(placement.origin, mark.cell);
      if (index.occupied.has(pointKey(add(worldCell, mark.direction)))) continue;
      frontier.push({ placement, mark, worldCell });
    }
  }

  let tested = 0;
  const byFrontier = frontier.map((frontierMark, frontierIndex) => {
    const candidates = new Map();
    for (const variant of state.catalog.variants) {
      if (remainingVariantCount(state, variant.id) <= 0) continue;
      for (const mark of variant.marks) {
        tested += 1;
        if (
          mark.channel !== frontierMark.mark.channel
          || mark.polarity === frontierMark.mark.polarity
          || pointKey(mark.direction) !== pointKey(opposite(frontierMark.mark.direction))
        ) continue;
        const targetCell = add(frontierMark.worldCell, frontierMark.mark.direction);
        const candidate = { variantId: variant.id, origin: subtract(targetCell, mark.cell) };
        const key = `${candidate.variantId}@${pointKey(candidate.origin)}`;
        if (validateCandidate(state, candidate, index)) candidates.set(key, candidate);
      }
    }
    return { frontierIndex, candidates: [...candidates.values()] };
  });
  const viable = byFrontier.filter(entry => entry.candidates.length > 0);
  viable.sort((left, right) => left.candidates.length - right.candidates.length || left.frontierIndex - right.frontierIndex);
  return {
    frontierCount: frontier.length,
    tested,
    candidates: viable[0]?.candidates ?? []
  };
}

function appendCandidate(state, candidate) {
  return { ...state, placements: [...state.placements, candidate] };
}

function placementStateKey(state) {
  return state.placements
    .map(placement => `${placement.variantId}@${pointKey(placement.origin)}`)
    .sort()
    .join(";");
}

export function solveGrowthPlan(catalog) {
  const initial = {
    catalog,
    placements: [{ variantId: catalog.seedVariantId, origin: [0, 0, 0] }]
  };
  const failed = new Set();
  const diagnostics = { nodes: 0, backtracks: 0 };

  function search(state) {
    diagnostics.nodes += 1;
    if (state.placements.length === catalog.targetCount) return [];
    const key = placementStateKey(state);
    if (failed.has(key)) return null;
    const result = enumerateGrowthCandidates(state);
    for (const candidate of result.candidates) {
      const suffix = search(appendCandidate(state, candidate));
      if (suffix) return [candidate, ...suffix];
      diagnostics.backtracks += 1;
    }
    failed.add(key);
    return null;
  }

  const plan = search(initial);
  if (!plan) throw new Error("The collared chair catalogue has no complete locally matched growth.");
  return { plan, diagnostics };
}

export function createGrowthState(level = 2) {
  const catalog = buildCollaredCatalog(level);
  const solved = solveGrowthPlan(catalog);
  return {
    catalog,
    placements: [{ variantId: catalog.seedVariantId, origin: [0, 0, 0] }],
    rejected: 0,
    tested: 0,
    history: [],
    plan: solved.plan,
    solverNodes: solved.diagnostics.nodes,
    solverBacktracks: solved.diagnostics.backtracks
  };
}

export function growOne(state) {
  const result = enumerateGrowthCandidates(state);
  if (!result.candidates.length) return { ...state, tested: state.tested + result.tested, frontierCount: result.frontierCount, complete: true };
  const planned = state.plan[state.placements.length - 1];
  const candidate = result.candidates.find(option =>
    option.variantId === planned.variantId && pointKey(option.origin) === pointKey(planned.origin)
  );
  if (!candidate) throw new Error("The cached local-search plan diverged from the current frontier.");
  return {
    ...state,
    placements: [...state.placements, candidate],
    rejected: state.rejected + Math.max(0, result.tested - result.candidates.length),
    tested: state.tested + result.tested,
    frontierCount: result.frontierCount,
    history: [...state.history, { rejected: state.rejected, tested: state.tested }],
    complete: state.placements.length + 1 >= state.catalog.targetCount
  };
}

export function shrinkOne(state) {
  if (state.placements.length <= 1) return state;
  const previous = state.history[state.history.length - 1] ?? { rejected: 0, tested: 0 };
  return {
    ...state,
    placements: state.placements.slice(0, -1),
    rejected: previous.rejected,
    tested: previous.tested,
    history: state.history.slice(0, -1),
    complete: false
  };
}

export function exposedMarks(state) {
  const index = stateIndex(state);
  const marks = [];
  for (const placement of state.placements) {
    const variant = state.catalog.variants[placement.variantId];
    for (const mark of variant.marks) {
      const cell = add(placement.origin, mark.cell);
      if (!index.occupied.has(pointKey(add(cell, mark.direction)))) marks.push({ ...mark, cell });
    }
  }
  return marks;
}
