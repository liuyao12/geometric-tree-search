#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  polycubeCellOrbitKeys,
  polycubeCoronaRingCellKeys,
  polycubePlacementClauseOrbitKeys,
  searchPolycubeCorona,
  verifyPolycubeCoronaPatch
} from "../assets/polycube-corona-search.js";
import { main as screenPlacementCubeRange } from "./screen-polycube-placement-cube-range.mjs";

const parseArguments = arguments_ => new Map(arguments_.map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));

const integerArgument = (args, name, fallback, minimum = 0) => {
  const value = Number(args.get(name) ?? fallback);
  if (!Number.isInteger(value) || value < minimum) {
    throw new Error(`--${name} must be an integer at least ${minimum}`);
  }
  return value;
};

const booleanArgument = (args, name, fallback) => {
  if (!args.has(name)) return fallback;
  return !["0", "false", "no"].includes(String(args.get(name)).toLowerCase());
};

const sha256 = value => createHash("sha256").update(value).digest("hex");
const placementKey = placement => placement.cells.map(cell => cell.join(",")).sort().join(";");
const normalizeClause = clause => [...new Set(clause.map(String))].sort();
const clauseKey = clause => normalizeClause(clause).join("|");

const readListReport = (path, fields) => {
  if (!path) return [];
  const report = JSON.parse(readFileSync(resolve(path), "utf8"));
  for (const field of fields) if (Array.isArray(report?.[field])) return report[field];
  if (Array.isArray(report)) return report;
  throw new Error(`${path} must contain ${fields.join(" or ")}`);
};

const writeJson = (path, value) => {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
};

const CEGAR_ARGUMENTS = new Set([
  "cegar-rounds",
  "continuation-layer",
  "continuation-time-ms",
  "continuation-nodes",
  "feedback-verification-time-ms",
  "feedback-verification-nodes",
  "symmetry-clauses",
  "learn-cell-coverability",
  "formula-cache-dir",
  "formula-cache-scope",
  "propagate-values",
  "output-dir",
  "report-output",
  "initial-clause-report",
  "initial-cell-report"
]);

const argumentName = argument => {
  const separator = argument.indexOf("=");
  return argument.slice(2, separator < 0 ? undefined : separator);
};

