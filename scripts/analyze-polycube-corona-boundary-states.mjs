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
const booleanArg = (name, fallback) => {
  if (!args.has(name)) return fallback;
  return !["0", "false", "no"].includes(String(args.get(name)).toLowerCase());
};
const id = args.get("id") ?? "p9-42947";
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);
const outerLayer = Math.max(1, Math.floor(numberArg("outer-layer", 1)));
const innerLayer = Math.max(outerLayer + 1, Math.floor(numberArg("inner-layer", outerLayer + 1)));
const sampleLimit = Math.max(1, Math.floor(numberArg("samples", 10_000)));
const outerNodeLimit = Math.max(1, Math.floor(numberArg("outer-nodes", 10_000_000)));
const outerTimeMs = Math.max(1, numberArg("outer-time-ms", 30_000));
const innerNodeLimit = Math.max(1, Math.floor(numberArg("inner-nodes", 1_000_000)));
const innerTimeMs = Math.max(1, numberArg("inner-time-ms", 5_000));
const seed = Math.floor(numberArg("seed", 0));
const learnObstructions = booleanArg("learn-obstructions", true);
const includeBoundaryKeys = booleanArg("include-boundary-keys", false);

const hashBoundary = value => {
  let hash = 14695981039346656037n;
  for (let index = 0; index < value.length; index++) {
    hash ^= BigInt(value.charCodeAt(index));
    hash = BigInt.asUintN(64, hash * 1099511628211n);
  }
  return hash.toString(16).padStart(16, "0");
};
const exteriorCellCount = key => key ? key.split(";").length : 0;

const boundaryStates = new Map();
let outerCoronas = 0;
let duplicateBoundaries = 0;
let continuationChecks = 0;
let extendable = 0;
let obstructed = 0;
let incomplete = 0;
let maximumContinuationNodes = 0;
let sampleLimitReached = false;
let explainedObstructions = 0;
let immediateObstructions = 0;
let subtreeObstructions = 0;
let obstructionClauseCells = 0;
let maximumObstructionSize = 0;
const transitionEdges = new Map();

const outer = searchPolycubeCorona(candidate.voxels, {
  layers: outerLayer,
  seed,
  nodeLimit: outerNodeLimit,
  timeLimitMs: outerTimeMs,
  nogoods: learnObstructions,
  returnNogoods: learnObstructions,
  acceptSolution(solution) {
    outerCoronas += 1;
    const boundaryKey = polycubeCoronaBoundaryKey(
      candidate.voxels,
      solution,
      outerLayer
    );
    if (boundaryStates.has(boundaryKey)) {
      duplicateBoundaries += 1;
      return false;
    }

    continuationChecks += 1;
    const continuation = searchPolycubeCorona(candidate.voxels, {
      layers: innerLayer,
      seed,
      fixedPlacements: solution,
      nodeLimit: innerNodeLimit,
      timeLimitMs: innerTimeMs,
      nogoods: true
    });
    maximumContinuationNodes = Math.max(maximumContinuationNodes, continuation.nodes);
    const row = {
      hash: hashBoundary(boundaryKey),
      exterior_cells: exteriorCellCount(boundaryKey),
      outer_tiles: solution.length,
      continuation: continuation.success
        ? "extendable"
        : continuation.exhausted
          ? "obstructed"
          : "incomplete",
      continuation_nodes: continuation.nodes,
      continuation_milliseconds: continuation.milliseconds,
      continuation_tiles: continuation.corona?.length ?? null,
      obstruction_size: continuation.fixed_obstruction_nogood
        ?.fixed_placement_keys?.length ?? null,
      next_boundary_hash: null
    };
    if (includeBoundaryKeys) row.boundary_key = boundaryKey;
    if (continuation.success) {
      const verification = verifyPolycubeCoronaPatch(
        candidate.voxels,
        continuation.corona,
        innerLayer
      );
      if (!verification.verified) {
        throw new Error(`Continuation failed verification: ${verification.reason}`);
      }
      extendable += 1;
      const nextBoundaryKey = polycubeCoronaBoundaryKey(
        candidate.voxels,
        continuation.corona,
        innerLayer
      );
      row.next_boundary_hash = hashBoundary(nextBoundaryKey);
      const edgeKey = `${row.hash}->${row.next_boundary_hash}`;
      transitionEdges.set(edgeKey, (transitionEdges.get(edgeKey) ?? 0) + 1);
    } else if (continuation.exhausted) {
      obstructed += 1;
      const obstruction = continuation.fixed_obstruction_nogood;
      if (obstruction?.fixed_placement_keys?.length) {
        explainedObstructions += 1;
        obstructionClauseCells += obstruction.fixed_placement_keys.length;
        maximumObstructionSize = Math.max(
          maximumObstructionSize,
          obstruction.fixed_placement_keys.length
        );
        if (obstruction.kind === "resolved_subtree_conflict") subtreeObstructions += 1;
        else immediateObstructions += 1;
      }
    } else {
      incomplete += 1;
    }
    boundaryStates.set(boundaryKey, row);
    if (boundaryStates.size >= sampleLimit) {
      sampleLimitReached = true;
      return true;
    }
    if (learnObstructions && continuation.exhausted
      && continuation.fixed_obstruction_nogood?.fixed_placement_keys?.length) {
      return {
        accept: false,
        nogood_placement_keys: continuation.fixed_obstruction_nogood.fixed_placement_keys
      };
    }
    return false;
  }
});

