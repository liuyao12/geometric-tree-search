export const PROPOSAL_FEATURES = Object.freeze([
  "coverage",
  "oldest_layer_completion",
  "growth_axis_rank",
  "growth_isotropy",
  "growth_planarity",
  "growth_compactness",
  "frontier_reduction",
  "same_orientation",
  "root_corona",
  "isohedral_reuse",
  "vector_repeat",
  "pair_periodic",
  "periodic_continuation",
  "parallelogram_completion"
]);

const DEFAULT_WEIGHTS = Object.freeze({
  coverage: 1,
  oldest_layer_completion: 1,
  growth_axis_rank: 0,
  growth_isotropy: 0,
  growth_planarity: 0,
  growth_compactness: 0,
  frontier_reduction: 0,
  same_orientation: 0,
  root_corona: 0,
  isohedral_reuse: 0,
  vector_repeat: 0,
  pair_periodic: 0,
  periodic_continuation: 0,
  parallelogram_completion: 0
});

const finiteNumber = (value, fallback = 0) => Number.isFinite(Number(value)) ? Number(value) : fallback;

const normalizeWeights = (raw = {}) => {
  const weights = {};
  for (const feature of PROPOSAL_FEATURES) {
    weights[feature] = finiteNumber(raw?.[feature], DEFAULT_WEIGHTS[feature]);
  }
  return weights;
};

const activeFeaturesForWeights = weights =>
  PROPOSAL_FEATURES.filter(feature => Math.abs(weights[feature]) > 1e-9);

export function proposalTileKey(config = {}) {
  const refs = config?.custom_system?.figure_refs ?? [];
  const customSignatures = [
    ...(config?.custom_system?.polycubes ?? []).map(tile =>
      JSON.stringify({ name: tile.name, voxels: tile.voxels })
    ),
    ...(config?.custom_system?.polyhedra ?? []).map(tile =>
      JSON.stringify({ name: tile.name, vertices: tile.vertices, faces: tile.faces ?? null })
    )
  ];
  return [
    config?.mode_key ?? "tile",
    config?.polycube_lattice ?? "z3",
    ...refs,
    ...customSignatures
  ].join("::");
}

export function normalizeProposalProgram(raw = {}) {
  const rawSequence = Array.isArray(raw.sequence) && raw.sequence.length
    ? raw.sequence
    : [{ weights: raw.weights }];
  const sequence = rawSequence.slice(0, 8).map((step, index) => {
    const weights = normalizeWeights(step?.weights ?? step);
    return {
      id: String(step?.id ?? `step-${index}`),
      weights,
      active_features: activeFeaturesForWeights(weights)
    };
  });
  const weights = { ...sequence[0].weights };
  const activeFeatures = [...new Set(sequence.flatMap(step => step.active_features))];
  const patch = Array.isArray(raw.patch)
    ? raw.patch.slice(0, 512).map((placement, index) => ({
        index,
        prototile_idx: Math.max(0, Math.floor(finiteNumber(placement?.prototile_idx, 0))),
        orientation_id: placement?.orientation_id == null ? null : String(placement.orientation_id),
        orientation_signature: placement?.orientation_signature == null
          ? null
          : String(placement.orientation_signature),
        orientation_index: placement?.orientation_index == null
          ? null
          : Math.max(0, Math.floor(finiteNumber(placement.orientation_index, 0))),
        translation: [0, 1, 2].map(axis => finiteNumber(placement?.translation?.[axis], 0))
      }))
    : [];
  return {
    version: 2,
    id: String(raw.id ?? "proposal"),
    tile_key: raw.tile_key == null ? null : String(raw.tile_key),
    generation: Math.max(0, Math.floor(finiteNumber(raw.generation, 0))),
    parent_id: raw.parent_id == null ? null : String(raw.parent_id),
    weights,
    active_features: activeFeatures,
    patch_size: sequence.length,
    sequence,
    patch
  };
}

