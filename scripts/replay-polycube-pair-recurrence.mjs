#!/usr/bin/env node

import { mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  polycubeCellPairOrbitKeys,
  polycubeCoronaIncompatibleTargetPairDetails,
  polycubeCoronaIncompatibleTargetQuadrupleDetails,
  polycubeCoronaIncompatibleTargetTripleDetails,
  verifyPolycubeCoronaPatch
} from "../assets/polycube-corona-search.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const id = args.get("id") ?? "p9-42947";
const layer = Number(args.get("layer") ?? 4);
const limit = Number(args.get("limit") ?? 0);
const tripleMaximumCellDistance = Number(args.get("triple-max-cell-distance") ?? 6);
const tripleAuditLimit = Number(args.get("triple-audit-limit") ?? 32);
const quadrupleMaximumCellDistance = Number(args.get("quadruple-max-cell-distance") ?? 6);
const requireIndividualCoverability = !["0", "false", "no"].includes(
  String(args.get("require-individual-coverability") ?? "true").toLowerCase()
);
const inputRoot = resolve(args.get("input-root") ?? "runs");
const basePairReportPath = args.get("base-pair-report")
  ? resolve(args.get("base-pair-report"))
  : null;
const outputPath = resolve(args.get("output") ?? `runs/${id}-pair-recurrence.json`);
if (!Number.isInteger(layer) || layer < 1 || !Number.isInteger(limit) || limit < 0
    || !Number.isInteger(tripleMaximumCellDistance) || tripleMaximumCellDistance < 1
    || !Number.isInteger(tripleAuditLimit) || tripleAuditLimit < 1
    || !Number.isInteger(quadrupleMaximumCellDistance) || quadrupleMaximumCellDistance < 1) {
  throw new Error("Layer and tuple-audit bounds must be positive integers; --limit may be zero");
}
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);

const witnessPaths = [];
const visit = path => {
  for (const entry of readdirSync(path, { withFileTypes: true })) {
    const child = resolve(path, entry.name);
    if (entry.isDirectory()) visit(child);
    else if (entry.isFile() && /^outer-witness-.*\.json$/.test(entry.name)) witnessPaths.push(child);
  }
};
if (!statSync(inputRoot).isDirectory()) throw new Error(`--input-root is not a directory: ${inputRoot}`);
visit(inputRoot);
witnessPaths.sort();

const baseReport = basePairReportPath
  ? JSON.parse(readFileSync(basePairReportPath, "utf8"))
  : {};
const basePairs = baseReport.pair_coverability_pairs ?? baseReport.pairs ?? [];
if (!Array.isArray(basePairs)) throw new Error("--base-pair-report must contain pairs");
const pairConstraints = [];
const pairConstraintKeys = new Set();
const addPair = pair => {
  const normalized = [...new Set(pair.map(String))].sort();
  if (normalized.length !== 2) throw new Error("A pair constraint must contain two distinct cells");
  const key = normalized.join(";");
  if (pairConstraintKeys.has(key)) return;
  pairConstraintKeys.add(key);
  pairConstraints.push(normalized);
};
for (const pair of basePairs) addPair(pair);
const orbitRepresentative = pair => polycubeCellPairOrbitKeys(candidate.voxels, pair)
  .map(item => [...item].sort().join(";"))
  .sort()[0];
const pairOrbitScores = new Map(Object.entries(baseReport.pair_orbit_scores ?? {}));
const pairOrbitHits = new Map();
const uniqueStates = new Set();
const pairCompleteWitnesses = [];
const tripleDefectWitnesses = [];
const boundedTripleCompleteWitnesses = [];
const quadrupleDefectWitnesses = [];
const tupleGateSurvivorWitnesses = [];
const pairDefectOrbitSets = [];
let filesRead = 0;
let extractedStates = 0;
let verifiedStates = 0;
let duplicateStates = 0;
let invalidStates = 0;
let pairDefectStates = 0;
let individuallyIncompleteStates = 0;
let eligibleStates = 0;

const stateKey = corona => corona.map(placement =>
  placement.cells.map(cell => cell.join(",")).sort().join(";")
).sort().join("|");
const extractedCoronas = report => {
  const coronas = [];
  if (Array.isArray(report.corona)) coronas.push(report.corona);
  for (const corona of report.coronas ?? []) if (Array.isArray(corona)) coronas.push(corona);
  for (const witness of report.witnesses ?? []) {
    if (Array.isArray(witness?.corona)) coronas.push(witness.corona);
  }
  return coronas;
};

