import { createTilingStream, preprocessTilingSystem, tileSpecs } from "./engine.js?v=20260830-a2-sliced9-v244";

let activeSequence = 0;
let stopToken = { stop: false, manual_pause: false, additional_time_ms: 0 };
let preparedRun = null;
const HISTORY_BATCH_LIMIT = 256;
const HISTORY_BATCH_INTERVAL_MS = 200;

const MODES = {
  free_range: {
    id: "free_range",
    label: "Free-range",
    strategy: "free_range",
    moveOrder: "balanced",
    templates: false,
    agentExhaustive: true
  },
  no_brainer: {
    id: "no_brainer",
    label: "Free-range · no-brainer",
    strategy: "free_range",
    moveOrder: "no_brainer",
    templates: false,
    agentExhaustive: true
  },
  proof: {
    id: "proof",
    label: "Proof search · complete rank",
    strategy: "free_range",
    moveOrder: "global",
    templates: false,
    agentExhaustive: true,
    proof: true
  },
  proof_nogood: {
    id: "proof_nogood",
    label: "Proof search · delayed nogoods",
    strategy: "free_range",
    moveOrder: "balanced",
    templates: false,
    agentExhaustive: true,
    proof: true,
    nogood: true
  },
  proof_crystal: {
    id: "proof_crystal",
    label: "Proof search · crystal rank",
    strategy: "free_range",
    moveOrder: "crystal",
    templates: false,
    agentExhaustive: true,
    proof: true
  },
  gcts: {
    id: "gcts",
    label: "GCTS",
    strategy: "free_range",
    moveOrder: "balanced",
    templates: false,
    agentExhaustive: true
  },
  rl: {
    id: "rl",
    label: "RL",
    strategy: "free_range",
    moveOrder: "rl",
    templates: false,
    agentExhaustive: true
  },
  gcts_rl: {
    id: "gcts_rl",
    label: "GCTS + RL",
    strategy: "free_range",
    moveOrder: "rl",
    templates: false,
    agentExhaustive: true
  },
  translational: {
    id: "translational",
    label: "Translational",
    strategy: "translational",
    moveOrder: "periodic",
    templates: true,
    agentExhaustive: true
  },
  isohedral: {
    id: "isohedral",
    label: "Isohedral",
    strategy: "isohedral",
    moveOrder: "isohedral",
    templates: true,
    agentExhaustive: false
  }
};

const post = (sequence, payload) => {
  if (sequence === activeSequence) self.postMessage({ sequence, ...payload });
};

