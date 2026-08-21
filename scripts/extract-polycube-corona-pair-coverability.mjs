#!/usr/bin/env node

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { mkdirSync } from "node:fs";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  polycubeCellPairOrbitKeys,
  polycubeCoronaIncompatibleTargetPairs,
  verifyPolycubeCoronaPatch
} from "../assets/polycube-corona-search.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const id = args.get("id") ?? "p9-42947";
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);
const outerLayer = Number(args.get("outer-layer") ?? 4);
if (!Number.isInteger(outerLayer) || outerLayer < 1) throw new Error("--outer-layer must be a positive integer");
const witnessReports = String(args.get("witness-report") ?? "")
  .split(",")
  .map(value => value.trim())
  .filter(Boolean);
if (!witnessReports.length) throw new Error("--witness-report must list at least one JSON witness");
const output = args.get("output") ? resolve(args.get("output")) : null;

const pairs = [];
const pairKeys = new Set();
const records = [];
for (const reportPath of witnessReports) {
  const report = JSON.parse(readFileSync(reportPath, "utf8"));
  const placements = report.corona ?? report.radius_witness?.corona;
  const verification = verifyPolycubeCoronaPatch(candidate.voxels, placements, outerLayer);
  if (!verification.verified) {
    throw new Error(`${reportPath} failed radius-${outerLayer} verification: ${verification.reason}`);
  }
  const incompatible = polycubeCoronaIncompatibleTargetPairs(
    candidate.voxels,
    placements,
    outerLayer
  );
  let orbitPairsAdded = 0;
  for (const pair of incompatible) {
    for (const orbitPair of polycubeCellPairOrbitKeys(candidate.voxels, pair)) {
      const key = orbitPair.join(";");
      if (pairKeys.has(key)) continue;
      pairKeys.add(key);
      pairs.push(orbitPair);
      orbitPairsAdded += 1;
    }
  }
  records.push({
    report: reportPath,
    placements: placements.length,
    incompatible_pairs: incompatible.length,
    orbit_pairs_added: orbitPairsAdded
  });
}

const summary = {
  kind: "polycube_corona_pair_coverability",
  candidate: id,
  outer_layer: outerLayer,
  inner_layer: outerLayer + 1,
  records,
  source_incompatible_pairs: records.reduce((sum, record) => sum + record.incompatible_pairs, 0),
  symmetry_closed_pair_count: pairs.length,
  pairs,
  interpretation: "Every pair is a necessary local condition for an inner-radius extension; it is not by itself a tiling or aperiodicity certificate."
};
if (output) {
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, `${JSON.stringify(summary, null, 2)}\n`);
}
process.stdout.write(`${JSON.stringify({ ...summary, pairs: undefined, output })}\n`);
