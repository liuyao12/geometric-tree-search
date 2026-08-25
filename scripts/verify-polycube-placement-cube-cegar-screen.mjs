#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { polycubeKey } from "../assets/polycube-enumerator.js";
import {
  enumeratePolycubeCoronaPlacements,
  polycubeCoronaRingCellKeys
} from "../assets/polycube-corona-search.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const reportPath = resolve(args.get("report")
  ?? fileURLToPath(new URL(
    "../data/polycube-p10-054782-placement-cube-cegar-screen-2026-08-23.json",
    import.meta.url
  )));
const archive = JSON.parse(readFileSync(reportPath, "utf8"));
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === archive.candidate);
if (!candidate) throw new Error(`unknown candidate ${archive.candidate}`);
const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const sha256 = value => createHash("sha256").update(value).digest("hex");
const failures = [];
const check = (condition, message) => {
  if (!condition) failures.push(message);
};
const readComponent = (path, expectedHash, label) => {
  const absolutePath = resolve(repositoryRoot, path);
  const contents = readFileSync(absolutePath);
  check(sha256(contents) === expectedHash, `${label} hash mismatch`);
  return JSON.parse(contents);
};

check(archive.kind === "polycube_placement_cube_cegar_screen", "unexpected archive kind");
check(polycubeKey(candidate.voxels) === archive.candidate_key, "candidate key mismatch");
check(archive.inner_layer === archive.outer_layer + 1, "inner layer is not the next radius");
check(archive.classification === "cegar_round_limit", "archive must remain explicitly inconclusive");
check(/neither a non-tiling nor an aperiodicity certificate/i.test(archive.warning), "missing warning");

const clauseReport = readComponent(
  archive.feedback.clause_report,
  archive.feedback.clause_report_sha256,
  "clause report"
);
const cellReport = readComponent(
  archive.feedback.cell_report,
  archive.feedback.cell_report_sha256,
  "cell report"
);
const replayReport = readComponent(
  archive.feedback.plain_clause_replay_report,
  archive.feedback.plain_clause_replay_report_sha256,
  "clause replay report"
);
const clauses = clauseReport.clauses;
const cells = cellReport.cells;
check(Array.isArray(clauses), "clause report lacks clauses");
check(Array.isArray(cells), "cell report lacks cells");
check(clauses?.length === archive.feedback.final_clauses, "final clause count mismatch");
check(cells?.length === archive.feedback.final_cells, "final cell count mismatch");
check(new Set(cells).size === cells.length, "duplicate cell constraint");

const placementKeys = new Set(
  enumeratePolycubeCoronaPlacements(candidate.voxels, archive.outer_layer)
    .map(placement => placement.key)
);
const normalizedClauseKeys = new Set();
for (const [index, clause] of clauses.entries()) {
  check(Array.isArray(clause) && clause.length > 0, `clause ${index} is empty`);
  const normalized = [...new Set(clause.map(String))].sort();
  check(JSON.stringify(normalized) === JSON.stringify(clause), `clause ${index} is not normalized`);
  check(normalized.every(key => placementKeys.has(key)), `clause ${index} contains an unknown placement`);
  const key = normalized.join("|");
  check(!normalizedClauseKeys.has(key), `clause ${index} is duplicated`);
  normalizedClauseKeys.add(key);
}
const nextRing = new Set(polycubeCoronaRingCellKeys(candidate.voxels, archive.inner_layer));
for (const cell of cells) check(nextRing.has(cell), `cell ${cell} is outside the next ring`);

const clausesAdded = archive.rounds.reduce((sum, round) => sum + round.clauses_added, 0);
const cellsAdded = archive.rounds.reduce((sum, round) => sum + round.cells_added, 0);
check(
  archive.feedback.initial_clauses + clausesAdded === archive.feedback.final_clauses,
  "round clause increments do not reach the final count"
);
check(
  archive.feedback.initial_cells + cellsAdded === archive.feedback.final_cells,
  "round cell increments do not reach the final count"
);
check(archive.rounds.every(round => round.proposal_placements === archive.placement_count), "proposal count mismatch");
check(archive.rounds.every(round => round.continuation_exhausted), "a recorded continuation is not exhausted");
check(archive.rounds.every(round => round.new_clause_replay === "verified"), "a round replay is unverified");

check(replayReport.classification === "verified", "plain replay is not verified");
check(replayReport.candidate === archive.candidate, "replay candidate mismatch");
check(replayReport.layer === archive.inner_layer, "replay layer mismatch");
check(replayReport.nogoods === false, "plain replay trusted nogoods");
check(replayReport.conflict_backjumping === false, "plain replay trusted conflict backjumping");
check(replayReport.clauses === clauses.length, "replay clause count mismatch");
check(replayReport.verified_clauses === clauses.length, "not every clause replayed");
check(replayReport.failed_clauses === 0, "replay has failed clauses");
check(replayReport.incomplete_clauses === 0, "replay has incomplete clauses");
check(
  replayReport.results?.length === clauses.length
    && replayReport.results.every(result => result.verified && result.status === "exact_obstruction"),
  "replay result list is not fully verified"
);

const summary = {
  kind: "polycube_placement_cube_cegar_archive_verification",
  candidate: archive.candidate,
  classification: failures.length ? "failed" : "verified_cegar_feedback_archive",
  rounds: archive.rounds.length,
  clauses_checked: clauses?.length ?? 0,
  cells_checked: cells?.length ?? 0,
  replayed_clauses: replayReport.verified_clauses,
  failures,
  warning: archive.warning
};
process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
if (failures.length) process.exitCode = 1;
