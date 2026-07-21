#!/usr/bin/env node

import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

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
const stringArg = (name, fallback) => args.get(name) ?? fallback;
const booleanArg = (name, fallback) => {
  if (!args.has(name)) return fallback;
  return !["0", "false", "no"].includes(args.get(name));
};

const mode = stringArg("mode", "1_cross");
const marking = booleanArg("marking", true);
const moveOrder = stringArg("move-order", "coverage");
const output = stringArg("output", "summary");
const config = {
  mode_key: mode,
  custom_system: { name: `Headless ${mode}`, figure_refs: [`${mode}::0`], polycubes: [], polycube_lattice: "z3" },
  polycube_lattice: "z3",
  criterion: "count",
  target_val: numberArg("target", 8),
  exhaustive: false,
  include_mirrors: false,
  snapshot_every: numberArg("snapshot-every", 1),
  move_order: moveOrder,
  face_order: stringArg("face-order", "mrv"),
  branch_cap: null,
  node_limit: numberArg("nodes", 3000),
  candidate_cap: null,
  time_limit_ms: numberArg("time-ms", 10000),
  ui_yield_interval_ms: 1000,
  online_failure_marking: marking,
  agent_exhaustive: booleanArg("agent-exhaustive", moveOrder === "rl"),
  template_preflight: booleanArg("clusters", moveOrder === "rl"),
  periodic_tile_count: 2
};

const eventCounts = new Map(), growth = [], updates = [];
let finished = null, latestStats = null, best = 0;
const started = performance.now();
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  eventCounts.set(message.type, (eventCounts.get(message.type) ?? 0) + 1);
  if (message.search_stats) latestStats = message.search_stats;
  const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
  if ((message.type === "full_update" || message.type === "node_snapshot") && (snapshot?.tile_count ?? 0) > best) {
    best = snapshot.tile_count;
    const point = { milliseconds: Math.round(performance.now() - started), tiles: best };
    growth.push(point);
    if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "growth", ...point })}\n`);
  }
  if (message.type === "marking_update") updates.push({
    revision: message.revision,
    failures: message.failures,
    observedFailures: message.observed_failures,
    pendingFailures: message.pending_failures,
    clauses: message.search_stats?.marking_geometric_clauses ?? 0,
    geometricPrunes: message.search_stats?.marking_geometric_prunes ?? 0
  });
  if (message.type === "finished") finished = message;
}

const summary = {
  configuration: { mode, target: config.target_val, marking, moveOrder, agentExhaustive: config.agent_exhaustive, clusters: config.template_preflight },
  success: finished?.success ?? false,
  tileCount: finished?.tile_count ?? best,
  growth,
  stats: finished?.search_stats ?? latestStats,
  markingUpdates: updates,
  eventCounts: Object.fromEntries(eventCounts),
  milliseconds: Math.round(performance.now() - started)
};
if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "summary", ...summary })}\n`);
else console.log(JSON.stringify(summary, null, 2));
