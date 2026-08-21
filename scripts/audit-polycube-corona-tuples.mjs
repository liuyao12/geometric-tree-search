#!/usr/bin/env node

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  polycubeCoronaIncompatibleTargetPairDetails,
  polycubeCoronaIncompatibleTargetQuadrupleDetails,
  polycubeCoronaIncompatibleTargetTripleDetails,
  polycubeCoronaRingCellKeys,
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
const maximumTripleDistance = Number(args.get("triple-max-cell-distance") ?? 20);
const maximumQuadrupleDistance = Number(args.get("quadruple-max-cell-distance") ?? 6);
if (!Number.isInteger(outerLayer) || outerLayer < 1
  || !Number.isInteger(maximumTripleDistance) || maximumTripleDistance < 1
  || !Number.isInteger(maximumQuadrupleDistance) || maximumQuadrupleDistance < 1) {
  throw new Error("layer and tuple-distance options must be positive integers");
}
const sourcePath = resolve(args.get("corona-report") ?? "");
if (!args.get("corona-report")) throw new Error("--corona-report is required");
const outputPath = args.get("output") ? resolve(args.get("output")) : null;
const source = JSON.parse(readFileSync(sourcePath, "utf8"));
const corona = source.corona ?? source.radius_witness?.corona;
if (!Array.isArray(corona)) throw new Error("The corona report must contain a corona array");
const verification = verifyPolycubeCoronaPatch(candidate.voxels, corona, outerLayer);
if (!verification.verified) throw new Error(`Outer corona verification failed: ${verification.reason}`);

const started = performance.now();
const incompatiblePairs = polycubeCoronaIncompatibleTargetPairDetails(
  candidate.voxels,
  corona,
  outerLayer
);
const incompatibleTriples = incompatiblePairs.length
  ? []
  : polycubeCoronaIncompatibleTargetTripleDetails(candidate.voxels, corona, outerLayer, {
      maximumCellDistance: maximumTripleDistance,
      limit: 1
    });
const incompatibleQuadruples = incompatiblePairs.length || incompatibleTriples.length
  ? []
  : polycubeCoronaIncompatibleTargetQuadrupleDetails(candidate.voxels, corona, outerLayer, {
      maximumCellDistance: maximumQuadrupleDistance,
      limit: 1
    });
const report = {
  kind: "polycube_corona_tuple_coverability_audit",
  candidate: id,
  outer_layer: outerLayer,
  next_ring_layer: outerLayer + 1,
  outer_placements: corona.length,
  outer_verified: true,
  next_ring_cells: polycubeCoronaRingCellKeys(candidate.voxels, outerLayer + 1).length,
  incompatible_pair_count: incompatiblePairs.length,
  pairwise_coverable: incompatiblePairs.length === 0,
  triple_max_cell_distance: maximumTripleDistance,
  first_incompatible_triple: incompatibleTriples[0] ?? null,
  triplewise_coverable: incompatiblePairs.length === 0 && incompatibleTriples.length === 0,
  quadruple_max_cell_distance: maximumQuadrupleDistance,
  first_incompatible_quadruple: incompatibleQuadruples[0] ?? null,
  quadruplewise_coverable: incompatiblePairs.length === 0
    && incompatibleTriples.length === 0
    && incompatibleQuadruples.length === 0,
  milliseconds: Math.round(performance.now() - started),
  source: sourcePath
};
if (outputPath) writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`);
process.stdout.write(`${JSON.stringify(report)}\n`);
