#!/usr/bin/env node

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  searchPolycubeCorona,
  verifyPolycubeCoronaPatch
} from "../assets/polycube-corona-search.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const numberArg = (name, fallback, minimum = 0) => {
  const value = Number(args.get(name) ?? fallback);
  if (!Number.isFinite(value) || value < minimum) {
    throw new Error(`--${name} must be a number at least ${minimum}`);
  }
  return value;
};
const booleanArg = (name, fallback) => {
  if (!args.has(name)) return fallback;
  return !["0", "false", "no"].includes(String(args.get(name)).toLowerCase());
};

const id = args.get("id") ?? "p9-42947";
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);
const layer = Math.max(1, Math.floor(numberArg("layer", 5, 1)));
const timeMs = numberArg("time-ms", 5_000, 1);
const nodeLimit = Math.max(1, Math.floor(numberArg("nodes", Number.MAX_SAFE_INTEGER, 1)));
const nogoodLimit = Math.max(1, Math.floor(numberArg("nogood-limit", 500_000, 1)));
const budgetClock = String(args.get("budget-clock") ?? "cpu").toLowerCase();
if (!["cpu", "wall"].includes(budgetClock)) throw new Error("--budget-clock must be cpu or wall");
const symmetryNogoods = booleanArg("symmetry-nogoods", false);
const carryNogoods = booleanArg("carry-nogoods", false);
const seeds = String(args.get("seeds") ?? "0,1,2,3,4,5,6,7")
  .split(",")
  .map(Number)
  .filter(Number.isFinite)
  .map(Math.floor);
if (!seeds.length) throw new Error("--seeds must contain at least one integer");
const witnessOutput = args.get("witness-output")
  ? resolve(String(args.get("witness-output")))
  : null;
const reportOutput = args.get("report-output")
  ? resolve(String(args.get("report-output")))
  : null;

let carriedNogoods = [];
let totalNodes = 0;
let totalMilliseconds = 0;
let witness = null;
const trials = [];

process.stdout.write(`${JSON.stringify({
  type: "corona_restart_portfolio_start",
  id,
  layer,
  seeds,
  time_ms_per_seed: timeMs,
  node_limit_per_seed: nodeLimit,
  nogood_limit: nogoodLimit,
  carry_nogoods: carryNogoods,
  symmetry_nogoods: symmetryNogoods,
  budget_clock: budgetClock
})}\n`);

for (const seed of seeds) {
  const result = searchPolycubeCorona(candidate.voxels, {
    layers: layer,
    seed,
    nodeLimit,
    timeLimitMs: timeMs,
    timeBudgetMode: budgetClock,
    nogoods: true,
    symmetryNogoods,
    nogoodLimit,
    initialNogoodPlacementKeys: carryNogoods ? carriedNogoods : [],
    returnNogoods: true
  });
  totalNodes += result.nodes;
  totalMilliseconds += result.milliseconds;
  if (carryNogoods) carriedNogoods = result.nogood_clause_keys ?? carriedNogoods;
  const trial = {
    seed,
    success: result.success,
    exhausted: result.exhausted,
    stopped_by: result.stopped_by,
    nodes: result.nodes,
    milliseconds: result.milliseconds,
    maximum_depth: result.maximum_depth,
    initial_nogood_clauses: result.initial_nogood_clauses,
    final_nogood_clauses: result.nogood_clauses,
    nogood_prunes: result.nogood_prunes,
    symmetry_nogood_clauses: result.symmetry_nogood_clauses
  };
  trials.push(trial);
  process.stdout.write(`${JSON.stringify({ type: "corona_restart_trial", ...trial })}\n`);
  if (!result.success) {
    if (result.exhausted) break;
    continue;
  }
  const verification = verifyPolycubeCoronaPatch(candidate.voxels, result.corona, layer);
  if (!verification.verified) {
    throw new Error(`Radius-${layer} witness failed verification: ${verification.reason}`);
  }
  witness = result;
  if (witnessOutput) {
    mkdirSync(dirname(witnessOutput), { recursive: true });
    writeFileSync(witnessOutput, `${JSON.stringify({
      kind: "verified_polycube_corona_witness",
      candidate: id,
      layer,
      seed,
      verification,
      corona: result.corona
    }, null, 2)}\n`);
  }
  break;
}

const summary = {
  type: "corona_restart_portfolio_summary",
  id,
  layer,
  classification: witness
    ? "verified_radius_witness"
    : trials.at(-1)?.exhausted
      ? "certified_non_tiler"
      : "portfolio_incomplete",
  trials,
  total_nodes: totalNodes,
  total_milliseconds: totalMilliseconds,
  carried_nogood_clauses: carriedNogoods.length,
  witness: witness ? {
    seed: witness.seed,
    placements: witness.corona.length,
    nodes: witness.nodes,
    milliseconds: witness.milliseconds,
    output: witnessOutput
  } : null,
  warning: "A bounded incomplete restart portfolio is not a non-tiling or aperiodicity certificate."
};
if (reportOutput) {
  mkdirSync(dirname(reportOutput), { recursive: true });
  writeFileSync(reportOutput, `${JSON.stringify({
    kind: "polycube_corona_restart_portfolio",
    candidate: id,
    layer,
    seeds,
    time_ms_per_seed: timeMs,
    node_limit_per_seed: nodeLimit,
    nogood_limit: nogoodLimit,
    carry_nogoods: carryNogoods,
    symmetry_nogoods: symmetryNogoods,
    budget_clock: budgetClock,
    ...summary
  }, null, 2)}\n`);
}
process.stdout.write(`${JSON.stringify({ ...summary, report_output: reportOutput })}\n`);
