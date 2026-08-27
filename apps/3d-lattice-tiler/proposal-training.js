import { createTilingStream, tileSpecs } from "./engine.js?v=20260827-a2-size8-v232";
import {
  createInitialProposalPopulation,
  growthCurveArea,
  nextProposalGeneration,
  normalizeProposalProgram,
  proposalTileKey,
  scoreProposalEvaluation
} from "./proposal-learner.js?v=20260824-gcts-tail-v32";

const numeric = (value, fallback) => Number.isFinite(Number(value)) ? Number(value) : fallback;
const median = values => {
  const ordered = [...values].sort((left, right) => left - right);
  return ordered[Math.floor(ordered.length / 2)] ?? 0;
};

export function normalizeProposalTrainingOptions(raw = {}) {
  return {
    target: Math.max(2, Math.floor(numeric(raw.target, 80))),
    horizon_ms: Math.max(50, numeric(raw.horizon_ms, 1500)),
    generations: Math.max(1, Math.floor(numeric(raw.generations, 2))),
    population: Math.max(2, Math.floor(numeric(raw.population, 8))),
    elite: Math.max(1, Math.floor(numeric(raw.elite, 3))),
    seed: Math.floor(numeric(raw.seed, 17)),
    min_improvement: Math.max(0, numeric(raw.min_improvement, 0.03)),
    baseline_replicates: Math.max(1, Math.floor(numeric(raw.baseline_replicates, 3))),
    proposal_replicates: Math.max(1, Math.floor(numeric(raw.proposal_replicates, 2))),
    refinement_rounds: Math.max(0, Math.floor(numeric(raw.refinement_rounds, 4))),
    refinement_horizon_multiplier: Math.max(1, numeric(raw.refinement_horizon_multiplier, 2)),
    refinement_fresh_retry: raw.refinement_fresh_retry !== false,
    seed_programs: Array.isArray(raw.seed_programs) ? raw.seed_programs.map(normalizeProposalProgram) : []
  };
}

function episodeConfig(baseConfig, options, program, randomSeed) {
  return {
    ...baseConfig,
    criterion: "count",
    target_val: options.target,
    tiling_strategy: "generic",
    move_order: program ? "proposal" : "no_brainer",
    proposal_program: program,
    greedy_no_backtrack: false,
    random_seed: randomSeed,
    template_preflight: false,
    periodic_preflight: false,
    snapshot_every: 0,
    placement_details: true,
    face_order: "coverage",
    exhaustive: false,
    branch_cap: null,
    candidate_cap: null,
    node_limit: null,
    time_limit_ms: options.horizon_ms,
    safety_max_tiles: Math.max(options.target, 200),
    ui_yield_interval_ms: Math.max(250, options.horizon_ms)
  };
}

export async function runProposalEpisode(baseConfig, rawOptions = {}, {
  program = null,
  randomSeed = 1,
  stopToken = { stop: false }
} = {}) {
  const options = normalizeProposalTrainingOptions(rawOptions);
  const started = performance.now();
  const points = [{ milliseconds: 0, tiles: 1 }];
  let bestTiles = 1;
  let bestPatch = [];
  let final = null;
  for await (const message of createTilingStream(
    episodeConfig(baseConfig, options, program, randomSeed),
    tileSpecs,
    stopToken
  )) {
    if (stopToken.stop) break;
    const tiles = Number(message?.tile_count ?? message?.snapshot?.tile_count ?? 0);
    if (
      tiles > bestTiles
      && (message.type === "placement_delta" || message.type === "full_update" || message.type === "node_snapshot")
    ) {
      bestTiles = tiles;
      points.push({ milliseconds: performance.now() - started, tiles });
    }
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    if (Array.isArray(snapshot?.placements) && snapshot.placements.length > bestPatch.length) {
      const rootTranslation = snapshot.placements[0]?.translation ?? [0, 0, 0];
      bestPatch = snapshot.placements.map(placement => ({
        prototile_idx: placement.prototile_idx ?? 0,
        orientation_id: placement.orientation_id ?? null,
        orientation_signature: placement.orientation_signature ?? null,
        orientation_index: placement.orientation_index ?? null,
        translation: [0, 1, 2].map(axis =>
          Number(placement.translation?.[axis] ?? 0) - Number(rootTranslation[axis] ?? 0)
        )
      }));
    }
    if (message.type === "finished") final = message;
  }
  const elapsedMs = performance.now() - started;
  return {
    program: program ? normalizeProposalProgram(program) : null,
    random_seed: randomSeed,
    success: !!final?.success,
    best_tiles: Math.max(bestTiles, Number(final?.tile_count ?? 0)),
    elapsed_ms: elapsedMs,
    points,
    patch: bestPatch,
    growth_isotropy: Number(final?.search_stats?.growth_isotropy ?? 0),
    backtracks: Number(final?.search_stats?.backtracks ?? 0),
    proposal_patch_tiles_replayed: Number(final?.search_stats?.proposal_patch_tiles_replayed ?? 0),
    proposal_patch_conflicts: Number(final?.search_stats?.proposal_patch_conflicts ?? 0),
    proposal_patch_conflict_index: final?.search_stats?.proposal_patch_conflict_index ?? null,
    proposal_patch_conflict_reason: final?.search_stats?.proposal_patch_conflict_reason ?? null,
    result_kind: final?.result_kind ?? null
  };
}

