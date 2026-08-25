#!/usr/bin/env node

import { writeFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { LATTICE_POLYHEDRON_CENSUS_POOL } from "../assets/lattice-polyhedron-survivors.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const split = argument.indexOf("=");
  return split < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, split), argument.slice(split + 1)];
}));
const numbers = (name, fallback) => (args.get(name) ?? fallback)
  .split(",")
  .map(Number)
  .filter(Number.isFinite);
const ids = (args.get("ids") ?? "10_16113,10_45026,10_45033,9_11683").split(",").filter(Boolean);
const layers = numbers("layers", "2,3").map(value => Math.max(1, Math.floor(value)));
const seeds = numbers("seeds", "1,2,3").map(value => Math.max(1, Math.floor(value)));
const timeMs = Math.max(50, Number(args.get("time-ms") ?? 5000));
const nodeLimit = Math.max(1, Number(args.get("node-limit") ?? 1000000));
const outputFile = args.get("output-file") ?? null;
const requestedProfiles = new Set((args.get("profiles") ?? "").split(",").filter(Boolean));

const PROFILES = [
  { id: "free_range", marking: false, moveOrder: "balanced", lag: 2, symmetry: "fixed", blockers: "first" },
  { id: "gcts_balanced_lag2", marking: true, moveOrder: "balanced", lag: 2, symmetry: "fixed", blockers: "first" },
  { id: "gcts_balanced_lag1", marking: true, moveOrder: "balanced", lag: 1, symmetry: "fixed", blockers: "first" },
  { id: "gcts_no_brainer_lag2", marking: true, moveOrder: "no_brainer", lag: 2, symmetry: "fixed", blockers: "first" },
  { id: "gcts_no_brainer_lag1", marking: true, moveOrder: "no_brainer", lag: 1, symmetry: "fixed", blockers: "first" },
  { id: "rl_lag2", marking: false, moveOrder: "rl", lag: 2, symmetry: "fixed", blockers: "first", agent: true },
  { id: "gcts_rl_lag2", marking: true, moveOrder: "rl", lag: 2, symmetry: "fixed", blockers: "first", agent: true },
  { id: "rl_macro_lag2", marking: false, moveOrder: "rl", lag: 2, symmetry: "fixed", blockers: "first", agent: true, macro: true },
  { id: "gcts_rl_macro_lag2", marking: true, moveOrder: "rl", lag: 2, symmetry: "fixed", blockers: "first", agent: true, macro: true },
  { id: "translational", marking: false, moveOrder: "periodic_agent", lag: 2, symmetry: "fixed", blockers: "first", strategy: "translational", templates: true, agent: true },
  { id: "isohedral", marking: false, moveOrder: "isohedral", lag: 2, symmetry: "fixed", blockers: "first", strategy: "isohedral", templates: true },
  { id: "gcts_rotations_lag2", marking: true, moveOrder: "balanced", lag: 2, symmetry: "rotations", blockers: "first" },
  { id: "gcts_all_blockers_lag2", marking: true, moveOrder: "balanced", lag: 2, symmetry: "fixed", blockers: "all" }
].filter(profile => !requestedProfiles.size || requestedProfiles.has(profile.id));

const census = new Map(LATTICE_POLYHEDRON_CENSUS_POOL.map(candidate => [candidate.id, candidate]));
const cases = ids.map(id => census.get(id)).filter(Boolean);
if (!cases.length) throw new Error("No matching lattice candidates");
if (!PROFILES.length) throw new Error("No matching profiles");

const customSystem = candidate => ({
  name: `Layer benchmark ${candidate.id}`,
  figure_refs: [],
  polycubes: [],
  polyhedra: [{ name: "Anonymous lattice polyhedron", vertices: candidate.vertices }],
  polycube_lattice: "z3"
});

