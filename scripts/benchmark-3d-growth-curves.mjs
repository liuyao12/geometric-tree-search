#!/usr/bin/env node

import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0 ? [argument.replace(/^--/, ""), "true"] : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const numberArg = (name, fallback) => {
  const value = Number(args.get(name));
  return Number.isFinite(value) ? value : fallback;
};
const modeKey = args.get("mode") ?? "1_cross", target = numberArg("target", 8);
const output = args.get("output") ?? "summary";
const base = {
  mode_key: modeKey,
  custom_system: { name: `Growth benchmark ${modeKey}`, figure_refs: [`${modeKey}::0`], polycubes: [], polycube_lattice: "z3" },
  polycube_lattice: "z3", criterion: "count", target_val: target,
  exhaustive: false, include_mirrors: false, snapshot_every: 1,
  face_order: args.get("face-order") ?? "mrv", branch_cap: null,
  node_limit: numberArg("nodes", 3000), candidate_cap: null,
  time_limit_ms: numberArg("time-ms", 10000), ui_yield_interval_ms: 1000
};
const modes = [
  { id: "naive", online_failure_marking: false, move_order: "coverage", template_preflight: false, agent_exhaustive: false },
  { id: "gcts", online_failure_marking: true, online_pair_marking: false, move_order: "coverage", template_preflight: false, agent_exhaustive: false },
  { id: "gcts+rl-clusters", online_failure_marking: true, online_pair_marking: false, move_order: "rl", template_preflight: true, periodic_tile_count: 2, agent_exhaustive: true }
];

async function run(mode) {
  const started = performance.now(), growth = [];
  let best = 0, finished = null;
  for await (const message of createTilingStream({ ...base, ...mode }, tileSpecs, { stop: false })) {
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    if ((message.type === "node_snapshot" || message.type === "full_update") && (snapshot?.tile_count ?? 0) > best) {
      best = snapshot.tile_count;
      const point = { milliseconds: Math.round(performance.now() - started), tiles: best };
      growth.push(point);
      if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "growth", mode: mode.id, ...point })}\n`);
    }
    if (message.type === "finished") finished = message;
  }
  const row = {
    mode: mode.id, success: finished?.success ?? false,
    tiles: finished?.tile_count ?? best, milliseconds: Math.round(performance.now() - started), growth,
    branchChoices: finished?.search_stats?.branch_choices_visited ?? 0,
    backtracks: finished?.search_stats?.backtracks ?? 0,
    encodedFailures: finished?.search_stats?.marking_failures ?? 0,
    observedFailures: finished?.search_stats?.marking_observed_failures ?? 0,
    pendingFailures: finished?.search_stats?.marking_pending_failures ?? 0,
    geometricPrunes: finished?.search_stats?.marking_geometric_prunes ?? 0
  };
  if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "result", ...row })}\n`);
  return row;
}

const rows = [];
for (const mode of modes) rows.push(await run(mode));
const summary = {
  configuration: { modeKey, target, nodeLimit: base.node_limit, timeLimitMs: base.time_limit_ms }, rows,
  branchOrderingVerified: rows[2].branchChoices < rows[1].branchChoices && rows[1].branchChoices < rows[0].branchChoices,
  wallTimeOrderingObserved: rows[2].milliseconds < rows[1].milliseconds && rows[1].milliseconds < rows[0].milliseconds,
  completeFailureEncoding: rows[1].pendingFailures === 0 && rows[1].encodedFailures === rows[1].observedFailures
};
if (output === "ndjson") process.stdout.write(`${JSON.stringify({ type: "summary", ...summary })}\n`);
else console.log(JSON.stringify(summary, null, 2));
if (!summary.branchOrderingVerified || !summary.completeFailureEncoding) process.exitCode = 2;
