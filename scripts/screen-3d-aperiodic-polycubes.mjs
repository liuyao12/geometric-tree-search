#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  canonicalPolycubeKey,
  enumeratePolycubes,
  isChiralPolycube,
  voxelsFromPolycubeKey
} from "../assets/polycube-enumerator.js";
import {
  searchPolycubeCorona,
  verifyPolycubeCoronaPatch
} from "../assets/polycube-corona-search.js";
import { findPolycubeBoxTiling } from "../assets/polycube-box-tiler.js";
import {
  findPolycubePeriodicTiling,
  polycubePeriodicResumeHnfIndex,
  verifyPolycubePeriodicCertificate
} from "../assets/polycube-periodic-tiler.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const numberArg = (name, fallback) => {
  const value = Number(args.get(name));
  return Number.isFinite(value) ? value : fallback;
};
const booleanArg = (name, fallback) => {
  if (!args.has(name)) return fallback;
  return !["0", "false", "no"].includes(String(args.get(name)).toLowerCase());
};

const requestedKey = args.get("key");
const requestedCandidateId = args.get("candidate-id");
const requestedVoxels = requestedKey ? voxelsFromPolycubeKey(requestedKey) : null;
const inputReports = String(args.get("input-report") ?? "")
  .split(",")
  .map(value => value.trim())
  .filter(Boolean);
const obstructionInitialNogoodReports = String(args.get("obstruction-initial-nogood-report") ?? "")
  .split(",")
  .map(value => value.trim())
  .filter(Boolean);
const obstructionPreferredCoronaReports = String(args.get("obstruction-preferred-corona-report") ?? "")
  .split(",")
  .map(value => value.trim())
  .filter(Boolean);
const obstructionNogoodsByIdentity = new Map();
const obstructionPreferredPlacementsByIdentity = new Map();
for (const report of obstructionInitialNogoodReports) {
  for (const line of readFileSync(report, "utf8").split(/\r?\n/).filter(Boolean)) {
    const record = JSON.parse(line);
    if (record.type !== "candidate" || !Array.isArray(record.obstruction?.nogood_clause_keys)) continue;
    for (const identity of [record.id ? `id:${record.id}` : null, record.key ? `key:${record.key}` : null].filter(Boolean)) {
      if (!obstructionNogoodsByIdentity.has(identity)) obstructionNogoodsByIdentity.set(identity, new Map());
      const clauses = obstructionNogoodsByIdentity.get(identity);
      for (const clause of record.obstruction.nogood_clause_keys) {
        if (!Array.isArray(clause)) continue;
        const normalized = [...new Set(clause.map(String))].sort();
        clauses.set(normalized.join("|"), normalized);
      }
    }
  }
}
for (const report of obstructionPreferredCoronaReports) {
  for (const line of readFileSync(report, "utf8").split(/\r?\n/).filter(Boolean)) {
    const record = JSON.parse(line);
    if (record.type !== "candidate" || !Array.isArray(record.obstruction?.corona)) continue;
    const placementKeys = record.obstruction.corona
      .filter(placement => Array.isArray(placement?.cells))
      .map(placement => placement.cells.map(cell => cell.join(",")).sort().join(";"));
    for (const identity of [record.id ? `id:${record.id}` : null, record.key ? `key:${record.key}` : null].filter(Boolean)) {
      if (!obstructionPreferredPlacementsByIdentity.has(identity)) {
        obstructionPreferredPlacementsByIdentity.set(identity, new Set());
      }
      for (const placementKey of placementKeys) {
        obstructionPreferredPlacementsByIdentity.get(identity).add(placementKey);
      }
    }
  }
}
const obstructionInitialNogoodsFor = candidate => {
  const clauses = new Map();
  for (const identity of [`id:${candidate.id}`, `key:${candidate.key}`]) {
    for (const [clauseKey, clause] of obstructionNogoodsByIdentity.get(identity) ?? []) {
      clauses.set(clauseKey, clause);
    }
  }
  return [...clauses.values()];
};
const obstructionPreferredPlacementsFor = candidate => {
  const placements = new Set();
  for (const identity of [`id:${candidate.id}`, `key:${candidate.key}`]) {
    for (const placementKey of obstructionPreferredPlacementsByIdentity.get(identity) ?? []) {
      placements.add(placementKey);
    }
  }
  return [...placements];
};
const inputClassification = args.get("input-classification") ?? "unresolved";
const inputStoppedBy = args.get("input-stopped-by");
const reportCandidates = inputReports.length
  ? inputReports.flatMap(inputReport => readFileSync(inputReport, "utf8").split(/\r?\n/).filter(Boolean)
      .map(line => JSON.parse(line))
      .filter(record => record.type === "candidate" && record.classification === inputClassification)
      .filter(record => !inputStoppedBy
        || (record.periodic_fast?.stopped_by ?? "exhausted") === inputStoppedBy)
      .map(({ id, key, voxels, periodic_fast }) => ({
        id,
        key,
        voxels,
        input_periodic_fast: periodic_fast ?? null
      })))
  : null;