function configureMode(baseConfig, mode) {
  const shellSearch = baseConfig.criterion === "shell";
  const translationalPatchGoal = baseConfig.criterion === "count"
    ? Math.max(1, Math.floor(baseConfig.target_val))
    : shellSearch
      ? Math.max(24, Math.floor(baseConfig.target_val) * 24)
      : Math.max(1, Math.floor(baseConfig.periodic_patch_max_tiles ?? baseConfig.target_val ?? 4));
  // The four general-search benchmark lanes must traverse the same complete
  // shell state space.  RL may reorder choices and GCTS may soundly prune
  // proved-failed supersets, but the naive Free-range control must not retain
  // the older generation-banded/local-search semantics.
  const exactLearningShell = shellSearch
    && ["free_range", "gcts", "rl", "gcts_rl"].includes(mode.id);
  const effectiveMode = shellSearch && mode.proof
    ? { ...mode, label: `${mode.label.replace(/ · .*$/u, "")} · complete shell` }
    : mode;
  const config = {
    ...baseConfig,
    tiling_strategy: mode.strategy,
    move_order: shellSearch && mode.proof ? "shell" : mode.moveOrder,
    proposal_program: null,
    complete_lattice_point_branching: ["free_range", "gcts", "rl", "gcts_rl", "no_brainer", "translational"].includes(mode.id),
    gcts_failure_marking: mode.id === "gcts" || mode.id === "gcts_rl",
    gcts_marking_reach_multiplier: baseConfig.gcts_marking_reach_multiplier ?? 1,
    gcts_marking_max_clauses: baseConfig.gcts_marking_max_clauses ?? 20000,
    gcts_marking_max_context_tiles: baseConfig.gcts_marking_max_context_tiles ?? 1000000,
    gcts_marking_activation_failures: baseConfig.gcts_marking_activation_failures ?? 0,
    gcts_marking_symmetry: baseConfig.gcts_marking_symmetry ?? "fixed",
    gcts_marking_index: baseConfig.gcts_marking_index !== false,
    agent_exhaustive: mode.agentExhaustive,
    agent_policy: ["rl", "gcts_rl"].includes(mode.id) ? "cold_linucb" : null,
    agent_ucb_alpha: ["rl", "gcts_rl"].includes(mode.id) ? 0 : null,
    // RL is deliberately a one-tile-at-a-time policy. Periodic or isohedral
    // clusters must emerge from its action sequence, not from macro replay.
    learned_layer_macro: false,
    known_periodic_template: null,
    initial_patch: null,
    greedy_no_backtrack: false,
    template_preflight: mode.templates,
    periodic_preflight: mode.templates,
    periodic_patch_unbounded: false,
    periodic_stop_at_growth_goal: mode.id === "translational",
    periodic_goal_preflight_time_ms: mode.id === "translational" ? 1000 : null,
    periodic_motif_node_limit: mode.id === "translational" ? 2500 : baseConfig.periodic_motif_node_limit,
    periodic_patch_max_tiles: mode.id === "translational"
      ? translationalPatchGoal
      : baseConfig.periodic_patch_max_tiles,
    snapshot_every: 1,
    placement_details: ["gcts", "rl", "gcts_rl"].includes(mode.id),
    branch_cap: null,
    candidate_cap: null,
    forced_move_layer_lag_cap: mode.proof || exactLearningShell ? 0 : baseConfig.forced_move_layer_lag_cap,
    generic_connected_patch_enumeration: !!mode.proof && !shellSearch,
    generic_complete_shell_enumeration: (!!mode.proof || exactLearningShell) && shellSearch,
    generic_failure_memo: !!mode.proof || exactLearningShell,
    generic_failure_memo_symmetry: shellSearch ? "rigid" : "fixed",
    // Exact shell GCTS records complete failed placement contexts.  These
    // translation-equivariant subset nogoods are sound because any later
    // state containing the failed patch is one of its extensions.  RL alone
    // keeps only the common exact-state memo; GCTS+RL gets both mechanisms.
    generic_geometric_nogood: ["gcts", "gcts_rl"].includes(mode.id)
      || (!!mode.nogood && !shellSearch),
    generic_geometric_nogood_max_clauses: 20000,
    generic_geometric_nogood_index: true,
    generic_geometric_nogood_activation_failure_states: mode.nogood ? 25 : 0,
    seeded_tie_breaks: !!mode.proof || ["rl", "gcts_rl", "translational"].includes(mode.id),
    random_seed: baseConfig.random_seed ?? 1,
    generic_periodic_certificate: !!mode.proof && !shellSearch,
    generic_periodic_certificate_method: mode.proof ? "internal_first" : "boundary_first",
    generic_periodic_certificate_check_new_maximum: !!mode.proof && !shellSearch,
    generic_periodic_certificate_check_distinct_patches: !!mode.proof && !shellSearch,
    generic_periodic_certificate_checkpoint_sampling_policy: mode.proof ? "hybrid" : "prefix",
    generic_periodic_certificate_checkpoint_sampling_prefix: 4,
    generic_periodic_certificate_checkpoint_sampling_stride: 16,
    generic_periodic_certificate_checkpoint_max_checks_per_size: 7,
    generic_periodic_certificate_checkpoint_max_total_checks: 280,
    generic_periodic_certificate_checkpoint_total_time_limit_ms: 5000,
    generic_periodic_certificate_time_limit_ms: 1000,
    // The comparison worker enforces this as a cooperative, resumable clock
    // at generator yield points. The engine must not unwind at the first cap.
    time_limit_ms: null,
    exhaustive: !!mode.proof || exactLearningShell
  };
  return { baseConfig, mode, effectiveMode, config };
}

const epochNow = () => performance.timeOrigin + performance.now();

