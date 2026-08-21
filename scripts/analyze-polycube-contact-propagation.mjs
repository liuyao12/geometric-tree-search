#!/usr/bin/env node

import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  enumeratePolycubeCoronaPlacements,
  polycubeReciprocalPlacement,
  polycubeRootContactKey,
  searchPolycubeCorona
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
const activeTypeIndices = String(args.get("active-types") ?? "3,25,29,43,44,53")
  .split(",")
  .map(Number)
  .filter(Number.isInteger);
const maximumLayer = Math.max(1, Math.floor(numberArg("maximum-layer", 4)));
const nodeLimit = Math.max(1, Math.floor(numberArg("nodes", 5_000_000)));
const timeLimitMs = Math.max(1, numberArg("time-ms", 30_000));
const seed = Math.floor(numberArg("seed", 3));

const catalog = enumeratePolycubeCoronaPlacements(candidate.voxels, 1);
const typeKeys = [...new Set(catalog.map(placement =>
  polycubeRootContactKey(candidate.voxels, placement)
))].sort();
const typeId = new Map(typeKeys.map((key, index) => [key, index]));
const active = new Set(activeTypeIndices);
const edgeCounts = new Map();

for (const placement of catalog) {
  const from = typeId.get(polycubeRootContactKey(candidate.voxels, placement));
  if (!active.has(from)) continue;
  const reciprocal = polycubeReciprocalPlacement(candidate.voxels, placement);
  if (!reciprocal) throw new Error("Unable to normalize a reciprocal placement");
  const to = typeId.get(polycubeRootContactKey(candidate.voxels, reciprocal));
  if (!Number.isInteger(to)) throw new Error("Reciprocal contact type is missing from the catalog");
  const key = `${from},${to}`;
  edgeCounts.set(key, (edgeCounts.get(key) ?? 0) + 1);
}

const edges = [...edgeCounts].map(([key, count]) => {
  const [from, to] = key.split(",").map(Number);
  return { from, to, to_active: active.has(to), placements: count };
}).sort((left, right) => left.from - right.from || left.to - right.to);
const activeEdges = edges.filter(edge => edge.to_active);
const reciprocalCycleRepresentatives = [];
const seenCycle = new Set();
for (const edge of activeEdges) {
  const reverseExists = activeEdges.some(candidateEdge =>
    candidateEdge.from === edge.to && candidateEdge.to === edge.from
  );
  if (!reverseExists) continue;
  const signature = [edge.from, edge.to].sort((left, right) => left - right).join(",");
  if (!seenCycle.has(signature)) {
    seenCycle.add(signature);
    reciprocalCycleRepresentatives.push(Math.min(edge.from, edge.to));
  }
}

const cycleExtensionTrials = [];
for (const typeIndex of reciprocalCycleRepresentatives) {
  const placement = catalog.find(candidatePlacement =>
    typeId.get(polycubeRootContactKey(candidate.voxels, candidatePlacement)) === typeIndex
  );
  if (!placement) throw new Error(`No representative placement for contact type ${typeIndex}`);
  for (let layers = 2; layers <= maximumLayer; layers++) {
    const result = searchPolycubeCorona(candidate.voxels, {
      layers,
      seed,
      fixedPlacements: [placement],
      nodeLimit,
      timeLimitMs,
      nogoods: true
    });
    cycleExtensionTrials.push({
      type_index: typeIndex,
      layers,
      success: result.success,
      exhausted: result.exhausted,
      stopped_by: result.stopped_by,
      nodes: result.nodes,
      placements: result.corona?.length ?? null,
      milliseconds: result.milliseconds
    });
    if (!result.success) break;
  }
}

process.stdout.write(`${JSON.stringify({
  type: "contact_propagation_summary",
  id,
  model: "directed root-contact types with the neighboring tile renormalized as root",
  active_type_indices: activeTypeIndices,
  active_placements: edges.reduce((sum, edge) => sum + edge.placements, 0),
  reciprocal_edges: edges,
  active_to_active_placements: activeEdges.reduce((sum, edge) => sum + edge.placements, 0),
  reciprocal_cycle_representatives: reciprocalCycleRepresentatives,
  cycle_extension_trials: cycleExtensionTrials,
  conclusion: cycleExtensionTrials.every(trial => trial.success)
    ? `Every reciprocal active cycle tested survives through radius ${maximumLayer}; the six-state rule alone does not force a hierarchy.`
    : "At least one reciprocal active cycle failed or remained incomplete within the configured extension screen.",
  warning: "Surviving finite coronas do not certify an infinite or periodic tiling."
})}\n`);
