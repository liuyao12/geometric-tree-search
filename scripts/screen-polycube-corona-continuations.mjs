#!/usr/bin/env node

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  createPolycubeCoronaPairObstructionOracle,
  polycubeCoronaBoundaryKey,
  searchPolycubeCorona,
  verifyPolycubeCoronaPairObstruction,
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
const booleanArg = (name, fallback) => {
  if (!args.has(name)) return fallback;
  return !["0", "false", "no"].includes(String(args.get(name)).toLowerCase());
};
const budgetClock = String(args.get("budget-clock") ?? "wall").toLowerCase();
if (!["wall", "cpu"].includes(budgetClock)) {
  throw new Error("--budget-clock must be wall or cpu");
}

const id = args.get("id") ?? "p9-42947";
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);
const outerLayer = Math.max(1, Math.floor(numberArg("outer-layer", 4)));
const innerLayer = Math.max(outerLayer + 1, Math.floor(numberArg("inner-layer", outerLayer + 1)));
const timePerSeedMs = Math.max(1, numberArg("time-ms", 30_000));
const outerNodeLimit = Math.max(1, Math.floor(numberArg("outer-nodes", Number.MAX_SAFE_INTEGER)));
const innerTimeMs = Math.max(1, numberArg("inner-time-ms", 250));
const innerNodeLimit = Math.max(1, Math.floor(numberArg("inner-nodes", 100_000)));
const nogoodLimit = Math.max(1, Math.floor(numberArg("nogood-limit", 500_000)));
const adaptiveProposal = booleanArg("adaptive-proposal", false);
const proposalTimeMs = Math.max(0, numberArg(
  "proposal-time-ms",
  adaptiveProposal ? 250 : 0
));
const proposalNodeLimit = Math.max(1, Math.floor(numberArg("proposal-nodes", innerNodeLimit)));
const symmetryNogoods = booleanArg("symmetry-nogoods", false);
const pairLookahead = booleanArg("pair-lookahead", false);
const partialNextLayerCoverability = booleanArg("partial-next-layer-coverability", false);
const partialNextLayerMinPlacements = Math.max(0, Math.floor(numberArg(
  "partial-next-layer-min-placements",
  0
)));
const placementOrdering = String(args.get("placement-order") ?? "compact").toLowerCase();
if (!["compact", "expansive", "seeded"].includes(placementOrdering)) {
  throw new Error("--placement-order must be compact, expansive, or seeded");
}
const seeds = String(args.get("seeds") ?? "3,4,1,2")
  .split(",")
  .map(Number)
  .filter(Number.isFinite)
  .map(Math.floor);
const fixedWitnessReports = String(args.get("fixed-witness-report") ?? "")
  .split(",")
  .map(value => value.trim())
  .filter(Boolean);
const reportOutput = args.get("report-output")
  ? resolve(String(args.get("report-output")))
  : null;
const proposalSampleOutput = args.get("proposal-sample-output")
  ? resolve(String(args.get("proposal-sample-output")))
  : null;
const proposalSampleLimit = Math.max(0, Math.floor(numberArg(
  "proposal-sample-limit",
  proposalSampleOutput ? 1 : 0
)));

let carriedNogoods = [];
let totalContinuationChecks = 0;
let totalExplainedObstructions = 0;
let totalImmediateObstructions = 0;
let totalResolvedSubtreeConflicts = 0;
let totalPairObstructions = 0;
let totalPairObstructionChecks = 0;
let totalNextLayerCoverabilityPrunes = 0;
let totalNextLayerCoverabilityNogoodClauses = 0;
let radiusWitness = null;
let incompleteContinuation = null;
const obstructedBoundaryStates = new Set();
const portfolioProposalBoundaryDigests = new Set();
const portfolioProposalPlacementCounts = new Map();
const proposalSamples = [];
const proposalSampleByDigest = new Map();
let boundaryCacheHits = 0;
const trials = [];
let directProposal = null;
const fixedWitnessContinuations = [];
const pairObstructionOracle = pairLookahead
  ? createPolycubeCoronaPairObstructionOracle(candidate.voxels, outerLayer)
  : null;