async function runMode(sequence, run, preparedSystem, preprocessingMilliseconds, startEpochMs) {
  const { baseConfig, mode, effectiveMode, config } = run;
  const delay = Math.max(0, startEpochMs - epochNow());
  if (delay > 0) await new Promise(resolve => setTimeout(resolve, delay));
  if (stopToken.stop || sequence !== activeSequence) return null;
  const started = startEpochMs;
  const baseClockBudgetMs = Number.isFinite(baseConfig.time_limit_ms)
    ? Math.max(0, Number(baseConfig.time_limit_ms))
    : Infinity;
  let pausedMilliseconds = 0;
  const searchElapsedMilliseconds = () => Math.max(0, epochNow() - started - pausedMilliseconds);
  const awaitClockBudget = async () => {
    while (
      (stopToken.manual_pause
        || (Number.isFinite(baseClockBudgetMs)
          && searchElapsedMilliseconds() >= baseClockBudgetMs + (Number(stopToken.additional_time_ms) || 0)))
      && !stopToken.stop
    ) {
      flushHistory();
      post(sequence, {
        type: "mode-paused",
        mode: mode.id,
        milliseconds: Math.round(searchElapsedMilliseconds()),
        tiles: lastHistoryTileCount ?? 0
      });
      const pausedAt = epochNow();
      await new Promise(resolve => { stopToken.resume_clock = resolve; });
      stopToken.resume_clock = null;
      pausedMilliseconds += Math.max(0, epochNow() - pausedAt);
    }
  };
  let best = 0;
  let final = null;
  let latestStats = null;
  let bestSnapshot = null;
  let terminalSnapshot = null;
  let checkedPatchSize = 0;
  const points = [];
  let lastHistoryTileCount = null;
  let lastHistoryFlushAt = epochNow();
  let pendingHistorySamples = [];
  const flushHistory = () => {
    if (!pendingHistorySamples.length) return;
    post(sequence, { type: "sample-batch", samples: pendingHistorySamples });
    pendingHistorySamples = [];
    lastHistoryFlushAt = epochNow();
  };
  const queueHistory = sample => {
    points.push(sample.point);
    pendingHistorySamples.push(sample);
    if (
      pendingHistorySamples.length >= HISTORY_BATCH_LIMIT
      || epochNow() - lastHistoryFlushAt >= HISTORY_BATCH_INTERVAL_MS
    ) flushHistory();
  };
  post(sequence, { type: "series-start", mode: effectiveMode });
  for await (const message of createTilingStream(config, tileSpecs, stopToken, preparedSystem)) {
    if (stopToken.stop || sequence !== activeSequence) return null;
    if (message.type === "prototile_info") post(sequence, { type: "prototile-info", mode: mode.id, info: message });
    if (message.type === "translational_check") {
      checkedPatchSize = Math.max(checkedPatchSize, message.patch_size ?? 0);
      const targetPatchCheck = message.source === "generic_target_patch";
      const growthCheckpoint = message.source === "generic_growth_checkpoint";
      post(sequence, {
        type: "mode-status",
        mode: mode.id,
        text: targetPatchCheck
          ? message.certified
            ? `target patch certifies a ${message.patch_size}-tile translational quotient`
            : message.check_completed
              ? `${message.patch_size}-tile target patch is not a translational quotient`
              : `${message.patch_size}-tile target-patch quotient check timed out`
          : growthCheckpoint
            ? message.certified
              ? `${message.patch_size}-tile checkpoint certifies a translational quotient`
              : message.check_completed
                ? `${message.patch_size}-tile checkpoint is not a translational quotient`
                : `${message.patch_size}-tile checkpoint quotient check timed out`
            : message.growth_goal_reached
              ? message.certified
                ? `goal patch certifies a ${message.patch_size}-tile translational quotient`
                : message.check_completed
                  ? message.growth_goal_criterion === "shell"
                    ? `reached shell ${message.growth_goal_target}; checked patch is not a translational quotient`
                    : `reached ${message.growth_goal_target}-tile goal; checked patch is not a translational quotient`
                  : `reached growth goal; quotient check timed out`
            : message.certified
              ? `certified ${message.patch_size}-tile patch`
              : `no ${message.patch_size}-tile patch; expanding`
      });
    }
    if (message.search_stats) latestStats = message.search_stats;
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    const tiles = snapshot?.tile_count ?? 0;
    // A resource cutoff makes recursive DFS unwind its internal stack. Those
    // removals are cleanup, not additional searched states, and plotting them
    // would make an inconclusive run look like a proof that fell to zero.
    // Certified exhaustive failure receives its explicit zero endpoint below.
    const terminalCleanupRemoval = message.type === "placement_delta"
      && message.action === "remove"
      && !!snapshot?.search_stats?.termination_reason;
    if (message.type === "placement_delta" && !terminalCleanupRemoval && tiles !== lastHistoryTileCount) {
      const point = { milliseconds: Math.round(searchElapsedMilliseconds()), tiles };
      queueHistory({ point, delta: message });
      lastHistoryTileCount = tiles;
      best = Math.max(best, tiles);
    } else if (message.type === "full_update") {
      if (lastHistoryTileCount === null || tiles !== lastHistoryTileCount) {
        const point = { milliseconds: Math.round(searchElapsedMilliseconds()), tiles };
        queueHistory({ point, snapshot });
        lastHistoryTileCount = tiles;
        best = Math.max(best, tiles);
      }
      if (
        mode.id === "gcts"
        && Array.isArray(snapshot?.placements)
        && (!bestSnapshot || tiles > (bestSnapshot.tile_count ?? 0))
      ) bestSnapshot = snapshot;
    }
    if (message.type === "full_update") terminalSnapshot = message;
    if (message.type === "finished") final = message;
    if (!final) await awaitClockBudget();
  }

  const elapsed = Math.round(searchElapsedMilliseconds());
  const learnedProgram = null;
  const finalStats = final?.search_stats ?? latestStats ?? {};
  const certificatePayloadBytes = final?.tiling_evidence?.periodic_template
    ? JSON.stringify(final.tiling_evidence.periodic_template).length
    : 0;
  const exactNoTiling = final?.result_kind === "no_tiling"
    && final?.can_tile === false
    && final?.tiling_evidence?.certified === true;
  if (exactNoTiling) {
    const point = { milliseconds: elapsed, tiles: 0, terminal: true };
    queueHistory({ point, snapshot: terminalSnapshot });
  }
  flushHistory();
  const result = {
    mode: mode.id,
    label: effectiveMode.label,
    criterion: baseConfig.criterion,
    targetValue: baseConfig.target_val,
    preprocessingMilliseconds,
    preprocessing: preparedSystem.summary,
    success: final?.success ?? false,
    tileCount: exactNoTiling
      ? 0
      : final?.tile_count ?? best,
    milliseconds: elapsed,
    points,
    stats: finalStats,
    memory: {
      learnedPayloadBytes:
        (finalStats.agent_model_payload_bytes ?? 0)
        + (finalStats.marking_payload_bytes ?? 0)
        + (finalStats.generic_geometric_nogood_payload_bytes ?? 0),
      modelParameters: finalStats.agent_model_parameter_count ?? 0,
      modelWeights: finalStats.agent_model_weight_count ?? 0,
      learnedTags: finalStats.agent_learned_tags ?? 0,
      markingClauses:
        (finalStats.marking_geometric_clauses ?? 0)
        + (finalStats.generic_geometric_nogood_clauses ?? 0),
      markingContextTokens:
        (finalStats.marking_context_tokens ?? 0)
        + (finalStats.generic_geometric_nogood_context_tokens ?? 0),
      certificatePayloadBytes,
      retainedFailedTranslationalDomains: 0,
      transientSearchCacheEntries:
        (finalStats.generic_failure_memo_states ?? 0)
        + (finalStats.isohedral_certificate_states_retained ?? 0)
        + (finalStats.uct_states ?? 0)
    },
    learnedProgram,
    reusedLearnedPatch: false,
    resultKind: final?.result_kind ?? null,
    certificatePatchSize: final?.tiling_evidence?.patch_size ?? null,
    checkedPatchSize,
    searchIncomplete: !!final?.search_incomplete,
    canTile: final?.can_tile ?? null,
    certified: !!final?.tiling_evidence?.certified,
    certificateKind: final?.tiling_evidence?.kind ?? null,
    certificateSource: final?.tiling_evidence?.source ?? null,
    certificateTargetTiles: final?.tiling_evidence?.target_tiles ?? null,
    certificateTargetShell: final?.tiling_evidence?.target_shell_depth ?? null
  };
  post(sequence, { type: "series-finished", result });
  return result;
}

