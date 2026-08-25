#!/usr/bin/env node

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  enumeratePolycubeCoronaPlacements,
  searchPolycubeCorona
} from "../assets/polycube-corona-search.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const integerArg = (name, fallback, minimum = 0) => {
  const value = Number(args.get(name) ?? fallback);
  if (!Number.isInteger(value) || value < minimum) {
    throw new Error(`--${name} must be an integer at least ${minimum}`);
  }
  return value;
};
const booleanArg = (name, fallback = false) => {
  const raw = args.get(name);
  if (raw === undefined) return fallback;
  if (raw === "true") return true;
  if (raw === "false") return false;
  throw new Error(`--${name} must be true or false`);
};

const id = args.get("id") ?? "p10-052588";
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);
const layer = integerArg("layer", 3, 1);
const nodeLimit = integerArg("node-limit", 1_000_000, 1);
const timeLimitMs = integerArg("time-ms", 30_000, 1);
const nogoods = booleanArg("nogoods");
const conflictBackjumping = booleanArg("conflict-backjumping");
const clauseReportPath = args.get("clause-report")
  ? resolve(args.get("clause-report"))
  : null;
if (!clauseReportPath) throw new Error("--clause-report is required");
const outputPath = args.get("output") ? resolve(args.get("output")) : null;

const rawReport = JSON.parse(readFileSync(clauseReportPath, "utf8"));
const rawClauses = rawReport.learned_clauses ?? rawReport.clauses ?? rawReport;
if (!Array.isArray(rawClauses)) {
  throw new Error("Clause report must contain learned_clauses or clauses");
}
const clauses = rawClauses.map((rawClause, index) => {
  if (!Array.isArray(rawClause) || !rawClause.length) {
    throw new Error(`Clause ${index} must be a nonempty array`);
  }
  return [...new Set(rawClause.map(String))].sort();
});
const placementByKey = new Map(
  enumeratePolycubeCoronaPlacements(candidate.voxels, layer)
    .map(placement => [placement.key, placement])
);

const results = [];
for (let index = 0; index < clauses.length; index += 1) {
  const clause = clauses[index];
  const missingPlacementKeys = clause.filter(key => !placementByKey.has(key));
  if (missingPlacementKeys.length) {
    results.push({
      index,
      clause_size: clause.length,
      verified: false,
      status: "unknown_placement",
      missing_placement_keys: missingPlacementKeys,
      nodes: 0,
      milliseconds: 0
    });
    continue;
  }
  let replay;
  try {
    replay = searchPolycubeCorona(candidate.voxels, {
      layers: layer,
      fixedPlacements: clause.map(key => placementByKey.get(key)),
      nodeLimit,
      timeLimitMs,
      timeBudgetMode: "cpu",
      nogoods,
      conflictBackjumping
    });
  } catch (error) {
    results.push({
      index,
      clause_size: clause.length,
      verified: false,
      status: "invalid_fixed_patch",
      reason: error instanceof Error ? error.message : String(error),
      nodes: 0,
      milliseconds: 0
    });
    continue;
  }
  results.push({
    index,
    clause_size: clause.length,
    verified: replay.exhausted,
    status: replay.exhausted
      ? "exact_obstruction"
      : replay.success
        ? "counterexample_extension"
        : "incomplete",
    nodes: replay.nodes,
    milliseconds: replay.milliseconds,
    stopped_by: replay.stopped_by,
    counterexample_placements: replay.success ? replay.corona.length : null
  });
}

const verifiedClauses = results.filter(result => result.verified).length;
const failedClauses = results.filter(result => result.status === "counterexample_extension"
  || result.status === "unknown_placement"
  || result.status === "invalid_fixed_patch").length;
const incompleteClauses = results.filter(result => result.status === "incomplete").length;
const summary = {
  kind: "polycube_corona_clause_replay",
  candidate: id,
  layer,
  clause_report: clauseReportPath,
  classification: failedClauses
    ? "failed"
    : incompleteClauses
      ? "incomplete"
      : "verified",
  clauses: clauses.length,
  verified_clauses: verifiedClauses,
  failed_clauses: failedClauses,
  incomplete_clauses: incompleteClauses,
  total_nodes: results.reduce((sum, result) => sum + result.nodes, 0),
  total_milliseconds: results.reduce((sum, result) => sum + result.milliseconds, 0),
  node_limit_per_clause: nodeLimit,
  time_limit_ms_per_clause: timeLimitMs,
  nogoods,
  conflict_backjumping: conflictBackjumping,
  results
};
if (outputPath) writeFileSync(outputPath, `${JSON.stringify(summary, null, 2)}\n`);
process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
if (summary.classification === "failed") process.exitCode = 1;
