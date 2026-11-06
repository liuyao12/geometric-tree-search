#!/usr/bin/env node

import {
  A2_TILE_LOOPS,
  FixedTurtleMarking,
  NoA2Marking,
  OnlineA2Marking,
  a2Transform,
  makeHexBoundary,
  solveA2Tiling,
  tileOrientations
} from "../assets/a2-tiling-engine.js";

globalThis.requestAnimationFrame ??= callback => setImmediate(callback);

const rawArgs = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));

const numberArg = (name, fallback) => {
  const value = Number(rawArgs.get(name));
  return Number.isFinite(value) ? value : fallback;
};
const stringArg = (name, fallback) => rawArgs.get(name) ?? fallback;

if (rawArgs.has("help")) {
  console.log(`Headless A2/GCTS runner

Usage:
  node scripts/run-a2-headless.mjs [options]

Options:
  --mode=growth|region          Search outward from a seed or tile a boundary
  --tile=turtle|hat|mixed       Allowed built-in tile set (default: turtle)
  --marking=online|cluster|none|fixed-turtle
  --target=N                    Growth target (default: 100)
  --nodes=N                     Node budget (default: 10000)
  --radius=N                    A2 hexagonal search boundary
  --seed=N                      Deterministic branch-order seed (default: 4)
  --seed-orientation=N          Initial tile orientation (default: 1)
  --warmup=N                    Depth before geometric encoding (default: 0)
  --revisions=N                 Maximum learned revisions
  --stagnation=N                Nodes without growth before witness replacement
  --witness-trials=N            Witness candidates per update (default: 128)
  --max-rank=3|6                Allow an independent second channel block
  --output=summary|ndjson       Pretty final report or one JSON object per event
`);
  process.exit(0);
}

const tileName = stringArg("tile", "turtle");
const tiles = tileName === "mixed" ? ["hat", "turtle"] : [tileName];
for (const tile of tiles) {
  if (!A2_TILE_LOOPS[tile]) throw new Error(`Unknown built-in tile: ${tile}`);
}

const mode = stringArg("mode", "growth");
if (!["growth", "region"].includes(mode)) throw new Error(`Unknown mode: ${mode}`);
const markingName = stringArg("marking", "online");
const output = stringArg("output", "summary");
if (!["summary", "ndjson"].includes(output)) throw new Error(`Unknown output mode: ${output}`);

const targetPlacements = numberArg("target", 100);
const nodeLimit = numberArg("nodes", 10_000);
const radius = numberArg("radius", Math.max(50, targetPlacements * 2));
const randomSeed = numberArg("seed", 4);
const seedOrientation = numberArg("seed-orientation", 1);
const learningWarmupDepth = numberArg("warmup", 0);
const maxMarkingRevisions = numberArg("revisions", Number.POSITIVE_INFINITY);
const markingStagnationNodes = numberArg("stagnation", Number.POSITIVE_INFINITY);
const maxWitnessTrials = numberArg("witness-trials", 128);
const maxRank = numberArg("max-rank", 3);

const marking = markingName === "none"
  ? new NoA2Marking()
  : markingName === "fixed-turtle"
    ? new FixedTurtleMarking(numberArg("extension", 1))
    : new OnlineA2Marking({ maxWitnessTrials, yieldEvery: maxWitnessTrials, maxRank, enableLocalInequalities: markingName !== "cluster" });

if (!["online", "cluster", "none", "fixed-turtle"].includes(markingName)) {
  throw new Error(`Unknown marking: ${markingName}`);
}
if (markingName === "fixed-turtle" && tiles.some(tile => tile !== "turtle")) {
  throw new Error("The fixed Turtle marking can only be used with --tile=turtle");
}

const placementSetKey = placements => placements.map(placement => placement.id).sort().join(";");
const trialKey = event => `${placementSetKey(event.placements)}=>${event.candidate.id}`;
const failedTrials = new Map();
const trialCounts = new Map();
const typeCounts = new Map();
const trace = [];
let sequence = 0;
let trials = 0;
let repeatedTrials = 0;
let retracedFailures = 0;
let exactConsecutiveRetraces = 0;
let lastTrialKey = null;

