#!/usr/bin/env node

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  createInitialProposalPopulation,
  growthCurveArea,
  nextProposalGeneration,
  normalizeProposalProgram,
  proposalProgramFromPatchSnapshot,
  scoreProposalEvaluation
} from "../apps/3d-lattice-tiler/proposal-learner.js";

const splitList = value => String(value).split(",").map(item => item.trim()).filter(Boolean);
const positive = (value, fallback) => Number.isFinite(Number(value)) && Number(value) > 0
  ? Number(value)
  : fallback;

function readArgs(argv) {
  const options = {
    modes: ["cube", "gyrobifastigium", "t_cross"],
    target: 80,
    horizonMs: 1500,
    generations: 3,
    population: 12,
    elite: 3,
    refinementRounds: 4,
    refinementHorizonMultiplier: 2,
    seed: 17,
    minImprovement: 0.03,
    output: null,
    quiet: false
  };
  for (let index = 0; index < argv.length; index++) {
    const arg = argv[index];
    const next = () => {
      if (index + 1 >= argv.length) throw new Error(`${arg} requires a value`);
      index += 1;
      return argv[index];
    };
    if (arg === "--modes" || arg === "--mode") options.modes = splitList(next());
    else if (arg === "--target") options.target = positive(next(), options.target);
    else if (arg === "--horizon-ms") options.horizonMs = positive(next(), options.horizonMs);
    else if (arg === "--generations") options.generations = Math.max(1, Math.floor(positive(next(), options.generations)));
    else if (arg === "--population") options.population = Math.max(2, Math.floor(positive(next(), options.population)));
    else if (arg === "--elite") options.elite = Math.max(1, Math.floor(positive(next(), options.elite)));
    else if (arg === "--refinement-rounds") options.refinementRounds = Math.max(0, Math.floor(Number(next()) || 0));
    else if (arg === "--refinement-horizon-multiplier") {
      options.refinementHorizonMultiplier = Math.max(1, positive(next(), options.refinementHorizonMultiplier));
    }
    else if (arg === "--seed") options.seed = Math.floor(Number(next()) || options.seed);
    else if (arg === "--min-improvement") options.minImprovement = Math.max(0, Number(next()) || 0);
    else if (arg === "--output") options.output = next();
    else if (arg === "--quiet") options.quiet = true;
    else if (arg === "--help" || arg === "-h") {
      process.stdout.write(`Usage: node scripts/learn-3d-proposals.mjs [options]

  --modes cube,t_cross       Catalog systems to train
  --target 80                Tile-count target
  --horizon-ms 1500          Per-episode wall-clock horizon
  --generations 3            Evolutionary generations
  --population 12            Proposal programs per generation
  --elite 3                  Parents retained per generation
  --refinement-rounds 4      Reuse and extend the winning patch
  --refinement-horizon-multiplier 2
                             Multiply the learning horizon after each round
  --seed 17                  Reproducible tie/mutation seed
  --min-improvement 0.03     Required curve-score improvement over baseline
  --output path.json         Save learned proposal records
  --quiet                    Suppress per-episode progress
`);
      process.exit(0);
    } else throw new Error(`Unknown option: ${arg}`);
  }
  return options;
}

function episodeConfig(modeKey, options, {
  program = null,
  randomSeed
} = {}) {
  return {
    mode_key: modeKey,
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
    time_limit_ms: options.horizonMs,
    safety_max_tiles: Math.max(options.target, 200),
    ui_yield_interval_ms: Math.max(250, options.horizonMs)
  };
}

