#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const required = ["training-10", "training-25", "training-50", "holdout-10", "prior-training", "prior-holdout"];
for (const name of required) assert.ok(args.get(name), `--${name}=<report.json> is required`);
const readJson = async name => JSON.parse(await readFile(args.get(name), "utf8"));
const normalizeCapturedWitnesses = report => ({
  ...report,
  rows: report.rows.map(row => {
    const milestone = row.growthMilestones?.at(-1);
    const maxLiveTiles = row.maxLiveTiles ?? row.largestPatch;
    if (!milestone) return {
      ...row,
      maxLiveTiles,
      uncapturedMaxLiveTiles: Math.max(0, maxLiveTiles - row.largestPatch)
    };
    assert.ok(maxLiveTiles >= milestone.patchSize);
    return {
      ...row,
      largestPatch: milestone.patchSize,
      witnessHash: milestone.witnessHash,
      maxLiveTiles,
      uncapturedMaxLiveTiles: maxLiveTiles - milestone.patchSize
    };
  })
});
const [training10Raw, training25Raw, training50Raw, holdout10Raw, priorTraining, priorHoldout] = await Promise.all(
  required.map(readJson)
);
const training10 = normalizeCapturedWitnesses(training10Raw);
const training25 = normalizeCapturedWitnesses(training25Raw);
const training50 = normalizeCapturedWitnesses(training50Raw);
const holdout10 = normalizeCapturedWitnesses(holdout10Raw);
const trainingReports = new Map([[10, training10], [25, training25], [50, training50]]);
for (const [threshold, report] of trainingReports) {
  assert.equal(report.schemaVersion, 16);
  assert.equal(report.configuration.geometricNogood, true);
  assert.equal(report.configuration.geometricNogoodActivationFailures, 0);
  assert.equal(report.configuration.geometricNogoodStagnationFailures, threshold);
  assert.deepEqual(report.configuration.seeds, [1, 2, 3]);
  assert.equal(report.rows.length, 12);
  assert.ok(report.rows.every(row =>
    row.geometricNogoodActivationStagnationFailureStates === threshold
    && row.geometricNogoodGrowthMarkTiles >= 1
    && row.growthMilestones.at(-1).patchSize === row.largestPatch
  ));
}
assert.equal(holdout10.schemaVersion, 16);
assert.equal(holdout10.configuration.geometricNogoodStagnationFailures, 10);
assert.deepEqual(holdout10.configuration.seeds, [4, 5, 6, 7, 8]);
assert.equal(holdout10.rows.length, 20);

const keyOf = row => `${row.case}:${row.seed}`;
const byKey = report => new Map(report.rows.map(row => [keyOf(row), row]));
const trainingRows = new Map([...trainingReports].map(([threshold, report]) => [threshold, byKey(report)]));
const holdoutRows = byKey(holdout10);
const compactMilestones = row => row.growthMilestones.map(milestone => ({
  patch_size: milestone.patchSize,
  visited_nodes: milestone.visitedNodes,
  backtracks: milestone.backtracks,
  elapsed_ms: milestone.elapsedMs,
  witness_hash: milestone.witnessHash
}));
const compact = row => ({
  largest_patch: row.largestPatch,
  max_live_tiles: row.maxLiveTiles,
  uncaptured_max_live_tiles: row.uncapturedMaxLiveTiles,
  witness_hash: row.witnessHash,
  visited_nodes: row.visitedNodes,
  backtracks: row.backtracks,
  elapsed_ms: row.elapsedMs,
  termination_reason: row.terminationReason,
  activated: row.geometricNogoodActivated,
  activation_failures_since_growth: row.geometricNogoodFailuresSinceGrowth,
  activation_growth_mark_tiles: row.geometricNogoodGrowthMarkTiles,
  nogood_failure_states: row.geometricNogoodFailureStates,
  nogood_clauses: row.geometricNogoodClauses,
  nogood_prunes: row.geometricNogoodPrunes,
  growth_milestones: compactMilestones(row)
});

const priorTrainingPaths = new Map(priorTraining.paths.map(path => [`${path.id}:${path.seed}`, path]));
const priorHoldoutPaths = new Map(priorHoldout.search_paths.map(path => [`${path.id}:${path.seed}`, path]));
for (const rows of trainingRows.values()) assert.deepEqual([...rows.keys()], [...priorTrainingPaths.keys()]);
assert.deepEqual([...holdoutRows.keys()], [...priorHoldoutPaths.keys()]);
const trainingPaths = [...priorTrainingPaths].map(([key, prior]) => ({
  id: prior.id,
  seed: prior.seed,
  fixed_delayed_25: prior.delayed[25],
  stagnation: Object.fromEntries([...trainingRows].map(([threshold, rows]) => [threshold, compact(rows.get(key))]))
}));
const holdoutPaths = [...priorHoldoutPaths].map(([key, prior]) => ({
  id: prior.id,
  seed: prior.seed,
  fixed_delayed_25: prior.delayed_25,
  stagnation_10: compact(holdoutRows.get(key))
}));