export function proposalProgramFromPatchSnapshot(config, snapshot, priorRaw = null) {
  const placements = snapshot?.placements;
  const prior = priorRaw ? normalizeProposalProgram(priorRaw) : null;
  if (!Array.isArray(placements) || placements.length < 2) return prior;
  const rootTranslation = placements[0].translation ?? [0, 0, 0];
  const tileKey = proposalTileKey(config);
  return normalizeProposalProgram({
    id: `live-${tileKey}-g${(prior?.generation ?? -1) + 1}`,
    tile_key: tileKey,
    generation: (prior?.generation ?? -1) + 1,
    parent_id: prior?.id ?? null,
    sequence: prior?.sequence ?? [{
      weights: {
        coverage: 1,
        oldest_layer_completion: 1,
        growth_axis_rank: 2,
        growth_isotropy: 1,
        growth_compactness: 0.25
      }
    }],
    patch: placements.map(placement => ({
      prototile_idx: placement.prototile_idx ?? 0,
      orientation_id: placement.orientation_id ?? null,
      orientation_signature: placement.orientation_signature ?? null,
      orientation_index: placement.orientation_index ?? null,
      translation: [0, 1, 2].map(axis =>
        Number(placement.translation?.[axis] ?? 0) - Number(rootTranslation[axis] ?? 0)
      )
    }))
  });
}

export function proposalComplexity(program) {
  const normalized = normalizeProposalProgram(program);
  const activeCount = normalized.sequence.reduce((sum, step) => sum + step.active_features.length, 0);
  const weightMagnitude = normalized.sequence.reduce((sum, step) =>
    sum + step.active_features.reduce(
      (stepSum, feature) => stepSum + Math.log1p(Math.abs(step.weights[feature])),
      0
    ), 0);
  return activeCount
    + weightMagnitude * 0.05
    + (normalized.patch_size - 1) * 0.35
    + Math.log1p(normalized.patch.length) * 0.02;
}

