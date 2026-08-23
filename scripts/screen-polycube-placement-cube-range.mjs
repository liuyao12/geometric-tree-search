#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { polycubeKey } from "../assets/polycube-enumerator.js";

export const placementCubeOrdinals = (candidateCount, parts, index) => {
  const ordinals = [];
  for (let ordinal = index; ordinal < candidateCount; ordinal += parts) ordinals.push(ordinal);
  return ordinals;
};

export const splitPlacementCubeBranch = ({ parts, index }, candidateCount, maximumParts) => {
  const childParts = parts * 2;
  if (childParts > maximumParts) return [];
  return [index, index + parts]
    .filter(childIndex => childIndex < candidateCount)
    .map(childIndex => ({ parts: childParts, index: childIndex }));
};

export const initialPlacementCubeBranches = (
  candidateCount,
  initialParts,
  maximumParts,
  preRefineIndices = []
) => {
  const preRefined = new Set(preRefineIndices);
  const branches = [];
  for (let index = 0; index < Math.min(initialParts, candidateCount); index += 1) {
    const branch = { parts: initialParts, index };
    if (preRefined.has(index)) {
      branches.push(...splitPlacementCubeBranch(branch, candidateCount, maximumParts));
    } else {
      branches.push(branch);
    }
  }
  return branches;
};

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

const validateBranchReport = (report, expected) => {
  for (const [field, value] of Object.entries(expected)) {
    if (report[field] !== value) throw new Error(`resumed branch disagrees on ${field}`);
  }
  if (!report.placement_cube_base_formula_sha256) {
    throw new Error("branch report lacks a base-formula digest");
  }
};

const sha256 = value => createHash("sha256").update(value).digest("hex");
const fileSha256 = path => path ? sha256(readFileSync(path)) : null;