const mergeNogoodClauses = (...collections) => {
  const merged = new Map();
  for (const collection of collections) for (const clause of collection ?? []) {
    if (!Array.isArray(clause)) continue;
    const normalized = [...new Set(clause.map(String))].sort();
    merged.set(normalized.join("|"), normalized);
  }
  return [...merged.values()];
};

for (const reportPath of fixedWitnessReports) {
  const report = JSON.parse(readFileSync(reportPath, "utf8"));
  const placements = report.radius_witness?.corona ?? report.corona;
  if (!Array.isArray(placements)) {
    throw new Error(`Fixed witness ${reportPath} does not contain corona or radius_witness.corona`);
  }
  const outerVerification = verifyPolycubeCoronaPatch(candidate.voxels, placements, outerLayer);
  if (!outerVerification.verified) {
    throw new Error(`Fixed witness ${reportPath} failed radius-${outerLayer} verification: ${outerVerification.reason}`);
  }
  const continuation = searchPolycubeCorona(candidate.voxels, {
    layers: innerLayer,
    seed: seeds[0] ?? 0,
    fixedPlacements: placements,
    nodeLimit: innerNodeLimit,
    timeLimitMs: innerTimeMs,
    timeBudgetMode: budgetClock,
    nogoods: true,
    symmetryNogoods,
    nogoodLimit
  });
  const fixedPairObstruction = pairLookahead
    && continuation.exhausted
    && continuation.fixed_obstruction_nogood?.kind === "resolved_subtree_conflict"
    ? pairObstructionOracle(placements)
    : null;
  let fixedPairReplayVerified = false;
  if (fixedPairObstruction?.fixed_placement_indices?.length) {
    const replay = verifyPolycubeCoronaPairObstruction(
      candidate.voxels,
      placements,
      outerLayer,
      fixedPairObstruction
    );
    fixedPairReplayVerified = replay.verified;
    if (!fixedPairReplayVerified) {
      throw new Error(`Fixed witness pair obstruction ${reportPath} failed independent replay: ${replay.reason}`);
    }
  }
  const record = {
    report: reportPath,
    fixed_placements: placements.length,
    success: continuation.success,
    exhausted: continuation.exhausted,
    stopped_by: continuation.stopped_by,
    nodes: continuation.nodes,
    milliseconds: continuation.milliseconds,
    obstruction_kind: continuation.fixed_obstruction_nogood?.kind
      ?? (continuation.fixed_obstruction_nogood?.target_cell ? "immediate_dead_target" : null),
    obstruction_target_cell: continuation.fixed_obstruction_nogood?.target_cell ?? null,
    obstruction_clause_size: continuation.fixed_obstruction_nogood?.fixed_placement_keys?.length ?? null,
    obstruction_clause_keys: continuation.fixed_obstruction_nogood?.fixed_placement_keys ?? null,
    immediate_dead_target_count: continuation.fixed_obstruction_nogoods?.length ?? 0,
    pair_obstruction_target_cells: fixedPairObstruction?.target_cells ?? null,
    pair_obstruction_clause_size: fixedPairObstruction?.fixed_placement_keys?.length ?? null,
    pair_obstruction_candidate_pairs_blocked: fixedPairObstruction?.candidate_pairs_blocked ?? null,
    pair_obstruction_replay_verified: fixedPairReplayVerified
  };
  fixedWitnessContinuations.push(record);
  process.stdout.write(`${JSON.stringify({ type: "fixed_witness_continuation", ...record })}\n`);
  if (continuation.success) {
    const verification = verifyPolycubeCoronaPatch(candidate.voxels, continuation.corona, innerLayer);
    if (!verification.verified) {
      throw new Error(`Fixed witness continuation ${reportPath} failed verification: ${verification.reason}`);
    }
    radiusWitness = continuation;
    break;
  }
  if (!continuation.exhausted) {
    incompleteContinuation = continuation;
    break;
  }
  const obstructionClause = fixedPairObstruction?.fixed_placement_keys
    ?? continuation.fixed_obstruction_nogood?.fixed_placement_keys;
  if (obstructionClause?.length) {
    carriedNogoods = mergeNogoodClauses(carriedNogoods, [obstructionClause]);
  }
  obstructedBoundaryStates.add(polycubeCoronaBoundaryKey(candidate.voxels, placements, outerLayer));
}

