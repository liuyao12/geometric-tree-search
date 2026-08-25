#!/usr/bin/env node

import { writeFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { LATTICE_POLYHEDRON_CENSUS_POOL } from "../assets/lattice-polyhedron-survivors.js";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const split = argument.indexOf("=");
  return split < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, split), argument.slice(split + 1)];
}));
const list = (name, fallback) => (args.get(name) ?? fallback).split(",").filter(Boolean);
const numbers = (name, fallback) => list(name, fallback).map(Number).filter(Number.isFinite);
const ids = list("ids", "p9-42947,p10-054782,p10-055695,p10-290795,p10-346304,10_45033");
const shells = numbers("shells", "2").map(value => Math.max(1, Math.floor(value)));
const seeds = numbers("seeds", "1").map(value => Math.max(1, Math.floor(value)));
const timeMs = Math.max(100, Number(args.get("time-ms") ?? 10000));
const nodeLimit = Math.max(1, Number(args.get("node-limit") ?? 1000000));
const outputFile = args.get("output-file") ?? null;
const requestedProfiles = new Set(list("profiles", ""));

const profiles = [
  { id: "binned_mean", policy: "cold_geometry" },
  { id: "linucb_a0", policy: "cold_linucb", alpha: 0 },
  { id: "linucb_a005", policy: "cold_linucb", alpha: 0.05 },
  { id: "linucb_a01", policy: "cold_linucb", alpha: 0.1 },
  { id: "linucb_a025", policy: "cold_linucb", alpha: 0.25 },
  { id: "linucb_a05", policy: "cold_linucb", alpha: 0.5 },
  { id: "linucb_a1", policy: "cold_linucb", alpha: 1 },
  { id: "linucb_a2", policy: "cold_linucb", alpha: 2 }
].filter(profile => !requestedProfiles.size || requestedProfiles.has(profile.id));
const census = new Map(LATTICE_POLYHEDRON_CENSUS_POOL.map(candidate => [candidate.id, candidate]));
const polycubes = new Map(POLYCUBE_GCTS_CANDIDATES.map(candidate => [candidate.id, candidate]));
const cases = ids.map(id => census.get(id) ?? polycubes.get(id)).filter(Boolean);
if (!cases.length || !profiles.length) throw new Error("No matching cases or RL profiles");

const customSystem = candidate => ({
  name: `Anonymous RL benchmark ${candidate.id}`,
  figure_refs: [],
  polycubes: candidate.voxels
    ? [{ name: "Anonymous polycube", voxels: candidate.voxels }]
    : [],
  polyhedra: candidate.vertices
    ? [{ name: "Anonymous lattice polyhedron", vertices: candidate.vertices }]
    : [],
  polycube_lattice: "z3"
});