export async function main(arguments_ = process.argv.slice(2)) {
  const args = parseArguments(arguments_);
  const id = args.get("id") ?? "p10-052588";
  const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
  if (!candidate) throw new Error(`unknown polycube candidate: ${id}`);
  const layer = integerArgument(args, "layer", 3, 1);
  const minimumCount = integerArgument(args, "min-count", 1, 1);
  const maximumCount = integerArgument(args, "max-count", minimumCount, minimumCount);
  const anchorCell = args.get("anchor-cell");
  if (!anchorCell) throw new Error("--anchor-cell is required");
  const initialParts = integerArgument(args, "initial-parts", 16, 2);
  const maximumParts = integerArgument(args, "max-parts", 128, initialParts);
  if (maximumParts % initialParts !== 0) {
    throw new Error("--max-parts must be a multiple of --initial-parts");
  }
  const preRefineIndices = String(args.get("pre-refine-indices") ?? "")
    .split(",")
    .filter(Boolean)
    .map(value => Number(value))
    .sort((left, right) => left - right);
  if (new Set(preRefineIndices).size !== preRefineIndices.length
      || preRefineIndices.some(index => !Number.isInteger(index) || index <= 0 || index >= initialParts)) {
    throw new Error("--pre-refine-indices must be distinct comma-separated indices between 1 and initial-parts - 1");
  }
  if (preRefineIndices.length && maximumParts < initialParts * 2) {
    throw new Error("--max-parts must permit one split when --pre-refine-indices is used");
  }
  const timeoutMs = integerArgument(args, "timeout-ms", 60_000, 1);
  const processGraceMs = integerArgument(args, "process-grace-ms", 120_000, 1);
  const randomSeed = integerArgument(args, "random-seed", 0, 0);
  const backend = args.get("backend") ?? "pb2bv-sat";
  const pbSolver = args.get("pb-solver") ?? "solver";
  const lookaheadEncoding = args.get("lookahead-conflict-encoding") ?? "grouped-pb";
  const python = args.get("python") ?? "python3";
  const outputDirectory = resolve(args.get("output-dir") ?? `runs/${id}-placement-cube-range`);
  const reportOutput = resolve(args.get("report-output") ?? `${outputDirectory}/summary.json`);
  const initialClauseReport = args.get("initial-clause-report")
    ? resolve(args.get("initial-clause-report"))
    : null;
  const initialCellReport = args.get("initial-cell-report")
    ? resolve(args.get("initial-cell-report"))
    : null;
  const resume = booleanArgument(args, "resume", true);
  const solver = fileURLToPath(new URL("./solve_polycube_corona_z3.py", import.meta.url));
  const verifier = fileURLToPath(new URL("./verify-polycube-placement-cube-cover.mjs", import.meta.url));
  mkdirSync(outputDirectory, { recursive: true });
  mkdirSync(dirname(reportOutput), { recursive: true });
  const runConfiguration = {
    version: 1,
    candidate: id,
    candidate_key: polycubeKey(candidate.voxels),
    layer,
    minimum_count: minimumCount,
    maximum_count: maximumCount,
    anchor_cell: anchorCell,
    initial_parts: initialParts,
    maximum_parts: maximumParts,
    timeout_milliseconds: timeoutMs,
    backend,
    pb_solver: pbSolver,
    lookahead_conflict_encoding: lookaheadEncoding,
    random_seed: randomSeed,
    initial_clause_report: initialClauseReport,
    initial_clause_report_sha256: fileSha256(initialClauseReport),
    initial_cell_report: initialCellReport,
    initial_cell_report_sha256: fileSha256(initialCellReport)
  };
  if (preRefineIndices.length) runConfiguration.pre_refine_indices = preRefineIndices;
  const runConfigurationSha256 = sha256(JSON.stringify(runConfiguration));
  const runConfigurationPath = resolve(outputDirectory, "run-configuration.json");
  if (existsSync(runConfigurationPath)) {
    const previousConfiguration = JSON.parse(readFileSync(runConfigurationPath, "utf8"));
    if (JSON.stringify(previousConfiguration) !== JSON.stringify(runConfiguration)) {
      throw new Error("output directory contains a different placement-cube run configuration");
    }
  } else {
    writeFileSync(runConfigurationPath, `${JSON.stringify(runConfiguration, null, 2)}\n`);
  }

  let launchedBranches = 0;
  let resumedBranches = 0;
  let seedOffset = 0;
  const countResults = [];
  for (let count = minimumCount; count <= maximumCount; count += 1) {
    const cachePath = resolve(outputDirectory, `exact-${count}-base.smt2`);
    const pending = [{ parts: initialParts, index: 0 }];
    const queued = new Set([`${initialParts}:0`]);
    const exhaustedReports = [];
    const openReports = [];
    let satReport = null;
    let candidateCount = null;
    while (pending.length && !satReport) {
      const branch = pending.shift();
      const seed = randomSeed + seedOffset;
      seedOffset += 1;
      const branchPath = resolve(
        outputDirectory,
        `exact-${count}-parts-${branch.parts}-index-${branch.index}-seed-${seed}.json`
      );
      let report;
      let wasResumed = false;
      if (resume && existsSync(branchPath)) {
        report = JSON.parse(readFileSync(branchPath, "utf8"));
        resumedBranches += 1;
        wasResumed = true;
      } else {
        const solverArguments = [
          solver,
          `--key=${polycubeKey(candidate.voxels)}`,
          `--layer=${layer}`,
          `--timeout-ms=${timeoutMs}`,
          `--backend=${backend}`,
          `--pb-solver=${pbSolver}`,
          `--random-seed=${seed}`,
          `--min-placements=${count}`,
          `--max-placements=${count}`,
          `--placement-cube-cell=${anchorCell}`,
          `--placement-cube-parts=${branch.parts}`,
          `--placement-cube-index=${branch.index}`,
          `--lookahead-conflict-encoding=${lookaheadEncoding}`,
          `--formula-cache=${cachePath}`,
          `--output=${branchPath}`
        ];
        if (initialClauseReport) solverArguments.push(`--forbidden-clause-report=${initialClauseReport}`);
        if (initialCellReport) solverArguments.push(`--cell-coverability-report=${initialCellReport}`);
        const solved = spawnSync(python, solverArguments, {
          encoding: "utf8",
          timeout: timeoutMs + processGraceMs,
          maxBuffer: 32 * 1024 * 1024
        });
        if (solved.status !== 0) {
          throw new Error(solved.stderr.trim() || solved.error?.message || `solver exited ${solved.status}`);
        }
        report = JSON.parse(readFileSync(branchPath, "utf8"));
        launchedBranches += 1;
      }
      validateBranchReport(report, {
        key: polycubeKey(candidate.voxels),
        layer,
        min_placements: count,
        max_placements: count,
        placement_cube_cell: anchorCell,
        placement_cube_parts: branch.parts,
        placement_cube_index: branch.index
      });
      if (candidateCount === null) {
        candidateCount = report.placement_cube_candidates;
        for (const initialBranch of initialPlacementCubeBranches(
          candidateCount,
          initialParts,
          maximumParts,
          preRefineIndices
        )) {
          const key = `${initialBranch.parts}:${initialBranch.index}`;
          if (queued.has(key)) continue;
          pending.push(initialBranch);
          queued.add(key);
        }
      } else if (report.placement_cube_candidates !== candidateCount) {
        throw new Error("branch reports disagree on the anchor candidate count");
      }
      process.stdout.write(`${JSON.stringify({
        type: "placement_cube_branch",
        placement_count: count,
        parts: branch.parts,
        index: branch.index,
        selected: report.placement_cube_selected_candidates,
        z3_status: report.z3_status,
        resumed: wasResumed,
        check_milliseconds: report.check_milliseconds
      })}\n`);
      if (report.z3_status === "unsat") {
        exhaustedReports.push(branchPath);
      } else if (report.z3_status === "sat") {
        satReport = branchPath;
      } else {
        const children = splitPlacementCubeBranch(branch, candidateCount, maximumParts);
        if (!children.length) {
          openReports.push(branchPath);
        } else {
          for (const child of children) {
            const key = `${child.parts}:${child.index}`;
            if (queued.has(key)) continue;
            queued.add(key);
            pending.push(child);
          }
        }
      }
    }

    let classification = "placement_cube_cover_incomplete";
    let certificate = null;
    if (satReport) {
      classification = "sat_outer_proposal_requires_continuation";
    } else if (!openReports.length) {
      const certificatePath = resolve(outputDirectory, `exact-${count}-certificate.json`);
      const verified = spawnSync(process.execPath, [
        verifier,
        `--output=${certificatePath}`,
        ...exhaustedReports
      ], { encoding: "utf8", timeout: 30_000, maxBuffer: 16 * 1024 * 1024 });
      if (verified.status !== 0) {
        throw new Error(verified.stderr.trim() || `coverage verifier exited ${verified.status}`);
      }
      certificate = certificatePath;
      classification = "placement_cube_cover_exhausted";
    }
    countResults.push({
      placement_count: count,
      classification,
      anchor_placement_candidates: candidateCount,
      exhausted_branch_reports: exhaustedReports,
      open_branch_reports: openReports,
      sat_branch_report: satReport,
      certificate
    });
    if (satReport || openReports.length) break;
  }

  const summary = {
    kind: "polycube_placement_cube_range_screen",
    candidate: id,
    layer,
    minimum_count: minimumCount,
    maximum_count: maximumCount,
    anchor_cell: anchorCell,
    initial_parts: initialParts,
    maximum_parts: maximumParts,
    pre_refine_indices: preRefineIndices,
    timeout_milliseconds: timeoutMs,
    launched_branches: launchedBranches,
    resumed_branches: resumedBranches,
    run_configuration: runConfigurationPath,
    run_configuration_sha256: runConfigurationSha256,
    counts: countResults,
    classification: countResults.every(result => result.classification === "placement_cube_cover_exhausted")
      && countResults.length === maximumCount - minimumCount + 1
      ? "placement_cube_range_exhausted"
      : countResults.at(-1)?.classification ?? "placement_cube_cover_incomplete",
    warning: "A bounded exact-count range proves neither non-tiling nor aperiodicity. SAT outer proposals require exact continuation verification."
  };
  writeFileSync(reportOutput, `${JSON.stringify(summary, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify({
    type: "placement_cube_range_summary",
    report: reportOutput,
    classification: summary.classification,
    counts: countResults.length,
    launched_branches: launchedBranches,
    resumed_branches: resumedBranches
  })}\n`);
  return summary;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