function aggregateEpisodes(episodes, options, program = null) {
  const scores = episodes.map(episode => program
    ? scoreProposalEvaluation({ ...episode, program }, {
        horizonMs: options.horizon_ms,
        targetTiles: options.target
      })
    : growthCurveArea(episode.points, {
        horizonMs: options.horizon_ms,
        targetTiles: options.target
      }) + Math.min(1, episode.best_tiles / options.target) * 0.1
  );
  return {
    program,
    score: median(scores),
    best_tiles: median(episodes.map(episode => episode.best_tiles)),
    elapsed_ms: median(episodes.map(episode => episode.elapsed_ms)),
    growth_isotropy: median(episodes.map(episode => episode.growth_isotropy)),
    episodes
  };
}

async function evaluateProgram(baseConfig, options, program, seedOffset, stopToken) {
  const episodes = [];
  for (let replicate = 0; replicate < options.proposal_replicates && !stopToken.stop; replicate++) {
    episodes.push(await runProposalEpisode(baseConfig, options, {
      program,
      randomSeed: options.seed + seedOffset + replicate * 104729,
      stopToken
    }));
  }
  return aggregateEpisodes(episodes, options, program);
}

const programWithPatch = (program, patch, suffix) => {
  const normalized = normalizeProposalProgram(program);
  return normalizeProposalProgram({
    ...normalized,
    id: `${normalized.id}-${suffix}`,
    generation: normalized.generation + 1,
    parent_id: normalized.id,
    patch
  });
};

