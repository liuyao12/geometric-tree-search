#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { polycubeKey } from "../assets/polycube-enumerator.js";
import {
  polycubePlacementClauseOrbitKeys,
  searchPolycubeCorona,
  verifyPolycubeCoronaPatch
} from "../assets/polycube-corona-search.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const integerArg = (name, fallback, minimum = 0) => {
  const value = Number(args.get(name) ?? fallback);
  if (!Number.isInteger(value) || value < minimum) {
    throw new Error(`--${name} must be an integer at least ${minimum}`);
  }
  return value;
};
const booleanArg = (name, fallback) => {
  if (!args.has(name)) return fallback;
  return !["0", "false", "no"].includes(String(args.get(name)).toLowerCase());
};

const id = args.get("id") ?? "p9-42947";
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);
const outerLayer = integerArg("outer-layer", 4, 1);
const innerLayer = integerArg("inner-layer", outerLayer + 1, outerLayer + 1);
const iterations = integerArg("iterations", 50, 1);
const z3TimeoutMs = integerArg("z3-timeout-ms", 30_000, 1);
const continuationTimeMs = integerArg("continuation-time-ms", 10_000, 1);
const continuationNodes = integerArg("continuation-nodes", 10_000_000, 1);
const nogoodLimit = integerArg("nogood-limit", 500_000, 1);
const backend = args.get("backend") ?? "pb2bv-sat";
const randomSeed = integerArg("random-seed", 0, 0);
const seedStride = integerArg("seed-stride", 0, 0);
const maxPlacements = args.has("max-placements")
  ? integerArg("max-placements", 1, 1)
  : null;
const progressEvery = integerArg("progress-every", 1, 1);
const symmetryClauses = booleanArg("symmetry-clauses", true);
const continueOnZ3Unknown = booleanArg("continue-on-z3-unknown", true);
const python = args.get("python") ?? "python3";
const outputDirectory = resolve(args.get("output-dir") ?? `runs/${id}-radius${outerLayer}-to-${innerLayer}-z3-cegar`);
const reportOutput = resolve(args.get("report-output") ?? `${outputDirectory}/summary.json`);
const initialClauseReport = args.get("initial-clause-report")
  ? resolve(args.get("initial-clause-report"))
  : null;
const pythonSolver = fileURLToPath(new URL("./solve_polycube_corona_z3.py", import.meta.url));
const clausePath = resolve(outputDirectory, "forbidden-clauses.json");
mkdirSync(outputDirectory, { recursive: true });

const clauses = [];
const clauseKeys = new Set();
const trials = [];
let classification = "iteration_limit";
let radiusWitness = null;
let z3UnknownTrials = 0;

const placementKey = placement => placement.cells.map(cell => cell.join(",")).sort().join(";");
const addClause = rawClause => {
  const normalized = [...new Set(rawClause.map(String))].sort();
  if (!normalized.length) throw new Error("A continuation obstruction produced an empty clause");
  const key = normalized.join("|");
  if (clauseKeys.has(key)) return false;
  clauseKeys.add(key);
  clauses.push(normalized);
  return true;
};
const addClauseOrbit = rawClause => {
  const orbit = symmetryClauses
    ? polycubePlacementClauseOrbitKeys(candidate.voxels, rawClause)
    : [rawClause];
  let added = 0;
  for (const clause of orbit) added += Number(addClause(clause));
  return added;
};
if (initialClauseReport) {
  const initial = JSON.parse(readFileSync(initialClauseReport, "utf8"));
  const initialClauses = initial.learned_clauses ?? initial.clauses ?? initial;
  if (!Array.isArray(initialClauses)) {
    throw new Error("--initial-clause-report must contain learned_clauses or clauses");
  }
  for (const clause of initialClauses) addClauseOrbit(clause);
}
const initialClauseCount = clauses.length;

