#!/usr/bin/env node

import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  LATTICE_POLYHEDRON_CENSUS_POOL,
  LATTICE_POLYHEDRON_SURVIVORS
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
const output = args.get("output") ?? "json";
const target = Math.max(2, Math.floor(numberArg("target", 24)));
const timeMs = Math.max(50, Math.floor(numberArg("time-ms", 1000)));
const exactTimeMs = Math.max(timeMs, Math.floor(numberArg("exact-time-ms", 3000)));
const isohedralHorizon = Math.max(2, Math.floor(numberArg("isohedral-horizon", 24)));
const periodicMax = Math.max(1, Math.floor(numberArg("periodic-max", 4)));
const requestedIds = new Set((args.get("ids") ?? "").split(",").filter(Boolean));
const includeSpecial = args.get("special-controls") !== "false";

const censusById = new Map(LATTICE_POLYHEDRON_CENSUS_POOL.map(candidate => [candidate.id, candidate]));
const defaultIds = [
  "8_2480",
  "10_27010",
  ...LATTICE_POLYHEDRON_SURVIVORS.map(candidate => candidate.id)
];
const censusCases = (requestedIds.size ? [...requestedIds] : defaultIds)
  .map(id => censusById.get(id))
  .filter(Boolean)
  .map(candidate => ({
    id: candidate.id,
    family: "census",
    expected: candidate.screening.status === "inconclusive"
      ? "unresolved"
      : candidate.screening.certificate,
    vertices: candidate.vertices,
    lanes: candidate.screening.certificate === "translational"
      ? ["translational", "free_range"]
      : candidate.screening.certificate === "isohedral_periodic_quotient"
        ? ["isohedral", "free_range"]
        : ["translational", "isohedral", "free_range", "free_range_no_brainer"]
  }));
const specialCases = includeSpecial ? [
  { id: "corner_tetra", family: "control", expected: "certified_non_tiler", lanes: ["free_range"] },
  { id: "scd_conway", family: "control", expected: "known_aperiodic_construction", lanes: ["free_range"] }
] : [];
const cases = [...censusCases, ...specialCases];

const customSystem = benchmarkCase => benchmarkCase.family === "census" ? {
  name: `Candidate benchmark ${benchmarkCase.id}`,
  figure_refs: [],
  polycubes: [],
  polyhedra: [{ name: `Candidate ${benchmarkCase.id}`, vertices: benchmarkCase.vertices }],
  polycube_lattice: "z3"
} : null;

const configFor = (benchmarkCase, lane) => ({
  mode_key: benchmarkCase.family === "control" ? benchmarkCase.id : "cube",
  custom_system: customSystem(benchmarkCase),
  polycube_lattice: "z3",
  criterion: "count",
  target_val: lane === "isohedral" ? Math.max(target, 500) : target,
  tiling_strategy: lane.startsWith("free_range") ? "free_range" : lane,
  move_order: lane === "isohedral"
    ? "isohedral"
    : lane === "free_range_no_brainer"
      ? "no_brainer"
      : "balanced",
  face_order: "mrv",
  exhaustive: true,
  agent_exhaustive: true,
  include_mirrors: false,
  template_preflight: !lane.startsWith("free_range"),
  periodic_patch_max_tiles: periodicMax,
  periodic_patch_unbounded: false,
  isohedral_search_horizon_tiles: isohedralHorizon,
  snapshot_every: 1,
  placement_details: false,
  branch_cap: null,
  candidate_cap: null,
  node_limit: 500000,
  time_limit_ms: lane.startsWith("free_range") ? timeMs : exactTimeMs,
  ui_yield_interval_ms: 1000000
});

async function runLane(benchmarkCase, lane) {
  const config = configFor(benchmarkCase, lane);
  const started = performance.now();
  let final = null;
  let largestPatch = 0;
  let maxFrontierPoints = 0;
  let maxCandidateCount = 0;
  let checkedPatchSize = 0;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    largestPatch = Math.max(largestPatch, snapshot?.tile_count ?? snapshot?.placements?.length ?? 0);
    maxFrontierPoints = Math.max(maxFrontierPoints, snapshot?.frontier_stats?.point_count ?? 0);
    maxCandidateCount = Math.max(maxCandidateCount, snapshot?.frontier_stats?.candidate_count ?? 0);
    if (message.type === "translational_check") checkedPatchSize = message.patch_size;
    if (message.type === "finished") final = message;
  }
  const stats = final?.search_stats ?? {};
  largestPatch = Math.max(largestPatch, stats.max_live_tiles ?? 0);
  return {
    case: benchmarkCase.id,
    family: benchmarkCase.family,
    expected: benchmarkCase.expected,
    lane,
    resultKind: final?.result_kind ?? "missing_result",
    success: !!final?.success,
    canTile: final?.can_tile ?? null,
    certified: !!final?.tiling_evidence?.certified,
    certificateKind: final?.tiling_evidence?.certificate_kind
      ?? final?.tiling_evidence?.kind
      ?? null,
    certificatePatchSize: final?.tiling_evidence?.patch_size ?? null,
    searchIncomplete: !!final?.search_incomplete,
    elapsedMs: Math.round(performance.now() - started),
    largestPatch,
    maxFrontierPoints,
    maxCandidateCount,
    checkedPatchSize,
    visitedNodes: stats.visited_nodes ?? 0,
    backtracks: stats.backtracks ?? 0,
    maxDepth: stats.max_depth ?? 0,
    moveOrder: stats.move_order ?? null,
    quotientAttempts: stats.isohedral_certificate_attempts ?? 0,
    duplicateQuotientStatesSkipped: stats.isohedral_certificate_duplicate_states_skipped ?? 0,
    periodicMotifNodes: stats.periodic_motif_nodes ?? 0
  };
}

