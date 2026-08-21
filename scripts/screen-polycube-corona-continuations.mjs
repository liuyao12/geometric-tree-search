#!/usr/bin/env node

import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  polycubeCoronaBoundaryKey,
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
const outerLayer = Math.max(1, Math.floor(numberArg("outer-layer", 4)));
const innerLayer = Math.max(outerLayer + 1, Math.floor(numberArg("inner-layer", outerLayer + 1)));
const timePerSeedMs = Math.max(1, numberArg("time-ms", 30_000));
const innerTimeMs = Math.max(1, numberArg("inner-time-ms", 250));
const innerNodeLimit = Math.max(1, Math.floor(numberArg("inner-nodes", 100_000)));
const nogoodLimit = Math.max(1, Math.floor(numberArg("nogood-limit", 500_000)));
const proposalTimeMs = Math.max(0, numberArg("proposal-time-ms", 0));
const proposalNodeLimit = Math.max(1, Math.floor(numberArg("proposal-nodes", innerNodeLimit)));
const seeds = String(args.get("seeds") ?? "3,4,1,2")
  .split(",")
  .map(Number)
  .filter(Number.isFinite)
  .map(Math.floor);

let carriedNogoods = [];
let totalContinuationChecks = 0;
let totalExplainedObstructions = 0;
let totalImmediateObstructions = 0;
let totalResolvedSubtreeConflicts = 0;
let radiusWitness = null;
let incompleteContinuation = null;
const obstructedBoundaryStates = new Set();
let boundaryCacheHits = 0;
const trials = [];
let directProposal = null;

if (proposalTimeMs > 0) {
  const proposal = searchPolycubeCorona(candidate.voxels, {
    layers: innerLayer,
    seed: seeds[0] ?? 0,
    nodeLimit: proposalNodeLimit,
    timeLimitMs: proposalTimeMs,
    nogoods: true,
    nogoodLimit,
    returnNogoods: true
  });
  carriedNogoods = proposal.nogood_clause_keys ?? [];
  directProposal = {
    success: proposal.success,
    exhausted: proposal.exhausted,
    stopped_by: proposal.stopped_by,
    nodes: proposal.nodes,
    milliseconds: proposal.milliseconds,
    placements: proposal.corona?.length ?? null,
    learned_clauses: carriedNogoods.length,
    nogood_prunes: proposal.nogood_prunes,
    maximum_depth: proposal.maximum_depth
  };
  if (proposal.success) {
    const verification = verifyPolycubeCoronaPatch(
      candidate.voxels,
      proposal.corona,
      innerLayer
    );
    if (!verification.verified) {
      throw new Error(`Direct proposal failed verification: ${verification.reason}`);
    }
    radiusWitness = proposal;
  }
}

process.stdout.write(`${JSON.stringify({
  type: "continuation_portfolio_start",
  id,
  outer_layer: outerLayer,
  inner_layer: innerLayer,
  seeds,
  time_per_seed_ms: timePerSeedMs,
  inner_time_ms: innerTimeMs,
  inner_node_limit: innerNodeLimit,
  nogood_limit: nogoodLimit,
  proposal_time_ms: proposalTimeMs,
  proposal_node_limit: proposalNodeLimit,
  direct_proposal: directProposal
})}\n`);

