#!/usr/bin/env node

import { createHash } from "node:crypto";
import { writeFile } from "node:fs/promises";
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
const outputFile = args.get("output-file") ?? null;
const target = Math.max(2, Math.floor(numberArg("target", 24)));
const timeMs = Math.max(50, Math.floor(numberArg("time-ms", 1000)));
const exactTimeMs = Math.max(timeMs, Math.floor(numberArg("exact-time-ms", 3000)));
const isohedralHorizon = Math.max(2, Math.floor(numberArg("isohedral-horizon", 24)));
const periodicMax = Math.max(1, Math.floor(numberArg("periodic-max", 4)));
const nodeLimit = Math.max(1, Math.floor(numberArg("node-limit", 500000)));
const failureMemo = args.get("failure-memo") !== "false";
const failureMemoSymmetry = args.get("failure-memo-symmetry") === "rigid" ? "rigid" : "fixed";
const failureMemoMaxStates = Math.max(0, Math.floor(numberArg("failure-memo-max-states", 200000)));
const geometricNogood = args.get("geometric-nogood") === "true";
const geometricNogoodMaxClauses = Math.max(0, Math.floor(numberArg("geometric-nogood-max-clauses", 20000)));
const geometricNogoodIndex = args.get("geometric-nogood-index") !== "false";
const geometricNogoodActivationFailures = Math.max(
  0,
  Math.floor(numberArg("geometric-nogood-activation-failures", 0))
);
const geometricNogoodStagnationFailures = Math.max(
  0,
  Math.floor(numberArg("geometric-nogood-stagnation-failures", 0))
);
const requestedFaceOrder = args.get("face-order");
const faceOrder = ["mrv", "pocket", "constrained", "coverage"].includes(requestedFaceOrder)
  ? requestedFaceOrder
  : "mrv";
const connectedPatchEnumeration = args.get("connected-patch-enumeration") !== "false";
const requestedUnbandedMoveOrder = args.get("unbanded-move-order");
const unbandedMoveOrder = [
  "balanced",
  "global",
  "no_brainer",
  "symmetric",
  "crystal",
  "isohedral",
  "periodic",
  "repeat",
  "layer"
].includes(requestedUnbandedMoveOrder)
  ? requestedUnbandedMoveOrder
  : connectedPatchEnumeration ? "global" : "balanced";
const genericPeriodicCertificate = args.get("generic-periodic-certificate") === "true";
const genericPeriodicCheckpoints = args.get("generic-periodic-checkpoints") === "true";
const genericPeriodicDistinctPatches = args.get("generic-periodic-distinct-patches") === "true";
const requestedGenericPeriodicSamplingPolicy = args.get("generic-periodic-sampling");
const genericPeriodicSamplingPolicy = ["spread", "hybrid"].includes(requestedGenericPeriodicSamplingPolicy)
  ? requestedGenericPeriodicSamplingPolicy
  : "prefix";
const genericPeriodicSamplingStride = Math.max(
  2,
  Math.floor(numberArg("generic-periodic-sampling-stride", 16))
);
const genericPeriodicSamplingPrefix = Math.max(
  1,
  Math.floor(numberArg("generic-periodic-sampling-prefix", 4))
);
const genericPeriodicMaxChecksPerSize = Math.max(
  1,
  Math.floor(numberArg("generic-periodic-max-checks-per-size", 4))
);
const genericPeriodicMaxTotalChecks = Math.max(
  1,
  Math.floor(numberArg("generic-periodic-max-total-checks", 160))
);
const genericPeriodicCheckpointTotalTimeMs = Math.max(
  1,
  Math.floor(numberArg("generic-periodic-checkpoint-total-time-ms", 10000))
);
const seededTies = args.get("seeded-ties") !== "false";
const genericPeriodicCertificateTimeMs = Math.max(
  1,
  Math.floor(numberArg("generic-periodic-certificate-time-ms", 5000))
);
const seeds = [...new Set((args.get("seeds") ?? "1,2,3")
  .split(",")
  .map(value => Math.floor(Number(value)))
  .filter(value => Number.isFinite(value) && value > 0))];