export async function main(arguments_ = process.argv.slice(2)) {
  const args = parseArguments(arguments_);
  const id = args.get("id") ?? "p10-052588";
  const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
  if (!candidate) throw new Error(`unknown polycube candidate: ${id}`);
  const outerLayer = integerArgument(args, "layer", 3, 1);
  const innerLayer = integerArgument(args, "continuation-layer", outerLayer + 1, outerLayer + 1);
  const maximumRounds = integerArgument(args, "cegar-rounds", 25, 1);
  const continuationTimeMs = integerArgument(args, "continuation-time-ms", 60_000, 1);
  const continuationNodes = integerArgument(args, "continuation-nodes", 1_000_000, 1);
  const verificationTimeMs = integerArgument(
    args,
    "feedback-verification-time-ms",
    continuationTimeMs,
    1
  );
  const verificationNodes = integerArgument(
    args,
    "feedback-verification-nodes",
    continuationNodes,
    1
  );
  const symmetryClauses = booleanArgument(args, "symmetry-clauses", true);
  const learnCellCoverability = booleanArgument(args, "learn-cell-coverability", true);
  const outputDirectory = resolve(args.get("output-dir") ?? `runs/${id}-placement-cube-cegar`);
  const reportOutput = resolve(args.get("report-output") ?? `${outputDirectory}/summary.json`);
  const formulaCacheDirectory = resolve(
    args.get("formula-cache-dir") ?? resolve(outputDirectory, "base-formulas")
  );
  const formulaCacheScope = args.get("formula-cache-scope") ?? "next-ring-universe";
  if (!["feedback", "next-ring-universe"].includes(formulaCacheScope)) {
    throw new Error("--formula-cache-scope must be feedback or next-ring-universe");
  }
  const propagateValues = booleanArgument(args, "propagate-values", true);
  const verifier = fileURLToPath(new URL("./verify-polycube-corona-clause-report.mjs", import.meta.url));
  const nodeExecutable = process.execPath;
  mkdirSync(outputDirectory, { recursive: true });
  mkdirSync(formulaCacheDirectory, { recursive: true });

  const clauses = [];
  const clauseKeys = new Set();
  const cells = [];
  const cellKeys = new Set();
  const addClause = rawClause => {
    const normalized = normalizeClause(rawClause);
    if (!normalized.length) throw new Error("an exact continuation produced an empty clause");
    const key = clauseKey(normalized);
    if (clauseKeys.has(key)) return false;
    clauseKeys.add(key);
    clauses.push(normalized);
    return true;
  };
  const addCell = rawCell => {
    const key = Array.isArray(rawCell) ? rawCell.join(",") : String(rawCell);
    if (cellKeys.has(key)) return false;
    cellKeys.add(key);
    cells.push(key);
    return true;
  };
  for (const clause of readListReport(args.get("initial-clause-report"), ["learned_clauses", "clauses"])) {
    addClause(clause);
  }
  for (const cell of readListReport(args.get("initial-cell-report"), ["cell_coverability_cells", "cells"])) {
    addCell(cell);
  }
  const initialClauseCount = clauses.length;
  const initialCellCount = cells.length;
  const nextRingCells = new Set(polycubeCoronaRingCellKeys(candidate.voxels, innerLayer));
  for (const cell of cells) {
    if (!nextRingCells.has(cell)) throw new Error(`initial coverability cell ${cell} is not in radius ${innerLayer}`);
  }

  const forwardedArguments = arguments_.filter(argument => !CEGAR_ARGUMENTS.has(argumentName(argument)));
  const rounds = [];
  let classification = "cegar_round_limit";
  let radiusWitness = null;
  for (let round = 0; round < maximumRounds; round += 1) {
    const roundLabel = String(round).padStart(3, "0");
    const roundDirectory = resolve(outputDirectory, `round-${roundLabel}`);
    const clauseReport = resolve(outputDirectory, `feedback-round-${roundLabel}-clauses.json`);
    const cellReport = resolve(outputDirectory, `feedback-round-${roundLabel}-cells.json`);
    const rangeReport = resolve(roundDirectory, "summary.json");
    writeJson(clauseReport, { clauses });
    writeJson(cellReport, { cells });
    const range = await screenPlacementCubeRange([
      ...forwardedArguments,
      `--output-dir=${roundDirectory}`,
      `--report-output=${rangeReport}`,
      `--formula-cache-dir=${formulaCacheDirectory}`,
      `--formula-cache-scope=${formulaCacheScope}`,
      `--propagate-values=${propagateValues}`,
      `--initial-clause-report=${clauseReport}`,
      `--initial-cell-report=${cellReport}`
    ]);
    const rangeResult = range.counts.at(-1);
    const record = {
      round,
      range_report: rangeReport,
      range_classification: range.classification,
      clause_constraints_before: clauses.length,
      cell_constraints_before: cells.length,
      sat_branch_report: rangeResult?.sat_branch_report ?? null
    };
    if (!rangeResult?.sat_branch_report) {
      classification = range.classification;
      rounds.push(record);
      break;
    }

    const proposalReport = JSON.parse(readFileSync(rangeResult.sat_branch_report, "utf8"));
    const proposal = proposalReport.radius_witness?.corona ?? proposalReport.corona;
    if (!Array.isArray(proposal)) throw new Error("SAT branch report does not contain a corona");
    const outerVerification = verifyPolycubeCoronaPatch(candidate.voxels, proposal, outerLayer);
    if (!outerVerification.verified) {
      throw new Error(`SAT branch failed radius-${outerLayer} verification: ${outerVerification.reason}`);
    }
    const continuation = searchPolycubeCorona(candidate.voxels, {
      layers: innerLayer,
      seed: round,
      fixedPlacements: proposal,
      nodeLimit: continuationNodes,
      timeLimitMs: continuationTimeMs,
      timeBudgetMode: "cpu",
      nogoods: true,
      conflictBackjumping: true
    });
    Object.assign(record, {
      outer_placements: proposal.length,
      continuation_success: continuation.success,
      continuation_exhausted: continuation.exhausted,
      continuation_stopped_by: continuation.stopped_by,
      continuation_nodes: continuation.nodes,
      continuation_milliseconds: continuation.milliseconds
    });
    if (continuation.success) {
      const verification = verifyPolycubeCoronaPatch(candidate.voxels, continuation.corona, innerLayer);
      if (!verification.verified) {
        throw new Error(`continuation witness failed radius-${innerLayer} verification: ${verification.reason}`);
      }
      classification = "verified_inner_radius_witness";
      radiusWitness = continuation;
      rounds.push(record);
      break;
    }
    if (!continuation.exhausted) {
      classification = "continuation_incomplete";
      rounds.push(record);
      break;
    }

    const immediateObstructions = continuation.fixed_obstruction_nogoods
      ?.filter(obstruction => obstruction?.fixed_placement_keys?.length) ?? [];
    const primaryObstruction = continuation.fixed_obstruction_nogood;
    const obstructionClauses = immediateObstructions.length
      ? immediateObstructions.map(obstruction => obstruction.fixed_placement_keys)
      : primaryObstruction?.fixed_placement_keys?.length
        ? [primaryObstruction.fixed_placement_keys]
        : [proposal.map(placementKey)];
    const clauseCountBeforeFeedback = clauses.length;
    const cellCountBeforeFeedback = cells.length;
    const newlyLearnedClauses = [];
    for (const rawClause of obstructionClauses) {
      const orbit = symmetryClauses
        ? polycubePlacementClauseOrbitKeys(candidate.voxels, rawClause)
        : [rawClause];
      for (const clause of orbit) {
        if (addClause(clause)) newlyLearnedClauses.push(normalizeClause(clause));
      }
    }
    let cellsAdded = 0;
    if (learnCellCoverability) for (const obstruction of immediateObstructions) {
      const cell = obstruction.target_cell?.join(",");
      if (!cell || !nextRingCells.has(cell)) {
        throw new Error(`continuation obstruction cell ${cell ?? "<missing>"} is not in radius ${innerLayer}`);
      }
      for (const orbitCell of polycubeCellOrbitKeys(candidate.voxels, cell)) {
        if (!nextRingCells.has(orbitCell)) {
          throw new Error(`symmetric obstruction cell ${orbitCell} is not in radius ${innerLayer}`);
        }
        cellsAdded += Number(addCell(orbitCell));
      }
    }
    Object.assign(record, {
      immediate_obstructions: immediateObstructions.length,
      obstruction_clause_sizes: obstructionClauses.map(clause => clause.length),
      clauses_added: newlyLearnedClauses.length,
      cells_added: cellsAdded,
      clause_constraints_after: clauses.length,
      cell_constraints_after: cells.length
    });
    if (!newlyLearnedClauses.length && !cellsAdded) {
      classification = "feedback_stalled";
      rounds.push(record);
      break;
    }
    if (newlyLearnedClauses.length) {
      const newClauseReport = resolve(outputDirectory, `round-${roundLabel}-new-clauses.json`);
      const verificationReport = resolve(outputDirectory, `round-${roundLabel}-clause-replay.json`);
      writeJson(newClauseReport, { clauses: newlyLearnedClauses });
      const replay = spawnSync(nodeExecutable, [
        verifier,
        `--id=${id}`,
        `--layer=${innerLayer}`,
        `--clause-report=${newClauseReport}`,
        `--node-limit=${verificationNodes}`,
        `--time-ms=${verificationTimeMs}`,
        "--nogoods=false",
        "--conflict-backjumping=false",
        `--output=${verificationReport}`
      ], { encoding: "utf8", timeout: verificationTimeMs * newlyLearnedClauses.length + 30_000 });
      if (replay.status !== 0) {
        throw new Error(replay.stderr.trim() || `clause replay exited ${replay.status}`);
      }
      const replayReport = JSON.parse(readFileSync(verificationReport, "utf8"));
      record.clause_replay_report = verificationReport;
      record.clause_replay_classification = replayReport.classification;
      record.clauses_replayed = replayReport.clauses;
      if (replayReport.classification !== "verified") {
        for (const clause of clauses.splice(clauseCountBeforeFeedback)) {
          clauseKeys.delete(clauseKey(clause));
        }
        for (const cell of cells.splice(cellCountBeforeFeedback)) cellKeys.delete(cell);
        record.feedback_rejected = true;
        record.rejected_clauses = newlyLearnedClauses.length;
        record.rejected_cells = cellsAdded;
        record.clauses_added = 0;
        record.cells_added = 0;
        record.clause_constraints_after = clauses.length;
        record.cell_constraints_after = cells.length;
        classification = "feedback_verification_incomplete";
        rounds.push(record);
        break;
      }
    }
    rounds.push(record);
    process.stdout.write(`${JSON.stringify({ type: "placement_cube_cegar_round", ...record })}\n`);
  }

  const finalClauseReport = resolve(outputDirectory, "final-clauses.json");
  const finalCellReport = resolve(outputDirectory, "final-cells.json");
  writeJson(finalClauseReport, { clauses });
  writeJson(finalCellReport, { cells });
  const summary = {
    kind: "polycube_placement_cube_cegar_screen",
    candidate: id,
    outer_layer: outerLayer,
    inner_layer: innerLayer,
    classification,
    maximum_rounds: maximumRounds,
    formula_cache_scope: formulaCacheScope,
    exact_availability: booleanArgument(args, "exact-availability", false),
    propagate_values: propagateValues,
    rounds,
    initial_clause_constraints: initialClauseCount,
    initial_cell_constraints: initialCellCount,
    final_clause_constraints: clauses.length,
    final_cell_constraints: cells.length,
    final_clause_report: finalClauseReport,
    final_clause_report_sha256: sha256(readFileSync(finalClauseReport)),
    final_cell_report: finalCellReport,
    final_cell_report_sha256: sha256(readFileSync(finalCellReport)),
    radius_witness: radiusWitness ? {
      placements: radiusWitness.corona.length,
      nodes: radiusWitness.nodes,
      milliseconds: radiusWitness.milliseconds,
      corona: radiusWitness.corona
    } : null,
    warning: classification === "verified_inner_radius_witness"
      ? "A verified finite-radius witness is not an infinite tiling or an aperiodicity certificate."
      : "Only exact exhausted placement-cube coverage, together with audited necessary constraints, can contribute to a non-tiling certificate."
  };
  writeJson(reportOutput, summary);
  process.stdout.write(`${JSON.stringify({
    type: "placement_cube_cegar_summary",
    report: reportOutput,
    classification,
    rounds: rounds.length,
    clauses: clauses.length,
    cells: cells.length
  })}\n`);
  return summary;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
