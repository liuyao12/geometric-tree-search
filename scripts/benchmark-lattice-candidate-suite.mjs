#!/usr/bin/env node

import { createHash } from "node:crypto";
import { writeFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  LATTICE_POLYHEDRON_CENSUS_POOL,
  LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES,
  LATTICE_POLYHEDRON_SURVIVORS
} from "../assets/lattice-polyhedron-survivors.js";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { searchPolycubeCorona } from "../assets/polycube-corona-search.js";

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
const criterion = args.get("criterion") === "shell" ? "shell" : "count";
const target = Math.max(2, Math.floor(numberArg("target", criterion === "shell" ? 2 : 24)));
const timeMs = Math.max(50, Math.floor(numberArg("time-ms", 1000)));
const exactTimeMs = Math.max(timeMs, Math.floor(numberArg("exact-time-ms", 3000)));
const isohedralHorizon = Math.max(2, Math.floor(numberArg("isohedral-horizon", 24)));
const periodicMax = Math.max(1, Math.floor(numberArg("periodic-max", 4)));
const nodeLimit = Math.max(1, Math.floor(numberArg("node-limit", 500000)));
const gctsRounds = Math.max(1, Math.floor(numberArg("gcts-rounds", 1)));
const gctsMarkingReachMultiplier = Math.max(1, numberArg("gcts-marking-reach", 1));
const gctsMarkingMaxClauses = Math.max(0, Math.floor(numberArg("gcts-marking-max-clauses", 20000)));
const gctsMarkingMaxContextTiles = Math.max(1, Math.floor(numberArg("gcts-marking-max-context", 1000000)));
const gctsMarkingActivationFailures = Math.max(0, Math.floor(numberArg("gcts-marking-activation-failures", 0)));
const gctsMarkingSymmetry = args.get("gcts-marking-symmetry") === "rotations" ? "rotations" : "fixed";
const gctsMarkingIndex = args.get("gcts-marking-index") !== "false";
const gctsMarkingBlockerMode = args.get("gcts-marking-blockers") === "all" ? "all" : "first";
const restartEpisodes = Math.max(1, Math.floor(numberArg("restart-episodes", 4)));
const discrepancySchedule = (args.get("discrepancy-schedule") ?? "0,1,2,4")
  .split(",")
  .map(value => Math.max(0, Math.floor(Number(value))))
  .filter(Number.isFinite);
if (!discrepancySchedule.length) discrepancySchedule.push(0);
const beamWidth = Math.max(1, Math.floor(numberArg("beam-width", 32)));
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
const polycubeById = new Map(POLYCUBE_GCTS_CANDIDATES.map(candidate => [candidate.id, candidate]));
const preShellIds = new Set(LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES.map(candidate => candidate.id));
const defaultIds = [
  "8_2480",
  "10_27010",
  ...LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES.map(candidate => candidate.id)
];
const censusCases = (requestedIds.size ? [...requestedIds] : defaultIds)
  .map(id => censusById.get(id) ?? polycubeById.get(id))
  .filter(Boolean)
  .map(candidate => ({
    id: candidate.id,
    family: candidate.voxels ? "polycube_census" : "census",
    expected: candidate.screening.status === "inconclusive"
      ? "unresolved"
      : candidate.screening.certificate,
    knownPeriodicTemplate: candidate.screening.periodic_template ?? null,
    researchQueue: preShellIds.has(candidate.id),
    vertices: candidate.vertices,
    voxels: candidate.voxels,
    lanes: preShellIds.has(candidate.id) || candidate.voxels
      ? ["translational", "isohedral", "free_range", "gcts", "rl", "gcts_rl", "restart_dfs", "ilds", "uct", "beam", "free_range_no_brainer", "free_range_unbanded"]
      : candidate.screening.certificate === "translational"
      ? ["translational", "free_range"]
      : candidate.screening.certificate === "isohedral_periodic_quotient"
        ? ["isohedral", "free_range"]
        : ["translational", "isohedral", "free_range", "gcts", "rl", "gcts_rl", "restart_dfs", "ilds", "uct", "beam", "free_range_no_brainer", "free_range_unbanded"]
  }));
