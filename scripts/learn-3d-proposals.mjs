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
    greedy_no_backtrack: true,
    random_seed: randomSeed,
    template_preflight: false,
    periodic_preflight: false,
    snapshot_every: 0,
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

  const improvement = baseline.score > 0 ? (winner.score - baseline.score) / baseline.score : Infinity;
  const accepted = winner.best_tiles >= baseline.best_tiles && improvement >= options.minImprovement;
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
      score: winner.score,
      best_tiles: winner.best_tiles,
      elapsed_ms: winner.elapsed_ms,
      growth_isotropy: winner.growth_isotropy,
      program: winner.program
    },
    history
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
