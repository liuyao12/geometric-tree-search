import { createTilingStream, tileSpecs } from "./engine.js?v=20260727-periodic-colors-v15";

let activeSequence = 0;
let stopToken = { stop: false };

const MODES = [
  { id: "coverage", label: "Generic", strategy: "generic", moveOrder: "coverage", templates: false, agentExhaustive: false },
  { id: "isohedral", label: "Isohedral", strategy: "isohedral", moveOrder: "isohedral", templates: true, agentExhaustive: false },
  { id: "auto", label: "Automatic", strategy: "auto", moveOrder: "balanced", templates: true, agentExhaustive: true }
];

const post = (sequence, payload) => {
  if (sequence === activeSequence) self.postMessage({ sequence, ...payload });
};

async function runMode(sequence, baseConfig, mode) {
  const config = {
    ...baseConfig,
    tiling_strategy: mode.strategy,
    move_order: mode.moveOrder,
    agent_exhaustive: mode.agentExhaustive,
    template_preflight: mode.templates,
    periodic_tile_count: mode.templates ? 2 : 0,
    snapshot_every: 1,
    branch_cap: null,
    candidate_cap: null,
    exhaustive: false
  };
  const started = performance.now();
  let best = 0, final = null, latestStats = null;
  const points = [];
  post(sequence, { type: "series-start", mode });
  for await (const message of createTilingStream(config, tileSpecs, stopToken)) {
    if (stopToken.stop || sequence !== activeSequence) return null;
    if (message.search_stats) latestStats = message.search_stats;
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    const tiles = snapshot?.tile_count ?? 0;
    if ((message.type === "full_update" || message.type === "node_snapshot") && tiles > best) {
      best = tiles;
      const point = { milliseconds: Math.round(performance.now() - started), tiles };
      points.push(point);
      post(sequence, { type: "sample", mode: mode.id, point });
    }
    if (message.type === "finished") final = message;
  }
  const result = {
    mode: mode.id,
    label: mode.label,
    success: final?.success ?? false,
    tileCount: final?.tile_count ?? best,
    milliseconds: Math.round(performance.now() - started),
    points,
    stats: final?.search_stats ?? latestStats
  };
  post(sequence, { type: "series-finished", result });
  return result;
}

async function runBenchmark(sequence, config) {
  try {
    const results = [];
    for (const mode of MODES) {
      if (stopToken.stop || sequence !== activeSequence) return;
      const result = await runMode(sequence, config, mode);
      if (!result) return;
      results.push(result);
    }
    post(sequence, { type: "finished", results });
  } catch (error) {
    post(sequence, { type: "error", error: error?.message ?? String(error) });
  }
}

self.onmessage = event => {
  const { type, sequence, config } = event.data ?? {};
  if (type === "stop") {
    stopToken.stop = true;
    return;
  }
  if (type !== "start") return;
  stopToken.stop = true;
  activeSequence = sequence;
  stopToken = { stop: false };
  runBenchmark(sequence, config);
};
