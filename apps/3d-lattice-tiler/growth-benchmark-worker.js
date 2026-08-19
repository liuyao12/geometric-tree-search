import { createTilingStream, tileSpecs } from "./engine.js?v=20260818-checkpoint-screen-v68";
import {
  normalizeProposalProgram,
  proposalProgramFromPatchSnapshot
} from "./proposal-learner.js?v=20260817-generation-band-v31";

let activeSequence = 0;
let stopToken = { stop: false };

const MODES = {
  free_range: {
    id: "free_range",
    label: "Free-range · balanced",
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
    label: "Proof search · unbanded",
    strategy: "free_range",
    moveOrder: "balanced",
    templates: false,
    agentExhaustive: true,
    proof: true
  },
  learning: {
    id: "learning",
    label: "Learning Free-range",
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
  const priorProgram = mode.id === "learning" && baseConfig.proposal_program
    ? normalizeProposalProgram(baseConfig.proposal_program)
    : null;
  const config = {
    ...baseConfig,
    tiling_strategy: mode.strategy,
    move_order: priorProgram
      ? "proposal"
      : mode.moveOrder,
    proposal_program: priorProgram,
    agent_exhaustive: mode.agentExhaustive,
    greedy_no_backtrack: false,
    template_preflight: mode.templates,
    periodic_preflight: mode.templates,
    periodic_patch_unbounded: mode.id === "translational",
    periodic_patch_max_tiles: mode.id === "translational" ? null : baseConfig.periodic_patch_max_tiles,
    snapshot_every: 1,
    placement_details: mode.id === "learning",
    branch_cap: null,
    candidate_cap: null,
    forced_move_layer_lag_cap: mode.proof ? 0 : baseConfig.forced_move_layer_lag_cap,
    generic_failure_memo: mode.proof,
    generic_geometric_nogood: false,
    seeded_tie_breaks: !!mode.proof,
    generic_periodic_certificate: !!mode.proof,
    generic_periodic_certificate_check_new_maximum: !!mode.proof,
    generic_periodic_certificate_time_limit_ms: 5000,
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
  post(sequence, { type: "series-start", mode });
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
    if ((message.type === "full_update" || message.type === "node_snapshot") && tiles > best) {
      best = tiles;
      const point = { milliseconds: Math.round(performance.now() - started), tiles };
      points.push(point);
      if (mode.id === "learning" && Array.isArray(snapshot?.placements)) bestSnapshot = snapshot;
      post(sequence, { type: "sample", mode: mode.id, point, snapshot });
    }
    if (message.type === "full_update") terminalSnapshot = message;
    if (message.type === "finished") final = message;
  }

  const elapsed = Math.round(performance.now() - started);
  const learnedProgram = mode.id === "learning" && bestSnapshot?.placements?.length > 1
    ? proposalProgramFromPatchSnapshot(baseConfig, bestSnapshot, priorProgram)
    : priorProgram;
  if (mode.id === "isohedral" && final?.success === false) {
    const point = { milliseconds: elapsed, tiles: 0, terminal: true };
    points.push(point);
    post(sequence, { type: "sample", mode: mode.id, point, snapshot: terminalSnapshot });
  }
  const result = {
    mode: mode.id,
    label: mode.label,
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
    certificateTargetTiles: final?.tiling_evidence?.target_tiles ?? null
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