const states = [...boundaryStates.values()];
const exteriorHistogram = Object.fromEntries([...new Set(states.map(row => row.exterior_cells))]
  .sort((left, right) => left - right)
  .map(count => [count, states.filter(row => row.exterior_cells === count).length]));
process.stdout.write(`${JSON.stringify({
  type: "corona_boundary_state_summary",
  id,
  model: "root-stabilizer canonical exterior occupancy of a complete outer corona",
  outer_layer: outerLayer,
  inner_layer: innerLayer,
  seed,
  limits: {
    sample_limit: sampleLimit,
    outer_nodes: outerNodeLimit,
    outer_time_ms: outerTimeMs,
    inner_nodes: innerNodeLimit,
    inner_time_ms: innerTimeMs
  },
  learned_obstructions: learnObstructions,
  classification: sampleLimitReached
    ? "sample_limit"
    : outer.exhausted
      ? "outer_exhausted"
      : outer.stopped_by ?? "stopped",
  outer_coronas: outerCoronas,
  canonical_boundary_states: boundaryStates.size,
  duplicate_boundary_coronas: duplicateBoundaries,
  continuation_checks: continuationChecks,
  extendable_states: extendable,
  obstructed_states: obstructed,
  incomplete_states: incomplete,
  explained_obstructions: explainedObstructions,
  immediate_obstructions: immediateObstructions,
  resolved_subtree_obstructions: subtreeObstructions,
  average_obstruction_size: explainedObstructions
    ? obstructionClauseCells / explainedObstructions
    : 0,
  maximum_obstruction_size: maximumObstructionSize,
  maximum_continuation_nodes: maximumContinuationNodes,
  exterior_cell_histogram: exteriorHistogram,
  sampled_transition_edges: [...transitionEdges].map(([edge, witnesses]) => {
    const [from, to] = edge.split("->");
    return { from, to, witnesses };
  }),
  states,
  outer_search: {
    success: outer.success,
    exhausted: outer.exhausted,
    stopped_by: outer.stopped_by,
    nodes: outer.nodes,
    dead_ends: outer.dead_ends,
    solutions_rejected: outer.solutions_rejected,
    nogood_clauses: outer.nogood_clauses,
    nogood_prunes: outer.nogood_prunes,
    nogood_average_size: outer.nogood_average_size,
    nogood_max_size: outer.nogood_max_size,
    milliseconds: outer.milliseconds
  },
  warning: sampleLimitReached || !outer.exhausted
    ? "The boundary-state census is sampled and cannot certify that omitted states are absent."
    : "Every outer corona was exhausted under the stated exact model."
})}\n`);