if (!seeds.length) seeds.push(1);
const requestedIds = new Set((args.get("ids") ?? "").split(",").filter(Boolean));
const requestedLanes = new Set((args.get("lanes") ?? "").split(",").filter(Boolean));
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
        : ["translational", "isohedral", "free_range", "free_range_no_brainer", "free_range_unbanded"]
  }));
const specialCases = includeSpecial ? [
  { id: "corner_tetra", family: "control", expected: "certified_non_tiler", lanes: ["free_range"] },
  { id: "scd_conway", family: "control", expected: "known_aperiodic_construction", lanes: ["free_range"] }
] : [];
const cases = [...censusCases, ...specialCases]
  .map(benchmarkCase => ({
    ...benchmarkCase,
    lanes: requestedLanes.size
      ? benchmarkCase.lanes.filter(lane => requestedLanes.has(lane))
      : benchmarkCase.lanes
  }))
  .filter(benchmarkCase => benchmarkCase.lanes.length);

const customSystem = benchmarkCase => benchmarkCase.family === "census" ? {
  name: `Candidate benchmark ${benchmarkCase.id}`,
  figure_refs: [],
  polycubes: [],
  polyhedra: [{ name: `Candidate ${benchmarkCase.id}`, vertices: benchmarkCase.vertices }],
  polycube_lattice: "z3"
} : null;

const configFor = (benchmarkCase, lane, seed) => ({
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
      : lane === "free_range_unbanded"
        ? unbandedMoveOrder
        : "balanced",
  face_order: faceOrder,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: lane === "free_range_unbanded" ? 0 : 2,
  generic_connected_patch_enumeration: connectedPatchEnumeration && lane === "free_range_unbanded",
  generic_failure_memo: failureMemo,
  generic_failure_memo_symmetry: failureMemoSymmetry,
  generic_failure_memo_max_states: failureMemoMaxStates,
  generic_geometric_nogood: geometricNogood,
  generic_geometric_nogood_max_clauses: geometricNogoodMaxClauses,
  generic_geometric_nogood_index: geometricNogoodIndex,
  generic_geometric_nogood_activation_failure_states: geometricNogoodActivationFailures,
  generic_geometric_nogood_activation_stagnation_failure_states: geometricNogoodStagnationFailures,
  generic_periodic_certificate: genericPeriodicCertificate && lane.startsWith("free_range"),
  generic_periodic_certificate_check_new_maximum:
    genericPeriodicCheckpoints && lane.startsWith("free_range"),
  generic_periodic_certificate_check_distinct_patches:
    genericPeriodicDistinctPatches && lane.startsWith("free_range"),
  generic_periodic_certificate_checkpoint_sampling_policy: genericPeriodicSamplingPolicy,
  generic_periodic_certificate_checkpoint_sampling_stride: genericPeriodicSamplingStride,
  generic_periodic_certificate_checkpoint_sampling_prefix: genericPeriodicSamplingPrefix,
  generic_periodic_certificate_checkpoint_max_checks_per_size: genericPeriodicMaxChecksPerSize,
  generic_periodic_certificate_checkpoint_max_total_checks: genericPeriodicMaxTotalChecks,
  generic_periodic_certificate_checkpoint_total_time_limit_ms: genericPeriodicCheckpointTotalTimeMs,
  generic_periodic_certificate_time_limit_ms: genericPeriodicCertificateTimeMs,
  include_mirrors: false,
  template_preflight: !lane.startsWith("free_range"),
  periodic_patch_max_tiles: periodicMax,
  periodic_patch_unbounded: false,
  isohedral_search_horizon_tiles: isohedralHorizon,
  snapshot_every: 1,
  placement_details: true,
  branch_cap: null,
  candidate_cap: null,
  node_limit: nodeLimit,
  random_seed: seed,
  seeded_tie_breaks: seededTies && benchmarkCase.expected === "unresolved" && lane.startsWith("free_range"),
  time_limit_ms: lane.startsWith("free_range") ? timeMs : exactTimeMs,
  ui_yield_interval_ms: 1000000
});

