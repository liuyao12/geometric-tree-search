#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { createInterface } from "node:readline";
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
const z3FormulaCache = booleanArg("z3-formula-cache", false);
const z3WitnessBatchSize = integerArg("z3-witness-batch-size", 1, 1);
const z3Interactive = booleanArg("z3-interactive", false);
const z3InteractiveReplacePairs = booleanArg("z3-interactive-replace-pairs", z3Interactive);
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
if (!["encoded", "hybrid-higher", "hybrid-all", "lazy-higher", "lazy-all"].includes(tupleEnforcement)) {
  throw new Error("--tuple-enforcement must be encoded, hybrid-higher, hybrid-all, lazy-higher, or lazy-all");
}
const pairSoftMinimum = args.has("pair-soft-minimum")
  ? integerArg("pair-soft-minimum", 1, 1)
  : null;
if (pairSoftMinimum !== null && z3Interactive) {
  throw new Error("--pair-soft-minimum is not yet supported with --z3-interactive=true");
}
if (pairSoftMinimum !== null && !["hybrid-all", "hybrid-higher"].includes(tupleEnforcement)) {
  throw new Error("--pair-soft-minimum requires a hybrid tuple-enforcement mode");
}
const encodedPairOrbitLimit = integerArg("encoded-pair-orbit-limit", 0, 0);
const encodedPairSelectionPolicy = args.get("encoded-pair-selection") ?? "first";
if (!["first", "recent", "max-blocked-combinations", "frequency-impact", "frequency-weighted-impact", "historical-cover", "historical-core", "recent-defect-cover"].includes(encodedPairSelectionPolicy)) {
  throw new Error("--encoded-pair-selection must be first, recent, max-blocked-combinations, frequency-impact, frequency-weighted-impact, historical-cover, historical-core, or recent-defect-cover");
}
const recentDefectOrbitLimit = integerArg(
  "recent-defect-orbit-limit",
  encodedPairOrbitLimit || 1,
  1
);
if (args.has("recent-defect-orbit-limit") && encodedPairSelectionPolicy !== "recent-defect-cover") {
  throw new Error("--recent-defect-orbit-limit is only valid with --encoded-pair-selection=recent-defect-cover");
}
if (tupleEnforcement === "hybrid-all" && encodedPairOrbitLimit === 0) {
  throw new Error("--tuple-enforcement=hybrid-all requires --encoded-pair-orbit-limit greater than zero");
}
if (!["hybrid-all", "hybrid-higher"].includes(tupleEnforcement) && encodedPairOrbitLimit > 0) {
  throw new Error("--encoded-pair-orbit-limit is only valid with a hybrid tuple-enforcement mode");
}
if (!["hybrid-all", "hybrid-higher"].includes(tupleEnforcement) && encodedPairSelectionPolicy !== "first") {
  throw new Error("--encoded-pair-selection is only valid with a hybrid tuple-enforcement mode");
}
const encodedTripleOrbitLimit = integerArg("encoded-triple-orbit-limit", 0, 0);
const encodedTripleSelectionPolicy = args.get("encoded-triple-selection") ?? "first";
if (!["first", "recent", "max-blocked-combinations"].includes(encodedTripleSelectionPolicy)) {
  throw new Error("--encoded-triple-selection must be first, recent, or max-blocked-combinations");
}
if (tupleEnforcement === "hybrid-higher" && encodedTripleOrbitLimit === 0) {
  throw new Error("--tuple-enforcement=hybrid-higher requires --encoded-triple-orbit-limit greater than zero");
}
if (tupleEnforcement !== "hybrid-higher" && encodedTripleOrbitLimit > 0) {
  throw new Error("--encoded-triple-orbit-limit is only valid with --tuple-enforcement=hybrid-higher");
}
if (tupleEnforcement !== "hybrid-higher" && encodedTripleSelectionPolicy !== "first") {
  throw new Error("--encoded-triple-selection is only valid with --tuple-enforcement=hybrid-higher");
}
if (z3Interactive && z3WitnessBatchSize !== 1) {
  throw new Error("--z3-interactive requires --z3-witness-batch-size=1");
}
if (z3Interactive && learnCellCoverability) {
  throw new Error("--z3-interactive does not yet support dynamic cell-coverability learning");
}
if (z3Interactive && tupleEnforcement === "encoded") {
  throw new Error("--z3-interactive requires a lazy or hybrid tuple-enforcement mode");
}
if (z3InteractiveReplacePairs && !z3Interactive) {
  throw new Error("--z3-interactive-replace-pairs requires --z3-interactive");
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
const encodedPairPath = resolve(outputDirectory, "encoded-pair-coverability.json");
const triplePath = resolve(outputDirectory, "triple-coverability.json");
const encodedTriplePath = resolve(outputDirectory, "encoded-triple-coverability.json");
const quadruplePath = resolve(outputDirectory, "quadruple-coverability.json");
const formulaCachePath = resolve(outputDirectory, "outer-formula-cache.smt2");
mkdirSync(outputDirectory, { recursive: true });

const clauses = [];
const clauseKeys = new Set();
const trials = [];
const pairConstraints = [];
const pairConstraintKeys = new Set();
const pairOrbitScores = new Map();
const pairOrbitHits = new Map();
const pairDefectOrbitSets = [];
const cellConstraints = [];
const cellConstraintKeys = new Set();
const tripleConstraints = [];
const tripleConstraintKeys = new Set();
const tripleOrbitScores = new Map();
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
const pairOrbitRepresentativeKey = rawPair => polycubeCellPairOrbitKeys(candidate.voxels, rawPair)
  .map(pair => [...pair].sort().join(";"))
  .sort()[0];
const updatePairOrbitScore = (orbitKey, blockedCombinations = 0) => {
  const score = Number(blockedCombinations);
  if (Number.isFinite(score) && score > (pairOrbitScores.get(orbitKey) ?? 0)) {
    pairOrbitScores.set(orbitKey, score);
  }
};
const addPairOrbit = (rawPair, blockedCombinations = 0) => {
  const orbitKey = pairOrbitRepresentativeKey(rawPair);
  updatePairOrbitScore(orbitKey, blockedCombinations);
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
const tripleOrbitRepresentativeKey = rawTriple => polycubeCellTripleOrbitKeys(candidate.voxels, rawTriple)
  .map(triple => [...triple].sort().join(";"))
  .sort()[0];
const addTripleOrbit = (rawTriple, blockedCombinations = 0) => {
  const orbitKey = tripleOrbitRepresentativeKey(rawTriple);
  const score = Number(blockedCombinations);
  if (Number.isFinite(score) && score > (tripleOrbitScores.get(orbitKey) ?? 0)) {
    tripleOrbitScores.set(orbitKey, score);
  }
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
  const initialPairOrbitScores = initial.pair_orbit_scores ?? {};
  if (!initialPairOrbitScores || Array.isArray(initialPairOrbitScores) || typeof initialPairOrbitScores !== "object") {
    throw new Error("pair_orbit_scores must be an object keyed by canonical orbit representative");
  }
  const initialPairOrbitHits = initial.pair_orbit_hits ?? {};
  if (!initialPairOrbitHits || Array.isArray(initialPairOrbitHits) || typeof initialPairOrbitHits !== "object") {
    throw new Error("pair_orbit_hits must be an object keyed by canonical orbit representative");
  }
  for (const [orbitKey, rawHits] of Object.entries(initialPairOrbitHits)) {
    const hits = Number(rawHits);
    if (!Number.isInteger(hits) || hits < 0) {
      throw new Error(`pair_orbit_hits[${orbitKey}] must be a nonnegative integer`);
    }
    if (hits > 0) pairOrbitHits.set(orbitKey, hits);
  }
  const initialPairDefectOrbitSets = initial.pair_defect_orbit_sets ?? [];
  if (!Array.isArray(initialPairDefectOrbitSets)) {
    throw new Error("pair_defect_orbit_sets must be an array of orbit-key arrays");
  }
  for (const [setIndex, rawOrbitKeys] of initialPairDefectOrbitSets.entries()) {
    if (!Array.isArray(rawOrbitKeys) || rawOrbitKeys.some(key => typeof key !== "string")) {
      throw new Error(`pair_defect_orbit_sets[${setIndex}] must contain orbit-key strings`);
    }
    const normalized = [...new Set(rawOrbitKeys)].sort();
    if (normalized.length) pairDefectOrbitSets.push(normalized);
  }
  for (const pair of initialPairs) {
    addPairOrbit(pair, initialPairOrbitScores[pairOrbitRepresentativeKey(pair)] ?? 0);
  }
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
  const initialTripleOrbitScores = initial.triple_orbit_scores ?? {};
  if (!initialTripleOrbitScores || Array.isArray(initialTripleOrbitScores) || typeof initialTripleOrbitScores !== "object") {
    throw new Error("triple_orbit_scores must be an object keyed by canonical orbit representative");
  }
  for (const triple of initialTriples) {
    addTripleOrbit(triple, initialTripleOrbitScores[tripleOrbitRepresentativeKey(triple)] ?? 0);
  }
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
const serializedTripleOrbitScores = () => Object.fromEntries(
  [...tripleOrbitScores.entries()]
    .filter(([, score]) => score > 0)
    .sort(([left], [right]) => left.localeCompare(right))
);
const serializedPairOrbitScores = () => Object.fromEntries(
  [...pairOrbitScores.entries()]
    .filter(([, score]) => score > 0)
    .sort(([left], [right]) => left.localeCompare(right))
);
const serializedPairOrbitHits = () => Object.fromEntries(
  [...pairOrbitHits.entries()]
    .filter(([, hits]) => hits > 0)
    .sort(([left], [right]) => left.localeCompare(right))
);
const coveredPairDefectSets = orbitKeys => {
  const selected = new Set(orbitKeys);
  return pairDefectOrbitSets.reduce((covered, orbitSet) =>
    covered + Number(orbitSet.some(key => selected.has(key))), 0
  );
};
const describeEncodedPairs = constraints => {
  const orbitKeys = [];
  const seenOrbitKeys = new Set();
  for (const pair of constraints) {
    const orbitKey = pairOrbitRepresentativeKey(pair);
    if (seenOrbitKeys.has(orbitKey)) continue;
    seenOrbitKeys.add(orbitKey);
    orbitKeys.push(orbitKey);
  }
  const selectedOrbitKeys = new Set(orbitKeys);
  const recentDefectOrbitKeys = pairDefectOrbitSets.at(-1) ?? [];
  const recentDefectOrbitsSelected = recentDefectOrbitKeys.reduce(
    (count, key) => count + Number(selectedOrbitKeys.has(key)),
    0
  );
  return {
    constraints,
    orbitCount: orbitKeys.length,
    orbitKeys,
    orbitScores: orbitKeys.map(key => pairOrbitScores.get(key) ?? 0),
    orbitHits: orbitKeys.map(key => pairOrbitHits.get(key) ?? 0),
    historicalSetsCovered: coveredPairDefectSets(orbitKeys),
    recentDefectSize: recentDefectOrbitKeys.length,
    recentDefectOrbitsSelected,
    recentDefectComplete: recentDefectOrbitKeys.length > 0
      && recentDefectOrbitsSelected === recentDefectOrbitKeys.length
  };
};
const selectEncodedPairs = () => {
  if (["encoded", "lazy-higher"].includes(tupleEnforcement)
    || (tupleEnforcement === "hybrid-higher" && encodedPairOrbitLimit === 0)) {
    return { ...describeEncodedPairs(pairConstraints), orbitCount: null };
  }
  if (tupleEnforcement === "lazy-all") {
    return {
      constraints: [], orbitCount: 0, orbitKeys: [], orbitScores: [], orbitHits: [], historicalSetsCovered: 0
    };
  }
  const orderedOrbitKeys = [];
  const seenOrbitKeys = new Set();
  for (const pair of pairConstraints) {
    const orbitKey = pairOrbitRepresentativeKey(pair);
    if (seenOrbitKeys.has(orbitKey)) continue;
    seenOrbitKeys.add(orbitKey);
    orderedOrbitKeys.push(orbitKey);
  }
  const orbitOrderIndex = new Map(orderedOrbitKeys.map((key, index) => [key, index]));
  let historicalCoverKeys = null;
  if (["historical-cover", "historical-core", "recent-defect-cover"].includes(encodedPairSelectionPolicy)) {
    const available = new Set(orderedOrbitKeys);
    let uncovered = pairDefectOrbitSets
      .map(orbitSet => orbitSet.filter(key => available.has(key)))
      .filter(orbitSet => orbitSet.length);
    historicalCoverKeys = [];
    if (encodedPairSelectionPolicy === "recent-defect-cover") {
      const latestDefectKeys = [...new Set(pairDefectOrbitSets.at(-1) ?? [])]
        .filter(key => available.has(key))
        .sort((left, right) =>
          (pairOrbitScores.get(right) ?? 0) - (pairOrbitScores.get(left) ?? 0)
          || (pairOrbitHits.get(right) ?? 0) - (pairOrbitHits.get(left) ?? 0)
          || (orbitOrderIndex.get(right) ?? 0) - (orbitOrderIndex.get(left) ?? 0)
        );
      historicalCoverKeys.push(...latestDefectKeys.slice(
        0,
        Math.min(encodedPairOrbitLimit, recentDefectOrbitLimit)
      ));
      const protectedKeys = new Set(historicalCoverKeys);
      uncovered = uncovered.filter(orbitSet => !orbitSet.some(key => protectedKeys.has(key)));
    }
    if (encodedPairSelectionPolicy === "historical-core") {
      const singletonCounts = new Map();
      for (const orbitSet of uncovered) {
        if (orbitSet.length !== 1) continue;
        singletonCounts.set(orbitSet[0], (singletonCounts.get(orbitSet[0]) ?? 0) + 1);
      }
      historicalCoverKeys.push(...[...singletonCounts.keys()].sort((left, right) =>
        (singletonCounts.get(right) ?? 0) - (singletonCounts.get(left) ?? 0)
        || (pairOrbitScores.get(right) ?? 0) - (pairOrbitScores.get(left) ?? 0)
        || (pairOrbitHits.get(right) ?? 0) - (pairOrbitHits.get(left) ?? 0)
        || (orbitOrderIndex.get(right) ?? 0) - (orbitOrderIndex.get(left) ?? 0)
      ).slice(0, encodedPairOrbitLimit));
      const protectedKeys = new Set(historicalCoverKeys);
      uncovered = uncovered.filter(orbitSet => !orbitSet.some(key => protectedKeys.has(key)));
    }
    while (uncovered.length && historicalCoverKeys.length < encodedPairOrbitLimit) {
      const coverage = new Map();
      for (const orbitSet of uncovered) for (const key of orbitSet) {
        coverage.set(key, (coverage.get(key) ?? 0) + 1);
      }
      const best = [...coverage.keys()].sort((left, right) =>
        (coverage.get(right) ?? 0) - (coverage.get(left) ?? 0)
        || (pairOrbitScores.get(right) ?? 0) - (pairOrbitScores.get(left) ?? 0)
        || (pairOrbitHits.get(right) ?? 0) - (pairOrbitHits.get(left) ?? 0)
        || (orbitOrderIndex.get(right) ?? 0) - (orbitOrderIndex.get(left) ?? 0)
      )[0];
      if (!best) break;
      historicalCoverKeys.push(best);
      uncovered = uncovered.filter(orbitSet => !orbitSet.includes(best));
    }
    const alreadyRanked = new Set(historicalCoverKeys);
    historicalCoverKeys.push(...orderedOrbitKeys
      .filter(key => !alreadyRanked.has(key))
      .sort((left, right) =>
        (pairOrbitScores.get(right) ?? 0) - (pairOrbitScores.get(left) ?? 0)
        || (pairOrbitHits.get(right) ?? 0) - (pairOrbitHits.get(left) ?? 0)
      ));
  }
  const rankedOrbitKeys = historicalCoverKeys
    ?? (encodedPairSelectionPolicy === "frequency-weighted-impact"
    ? orderedOrbitKeys.map((key, index) => ({
        key,
        index,
        hits: pairOrbitHits.get(key) ?? 0,
        score: pairOrbitScores.get(key) ?? 0
      }))
        .sort((left, right) =>
          right.hits * right.score - left.hits * left.score
          || right.hits - left.hits
          || right.score - left.score
          || right.index - left.index
        )
        .map(entry => entry.key)
    : encodedPairSelectionPolicy === "frequency-impact"
    ? orderedOrbitKeys.map((key, index) => ({
        key,
        index,
        hits: pairOrbitHits.get(key) ?? 0,
        score: pairOrbitScores.get(key) ?? 0
      }))
        .sort((left, right) => right.hits - left.hits || right.score - left.score || right.index - left.index)
        .map(entry => entry.key)
    : encodedPairSelectionPolicy === "max-blocked-combinations"
    ? orderedOrbitKeys.map((key, index) => ({ key, index, score: pairOrbitScores.get(key) ?? 0 }))
        .sort((left, right) => right.score - left.score || right.index - left.index)
        .map(entry => entry.key)
    : encodedPairSelectionPolicy === "recent"
      ? orderedOrbitKeys.slice().reverse()
      : orderedOrbitKeys);
  const selectedOrbitKeys = new Set(rankedOrbitKeys.slice(0, encodedPairOrbitLimit));
  const constraints = pairConstraints.filter(pair =>
    selectedOrbitKeys.has(pairOrbitRepresentativeKey(pair))
  );
  return describeEncodedPairs(constraints);
};
const selectEncodedTriples = () => {
  if (tupleEnforcement === "encoded") {
    return { constraints: tripleConstraints, orbitCount: null, orbitKeys: [], orbitScores: [] };
  }
  if (tupleEnforcement !== "hybrid-higher") {
    return { constraints: [], orbitCount: 0, orbitKeys: [], orbitScores: [] };
  }
  const orderedOrbitKeys = [];
  const seenOrbitKeys = new Set();
  for (const triple of tripleConstraints) {
    const orbitKey = tripleOrbitRepresentativeKey(triple);
    if (seenOrbitKeys.has(orbitKey)) continue;
    seenOrbitKeys.add(orbitKey);
    orderedOrbitKeys.push(orbitKey);
  }
  const rankedOrbitKeys = encodedTripleSelectionPolicy === "max-blocked-combinations"
    ? orderedOrbitKeys.map((key, index) => ({ key, index, score: tripleOrbitScores.get(key) ?? 0 }))
        .sort((left, right) => right.score - left.score || right.index - left.index)
        .map(entry => entry.key)
    : encodedTripleSelectionPolicy === "recent"
      ? orderedOrbitKeys.slice().reverse()
      : orderedOrbitKeys;
  const selectedOrbitKeys = new Set(rankedOrbitKeys.slice(0, encodedTripleOrbitLimit));
  const constraints = tripleConstraints.filter(triple =>
    selectedOrbitKeys.has(tripleOrbitRepresentativeKey(triple))
  );
  const orbitKeys = [...selectedOrbitKeys];
  return {
    constraints,
    orbitCount: selectedOrbitKeys.size,
    orbitKeys,
    orbitScores: orbitKeys.map(key => tripleOrbitScores.get(key) ?? 0)
  };
};
const effectiveNextLayerCoverability = requireNextLayerCoverability
  || learnCellCoverability
  || cellConstraints.length > 0
  || learnPairCoverability
  || pairConstraints.length > 0
  || learnTripleCoverability
  || tripleConstraints.length > 0
  || learnQuadrupleCoverability
  || quadrupleConstraints.length > 0;
const encodeQuadrupleCoverability = tupleEnforcement === "encoded";

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
  const observedPairOrbitKeys = new Set();
  for (const detail of incompatiblePairDetails) {
    const orbitKey = pairOrbitRepresentativeKey(detail.target_cells);
    updatePairOrbitScore(orbitKey, detail.candidate_pairs_blocked);
    observedPairOrbitKeys.add(orbitKey);
  }
  for (const orbitKey of observedPairOrbitKeys) {
    pairOrbitHits.set(orbitKey, (pairOrbitHits.get(orbitKey) ?? 0) + 1);
  }
  if (observedPairOrbitKeys.size) pairDefectOrbitSets.push([...observedPairOrbitKeys].sort());
  let pairsAdded = 0;
  let pairOrbitsAdded = 0;
  let selectedPairCandidateCombinationsBlocked = null;
  for (const detail of incompatiblePairDetails) {
    if (pairOrbitLimit && pairOrbitsAdded >= pairOrbitLimit) break;
    const added = addPairOrbit(detail.target_cells, detail.candidate_pairs_blocked);
    selectedPairCandidateCombinationsBlocked ??= detail.candidate_pairs_blocked;
    if (added) {
      pairOrbitsAdded += 1;
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
    const added = addTripleOrbit(detail.target_cells, detail.candidate_triples_blocked);
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
  z3_formula_cache: z3FormulaCache,
  z3_witness_batch_size: z3WitnessBatchSize,
  z3_interactive: z3Interactive,
  z3_interactive_replace_pairs: z3InteractiveReplacePairs,
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
  pair_soft_minimum: pairSoftMinimum,
  pair_selection: pairSelection,
  encoded_pair_orbit_limit: encodedPairOrbitLimit,
  encoded_pair_selection: encodedPairSelectionPolicy,
  recent_defect_orbit_limit: encodedPairSelectionPolicy === "recent-defect-cover"
    ? recentDefectOrbitLimit
    : null,
  scored_pair_orbits: pairOrbitScores.size,
  recurrent_pair_orbits: pairOrbitHits.size,
  historical_pair_defect_sets: pairDefectOrbitSets.length,
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
  encoded_triple_orbit_limit: encodedTripleOrbitLimit,
  encoded_triple_selection: encodedTripleSelectionPolicy,
  scored_triple_orbits: tripleOrbitScores.size,
  initial_triple_coverability_constraints: initialTripleCount,
  learn_quadruple_coverability: learnQuadrupleCoverability,
  quadruple_orbit_limit: quadrupleOrbitLimit,
  quadruple_max_cell_distance: quadrupleMaximumCellDistance,
  quadruple_encoding: "choice-cnf",
  initial_quadruple_coverability_constraints: initialQuadrupleCount,
  output_directory: outputDirectory
})}\n`);

const proposalTiming = (proposal, witness = null, proposalIndex = 0) => ({
  z3_milliseconds: (witness?.check_milliseconds ?? proposal.check_milliseconds ?? 0)
    + (proposalIndex === 0 ? proposal.construction_milliseconds ?? 0 : 0),
  z3_construction_milliseconds: proposalIndex === 0
    ? proposal.construction_milliseconds ?? null
    : 0,
  z3_check_milliseconds: witness?.check_milliseconds ?? proposal.check_milliseconds ?? null,
  z3_formula_cache_hit: proposal.formula_cache_hit ?? false,
  z3_formula_cache_pairs_reused: proposalIndex === 0 ? proposal.formula_cache_pairs_reused ?? 0 : 0,
  z3_formula_cache_pairs_added: proposalIndex === 0 ? proposal.formula_cache_pairs_added ?? 0 : 0,
  z3_formula_cache_load_milliseconds: proposalIndex === 0
    ? proposal.formula_cache_load_milliseconds ?? 0
    : 0,
  z3_formula_cache_write_milliseconds: proposalIndex === 0
    ? proposal.formula_cache_write_milliseconds ?? 0
    : 0
});

const recordTrial = (iteration, trial) => {
  trials.push(trial);
  if (iteration % progressEvery === 0 || iteration + 1 === iterations) {
    process.stdout.write(`${JSON.stringify({ type: "z3_cegar_trial", ...trial })}\n`);
  }
};

const processSatProposal = ({
  proposal,
  witness,
  iteration,
  iterationSeed,
  proposalIndex,
  proposalBatchSize,
  encodedPairs,
  encodedTriples
}) => {
  const state = { ...proposal, corona: witness.corona };
  const common = {
    iteration,
    proposal_index: proposalIndex,
    proposal_batch_size: proposalBatchSize,
    proposal_batch_requested: proposal.max_witnesses ?? 1,
    proposal_batch_terminal_status: proposal.batch_terminal_status ?? "limit",
    random_seed: iterationSeed,
    z3_status: "sat",
    z3_interactive: proposal.interactive ?? false,
    z3_interactive_clauses_applied: proposal.interactive_clauses_applied ?? 0,
    z3_interactive_pairs_applied: proposal.interactive_pairs_applied ?? 0,
    z3_interactive_pair_coverability_constraints:
      proposal.interactive_pair_coverability_constraints ?? null,
    z3_interactive_pair_coverability_formulas:
      proposal.interactive_pair_coverability_formulas ?? null,
    encoded_pair_coverability_constraints: encodedPairs.constraints.length,
    encoded_pair_coverability_orbits: encodedPairs.orbitCount,
    encoded_pair_orbit_keys: encodedPairs.orbitKeys,
    encoded_pair_orbit_scores: encodedPairs.orbitScores,
    encoded_pair_orbit_hits: encodedPairs.orbitHits,
    encoded_pair_historical_sets_covered: encodedPairs.historicalSetsCovered,
    encoded_pair_recent_defect_size: encodedPairs.recentDefectSize,
    encoded_pair_recent_defect_orbits_selected: encodedPairs.recentDefectOrbitsSelected,
    encoded_pair_recent_defect_complete: encodedPairs.recentDefectComplete,
    z3_pair_soft_satisfied: witness?.pair_soft_satisfied ?? proposal.pair_soft_satisfied ?? null,
    ...proposalTiming(proposal, witness, proposalIndex)
  };
  const outerVerification = verifyPolycubeCoronaPatch(candidate.voxels, state.corona, outerLayer);
  if (!outerVerification.verified) {
    throw new Error(`Z3 outer witness ${iteration}:${proposalIndex} failed verification: ${outerVerification.reason}`);
  }
  let tupleResult = null;
  if (tupleEnforcement !== "encoded") {
    tupleResult = learnTupleObstructions(state);
    if (tupleResult.rejected) {
      const learnedClause = state.corona.map(placementKey);
      const clausesAdded = addClauseOrbit(learnedClause);
      const tupleKind = tupleResult.incompatiblePairs.length
        ? "pair"
        : tupleResult.incompatibleTripleDetails.length
          ? "triple"
          : "quadruple";
      recordTrial(iteration, {
        ...common,
        outer_placements: state.corona.length,
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
        encoded_pair_coverability_constraints: encodedPairs.constraints.length,
        encoded_pair_coverability_orbits: encodedPairs.orbitCount,
        encoded_pair_orbit_keys: encodedPairs.orbitKeys,
        encoded_pair_orbit_scores: encodedPairs.orbitScores,
        encoded_pair_orbit_hits: encodedPairs.orbitHits,
        encoded_pair_historical_sets_covered: encodedPairs.historicalSetsCovered,
        incompatible_target_triples: tupleResult.incompatibleTripleDetails.length,
        triple_audit_truncated: tupleResult.tripleAuditTruncated,
        selected_triple_candidate_combinations_blocked: tupleResult.incompatibleTripleDetails[0]?.candidate_triples_blocked ?? null,
        triple_constraints_added: tupleResult.triplesAdded,
        triple_orbits_added: tupleResult.tripleOrbitsAdded,
        triple_coverability_constraints: tripleConstraints.length,
        encoded_triple_coverability_constraints: encodedTriples.constraints.length,
        encoded_triple_coverability_orbits: encodedTriples.orbitCount,
        encoded_triple_orbit_keys: encodedTriples.orbitKeys,
        encoded_triple_orbit_scores: encodedTriples.orbitScores,
        incompatible_target_quadruples: tupleResult.incompatibleQuadrupleDetails.length,
        selected_quadruple_candidate_combinations_blocked: tupleResult.incompatibleQuadrupleDetails[0]?.candidate_quadruples_blocked ?? null,
        quadruple_constraints_added: tupleResult.quadruplesAdded,
        quadruple_orbits_added: tupleResult.quadrupleOrbitsAdded,
        quadruple_coverability_constraints: quadrupleConstraints.length
      });
      return {
        terminal: false,
        progress: Boolean(clausesAdded || tupleResult.pairsAdded || tupleResult.triplesAdded || tupleResult.quadruplesAdded)
      };
    }
  }
  const continuation = searchPolycubeCorona(candidate.voxels, {
    layers: innerLayer,
    seed: iterationSeed + proposalIndex * 1_000_003,
    fixedPlacements: state.corona,
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
    recordTrial(iteration, {
      ...common,
      outer_placements: state.corona.length,
      continuation_success: true,
      continuation_nodes: continuation.nodes,
      continuation_milliseconds: continuation.milliseconds,
      clauses: clauses.length
    });
    return { terminal: true, progress: true };
  }
  if (!continuation.exhausted) {
    classification = "continuation_incomplete";
    recordTrial(iteration, {
      ...common,
      outer_placements: state.corona.length,
      continuation_success: false,
      continuation_exhausted: false,
      continuation_nodes: continuation.nodes,
      continuation_milliseconds: continuation.milliseconds,
      clauses: clauses.length
    });
    return { terminal: true, progress: false };
  }
  const obstruction = continuation.fixed_obstruction_nogood;
  const learnedClause = obstruction?.fixed_placement_keys?.length
    ? obstruction.fixed_placement_keys
    : state.corona.map(placementKey);
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
  } = tupleResult ?? learnTupleObstructions(state);
  recordTrial(iteration, {
    ...common,
    outer_placements: state.corona.length,
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
    encoded_pair_coverability_constraints: encodedPairs.constraints.length,
    encoded_pair_coverability_orbits: encodedPairs.orbitCount,
    encoded_pair_orbit_keys: encodedPairs.orbitKeys,
    encoded_pair_orbit_scores: encodedPairs.orbitScores,
    encoded_pair_orbit_hits: encodedPairs.orbitHits,
    incompatible_target_triples: incompatibleTripleDetails.length,
    triple_audit_truncated: tripleAuditTruncated,
    selected_triple_candidate_combinations_blocked: incompatibleTripleDetails[0]?.candidate_triples_blocked ?? null,
    triple_constraints_added: triplesAdded,
    triple_orbits_added: tripleOrbitsAdded,
    triple_coverability_constraints: tripleConstraints.length,
    encoded_triple_coverability_constraints: encodedTriples.constraints.length,
    encoded_triple_coverability_orbits: encodedTriples.orbitCount,
    encoded_triple_orbit_keys: encodedTriples.orbitKeys,
    encoded_triple_orbit_scores: encodedTriples.orbitScores,
    incompatible_target_quadruples: incompatibleQuadrupleDetails.length,
    selected_quadruple_candidate_combinations_blocked: incompatibleQuadrupleDetails[0]?.candidate_quadruples_blocked ?? null,
    quadruple_constraints_added: quadruplesAdded,
    quadruple_orbits_added: quadrupleOrbitsAdded,
    quadruple_coverability_constraints: quadrupleConstraints.length
  });
  return {
    terminal: false,
    progress: Boolean(clausesAdded || cellsAdded || pairsAdded || triplesAdded || quadruplesAdded)
  };
};

const writeCurrentReports = () => {
  writeFileSync(clausePath, `${JSON.stringify({ clauses }, null, 2)}\n`);
  writeFileSync(cellPath, `${JSON.stringify({ cells: cellConstraints }, null, 2)}\n`);
  writeFileSync(pairPath, `${JSON.stringify({
    pairs: pairConstraints,
    pair_orbit_scores: serializedPairOrbitScores(),
    pair_orbit_hits: serializedPairOrbitHits(),
    pair_defect_orbit_sets: pairDefectOrbitSets
  }, null, 2)}\n`);
  const encodedPairs = selectEncodedPairs();
  writeFileSync(encodedPairPath, `${JSON.stringify({ pairs: encodedPairs.constraints }, null, 2)}\n`);
  writeFileSync(triplePath, `${JSON.stringify({
    triples: tripleConstraints,
    triple_orbit_scores: serializedTripleOrbitScores()
  }, null, 2)}\n`);
  const encodedTriples = selectEncodedTriples();
  writeFileSync(encodedTriplePath, `${JSON.stringify({ triples: encodedTriples.constraints }, null, 2)}\n`);
  writeFileSync(quadruplePath, `${JSON.stringify({ quadruples: quadrupleConstraints }, null, 2)}\n`);
  return { encodedPairs, encodedTriples };
};

const solverArgumentsFor = (iterationSeed, encodedPairs, encodedTriples, witnessPath = null) => {
  const solverArguments = [
    pythonSolver,
    `--key=${polycubeKey(candidate.voxels)}`,
    `--layer=${outerLayer}`,
    `--timeout-ms=${z3TimeoutMs}`,
    `--max-witnesses=${z3WitnessBatchSize}`,
    `--backend=${backend}`,
    `--random-seed=${iterationSeed}`,
    `--lookahead-conflict-encoding=${lookaheadConflictEncoding}`,
    `--forbidden-clause-report=${clausePath}`
  ];
  if (witnessPath) solverArguments.push(`--output=${witnessPath}`);
  if (minPlacements !== null) solverArguments.push(`--min-placements=${minPlacements}`);
  if (maxPlacements !== null) solverArguments.push(`--max-placements=${maxPlacements}`);
  if (requireNextLayerCoverability) solverArguments.push("--require-next-layer-coverability");
  if (cellConstraints.length) solverArguments.push(`--cell-coverability-report=${cellPath}`);
  if (rootSymmetryBreaking) solverArguments.push("--root-symmetry-breaking");
  if (encodedPairs.constraints.length) {
    solverArguments.push(`--pair-coverability-report=${encodedPairPath}`);
    solverArguments.push(`--pair-encoding=${pairEncoding}`);
    if (pairSoftMinimum !== null) solverArguments.push(`--pair-soft-minimum=${pairSoftMinimum}`);
  }
  if (encodedTriples.constraints.length) {
    solverArguments.push(`--triple-coverability-report=${encodedTriplePath}`);
    solverArguments.push(`--triple-encoding=${tripleEncoding}`);
  }
  if (quadrupleConstraints.length && encodeQuadrupleCoverability) {
    solverArguments.push(`--quadruple-coverability-report=${quadruplePath}`);
  }
  if (z3FormulaCache) solverArguments.push(`--formula-cache=${formulaCachePath}`);
  return solverArguments;
};

const runInteractiveCegar = async () => {
  let { encodedPairs, encodedTriples } = writeCurrentReports();
  const solverArguments = solverArgumentsFor(randomSeed, encodedPairs, encodedTriples);
  solverArguments.push("--interactive-jsonl");
  if (z3InteractiveReplacePairs) solverArguments.push("--interactive-replace-pairs");
  const worker = spawn(python, solverArguments, { stdio: ["pipe", "pipe", "pipe"] });
  const lines = createInterface({ input: worker.stdout });
  const iterator = lines[Symbol.asyncIterator]();
  let stderr = "";
  worker.stderr.setEncoding("utf8");
  worker.stderr.on("data", chunk => { stderr += chunk; });
  const readEvent = async timeoutMs => {
    let timeoutId;
    try {
      const result = await Promise.race([
        iterator.next(),
        new Promise((_, reject) => {
          timeoutId = setTimeout(() => reject(new Error("Interactive Z3 worker timed out")), timeoutMs);
        })
      ]);
      if (result.done) {
        throw new Error(stderr.trim() || "Interactive Z3 worker exited without a response");
      }
      return JSON.parse(result.value);
    } finally {
      clearTimeout(timeoutId);
    }
  };
  let pendingClauses = [];
  let pendingPairs = [];
  const encodedPairKeysSent = new Set(encodedPairs.constraints.map(pair => pair.join(";")));
  try {
    const ready = await readEvent(z3TimeoutMs + z3ProcessGraceMs);
    if (ready.type !== "ready") throw new Error(`Expected interactive ready event, received ${ready.type}`);
    for (let iteration = 0; iteration < iterations; iteration += 1) {
      const iterationSeed = randomSeed + iteration * seedStride;
      worker.stdin.write(`${JSON.stringify({
        type: "next",
        timeout_ms: z3TimeoutMs,
        clauses: pendingClauses,
        ...(z3InteractiveReplacePairs
          ? { replace_pairs: encodedPairs.constraints }
          : { pairs: pendingPairs })
      })}\n`);
      const result = await readEvent(z3TimeoutMs + z3ProcessGraceMs);
      if (result.type !== "result") throw new Error(`Expected interactive result event, received ${result.type}`);
      const proposal = {
        kind: "polycube_corona_z3_interactive",
        z3_status: result.z3_status,
        reason_unknown: result.reason_unknown,
        corona: result.corona,
        max_witnesses: 1,
        batch_terminal_status: "interactive",
        construction_milliseconds: iteration === 0 ? ready.construction_milliseconds : 0,
        check_milliseconds: result.check_milliseconds,
        formula_cache_hit: ready.formula_cache_hit,
        formula_cache_pairs_reused: iteration === 0 ? ready.formula_cache_pairs_reused : 0,
        formula_cache_pairs_added: iteration === 0 ? ready.formula_cache_pairs_added : 0,
        formula_cache_load_milliseconds: iteration === 0 ? ready.formula_cache_load_milliseconds : 0,
        formula_cache_write_milliseconds: iteration === 0 ? ready.formula_cache_write_milliseconds : 0,
        interactive: true,
        interactive_clauses_applied: result.clauses_added,
        interactive_pairs_applied: result.pairs_added,
        interactive_forbidden_clauses: result.forbidden_clauses,
        interactive_pair_coverability_constraints: result.pair_coverability_constraints,
        interactive_pair_coverability_formulas: result.pair_coverability_formulas
      };
      const witnessPath = resolve(outputDirectory, `outer-witness-${String(iteration).padStart(4, "0")}.json`);
      writeFileSync(witnessPath, `${JSON.stringify(proposal, null, 2)}\n`);
      if (proposal.z3_status === "unsat") {
        classification = minPlacements !== null || maxPlacements !== null
          ? "placement_bound_exhausted"
          : initialClauseCount > 0
            ? "conditional_unsat"
            : "certified_non_tiler";
        recordTrial(iteration, {
          iteration,
          proposal_index: 0,
          proposal_batch_size: 0,
          proposal_batch_requested: 1,
          proposal_batch_terminal_status: "interactive",
          random_seed: iterationSeed,
          z3_status: "unsat",
          z3_interactive: true,
          z3_interactive_clauses_applied: result.clauses_added,
          z3_interactive_pairs_applied: result.pairs_added,
          z3_interactive_pair_coverability_constraints: result.pair_coverability_constraints,
          z3_interactive_pair_coverability_formulas: result.pair_coverability_formulas,
          encoded_pair_coverability_constraints: encodedPairs.constraints.length,
          encoded_pair_coverability_orbits: encodedPairs.orbitCount,
          ...proposalTiming(proposal),
          clauses: clauses.length
        });
        break;
      }
      if (proposal.z3_status !== "sat") {
        z3UnknownTrials += 1;
        classification = "z3_incomplete";
        recordTrial(iteration, {
          iteration,
          proposal_index: 0,
          proposal_batch_size: 0,
          proposal_batch_requested: 1,
          proposal_batch_terminal_status: "interactive",
          random_seed: iterationSeed,
          z3_status: proposal.z3_status,
          z3_interactive: true,
          z3_interactive_clauses_applied: result.clauses_added,
          z3_interactive_pairs_applied: result.pairs_added,
          z3_interactive_pair_coverability_constraints: result.pair_coverability_constraints,
          z3_interactive_pair_coverability_formulas: result.pair_coverability_formulas,
          encoded_pair_coverability_constraints: encodedPairs.constraints.length,
          encoded_pair_coverability_orbits: encodedPairs.orbitCount,
          ...proposalTiming(proposal),
          reason_unknown: proposal.reason_unknown,
          clauses: clauses.length
        });
        break;
      }
      const clauseCountBefore = clauses.length;
      const outcome = processSatProposal({
        proposal,
        witness: { corona: proposal.corona, check_milliseconds: proposal.check_milliseconds },
        iteration,
        iterationSeed,
        proposalIndex: 0,
        proposalBatchSize: 1,
        encodedPairs,
        encodedTriples
      });
      if (outcome.terminal) break;
      if (!outcome.progress) {
        classification = "duplicate_obstruction";
        break;
      }
      pendingClauses = clauses.slice(clauseCountBefore);
      const nextEncodedPairs = selectEncodedPairs();
      if (z3InteractiveReplacePairs) {
        pendingPairs = [];
        encodedPairs = nextEncodedPairs;
      } else {
        pendingPairs = nextEncodedPairs.constraints.filter(pair => {
          const key = pair.join(";");
          if (encodedPairKeysSent.has(key)) return false;
          encodedPairKeysSent.add(key);
          return true;
        });
        encodedPairs = describeEncodedPairs(pairConstraints.filter(pair =>
          encodedPairKeysSent.has(pair.join(";"))
        ));
      }
    }
  } finally {
    if (!worker.killed) {
      worker.stdin.write(`${JSON.stringify({ type: "stop" })}\n`);
      worker.stdin.end();
    }
    lines.close();
  }
};

if (z3Interactive) {
  await runInteractiveCegar();
} else for (let iteration = 0; iteration < iterations; iteration += 1) {
  const { encodedPairs, encodedTriples } = writeCurrentReports();
  const witnessPath = resolve(outputDirectory, `outer-witness-${String(iteration).padStart(4, "0")}.json`);
  const iterationSeed = randomSeed + iteration * seedStride;
  const solverArguments = solverArgumentsFor(iterationSeed, encodedPairs, encodedTriples, witnessPath);
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
        encoded_pair_coverability_constraints: encodedPairs.constraints.length,
        encoded_pair_coverability_orbits: encodedPairs.orbitCount,
        encoded_pair_orbit_keys: encodedPairs.orbitKeys,
        encoded_pair_orbit_scores: encodedPairs.orbitScores,
        encoded_pair_orbit_hits: encodedPairs.orbitHits,
        encoded_pair_historical_sets_covered: encodedPairs.historicalSetsCovered,
        triple_coverability_constraints: tripleConstraints.length,
        encoded_triple_coverability_constraints: encodedTriples.constraints.length,
        encoded_triple_coverability_orbits: encodedTriples.orbitCount,
        encoded_triple_orbit_keys: encodedTriples.orbitKeys,
        encoded_triple_orbit_scores: encodedTriples.orbitScores,
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
    trials.push({
      iteration,
      random_seed: iterationSeed,
      z3_status: "unsat",
      z3_milliseconds: proposal.milliseconds,
      ...proposalTiming(proposal),
      clauses: clauses.length
    });
    break;
  }
  if (proposal.z3_status !== "sat") {
    z3UnknownTrials += 1;
    const trial = {
      iteration,
      random_seed: iterationSeed,
      z3_status: proposal.z3_status,
      z3_milliseconds: proposal.milliseconds,
      ...proposalTiming(proposal),
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
  const proposalWitnesses = Array.isArray(proposal.witnesses) && proposal.witnesses.length
    ? proposal.witnesses
    : [{ corona: proposal.corona, check_milliseconds: proposal.check_milliseconds }];
  let batchMadeProgress = false;
  let batchReachedTerminalResult = false;
  for (let proposalIndex = 0; proposalIndex < proposalWitnesses.length; proposalIndex += 1) {
    const outcome = processSatProposal({
      proposal,
      witness: proposalWitnesses[proposalIndex],
      iteration,
      iterationSeed,
      proposalIndex,
      proposalBatchSize: proposalWitnesses.length,
      encodedPairs,
      encodedTriples
    });
    batchMadeProgress ||= outcome.progress;
    if (outcome.terminal) {
      batchReachedTerminalResult = true;
      break;
    }
  }
  if (batchReachedTerminalResult) break;
  if (proposal.batch_terminal_status === "unknown") {
    z3UnknownTrials += 1;
    const successfulCheckMilliseconds = proposalWitnesses.reduce(
      (total, witness) => total + (witness.check_milliseconds ?? 0),
      0
    );
    recordTrial(iteration, {
      iteration,
      proposal_index: proposalWitnesses.length,
      proposal_batch_size: proposalWitnesses.length,
      proposal_batch_requested: proposal.max_witnesses ?? z3WitnessBatchSize,
      proposal_batch_terminal_status: proposal.batch_terminal_status,
      random_seed: iterationSeed,
      z3_status: "unknown",
      z3_milliseconds: Math.max(0, (proposal.check_milliseconds ?? 0) - successfulCheckMilliseconds),
      z3_construction_milliseconds: 0,
      z3_check_milliseconds: Math.max(0, (proposal.check_milliseconds ?? 0) - successfulCheckMilliseconds),
      z3_formula_cache_hit: proposal.formula_cache_hit ?? false,
      z3_formula_cache_pairs_reused: 0,
      z3_formula_cache_pairs_added: 0,
      z3_formula_cache_load_milliseconds: 0,
      z3_formula_cache_write_milliseconds: 0,
      reason_unknown: proposal.batch_reason_unknown,
      obstruction_kind: "batch_enumeration_timeout",
      clauses: clauses.length
    });
    if (!continueOnZ3Unknown) {
      classification = "z3_incomplete";
      break;
    }
  }
  if (!batchMadeProgress) {
    classification = proposal.batch_terminal_status === "unknown"
      ? "z3_incomplete"
      : "duplicate_obstruction";
    break;
  }
}

// Keep resumable artifacts synchronized even when the final iteration learns
// new obligations and exits before the next proposal write.
writeFileSync(clausePath, `${JSON.stringify({ clauses }, null, 2)}\n`);
writeFileSync(cellPath, `${JSON.stringify({ cells: cellConstraints }, null, 2)}\n`);
writeFileSync(pairPath, `${JSON.stringify({
  pairs: pairConstraints,
  pair_orbit_scores: serializedPairOrbitScores(),
  pair_orbit_hits: serializedPairOrbitHits(),
  pair_defect_orbit_sets: pairDefectOrbitSets
}, null, 2)}\n`);
const finalEncodedPairSelection = selectEncodedPairs();
writeFileSync(encodedPairPath, `${JSON.stringify({ pairs: finalEncodedPairSelection.constraints }, null, 2)}\n`);
writeFileSync(triplePath, `${JSON.stringify({
  triples: tripleConstraints,
  triple_orbit_scores: serializedTripleOrbitScores()
}, null, 2)}\n`);
const finalEncodedTripleSelection = selectEncodedTriples();
writeFileSync(encodedTriplePath, `${JSON.stringify({ triples: finalEncodedTripleSelection.constraints }, null, 2)}\n`);
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
  pair_soft_minimum: pairSoftMinimum,
  pair_selection: pairSelection,
  encoded_pair_orbit_limit: encodedPairOrbitLimit,
  encoded_pair_selection: encodedPairSelectionPolicy,
  recent_defect_orbit_limit: encodedPairSelectionPolicy === "recent-defect-cover"
    ? recentDefectOrbitLimit
    : null,
  encoded_pair_coverability_orbits: finalEncodedPairSelection.orbitCount,
  encoded_pair_coverability_constraints: finalEncodedPairSelection.constraints.length,
  encoded_pair_orbit_keys: finalEncodedPairSelection.orbitKeys,
  encoded_pair_orbit_scores: finalEncodedPairSelection.orbitScores,
  encoded_pair_orbit_hits: finalEncodedPairSelection.orbitHits,
  encoded_pair_historical_sets_covered: finalEncodedPairSelection.historicalSetsCovered,
  encoded_pair_recent_defect_size: finalEncodedPairSelection.recentDefectSize,
  encoded_pair_recent_defect_orbits_selected: finalEncodedPairSelection.recentDefectOrbitsSelected,
  encoded_pair_recent_defect_complete: finalEncodedPairSelection.recentDefectComplete,
  pair_orbit_scores: serializedPairOrbitScores(),
  pair_orbit_hits: serializedPairOrbitHits(),
  pair_defect_orbit_sets: pairDefectOrbitSets,
  pair_defect_orbit_set_count: pairDefectOrbitSets.length,
  lookahead_conflict_encoding: lookaheadConflictEncoding,
  root_symmetry_breaking: rootSymmetryBreaking,
  z3_unknown_trials: z3UnknownTrials,
  z3_timeout_ms: z3TimeoutMs,
  z3_process_grace_ms: z3ProcessGraceMs,
  z3_formula_cache: z3FormulaCache,
  z3_witness_batch_size: z3WitnessBatchSize,
  z3_interactive: z3Interactive,
  z3_interactive_replace_pairs: z3InteractiveReplacePairs,
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
  encoded_triple_orbit_limit: encodedTripleOrbitLimit,
  encoded_triple_selection: encodedTripleSelectionPolicy,
  encoded_triple_coverability_orbits: finalEncodedTripleSelection.orbitCount,
  encoded_triple_coverability_constraints: finalEncodedTripleSelection.constraints.length,
  encoded_triple_orbit_keys: finalEncodedTripleSelection.orbitKeys,
  encoded_triple_orbit_scores: finalEncodedTripleSelection.orbitScores,
  triple_orbit_scores: serializedTripleOrbitScores(),
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
