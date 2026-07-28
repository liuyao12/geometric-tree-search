import { createTilingStream, tileSpecs } from "./engine.js?v=20260728-four-modes-v18";

let activeSequence = 0;
let stopToken = { stop: false };

const MODES = {
  free_range: {
    id: "free_range",
    label: "Free-range",
    strategy: "free_range",
    moveOrder: "no_brainer",
    templates: false,
    agentExhaustive: true
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
  const config = {
    ...baseConfig,
    tiling_strategy: mode.strategy,
    move_order: mode.moveOrder,
    agent_exhaustive: mode.agentExhaustive,
    greedy_no_backtrack: false,
    template_preflight: mode.templates,
    periodic_preflight: mode.templates,
    periodic_patch_unbounded: mode.id === "translational",
    periodic_patch_max_tiles: mode.id === "translational" ? null : baseConfig.periodic_patch_max_tiles,
    snapshot_every: 1,
    branch_cap: null,
    candidate_cap: null,
    exhaustive: false
  };
  const started = performance.now();
  let best = 0;
  let final = null;
  let latestStats = null;
  const points = [];
  post(sequence, { type: "series-start", mode });
  for await (const message of createTilingStream(config, tileSpecs, stopToken)) {
    if (stopToken.stop || sequence !== activeSequence) return null;
    if (message.type === "prototile_info") post(sequence, { type: "prototile-info", mode: mode.id, info: message });
    if (message.type === "translational_check") {
      post(sequence, {
        type: "mode-status",
        mode: mode.id,
        text: message.certified
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
      post(sequence, { type: "sample", mode: mode.id, point, snapshot });
    }
    if (message.type === "finished") final = message;
  }

  const elapsed = Math.round(performance.now() - started);
  if (mode.id === "isohedral" && final?.success === false) {
    const point = { milliseconds: elapsed, tiles: 0, terminal: true };
    points.push(point);
    post(sequence, { type: "sample", mode: mode.id, point, snapshot: null });
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
    resultKind: final?.result_kind ?? null,
    searchIncomplete: !!final?.search_incomplete
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