for (const seed of radiusWitness || directProposal?.exhausted ? [] : seeds) {
  let continuationChecks = 0;
  let explainedObstructions = 0;
  let immediateObstructions = 0;
  let resolvedSubtreeConflicts = 0;
  let unexplainedObstructions = 0;
  const result = searchPolycubeCorona(candidate.voxels, {
    layers: outerLayer,
    seed,
    nodeLimit: Infinity,
    timeLimitMs: timePerSeedMs,
    nogoods: true,
    nogoodLimit,
    initialNogoodPlacementKeys: carriedNogoods,
    returnNogoods: true,
    acceptSolution(solution) {
      const boundaryKey = polycubeCoronaBoundaryKey(candidate.voxels, solution, outerLayer);
      if (obstructedBoundaryStates.has(boundaryKey)) {
        boundaryCacheHits += 1;
        return false;
      }
      continuationChecks += 1;
      const continuation = searchPolycubeCorona(candidate.voxels, {
        layers: innerLayer,
        seed,
        fixedPlacements: solution,
        nodeLimit: innerNodeLimit,
        timeLimitMs: innerTimeMs,
        nogoods: true,
        nogoodLimit
      });
      if (continuation.success) {
        const verification = verifyPolycubeCoronaPatch(
          candidate.voxels,
          continuation.corona,
          innerLayer
        );
        if (!verification.verified) {
          throw new Error(`Continuation witness failed verification: ${verification.reason}`);
        }
        radiusWitness = continuation;
        return true;
      }
      if (!continuation.exhausted) {
        incompleteContinuation = continuation;
        return true;
      }
      const obstruction = continuation.fixed_obstruction_nogood;
      obstructedBoundaryStates.add(boundaryKey);
      if (obstruction?.fixed_placement_keys?.length) {
        explainedObstructions += 1;
        if (obstruction.kind === "resolved_subtree_conflict") resolvedSubtreeConflicts += 1;
        else immediateObstructions += 1;
        return { accept: false, nogood_placement_keys: obstruction.fixed_placement_keys };
      }
      unexplainedObstructions += 1;
      return false;
    }
  });
  carriedNogoods = result.nogood_clause_keys ?? carriedNogoods;
  totalContinuationChecks += continuationChecks;
  totalExplainedObstructions += explainedObstructions;
  totalImmediateObstructions += immediateObstructions;
  totalResolvedSubtreeConflicts += resolvedSubtreeConflicts;
  const trial = {
    seed,
    success: result.success,
    exhausted: result.exhausted,
    stopped_by: result.stopped_by,
    nodes: result.nodes,
    milliseconds: result.milliseconds,
    continuation_checks: continuationChecks,
    explained_obstructions: explainedObstructions,
    immediate_obstructions: immediateObstructions,
    resolved_subtree_conflicts: resolvedSubtreeConflicts,
    obstructed_boundary_states: obstructedBoundaryStates.size,
    boundary_cache_hits: boundaryCacheHits,
    unexplained_obstructions: unexplainedObstructions,
    initial_nogood_clauses: result.initial_nogood_clauses,
    final_nogood_clauses: result.nogood_clauses,
    nogood_prunes: result.nogood_prunes,
    nogood_average_size: result.nogood_average_size,
    nogood_max_size: result.nogood_max_size,
    nogood_saturated: result.nogood_saturated,
    maximum_depth: result.maximum_depth
  };
  trials.push(trial);
  process.stdout.write(`${JSON.stringify({ type: "continuation_portfolio_trial", ...trial })}\n`);
  if (radiusWitness || incompleteContinuation || result.exhausted) break;
}

process.stdout.write(`${JSON.stringify({
  type: "continuation_portfolio_summary",
  id,
  outer_layer: outerLayer,
  inner_layer: innerLayer,
  direct_proposal: directProposal,
  classification: radiusWitness
    ? "inner_radius_witness"
    : directProposal?.exhausted
      ? "certified_non_tiler"
    : incompleteContinuation
      ? "continuation_incomplete"
      : trials.at(-1)?.exhausted
        ? "certified_non_tiler"
        : "outer_portfolio_incomplete",
  trials,
  total_continuation_checks: totalContinuationChecks,
  total_explained_obstructions: totalExplainedObstructions,
  total_immediate_obstructions: totalImmediateObstructions,
  total_resolved_subtree_conflicts: totalResolvedSubtreeConflicts,
  obstructed_boundary_states: obstructedBoundaryStates.size,
  boundary_cache_hits: boundaryCacheHits,
  carried_nogood_clauses: carriedNogoods.length,
  radius_witness: radiusWitness ? {
    placements: radiusWitness.corona?.length ?? null,
    nodes: radiusWitness.nodes,
    milliseconds: radiusWitness.milliseconds
  } : null,
  incomplete_continuation: incompleteContinuation ? {
    stopped_by: incompleteContinuation.stopped_by,
    nodes: incompleteContinuation.nodes,
    milliseconds: incompleteContinuation.milliseconds
  } : null,
  warning: "A bounded incomplete portfolio is not a non-tiling or aperiodicity certificate."
})}\n`);
