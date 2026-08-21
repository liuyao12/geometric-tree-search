#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { polycubeKey } from "../assets/polycube-enumerator.js";
import {
  polycubeCellOrbitKeys,
  polycubeCellPairOrbitKeys,
  polycubeCellQuadrupleOrbitKeys,
  polycubeCellTripleOrbitKeys,
  polycubeCoronaIncompatibleTargetPairDetails,
  polycubeCoronaIncompatibleTargetQuadrupleDetails,
  polycubeCoronaIncompatibleTargetTripleDetails,
  polycubeCoronaRingCellKeys,
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
const z3ProcessGraceMs = integerArg("z3-process-grace-ms", 120_000, 1);
const continuationTimeMs = integerArg("continuation-time-ms", 10_000, 1);
const continuationNodes = integerArg("continuation-nodes", 10_000_000, 1);
const nogoodLimit = integerArg("nogood-limit", 500_000, 1);
const backend = args.get("backend") ?? "pb2bv-sat";
const randomSeed = integerArg("random-seed", 0, 0);
const seedStride = integerArg("seed-stride", 0, 0);
const minPlacements = args.has("min-placements")
  ? integerArg("min-placements", 1, 1)
  : null;
const maxPlacements = args.has("max-placements")
  ? integerArg("max-placements", 1, 1)
  : null;
if (minPlacements !== null && maxPlacements !== null && minPlacements > maxPlacements) {
  throw new Error("--min-placements cannot exceed --max-placements");
}
const progressEvery = integerArg("progress-every", 1, 1);
const symmetryClauses = booleanArg("symmetry-clauses", true);
const continueOnZ3Unknown = booleanArg("continue-on-z3-unknown", true);
const requireNextLayerCoverability = booleanArg("require-next-layer-coverability", false);
const learnCellCoverability = booleanArg("learn-cell-coverability", false);
const learnPairCoverability = booleanArg("learn-pair-coverability", false);
const learnTripleCoverability = booleanArg("learn-triple-coverability", false);
const learnQuadrupleCoverability = booleanArg("learn-quadruple-coverability", false);
const cellOrbitLimit = integerArg("cell-orbit-limit", 0, 0);
const pairOrbitLimit = integerArg("pair-orbit-limit", 0, 0);
const tripleOrbitLimit = integerArg("triple-orbit-limit", 1, 0);
const tripleMaximumCellDistance = integerArg("triple-max-cell-distance", 3, 1);
const tripleAuditLimit = integerArg("triple-audit-limit", tripleOrbitLimit || 1, 1);
const quadrupleOrbitLimit = integerArg("quadruple-orbit-limit", 1, 0);
const quadrupleMaximumCellDistance = integerArg("quadruple-max-cell-distance", 6, 1);
const bootstrapPairDistance = integerArg("bootstrap-pair-distance", 0, 0);
const pairEncoding = args.get("pair-encoding") ?? "dnf";
if (!["dnf", "choice-cnf", "witness-cnf"].includes(pairEncoding)) {
  throw new Error("--pair-encoding must be dnf, choice-cnf, or witness-cnf");
}
const tripleEncoding = args.get("triple-encoding") ?? "choice-cnf";
if (!["dnf", "choice-cnf"].includes(tripleEncoding)) {
  throw new Error("--triple-encoding must be dnf or choice-cnf");
}
const tupleEnforcement = args.get("tuple-enforcement") ?? "encoded";
if (!["encoded", "lazy-higher", "lazy-all"].includes(tupleEnforcement)) {
  throw new Error("--tuple-enforcement must be encoded, lazy-higher, or lazy-all");
}
const pairSelection = args.get("pair-selection") ?? "lexicographic";
if (!["lexicographic", "max-blocked-combinations", "min-blocked-combinations"].includes(pairSelection)) {
  throw new Error("--pair-selection must be lexicographic, max-blocked-combinations, or min-blocked-combinations");
}
const lookaheadConflictEncoding = args.get("lookahead-conflict-encoding") ?? "edge-cnf";
if (!["edge-cnf", "grouped-pb"].includes(lookaheadConflictEncoding)) {
  throw new Error("--lookahead-conflict-encoding must be edge-cnf or grouped-pb");
}
const rootSymmetryBreaking = booleanArg("root-symmetry-breaking", false);
const python = args.get("python") ?? "python3";
const outputDirectory = resolve(args.get("output-dir") ?? `runs/${id}-radius${outerLayer}-to-${innerLayer}-z3-cegar`);
const reportOutput = resolve(args.get("report-output") ?? `${outputDirectory}/summary.json`);
const initialClauseReport = args.get("initial-clause-report")
  ? resolve(args.get("initial-clause-report"))
  : null;
const initialPairReport = args.get("initial-pair-report")
  ? resolve(args.get("initial-pair-report"))
  : null;
const initialCellReport = args.get("initial-cell-report")
  ? resolve(args.get("initial-cell-report"))
  : null;
const initialTripleReport = args.get("initial-triple-report")
  ? resolve(args.get("initial-triple-report"))
  : null;
const initialQuadrupleReport = args.get("initial-quadruple-report")
  ? resolve(args.get("initial-quadruple-report"))
  : null;
const pythonSolver = fileURLToPath(new URL("./solve_polycube_corona_z3.py", import.meta.url));
const clausePath = resolve(outputDirectory, "forbidden-clauses.json");
const cellPath = resolve(outputDirectory, "cell-coverability.json");
const pairPath = resolve(outputDirectory, "pair-coverability.json");
const triplePath = resolve(outputDirectory, "triple-coverability.json");
const quadruplePath = resolve(outputDirectory, "quadruple-coverability.json");
mkdirSync(outputDirectory, { recursive: true });

const clauses = [];
const clauseKeys = new Set();
const trials = [];
const pairConstraints = [];
const pairConstraintKeys = new Set();
const cellConstraints = [];
const cellConstraintKeys = new Set();
const tripleConstraints = [];
const tripleConstraintKeys = new Set();
const quadrupleConstraints = [];
const quadrupleConstraintKeys = new Set();
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
const addPair = rawPair => {
  const normalized = [...new Set(rawPair.map(String))].sort();
  if (normalized.length !== 2) throw new Error("A pair-coverability constraint must contain two distinct cells");
  const key = normalized.join(";");
  if (pairConstraintKeys.has(key)) return false;
  pairConstraintKeys.add(key);
  pairConstraints.push(normalized);
  return true;
};
const addPairOrbit = rawPair => {
  let added = 0;
  for (const pair of polycubeCellPairOrbitKeys(candidate.voxels, rawPair)) {
    added += Number(addPair(pair));
  }
  return added;
};
const addCell = rawCell => {
  const key = String(rawCell);
  if (cellConstraintKeys.has(key)) return false;
  cellConstraintKeys.add(key);
  cellConstraints.push(key);
  return true;
};
const addCellOrbit = rawCell => {
  let added = 0;
  for (const cell of polycubeCellOrbitKeys(candidate.voxels, rawCell)) {
    added += Number(addCell(cell));
  }
  return added;
};
const addTriple = rawTriple => {
  const normalized = [...new Set(rawTriple.map(String))].sort();
  if (normalized.length !== 3) throw new Error("A triple-coverability constraint must contain three distinct cells");
  const key = normalized.join(";");
  if (tripleConstraintKeys.has(key)) return false;
  tripleConstraintKeys.add(key);
  tripleConstraints.push(normalized);
  return true;
};
const addTripleOrbit = rawTriple => {
  let added = 0;
  for (const triple of polycubeCellTripleOrbitKeys(candidate.voxels, rawTriple)) {
    added += Number(addTriple(triple));
  }
  return added;
};
const addQuadruple = rawQuadruple => {
  const normalized = [...new Set(rawQuadruple.map(String))].sort();
  if (normalized.length !== 4) throw new Error("A quadruple-coverability constraint must contain four distinct cells");
  const key = normalized.join(";");
  if (quadrupleConstraintKeys.has(key)) return false;
  quadrupleConstraintKeys.add(key);
  quadrupleConstraints.push(normalized);
  return true;
};
const addQuadrupleOrbit = rawQuadruple => {
  let added = 0;
  for (const quadruple of polycubeCellQuadrupleOrbitKeys(candidate.voxels, rawQuadruple)) {
    added += Number(addQuadruple(quadruple));
  }
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
if (initialCellReport) {
  const initial = JSON.parse(readFileSync(initialCellReport, "utf8"));
  const initialCells = initial.cell_coverability_cells ?? initial.cells ?? initial;
  if (!Array.isArray(initialCells)) {
    throw new Error("--initial-cell-report must contain cell_coverability_cells or cells");
  }
  for (const cell of initialCells) addCellOrbit(cell);
}
const initialCellCount = cellConstraints.length;
if (initialPairReport) {
  const initial = JSON.parse(readFileSync(initialPairReport, "utf8"));
  const initialPairs = initial.pair_coverability_pairs ?? initial.pairs ?? initial;
  if (!Array.isArray(initialPairs)) {
    throw new Error("--initial-pair-report must contain pair_coverability_pairs or pairs");
  }
  for (const pair of initialPairs) addPairOrbit(pair);
}
const initialPairCount = pairConstraints.length;
const bootstrapPairStartCount = pairConstraints.length;
if (bootstrapPairDistance > 0) {
  const ringCells = polycubeCoronaRingCellKeys(candidate.voxels, innerLayer);
  for (let leftIndex = 0; leftIndex < ringCells.length; leftIndex += 1) {
    const left = ringCells[leftIndex].split(",").map(Number);
    for (let rightIndex = leftIndex + 1; rightIndex < ringCells.length; rightIndex += 1) {
      const right = ringCells[rightIndex].split(",").map(Number);
      const distance = left.reduce((sum, value, axis) => sum + Math.abs(value - right[axis]), 0);
      if (distance <= bootstrapPairDistance) addPairOrbit([ringCells[leftIndex], ringCells[rightIndex]]);
    }
  }
}
const bootstrapPairCount = pairConstraints.length - bootstrapPairStartCount;
if (initialTripleReport) {
  const initial = JSON.parse(readFileSync(initialTripleReport, "utf8"));
  const initialTriples = initial.triple_coverability_triples ?? initial.triples ?? initial;
  if (!Array.isArray(initialTriples)) {
    throw new Error("--initial-triple-report must contain triple_coverability_triples or triples");
  }
  for (const triple of initialTriples) addTripleOrbit(triple);
}
const initialTripleCount = tripleConstraints.length;
if (initialQuadrupleReport) {
  const initial = JSON.parse(readFileSync(initialQuadrupleReport, "utf8"));
  const initialQuadruples = initial.quadruple_coverability_quadruples ?? initial.quadruples ?? initial;
  if (!Array.isArray(initialQuadruples)) {
    throw new Error("--initial-quadruple-report must contain quadruple_coverability_quadruples or quadruples");
  }
  for (const quadruple of initialQuadruples) addQuadrupleOrbit(quadruple);
}
const initialQuadrupleCount = quadrupleConstraints.length;
const effectiveNextLayerCoverability = requireNextLayerCoverability
  || learnCellCoverability
  || cellConstraints.length > 0
  || learnPairCoverability
  || pairConstraints.length > 0
  || learnTripleCoverability
  || tripleConstraints.length > 0
  || learnQuadrupleCoverability
  || quadrupleConstraints.length > 0;
const encodePairCoverability = tupleEnforcement !== "lazy-all";
const encodeHigherCoverability = tupleEnforcement === "encoded";

const learnTupleObstructions = proposal => {
  const incompatiblePairDetails = learnPairCoverability || learnTripleCoverability || learnQuadrupleCoverability
    ? polycubeCoronaIncompatibleTargetPairDetails(candidate.voxels, proposal.corona, outerLayer)
    : [];
  const pairKey = detail => detail.target_cells.join(";");
  incompatiblePairDetails.sort((left, right) => {
    const blockedDifference = pairSelection === "max-blocked-combinations"
      ? right.candidate_pairs_blocked - left.candidate_pairs_blocked
      : pairSelection === "min-blocked-combinations"
        ? left.candidate_pairs_blocked - right.candidate_pairs_blocked
        : 0;
    return blockedDifference || pairKey(left).localeCompare(pairKey(right));
  });
  const incompatiblePairs = incompatiblePairDetails.map(detail => detail.target_cells);
  let pairsAdded = 0;
  let pairOrbitsAdded = 0;
  let selectedPairCandidateCombinationsBlocked = null;
  for (const detail of incompatiblePairDetails) {
    if (pairOrbitLimit && pairOrbitsAdded >= pairOrbitLimit) break;
    const added = addPairOrbit(detail.target_cells);
    if (added) {
      pairOrbitsAdded += 1;
      selectedPairCandidateCombinationsBlocked ??= detail.candidate_pairs_blocked;
    }
    pairsAdded += added;
  }
  const incompatibleTripleAudit = (learnTripleCoverability || learnQuadrupleCoverability) && incompatiblePairs.length === 0
    ? polycubeCoronaIncompatibleTargetTripleDetails(candidate.voxels, proposal.corona, outerLayer, {
        maximumCellDistance: tripleMaximumCellDistance,
        limit: tripleAuditLimit + 1
      })
    : [];
  const tripleAuditTruncated = incompatibleTripleAudit.length > tripleAuditLimit;
  const incompatibleTripleDetails = incompatibleTripleAudit.slice(0, tripleAuditLimit);
  let triplesAdded = 0;
  let tripleOrbitsAdded = 0;
  for (const detail of incompatibleTripleDetails) {
    if (tripleOrbitLimit && tripleOrbitsAdded >= tripleOrbitLimit) break;
    const added = addTripleOrbit(detail.target_cells);
    if (added) tripleOrbitsAdded += 1;
    triplesAdded += added;
  }
  const incompatibleQuadrupleDetails = learnQuadrupleCoverability
    && incompatiblePairs.length === 0
    && incompatibleTripleDetails.length === 0
    ? polycubeCoronaIncompatibleTargetQuadrupleDetails(candidate.voxels, proposal.corona, outerLayer, {
        maximumCellDistance: quadrupleMaximumCellDistance,
        limit: quadrupleOrbitLimit || 1
      })
    : [];
  let quadruplesAdded = 0;
  let quadrupleOrbitsAdded = 0;
  for (const detail of incompatibleQuadrupleDetails) {
    if (quadrupleOrbitLimit && quadrupleOrbitsAdded >= quadrupleOrbitLimit) break;
    const added = addQuadrupleOrbit(detail.target_cells);
    if (added) quadrupleOrbitsAdded += 1;
    quadruplesAdded += added;
  }
  return {
    incompatiblePairDetails,
    incompatiblePairs,
    pairsAdded,
    pairOrbitsAdded,
    selectedPairCandidateCombinationsBlocked,
    incompatibleTripleDetails,
    tripleAuditTruncated,
    triplesAdded,
    tripleOrbitsAdded,
    incompatibleQuadrupleDetails,
    quadruplesAdded,
    quadrupleOrbitsAdded,
    rejected: incompatiblePairs.length > 0
      || incompatibleTripleDetails.length > 0
      || incompatibleQuadrupleDetails.length > 0
  };
};

process.stdout.write(`${JSON.stringify({
  type: "z3_cegar_start",
  id,
  outer_layer: outerLayer,
  inner_layer: innerLayer,
  iterations,
  z3_timeout_ms: z3TimeoutMs,
  z3_process_grace_ms: z3ProcessGraceMs,
  continuation_time_ms: continuationTimeMs,
  continuation_nodes: continuationNodes,
  backend,
  random_seed: randomSeed,
  seed_stride: seedStride,
  min_placements: minPlacements,
  max_placements: maxPlacements,
  symmetry_clauses: symmetryClauses,
  continue_on_z3_unknown: continueOnZ3Unknown,
  require_next_layer_coverability: requireNextLayerCoverability,
  effective_next_layer_coverability: effectiveNextLayerCoverability,
  learn_cell_coverability: learnCellCoverability,
  cell_orbit_limit: cellOrbitLimit,
  learn_pair_coverability: learnPairCoverability,
  pair_orbit_limit: pairOrbitLimit,
  bootstrap_pair_distance: bootstrapPairDistance,
  pair_encoding: pairEncoding,
  pair_selection: pairSelection,
  lookahead_conflict_encoding: lookaheadConflictEncoding,
  root_symmetry_breaking: rootSymmetryBreaking,
  initial_clause_count: initialClauseCount,
  initial_cell_coverability_constraints: initialCellCount,
  initial_pair_coverability_constraints: initialPairCount,
  bootstrap_pair_coverability_constraints: bootstrapPairCount,
  learn_triple_coverability: learnTripleCoverability,
  triple_orbit_limit: tripleOrbitLimit,
  triple_audit_limit: tripleAuditLimit,
  triple_max_cell_distance: tripleMaximumCellDistance,
  triple_encoding: tripleEncoding,
  tuple_enforcement: tupleEnforcement,
  initial_triple_coverability_constraints: initialTripleCount,
  learn_quadruple_coverability: learnQuadrupleCoverability,
  quadruple_orbit_limit: quadrupleOrbitLimit,
  quadruple_max_cell_distance: quadrupleMaximumCellDistance,
  quadruple_encoding: "choice-cnf",
  initial_quadruple_coverability_constraints: initialQuadrupleCount,
  output_directory: outputDirectory
})}\n`);

for (let iteration = 0; iteration < iterations; iteration += 1) {
  writeFileSync(clausePath, `${JSON.stringify({ clauses }, null, 2)}\n`);
  writeFileSync(cellPath, `${JSON.stringify({ cells: cellConstraints }, null, 2)}\n`);
  writeFileSync(pairPath, `${JSON.stringify({ pairs: pairConstraints }, null, 2)}\n`);
  writeFileSync(triplePath, `${JSON.stringify({ triples: tripleConstraints }, null, 2)}\n`);
  writeFileSync(quadruplePath, `${JSON.stringify({ quadruples: quadrupleConstraints }, null, 2)}\n`);
  const witnessPath = resolve(outputDirectory, `outer-witness-${String(iteration).padStart(4, "0")}.json`);
  const iterationSeed = randomSeed + iteration * seedStride;
  const solverArguments = [
    pythonSolver,
    `--key=${polycubeKey(candidate.voxels)}`,
    `--layer=${outerLayer}`,
    `--timeout-ms=${z3TimeoutMs}`,
    `--backend=${backend}`,
    `--random-seed=${iterationSeed}`,
    `--lookahead-conflict-encoding=${lookaheadConflictEncoding}`,
    `--forbidden-clause-report=${clausePath}`,
    `--output=${witnessPath}`
  ];
  if (minPlacements !== null) solverArguments.push(`--min-placements=${minPlacements}`);
  if (maxPlacements !== null) solverArguments.push(`--max-placements=${maxPlacements}`);
  if (requireNextLayerCoverability) solverArguments.push("--require-next-layer-coverability");
  if (cellConstraints.length) solverArguments.push(`--cell-coverability-report=${cellPath}`);
  if (rootSymmetryBreaking) solverArguments.push("--root-symmetry-breaking");
  if (pairConstraints.length && encodePairCoverability) {
    solverArguments.push(`--pair-coverability-report=${pairPath}`);
    solverArguments.push(`--pair-encoding=${pairEncoding}`);
  }
  if (tripleConstraints.length && encodeHigherCoverability) {
    solverArguments.push(`--triple-coverability-report=${triplePath}`);
    solverArguments.push(`--triple-encoding=${tripleEncoding}`);
  }
  if (quadrupleConstraints.length && encodeHigherCoverability) {
    solverArguments.push(`--quadruple-coverability-report=${quadruplePath}`);
  }
  const solved = spawnSync(python, solverArguments, {
    encoding: "utf8",
    timeout: z3TimeoutMs + z3ProcessGraceMs,
    maxBuffer: 16 * 1024 * 1024
  });
  if (solved.status !== 0) {
    if (solved.error?.code === "ETIMEDOUT" || solved.signal) {
      z3UnknownTrials += 1;
      const trial = {
        iteration,
        random_seed: iterationSeed,
        z3_status: "process_timeout",
        z3_milliseconds: z3TimeoutMs + z3ProcessGraceMs,
        reason_unknown: solved.error?.code ?? solved.signal ?? "process_timeout",
        clauses: clauses.length,
        cell_coverability_constraints: cellConstraints.length,
        pair_coverability_constraints: pairConstraints.length,
        triple_coverability_constraints: tripleConstraints.length,
        quadruple_coverability_constraints: quadrupleConstraints.length
      };
      trials.push(trial);
      if (iteration % progressEvery === 0 || iteration + 1 === iterations) {
        process.stdout.write(`${JSON.stringify({ type: "z3_cegar_trial", ...trial })}\n`);
      }
      if (continueOnZ3Unknown) continue;
      classification = "z3_incomplete";
      break;
    }
    throw new Error(solved.stderr.trim() || `Z3 proposal process exited ${solved.status}`);
  }
  const proposal = JSON.parse(readFileSync(witnessPath, "utf8"));
  if (proposal.z3_status === "unsat") {
    classification = minPlacements !== null || maxPlacements !== null
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
  let tupleResult = null;
  if (tupleEnforcement !== "encoded") {
    tupleResult = learnTupleObstructions(proposal);
    if (tupleResult.rejected) {
      const learnedClause = proposal.corona.map(placementKey);
      const clausesAdded = addClauseOrbit(learnedClause);
      const tupleKind = tupleResult.incompatiblePairs.length
        ? "pair"
        : tupleResult.incompatibleTripleDetails.length
          ? "triple"
          : "quadruple";
      const trial = {
        iteration,
        random_seed: iterationSeed,
        z3_status: "sat",
        z3_milliseconds: proposal.milliseconds,
        outer_placements: proposal.corona.length,
        continuation_skipped: true,
        continuation_success: false,
        continuation_exhausted: null,
        continuation_nodes: 0,
        continuation_milliseconds: 0,
        obstruction_kind: `lazy_${tupleKind}_coverability`,
        learned_clause_size: learnedClause.length,
        clauses_added: clausesAdded,
        clauses: clauses.length,
        cell_constraints_added: 0,
        cell_orbits_added: 0,
        cell_coverability_constraints: cellConstraints.length,
        incompatible_target_pairs: tupleResult.incompatiblePairs.length,
        selected_pair_candidate_combinations_blocked: tupleResult.selectedPairCandidateCombinationsBlocked,
        pair_constraints_added: tupleResult.pairsAdded,
        pair_orbits_added: tupleResult.pairOrbitsAdded,
        pair_coverability_constraints: pairConstraints.length,
        incompatible_target_triples: tupleResult.incompatibleTripleDetails.length,
        triple_audit_truncated: tupleResult.tripleAuditTruncated,
        selected_triple_candidate_combinations_blocked: tupleResult.incompatibleTripleDetails[0]?.candidate_triples_blocked ?? null,
        triple_constraints_added: tupleResult.triplesAdded,
        triple_orbits_added: tupleResult.tripleOrbitsAdded,
        triple_coverability_constraints: tripleConstraints.length,
        incompatible_target_quadruples: tupleResult.incompatibleQuadrupleDetails.length,
        selected_quadruple_candidate_combinations_blocked: tupleResult.incompatibleQuadrupleDetails[0]?.candidate_quadruples_blocked ?? null,
        quadruple_constraints_added: tupleResult.quadruplesAdded,
        quadruple_orbits_added: tupleResult.quadrupleOrbitsAdded,
        quadruple_coverability_constraints: quadrupleConstraints.length
      };
      trials.push(trial);
      if (iteration % progressEvery === 0 || iteration + 1 === iterations) {
        process.stdout.write(`${JSON.stringify({ type: "z3_cegar_trial", ...trial })}\n`);
      }
      if (!clausesAdded && !tupleResult.pairsAdded && !tupleResult.triplesAdded && !tupleResult.quadruplesAdded) {
        classification = "duplicate_obstruction";
        break;
      }
      continue;
    }
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
  let cellOrbitsAdded = 0;
  let cellsAdded = 0;
  if (learnCellCoverability && obstruction?.target_cell) {
    if (!cellOrbitLimit || cellOrbitsAdded < cellOrbitLimit) {
      cellsAdded = addCellOrbit(obstruction.target_cell.join(","));
      if (cellsAdded) cellOrbitsAdded += 1;
    }
  }
  const {
    incompatiblePairs,
    pairsAdded,
    pairOrbitsAdded,
    selectedPairCandidateCombinationsBlocked,
    incompatibleTripleDetails,
    tripleAuditTruncated,
    triplesAdded,
    tripleOrbitsAdded,
    incompatibleQuadrupleDetails,
    quadruplesAdded,
    quadrupleOrbitsAdded
  } = tupleResult ?? learnTupleObstructions(proposal);
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
    clauses: clauses.length,
    dead_target_cell: obstruction?.target_cell?.join(",") ?? null,
    cell_constraints_added: cellsAdded,
    cell_orbits_added: cellOrbitsAdded,
    cell_coverability_constraints: cellConstraints.length,
    incompatible_target_pairs: incompatiblePairs.length,
    selected_pair_candidate_combinations_blocked: selectedPairCandidateCombinationsBlocked,
    pair_constraints_added: pairsAdded,
    pair_orbits_added: pairOrbitsAdded,
    pair_coverability_constraints: pairConstraints.length,
    incompatible_target_triples: incompatibleTripleDetails.length,
    triple_audit_truncated: tripleAuditTruncated,
    selected_triple_candidate_combinations_blocked: incompatibleTripleDetails[0]?.candidate_triples_blocked ?? null,
    triple_constraints_added: triplesAdded,
    triple_orbits_added: tripleOrbitsAdded,
    triple_coverability_constraints: tripleConstraints.length,
    incompatible_target_quadruples: incompatibleQuadrupleDetails.length,
    selected_quadruple_candidate_combinations_blocked: incompatibleQuadrupleDetails[0]?.candidate_quadruples_blocked ?? null,
    quadruple_constraints_added: quadruplesAdded,
    quadruple_orbits_added: quadrupleOrbitsAdded,
    quadruple_coverability_constraints: quadrupleConstraints.length
  };
  trials.push(trial);
  if (iteration % progressEvery === 0 || iteration + 1 === iterations) {
    process.stdout.write(`${JSON.stringify({ type: "z3_cegar_trial", ...trial })}\n`);
  }
  if (!clausesAdded && !cellsAdded && !pairsAdded && !triplesAdded && !quadruplesAdded) {
    classification = "duplicate_obstruction";
    break;
  }
}

// Keep resumable artifacts synchronized even when the final iteration learns
// new obligations and exits before the next proposal write.
writeFileSync(clausePath, `${JSON.stringify({ clauses }, null, 2)}\n`);
writeFileSync(cellPath, `${JSON.stringify({ cells: cellConstraints }, null, 2)}\n`);
writeFileSync(pairPath, `${JSON.stringify({ pairs: pairConstraints }, null, 2)}\n`);
writeFileSync(triplePath, `${JSON.stringify({ triples: tripleConstraints }, null, 2)}\n`);
writeFileSync(quadruplePath, `${JSON.stringify({ quadruples: quadrupleConstraints }, null, 2)}\n`);

const summary = {
  kind: "polycube_corona_z3_cegar",
  candidate: id,
  outer_layer: outerLayer,
  inner_layer: innerLayer,
  classification,
  backend,
  random_seed: randomSeed,
  seed_stride: seedStride,
  min_placements: minPlacements,
  max_placements: maxPlacements,
  symmetry_clauses: symmetryClauses,
  continue_on_z3_unknown: continueOnZ3Unknown,
  require_next_layer_coverability: requireNextLayerCoverability,
  effective_next_layer_coverability: effectiveNextLayerCoverability,
  learn_cell_coverability: learnCellCoverability,
  cell_orbit_limit: cellOrbitLimit,
  learn_pair_coverability: learnPairCoverability,
  pair_orbit_limit: pairOrbitLimit,
  bootstrap_pair_distance: bootstrapPairDistance,
  pair_encoding: pairEncoding,
  pair_selection: pairSelection,
  lookahead_conflict_encoding: lookaheadConflictEncoding,
  root_symmetry_breaking: rootSymmetryBreaking,
  z3_unknown_trials: z3UnknownTrials,
  z3_timeout_ms: z3TimeoutMs,
  z3_process_grace_ms: z3ProcessGraceMs,
  continuation_time_ms: continuationTimeMs,
  continuation_nodes: continuationNodes,
  trials,
  learned_clauses: clauses,
  learned_clause_count: clauses.length,
  initial_clause_count: initialClauseCount,
  cell_coverability_cells: cellConstraints,
  cell_coverability_constraint_count: cellConstraints.length,
  initial_cell_coverability_constraints: initialCellCount,
  pair_coverability_pairs: pairConstraints,
  pair_coverability_constraint_count: pairConstraints.length,
  initial_pair_coverability_constraints: initialPairCount,
  bootstrap_pair_coverability_constraints: bootstrapPairCount,
  learn_triple_coverability: learnTripleCoverability,
  triple_orbit_limit: tripleOrbitLimit,
  triple_audit_limit: tripleAuditLimit,
  triple_max_cell_distance: tripleMaximumCellDistance,
  triple_encoding: tripleEncoding,
  tuple_enforcement: tupleEnforcement,
  triple_coverability_triples: tripleConstraints,
  triple_coverability_constraint_count: tripleConstraints.length,
  initial_triple_coverability_constraints: initialTripleCount,
  learn_quadruple_coverability: learnQuadrupleCoverability,
  quadruple_orbit_limit: quadrupleOrbitLimit,
  quadruple_max_cell_distance: quadrupleMaximumCellDistance,
  quadruple_encoding: "choice-cnf",
  quadruple_coverability_quadruples: quadrupleConstraints,
  quadruple_coverability_constraint_count: quadrupleConstraints.length,
  initial_quadruple_coverability_constraints: initialQuadrupleCount,
  radius_witness: radiusWitness ? {
    placements: radiusWitness.corona.length,
    corona: radiusWitness.corona
  } : null,
  warning: ["certified_non_tiler", "verified_inner_radius_witness"].includes(classification)
    ? null
    : classification === "placement_bound_exhausted"
      ? `The exact CEGAR loop exhausted only outer patches in the configured placement-count range [${minPlacements ?? 0}, ${maxPlacements ?? "unbounded"}]; this is not a non-tiling or aperiodicity certificate.`
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