if (inputReports.length && !reportCandidates.length && !booleanArg("allow-empty-input", false)) {
  throw new Error(`No candidates matched the requested input reports and filters (${inputReports.join(", ")})`);
}
const size = requestedVoxels?.length ?? reportCandidates?.[0]?.voxels?.length
  ?? Math.max(1, Math.floor(numberArg("size", 5)));
const includeReflections = booleanArg("include-reflections", false);
const reportChirality = booleanArg("report-chirality", true);
const maxCandidates = Math.max(1, Math.floor(numberArg("max-candidates", Infinity)));
const startIndex = Math.max(0, Math.floor(numberArg("start-index", 0)));
const periodicMaxTiles = Math.max(1, Math.min(16, Math.floor(numberArg("periodic-max-tiles", 4))));
const periodicMinTiles = Math.max(1, Math.min(periodicMaxTiles,
  Math.floor(numberArg("periodic-min-tiles", 1))));
const boxMaxTiles = Math.max(1, Math.floor(numberArg("box-max-tiles", 4)));
const boxTimeMs = Math.max(1, numberArg("box-time-ms", 100));
const boxScreen = booleanArg("box-screen", true);
const periodicTimeMs = Math.max(1, numberArg("periodic-time-ms", 1000));
const periodicScreenEnabled = booleanArg("periodic-screen", true);
const periodicExactCoverBackend = String(args.get("periodic-exact-cover-backend") ?? "scan").toLowerCase();
if (!["scan", "dlx"].includes(periodicExactCoverBackend)) {
  throw new Error("--periodic-exact-cover-backend must be scan or dlx");
}
const periodicLinearPrefilter = booleanArg("periodic-linear-prefilter", false);
const periodicBudgetClock = String(args.get("periodic-budget-clock") ?? "wall").toLowerCase();
if (!["wall", "cpu"].includes(periodicBudgetClock)) {
  throw new Error("--periodic-budget-clock must be wall or cpu");
}
const resumeActiveHnf = booleanArg("resume-active-hnf", false);
if (resumeActiveHnf && periodicMinTiles !== periodicMaxTiles) {
  throw new Error("--resume-active-hnf requires equal periodic minimum and maximum tile counts");
}
const explicitPeriodicHnfStart = args.has("periodic-hnf-start-index");
const explicitPeriodicHnfEnd = args.has("periodic-hnf-end-index");
const periodicHnfStartIndex = Math.max(0,
  Math.floor(numberArg("periodic-hnf-start-index", 0)));
const periodicHnfEndIndex = explicitPeriodicHnfEnd
  ? Math.max(0, Math.floor(numberArg("periodic-hnf-end-index", 0)))
  : null;