self.onmessage = event => {
  const { type, sequence, config, mode: modeId, startEpochMs, additionalTimeMs } = event.data ?? {};
  if (type === "extend-time" && sequence === activeSequence) {
    stopToken.additional_time_ms = Math.max(0, Number(stopToken.additional_time_ms) || 0)
      + Math.max(0, Number(additionalTimeMs) || 0);
    stopToken.manual_pause = false;
    stopToken.resume_clock?.();
    return;
  }
  if (type === "pause" && sequence === activeSequence) {
    stopToken.manual_pause = true;
    return;
  }
  if (type === "stop") {
    stopToken.stop = true;
    stopToken.resume_clock?.();
    preparedRun = null;
    return;
  }
  if (type === "prepare" && MODES[modeId]) {
    stopToken.stop = true;
    activeSequence = sequence;
    stopToken = { stop: false, manual_pause: false, additional_time_ms: 0 };
    try {
      const run = configureMode(config, MODES[modeId]);
      const preprocessingStarted = performance.now();
      const preparedSystem = preprocessTilingSystem(run.config, tileSpecs);
      const preprocessingMilliseconds = performance.now() - preprocessingStarted;
      preparedRun = { sequence, run, preparedSystem, preprocessingMilliseconds };
      post(sequence, {
        type: "mode-ready",
        mode: modeId,
        preprocessingMilliseconds,
        preprocessing: preparedSystem.summary
      });
    } catch (error) {
      post(sequence, { type: "error", mode: modeId, error: error?.message ?? String(error) });
    }
    return;
  }
  if (type !== "go" || preparedRun?.sequence !== sequence || !Number.isFinite(startEpochMs)) return;
  const ready = preparedRun;
  preparedRun = null;
  runMode(sequence, ready.run, ready.preparedSystem, ready.preprocessingMilliseconds, startEpochMs)
    .then(result => {
      if (result && !stopToken.stop) post(sequence, { type: "finished", result });
    })
    .catch(error => post(sequence, { type: "error", mode: ready.run.mode.id, error: error?.message ?? String(error) }));
};