async function runLane(benchmarkCase, lane, seed) {
  const config = configFor(benchmarkCase, lane, seed);
  const started = performance.now();
  let final = null;
  let largestPatch = 0;
  let maxLiveTiles = 0;
  let maxFrontierPoints = 0;
  let maxCandidateCount = 0;
  let checkedPatchSize = 0;
  let witnessHash = null;
  let witnessGrowthAxisRank = 0;
  let witnessGrowthSpans = [];
  let witnessGrowthIsotropy = 0;
  let witnessPeriodicTranslationRank = 0;
  const growthMilestones = [];
  const checkpointFingerprints = [];
  const hashPlacements = placements => createHash("sha256")
    .update(placements.map(placement => [
      placement.prototile_idx,
      placement.orientation_id ?? placement.orientation_signature,
      ...(placement.translation ?? [])
    ].join(":"))
      .sort()
      .join("||"))
    .digest("hex")
    .slice(0, 16);
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    const patchSize = snapshot?.tile_count ?? snapshot?.placements?.length ?? 0;
    maxLiveTiles = Math.max(maxLiveTiles, patchSize, snapshot?.search_stats?.max_live_tiles ?? 0);
    if (Array.isArray(snapshot?.placements) && snapshot.placements.length > largestPatch) {
      largestPatch = snapshot.placements.length;
      witnessGrowthAxisRank = snapshot?.search_stats?.growth_axis_rank ?? 0;
      witnessGrowthSpans = snapshot?.search_stats?.growth_spans ?? [];
      witnessGrowthIsotropy = snapshot?.search_stats?.growth_isotropy ?? 0;
      witnessPeriodicTranslationRank = snapshot?.search_stats?.periodic_translation_rank ?? 0;
      growthMilestones.push({
        patchSize: largestPatch,
        visitedNodes: snapshot?.search_stats?.visited_nodes ?? 0,
        backtracks: snapshot?.search_stats?.backtracks ?? 0,
        elapsedMs: Math.round(performance.now() - started),
        witnessHash: hashPlacements(snapshot.placements)
      });
    }
    if (Array.isArray(snapshot?.placements) && snapshot.placements.length === largestPatch) {
      witnessHash = hashPlacements(snapshot.placements);
      const milestone = growthMilestones.at(-1);
      if (milestone?.patchSize === snapshot.placements.length) milestone.witnessHash = witnessHash;
    }
    maxFrontierPoints = Math.max(maxFrontierPoints, snapshot?.frontier_stats?.point_count ?? 0);
    maxCandidateCount = Math.max(maxCandidateCount, snapshot?.frontier_stats?.candidate_count ?? 0);
    if (message.type === "translational_check") {
      checkedPatchSize = message.patch_size;
      if (message.patch_fingerprint) checkpointFingerprints.push(message.patch_fingerprint);
    }
    if (message.type === "finished") final = message;
  }
  const stats = final?.search_stats ?? {};
  maxLiveTiles = Math.max(maxLiveTiles, stats.max_live_tiles ?? 0);
  return {
    case: benchmarkCase.id,
    family: benchmarkCase.family,
    expected: benchmarkCase.expected,
    lane,
    seed,
    resultKind: final?.result_kind ?? "missing_result",
    success: !!final?.success,
    canTile: final?.can_tile ?? null,
    certified: !!final?.tiling_evidence?.certified,
    certificateKind: final?.tiling_evidence?.certificate_kind
      ?? final?.tiling_evidence?.kind
      ?? null,
    certificatePatchSize: final?.tiling_evidence?.patch_size ?? null,
    periodVectors: final?.tiling_evidence?.period_vectors ?? null,
    certificateMotif: final?.tiling_evidence?.periodic_template?.motif ?? null,
    certificateProof: final?.tiling_evidence?.periodic_template?.proof ?? null,
    searchIncomplete: !!final?.search_incomplete,
    elapsedMs: Math.round(performance.now() - started),
    largestPatch,
    maxLiveTiles,
    uncapturedMaxLiveTiles: Math.max(0, maxLiveTiles - largestPatch),
    maxFrontierPoints,
    maxCandidateCount,
    checkedPatchSize,
    visitedNodes: stats.visited_nodes ?? 0,
    backtracks: stats.backtracks ?? 0,
    maxDepth: stats.max_depth ?? 0,
    moveOrder: stats.move_order ?? null,
    faceOrder: stats.face_order ?? faceOrder,
    effectiveSeed: stats.random_seed ?? null,
    seededTieBreaks: !!stats.seeded_tie_breaks,
    witnessHash,
    witnessGrowthAxisRank,
    witnessGrowthSpans,
    witnessGrowthIsotropy,
    witnessPeriodicTranslationRank,
    growthMilestones,
    generationLagCap: stats.generation_lag_cap ?? null,
    generationBandDeferrals: stats.generation_band_deferrals ?? 0,
    failureMemoEnabled: !!stats.generic_failure_memo_enabled,
    failureMemoStates: stats.generic_failure_memo_states ?? 0,
    failureMemoHits: stats.generic_failure_memo_hits ?? 0,
    failureMemoCapacityReached: !!stats.generic_failure_memo_capacity_reached,
    failureMemoKeyEquivalence: stats.generic_failure_memo_key_equivalence ?? "disabled",
    connectedPatchEnumeration: !!stats.generic_connected_patch_enumeration,
    connectedPatchCandidateStates: stats.generic_connected_patch_candidate_states ?? 0,
    connectedPatchMaxCandidates: stats.generic_connected_patch_max_candidates ?? 0,
    geometricNogoodEnabled: !!stats.generic_geometric_nogood_enabled,
    geometricNogoodDisableReason: stats.generic_geometric_nogood_disable_reason ?? null,
    geometricNogoodClauses: stats.generic_geometric_nogood_clauses ?? 0,
    geometricNogoodPrunes: stats.generic_geometric_nogood_prunes ?? 0,
    geometricNogoodFailureStates: stats.generic_geometric_nogood_failure_states ?? 0,
    geometricNogoodActivationFailureStates:
      stats.generic_geometric_nogood_activation_failure_states ?? 0,
    geometricNogoodActivationStagnationFailureStates:
      stats.generic_geometric_nogood_activation_stagnation_failure_states ?? 0,
    geometricNogoodFailuresSinceGrowth: stats.generic_geometric_nogood_failures_since_growth ?? 0,
    geometricNogoodGrowthMarkTiles: stats.generic_geometric_nogood_growth_mark_tiles ?? 1,
    geometricNogoodActivated: !!stats.generic_geometric_nogood_activated,
    geometricNogoodCapacityReached: !!stats.generic_geometric_nogood_capacity_reached,
    geometricNogoodPivotIndex: !!stats.generic_geometric_nogood_pivot_index,
    geometricNogoodCompatibilityChecks: stats.generic_geometric_nogood_compatibility_checks ?? 0,
    geometricNogoodClauseChecks: stats.generic_geometric_nogood_clause_checks ?? 0,
    geometricNogoodLinearClauseChecks: stats.generic_geometric_nogood_linear_clause_checks ?? 0,
    geometricNogoodAvoidedClauseChecks: stats.generic_geometric_nogood_avoided_clause_checks ?? 0,
    genericPeriodicCertificateAttempted: !!stats.generic_periodic_certificate_attempted,
    genericPeriodicCertificateCompleted: !!stats.generic_periodic_certificate_completed,
    genericPeriodicCertificateTimedOut: !!stats.generic_periodic_certificate_timed_out,
    genericPeriodicCertificateFound: !!stats.generic_periodic_certificate_found,
    genericPeriodicCertificatePatchSize: stats.generic_periodic_certificate_patch_size ?? 0,
    genericPeriodicCertificateElapsedMs: stats.generic_periodic_certificate_elapsed_ms ?? 0,
    genericPeriodicCertificateChecksAttempted: stats.generic_periodic_certificate_checks_attempted ?? 0,
    genericPeriodicCertificateChecksCompleted: stats.generic_periodic_certificate_checks_completed ?? 0,
    genericPeriodicCertificateChecksTimedOut: stats.generic_periodic_certificate_checks_timed_out ?? 0,
    genericPeriodicCertificateCheckSizes: stats.generic_periodic_certificate_check_sizes ?? [],
    genericPeriodicCertificateCheckFingerprints: checkpointFingerprints,
    genericPeriodicCertificateTotalElapsedMs: stats.generic_periodic_certificate_total_elapsed_ms ?? 0,
    genericPeriodicCertificateDistinctPatchMode: !!stats.generic_periodic_certificate_distinct_patch_mode,
    genericPeriodicCertificateCheckpointSamplingPolicy:
      stats.generic_periodic_certificate_checkpoint_sampling_policy ?? "prefix",
    genericPeriodicCertificateCheckpointSamplingStride:
      stats.generic_periodic_certificate_checkpoint_sampling_stride ?? 1,
    genericPeriodicCertificateCheckpointSamplingPrefix:
      stats.generic_periodic_certificate_checkpoint_sampling_prefix ?? 0,
    genericPeriodicCertificateCheckpointEligibleStates:
      stats.generic_periodic_certificate_checkpoint_eligible_states ?? 0,
    genericPeriodicCertificateCheckpointSamplingSkips:
      stats.generic_periodic_certificate_checkpoint_sampling_skips ?? 0,
    genericPeriodicCertificateDuplicateStatesSkipped:
      stats.generic_periodic_certificate_duplicate_states_skipped ?? 0,
    genericPeriodicCertificatePerSizeCapSkips:
      stats.generic_periodic_certificate_per_size_cap_skips ?? 0,
    genericPeriodicCertificateTotalCapSkips:
      stats.generic_periodic_certificate_total_cap_skips ?? 0,
    genericPeriodicCertificateCheckpointTimeBudgetSkips:
      stats.generic_periodic_certificate_checkpoint_time_budget_skips ?? 0,
    genericPeriodicCertificateCheckpointTimeBudgetExhausted:
      !!stats.generic_periodic_certificate_checkpoint_time_budget_exhausted,
    genericPeriodicCertificateTargetAttempted: !!stats.generic_periodic_certificate_target_attempted,
    genericPeriodicCertificateTargetCompleted: !!stats.generic_periodic_certificate_target_completed,
    genericPeriodicCertificateTargetTimedOut: !!stats.generic_periodic_certificate_target_timed_out,
    genericPeriodicCertificateTargetFound: !!stats.generic_periodic_certificate_target_found,
    genericPeriodicInternalMotifAttempted: !!stats.generic_periodic_internal_motif_attempted,
    genericPeriodicInternalMotifFound: !!stats.generic_periodic_internal_motif_found,
    genericPeriodicInternalMotifVectorCount:
      stats.generic_periodic_internal_motif_vector_count ?? 0,
    genericPeriodicInternalMotifBasesTested:
      stats.generic_periodic_internal_motif_bases_tested ?? 0,
    genericPeriodicInternalMotifMaxTranslationSupport:
      stats.generic_periodic_internal_motif_max_translation_support ?? 0,
    genericPeriodicInternalMotifTopTranslations:
      stats.generic_periodic_internal_motif_top_translations ?? [],
    terminationReason: stats.termination_reason
      ?? (final?.tiling_evidence?.certified
        ? "certificate_found"
        : final?.success
          ? "target_reached"
          : final?.search_incomplete
            ? "bounded_incomplete"
            : "exhausted"),
    quotientAttempts: stats.isohedral_certificate_attempts ?? 0,
    duplicateQuotientStatesSkipped: stats.isohedral_certificate_duplicate_states_skipped ?? 0,
    periodicMotifNodes: stats.periodic_motif_nodes ?? 0
  };
}