process.stdout.write(`${JSON.stringify({
  type: "z3_cegar_start",
  id,
  outer_layer: outerLayer,
  inner_layer: innerLayer,
  iterations,
  z3_timeout_ms: z3TimeoutMs,
  continuation_time_ms: continuationTimeMs,
  continuation_nodes: continuationNodes,
  backend,
  random_seed: randomSeed,
  seed_stride: seedStride,
  max_placements: maxPlacements,
  symmetry_clauses: symmetryClauses,
  continue_on_z3_unknown: continueOnZ3Unknown,
  initial_clause_count: initialClauseCount,
  output_directory: outputDirectory
})}\n`);

for (let iteration = 0; iteration < iterations; iteration += 1) {
  writeFileSync(clausePath, `${JSON.stringify({ clauses }, null, 2)}\n`);
  const witnessPath = resolve(outputDirectory, `outer-witness-${String(iteration).padStart(4, "0")}.json`);
  const iterationSeed = randomSeed + iteration * seedStride;
  const solverArguments = [
    pythonSolver,
    `--key=${polycubeKey(candidate.voxels)}`,
    `--layer=${outerLayer}`,
    `--timeout-ms=${z3TimeoutMs}`,
    `--backend=${backend}`,
    `--random-seed=${iterationSeed}`,
    `--forbidden-clause-report=${clausePath}`,
    `--output=${witnessPath}`
  ];
  if (maxPlacements !== null) solverArguments.push(`--max-placements=${maxPlacements}`);
  const solved = spawnSync(python, solverArguments, {
    encoding: "utf8",
    timeout: z3TimeoutMs + 60_000,
    maxBuffer: 16 * 1024 * 1024
  });
  if (solved.status !== 0) {
    throw new Error(solved.stderr.trim() || `Z3 proposal process exited ${solved.status}`);
  }
  const proposal = JSON.parse(readFileSync(witnessPath, "utf8"));
  if (proposal.z3_status === "unsat") {
    classification = maxPlacements !== null
      ? "placement_bound_exhausted"
      : initialClauseCount > 0
        ? "conditional_unsat"
        : "certified_non_tiler";
    trials.push({ iteration, random_seed: iterationSeed, z3_status: "unsat", z3_milliseconds: proposal.milliseconds, clauses: clauses.length });
    break;
  }
  if (proposal.z3_status !== "sat") {
    z3UnknownTrials += 1;
    const trial = {
      iteration,
      random_seed: iterationSeed,
      z3_status: proposal.z3_status,
      z3_milliseconds: proposal.milliseconds,
      reason_unknown: proposal.reason_unknown,
      clauses: clauses.length
    };
    trials.push(trial);
    if (iteration % progressEvery === 0 || iteration + 1 === iterations) {
      process.stdout.write(`${JSON.stringify({ type: "z3_cegar_trial", ...trial })}\n`);
    }
    if (continueOnZ3Unknown) continue;
    classification = "z3_incomplete";
    break;
  }
  const outerVerification = verifyPolycubeCoronaPatch(candidate.voxels, proposal.corona, outerLayer);
  if (!outerVerification.verified) {
    throw new Error(`Z3 outer witness ${iteration} failed verification: ${outerVerification.reason}`);
  }
  const continuation = searchPolycubeCorona(candidate.voxels, {
    layers: innerLayer,
    seed: iterationSeed,
    fixedPlacements: proposal.corona,
    nodeLimit: continuationNodes,
    timeLimitMs: continuationTimeMs,
    timeBudgetMode: "cpu",
    nogoods: true,
    conflictBackjumping: true,
    nogoodLimit
  });
  if (continuation.success) {
    const verification = verifyPolycubeCoronaPatch(candidate.voxels, continuation.corona, innerLayer);
    if (!verification.verified) {
      throw new Error(`Radius-${innerLayer} witness failed verification: ${verification.reason}`);
    }
    classification = "verified_inner_radius_witness";
    radiusWitness = continuation;
    trials.push({
      iteration,
      random_seed: iterationSeed,
      z3_status: "sat",
      z3_milliseconds: proposal.milliseconds,
      outer_placements: proposal.corona.length,
      continuation_success: true,
      continuation_nodes: continuation.nodes,
      continuation_milliseconds: continuation.milliseconds,
      clauses: clauses.length
    });
    break;
  }
  if (!continuation.exhausted) {
    classification = "continuation_incomplete";
    trials.push({
      iteration,
      random_seed: iterationSeed,
      z3_status: "sat",
      z3_milliseconds: proposal.milliseconds,
      outer_placements: proposal.corona.length,
      continuation_success: false,
      continuation_exhausted: false,
      continuation_nodes: continuation.nodes,
      continuation_milliseconds: continuation.milliseconds,
      clauses: clauses.length
    });
    break;
  }
  const obstruction = continuation.fixed_obstruction_nogood;
  const learnedClause = obstruction?.fixed_placement_keys?.length
    ? obstruction.fixed_placement_keys
    : proposal.corona.map(placementKey);
  const clausesAdded = addClauseOrbit(learnedClause);
  const trial = {
    iteration,
    random_seed: iterationSeed,
    z3_status: "sat",
    z3_milliseconds: proposal.milliseconds,
    outer_placements: proposal.corona.length,
    continuation_success: false,
    continuation_exhausted: true,
    continuation_nodes: continuation.nodes,
    continuation_milliseconds: continuation.milliseconds,
    obstruction_kind: obstruction?.fixed_placement_keys?.length
      ? obstruction.kind ?? "immediate_dead_target"
      : "full_outer_state",
    learned_clause_size: learnedClause.length,
    clauses_added: clausesAdded,
    clauses: clauses.length
  };
  trials.push(trial);
  if (iteration % progressEvery === 0 || iteration + 1 === iterations) {
    process.stdout.write(`${JSON.stringify({ type: "z3_cegar_trial", ...trial })}\n`);
  }
  if (!clausesAdded) {
    classification = "duplicate_obstruction";
    break;
  }
}