if (!radiusWitness && !incompleteContinuation && proposalTimeMs > 0) {
  const proposal = searchPolycubeCorona(candidate.voxels, {
    layers: innerLayer,
    seed: seeds[0] ?? 0,
    nodeLimit: proposalNodeLimit,
    timeLimitMs: proposalTimeMs,
    timeBudgetMode: budgetClock,
    nogoods: true,
    symmetryNogoods,
    nogoodLimit,
    returnNogoods: true
  });
  carriedNogoods = mergeNogoodClauses(carriedNogoods, proposal.nogood_clause_keys);
  directProposal = {
    success: proposal.success,
    exhausted: proposal.exhausted,
    stopped_by: proposal.stopped_by,
    nodes: proposal.nodes,
    milliseconds: proposal.milliseconds,
    placements: proposal.corona?.length ?? null,
    learned_clauses: carriedNogoods.length,
    nogood_prunes: proposal.nogood_prunes,
    symmetry_nogood_clauses: proposal.symmetry_nogood_clauses,
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
  outer_node_limit: outerNodeLimit,
  inner_time_ms: innerTimeMs,
  inner_node_limit: innerNodeLimit,
  nogood_limit: nogoodLimit,
  proposal_time_ms: proposalTimeMs,
  proposal_node_limit: proposalNodeLimit,
  adaptive_proposal: adaptiveProposal,
  direct_proposal: directProposal,
  fixed_witness_continuations: fixedWitnessContinuations,
  symmetry_nogoods: symmetryNogoods,
  pair_lookahead: pairLookahead,
  partial_next_layer_coverability: partialNextLayerCoverability,
  partial_next_layer_min_placements: partialNextLayerMinPlacements,
  placement_ordering: placementOrdering,
  proposal_sample_limit: proposalSampleLimit,
  budget_clock: budgetClock
})}\n`);

for (const seed of radiusWitness || incompleteContinuation || directProposal?.exhausted ? [] : seeds) {
  let continuationChecks = 0;
  let explainedObstructions = 0;
  let immediateObstructions = 0;
  let resolvedSubtreeConflicts = 0;
  let unexplainedObstructions = 0;
  let pairObstructionChecks = 0;
  let pairObstructions = 0;
  const proposalPlacementCounts = new Map();
  const proposalBoundaryDigests = new Set();
  const result = searchPolycubeCorona(candidate.voxels, {
    layers: outerLayer,
    seed,
    nodeLimit: outerNodeLimit,
    timeLimitMs: timePerSeedMs,
    timeBudgetMode: budgetClock,
    nogoods: true,
    symmetryNogoods,
    nogoodLimit,
    initialNogoodPlacementKeys: carriedNogoods,
    returnNogoods: true,
    nextLayerCoverability: partialNextLayerCoverability,
    nextLayerCoverabilityMinPlacements: partialNextLayerMinPlacements,
    placementOrdering,
    acceptSolution(solution) {
      const boundaryKey = polycubeCoronaBoundaryKey(candidate.voxels, solution, outerLayer);
      proposalPlacementCounts.set(
        solution.length,
        (proposalPlacementCounts.get(solution.length) ?? 0) + 1
      );
      portfolioProposalPlacementCounts.set(
        solution.length,
        (portfolioProposalPlacementCounts.get(solution.length) ?? 0) + 1
      );
      const boundaryDigest = createHash("sha256").update(boundaryKey).digest("hex");
      proposalBoundaryDigests.add(boundaryDigest);
      portfolioProposalBoundaryDigests.add(boundaryDigest);
      let proposalSample = proposalSampleByDigest.get(boundaryDigest) ?? null;
      if (!proposalSample && proposalSamples.length < proposalSampleLimit) {
        proposalSample = {
          seed,
          placement_ordering: placementOrdering,
          placements: solution.length,
          boundary_sha256: boundaryDigest,
          corona: solution.map(placement => ({
            orientation_index: placement.orientationIndex,
            orientation_key: placement.orientationKey,
            translation: placement.translation,
            cells: placement.cells
          })),
          continuation: null
        };
        proposalSamples.push(proposalSample);
        proposalSampleByDigest.set(boundaryDigest, proposalSample);
      }
      if (obstructedBoundaryStates.has(boundaryKey)) {
        boundaryCacheHits += 1;
        if (proposalSample && !proposalSample.continuation) {
          proposalSample.continuation = { status: "cached_exact_obstruction" };
        }
        return false;
      }
      continuationChecks += 1;
      const continuation = searchPolycubeCorona(candidate.voxels, {
        layers: innerLayer,
        seed,
        fixedPlacements: solution,
        nodeLimit: innerNodeLimit,
        timeLimitMs: innerTimeMs,
        timeBudgetMode: budgetClock,
        nogoods: true,
        symmetryNogoods,
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
        if (proposalSample) {
          proposalSample.continuation = {
            status: "verified_inner_radius_witness",
            nodes: continuation.nodes,
            milliseconds: continuation.milliseconds,
            placements: continuation.corona.length
          };
        }
        radiusWitness = continuation;
        return true;
      }
      if (!continuation.exhausted) {
        if (proposalSample) {
          proposalSample.continuation = {
            status: "incomplete",
            stopped_by: continuation.stopped_by,
            nodes: continuation.nodes,
            milliseconds: continuation.milliseconds
          };
        }
        incompleteContinuation = continuation;
        return true;
      }
      const obstruction = continuation.fixed_obstruction_nogood;
      if (proposalSample) {
        proposalSample.continuation = {
          status: "exact_obstruction",
          nodes: continuation.nodes,
          milliseconds: continuation.milliseconds,
          obstruction_kind: obstruction?.kind ?? null,
          obstruction_fixed_placement_indices: obstruction?.fixed_placement_indices ?? [],
          obstruction_fixed_placement_keys: obstruction?.fixed_placement_keys ?? []
        };
      }
      obstructedBoundaryStates.add(boundaryKey);
      if (obstruction?.fixed_placement_keys?.length) {
        explainedObstructions += 1;
        if (obstruction.kind === "resolved_subtree_conflict") {
          resolvedSubtreeConflicts += 1;
          if (pairLookahead) {
            pairObstructionChecks += 1;
            const pairObstruction = pairObstructionOracle(solution);
            if (pairObstruction?.fixed_placement_keys?.length) {
              pairObstructions += 1;
              return {
                accept: false,
                nogood_placement_keys: pairObstruction.fixed_placement_keys
              };
            }
          }
        } else immediateObstructions += 1;
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
  totalPairObstructionChecks += pairObstructionChecks;
  totalPairObstructions += pairObstructions;
  totalNextLayerCoverabilityPrunes += result.next_layer_coverability_prunes;
  totalNextLayerCoverabilityNogoodClauses += result.next_layer_coverability_nogood_clauses;
  const trial = {
    seed,
    placement_ordering: result.placement_ordering,
    success: result.success,
    exhausted: result.exhausted,
    stopped_by: result.stopped_by,
    nodes: result.nodes,
    milliseconds: result.milliseconds,
    continuation_checks: continuationChecks,
    explained_obstructions: explainedObstructions,
    immediate_obstructions: immediateObstructions,
    resolved_subtree_conflicts: resolvedSubtreeConflicts,
    pair_obstruction_checks: pairObstructionChecks,
    pair_obstructions: pairObstructions,
    proposal_placement_distribution: Object.fromEntries(
      [...proposalPlacementCounts].sort(([left], [right]) => left - right)
    ),
    unique_proposal_boundary_states: proposalBoundaryDigests.size,
    proposal_boundary_sha256: [...proposalBoundaryDigests].sort(),
    next_layer_coverability_prunes: result.next_layer_coverability_prunes,
    next_layer_coverability_nogood_clauses: result.next_layer_coverability_nogood_clauses,
    obstructed_boundary_states: obstructedBoundaryStates.size,
    boundary_cache_hits: boundaryCacheHits,
    unexplained_obstructions: unexplainedObstructions,
    initial_nogood_clauses: result.initial_nogood_clauses,
    final_nogood_clauses: result.nogood_clauses,
    nogood_prunes: result.nogood_prunes,
    symmetry_nogood_clauses: result.symmetry_nogood_clauses,
    nogood_average_size: result.nogood_average_size,
    nogood_max_size: result.nogood_max_size,
    nogood_saturated: result.nogood_saturated,
    maximum_depth: result.maximum_depth
  };
  trials.push(trial);
  process.stdout.write(`${JSON.stringify({ type: "continuation_portfolio_trial", ...trial })}\n`);
  if (radiusWitness || incompleteContinuation || result.exhausted) break;
}

const summary = {
  type: "continuation_portfolio_summary",
  id,
  outer_layer: outerLayer,
  inner_layer: innerLayer,
  direct_proposal: directProposal,
  fixed_witness_continuations: fixedWitnessContinuations,
  pair_lookahead: pairLookahead,
  partial_next_layer_coverability: partialNextLayerCoverability,
  partial_next_layer_min_placements: partialNextLayerMinPlacements,
  placement_ordering: placementOrdering,
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
  total_pair_obstruction_checks: totalPairObstructionChecks,
  total_pair_obstructions: totalPairObstructions,
  total_next_layer_coverability_prunes: totalNextLayerCoverabilityPrunes,
  total_next_layer_coverability_nogood_clauses: totalNextLayerCoverabilityNogoodClauses,
  proposal_placement_distribution: Object.fromEntries(
    [...portfolioProposalPlacementCounts].sort(([left], [right]) => left - right)
  ),
  unique_proposal_boundary_states: portfolioProposalBoundaryDigests.size,
  proposal_boundary_sha256: [...portfolioProposalBoundaryDigests].sort(),
  proposal_samples_saved: proposalSamples.length,
  proposal_sample_output: proposalSampleOutput,
  obstructed_boundary_states: obstructedBoundaryStates.size,
  boundary_cache_hits: boundaryCacheHits,
  carried_nogood_clauses: carriedNogoods.length,
  radius_witness: radiusWitness ? {
    placements: radiusWitness.corona?.length ?? null,
    nodes: radiusWitness.nodes,
    milliseconds: radiusWitness.milliseconds,
    corona: radiusWitness.corona
  } : null,
  incomplete_continuation: incompleteContinuation ? {
    stopped_by: incompleteContinuation.stopped_by,
    nodes: incompleteContinuation.nodes,
    milliseconds: incompleteContinuation.milliseconds
  } : null,
  warning: "A bounded incomplete portfolio is not a non-tiling or aperiodicity certificate."
};
if (reportOutput) {
  mkdirSync(dirname(reportOutput), { recursive: true });
  writeFileSync(reportOutput, `${JSON.stringify({
    kind: "polycube_corona_continuation_portfolio",
    ...summary
  }, null, 2)}\n`);
}
if (proposalSampleOutput && proposalSamples.length) {
  mkdirSync(dirname(proposalSampleOutput), { recursive: true });
  writeFileSync(proposalSampleOutput, `${JSON.stringify({
    kind: "polycube_corona_proposal_samples",
    candidate: id,
    outer_layer: outerLayer,
    inner_layer: innerLayer,
    placement_ordering: placementOrdering,
    samples: proposalSamples,
    corona: proposalSamples.length === 1 ? proposalSamples[0].corona : null,
    warning: "Each sample is a verified finite outer patch; an exact failed continuation is not an infinite-tiling or aperiodicity result."
  }, null, 2)}\n`);
}
process.stdout.write(`${JSON.stringify({ ...summary, report_output: reportOutput })}\n`);