const specialCases = includeSpecial ? [
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

const customSystem = benchmarkCase => ["census", "polycube_census"].includes(benchmarkCase.family) ? {
  name: `Candidate benchmark ${benchmarkCase.id}`,
  figure_refs: [],
  polycubes: benchmarkCase.voxels
    ? [{ name: `Candidate ${benchmarkCase.id}`, voxels: benchmarkCase.voxels }]
    : [],
  polyhedra: benchmarkCase.vertices
    ? [{ name: `Candidate ${benchmarkCase.id}`, vertices: benchmarkCase.vertices }]
    : [],
  polycube_lattice: "z3"
} : null;

const configFor = (benchmarkCase, lane, seed, proposalProgram = null, searchOptions = {}) => {
  const genericLane = lane.startsWith("free_range")
    || ["gcts", "rl", "gcts_rl", "restart_dfs", "ilds", "uct", "beam"].includes(lane);
  return ({
  mode_key: benchmarkCase.family === "control" ? benchmarkCase.id : "cube",
  custom_system: customSystem(benchmarkCase),
  polycube_lattice: "z3",
  criterion,
  target_val: lane === "isohedral" && criterion === "count" ? Math.max(target, 500) : target,
  tiling_strategy: genericLane ? "free_range" : lane,
  move_order: lane === "isohedral"
    ? "isohedral"
    : lane === "gcts"
      ? "balanced"
    : lane === "rl" || lane === "gcts_rl"
      ? "rl"
    : lane === "uct"
      ? "uct"
    : lane === "free_range_no_brainer"
      ? "no_brainer"
      : lane === "free_range_unbanded"
        ? unbandedMoveOrder
        : "balanced",
  proposal_program: null,
  complete_lattice_point_branching: genericLane && lane !== "free_range_unbanded",
  gcts_failure_marking: lane === "gcts" || lane === "gcts_rl",
  gcts_marking_reach_multiplier: gctsMarkingReachMultiplier,
  gcts_marking_max_clauses: gctsMarkingMaxClauses,
  gcts_marking_max_context_tiles: gctsMarkingMaxContextTiles,
  gcts_marking_activation_failures: gctsMarkingActivationFailures,
  gcts_marking_symmetry: gctsMarkingSymmetry,
  gcts_marking_index: gctsMarkingIndex,
  gcts_marking_blocker_mode: gctsMarkingBlockerMode,
  search_discrepancy_limit: searchOptions.discrepancyLimit ?? null,
  enumerate_successors_only: searchOptions.enumerateSuccessorsOnly === true,
  initial_patch: searchOptions.initialPatch ?? null,
  initial_patch_relative_to_root: false,
  initial_patch_require_face_connectivity: lane !== "beam",
  face_order: faceOrder,
  exhaustive: true,
  agent_exhaustive: true,
  agent_policy: lane === "rl" || lane === "gcts_rl" ? "cold_linucb" : null,
  agent_ucb_alpha: lane === "rl" || lane === "gcts_rl" ? 0 : null,
  forced_move_layer_lag_cap:
    lane === "free_range_unbanded"
    || (criterion === "shell" && ["free_range", "gcts", "rl", "gcts_rl"].includes(lane))
      ? 0
      : 2,
  generic_complete_shell_enumeration:
    criterion === "shell" && ["free_range", "gcts", "rl", "gcts_rl"].includes(lane),
  generic_connected_patch_enumeration: connectedPatchEnumeration && lane === "free_range_unbanded",
  generic_failure_memo: lane === "uct" ? false : failureMemo,
  generic_failure_memo_symmetry: failureMemoSymmetry,
  generic_failure_memo_max_states: failureMemoMaxStates,
  generic_geometric_nogood: geometricNogood,
  generic_geometric_nogood_max_clauses: geometricNogoodMaxClauses,
  generic_geometric_nogood_index: geometricNogoodIndex,
  generic_geometric_nogood_activation_failure_states: geometricNogoodActivationFailures,
  generic_geometric_nogood_activation_stagnation_failure_states: geometricNogoodStagnationFailures,
  generic_periodic_certificate: genericPeriodicCertificate && genericLane,
  generic_periodic_certificate_check_new_maximum:
    genericPeriodicCheckpoints && genericLane,
  generic_periodic_certificate_check_distinct_patches:
    genericPeriodicDistinctPatches && genericLane,
  generic_periodic_certificate_checkpoint_sampling_policy: genericPeriodicSamplingPolicy,
  generic_periodic_certificate_checkpoint_sampling_stride: genericPeriodicSamplingStride,
  generic_periodic_certificate_checkpoint_sampling_prefix: genericPeriodicSamplingPrefix,
  generic_periodic_certificate_checkpoint_max_checks_per_size: genericPeriodicMaxChecksPerSize,
  generic_periodic_certificate_checkpoint_max_total_checks: genericPeriodicMaxTotalChecks,
  generic_periodic_certificate_checkpoint_total_time_limit_ms: genericPeriodicCheckpointTotalTimeMs,
  generic_periodic_certificate_time_limit_ms: genericPeriodicCertificateTimeMs,
  generic_periodic_certificate_method: "internal_first",
  known_periodic_template: null,
  include_mirrors: false,
  template_preflight: !genericLane,
  periodic_patch_max_tiles: periodicMax,
  periodic_patch_unbounded: false,
  isohedral_search_horizon_tiles: isohedralHorizon,
  snapshot_every: 1,
  placement_details: true,
  branch_cap: null,
  candidate_cap: null,
  node_limit: nodeLimit,
  random_seed: seed,
  seeded_tie_breaks: seededTies && benchmarkCase.researchQueue && genericLane,
  time_limit_ms: searchOptions.timeLimitMs ?? (genericLane ? timeMs : exactTimeMs),
  ui_yield_interval_ms: 1000000
  });
};

async function runLane(
  benchmarkCase,
  lane,
  seed,
  { proposalProgram = null, round = 0, timeLimitMs = null, discrepancyLimit = null } = {}
) {
  const config = configFor(benchmarkCase, lane, seed, proposalProgram, {
    timeLimitMs,
    discrepancyLimit
  });
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
  let bestSnapshot = null;
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
      bestSnapshot = snapshot;
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
  const learnedProgram = null;
  const certificatePayloadBytes = final?.tiling_evidence?.periodic_template
    ? JSON.stringify(final.tiling_evidence.periodic_template).length
    : 0;
  return {
    case: benchmarkCase.id,
    family: benchmarkCase.family,
    expected: benchmarkCase.expected,
    lane,
    gctsRound: lane === "gcts" || lane === "gcts_rl" ? round : null,
    reusedLearnedPatch: false,
    learnedProgram,
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
    discrepancyLimit: stats.discrepancy_limit ?? null,
    discrepancyPrunes: stats.discrepancy_prunes ?? 0,
    maxDiscrepancyReached: stats.max_discrepancy_reached ?? 0,
    uctSimulations: stats.uct_simulations ?? 0,
    uctStates: stats.uct_states ?? 0,
    uctActionVisits: stats.uct_action_visits ?? 0,
    uctMaxReward: stats.uct_max_reward ?? 0,
    agentObservations: stats.agent_observations ?? 0,
    agentResolvedFailures: stats.agent_resolved_failures ?? 0,
    agentIncompleteObservations: stats.agent_incomplete_observations ?? 0,
    agentPositiveGrowthObservations: stats.agent_positive_growth_observations ?? 0,
    agentMaxBranchGrowth: stats.agent_max_branch_growth ?? 0,
    agentLearnedTags: stats.agent_learned_tags ?? 0,
    agentSiblingReorders: stats.agent_sibling_reorders ?? 0,
    agentPolicy: stats.agent_policy ?? null,
    agentStartedEmpty: !!stats.agent_started_empty,
    agentFeatureSchema: stats.agent_feature_schema ?? null,
    agentScoreTimeMs: stats.agent_score_time_ms ?? 0,
    agentTrainingUpdates: stats.agent_training_updates ?? 0,
    agentTrainingTimeMs: stats.agent_training_time_ms ?? 0,
    agentModelParameters: stats.agent_model_parameter_count ?? 0,
    agentModelWeights: stats.agent_model_weight_count ?? 0,
    agentModelPayloadBytes: stats.agent_model_payload_bytes ?? 0,
    agentProbeMaxLiveTiles: stats.agent_probe_max_live_tiles ?? null,
    proposalPatchTilesReplayed: stats.proposal_patch_tiles_replayed ?? 0,
    proposalPatchConflicts: stats.proposal_patch_conflicts ?? 0,
    proposalPatchConflictIndex: stats.proposal_patch_conflict_index ?? null,
    proposalPatchConflictReason: stats.proposal_patch_conflict_reason ?? null,
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
    gctsFailureMarkingEnabled: !!stats.gcts_failure_marking_enabled,
    markingStartedEmpty: stats.marking_started_empty !== false,
    markingObservedFailures: stats.marking_observed_failures ?? 0,
    markingGeometricClauses: stats.marking_geometric_clauses ?? 0,
    markingGeometricPrunes: stats.marking_geometric_prunes ?? 0,
    markingDuplicateFailures: stats.marking_duplicate_failures ?? 0,
    markingSkippedLargeContexts: stats.marking_skipped_large_contexts ?? 0,
    markingAverageContextTiles: stats.marking_average_context_tiles ?? 0,
    markingMaxContextTiles: stats.marking_max_context_tiles ?? 0,
    markingContextTokens: stats.marking_context_tokens ?? 0,
    markingPayloadBytes: stats.marking_payload_bytes ?? 0,
    markingFrontierChecks: stats.marking_frontier_checks ?? 0,
    markingClauseChecks: stats.marking_clause_checks ?? 0,
    markingAvoidedClauseChecks: stats.marking_avoided_clause_checks ?? 0,
    markingReach: stats.marking_reach ?? 0,
    markingRotationCount: stats.marking_rotation_count ?? 0,
    learnedPayloadBytes:
      (stats.agent_model_payload_bytes ?? 0) + (stats.marking_payload_bytes ?? 0),
    certificatePayloadBytes,
    retainedFailedTranslationalDomains: 0,
    transientSearchCacheEntries:
      (stats.generic_failure_memo_states ?? 0)
      + (stats.isohedral_certificate_states_retained ?? 0)
      + (stats.uct_states ?? 0),
    translationalMotifSizesAttempted: stats.translational_motif_sizes_attempted ?? 0,
    translationalLargestMotifSizeAttempted:
      stats.translational_largest_motif_size_attempted ?? 0,
    isohedralCertificateStatesRetained: stats.isohedral_certificate_states_retained ?? 0,
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

const patchFingerprint = placements => createHash("sha256")
  .update((placements ?? []).map(placement => [
    placement.prototile_idx,
    placement.orientation_id ?? placement.orientation_signature,
    ...(placement.translation ?? [])
  ].join(":"))
    .sort()
    .join("||"))
  .digest("hex")
  .slice(0, 16);

const beamSnapshotScore = snapshot => [
  snapshot?.frontier_stats?.min_gen ?? 0,
  snapshot?.search_stats?.growth_axis_rank ?? 0,
  snapshot?.search_stats?.growth_isotropy ?? 0,
  -(snapshot?.frontier_stats?.point_count ?? Infinity),
  snapshot?.tile_count ?? 0
];

const compareBeamSnapshots = (left, right) => {
  const leftScore = beamSnapshotScore(left);
  const rightScore = beamSnapshotScore(right);
  for (let index = 0; index < leftScore.length; index++) {
    if (leftScore[index] !== rightScore[index]) return rightScore[index] - leftScore[index];
  }
  return patchFingerprint(left?.placements).localeCompare(patchFingerprint(right?.placements));
};

async function enumerateBeamSuccessors(benchmarkCase, seed, initialSnapshot, remainingMs) {
  const config = configFor(benchmarkCase, "beam", seed, null, {
    timeLimitMs: Math.max(25, remainingMs),
    enumerateSuccessorsOnly: true,
    initialPatch: initialSnapshot ? { placements: initialSnapshot.placements } : null
  });
  const successors = [];
  let finalStats = null;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.type === "search_successor" && message.snapshot) successors.push(message.snapshot);
    if (message.type === "successor_set_finished") finalStats = message.search_stats;
  }
  return { successors, stats: finalStats ?? {} };
}

async function runBeamLane(benchmarkCase, seed) {
  const started = performance.now();
  let frontier = [null];
  let bestSnapshot = null;
  let visitedNodes = 0;
  let expandedStates = 0;
  let generatedStates = 0;
  const seen = new Set();
  const growthMilestones = [];
  while (frontier.length && performance.now() - started < timeMs) {
    const next = new Map();
    for (const stateSnapshot of frontier) {
      const remaining = Math.floor(timeMs - (performance.now() - started));
      if (remaining <= 0) break;
      const expansion = await enumerateBeamSuccessors(
        benchmarkCase,
        seed + expandedStates * 7919,
        stateSnapshot,
        remaining
      );
      expandedStates += 1;
      visitedNodes += expansion.stats.visited_nodes ?? 0;
      for (const successor of expansion.successors) {
        generatedStates += 1;
        const fingerprint = patchFingerprint(successor.placements);
        if (seen.has(fingerprint)) continue;
        seen.add(fingerprint);
        next.set(fingerprint, successor);
        if (!bestSnapshot || (successor.tile_count ?? 0) > (bestSnapshot.tile_count ?? 0)) {
          bestSnapshot = successor;
          growthMilestones.push({
            patchSize: successor.tile_count,
            visitedNodes,
            backtracks: 0,
            elapsedMs: Math.round(performance.now() - started),
            witnessHash: fingerprint
          });
        }
      }
    }
    frontier = [...next.values()].sort(compareBeamSnapshots).slice(0, beamWidth);
    if ((bestSnapshot?.tile_count ?? 0) >= target) break;
  }
  const elapsedMs = Math.round(performance.now() - started);
  return {
    case: benchmarkCase.id,
    family: benchmarkCase.family,
    expected: benchmarkCase.expected,
    lane: "beam",
    seed,
    resultKind: (bestSnapshot?.tile_count ?? 0) >= target ? "target_reached" : "search_incomplete",
    success: (bestSnapshot?.tile_count ?? 0) >= target,
    canTile: null,
    certified: false,
    searchIncomplete: (bestSnapshot?.tile_count ?? 0) < target,
    elapsedMs,
    largestPatch: bestSnapshot?.tile_count ?? 1,
    maxLiveTiles: bestSnapshot?.tile_count ?? 1,
    visitedNodes,
    backtracks: 0,
    witnessHash: bestSnapshot ? patchFingerprint(bestSnapshot.placements) : null,
    witnessGrowthAxisRank: bestSnapshot?.search_stats?.growth_axis_rank ?? 0,
    witnessGrowthSpans: bestSnapshot?.search_stats?.growth_spans ?? [],
    witnessGrowthIsotropy: bestSnapshot?.search_stats?.growth_isotropy ?? 0,
    witnessPeriodicTranslationRank: bestSnapshot?.search_stats?.periodic_translation_rank ?? 0,
    growthMilestones,
    faceOrder,
    beamWidth,
    beamExpandedStates: expandedStates,
    beamGeneratedStates: generatedStates,
    beamDistinctStates: seen.size,
    terminationReason: (bestSnapshot?.tile_count ?? 0) >= target ? "target_reached" : "time_limit"
  };
}

const combineEpisodes = (lane, seed, episodes) => {
  const best = episodes.slice().sort((left, right) =>
    right.largestPatch - left.largestPatch
    || Number(right.success) - Number(left.success)
    || left.elapsedMs - right.elapsedMs
  )[0];
  let elapsedOffset = 0;
  const growthMilestones = [];
  let runningBest = 0;
  for (const episode of episodes) {
    for (const milestone of episode.growthMilestones ?? []) {
      if (milestone.patchSize <= runningBest) continue;
      runningBest = milestone.patchSize;
      growthMilestones.push({ ...milestone, elapsedMs: elapsedOffset + milestone.elapsedMs });
    }
    elapsedOffset += episode.elapsedMs;
  }
  return {
    ...best,
    lane,
    seed,
    elapsedMs: episodes.reduce((sum, row) => sum + row.elapsedMs, 0),
    visitedNodes: episodes.reduce((sum, row) => sum + row.visitedNodes, 0),
    backtracks: episodes.reduce((sum, row) => sum + row.backtracks, 0),
    discrepancyPrunes: episodes.reduce((sum, row) => sum + row.discrepancyPrunes, 0),
    growthMilestones,
    episodeCount: episodes.length,
    episodes: episodes.map(row => ({
      effectiveSeed: row.effectiveSeed,
      discrepancyLimit: row.discrepancyLimit,
      largestPatch: row.largestPatch,
      visitedNodes: row.visitedNodes,
      backtracks: row.backtracks,
      elapsedMs: row.elapsedMs,
      terminationReason: row.terminationReason
    }))
  };
};

async function runSearchBaseline(benchmarkCase, lane, seed) {
  if (lane === "restart_dfs") {
    const episodeBudget = Math.max(50, Math.floor(timeMs / restartEpisodes));
    const episodes = [];
    for (let episode = 0; episode < restartEpisodes; episode++) {
      episodes.push(await runLane(benchmarkCase, lane, seed * 1009 + episode * 7919, {
        timeLimitMs: episodeBudget
      }));
    }
    return combineEpisodes(lane, seed, episodes);
  }
  if (lane === "ilds") {
    const episodes = [];
    for (let index = 0; index < discrepancySchedule.length; index++) {
      const discrepancyLimit = discrepancySchedule[index];
      const used = episodes.reduce((sum, row) => sum + row.elapsedMs, 0);
      const remainingIterations = discrepancySchedule.length - index;
      const episodeBudget = Math.max(50, Math.floor((timeMs - used) / remainingIterations));
      episodes.push(await runLane(benchmarkCase, lane, seed, {
        timeLimitMs: episodeBudget,
        discrepancyLimit
      }));
    }
    return combineEpisodes(lane, seed, episodes);
  }
  if (lane === "beam") return runBeamLane(benchmarkCase, seed);
  return runLane(benchmarkCase, lane, seed);
}

const rows = [];
for (const benchmarkCase of cases) {
  for (const lane of benchmarkCase.lanes) {
    const laneSeeds = benchmarkCase.researchQueue
      && (lane.startsWith("free_range") || ["gcts", "rl", "gcts_rl", "restart_dfs", "ilds", "uct", "beam"].includes(lane))
      ? seeds
      : [seeds[0]];
    for (const seed of laneSeeds) {
      const rounds = lane === "gcts" || lane === "gcts_rl" ? gctsRounds : 1;
      for (let round = 0; round < rounds; round++) {
        const row = ["restart_dfs", "ilds", "beam"].includes(lane)
          ? await runSearchBaseline(benchmarkCase, lane, seed)
          : await runLane(benchmarkCase, lane, seed, { proposalProgram: null, round });
        rows.push(row);
        if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "result", ...row })}\n`);
      }
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
const SEARCH_ALGORITHM_LANES = ["free_range", "gcts", "rl", "gcts_rl", "restart_dfs", "ilds", "uct", "beam"];
const searchAlgorithmComparisons = cases
  .filter(benchmarkCase => benchmarkCase.researchQueue)
  .map(benchmarkCase => ({
    id: benchmarkCase.id,
    role: censusById.get(benchmarkCase.id)?.screening?.certificate === "translational"
      ? "periodic_control"
      : "hard_obstruction_control",
    algorithms: SEARCH_ALGORITHM_LANES.map(lane => {
      const trials = rowsFor(benchmarkCase.id, lane);
      if (!trials.length) return null;
      const depths = trials.map(row => row.largestPatch);
      return {
        lane,
        trials: trials.length,
        robustLargestPatch: Math.min(...depths),
        medianLargestPatch: median(depths),
        bestLargestPatch: Math.max(...depths),
        targetHits: trials.filter(row => row.largestPatch >= target).length,
        medianVisitedNodes: median(trials.map(row => row.visitedNodes ?? 0)),
        medianElapsedMs: median(trials.map(row => row.elapsedMs ?? 0))
      };
    }).filter(Boolean)
  }));
const gctsGrowthComparisons = cases
  .filter(benchmarkCase => benchmarkCase.researchQueue)
  .map(benchmarkCase => {
    const free = rowsFor(benchmarkCase.id, "free_range");
    const gcts = rowsFor(benchmarkCase.id, "gcts");
    if (!free.length || !gcts.length) return null;
    const freeDepths = free.map(row => row.largestPatch);
    const gctsDepths = gcts.map(row => row.largestPatch);
    const periodicControl = censusById.get(benchmarkCase.id)?.screening?.certificate === "translational";
    const result = {
      id: benchmarkCase.id,
      role: periodicControl ? "periodic_control" : "hard_obstruction_control",
      freeRange: {
        robustLargestPatch: Math.min(...freeDepths),
        medianLargestPatch: median(freeDepths),
        bestLargestPatch: Math.max(...freeDepths)
      },
      gcts: {
        robustLargestPatch: Math.min(...gctsDepths),
        medianLargestPatch: median(gctsDepths),
        bestLargestPatch: Math.max(...gctsDepths)
      }
    };
    result.robustAdvantage = result.gcts.robustLargestPatch - result.freeRange.robustLargestPatch;
    result.medianAdvantage = result.gcts.medianLargestPatch - result.freeRange.medianLargestPatch;
    result.gatePassed = periodicControl
      ? null
      : result.robustAdvantage > 0 && result.medianAdvantage > 0;
    return result;
  })
  .filter(Boolean);
const hardGctsGrowthComparisons = gctsGrowthComparisons.filter(row => row.role === "hard_obstruction_control");
const gctsGrowthGatePassed = hardGctsGrowthComparisons.length > 0
  && hardGctsGrowthComparisons.every(row => row.gatePassed);
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
// A finite connected patch cannot serve as a non-tiling oracle: even a
// genuine non-tiler may admit arbitrarily many partial copies.  Use the
// independent, exhaustive radius-two corona solver for the negative control.
const nonTilerControlVoxels = [[0,0,0],[0,0,1],[0,0,2],[0,1,0],[0,1,2],[0,2,0],[0,2,1],[1,1,1],[1,2,1],[1,2,2]];
const nonTilerControlResult = includeSpecial ? searchPolycubeCorona(nonTilerControlVoxels, {
  layers: 2,
  nodeLimit: 500,
  timeLimitMs: 5000,
  nogoods: true,
  conflictBackjumping: true
}) : null;
const controlGates = {
  translationalControl: cases.some(item => item.id === "8_2480")
    ? rowFor("8_2480", "translational")?.resultKind === "certified_tiling"
    : true,
  isohedralControl: cases.some(item => item.id === "10_27010")
    ? rowFor("10_27010", "isohedral")?.certificatePatchSize === 24
    : true,
  nonTilerControl: includeSpecial
    ? nonTilerControlResult?.certified_non_tiler === true
    : true,
  aperiodicControl: includeSpecial
    ? rowFor("scd_conway", "free_range")?.resultKind === "known_aperiodic_construction"
    : true
};
const candidateSummaries = LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES
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
      gcts: rowFor(id, "gcts") ?? null,
      gctsTrials: rowsFor(id, "gcts"),
      gctsWarmTrials: rows.filter(row => row.case === id && row.lane.startsWith("gcts_warm_")),
      freeRangeNoBrainer: rowFor(id, "free_range_no_brainer") ?? null,
      freeRangeUnbanded,
      freeRangeUnbandedTrials,
      proofSearchPortfolio: proofPortfolio,
      freeRangeTrials: rowsFor(id, "free_range"),
      freeRangeNoBrainerTrials: rowsFor(id, "free_range_no_brainer"),
      preferredFreeRangePolicy: preferredFreeRangePolicy(id),
      freeRangePortfolio: freeRangePortfolio(id),
      screeningConclusion: censusById.get(id)?.screening?.certificate === "translational"
        ? "reject_certified_periodic"
        : proofPortfolio?.certifiedNonTilerTrials > 0
        ? "reject_certified_non_tiler"
        : proofPortfolio?.certifiedPeriodicTrials > 0
          ? "reject_certified_periodic"
          : "inconclusive"
    };
  });
const unresolvedIds = new Set(LATTICE_POLYHEDRON_SURVIVORS.map(candidate => candidate.id));
const activeUnresolved = candidateSummaries.filter(candidate => unresolvedIds.has(candidate.id));
const summary = {
  schemaVersion: 24,
  configuration: {
    criterion,
    target,
    timeMs,
    exactTimeMs,
    isohedralHorizon,
    periodicMax,
    nodeLimit,
    gctsRounds,
    gctsMarkingReachMultiplier,
    gctsMarkingMaxClauses,
    gctsMarkingMaxContextTiles,
    gctsMarkingActivationFailures,
    gctsMarkingSymmetry,
    gctsMarkingIndex,
    gctsMarkingBlockerMode,
    restartEpisodes,
    discrepancySchedule,
    beamWidth,
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
  searchAlgorithmComparisons,
  gctsGrowthComparisons,
  gctsGrowthGatePassed,
  controls: controlGates,
  controlEvidence: {
    nonTiler: nonTilerControlResult ? {
      method: "independent_exhaustive_radius_two_corona",
      certifiedNonTiler: nonTilerControlResult.certified_non_tiler === true,
      stoppedBy: nonTilerControlResult.stopped_by ?? null,
      visitedNodes: nonTilerControlResult.nodes ?? null
    } : null
  },
  controlGatesPassed: Object.values(controlGates).every(Boolean),
  candidates: candidateSummaries,
  // Kept as a compatibility alias for archived benchmark consumers. These are
  // the four historical research-queue summaries; use activeUnresolved for
  // the current catalogue conclusion.
  unresolved: candidateSummaries,
  activeUnresolved
};
if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "summary", ...summary })}\n`);
else {
  const serializedSummary = `${JSON.stringify(summary, null, 2)}\n`;
  if (outputFile) await writeFile(outputFile, serializedSummary);
  else process.stdout.write(serializedSummary);
}
if (!summary.controlGatesPassed) process.exitCode = 2;