const summary = {
  kind: "polycube_corona_z3_cegar",
  candidate: id,
  outer_layer: outerLayer,
  inner_layer: innerLayer,
  classification,
  backend,
  random_seed: randomSeed,
  seed_stride: seedStride,
  max_placements: maxPlacements,
  symmetry_clauses: symmetryClauses,
  continue_on_z3_unknown: continueOnZ3Unknown,
  z3_unknown_trials: z3UnknownTrials,
  z3_timeout_ms: z3TimeoutMs,
  continuation_time_ms: continuationTimeMs,
  continuation_nodes: continuationNodes,
  trials,
  learned_clauses: clauses,
  learned_clause_count: clauses.length,
  initial_clause_count: initialClauseCount,
  radius_witness: radiusWitness ? {
    placements: radiusWitness.corona.length,
    corona: radiusWitness.corona
  } : null,
  warning: ["certified_non_tiler", "verified_inner_radius_witness"].includes(classification)
    ? null
    : classification === "placement_bound_exhausted"
      ? `The exact CEGAR loop exhausted only outer patches with at most ${maxPlacements} placements; this is not a non-tiling or aperiodicity certificate.`
      : classification === "conditional_unsat"
        ? "UNSAT depends on imported clauses; independently replay their continuation proofs before classifying the candidate as a non-tiler."
      : "An incomplete CEGAR portfolio proves neither non-tiling nor aperiodicity."
};
writeFileSync(reportOutput, `${JSON.stringify(summary, null, 2)}\n`);
process.stdout.write(`${JSON.stringify({
  type: "z3_cegar_summary",
  candidate: id,
  classification,
  trials: trials.length,
  learned_clause_count: clauses.length,
  radius_witness_placements: radiusWitness?.corona.length ?? null,
  report_output: reportOutput,
  warning: summary.warning
})}\n`);