async function runEpisode(modeKey, options, {
  program = null,
  randomSeed
} = {}) {
  const started = performance.now();
  const points = [{ milliseconds: 0, tiles: 1 }];
  let bestTiles = 1;
  let bestSnapshot = null;
  let final = null;
  for await (const message of createTilingStream(
    episodeConfig(modeKey, options, { program, randomSeed }),
    tileSpecs,
    { stop: false }
  )) {
    const tiles = Number(message?.tile_count ?? message?.snapshot?.tile_count ?? 0);
    if (
      tiles > bestTiles
      && (message.type === "placement_delta" || message.type === "full_update" || message.type === "node_snapshot")
    ) {
      bestTiles = tiles;
      points.push({ milliseconds: performance.now() - started, tiles });
    }
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    if (Array.isArray(snapshot?.placements) && snapshot.placements.length > (bestSnapshot?.placements?.length ?? 0)) {
      bestSnapshot = snapshot;
    }
    if (message.type === "finished") final = message;
  }
  const elapsedMs = performance.now() - started;
  return {
    mode_key: modeKey,
    program: program ? normalizeProposalProgram(program) : null,
    random_seed: randomSeed,
    success: !!final?.success,
    best_tiles: Math.max(bestTiles, Number(final?.tile_count ?? 0)),
    elapsed_ms: elapsedMs,
    points,
    patch_snapshot: bestSnapshot,
    growth_isotropy: Number(final?.search_stats?.growth_isotropy ?? 0),
    backtracks: Number(final?.search_stats?.backtracks ?? 0),
    result_kind: final?.result_kind ?? null
  };
}

const median = values => {
  const ordered = [...values].sort((left, right) => left - right);
  return ordered[Math.floor(ordered.length / 2)] ?? 0;
};

