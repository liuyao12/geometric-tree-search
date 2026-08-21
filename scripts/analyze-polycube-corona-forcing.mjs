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
const placementKey = placement => placement.cells
  .map(cell => cell.join(","))
  .sort()
  .join(";");

const id = args.get("id") ?? "p9-42947";
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);
const layers = Math.max(1, Math.floor(numberArg("layers", 1)));
const seed = Math.floor(numberArg("seed", 0));
const nodeLimit = Math.max(1, Math.floor(numberArg("nodes", 5_000_000)));
const timeLimitMs = Math.max(1, numberArg("time-ms", 30_000));

const baseline = searchPolycubeCorona(candidate.voxels, {
  layers,
  seed,
  nodeLimit,
  timeLimitMs
});
if (!baseline.success) {
  process.stdout.write(`${JSON.stringify({
    type: "corona_forcing_summary",
    id,
    layers,
    classification: "baseline_incomplete_or_obstructed",
    baseline
  })}\n`);
  process.exit(0);
}
const baselineVerification = verifyPolycubeCoronaPatch(candidate.voxels, baseline.corona, layers);
if (!baselineVerification.verified) {
  throw new Error(`Baseline corona failed independent verification: ${baselineVerification.reason}`);
}

const probes = [];
for (const [index, placement] of baseline.corona.entries()) {
  const key = placementKey(placement);
  const alternative = searchPolycubeCorona(candidate.voxels, {
    layers,
    seed,
    forbiddenPlacementKeys: [key],
    nodeLimit,
    timeLimitMs
  });
  const alternativeVerification = alternative.success
    ? verifyPolycubeCoronaPatch(candidate.voxels, alternative.corona, layers, {
        forbiddenPlacementKeys: [key]
      })
    : null;
  if (alternativeVerification && !alternativeVerification.verified) {
    throw new Error(`Alternative ${index} failed independent verification: ${alternativeVerification.reason}`);
  }
  const outcome = alternative.success
    ? "replaceable"
    : alternative.exhausted
      ? "forced"
      : "incomplete";
  probes.push({
    baseline_placement_index: index,
    placement_key: key,
    outcome,
    nodes: alternative.nodes,
    milliseconds: alternative.milliseconds,
    stopped_by: alternative.stopped_by,
    alternative_tiles: alternative.corona?.length ?? null,
    alternative_verified: alternativeVerification?.verified ?? null
  });
}

const forced = probes.filter(probe => probe.outcome === "forced");
const replaceable = probes.filter(probe => probe.outcome === "replaceable");
const incomplete = probes.filter(probe => probe.outcome === "incomplete");
process.stdout.write(`${JSON.stringify({
  type: "corona_forcing_summary",
  id,
  layers,
  model: "normalized root; proper rotations; integer translations",
  classification: incomplete.length
    ? "forcing_audit_incomplete"
    : forced.length
      ? "forced_placements_found"
      : "no_individually_forced_placement",
  baseline: {
    seed,
    tiles: baseline.corona.length,
    nodes: baseline.nodes,
    milliseconds: baseline.milliseconds,
    verified: baselineVerification.verified
  },
  probes,
  totals: {
    tested: probes.length,
    forced: forced.length,
    replaceable: replaceable.length,
    incomplete: incomplete.length
  },
  inference: incomplete.length || forced.length
    ? null
    : "Any placement forced in every legal corona would occur in the baseline; every baseline placement has a certified alternative, so no individual absolute placement is forced.",
  warning: "This does not exclude forced disjunctions, adjacency types, larger clusters, or hierarchical supertiles."
})}\n`);
