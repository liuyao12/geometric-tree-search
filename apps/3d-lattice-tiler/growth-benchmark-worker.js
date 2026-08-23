import { createTilingStream, tileSpecs } from "./engine.js?v=20260823-polycube10-v176";
import {
  normalizeProposalProgram,
  proposalProgramFromPatchSnapshot
} from "./proposal-learner.js?v=20260817-generation-band-v31";

let activeSequence = 0;
let stopToken = { stop: false };
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
    strategy: "learning_free_range",
    moveOrder: "agent",
    templates: false,
    agentExhaustive: true
  },
  translational: {
    id: "translational",
    label: "Translational",
    strategy: "translational",
    moveOrder: "balanced",
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

async function runMode(sequence, baseConfig, mode) {
  const shellSearch = baseConfig.criterion === "shell";
  const effectiveMode = shellSearch && mode.proof
    ? { ...mode, label: `${mode.label.replace(/ · .*$/u, "")} · complete shell` }
    : mode;
  const priorProgram = mode.id === "gcts" && baseConfig.proposal_program
    ? normalizeProposalProgram(baseConfig.proposal_program)
    : null;
  const config = {
    ...baseConfig,
    tiling_strategy: mode.strategy,
    move_order: priorProgram
      ? "proposal"
      : shellSearch && mode.proof ? "shell" : mode.moveOrder,
    proposal_program: priorProgram,
    agent_exhaustive: mode.agentExhaustive,
    greedy_no_backtrack: false,
    template_preflight: mode.templates,
    periodic_preflight: mode.templates,
    periodic_patch_unbounded: mode.id === "translational",
    periodic_patch_max_tiles: mode.id === "translational" ? null : baseConfig.periodic_patch_max_tiles,
    snapshot_every: 1,
    placement_details: mode.id === "gcts",
    branch_cap: null,
    candidate_cap: null,
    forced_move_layer_lag_cap: mode.proof ? 0 : baseConfig.forced_move_layer_lag_cap,
    generic_connected_patch_enumeration: !!mode.proof && !shellSearch,
    generic_complete_shell_enumeration: !!mode.proof && shellSearch,
    generic_failure_memo: mode.proof,
    generic_failure_memo_symmetry: shellSearch ? "rigid" : "fixed",
    generic_geometric_nogood: !!mode.nogood && !shellSearch,
    generic_geometric_nogood_max_clauses: 20000,
    generic_geometric_nogood_index: true,
    generic_geometric_nogood_activation_failure_states: mode.nogood ? 25 : 0,
    seeded_tie_breaks: !!mode.proof,
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
    exhaustive: !!mode.proof
  };
  const started = performance.now();
  let best = 0;
  let final = null;
  let latestStats = null;
  let bestSnapshot = null;
  let terminalSnapshot = null;
  let checkedPatchSize = 0;
  const points = [];
  let lastHistoryTileCount = null;
  let lastHistoryFlushAt = performance.now();
  let pendingHistorySamples = [];
  const flushHistory = () => {
    if (!pendingHistorySamples.length) return;
    post(sequence, { type: "sample-batch", samples: pendingHistorySamples });
    pendingHistorySamples = [];
    lastHistoryFlushAt = performance.now();
  };
  const queueHistory = sample => {
    points.push(sample.point);
    pendingHistorySamples.push(sample);
    if (
      pendingHistorySamples.length >= HISTORY_BATCH_LIMIT
      || performance.now() - lastHistoryFlushAt >= HISTORY_BATCH_INTERVAL_MS
    ) flushHistory();
  };
  post(sequence, { type: "series-start", mode: effectiveMode });
  for await (const message of createTilingStream(config, tileSpecs, stopToken)) {
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
            : message.certified
              ? `certified ${message.patch_size}-tile patch`
              : `no ${message.patch_size}-tile patch; expanding`
      });
    }
    if (message.search_stats) latestStats = message.search_stats;
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    const tiles = snapshot?.tile_count ?? 0;
    if (message.type === "placement_delta" && tiles !== lastHistoryTileCount) {
      const point = { milliseconds: Math.round(performance.now() - started), tiles };
      queueHistory({ point, delta: message });
      lastHistoryTileCount = tiles;
      best = Math.max(best, tiles);
    } else if (message.type === "full_update") {
      if (lastHistoryTileCount === null || tiles !== lastHistoryTileCount) {
        const point = { milliseconds: Math.round(performance.now() - started), tiles };
        queueHistory({ point, snapshot });
        lastHistoryTileCount = tiles;
        best = Math.max(best, tiles);
      }
      if (
        mode.id === "gcts"
        && Array.isArray(snapshot?.placements)
        && (!bestSnapshot || tiles >= (bestSnapshot.tile_count ?? 0))
      ) bestSnapshot = snapshot;
    }
    if (message.type === "full_update") terminalSnapshot = message;
    if (message.type === "finished") final = message;
  }

  const elapsed = Math.round(performance.now() - started);
  const learnedProgram = mode.id === "gcts" && bestSnapshot?.placements?.length > 1
    ? proposalProgramFromPatchSnapshot(baseConfig, bestSnapshot, priorProgram)
    : priorProgram;
  if (mode.id === "isohedral" && final?.success === false) {
    const point = { milliseconds: elapsed, tiles: 0, terminal: true };
    queueHistory({ point, snapshot: terminalSnapshot });
  }
  flushHistory();
  const result = {
    mode: mode.id,
    label: effectiveMode.label,
    criterion: baseConfig.criterion,
    targetValue: baseConfig.target_val,
    success: final?.success ?? false,
    tileCount: mode.id === "isohedral" && final?.success === false
      ? 0
      : final?.tile_count ?? best,
    milliseconds: elapsed,
    points,
    stats: final?.search_stats ?? latestStats,
    learnedProgram,
    reusedLearnedPatch: !!priorProgram,
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
  const { type, sequence, config, mode: modeId } = event.data ?? {};
  if (type === "stop") {
    stopToken.stop = true;
    return;
  }
  if (type !== "start" || !MODES[modeId]) return;
  stopToken.stop = true;
  activeSequence = sequence;
  stopToken = { stop: false };
  runMode(sequence, config, MODES[modeId])
    .then(result => {
      if (result && !stopToken.stop) post(sequence, { type: "finished", result });
    })
    .catch(error => post(sequence, { type: "error", mode: modeId, error: error?.message ?? String(error) }));
};
