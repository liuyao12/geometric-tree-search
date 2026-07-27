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

export function normalizeProposalProgram(raw = {}) {
  const weights = {};
  for (const feature of PROPOSAL_FEATURES) {
    weights[feature] = finiteNumber(raw.weights?.[feature], DEFAULT_WEIGHTS[feature]);
  }
  const activeFeatures = PROPOSAL_FEATURES.filter(feature => Math.abs(weights[feature]) > 1e-9);
  return {
    version: 1,
    id: String(raw.id ?? "proposal"),
    tile_key: raw.tile_key == null ? null : String(raw.tile_key),
    generation: Math.max(0, Math.floor(finiteNumber(raw.generation, 0))),
    parent_id: raw.parent_id == null ? null : String(raw.parent_id),
    weights,
    active_features: activeFeatures
  };
}

export function proposalComplexity(program) {
  const normalized = normalizeProposalProgram(program);
  return normalized.active_features.length
    + normalized.active_features.reduce((sum, feature) => sum + Math.log1p(Math.abs(normalized.weights[feature])), 0) * 0.05;
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
  for (let index = 0; index < Math.max(1, populationSize); index++) {
    const anchor = anchors[index % anchors.length];
    const weights = {};
    for (const feature of PROPOSAL_FEATURES) {
      const centered = finiteNumber(anchor[feature], 0);
      const explore = index < anchors.length ? 0 : gaussian(random) * 0.75;
      const keep = centered !== 0 || random() < 0.3;
      weights[feature] = keep ? centered + explore : 0;
    }
    population.push(normalizeProposalProgram({
      id: `g0-p${index}`,
      tile_key: tileKey,
      generation: 0,
      weights
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
  const weights = { ...normalized.weights };
  for (const feature of PROPOSAL_FEATURES) {
    if (random() < featureToggleRate) {
      weights[feature] = Math.abs(weights[feature]) > 1e-9 ? 0 : gaussian(random) * mutationScale;
    } else if (Math.abs(weights[feature]) > 1e-9 || random() < 0.25) {
      weights[feature] += gaussian(random) * mutationScale;
    }
    if (Math.abs(weights[feature]) < 0.04) weights[feature] = 0;
  }
  if (!Object.values(weights).some(value => Math.abs(value) > 1e-9)) weights.coverage = 1;
  return normalizeProposalProgram({
    id: id ?? `${normalized.id}-m${seed}`,
    tile_key: normalized.tile_key,
    generation: normalized.generation + 1,
    parent_id: normalized.id,
    weights
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
