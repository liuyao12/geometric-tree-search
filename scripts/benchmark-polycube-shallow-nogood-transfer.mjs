#!/usr/bin/env node

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
const numberArg = (name, fallback) => {
  const value = Number(args.get(name));
  return Number.isFinite(value) ? value : fallback;
};
const id = args.get("id") ?? "p9-42947";
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);
const trainingOuterLayer = Math.max(1, Math.floor(numberArg("training-outer-layer", 1)));
const trainingInnerLayer = Math.max(
  trainingOuterLayer + 1,
  Math.floor(numberArg("training-inner-layer", trainingOuterLayer + 1))
);
const trainingTimeMs = Math.max(1, numberArg("training-time-ms", 10_000));
const trainingNodes = Math.max(1, Math.floor(numberArg("training-nodes", 10_000_000)));
const innerTimeMs = Math.max(1, numberArg("inner-time-ms", 5_000));
const innerNodes = Math.max(1, Math.floor(numberArg("inner-nodes", 1_000_000)));
const targetLayer = Math.max(trainingInnerLayer, Math.floor(numberArg("target-layer", 4)));
const targetTimeMs = Math.max(1, numberArg("target-time-ms", 30_000));
const targetNodes = Math.max(1, Math.floor(numberArg("target-nodes", 20_000_000)));
const seed = Math.floor(numberArg("seed", 3));
const nogoodLimit = Math.max(1, Math.floor(numberArg("nogood-limit", 500_000)));

let continuationChecks = 0;
let extendableStates = 0;
let obstructedStates = 0;
let incompleteStates = 0;
const training = searchPolycubeCorona(candidate.voxels, {
  layers: trainingOuterLayer,
  seed,
  nodeLimit: trainingNodes,
  timeLimitMs: trainingTimeMs,
  nogoods: true,
  nogoodLimit,
  returnNogoods: true,
  acceptSolution(solution) {
    continuationChecks += 1;
    const continuation = searchPolycubeCorona(candidate.voxels, {
      layers: trainingInnerLayer,
      seed,
      fixedPlacements: solution,
      nodeLimit: innerNodes,
      timeLimitMs: innerTimeMs,
      nogoods: true,
      nogoodLimit
    });
    if (continuation.success) {
      extendableStates += 1;
      return false;
    }
    if (!continuation.exhausted) {
      incompleteStates += 1;
      return true;
    }
    obstructedStates += 1;
    const clause = continuation.fixed_obstruction_nogood?.fixed_placement_keys;
    return clause?.length
      ? { accept: false, nogood_placement_keys: clause }
      : false;
  }
});
if (incompleteStates) throw new Error("Shallow continuation training was incomplete");
const learnedClauses = training.nogood_clause_keys ?? [];

const runTarget = (initialNogoodPlacementKeys = []) => searchPolycubeCorona(candidate.voxels, {
  layers: targetLayer,
  seed,
  nodeLimit: targetNodes,
  timeLimitMs: targetTimeMs,
  nogoods: true,
  nogoodLimit,
  initialNogoodPlacementKeys,
  returnNogoods: true
});
const baseline = runTarget();
const transferred = runTarget(learnedClauses);
for (const [label, result] of [["baseline", baseline], ["transferred", transferred]]) {
  if (!result.success) continue;
  const verification = verifyPolycubeCoronaPatch(candidate.voxels, result.corona, targetLayer);
  if (!verification.verified) throw new Error(`${label} target witness failed verification: ${verification.reason}`);
}

const targetSummary = result => ({
  success: result.success,
  exhausted: result.exhausted,
  stopped_by: result.stopped_by,
  nodes: result.nodes,
  dead_ends: result.dead_ends,
  placements: result.corona?.length ?? null,
  milliseconds: result.milliseconds,
  initial_nogood_clauses: result.initial_nogood_clauses,
  final_nogood_clauses: result.nogood_clauses,
  nogood_prunes: result.nogood_prunes,
  maximum_depth: result.maximum_depth
});
process.stdout.write(`${JSON.stringify({
  type: "shallow_nogood_transfer_benchmark",
  id,
  seed,
  training: {
    outer_layer: trainingOuterLayer,
    inner_layer: trainingInnerLayer,
    configured_time_ms: trainingTimeMs,
    nodes: training.nodes,
    milliseconds: training.milliseconds,
    continuation_checks: continuationChecks,
    extendable_states: extendableStates,
    obstructed_states: obstructedStates,
    learned_clauses: learnedClauses.length,
    nogood_prunes: training.nogood_prunes,
    average_clause_size: training.nogood_average_size,
    maximum_clause_size: training.nogood_max_size
  },
  target_layer: targetLayer,
  baseline: targetSummary(baseline),
  transferred: targetSummary(transferred),
  node_ratio: baseline.nodes ? transferred.nodes / baseline.nodes : null,
  time_ratio: baseline.milliseconds ? transferred.milliseconds / baseline.milliseconds : null,
  warning: "A performance comparison is not a non-tiling, tiling, or aperiodicity certificate."
})}\n`);
