#!/usr/bin/env node

import {
  A2_TILE_LOOPS,
  NoA2Marking,
  OnlineA2Marking,
  a2Transform,
  learnA2ClusterProposals,
  makeHexBoundary,
  solveA2Tiling,
  tileOrientations
} from "../assets/a2-tiling-engine.js";

globalThis.requestAnimationFrame ??= callback => setImmediate(callback);

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0 ? [argument.replace(/^--/, ""), "true"] : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const numberArg = (name, fallback) => {
  const value = Number(args.get(name));
  return Number.isFinite(value) ? value : fallback;
};
const tile = args.get("tile") ?? "turtle";
if (!A2_TILE_LOOPS[tile]) throw new Error(`Unknown A2 tile: ${tile}`);
const target = numberArg("target", 30), nodeLimit = numberArg("nodes", 5000);
const randomSeed = numberArg("seed", 4), radius = numberArg("radius", Math.max(50, target * 2));
const output = args.get("output") ?? "summary";
const orientation = tileOrientations(tile, A2_TILE_LOOPS[tile])[numberArg("seed-orientation", 1)];
if (!orientation) throw new Error("Seed orientation is unavailable");
const base = {
  boundary: makeHexBoundary(radius),
  seed: { loop: A2_TILE_LOOPS[tile].map(point => a2Transform(point, orientation.symmetry)) },
  tiles: [tile], maximize: true, targetPlacements: target, nodeLimit, randomSeed,
  animationDelayMs: 0, learningWarmupDepth: 0, markingStagnationNodes: Infinity
};

async function run(label, marking, clusterProposals = []) {
  const started = performance.now(), growth = [];
  let best = 0;
  const result = await solveA2Tiling({
    ...base, marking, clusterProposals,
    onEvent: event => {
      if (event.placed <= best) return;
      best = event.placed;
      const point = { milliseconds: Math.round(performance.now() - started), tiles: best };
      growth.push(point);
      if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "growth", mode: label, ...point })}\n`);
    }
  });
  const row = {
    mode: label, result: result.result, tiles: result.placements.length,
    nodes: result.stats.nodes, backtracks: result.stats.backtracks,
    milliseconds: Math.round(performance.now() - started), growth,
    encodedFailures: result.stats.encodedFailures ?? 0,
    observedFailures: result.stats.observedFailures ?? 0,
    frontierClauses: result.stats.frontierClauses ?? 0,
    frontierPrunes: result.stats.frontierPrunes ?? 0
  };
  if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "result", ...row })}\n`);
  return { row, placements: result.placements };
}

const naive = await run("naive", new NoA2Marking());
const gcts = await run("gcts", new OnlineA2Marking({ enableLocalInequalities: false }));
const proposals = learnA2ClusterProposals(gcts.placements);
const gctsRl = await run("gcts+clusters", new OnlineA2Marking({ enableLocalInequalities: false }), proposals);
const rows = [naive.row, gcts.row, gctsRl.row];
const summary = {
  configuration: { tile, target, nodeLimit, randomSeed, radius }, rows,
  learnedClusterRelations: proposals.length,
  nodeOrderingVerified: gctsRl.row.nodes < gcts.row.nodes && gcts.row.nodes < naive.row.nodes,
  wallTimeOrderingObserved: gctsRl.row.milliseconds < gcts.row.milliseconds && gcts.row.milliseconds < naive.row.milliseconds
};
if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "summary", ...summary })}\n`);
else console.log(JSON.stringify(summary, null, 2));

if (!summary.nodeOrderingVerified) process.exitCode = 2;