const rows = [];
for (const benchmarkCase of cases) {
  for (const lane of benchmarkCase.lanes) {
    const row = await runLane(benchmarkCase, lane);
    rows.push(row);
    if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "result", ...row })}\n`);
  }
}

const rowFor = (id, lane) => rows.find(row => row.case === id && row.lane === lane);
const preferredFreeRangePolicy = id => {
  const balanced = rowFor(id, "free_range");
  const noBrainer = rowFor(id, "free_range_no_brainer");
  if (!balanced || !noBrainer) return null;
  if (balanced.largestPatch !== noBrainer.largestPatch) {
    return balanced.largestPatch > noBrainer.largestPatch ? "balanced" : "no_brainer";
  }
  if (balanced.success !== noBrainer.success) return balanced.success ? "balanced" : "no_brainer";
  if (balanced.visitedNodes !== noBrainer.visitedNodes) {
    return balanced.visitedNodes < noBrainer.visitedNodes ? "balanced" : "no_brainer";
  }
  return balanced.backtracks <= noBrainer.backtracks ? "balanced" : "no_brainer";
};
const freeRangePortfolio = id => {
  const balanced = rowFor(id, "free_range");
  const noBrainer = rowFor(id, "free_range_no_brainer");
  if (!balanced || !noBrainer) return null;
  const policies = [
    { policy: "balanced", row: balanced },
    { policy: "no_brainer", row: noBrainer }
  ];
  const policiesReachingTarget = policies
    .filter(({ row }) => row.largestPatch >= target)
    .map(({ policy }) => policy);
  return {
    target,
    outcome: policiesReachingTarget.length === policies.length
      ? "robust_target_reached"
      : policiesReachingTarget.length
        ? "policy_sensitive_target_reached"
        : "bounded_below_target",
    policiesReachingTarget,
    robustLargestPatch: Math.min(...policies.map(({ row }) => row.largestPatch)),
    bestLargestPatch: Math.max(...policies.map(({ row }) => row.largestPatch)),
    preferredPolicy: preferredFreeRangePolicy(id),
    combinedVisitedNodes: policies.reduce((sum, { row }) => sum + row.visitedNodes, 0),
    combinedBacktracks: policies.reduce((sum, { row }) => sum + row.backtracks, 0)
  };
};
const controlGates = {
  translationalControl: cases.some(item => item.id === "8_2480")
    ? rowFor("8_2480", "translational")?.resultKind === "certified_tiling"
    : true,
  isohedralControl: cases.some(item => item.id === "10_27010")
    ? rowFor("10_27010", "isohedral")?.certificatePatchSize === 24
    : true,
  nonTilerControl: includeSpecial
    ? rowFor("corner_tetra", "free_range")?.canTile === false
    : true,
  aperiodicControl: includeSpecial
    ? rowFor("scd_conway", "free_range")?.resultKind === "known_aperiodic_construction"
    : true
};
const unresolved = LATTICE_POLYHEDRON_SURVIVORS
  .map(candidate => candidate.id)
  .filter(id => !requestedIds.size || requestedIds.has(id))
  .map(id => ({
    id,
    translational: rowFor(id, "translational") ?? null,
    isohedral: rowFor(id, "isohedral") ?? null,
    freeRange: rowFor(id, "free_range") ?? null,
    freeRangeNoBrainer: rowFor(id, "free_range_no_brainer") ?? null,
    preferredFreeRangePolicy: preferredFreeRangePolicy(id),
    freeRangePortfolio: freeRangePortfolio(id)
  }));
const summary = {
  schemaVersion: 2,
  configuration: { target, timeMs, exactTimeMs, isohedralHorizon, periodicMax },
  cases: cases.map(({ id, family, expected }) => ({ id, family, expected })),
  rows,
  controls: controlGates,
  controlGatesPassed: Object.values(controlGates).every(Boolean),
  unresolved
};
if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "summary", ...summary })}\n`);
else process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
if (!summary.controlGatesPassed) process.exitCode = 2;