async function run(candidate, shell, seed, profile) {
  const config = {
    mode_key: "cube",
    custom_system: customSystem(candidate),
    polycube_lattice: "z3",
    criterion: "shell",
    target_val: shell,
    tiling_strategy: "free_range",
    move_order: "rl",
    face_order: "mrv",
    complete_lattice_point_branching: true,
    gcts_failure_marking: false,
    forced_move_layer_lag_cap: 0,
    generic_complete_shell_enumeration: true,
    generic_failure_memo: true,
    generic_failure_memo_symmetry: "rigid",
    exhaustive: true,
    agent_exhaustive: true,
    agent_policy: profile.policy,
    agent_ucb_alpha: profile.alpha,
    agent_linucb_ridge: 1,
    learned_layer_macro: false,
    known_periodic_template: null,
    initial_patch: null,
    proposal_program: null,
    template_preflight: false,
    periodic_preflight: false,
    random_seed: seed,
    seeded_tie_breaks: true,
    node_limit: nodeLimit,
    time_limit_ms: timeMs,
    snapshot_every: 1,
    placement_details: false,
    ui_yield_interval_ms: 1000000
  };
  const started = performance.now();
  let final = null;
  let maximumCompletedShell = 0;
  let maximumLiveTiles = 1;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    maximumCompletedShell = Math.max(
      maximumCompletedShell,
      snapshot?.frontier_stats?.complete_shell_depth ?? 0
    );
    maximumLiveTiles = Math.max(
      maximumLiveTiles,
      snapshot?.tile_count ?? 0,
      message.search_stats?.max_live_tiles ?? 0
    );
    if (message.type === "finished") final = message;
  }
  const stats = final?.search_stats ?? {};
  return {
    case: candidate.id,
    targetShell: shell,
    seed,
    profile: profile.id,
    policy: profile.policy,
    alpha: profile.alpha ?? null,
    success: maximumCompletedShell >= shell,
    resultKind: final?.result_kind ?? null,
    searchIncomplete: !!final?.search_incomplete,
    elapsedMs: Math.round(performance.now() - started),
    maximumCompletedShell,
    maximumLiveTiles: Math.max(maximumLiveTiles, stats.max_live_tiles ?? 0),
    visitedNodes: stats.visited_nodes ?? 0,
    branchChoices: stats.branch_choices_visited ?? 0,
    backtracks: stats.backtracks ?? 0,
    scoreCalls: stats.agent_score_calls ?? 0,
    scoreTimeMs: stats.agent_score_time_ms ?? 0,
    trainingUpdates: stats.agent_training_updates ?? 0,
    trainingTimeMs: stats.agent_training_time_ms ?? 0,
    learningTimeMs: (stats.agent_score_time_ms ?? 0) + (stats.agent_training_time_ms ?? 0),
    learnedTags: stats.agent_learned_tags ?? 0,
    modelDimension: stats.agent_model_dimension ?? 0,
    modelWeights: stats.agent_model_weight_count ?? 0,
    modelParameters: stats.agent_model_parameter_count ?? 0,
    modelPayloadBytes: stats.agent_model_payload_bytes ?? 0,
    evidenceKind: final?.tiling_evidence?.kind ?? null,
    motifTiles: final?.tiling_evidence?.patch_size ?? null,
    terminationReason: stats.termination_reason ?? null
  };
}

const rows = [];
for (const shell of shells) {
  for (const candidate of cases) {
    for (const profile of profiles) {
      for (const seed of seeds) rows.push(await run(candidate, shell, seed, profile));
    }
  }
}
const median = values => {
  const sorted = values.slice().sort((left, right) => left - right);
  return sorted[Math.floor(sorted.length / 2)] ?? 0;
};
const summaries = profiles.map(profile => {
  const selected = rows.filter(row => row.profile === profile.id);
  return {
    profile: profile.id,
    policy: profile.policy,
    alpha: profile.alpha ?? null,
    runs: selected.length,
    successes: selected.filter(row => row.success).length,
    certifiedNoTilings: selected.filter(row => row.resultKind === "no_tiling").length,
    medianCompletedShell: median(selected.map(row => row.maximumCompletedShell)),
    medianMaximumLiveTiles: median(selected.map(row => row.maximumLiveTiles)),
    medianVisitedNodes: median(selected.map(row => row.visitedNodes)),
    medianElapsedMs: median(selected.map(row => row.elapsedMs)),
    medianModelPayloadBytes: median(selected.map(row => row.modelPayloadBytes)),
    maxModelPayloadBytes: Math.max(0, ...selected.map(row => row.modelPayloadBytes)),
    totalLearningTimeMs: selected.reduce((sum, row) => sum + row.learningTimeMs, 0),
    totalElapsedMs: selected.reduce((sum, row) => sum + row.elapsedMs, 0)
  };
});
const report = {
  schemaVersion: 1,
  protocol: "cold anonymous geometry; exact shell search; one tile per action; no motif macros, templates, initial patches, proposals, or prior-run state; all inference and training charged to elapsed time",
  configuration: { ids: cases.map(candidate => candidate.id), shells, seeds, timeMs, nodeLimit },
  profiles,
  summaries,
  rows
};
const serialized = `${JSON.stringify(report, null, 2)}\n`;
if (outputFile) await writeFile(outputFile, serialized);
else process.stdout.write(serialized);