outer: for (const path of witnessPaths) {
  const report = JSON.parse(readFileSync(path, "utf8"));
  filesRead += 1;
  for (const corona of extractedCoronas(report)) {
    extractedStates += 1;
    const key = stateKey(corona);
    if (uniqueStates.has(key)) {
      duplicateStates += 1;
      continue;
    }
    uniqueStates.add(key);
    const verification = verifyPolycubeCoronaPatch(candidate.voxels, corona, layer);
    if (!verification.verified) {
      invalidStates += 1;
      continue;
    }
    verifiedStates += 1;
    const details = polycubeCoronaIncompatibleTargetPairDetails(candidate.voxels, corona, layer);
    if (requireIndividualCoverability
        && details.some(detail => Number(detail.candidate_pairs_blocked) === 0)) {
      individuallyIncompleteStates += 1;
      continue;
    }
    eligibleStates += 1;
    if (!details.length) {
      pairCompleteWitnesses.push(path);
      const tripleDetails = polycubeCoronaIncompatibleTargetTripleDetails(
        candidate.voxels,
        corona,
        layer,
        { maximumCellDistance: tripleMaximumCellDistance, limit: tripleAuditLimit + 1 }
      );
      if (tripleDetails.length) {
        tripleDefectWitnesses.push({
          path,
          defects_returned: Math.min(tripleDetails.length, tripleAuditLimit),
          truncated: tripleDetails.length > tripleAuditLimit,
          strongest_blocked_combinations: Math.max(...tripleDetails.map(detail => detail.candidate_triples_blocked))
        });
      } else {
        boundedTripleCompleteWitnesses.push(path);
        const quadrupleDetails = polycubeCoronaIncompatibleTargetQuadrupleDetails(
          candidate.voxels,
          corona,
          layer,
          { maximumCellDistance: quadrupleMaximumCellDistance, limit: 1 }
        );
        if (quadrupleDetails.length) quadrupleDefectWitnesses.push({
          path,
          strongest_blocked_combinations: quadrupleDetails[0].candidate_quadruples_blocked
        });
        else tupleGateSurvivorWitnesses.push(path);
      }
    } else pairDefectStates += 1;
    const observedOrbits = new Set();
    for (const detail of details) {
      const orbitKey = orbitRepresentative(detail.target_cells);
      observedOrbits.add(orbitKey);
      const score = Number(detail.candidate_pairs_blocked);
      if (Number.isFinite(score) && score > Number(pairOrbitScores.get(orbitKey) ?? 0)) {
        pairOrbitScores.set(orbitKey, score);
      }
      for (const pair of polycubeCellPairOrbitKeys(candidate.voxels, detail.target_cells)) addPair(pair);
    }
    for (const orbitKey of observedOrbits) {
      pairOrbitHits.set(orbitKey, (pairOrbitHits.get(orbitKey) ?? 0) + 1);
    }
    if (observedOrbits.size) pairDefectOrbitSets.push([...observedOrbits].sort());
    if (limit && verifiedStates >= limit) break outer;
  }
}

const sortedObject = map => Object.fromEntries(
  [...map.entries()]
    .filter(([, value]) => Number(value) > 0)
    .sort(([left], [right]) => left.localeCompare(right))
);
const output = {
  kind: "polycube_pair_recurrence_replay",
  candidate: id,
  layer,
  input_root: inputRoot,
  base_pair_report: basePairReportPath,
  files_read: filesRead,
  extracted_states: extractedStates,
  unique_states: uniqueStates.size,
  verified_states: verifiedStates,
  duplicate_states: duplicateStates,
  invalid_states: invalidStates,
  require_individual_coverability: requireIndividualCoverability,
  individually_incomplete_states: individuallyIncompleteStates,
  eligible_states: eligibleStates,
  pair_defect_states: pairDefectStates,
  pair_complete_states: pairCompleteWitnesses.length,
  pair_complete_witnesses: pairCompleteWitnesses,
  triple_max_cell_distance: tripleMaximumCellDistance,
  triple_audit_limit: tripleAuditLimit,
  pair_complete_triple_defect_states: tripleDefectWitnesses.length,
  triple_defect_witnesses: tripleDefectWitnesses,
  bounded_triple_complete_states: boundedTripleCompleteWitnesses.length,
  bounded_triple_complete_witnesses: boundedTripleCompleteWitnesses,
  quadruple_max_cell_distance: quadrupleMaximumCellDistance,
  bounded_triple_complete_quadruple_defect_states: quadrupleDefectWitnesses.length,
  quadruple_defect_witnesses: quadrupleDefectWitnesses,
  tuple_gate_survivor_states: tupleGateSurvivorWitnesses.length,
  tuple_gate_survivor_witnesses: tupleGateSurvivorWitnesses,
  pair_orbit_scores: sortedObject(pairOrbitScores),
  pair_orbit_hits: sortedObject(pairOrbitHits),
  pair_defect_orbit_sets: pairDefectOrbitSets,
  pairs: pairConstraints,
  warning: "Finite patch recurrence statistics are a proposal-ranking heuristic, not a tiling, non-tiling, or aperiodicity certificate."
};
mkdirSync(dirname(outputPath), { recursive: true });
writeFileSync(outputPath, `${JSON.stringify(output, null, 2)}\n`);
process.stdout.write(`${JSON.stringify({
  type: "polycube_pair_recurrence_replay",
  output: outputPath,
  files_read: filesRead,
  verified_states: verifiedStates,
  eligible_states: eligibleStates,
  pair_defect_states: pairDefectStates,
  pair_complete_states: pairCompleteWitnesses.length,
  pair_complete_triple_defect_states: tripleDefectWitnesses.length,
  tuple_gate_survivor_states: tupleGateSurvivorWitnesses.length,
  pair_orbits: pairOrbitHits.size,
  pair_constraints: pairConstraints.length
})}\n`);