const rows = [];
for (const benchmarkCase of cases) {
  for (const lane of benchmarkCase.lanes) {
    const laneSeeds = benchmarkCase.expected === "unresolved"
      && lane.startsWith("free_range")
      ? seeds
      : [seeds[0]];
    for (const seed of laneSeeds) {
      const row = await runLane(benchmarkCase, lane, seed);
      rows.push(row);
      if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "result", ...row })}\n`);
    }
  }
}

const rowsFor = (id, lane) => rows.filter(row => row.case === id && row.lane === lane);
const rowFor = (id, lane, seed = seeds[0]) => rows.find(row => row.case === id && row.lane === lane && row.seed === seed);
const median = values => {
  const sorted = values.slice().sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
};
const freeRangePolicySummary = (id, lane, policy) => {
  const trials = rowsFor(id, lane);
  if (!trials.length) return null;
  const depths = trials.map(row => row.largestPatch);
  const targetHits = trials.filter(row => row.largestPatch >= target).length;
  return {
    policy,
    trials: trials.length,
    seeds: trials.map(row => row.seed),
    targetHits,
    targetHitRate: targetHits / trials.length,
    minimumLargestPatch: Math.min(...depths),
    medianLargestPatch: median(depths),
    maximumLargestPatch: Math.max(...depths),
    totalVisitedNodes: trials.reduce((sum, row) => sum + row.visitedNodes, 0),
    totalBacktracks: trials.reduce((sum, row) => sum + row.backtracks, 0),
    terminationReasons: Object.fromEntries([...new Set(trials.map(row => row.terminationReason ?? "completed"))]
      .map(reason => [reason, trials.filter(row => (row.terminationReason ?? "completed") === reason).length]))
  };
};
const preferredFreeRangePolicy = id => {
  const balanced = freeRangePolicySummary(id, "free_range", "balanced");
  const noBrainer = freeRangePolicySummary(id, "free_range_no_brainer", "no_brainer");
  if (!balanced || !noBrainer) return null;
  if (balanced.targetHits !== noBrainer.targetHits) {
    return balanced.targetHits > noBrainer.targetHits ? "balanced" : "no_brainer";
  }
  for (const metric of ["medianLargestPatch", "minimumLargestPatch", "maximumLargestPatch"]) {
    if (balanced[metric] !== noBrainer[metric]) return balanced[metric] > noBrainer[metric] ? "balanced" : "no_brainer";
  }
  return balanced.totalVisitedNodes <= noBrainer.totalVisitedNodes ? "balanced" : "no_brainer";
};
const proofSearchPortfolio = id => {
  const trials = rowsFor(id, "free_range_unbanded");
  if (!trials.length) return null;
  const depths = trials.map(row => row.largestPatch);
  const targetHits = trials.filter(row => row.largestPatch >= target).length;
  const certifiedNonTilerTrials = trials.filter(row => row.certified && row.canTile === false).length;
  const certifiedPeriodicTrials = trials.filter(row => row.certified && row.canTile === true).length;
  const targetWitnessHashes = trials
    .filter(row => row.largestPatch >= target && row.witnessHash)
    .map(row => row.witnessHash);
  return {
    target,
    trials: trials.length,
    seeds: trials.map(row => row.seed),
    targetHits,
    targetHitRate: targetHits / trials.length,
    certifiedNonTilerTrials,
    certifiedPeriodicTrials,
    distinctTargetWitnesses: new Set(targetWitnessHashes).size,
    targetWitnessHashes,
    robustLargestPatch: Math.min(...depths),
    medianLargestPatch: median(depths),
    bestLargestPatch: Math.max(...depths),
    totalVisitedNodes: trials.reduce((sum, row) => sum + row.visitedNodes, 0),
    totalBacktracks: trials.reduce((sum, row) => sum + row.backtracks, 0),
    outcome: certifiedPeriodicTrials
      ? "certified_periodic_target_patch"
      : certifiedNonTilerTrials
        ? "certified_non_tiler"
        : targetHits === trials.length
          ? "robust_target_patch"
          : targetHits
            ? "seed_sensitive_target_patch"
            : "bounded_below_target",
    terminationReasons: Object.fromEntries([...new Set(trials.map(row => row.terminationReason ?? "completed"))]
      .map(reason => [reason, trials.filter(row => (row.terminationReason ?? "completed") === reason).length]))
  };
};
const freeRangePortfolio = id => {
  const balanced = freeRangePolicySummary(id, "free_range", "balanced");
  const noBrainer = freeRangePolicySummary(id, "free_range_no_brainer", "no_brainer");
  if (!balanced || !noBrainer) return null;
  const policies = [balanced, noBrainer];
  const trials = [...rowsFor(id, "free_range"), ...rowsFor(id, "free_range_no_brainer")];
  const depths = trials.map(row => row.largestPatch);
  const targetHitCount = trials.filter(row => row.largestPatch >= target).length;
  const policiesReachingTarget = policies.filter(policy => policy.targetHits > 0).map(policy => policy.policy);
  const policiesReachingTargetEverySeed = policies
    .filter(policy => policy.targetHits === policy.trials)
    .map(policy => policy.policy);
  return {
    target,
    seeds,
    trialCount: trials.length,
    targetHitCount,
    targetHitRate: targetHitCount / trials.length,
    outcome: targetHitCount === trials.length
      ? "robust_target_reached"
      : targetHitCount
        ? "policy_or_seed_sensitive_target_reached"
        : "bounded_below_target",
    policiesReachingTarget,
    policiesReachingTargetEverySeed,
    robustLargestPatch: Math.min(...depths),
    medianLargestPatch: median(depths),
    bestLargestPatch: Math.max(...depths),
    preferredPolicy: preferredFreeRangePolicy(id),
    policySummaries: { balanced, noBrainer },
    combinedVisitedNodes: trials.reduce((sum, row) => sum + row.visitedNodes, 0),
    combinedBacktracks: trials.reduce((sum, row) => sum + row.backtracks, 0)
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
  .map(id => {
    const freeRangeUnbanded = rowFor(id, "free_range_unbanded") ?? null;
    const freeRangeUnbandedTrials = rowsFor(id, "free_range_unbanded");
    const proofPortfolio = proofSearchPortfolio(id);
    return {
      id,
      translational: rowFor(id, "translational") ?? null,
      isohedral: rowFor(id, "isohedral") ?? null,
      freeRange: rowFor(id, "free_range") ?? null,
      freeRangeNoBrainer: rowFor(id, "free_range_no_brainer") ?? null,
      freeRangeUnbanded,
      freeRangeUnbandedTrials,
      proofSearchPortfolio: proofPortfolio,
      freeRangeTrials: rowsFor(id, "free_range"),
      freeRangeNoBrainerTrials: rowsFor(id, "free_range_no_brainer"),
      preferredFreeRangePolicy: preferredFreeRangePolicy(id),
      freeRangePortfolio: freeRangePortfolio(id),
      screeningConclusion: proofPortfolio?.certifiedNonTilerTrials > 0
        ? "reject_certified_non_tiler"
        : proofPortfolio?.certifiedPeriodicTrials > 0
          ? "reject_certified_periodic"
          : "inconclusive"
    };
  });
const summary = {
  schemaVersion: 19,
  configuration: {
    target,
    timeMs,
    exactTimeMs,
    isohedralHorizon,
    periodicMax,
    nodeLimit,
    seeds,
    failureMemo,
    failureMemoSymmetry,
    failureMemoMaxStates,
    geometricNogood,
    geometricNogoodMaxClauses,
    geometricNogoodIndex,
    geometricNogoodActivationFailures,
    geometricNogoodStagnationFailures,
    faceOrder,
    unbandedMoveOrder,
    genericPeriodicCertificate,
    genericPeriodicCheckpoints,
    genericPeriodicDistinctPatches,
    genericPeriodicSamplingPolicy,
    genericPeriodicSamplingStride,
    genericPeriodicSamplingPrefix,
    genericPeriodicMaxChecksPerSize,
    genericPeriodicMaxTotalChecks,
    genericPeriodicCheckpointTotalTimeMs,
    genericPeriodicCertificateTimeMs,
    seededTies,
    connectedPatchEnumeration,
    lanes: requestedLanes.size ? [...requestedLanes] : null
  },
  cases: cases.map(({ id, family, expected }) => ({ id, family, expected })),
  rows,
  controls: controlGates,
  controlGatesPassed: Object.values(controlGates).every(Boolean),
  unresolved
};
if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "summary", ...summary })}\n`);
else {
  const serializedSummary = `${JSON.stringify(summary, null, 2)}\n`;
  if (outputFile) await writeFile(outputFile, serializedSummary);
  else process.stdout.write(serializedSummary);
}
if (!summary.controlGatesPassed) process.exitCode = 2;
