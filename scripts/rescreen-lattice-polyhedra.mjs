#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  classifyLatticeCandidateScreen,
  LATTICE_POLYHEDRON_CENSUS_POOL
} from "../assets/lattice-polyhedron-survivors.js";

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
const only = new Set((args.get("ids") ?? "").split(",").filter(Boolean));
const candidatesFile = args.get("candidates-file") ?? null;
const outputFile = args.get("output-file") ?? null;
const candidatesDocument = candidatesFile
  ? JSON.parse(await readFile(candidatesFile, "utf8"))
  : null;
const candidatePool = candidatesDocument
  ? (candidatesDocument.survivors ?? candidatesDocument.candidates ?? candidatesDocument)
  : LATTICE_POLYHEDRON_CENSUS_POOL;
if (!Array.isArray(candidatePool)) throw new Error("Candidate input must be an array or contain a survivors/candidates array");
const pool = only.size
  ? candidatePool.filter(candidate => only.has(candidate.id))
  : candidatePool;
const timeMs = numberArg("time-ms", 10000);
const periodicMax = numberArg("periodic-max", 6);
const isohedralTarget = numberArg("isohedral-target", 24);
const displayTarget = numberArg("display-target", isohedralTarget);
const translationalMoveOrder = args.get("translational-move-order") ?? "balanced";
const skipIsohedral = args.get("skip-isohedral") === "true";
const skipTranslational = args.get("skip-translational") === "true";

const baseConfig = candidate => ({
  mode_key: "cube",
  custom_system: {
    name: `Census ${candidate.id}`,
    figure_refs: [],
    polycubes: [],
    polyhedra: [{ name: `Candidate ${candidate.id}`, vertices: candidate.vertices }],
    polycube_lattice: "z3"
  },
  polycube_lattice: "z3",
  criterion: "count",
  exhaustive: true,
  include_mirrors: false,
  snapshot_every: 0,
  placement_details: false,
  face_order: "mrv",
  agent_exhaustive: true,
  branch_cap: null,
  candidate_cap: null,
  node_limit: 500000,
  time_limit_ms: timeMs,
  ui_yield_interval_ms: 1000000,
  template_preflight: true
});

async function run(candidate, strategy) {
  const config = {
    ...baseConfig(candidate),
    criterion: "count",
    target_val: displayTarget,
    tiling_strategy: strategy,
    move_order: strategy === "isohedral" ? "isohedral" : translationalMoveOrder,
    periodic_patch_max_tiles: periodicMax,
    isohedral_search_horizon_tiles: isohedralTarget
  };
  const checks = [];
  let finished = null;
  let largestPatch = 0;
  let maxFrontierPoints = 0;
  let maxCandidateCount = 0;
  const started = performance.now();
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    largestPatch = Math.max(largestPatch, snapshot?.tile_count ?? snapshot?.placements?.length ?? 0);
    maxFrontierPoints = Math.max(maxFrontierPoints, snapshot?.frontier_stats?.point_count ?? 0);
    maxCandidateCount = Math.max(maxCandidateCount, snapshot?.frontier_stats?.candidate_count ?? 0);
    if (message.type === "translational_check") {
      checks.push({ size: message.patch_size, certified: message.certified });
    }
    if (message.type === "finished") finished = message;
  }
  largestPatch = Math.max(largestPatch, finished?.search_stats?.max_live_tiles ?? 0);
  return {
    strategy,
    outcome: finished?.result_kind ?? "missing_result",
    success: !!finished?.success,
    certified: !!finished?.tiling_evidence?.certified && finished?.can_tile === true,
    provenImpossible: !!finished?.tiling_evidence?.certified && finished?.can_tile === false,
    canTile: finished?.can_tile ?? null,
    certificate: finished?.tiling_evidence ?? null,
    incomplete: !!finished?.search_incomplete,
    tiles: finished?.tile_count ?? 0,
    largestPatch,
    maxFrontierPoints,
    maxCandidateCount,
    checks,
    milliseconds: Math.round(performance.now() - started),
    stats: finished?.search_stats ?? null
  };
}

const rows = [];
for (const candidate of pool) {
  const translational = skipTranslational ? null : await run(candidate, "translational");
  const isohedral = translational?.certified || translational?.provenImpossible || skipIsohedral
    ? null
    : await run(candidate, "isohedral");
  const classification = classifyLatticeCandidateScreen({ translational, isohedral });
  const row = {
    id: candidate.id,
    vertices: candidate.vertices,
    classification,
    translational,
    isohedral
  };
  rows.push(row);
  if (!outputFile) process.stdout.write(`${JSON.stringify(row)}\n`);
  else process.stderr.write(`${candidate.id}: ${classification}\n`);
}
if (outputFile) await writeFile(outputFile, `${JSON.stringify({
  schemaVersion: 1,
  kind: "lattice_polyhedron_easy_lane_screen",
  generatedAt: new Date().toISOString(),
  configuration: { candidatesFile, timeMs, periodicMax, isohedralTarget, displayTarget },
  rows
}, null, 2)}\n`);
