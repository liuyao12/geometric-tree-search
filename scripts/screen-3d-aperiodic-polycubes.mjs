#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  canonicalPolycubeKey,
  enumeratePolycubes,
  isChiralPolycube,
  voxelsFromPolycubeKey
} from "../assets/polycube-enumerator.js";
import { searchPolycubeCorona } from "../assets/polycube-corona-search.js";
import { findPolycubeBoxTiling } from "../assets/polycube-box-tiler.js";
import { findPolycubePeriodicTiling } from "../assets/polycube-periodic-tiler.js";

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
const requestedVoxels = requestedKey ? voxelsFromPolycubeKey(requestedKey) : null;
const inputReport = args.get("input-report");
const inputClassification = args.get("input-classification") ?? "unresolved";
const reportCandidates = inputReport
  ? readFileSync(inputReport, "utf8").split(/\r?\n/).filter(Boolean)
      .map(line => JSON.parse(line))
      .filter(record => record.type === "candidate" && record.classification === inputClassification)
      .map(({ id, key, voxels }) => ({ id, key, voxels }))
  : null;
const size = requestedVoxels?.length ?? reportCandidates?.[0]?.voxels?.length
  ?? Math.max(1, Math.floor(numberArg("size", 5)));
const includeReflections = booleanArg("include-reflections", false);
const maxCandidates = Math.max(1, Math.floor(numberArg("max-candidates", Infinity)));
const startIndex = Math.max(0, Math.floor(numberArg("start-index", 0)));
const periodicMaxTiles = Math.max(1, Math.min(16, Math.floor(numberArg("periodic-max-tiles", 4))));
const boxMaxTiles = Math.max(1, Math.floor(numberArg("box-max-tiles", 4)));
const boxTimeMs = Math.max(1, numberArg("box-time-ms", 100));
const periodicTimeMs = Math.max(1, numberArg("periodic-time-ms", 1000));
const generalPeriodic = booleanArg("general-periodic", true);
const isohedralTarget = Math.max(2, Math.floor(numberArg("isohedral-target", 12)));
const isohedralTimeMs = Math.max(1, numberArg("isohedral-time-ms", 500));
const obstructionLayer = Math.max(1, Math.floor(numberArg("obstruction-layer", 1)));
const obstructionTimeMs = Math.max(1, numberArg("obstruction-time-ms", 1000));
const nodeLimit = Math.max(1, Math.floor(numberArg("nodes", 20000)));

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
  return searchPolycubeCorona(candidate.voxels, {
    includeReflections,
    layers: obstructionLayer,
    nodeLimit,
    timeLimitMs: obstructionTimeMs
  });
}

const candidates = requestedVoxels
  ? [{
      id: `custom-${size}`,
      key: canonicalPolycubeKey(requestedVoxels, { includeReflections }),
      voxels: requestedVoxels
    }]
  : (reportCandidates ?? enumeratePolycubes(size, { includeReflections }))
      .slice(startIndex, startIndex + maxCandidates);
const counts = { periodic: 0, non_tiler: 0, isohedral_lead: 0, unresolved: 0 };
const witnessCounts = { torus: 0, box: 0, isohedral_easy: 0, general_periodic: 0 };
const startedAt = performance.now();

process.stdout.write(`${JSON.stringify({
  type: "screen_start",
  size,
  candidates: candidates.length,
  equivalence: includeReflections ? "rotations_and_reflections" : "proper_rotations",
  periodic_max_tiles: periodicMaxTiles,
  obstruction_layer: obstructionLayer
})}\n`);

for (let index = 0; index < candidates.length; index++) {
  const candidate = candidates[index];
  const candidateStartedAt = performance.now();
  const torus = findPolycubePeriodicTiling(candidate.voxels, {
    includeReflections,
    maxCopies: periodicMaxTiles,
    nodeLimit,
    timeLimitMs: periodicTimeMs
  });
  const box = torus.certified ? null : findPolycubeBoxTiling(candidate.voxels, {
    includeReflections,
    maxCopies: boxMaxTiles,
    nodeLimit,
    timeLimitMs: boxTimeMs
  });
  const easy = torus.certified ? torus : box;
  const periodic = easy.certified || !generalPeriodic ? null : await periodicScreen(candidate);
  let classification = "unresolved";
  let isohedral = null;
  let obstruction = null;

  if (easy.certified || (periodic?.tiling_evidence?.certified && periodic?.can_tile === true)) {
    classification = "periodic";
  } else {
    isohedral = await isohedralLeadScreen(candidate);
    obstruction = await obstructionScreen(candidate);
    if (obstruction?.certified_non_tiler) {
      classification = "non_tiler";
    } else if (isohedral?.success) {
      classification = "isohedral_lead";
    }
  }
  if (torus.certified) witnessCounts.torus += 1;
  if (box?.certified) witnessCounts.box += 1;
  if (easy.isohedral?.certified) witnessCounts.isohedral_easy += 1;
  if (periodic?.tiling_evidence?.certified && periodic?.can_tile === true) witnessCounts.general_periodic += 1;
  counts[classification] += 1;

  process.stdout.write(`${JSON.stringify({
    type: "candidate",
    index: index + 1,
    total: candidates.length,
    id: candidate.id,
    key: candidate.key,
    voxels: candidate.voxels,
    chiral: isChiralPolycube(candidate.voxels),
    classification,
    easy_witness: easy.certified ? {
      kind: easy.kind,
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
      stopped_by: torus.stopped_by ?? null,
      copies: torus.copies ?? null,
      nodes: torus.nodes ?? null,
      hnf_visited: torus.hnf_visited ?? null,
      milliseconds: torus.milliseconds
    },
    isohedral: isohedral ? {
      patch_found: !!isohedral.success,
      tiles: isohedral.tile_count,
      incomplete: isohedral.search_incomplete
    } : null,
    obstruction: obstruction ? {
      certified: obstruction.certified_non_tiler,
      layer: obstructionLayer,
      incomplete: !!obstruction.stopped_by,
      stopped_by: obstruction.stopped_by,
      nodes: obstruction.nodes,
      target_cells: obstruction.target_cells ?? null,
      placements_considered: obstruction.placements_considered ?? null,
      memo_hits: obstruction.memo_hits ?? null
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
  milliseconds: Math.round(performance.now() - startedAt),
  warning: "Unresolved means only that these bounded screens found neither a proof of periodic tiling nor a finite non-tiling obstruction; it is not evidence of aperiodicity."
})}\n`);