if ((explicitPeriodicHnfStart || explicitPeriodicHnfEnd)
  && periodicMinTiles !== periodicMaxTiles) {
  throw new Error("explicit periodic HNF ranges require equal periodic minimum and maximum tile counts");
}
if (resumeActiveHnf && (explicitPeriodicHnfStart || explicitPeriodicHnfEnd)) {
  throw new Error("--resume-active-hnf cannot be combined with an explicit periodic HNF range");
}
if (periodicHnfEndIndex != null && periodicHnfEndIndex < periodicHnfStartIndex) {
  throw new Error("--periodic-hnf-end-index must be at least --periodic-hnf-start-index");
}
const generalPeriodic = booleanArg("general-periodic", true);
const isohedralTarget = Math.max(2, Math.floor(numberArg("isohedral-target", 12)));
const isohedralTimeMs = Math.max(1, numberArg("isohedral-time-ms", 500));
const isohedralScreenEnabled = booleanArg("isohedral-screen", true);
const engineBudgetClock = String(args.get("engine-budget-clock") ?? "wall").toLowerCase();
if (!["wall", "cpu"].includes(engineBudgetClock)) {
  throw new Error("--engine-budget-clock must be wall or cpu");
}
const obstructionLayer = Math.max(1, Math.floor(numberArg("obstruction-layer", 1)));
const obstructionTimeMs = Math.max(1, numberArg("obstruction-time-ms", 1000));
const obstructionBudgetClock = String(args.get("obstruction-budget-clock") ?? "wall").toLowerCase();
if (!["wall", "cpu"].includes(obstructionBudgetClock)) {
  throw new Error("--obstruction-budget-clock must be wall or cpu");
}
const obstructionNogoods = booleanArg("obstruction-nogoods", true);
const obstructionConflictBackjumping = booleanArg("obstruction-conflict-backjumping", true);
const obstructionSymmetryNogoods = booleanArg("obstruction-symmetry-nogoods", false);
const obstructionReturnNogoods = booleanArg("obstruction-return-nogoods", false);
const obstructionReturnCorona = booleanArg("obstruction-return-corona", false);
const obstructionNogoodLimit = Math.max(1, Math.floor(numberArg("obstruction-nogood-limit", 50_000)));
const obstructionSeed = Math.floor(numberArg("obstruction-seed", 0));
const nodeLimit = Math.max(1, Math.floor(numberArg("nodes", 20000)));
const stopAfter = String(args.get("stop-after") ?? "all").toLowerCase();
if (!["periodic", "isohedral", "all"].includes(stopAfter)) {
  throw new Error("--stop-after must be periodic, isohedral, or all");
}

const baseConfig = (candidate, suffix) => ({
  mode_key: "custom",
  custom_system: {
    name: `${candidate.id} ${suffix}`,
    polycubes: [{ name: candidate.id, voxels: candidate.voxels }],
    polycube_lattice: "z3"
  },
  polycube_lattice: "z3",
  include_mirrors: includeReflections,
  snapshot_every: 1000000,
  placement_details: false,
  branch_details: false,
  candidate_cap: null,
  branch_cap: null,
  node_limit: nodeLimit,
  safety_max_tiles: 200,
  ui_yield_interval_ms: 1000000,
  time_budget_clock: engineBudgetClock,
  online_failure_marking: false
});

async function solve(config) {
  let finished = null;
  for await (const message of createTilingStream(config, tileSpecs)) {
    if (message.type === "finished") finished = message;
  }
  return finished;
}

async function periodicScreen(candidate) {
  return solve({
    ...baseConfig(candidate, "periodic screen"),
    criterion: "count",
    target_val: 8,
    tiling_strategy: "translational",
    template_preflight: true,
    periodic_preflight: true,
    periodic_patch_max_tiles: periodicMaxTiles,
    periodic_patch_hard_max: periodicMaxTiles,
    periodic_template_max_volume: Math.max(64, size * periodicMaxTiles),
    periodic_hnf_candidate_limit: 50000,
    time_limit_ms: periodicTimeMs
  });
}