const compare = (paths, valueFor) => ({
  better_than_fixed_delayed_25: paths.filter(path => valueFor(path) > path.fixed_delayed_25.largest_patch).length,
  equal_to_fixed_delayed_25: paths.filter(path => valueFor(path) === path.fixed_delayed_25.largest_patch).length,
  worse_than_fixed_delayed_25: paths.filter(path => valueFor(path) < path.fixed_delayed_25.largest_patch).length,
  target_hits: paths.filter(path => valueFor(path) >= 40).length,
  fixed_delayed_25_target_hits: paths.filter(path => path.fixed_delayed_25.largest_patch >= 40).length
});
const trainingSummary = [...trainingReports.keys()].map(threshold => ({
  stagnation_failure_states: threshold,
  ...compare(trainingPaths, path => path.stagnation[threshold].largest_patch)
}));
const holdoutSummary = compare(holdoutPaths, path => path.stagnation_10.largest_patch);
assert.deepEqual(trainingSummary, [
  {
    stagnation_failure_states: 10,
    better_than_fixed_delayed_25: 0,
    equal_to_fixed_delayed_25: 11,
    worse_than_fixed_delayed_25: 1,
    target_hits: 2,
    fixed_delayed_25_target_hits: 2
  },
  {
    stagnation_failure_states: 25,
    better_than_fixed_delayed_25: 0,
    equal_to_fixed_delayed_25: 11,
    worse_than_fixed_delayed_25: 1,
    target_hits: 1,
    fixed_delayed_25_target_hits: 2
  },
  {
    stagnation_failure_states: 50,
    better_than_fixed_delayed_25: 1,
    equal_to_fixed_delayed_25: 7,
    worse_than_fixed_delayed_25: 4,
    target_hits: 0,
    fixed_delayed_25_target_hits: 2
  }
]);
assert.deepEqual(holdoutSummary, {
  better_than_fixed_delayed_25: 0,
  equal_to_fixed_delayed_25: 16,
  worse_than_fixed_delayed_25: 4,
  target_hits: 1,
  fixed_delayed_25_target_hits: 2
});

const combinedStagnation10 = {
  better_than_fixed_delayed_25:
    trainingSummary[0].better_than_fixed_delayed_25 + holdoutSummary.better_than_fixed_delayed_25,
  equal_to_fixed_delayed_25:
    trainingSummary[0].equal_to_fixed_delayed_25 + holdoutSummary.equal_to_fixed_delayed_25,
  worse_than_fixed_delayed_25:
    trainingSummary[0].worse_than_fixed_delayed_25 + holdoutSummary.worse_than_fixed_delayed_25,
  target_hits: trainingSummary[0].target_hits + holdoutSummary.target_hits,
  fixed_delayed_25_target_hits:
    trainingSummary[0].fixed_delayed_25_target_hits + holdoutSummary.fixed_delayed_25_target_hits
};
const result = {
  schema_version: 1,
  screen_date: args.get("screen-date") ?? new Date().toISOString().slice(0, 10),
  engine_commit: args.get("engine-commit") ?? null,
  benchmark_schema_version: 16,
  prior_training_report: args.get("prior-training"),
  prior_holdout_report: args.get("prior-holdout"),
  protocol: {
    training_seeds: [1, 2, 3],
    holdout_seeds: [4, 5, 6, 7, 8],
    node_limit: training10.configuration.nodeLimit,
    target_tiles: training10.configuration.target,
    training_stagnation_failure_thresholds: [10, 25, 50],
    selected_holdout_threshold: 10,
    activation_rule: "one-way activation after N encoded failure states without increasing max_live_tiles",
    witness_accounting: "largest_patch and witness_hash identify the last captured placement snapshot; max_live_tiles retains any transient uncaptured engine peak"
  },
  training_paths: trainingPaths,
  holdout_paths: holdoutPaths,
  training_summary: trainingSummary,
  holdout_summary: holdoutSummary,
  summary: {
    training_paths_per_policy: trainingPaths.length,
    holdout_paths: holdoutPaths.length,
    combined_stagnation_10: combinedStagnation10,
    policy_decision: "reject_stagnation_gate_retain_fixed_delayed_25"
  },
  interpretation: [
    "Stagnation-10 is the least harmful training threshold but does not improve any training path over fixed delayed-25 and worsens one.",
    "On five unseen seeds, stagnation-10 improves zero paths, ties sixteen, worsens four, and loses one target hit.",
    "The stagnation gate remains a sound opt-in ablation because dormant gating preserves the baseline path exactly, but it is not promoted to the web proof lane.",
    "The lattice candidates served as discriminating algorithm benchmarks: a plausible adaptive policy was rejected by both training and holdout evidence."
  ]
};

const serialized = `${JSON.stringify(result, null, 2)}\n`;
if (args.get("output")) await writeFile(args.get("output"), serialized);
else process.stdout.write(serialized);