async function run(candidate, layer, seed, profile) {
  const config = {
    mode_key: "cube",
    custom_system: customSystem(candidate),
    polycube_lattice: "z3",
    criterion: "layer",
    target_val: layer,
    tiling_strategy: profile.strategy ?? "free_range",
    move_order: profile.moveOrder,
    face_order: "mrv",
    complete_lattice_point_branching: true,
    gcts_failure_marking: profile.marking,
    gcts_marking_reach_multiplier: 1,
    gcts_marking_max_clauses: 20000,
    gcts_marking_max_context_tiles: 1000000,
    gcts_marking_activation_failures: 0,
    gcts_marking_symmetry: profile.symmetry,
    gcts_marking_index: true,
    gcts_marking_blocker_mode: profile.blockers,
    forced_move_layer_lag_cap: profile.lag,
    template_preflight: !!profile.templates,
    periodic_preflight: !!profile.templates,
    periodic_patch_unbounded: profile.strategy === "translational",
    periodic_motif_node_limit: profile.strategy === "translational" ? 2500 : null,
    known_periodic_template: null,
    proposal_program: null,
    initial_patch: null,
    greedy_no_backtrack: false,
    exhaustive: true,
    agent_exhaustive: true,
    agent_policy: profile.agent ? "cold_geometry" : null,
    learned_layer_macro: !!profile.macro,
    learned_layer_macro_max_motif_tiles: 8,
    learned_layer_macro_motif_node_limit: 2500,
    learned_layer_macro_discovery_time_ms: 5000,
    branch_cap: null,
    candidate_cap: null,
    node_limit: nodeLimit,
    random_seed: seed,
    seeded_tie_breaks: true,
    time_limit_ms: timeMs,
    snapshot_every: 1,
    placement_details: false,
    ui_yield_interval_ms: 1000000
  };
  const started = performance.now();
  let final = null;
  let maximumCompletedLayer = 0;
  let tilesAtMaximumLayer = 1;
  let maximumLiveTiles = 1;
  let maximumTranslationalPatchChecked = 0;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    const completedLayer = snapshot?.frontier_stats?.min_gen ?? 0;
    const tiles = snapshot?.tile_count ?? 0;
    if (completedLayer > maximumCompletedLayer) {
      maximumCompletedLayer = completedLayer;
      tilesAtMaximumLayer = tiles;
    } else if (completedLayer === maximumCompletedLayer) {
      tilesAtMaximumLayer = Math.max(tilesAtMaximumLayer, tiles);
    }
    maximumLiveTiles = Math.max(maximumLiveTiles, tiles, message.search_stats?.max_live_tiles ?? 0);
    if (message.type === "translational_check") {
      maximumTranslationalPatchChecked = Math.max(
        maximumTranslationalPatchChecked,
        Number(message.patch_size) || 0
      );
    }
    if (message.type === "finished") final = message;
  }
  const stats = final?.search_stats ?? {};
  const layerCompleted = maximumCompletedLayer >= layer;
  return {
    case: candidate.id,
    targetLayer: layer,
    seed,
    profile: profile.id,
    // A periodic certificate proves that the tile can continue forever, but
    // this curriculum scores the harder operational milestone: the requested
    // frontier generation was actually filled in the live patch.
    success: layerCompleted,
    layerCompleted,
    solverSuccess: !!final?.success,
    evidenceKind: final?.tiling_evidence?.kind ?? null,
    evidencePatchSize: final?.tiling_evidence?.patch_size ?? null,
    searchIncomplete: !!final?.search_incomplete,
    elapsedMs: Math.round(performance.now() - started),
    maximumCompletedLayer,
    tilesAtMaximumLayer,
    maximumLiveTiles: Math.max(maximumLiveTiles, stats.max_live_tiles ?? 0),
    visitedNodes: stats.visited_nodes ?? 0,
    periodicMotifNodes: stats.periodic_motif_nodes ?? 0,
    maximumTranslationalPatchChecked,
    periodicLastRejection: stats.periodic_certificate_last_rejection ?? null,
    branchChoices: stats.branch_choices_visited ?? 0,
    backtracks: stats.backtracks ?? 0,
    failedLeaves: stats.failed_leaves ?? 0,
    markingClauses: stats.marking_geometric_clauses ?? 0,
    markingPrunes: stats.marking_geometric_prunes ?? 0,
    markingChecks: stats.marking_clause_checks ?? 0,
    moveOrder: stats.move_order ?? null,
    generationLagCap: stats.generation_lag_cap ?? null,
    markingSymmetry: profile.symmetry,
    blockerMode: profile.blockers,
    agentPolicy: stats.agent_policy ?? null,
    agentObservations: stats.agent_observations ?? 0,
    agentLearnedTags: stats.agent_learned_tags ?? 0,
    macroAttempts: stats.learned_layer_macro_attempts ?? 0,
    macroSuccesses: stats.learned_layer_macro_successes ?? 0,
    macroTilesApplied: stats.learned_layer_macro_tiles_applied ?? 0,
    macroRollbacks: stats.learned_layer_macro_rollbacks ?? 0,
    macroPeriodicTemplates: stats.learned_layer_macro_periodic_templates ?? 0,
    terminationReason: stats.termination_reason ?? null
  };
}

const rows = [];
for (const layer of layers) {
  for (const candidate of cases) {
    for (const profile of PROFILES) {
      for (const seed of seeds) rows.push(await run(candidate, layer, seed, profile));
    }
  }
}

const median = values => {
  const sorted = values.slice().sort((left, right) => left - right);
  return sorted[Math.floor(sorted.length / 2)] ?? 0;
};
const summaries = [];
for (const layer of layers) {
  for (const profile of PROFILES) {
    const selected = rows.filter(row => row.targetLayer === layer && row.profile === profile.id);
    summaries.push({
      targetLayer: layer,
      profile: profile.id,
      runs: selected.length,
      successes: selected.filter(row => row.success).length,
      casesWithSuccess: [...new Set(selected.filter(row => row.success).map(row => row.case))].length,
      minimumCompletedLayer: Math.min(...selected.map(row => row.maximumCompletedLayer)),
      medianCompletedLayer: median(selected.map(row => row.maximumCompletedLayer)),
      medianMaximumLiveTiles: median(selected.map(row => row.maximumLiveTiles)),
      medianVisitedNodes: median(selected.map(row => row.visitedNodes)),
      totalMarkingPrunes: selected.reduce((sum, row) => sum + row.markingPrunes, 0)
    });
  }
}

const report = {
  schemaVersion: 1,
  protocol: "cold anonymous lattice geometry; no catalog templates, initial patches, proposals, or prior-run state",
  configuration: { ids: cases.map(candidate => candidate.id), layers, seeds, timeMs, nodeLimit },
  profiles: PROFILES,
  summaries,
  rows
};
const serialized = `${JSON.stringify(report, null, 2)}\n`;
if (outputFile) await writeFile(outputFile, serialized);
else process.stdout.write(serialized);