async function isohedralLeadScreen(candidate) {
  return solve({
    ...baseConfig(candidate, "isohedral lead"),
    criterion: "count",
    target_val: isohedralTarget,
    tiling_strategy: "isohedral",
    exhaustive: false,
    template_preflight: true,
    periodic_preflight: false,
    isohedral_preflight_max_steps: isohedralTarget - 1,
    move_order: "isohedral",
    face_order: "mrv",
    time_limit_ms: isohedralTimeMs
  });
}

async function obstructionScreen(candidate) {
  const initialNogoodPlacementKeys = obstructionInitialNogoodsFor(candidate);
  const preferredPlacementKeys = obstructionPreferredPlacementsFor(candidate);
  return searchPolycubeCorona(candidate.voxels, {
    includeReflections,
    layers: obstructionLayer,
    nodeLimit,
    timeLimitMs: obstructionTimeMs,
    timeBudgetMode: obstructionBudgetClock,
    nogoods: obstructionNogoods,
    conflictBackjumping: obstructionConflictBackjumping,
    symmetryNogoods: obstructionSymmetryNogoods,
    initialNogoodPlacementKeys,
    preferredPlacementKeys,
    returnNogoods: obstructionReturnNogoods,
    nogoodLimit: obstructionNogoodLimit,
    seed: obstructionSeed
  });
}

const candidates = requestedVoxels
  ? [{
      id: requestedCandidateId ?? `custom-${size}`,
      key: canonicalPolycubeKey(requestedVoxels, { includeReflections }),
      voxels: requestedVoxels
    }]
  : (reportCandidates ?? enumeratePolycubes(size, { includeReflections }))
      .slice(startIndex, startIndex + maxCandidates);
const counts = { periodic: 0, non_tiler: 0, isohedral_lead: 0, unresolved: 0 };
const witnessCounts = { torus: 0, box: 0, isohedral_easy: 0, general_periodic: 0, isohedral_lane: 0 };
const startedAt = performance.now();

process.stdout.write(`${JSON.stringify({
  type: "screen_start",
  size,
  candidates: candidates.length,
  equivalence: includeReflections ? "rotations_and_reflections" : "proper_rotations",
  report_chirality: reportChirality,
  input_reports: inputReports,
  input_stopped_by: inputStoppedBy ?? null,
  periodic_max_tiles: periodicMaxTiles,
  periodic_min_tiles: periodicMinTiles,
  periodic_screen: periodicScreenEnabled,
  periodic_budget_clock: periodicBudgetClock,
  periodic_exact_cover_backend: periodicExactCoverBackend,
  periodic_linear_prefilter: periodicLinearPrefilter,
  periodic_time_ms: periodicTimeMs,
  node_limit: nodeLimit,
  resume_active_hnf: resumeActiveHnf,
  periodic_hnf_start_index: explicitPeriodicHnfStart ? periodicHnfStartIndex : null,
  periodic_hnf_end_index: periodicHnfEndIndex,
  box_screen: boxScreen,
  box_time_ms: boxTimeMs,
  general_periodic: generalPeriodic,
  isohedral_screen: isohedralScreenEnabled,
  isohedral_time_ms: isohedralTimeMs,
  engine_budget_clock: engineBudgetClock,
  obstruction_layer: obstructionLayer,
  obstruction_time_ms: obstructionTimeMs,
  obstruction_budget_clock: obstructionBudgetClock,
  obstruction_conflict_backjumping: obstructionConflictBackjumping,
  obstruction_symmetry_nogoods: obstructionSymmetryNogoods,
  obstruction_initial_nogood_reports: obstructionInitialNogoodReports,
  obstruction_preferred_corona_reports: obstructionPreferredCoronaReports,
  obstruction_return_nogoods: obstructionReturnNogoods,
  obstruction_return_corona: obstructionReturnCorona,
  obstruction_seed: obstructionSeed,
  stop_after: stopAfter
})}\n`);

