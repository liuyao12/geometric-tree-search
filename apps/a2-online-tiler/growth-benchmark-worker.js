import {
  NoA2Marking,
  OnlineA2Marking,
  learnA2ClusterProposals,
  solveA2Tiling
} from "../../assets/a2-tiling-engine.js?v=20260721-frontier-memo";

globalThis.requestAnimationFrame ??= callback => setTimeout(() => callback(performance.now()), 0);

let activeSequence = 0;
let stopToken = { stop: false };
let canceled = false;

const MODES = [
  { id: "naive", label: "Naive" },
  { id: "gcts", label: "GCTS cluster memo" },
  { id: "gcts-rl", label: "GCTS + learned clusters" }
];

const post = (sequence, payload) => {
  if (sequence === activeSequence) self.postMessage({ sequence, ...payload });
};

async function runMode(sequence, base, mode, clusterProposals = []) {
  stopToken = { stop: false };
  const marking = mode.id === "naive"
    ? new NoA2Marking()
    : new OnlineA2Marking({ maxWitnessTrials: 32, yieldEvery: 32, maxRank: base.maxRank ?? 3, enableLocalInequalities: false });
  const started = performance.now();
  const points = [];
  let best = 0;
  post(sequence, { type: "series-start", mode });
  const timeout = setTimeout(() => { stopToken.stop = true; }, base.timeLimitMs);
  const result = await solveA2Tiling({
    boundary: base.boundary,
    seed: base.seedLoop ? { tile: "seed", loop: base.seedLoop } : null,
    tiles: base.tiles,
    customTiles: base.customTiles,
    maximize: true,
    targetPlacements: base.targetPlacements,
    nodeLimit: base.nodeLimit,
    animationDelayMs: 0,
    learningWarmupDepth: 10,
    maxMarkingRevisions: Infinity,
    markingStagnationNodes: 1200,
    randomSeed: base.randomSeed,
    marking,
    clusterProposals,
    stopToken,
    onEvent: event => {
      if (event.placed <= best) return;
      best = event.placed;
      const point = { milliseconds: Math.round(performance.now() - started), tiles: best };
      points.push(point);
      post(sequence, { type: "sample", mode: mode.id, point });
    }
  });
  clearTimeout(timeout);
  const output = {
    mode: mode.id,
    label: mode.label,
    success: result.result === "yes",
    tileCount: result.placements.length,
    milliseconds: Math.round(performance.now() - started),
    points,
    stats: result.stats
  };
  post(sequence, { type: "series-finished", result: output });
  return { output, placements: result.placements };
}

async function runBenchmark(sequence, base) {
  try {
    const results = [];
    let learnedClusters = [];
    for (const mode of MODES) {
      if (canceled || sequence !== activeSequence) return;
      const run = await runMode(sequence, base, mode, mode.id === "gcts-rl" ? learnedClusters : []);
      results.push(run.output);
      if (mode.id === "gcts") learnedClusters = learnA2ClusterProposals(run.placements);
    }
    post(sequence, { type: "finished", results, learnedClusterCount: learnedClusters.length });
  } catch (error) {
    post(sequence, { type: "error", error: error?.message ?? String(error) });
  }
}

self.onmessage = event => {
  const { type, sequence, config } = event.data ?? {};
  if (type === "stop") {
    canceled = true;
    stopToken.stop = true;
    return;
  }
  if (type !== "start") return;
  stopToken.stop = true;
  activeSequence = sequence;
  canceled = false;
  stopToken = { stop: false };
  runBenchmark(sequence, config);
};