const compactEvent = event => {
  sequence++;
  typeCounts.set(event.type, (typeCounts.get(event.type) ?? 0) + 1);
  const row = {
    sequence,
    type: event.type,
    nodes: event.nodes,
    backtracks: event.backtracks,
    depth: event.placed,
    revision: event.marking?.revision ?? 0,
    prunes: event.marking?.prunes ?? 0
  };

  if (event.choice != null) row.choice = event.choice;
  if (event.candidate) {
    const key = trialKey(event);
    const seen = trialCounts.get(key) ?? 0;
    const priorFailure = failedTrials.get(key);
    trialCounts.set(key, seen + 1);
    trials++;
    if (seen) repeatedTrials++;
    if (priorFailure) retracedFailures++;
    if (key === lastTrialKey && priorFailure) exactConsecutiveRetraces++;
    lastTrialKey = key;
    Object.assign(row, {
      candidate: event.candidate.id,
      stateKey: key,
      repeatedTrial: seen > 0,
      retracedFailure: Boolean(priorFailure),
      firstFailureSequence: priorFailure?.sequence ?? null
    });
  }
  if (event.removed) {
    const key = `${placementSetKey(event.placements)}=>${event.removed.id}`;
    if (!failedTrials.has(key)) failedTrials.set(key, { sequence, revision: row.revision });
    row.removed = event.removed.id;
    row.stateKey = key;
  }
  if (event.update) {
    row.update = {
      revision: event.update.revision ?? null,
      reason: event.update.reason ?? null,
      pending: event.update.pending ?? false,
      branchDepth: event.update.branchDepth ?? null,
      subtreeSites: event.update.subtreeSites ?? null,
      witness: event.update.sourceGlobal ?? null
    };
  }
  if (event.reencoding) {
    row.reencoding = {
      targetFailure: event.reencoding.targetFailure,
      preservedFailures: event.reencoding.preservedFailures,
      attempts: event.reencoding.attempts
    };
  }
  if (output === "ndjson") process.stdout.write(`${JSON.stringify(row)}\n`);
  if (["trial", "backtrack", "learn", "learning-skip", "marking-reencoded", "finished"].includes(event.type)) trace.push(row);
};

const started = performance.now();
const solveOptions = {
  boundary: makeHexBoundary(radius),
  tiles,
  maximize: mode === "growth",
  targetPlacements,
  nodeLimit,
  learningWarmupDepth,
  maxMarkingRevisions,
  markingStagnationNodes,
  randomSeed,
  marking,
  onEvent: compactEvent
};
if (mode === "growth") {
  const orientation = tileOrientations(tiles[0], A2_TILE_LOOPS[tiles[0]])[seedOrientation];
  if (!orientation) throw new Error(`Seed orientation ${seedOrientation} is unavailable for ${tiles[0]}`);
  solveOptions.seed = { loop: A2_TILE_LOOPS[tiles[0]].map(point => a2Transform(point, orientation.symmetry)) };
}

const result = await solveA2Tiling(solveOptions);
const summary = {
  configuration: {
    mode,
    tiles,
    marking: markingName,
    targetPlacements,
    nodeLimit,
    radius,
    randomSeed,
    seedOrientation,
    learningWarmupDepth,
    maxMarkingRevisions: Number.isFinite(maxMarkingRevisions) ? maxMarkingRevisions : "unbounded",
    markingStagnationNodes: Number.isFinite(markingStagnationNodes) ? markingStagnationNodes : "disabled",
    maxRank
  },
  result: result.result,
  placements: result.placements.length,
  nodes: result.stats.nodes,
  backtracks: result.stats.backtracks,
  marking: {
    revisions: result.stats.revision ?? 0,
    rank: result.stats.rank ?? 0,
    rankExpansions: result.stats.rankExpansions ?? 0,
    observedFailures: result.stats.observedFailures ?? 0,
    encodedFailures: result.stats.encodedFailures ?? 0,
    pendingFailures: result.stats.pendingFailures ?? 0,
    prunes: result.stats.prunes ?? 0,
    supportSites: result.stats.supportSites ?? 0,
    geometricClauses: result.stats.geometricClauses ?? 0,
    geometricPrunes: result.stats.geometricPrunes ?? 0,
    frontierClauses: result.stats.frontierClauses ?? 0,
    frontierPrunes: result.stats.frontierPrunes ?? 0
  },
  searchMemo: {
    failures: result.stats.memoizedBranches ?? 0,
    prunes: result.stats.exactMemoPrunes ?? 0
  },
  audit: {
    trials,
    uniqueTrialStates: trialCounts.size,
    repeatedTrials,
    retracedFailures,
    exactConsecutiveRetraces,
    failureStates: failedTrials.size,
    eventCounts: Object.fromEntries(typeCounts)
  },
  milliseconds: Math.round(performance.now() - started)
};

if (output === "ndjson") {
  process.stdout.write(`${JSON.stringify({ type: "summary", ...summary })}\n`);
} else {
  console.log(JSON.stringify(summary, null, 2));
  if (retracedFailures) {
    console.log("\nFirst retraced failed states:");
    console.table(trace.filter(event => event.retracedFailure).slice(0, 12).map(event => ({
      sequence: event.sequence,
      firstFailure: event.firstFailureSequence,
      nodes: event.nodes,
      depth: event.depth,
      revision: event.revision,
      candidate: event.candidate
    })));
  }
}