function aggregateEpisodes(episodes, options, program = null) {
  const scores = episodes.map(episode => program
    ? scoreProposalEvaluation({ ...episode, program }, {
        horizonMs: options.horizonMs,
        targetTiles: options.target
      })
    : growthCurveArea(episode.points, {
        horizonMs: options.horizonMs,
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

async function evaluateProgram(modeKey, options, program, seedOffset = 0) {
  const episodes = [];
  for (let replicate = 0; replicate < 2; replicate++) {
    episodes.push(await runEpisode(modeKey, options, {
      program,
      randomSeed: options.seed + seedOffset + replicate * 104729
    }));
  }
  return aggregateEpisodes(episodes, options, program);
}

async function trainMode(modeKey, options) {
  if (!tileSpecs.TILING_REGISTRY[modeKey]) throw new Error(`Unknown catalog mode: ${modeKey}`);
  const baselineEpisodes = [];
  for (let replicate = 0; replicate < 3; replicate++) {
    baselineEpisodes.push(await runEpisode(modeKey, options, {
      randomSeed: options.seed + replicate * 104729
    }));
  }
  const baseline = aggregateEpisodes(baselineEpisodes, options);
  if (!options.quiet) {
    process.stderr.write(
      `${modeKey}: baseline ${baseline.best_tiles} tiles, score ${baseline.score.toFixed(4)}\n`
    );
  }

  let population = createInitialProposalPopulation({
    tileKey: modeKey,
    populationSize: options.population,
    seed: options.seed
  });
  const history = [];
  let winner = null;
  for (let generation = 0; generation < options.generations; generation++) {
    const evaluations = [];
    for (let index = 0; index < population.length; index++) {
      const program = population[index];
      const evaluation = await evaluateProgram(
        modeKey,
        options,
        program,
        generation * 1000003 + index * 8191
      );
      evaluations.push(evaluation);
      if (!winner || evaluation.score > winner.score) winner = evaluation;
      if (!options.quiet) {
        process.stderr.write(
          `${modeKey}: g${generation} ${index + 1}/${population.length} `
          + `${evaluation.best_tiles} tiles, score ${evaluation.score.toFixed(4)}\n`
        );
      }
    }
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

  const patchEpisode = [...winner.episodes].sort((left, right) =>
    (right.patch_snapshot?.placements?.length ?? 0) - (left.patch_snapshot?.placements?.length ?? 0)
    || left.elapsed_ms - right.elapsed_ms
  )[0];
  let learnedProgram = proposalProgramFromPatchSnapshot(
    { mode_key: modeKey, polycube_lattice: "z3" },
    patchEpisode?.patch_snapshot,
    winner.program
  ) ?? winner.program;
  const refinement = [];
  for (let round = 0; round < options.refinementRounds; round++) {
    const refinementOptions = {
      ...options,
      horizonMs: options.horizonMs * (options.refinementHorizonMultiplier ** (round + 1))
    };
    const episode = await runEpisode(modeKey, refinementOptions, {
      program: learnedProgram,
      randomSeed: options.seed + 7000001 + round * 131071
    });
    const priorPatchTiles = learnedProgram.patch.length;
    if ((episode.patch_snapshot?.placements?.length ?? 0) > priorPatchTiles) {
      learnedProgram = proposalProgramFromPatchSnapshot(
        { mode_key: modeKey, polycube_lattice: "z3" },
        episode.patch_snapshot,
        learnedProgram
      );
    }
    refinement.push({
      round,
      horizon_ms: refinementOptions.horizonMs,
      prior_patch_tiles: priorPatchTiles,
      patch_tiles: learnedProgram.patch.length,
      best_tiles: episode.best_tiles,
      success: episode.success
    });
    if (!options.quiet) {
      process.stderr.write(
        `${modeKey}: refinement ${round + 1}/${options.refinementRounds} `
        + `${learnedProgram.patch.length} patch tiles\n`
      );
    }
    if (learnedProgram.patch.length >= options.target) break;
  }
  let learnedEvaluation = await evaluateProgram(modeKey, options, learnedProgram, 12000017);
  const validationEpisode = [...learnedEvaluation.episodes].sort((left, right) =>
    (right.patch_snapshot?.placements?.length ?? 0) - (left.patch_snapshot?.placements?.length ?? 0)
    || left.elapsed_ms - right.elapsed_ms
  )[0];
  if ((validationEpisode?.patch_snapshot?.placements?.length ?? 0) > learnedProgram.patch.length) {
    learnedProgram = proposalProgramFromPatchSnapshot(
      { mode_key: modeKey, polycube_lattice: "z3" },
      validationEpisode.patch_snapshot,
      learnedProgram
    );
    learnedEvaluation = await evaluateProgram(modeKey, options, learnedProgram, 14000029);
  }
  const improvement = baseline.score > 0
    ? (learnedEvaluation.score - baseline.score) / baseline.score
    : Infinity;
  const accepted = learnedEvaluation.best_tiles >= baseline.best_tiles
    && improvement >= options.minImprovement;
  return {
    mode_key: modeKey,
    system: tileSpecs.TILING_REGISTRY[modeKey].name,
    accepted,
    improvement,
    baseline: {
      score: baseline.score,
      best_tiles: baseline.best_tiles,
      elapsed_ms: baseline.elapsed_ms,
      growth_isotropy: baseline.growth_isotropy
    },
    learned: {
      score: learnedEvaluation.score,
      best_tiles: learnedEvaluation.best_tiles,
      elapsed_ms: learnedEvaluation.elapsed_ms,
      growth_isotropy: learnedEvaluation.growth_isotropy,
      program: learnedProgram
    },
    history,
    refinement
  };
}

async function main() {
  const options = readArgs(process.argv.slice(2));
  const started = performance.now();
  const results = [];
  for (const modeKey of options.modes) results.push(await trainMode(modeKey, options));
  const report = {
    type: "proposal_learning_report",
    version: 1,
    generated_at: new Date().toISOString(),
    training_ms: performance.now() - started,
    options,
    accepted: results.filter(result => result.accepted).length,
    results
  };
  const json = JSON.stringify(report, null, 2);
  if (options.output) {
    const output = resolve(options.output);
    mkdirSync(dirname(output), { recursive: true });
    writeFileSync(output, `${json}\n`);
  } else {
    process.stdout.write(`${json}\n`);
  }
}

main().catch(error => {
  console.error(error?.stack ?? String(error));
  process.exit(1);
});