for (let index = 0; index < candidates.length; index++) {
  const candidate = candidates[index];
  const candidateStartedAt = performance.now();
  const torus = periodicScreenEnabled
    ? findPolycubePeriodicTiling(candidate.voxels, {
        includeReflections,
        minCopies: periodicMinTiles,
        maxCopies: periodicMaxTiles,
        nodeLimit,
        timeLimitMs: periodicTimeMs,
        timeBudgetMode: periodicBudgetClock,
        exactCoverBackend: periodicExactCoverBackend,
        linearAlgebraPrefilter: periodicLinearPrefilter,
        hnfStartIndex: resumeActiveHnf
          ? polycubePeriodicResumeHnfIndex(candidate.input_periodic_fast)
          : periodicHnfStartIndex,
        hnfEndIndex: periodicHnfEndIndex,
        assumeHnfPrefixExhausted: resumeActiveHnf
      })
    : {
        kind: "periodic_screen_skipped",
        certified: false,
        can_tile: null,
        stopped_by: null,
        nodes: 0,
        hnf_visited: 0,
        milliseconds: 0
      };
  const box = torus.certified || !boxScreen ? null : findPolycubeBoxTiling(candidate.voxels, {
    includeReflections,
    maxCopies: boxMaxTiles,
    nodeLimit,
    timeLimitMs: boxTimeMs
  });
  const easy = torus.certified ? torus : box ?? torus;
  const easyVerification = easy.certified
    ? verifyPolycubePeriodicCertificate(candidate.voxels, easy, { includeReflections })
    : null;
  if (easy.certified && !easyVerification?.verified) {
    throw new Error(`Independent periodic-certificate verification failed for ${candidate.id}: ${easyVerification?.reason ?? "unknown"}`);
  }
  const easyCertified = !!easyVerification?.verified;
  const periodic = easyCertified || !generalPeriodic ? null : await periodicScreen(candidate);
  let classification = "unresolved";
  let isohedral = null;
  let obstruction = null;

  if (easyCertified || (periodic?.tiling_evidence?.certified && periodic?.can_tile === true)) {
    classification = "periodic";
  } else if (stopAfter !== "periodic") {
    if (isohedralScreenEnabled) isohedral = await isohedralLeadScreen(candidate);
    if (isohedral?.tiling_evidence?.certified && isohedral?.can_tile === true) {
      classification = "periodic";
    } else {
      if (stopAfter === "all") obstruction = await obstructionScreen(candidate);
      if (obstruction?.success) {
        obstruction.verification = verifyPolycubeCoronaPatch(
          candidate.voxels,
          obstruction.corona,
          obstructionLayer,
          { includeReflections }
        );
        if (!obstruction.verification.verified) {
          throw new Error(`Independent corona verification failed for ${candidate.id}`);
        }
      }
      if (obstruction?.certified_non_tiler) {
        classification = "non_tiler";
      } else if (isohedral?.success) {
        classification = "isohedral_lead";
      }
    }
  }
  if (torus.certified && easyCertified) witnessCounts.torus += 1;
  if (box?.certified && easyCertified) witnessCounts.box += 1;
  if (easy.isohedral?.certified && easyCertified) witnessCounts.isohedral_easy += 1;
  if (periodic?.tiling_evidence?.certified && periodic?.can_tile === true) witnessCounts.general_periodic += 1;
  if (isohedral?.tiling_evidence?.certified && isohedral?.can_tile === true) witnessCounts.isohedral_lane += 1;
  counts[classification] += 1;

  process.stdout.write(`${JSON.stringify({
    type: "candidate",
    index: index + 1,
    total: candidates.length,
    id: candidate.id,
    key: candidate.key,
    voxels: candidate.voxels,
    chiral: reportChirality ? isChiralPolycube(candidate.voxels) : null,
    classification,
    easy_witness: easy.certified ? {
      kind: easy.kind,
      verified: easyCertified,
      copies: easy.copies,
      box: easy.box ?? null,
      period_vectors: easy.period_vectors,
      isohedral_certificate: easy.isohedral,
      nodes: easy.nodes ?? null,
      tests: easy.tests ?? null
    } : {
      kind: easy.kind,
      stopped_by: easy.stopped_by ?? null,
      nodes: easy.nodes ?? null,
      tests: torus.tests ?? null,
      hnf_visited: torus.hnf_visited ?? null
    },
    periodic: {
      result_kind: periodic?.result_kind ?? null,
      certificate: periodic?.tiling_evidence?.kind ?? null,
      motif_tiles: periodic?.tiling_evidence?.patch_size
        ?? periodic?.tiling_evidence?.motif?.length
        ?? null,
      incomplete: periodic?.search_incomplete ?? true
    },
    periodic_fast: {
      kind: torus.kind,
      certified: torus.certified,
      certificate_verified: torus.certified ? easyCertified : null,
      stopped_by: torus.stopped_by ?? null,
      copies: torus.copies ?? null,
      nodes: torus.nodes ?? null,
      hnf_visited: torus.hnf_visited ?? null,
      hnf_skipped: torus.hnf_skipped ?? null,
      active_hnf_index: torus.active_hnf_index ?? null,
      hnf_range_start: torus.hnf_range_start ?? null,
      hnf_range_end_exclusive: torus.hnf_range_end_exclusive ?? null,
      hnf_range_total: torus.hnf_range_total ?? null,
      hnf_range_exhausted: torus.hnf_range_exhausted ?? null,
      hnf_exhausted_by_copies: torus.hnf_exhausted_by_copies ?? null,
      linear_prefilter_rejections: torus.linear_prefilter_rejections ?? 0,
      milliseconds: torus.milliseconds
    },
    isohedral: isohedral ? {
      patch_found: !!isohedral.success,
      tiles: isohedral.tile_count,
      incomplete: isohedral.search_incomplete,
      certified: !!isohedral.tiling_evidence?.certified,
      certificate: isohedral.tiling_evidence?.kind ?? null,
      motif_tiles: isohedral.tiling_evidence?.patch_size ?? null
    } : null,
    obstruction: obstruction ? {
      certified: obstruction.certified_non_tiler,
      patch_verified: obstruction.success ? !!obstruction.verification?.verified : null,
      layer: obstructionLayer,
      seed: obstruction.seed ?? obstructionSeed,
      incomplete: !!obstruction.stopped_by,
      stopped_by: obstruction.stopped_by,
      nodes: obstruction.nodes,
      target_cells: obstruction.target_cells ?? null,
      placements_considered: obstruction.placements_considered ?? null,
      memo_hits: obstruction.memo_hits ?? null,
      nogood_clauses: obstruction.nogood_clauses ?? null,
      nogood_prunes: obstruction.nogood_prunes ?? null,
      nogood_average_size: obstruction.nogood_average_size ?? null,
      initial_nogood_clauses: obstruction.initial_nogood_clauses ?? null,
      preferred_placements_requested: obstruction.preferred_placements_requested ?? null,
      preferred_placements_matched: obstruction.preferred_placements_matched ?? null,
      nogood_clause_keys: obstructionReturnNogoods ? obstruction.nogood_clause_keys : null,
      corona: obstructionReturnCorona && obstruction.success ? obstruction.corona : null,
      corona_verification: obstructionReturnCorona && obstruction.success
        ? obstruction.verification
        : null,
      conflict_backjumps: obstruction.conflict_backjumps ?? null,
      symmetry_nogood_clauses: obstruction.symmetry_nogood_clauses ?? null,
      resolved_fixed_conflict_size: obstruction.resolved_fixed_conflict
        ?.fixed_placement_indices?.length ?? null
    } : null,
    milliseconds: Math.round(performance.now() - candidateStartedAt)
  })}\n`);
}

process.stdout.write(`${JSON.stringify({
  type: "screen_summary",
  size,
  candidates: candidates.length,
  counts,
  witness_counts: witnessCounts,
  stop_after: stopAfter,
  milliseconds: Math.round(performance.now() - startedAt),
  warning: "Unresolved means only that these bounded screens found neither a proof of periodic tiling nor a finite non-tiling obstruction; it is not evidence of aperiodicity."
})}\n`);
