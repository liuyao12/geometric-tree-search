#!/usr/bin/env node

import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { growthCurveArea } from "../apps/3d-lattice-tiler/proposal-learner.js";
import {
  runProposalEpisode,
  trainProposalProgram
} from "../apps/3d-lattice-tiler/proposal-training.js";

const valueArg = (name, fallback) => {
  const prefix = `--${name}=`;
  const argument = process.argv.slice(2).find(item => item.startsWith(prefix));
  return argument ? argument.slice(prefix.length) : fallback;
};
const numberArg = (name, fallback) => {
  const value = Number(valueArg(name, fallback));
  return Number.isFinite(value) ? value : fallback;
};
const modeKeys = String(valueArg(
  "modes",
  "cube,hex_prism,trunc_oct,tetragonal_disphenoid,gyrobifastigium,rhombic,elongated_dod,t_cross"
)).split(",").map(value => value.trim()).filter(Boolean);
const target = Math.max(2, Math.floor(numberArg("target", 40)));
const horizonMs = Math.max(50, numberArg("horizon-ms", 500));
const generations = Math.max(1, Math.floor(numberArg("generations", 2)));
const population = Math.max(2, Math.floor(numberArg("population", 8)));
const seed = Math.floor(numberArg("seed", 17));

const baseConfig = modeKey => ({
  mode_key: modeKey,
  criterion: "count",
  target_val: target,
  include_mirrors: false,
  snapshot_every: 0,
  face_order: "coverage",
  branch_cap: null,
  candidate_cap: null,
  node_limit: null,
  time_limit_ms: horizonMs,
  safety_max_tiles: Math.max(target, 200),
  ui_yield_interval_ms: Math.max(250, horizonMs)
});

async function runStrategy(modeKey, strategy) {
  const config = {
    ...baseConfig(modeKey),
    tiling_strategy: strategy,
    move_order: strategy === "isohedral" ? "isohedral" : "balanced",
    agent_exhaustive: strategy !== "isohedral",
    greedy_no_backtrack: false,
    template_preflight: true,
    periodic_preflight: true,
    periodic_patch_unbounded: strategy === "translational",
    periodic_patch_max_tiles: strategy === "translational" ? null : 4
  };
  const started = performance.now();
  const points = [{ milliseconds: 0, tiles: 1 }];
  let bestTiles = 1;
  let final = null;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    const tiles = Number(message?.tile_count ?? message?.snapshot?.tile_count ?? 0);
    if (tiles > bestTiles) {
      bestTiles = tiles;
      points.push({ milliseconds: performance.now() - started, tiles });
    }
    if (message.type === "finished") final = message;
  }
  return {
    strategy,
    success: !!final?.success,
    best_tiles: Math.max(bestTiles, Number(final?.tile_count ?? 0)),
    elapsed_ms: performance.now() - started,
    growth_isotropy: Number(final?.search_stats?.growth_isotropy ?? 0),
    points
  };
}

const scoreEpisode = episode => growthCurveArea(episode.points, {
  horizonMs,
  targetTiles: target
});

const results = [];
for (const modeKey of modeKeys) {
  if (!tileSpecs.TILING_REGISTRY[modeKey]) throw new Error(`Unknown catalog mode: ${modeKey}`);
  const training = await trainProposalProgram(baseConfig(modeKey), {
    target,
    horizon_ms: horizonMs,
    generations,
    population,
    elite: Math.min(3, population),
    seed,
    min_improvement: 0,
    baseline_replicates: 1,
    proposal_replicates: 1
  });
  const learned = await runProposalEpisode(baseConfig(modeKey), {
    target,
    horizon_ms: horizonMs
  }, {
    program: training.learned.program,
    randomSeed: seed + 99991
  });
  const translational = await runStrategy(modeKey, "translational");
  const isohedral = await runStrategy(modeKey, "isohedral");
  const learnedScore = scoreEpisode(learned);
  const baselines = [translational, isohedral];
  const bestBaseline = baselines.reduce(
    (best, episode) => scoreEpisode(episode) > scoreEpisode(best) ? episode : best,
    baselines[0]
  );
  const bestBaselineScore = scoreEpisode(bestBaseline);
  const row = {
    mode_key: modeKey,
    system: tileSpecs.TILING_REGISTRY[modeKey].name,
    learned: {
      tiles: learned.best_tiles,
      score: learnedScore,
      milliseconds: learned.elapsed_ms,
      isotropy: learned.growth_isotropy,
      sequence_size: training.learned.program.patch_size,
      patch_tiles: training.learned.program.patch.length,
      replayed_tiles: learned.proposal_patch_tiles_replayed,
      replay_conflicts: learned.proposal_patch_conflicts
    },
    translational: {
      tiles: translational.best_tiles,
      score: scoreEpisode(translational),
      milliseconds: translational.elapsed_ms
    },
    isohedral: {
      tiles: isohedral.best_tiles,
      score: scoreEpisode(isohedral),
      milliseconds: isohedral.elapsed_ms
    },
    best_human_baseline: bestBaseline.strategy,
    baseline_reaches_target: bestBaseline.best_tiles >= target,
    learner_reaches_target: learned.best_tiles >= target,
    ratio: bestBaselineScore > 0 ? learnedScore / bestBaselineScore : 1,
    matches_or_beats: learnedScore >= bestBaselineScore,
    competitive_target: bestBaseline.best_tiles >= target
      && learned.best_tiles >= target
      && learnedScore >= bestBaselineScore
  };
  results.push(row);
  process.stderr.write(
    `${modeKey}: learner ${learned.best_tiles}/${learnedScore.toFixed(3)} `
    + `vs ${bestBaseline.strategy} ${bestBaseline.best_tiles}/${bestBaselineScore.toFixed(3)} `
    + `(${row.ratio.toFixed(2)}x, replay ${learned.proposal_patch_tiles_replayed})\n`
  );
}

const report = {
  type: "proposal_catalog_benchmark",
  version: 1,
  target,
  horizon_ms: horizonMs,
  generations,
  population,
  matched_or_beaten: results.filter(result => result.matches_or_beats).length,
  total: results.length,
  portion: results.filter(result => result.matches_or_beats).length / Math.max(1, results.length),
  target_eligible: results.filter(result => result.baseline_reaches_target).length,
  competitive_targets: results.filter(result => result.competitive_target).length,
  competitive_portion: results.filter(result => result.baseline_reaches_target).length
    ? results.filter(result => result.competitive_target).length
      / results.filter(result => result.baseline_reaches_target).length
    : 0,
  median_ratio: [...results].sort((left, right) => left.ratio - right.ratio)[Math.floor(results.length / 2)]?.ratio ?? 0,
  results
};
console.log(JSON.stringify(report, null, 2));