export async function trainProposalProgram(baseConfig, rawOptions = {}, {
  stopToken = { stop: false },
  onProgress = () => {}
} = {}) {
  const options = normalizeProposalTrainingOptions(rawOptions);
  const tileKey = proposalTileKey(baseConfig);
  const started = performance.now();
  const baselineEpisodes = [];
  onProgress({ phase: "baseline", tile_key: tileKey, completed: 0, total: options.baseline_replicates });
  for (let replicate = 0; replicate < options.baseline_replicates && !stopToken.stop; replicate++) {
    baselineEpisodes.push(await runProposalEpisode(baseConfig, options, {
      randomSeed: options.seed + replicate * 104729,
      stopToken
    }));
    onProgress({
      phase: "baseline",
      tile_key: tileKey,
      completed: replicate + 1,
      total: options.baseline_replicates
    });
  }
  if (stopToken.stop) return null;
  const baseline = aggregateEpisodes(baselineEpisodes, options);

  let population = createInitialProposalPopulation({
    tileKey,
    populationSize: options.population,
    seed: options.seed
  });
  if (options.seed_programs.length) {
    population = [
      ...options.seed_programs,
      ...population
    ].slice(0, options.population);
  }
  const history = [];
  let winner = null;
  for (let generation = 0; generation < options.generations && !stopToken.stop; generation++) {
    const evaluations = [];
    for (let index = 0; index < population.length && !stopToken.stop; index++) {
      const program = population[index];
      const evaluation = await evaluateProgram(
        baseConfig,
        options,
        program,
        generation * 1000003 + index * 8191,
        stopToken
      );
      evaluations.push(evaluation);
      if (!winner || evaluation.score > winner.score) winner = evaluation;
      onProgress({
        phase: "training",
        tile_key: tileKey,
        generation,
        generations: options.generations,
        candidate: index + 1,
        population: population.length,
        best_score: winner?.score ?? null,
        best_tiles: winner?.best_tiles ?? 0,
        baseline_score: baseline.score,
        baseline_tiles: baseline.best_tiles
      });
    }
    if (!evaluations.length) break;
    const ranked = [...evaluations].sort((left, right) => right.score - left.score);
    history.push({
      generation,
      best_score: ranked[0]?.score ?? 0,
      best_tiles: ranked[0]?.best_tiles ?? 0,
      program_id: ranked[0]?.program?.id ?? null
    });
    population = nextProposalGeneration(evaluations, {
      populationSize: options.population,
      eliteCount: options.elite,
      seed: options.seed + (generation + 1) * 65537
    });
  }
  if (stopToken.stop || !winner) return null;

  const patchEpisode = [...winner.episodes].sort((left, right) =>
    right.patch.length - left.patch.length
    || left.elapsed_ms - right.elapsed_ms
  )[0];
  let learnedProgram = normalizeProposalProgram({
    ...winner.program,
    patch: patchEpisode?.patch ?? []
  });
  const refinement = [];
  for (let round = 0; round < options.refinement_rounds && !stopToken.stop; round++) {
    const refinementOptions = {
      ...options,
      horizon_ms: options.horizon_ms * (options.refinement_horizon_multiplier ** (round + 1))
    };
    const replayEpisode = await runProposalEpisode(baseConfig, refinementOptions, {
      program: learnedProgram,
      randomSeed: options.seed + 7000001 + round * 131071,
      stopToken
    });
    let bestEpisode = replayEpisode;
    if (
      options.refinement_fresh_retry
      && replayEpisode.patch.length <= learnedProgram.patch.length
      && learnedProgram.patch.length > 1
      && !stopToken.stop
    ) {
      const freshProgram = normalizeProposalProgram({ ...learnedProgram, patch: [] });
      const freshEpisode = await runProposalEpisode(baseConfig, refinementOptions, {
        program: freshProgram,
        randomSeed: options.seed + 9000011 + round * 131071,
        stopToken
      });
      if (
        freshEpisode.patch.length > bestEpisode.patch.length
        || (
          freshEpisode.patch.length === bestEpisode.patch.length
          && freshEpisode.best_tiles > bestEpisode.best_tiles
        )
      ) bestEpisode = freshEpisode;
    }
    const priorPatchTiles = learnedProgram.patch.length;
    if (bestEpisode.patch.length > priorPatchTiles) {
      learnedProgram = programWithPatch(learnedProgram, bestEpisode.patch, `r${round + 1}`);
    }
    refinement.push({
      round,
      prior_patch_tiles: priorPatchTiles,
      patch_tiles: learnedProgram.patch.length,
      best_tiles: bestEpisode.best_tiles,
      success: bestEpisode.success,
      fresh_retry: bestEpisode !== replayEpisode,
      horizon_ms: refinementOptions.horizon_ms
    });
    onProgress({
      phase: "refinement",
      tile_key: tileKey,
      round: round + 1,
      rounds: options.refinement_rounds,
      patch_tiles: learnedProgram.patch.length,
      best_tiles: bestEpisode.best_tiles
    });
    if (learnedProgram.patch.length >= options.target) break;
  }
  if (stopToken.stop) return null;

  let learnedEvaluation = await evaluateProgram(
    baseConfig,
    options,
    learnedProgram,
    12000017,
    stopToken
  );
  const validationPatch = [...learnedEvaluation.episodes].sort((left, right) =>
    right.patch.length - left.patch.length
    || left.elapsed_ms - right.elapsed_ms
  )[0]?.patch ?? [];
  if (validationPatch.length > learnedProgram.patch.length && !stopToken.stop) {
    learnedProgram = programWithPatch(learnedProgram, validationPatch, "validation");
    learnedEvaluation = await evaluateProgram(
      baseConfig,
      options,
      learnedProgram,
      14000029,
      stopToken
    );
  }
  if (stopToken.stop) return null;
  learnedEvaluation.program = learnedProgram;
  const improvement = baseline.score > 0
    ? (learnedEvaluation.score - baseline.score) / baseline.score
    : Infinity;
  const accepted = learnedEvaluation.best_tiles >= baseline.best_tiles
    && improvement >= options.min_improvement;
  return {
    type: "learned_proposal",
    version: 1,
    tile_key: tileKey,
    accepted,
    improvement,
    training_ms: performance.now() - started,
    options,
    baseline: {
      score: baseline.score,
      best_tiles: baseline.best_tiles,
      elapsed_ms: baseline.elapsed_ms,
      growth_isotropy: baseline.growth_isotropy,
      points: baseline.episodes[0]?.points ?? []
    },
    learned: {
      score: learnedEvaluation.score,
      best_tiles: learnedEvaluation.best_tiles,
      elapsed_ms: learnedEvaluation.elapsed_ms,
      growth_isotropy: learnedEvaluation.growth_isotropy,
      points: learnedEvaluation.episodes[0]?.points ?? [],
      program: learnedProgram
    },
    history,
    refinement
  };
}