export function seededRandom(seed = 1) {
  let state = (Math.floor(finiteNumber(seed, 1)) >>> 0) || 0x6d2b79f5;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

const gaussian = (random) => {
  const u = Math.max(1e-12, random());
  const v = Math.max(1e-12, random());
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
};

export function createInitialProposalPopulation({
  tileKey = null,
  populationSize = 18,
  seed = 1
} = {}) {
  const random = seededRandom(seed);
  const population = [];
  const anchors = [
    { coverage: 1, oldest_layer_completion: 1 },
    { coverage: 1, growth_axis_rank: 2, growth_isotropy: 1, growth_compactness: 0.25 },
    { coverage: 1, isohedral_reuse: 2, root_corona: 0.5, same_orientation: 0.25 },
    { coverage: 1, vector_repeat: 1, pair_periodic: 2, periodic_continuation: 1, parallelogram_completion: 2 },
    { coverage: 1, frontier_reduction: 1, oldest_layer_completion: 1 }
  ];
  const sequenceAnchors = [
    [
      { coverage: 1, oldest_layer_completion: 1, growth_axis_rank: 2 },
      { coverage: 1, growth_isotropy: 2, growth_compactness: 0.3 }
    ],
    [
      { coverage: 1, root_corona: 2, isohedral_reuse: 1 },
      { coverage: 1, isohedral_reuse: 2, frontier_reduction: 0.5 }
    ],
    [
      { coverage: 1, pair_periodic: 2, parallelogram_completion: 1 },
      { coverage: 1, periodic_continuation: 2, vector_repeat: 0.5 },
      { coverage: 1, growth_axis_rank: 2, growth_isotropy: 1 }
    ]
  ];
  for (let index = 0; index < Math.max(1, populationSize); index++) {
    const anchor = anchors[index % anchors.length];
    const structuralIndex = index - anchors.length;
    const sourceSequence = structuralIndex >= 0 && structuralIndex < sequenceAnchors.length
      ? sequenceAnchors[structuralIndex]
      : [anchor];
    const sequence = sourceSequence.map((source, stepIndex) => {
      const weights = {};
      for (const feature of PROPOSAL_FEATURES) {
        const centered = finiteNumber(source[feature], 0);
        const explore = index < anchors.length + sequenceAnchors.length ? 0 : gaussian(random) * 0.75;
        const keep = centered !== 0 || random() < 0.3;
        weights[feature] = keep ? centered + explore : 0;
      }
      return { id: `step-${stepIndex}`, weights };
    });
    population.push(normalizeProposalProgram({
      id: `g0-p${index}`,
      tile_key: tileKey,
      generation: 0,
      sequence
    }));
  }
  return population;
}

export function mutateProposalProgram(parent, {
  seed = 1,
  id = null,
  mutationScale = 0.45,
  featureToggleRate = 0.12
} = {}) {
  const normalized = normalizeProposalProgram(parent);
  const random = seededRandom(seed);
  let sequence = normalized.sequence.map(step => ({
    id: step.id,
    weights: { ...step.weights }
  }));
  if (random() < 0.22 && sequence.length < 8) {
    const sourceIndex = Math.floor(random() * sequence.length);
    const insertionIndex = Math.floor(random() * (sequence.length + 1));
    sequence.splice(insertionIndex, 0, {
      id: `step-${insertionIndex}`,
      weights: { ...sequence[sourceIndex].weights }
    });
  } else if (random() < 0.14 && sequence.length > 1) {
    sequence.splice(Math.floor(random() * sequence.length), 1);
  }
  for (const step of sequence) {
    for (const feature of PROPOSAL_FEATURES) {
      if (random() < featureToggleRate) {
        step.weights[feature] = Math.abs(step.weights[feature]) > 1e-9 ? 0 : gaussian(random) * mutationScale;
      } else if (Math.abs(step.weights[feature]) > 1e-9 || random() < 0.25) {
        step.weights[feature] += gaussian(random) * mutationScale;
      }
      if (Math.abs(step.weights[feature]) < 0.04) step.weights[feature] = 0;
    }
  }
  if (!sequence.some(step => Object.values(step.weights).some(value => Math.abs(value) > 1e-9))) {
    sequence[0].weights.coverage = 1;
  }
  return normalizeProposalProgram({
    id: id ?? `${normalized.id}-m${seed}`,
    tile_key: normalized.tile_key,
    generation: normalized.generation + 1,
    parent_id: normalized.id,
    sequence,
    patch: normalized.patch
  });
}

export function growthCurveArea(points, {
  horizonMs,
  targetTiles
} = {}) {
  const horizon = Math.max(1, finiteNumber(horizonMs, 1));
  const target = Math.max(1, finiteNumber(targetTiles, 1));
  const ordered = [...(points ?? [])]
    .map(point => ({
      milliseconds: Math.max(0, finiteNumber(point.milliseconds, 0)),
      tiles: Math.max(0, finiteNumber(point.tiles, 0))
    }))
    .sort((left, right) => left.milliseconds - right.milliseconds);
  let area = 0;
  let priorTime = 0;
  let bestTiles = 0;
  for (const point of ordered) {
    const time = Math.min(horizon, point.milliseconds);
    if (time > priorTime) area += (time - priorTime) * Math.min(target, bestTiles);
    bestTiles = Math.max(bestTiles, point.tiles);
    priorTime = time;
    if (time >= horizon) break;
  }
  if (priorTime < horizon) area += (horizon - priorTime) * Math.min(target, bestTiles);
  return area / (horizon * target);
}

export function scoreProposalEvaluation(evaluation, {
  horizonMs,
  targetTiles,
  complexityPenalty = 0.002
} = {}) {
  const curve = growthCurveArea(evaluation?.points, { horizonMs, targetTiles });
  const reached = Math.min(1, Math.max(0, finiteNumber(evaluation?.best_tiles, 0) / Math.max(1, targetTiles)));
  const isotropy = Math.min(1, Math.max(0, finiteNumber(evaluation?.growth_isotropy, 0)));
  const complexity = proposalComplexity(evaluation?.program);
  return curve + reached * 0.1 + isotropy * 0.02 - complexity * complexityPenalty;
}

export function nextProposalGeneration(evaluations, {
  populationSize = 18,
  eliteCount = 4,
  seed = 1
} = {}) {
  const ranked = [...(evaluations ?? [])].sort((left, right) => right.score - left.score);
  const elites = ranked.slice(0, Math.max(1, Math.min(eliteCount, ranked.length)));
  if (!elites.length) return [];
  const next = elites.map(item => normalizeProposalProgram(item.program));
  let index = next.length;
  while (next.length < populationSize) {
    const parent = elites[index % elites.length].program;
    next.push(mutateProposalProgram(parent, {
      seed: seed + index * 7919,
      id: `g${normalizeProposalProgram(parent).generation + 1}-p${index}`
    }));
    index += 1;
  }
  return next;
}
