#!/usr/bin/env node

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { polycubeKey } from "../assets/polycube-enumerator.js";
import {
  enumeratePolycubeCoronaPlacements,
  polycubeCellPairOrbitKeys,
  polycubeCellTripleOrbitKeys
} from "../assets/polycube-corona-search.js";

const python = process.env.PYTHON ?? "python3";
const solver = fileURLToPath(new URL("./solve_polycube_corona_z3.py", import.meta.url));
const cegar = fileURLToPath(new URL("./screen-polycube-corona-z3-cegar.mjs", import.meta.url));
const recurrenceReplay = fileURLToPath(new URL("./replay-polycube-pair-recurrence.mjs", import.meta.url));
const cegarSource = readFileSync(cegar, "utf8");
assert.match(cegarSource, /Keep resumable artifacts synchronized[\s\S]*?writeFileSync\(clausePath[\s\S]*?writeFileSync\(cellPath[\s\S]*?writeFileSync\(pairPath[\s\S]*?writeFileSync\(triplePath[\s\S]*?writeFileSync\(quadruplePath/);
assert.match(cegarSource, /const tripleAuditLimit = integerArg\("triple-audit-limit", tripleOrbitLimit \|\| 1, 1\)/);
assert.match(cegarSource, /limit: tripleAuditLimit \+ 1[\s\S]*?tripleAuditTruncated = incompatibleTripleAudit\.length > tripleAuditLimit/);
assert.match(cegarSource, /triple_audit_truncated: tripleAuditTruncated/);
assert.match(cegarSource, /--tuple-enforcement must be encoded, hybrid-higher, hybrid-all, lazy-higher, or lazy-all/);
assert.match(cegarSource, /--encoded-pair-selection must be first, recent, max-blocked-combinations, frequency-impact, or frequency-weighted-impact/);
assert.match(cegarSource, /--encoded-triple-selection must be first, recent, or max-blocked-combinations/);
assert.match(cegarSource, /triple_orbit_scores: serializedTripleOrbitScores\(\)/);
assert.match(cegarSource, /--formula-cache=\$\{formulaCachePath\}/);
assert.match(cegarSource, /--max-witnesses=\$\{z3WitnessBatchSize\}/);
assert.match(cegarSource, /const processSatProposal =/);
assert.match(cegarSource, /solverArguments\.push\("--interactive-jsonl"\)/);
assert.match(cegarSource, /solverArguments\.push\("--interactive-replace-pairs"\)/);
assert.match(cegarSource, /replace_pairs: encodedPairs\.constraints/);
assert.match(cegarSource, /interactive_clauses_applied/);
assert.match(cegarSource, /if \(encodedPairs\.constraints\.length\)/);
assert.match(cegarSource, /--pair-coverability-report=\$\{encodedPairPath\}/);
assert.match(cegarSource, /const encodedTriples = selectEncodedTriples\(\)/);
assert.match(cegarSource, /--triple-coverability-report=\$\{encodedTriplePath\}/);
assert.match(cegarSource, /if \(tupleEnforcement !== "encoded"\)[\s\S]*?continuation_skipped: true[\s\S]*?const continuation = searchPolycubeCorona/);
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === "p9-42947");
assert.ok(candidate);
const nonTiler = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === "p10-052670");
assert.ok(nonTiler);

const directory = mkdtempSync(join(tmpdir(), "polycube-z3-cegar-test-"));
try {
  const boundedOutput = join(directory, "bounded.json");
  const bounded = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=1",
    "--root-symmetry-breaking",
    `--output=${boundedOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(bounded.status, 0, bounded.stderr);
  const boundedReport = JSON.parse(readFileSync(boundedOutput, "utf8"));
  assert.equal(boundedReport.z3_status, "unsat");
  assert.ok(boundedReport.construction_milliseconds >= 0);
  assert.ok(boundedReport.check_milliseconds >= 0);
  assert.ok(boundedReport.milliseconds >= boundedReport.construction_milliseconds);
  assert.equal(boundedReport.classification, "placement_bound_exhausted");
  assert.equal(boundedReport.max_placements, 1);
  assert.equal(boundedReport.root_symmetry_breaking, true);
  assert.equal(boundedReport.root_stabilizer_size, 3);
  assert.ok(boundedReport.symmetry_breaking_constraints > 0);
  assert.match(boundedReport.warning, /not a non-tiling or aperiodicity certificate/);

  const minimumBoundedOutput = join(directory, "minimum-bounded.json");
  const minimumBounded = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--min-placements=1000",
    `--output=${minimumBoundedOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(minimumBounded.status, 0, minimumBounded.stderr);
  const minimumBoundedReport = JSON.parse(readFileSync(minimumBoundedOutput, "utf8"));
  assert.equal(minimumBoundedReport.z3_status, "unsat");
  assert.equal(minimumBoundedReport.classification, "placement_bound_exhausted");
  assert.equal(minimumBoundedReport.min_placements, 1000);
  assert.equal(minimumBoundedReport.max_placements, null);
  assert.match(minimumBoundedReport.warning, /\[1000, unbounded\]/);

  const allForbiddenPath = join(directory, "all-forbidden.json");
  const allForbiddenClauses = enumeratePolycubeCoronaPlacements(candidate.voxels, 1)
    .map(placement => [placement.cells.map(cell => cell.join(",")).sort().join(";")]);
  writeFileSync(allForbiddenPath, `${JSON.stringify({ clauses: allForbiddenClauses })}\n`);
  const conditionalOutput = join(directory, "conditional.json");
  const conditional = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    `--forbidden-clause-report=${allForbiddenPath}`,
    `--output=${conditionalOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(conditional.status, 0, conditional.stderr);
  const conditionalReport = JSON.parse(readFileSync(conditionalOutput, "utf8"));
  assert.equal(conditionalReport.z3_status, "unsat");
  assert.equal(conditionalReport.classification, "unsat_under_forbidden_clauses");
  assert.match(conditionalReport.warning, /validate their continuation proofs/);

  const cegarOutput = join(directory, "cegar-summary.json");
  const boundedCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=1",
    "--z3-timeout-ms=10000",
    `--python=${python}`,
    `--output-dir=${join(directory, "cegar")}`,
    `--report-output=${cegarOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(boundedCegar.status, 0, boundedCegar.stderr);
  const cegarReport = JSON.parse(readFileSync(cegarOutput, "utf8"));
  assert.equal(cegarReport.classification, "placement_bound_exhausted");
  assert.equal(cegarReport.max_placements, 1);
  assert.match(cegarReport.warning, /not a non-tiling or aperiodicity certificate/);

  const minimumBoundedCegarOutput = join(directory, "minimum-bounded-cegar-summary.json");
  const minimumBoundedCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--min-placements=1000",
    "--z3-timeout-ms=10000",
    `--python=${python}`,
    `--output-dir=${join(directory, "minimum-bounded-cegar")}`,
    `--report-output=${minimumBoundedCegarOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(minimumBoundedCegar.status, 0, minimumBoundedCegar.stderr);
  const minimumBoundedCegarReport = JSON.parse(readFileSync(minimumBoundedCegarOutput, "utf8"));
  assert.equal(minimumBoundedCegarReport.classification, "placement_bound_exhausted");
  assert.equal(minimumBoundedCegarReport.min_placements, 1000);
  assert.equal(minimumBoundedCegarReport.max_placements, null);
  assert.match(minimumBoundedCegarReport.warning, /\[1000, unbounded\]/);

  const conditionalCegarOutput = join(directory, "conditional-cegar-summary.json");
  const conditionalCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--z3-timeout-ms=10000",
    `--python=${python}`,
    `--initial-clause-report=${allForbiddenPath}`,
    `--output-dir=${join(directory, "conditional-cegar")}`,
    `--report-output=${conditionalCegarOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(conditionalCegar.status, 0, conditionalCegar.stderr);
  const conditionalCegarReport = JSON.parse(readFileSync(conditionalCegarOutput, "utf8"));
  assert.equal(conditionalCegarReport.classification, "conditional_unsat");
  assert.match(conditionalCegarReport.warning, /independently replay/);

  const learnedCellOutput = join(directory, "learned-cell-summary.json");
  const learnedCellCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p10-052670",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=2",
    "--learn-cell-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--output-dir=${join(directory, "learned-cell")}`,
    `--report-output=${learnedCellOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(learnedCellCegar.status, 0, learnedCellCegar.stderr);
  const learnedCellReport = JSON.parse(readFileSync(learnedCellOutput, "utf8"));
  assert.equal(learnedCellReport.classification, "certified_non_tiler");
  assert.equal(learnedCellReport.require_next_layer_coverability, false);
  assert.equal(learnedCellReport.learn_cell_coverability, true);
  assert.equal(learnedCellReport.cell_coverability_constraint_count, 1);
  assert.equal(learnedCellReport.trials[0].obstruction_kind, "immediate_dead_target");
  assert.equal(learnedCellReport.trials[0].cell_constraints_added, 1);
  assert.equal(learnedCellReport.trials[1].z3_status, "unsat");
  const learnedCellProposal = JSON.parse(readFileSync(join(directory, "learned-cell", "outer-witness-0001.json"), "utf8"));
  assert.equal(learnedCellProposal.require_next_layer_coverability, false);
  assert.equal(learnedCellProposal.cell_coverability_constraints, 1);
  assert.equal(learnedCellProposal.lookahead_target_cells, 1);

  const distanceFromRoot = cell => Math.min(...candidate.voxels.map(root =>
    Math.abs(cell[0] - root[0]) + Math.abs(cell[1] - root[1]) + Math.abs(cell[2] - root[2])
  ));
  const secondRing = [...new Set(enumeratePolycubeCoronaPlacements(candidate.voxels, 2)
    .flatMap(placement => placement.cells)
    .filter(cell => distanceFromRoot(cell) === 2)
    .map(cell => cell.join(",")))].sort();
  assert.ok(secondRing.length > 1);
  const pairPath = join(directory, "pair-coverability.json");
  writeFileSync(pairPath, `${JSON.stringify({ pairs: [[secondRing[0], secondRing.at(-1)]] })}\n`);
  const pairOrbitKey = pair => polycubeCellPairOrbitKeys(candidate.voxels, pair)
    .map(item => [...item].sort().join(";"))
    .sort()[0];
  const scoredPairsByOrbit = new Map();
  for (let left = 0; left < secondRing.length && scoredPairsByOrbit.size < 2; left += 1) {
    for (let right = left + 1; right < secondRing.length && scoredPairsByOrbit.size < 2; right += 1) {
      const pair = [secondRing[left], secondRing[right]];
      scoredPairsByOrbit.set(pairOrbitKey(pair), pair);
    }
  }
  assert.equal(scoredPairsByOrbit.size, 2);
  const [scoredPairLow, scoredPairHigh] = [...scoredPairsByOrbit.values()];
  const scoredPairLowKey = pairOrbitKey(scoredPairLow);
  const scoredPairHighKey = pairOrbitKey(scoredPairHigh);
  const scoredPairPath = join(directory, "scored-pair-coverability.json");
  writeFileSync(scoredPairPath, `${JSON.stringify({
    pairs: [scoredPairLow, scoredPairHigh],
    pair_orbit_scores: {
      [scoredPairLowKey]: 5,
      [scoredPairHighKey]: 23
    },
    pair_orbit_hits: {
      [scoredPairLowKey]: 7,
      [scoredPairHighKey]: 2
    }
  })}\n`);
  const replacePairWorker = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    "--interactive-jsonl",
    "--interactive-replace-pairs",
    `--pair-coverability-report=${scoredPairPath}`
  ], {
    encoding: "utf8",
    timeout: 30_000,
    input: [
      JSON.stringify({ type: "next", timeout_ms: 10_000, replace_pairs: [scoredPairLow] }),
      JSON.stringify({ type: "next", timeout_ms: 10_000, replace_pairs: [scoredPairHigh] }),
      JSON.stringify({ type: "stop" })
    ].join("\n") + "\n"
  });
  assert.equal(replacePairWorker.status, 0, replacePairWorker.stderr);
  const replacePairEvents = replacePairWorker.stdout.trim().split("\n").map(line => JSON.parse(line));
  assert.equal(replacePairEvents[0].type, "ready");
  assert.equal(replacePairEvents[0].pair_coverability_formulas, 2);
  assert.equal(replacePairEvents[0].interactive_replace_pairs, true);
  assert.equal(replacePairEvents[1].pair_coverability_constraints, 1);
  assert.equal(replacePairEvents[1].pair_coverability_formulas, 2);
  assert.equal(replacePairEvents[2].pair_coverability_constraints, 1);
  assert.equal(replacePairEvents[2].pair_coverability_formulas, 2);
  const replacePairCachePath = join(directory, "replace-pair-formula-cache.smt2");
  const replacePairLowPath = join(directory, "replace-pair-low.json");
  const replacePairHighPath = join(directory, "replace-pair-high.json");
  writeFileSync(replacePairLowPath, `${JSON.stringify({ pairs: [scoredPairLow] })}\n`);
  writeFileSync(replacePairHighPath, `${JSON.stringify({ pairs: [scoredPairHigh] })}\n`);
  const replacePairCacheArguments = pairReport => [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    "--interactive-jsonl",
    "--interactive-replace-pairs",
    `--pair-coverability-report=${pairReport}`,
    `--formula-cache=${replacePairCachePath}`
  ];
  const replacePairCacheMiss = spawnSync(python, replacePairCacheArguments(replacePairLowPath), {
    encoding: "utf8",
    timeout: 30_000,
    input: `${JSON.stringify({ type: "stop" })}\n`
  });
  assert.equal(replacePairCacheMiss.status, 0, replacePairCacheMiss.stderr);
  const replacePairCacheHit = spawnSync(python, replacePairCacheArguments(replacePairHighPath), {
    encoding: "utf8",
    timeout: 30_000,
    input: `${JSON.stringify({ type: "stop" })}\n`
  });
  assert.equal(replacePairCacheHit.status, 0, replacePairCacheHit.stderr);
  const replacePairCacheReady = JSON.parse(replacePairCacheHit.stdout.trim());
  assert.equal(replacePairCacheReady.formula_cache_hit, true);
  assert.equal(replacePairCacheReady.formula_cache_pairs_reused, 1);
  assert.equal(replacePairCacheReady.formula_cache_pairs_added, 1);
  assert.equal(replacePairCacheReady.pair_coverability_constraints, 1);
  assert.equal(replacePairCacheReady.pair_coverability_formulas, 2);
  const triplePath = join(directory, "triple-coverability.json");
  writeFileSync(triplePath, `${JSON.stringify({
    triples: [[secondRing[0], secondRing[1], secondRing.at(-1)]]
  })}\n`);
  const scoredTriple = [secondRing[0], secondRing[1], secondRing.at(-1)];
  const scoredTripleOrbitKey = polycubeCellTripleOrbitKeys(candidate.voxels, scoredTriple)
    .map(triple => [...triple].sort().join(";"))
    .sort()[0];
  const scoredTriplePath = join(directory, "scored-triple-coverability.json");
  writeFileSync(scoredTriplePath, `${JSON.stringify({
    triples: [scoredTriple],
    triple_orbit_scores: { [scoredTripleOrbitKey]: 17 }
  })}\n`);
  const quadruplePath = join(directory, "quadruple-coverability.json");
  writeFileSync(quadruplePath, `${JSON.stringify({
    quadruples: [[secondRing[0], secondRing[1], secondRing[2], secondRing.at(-1)]]
  })}\n`);
  const cellPath = join(directory, "cell-coverability.json");
  writeFileSync(cellPath, `${JSON.stringify({ cells: [secondRing[0]] })}\n`);

  const cellOutput = join(directory, "cell-encoded.json");
  const cellEncoded = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    `--cell-coverability-report=${cellPath}`,
    `--output=${cellOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(cellEncoded.status, 0, cellEncoded.stderr);
  const cellReport = JSON.parse(readFileSync(cellOutput, "utf8"));
  assert.equal(cellReport.z3_status, "sat");
  assert.equal(cellReport.require_next_layer_coverability, false);
  assert.equal(cellReport.cell_coverability_constraints, 1);
  assert.equal(cellReport.lookahead_target_cells, 1);
  assert.ok(cellReport.lookahead_placements > 0);

  const groupedCellOutput = join(directory, "cell-grouped-pb.json");
  const groupedCellEncoded = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--lookahead-conflict-encoding=grouped-pb",
    `--cell-coverability-report=${cellPath}`,
    `--output=${groupedCellOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(groupedCellEncoded.status, 0, groupedCellEncoded.stderr);
  const groupedCellReport = JSON.parse(readFileSync(groupedCellOutput, "utf8"));
  assert.equal(groupedCellReport.z3_status, cellReport.z3_status);
  assert.equal(groupedCellReport.lookahead_conflict_encoding, "grouped-pb");
  assert.equal(groupedCellReport.lookahead_conflicts, cellReport.lookahead_conflicts);
  assert.ok(groupedCellReport.lookahead_conflict_groups > 0);
  assert.ok(groupedCellReport.constraints < cellReport.constraints);

  const tripleOutput = join(directory, "triple-encoded.json");
  const tripleEncoded = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    "--lookahead-conflict-encoding=grouped-pb",
    `--triple-coverability-report=${triplePath}`,
    `--output=${tripleOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(tripleEncoded.status, 0, tripleEncoded.stderr);
  const tripleReport = JSON.parse(readFileSync(tripleOutput, "utf8"));
  assert.equal(tripleReport.z3_status, "sat");
  assert.equal(tripleReport.triple_coverability_constraints, 1);
  assert.equal(tripleReport.triple_coverability_encoding, "choice-cnf");
  assert.equal(tripleReport.triple_coverability_terms, 0);
  assert.ok(tripleReport.triple_coverability_choice_variables > 0);
  assert.ok(tripleReport.triple_coverability_incompatibilities >= 0);

  const batchOutput = join(directory, "batch-encoded.json");
  const batchEncoded = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    "--lookahead-conflict-encoding=grouped-pb",
    "--max-witnesses=3",
    `--output=${batchOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(batchEncoded.status, 0, batchEncoded.stderr);
  const batchReport = JSON.parse(readFileSync(batchOutput, "utf8"));
  assert.equal(batchReport.z3_status, "sat");
  assert.equal(batchReport.witness_count, 3);
  assert.equal(batchReport.batch_terminal_status, "limit");
  assert.equal(batchReport.batch_blocking_clauses, 2);
  assert.equal(batchReport.witnesses.length, 3);
  assert.equal(new Set(batchReport.coronas.map(corona => JSON.stringify(
    corona.map(placement => placement.cells).sort()
  ))).size, 3);

  const quadrupleOutput = join(directory, "quadruple-encoded.json");
  const quadrupleEncoded = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    "--lookahead-conflict-encoding=grouped-pb",
    `--quadruple-coverability-report=${quadruplePath}`,
    `--output=${quadrupleOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(quadrupleEncoded.status, 0, quadrupleEncoded.stderr);
  const quadrupleReport = JSON.parse(readFileSync(quadrupleOutput, "utf8"));
  assert.equal(quadrupleReport.z3_status, "sat");
  assert.equal(quadrupleReport.quadruple_coverability_constraints, 1);
  assert.equal(quadrupleReport.quadruple_coverability_encoding, "choice-cnf");
  assert.ok(quadrupleReport.quadruple_coverability_choice_variables > 0);
  assert.ok(quadrupleReport.quadruple_coverability_incompatibilities >= 0);

  const initialTripleOutput = join(directory, "initial-triple-summary.json");
  const initialTripleCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--lookahead-conflict-encoding=grouped-pb",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-triple-report=${triplePath}`,
    `--output-dir=${join(directory, "initial-triple")}`,
    `--report-output=${initialTripleOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(initialTripleCegar.status, 0, initialTripleCegar.stderr);
  const initialTripleReport = JSON.parse(readFileSync(initialTripleOutput, "utf8"));
  assert.ok(initialTripleReport.initial_triple_coverability_constraints >= 1);
  assert.equal(
    initialTripleReport.triple_coverability_constraint_count,
    initialTripleReport.initial_triple_coverability_constraints
  );
  const initialTripleProposal = JSON.parse(readFileSync(join(directory, "initial-triple", "outer-witness-0000.json"), "utf8"));
  assert.equal(
    initialTripleProposal.triple_coverability_constraints,
    initialTripleReport.initial_triple_coverability_constraints
  );

  const initialQuadrupleOutput = join(directory, "initial-quadruple-summary.json");
  const initialQuadrupleCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--lookahead-conflict-encoding=grouped-pb",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-quadruple-report=${quadruplePath}`,
    `--output-dir=${join(directory, "initial-quadruple")}`,
    `--report-output=${initialQuadrupleOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(initialQuadrupleCegar.status, 0, initialQuadrupleCegar.stderr);
  const initialQuadrupleReport = JSON.parse(readFileSync(initialQuadrupleOutput, "utf8"));
  assert.ok(initialQuadrupleReport.initial_quadruple_coverability_constraints >= 1);
  assert.equal(
    initialQuadrupleReport.quadruple_coverability_constraint_count,
    initialQuadrupleReport.initial_quadruple_coverability_constraints
  );
  const initialQuadrupleProposal = JSON.parse(readFileSync(join(directory, "initial-quadruple", "outer-witness-0000.json"), "utf8"));
  assert.equal(
    initialQuadrupleProposal.quadruple_coverability_constraints,
    initialQuadrupleReport.initial_quadruple_coverability_constraints
  );

  const lazyHigherOutput = join(directory, "lazy-higher-summary.json");
  const lazyHigherCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=lazy-higher",
    "--pair-encoding=witness-cnf",
    "--lookahead-conflict-encoding=grouped-pb",
    "--learn-pair-coverability=true",
    "--learn-triple-coverability=true",
    "--triple-max-cell-distance=6",
    "--triple-audit-limit=32",
    "--triple-orbit-limit=0",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-pair-report=${pairPath}`,
    `--initial-triple-report=${triplePath}`,
    `--initial-quadruple-report=${quadruplePath}`,
    `--output-dir=${join(directory, "lazy-higher")}`,
    `--report-output=${lazyHigherOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(lazyHigherCegar.status, 0, lazyHigherCegar.stderr);
  const lazyHigherReport = JSON.parse(readFileSync(lazyHigherOutput, "utf8"));
  assert.equal(lazyHigherReport.tuple_enforcement, "lazy-higher");
  const lazyHigherProposal = JSON.parse(readFileSync(join(directory, "lazy-higher", "outer-witness-0000.json"), "utf8"));
  assert.ok(lazyHigherProposal.pair_coverability_constraints > 0);
  assert.equal(lazyHigherProposal.triple_coverability_constraints, 0);
  assert.equal(lazyHigherProposal.quadruple_coverability_constraints, 0);

  const hybridHigherOutput = join(directory, "hybrid-higher-summary.json");
  const hybridHigherCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=hybrid-higher",
    "--encoded-triple-orbit-limit=1",
    "--encoded-triple-selection=max-blocked-combinations",
    "--z3-formula-cache=true",
    "--lookahead-conflict-encoding=grouped-pb",
    "--learn-triple-coverability=true",
    "--triple-max-cell-distance=6",
    "--triple-audit-limit=32",
    "--triple-orbit-limit=0",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-triple-report=${scoredTriplePath}`,
    `--initial-quadruple-report=${quadruplePath}`,
    `--output-dir=${join(directory, "hybrid-higher")}`,
    `--report-output=${hybridHigherOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(hybridHigherCegar.status, 0, hybridHigherCegar.stderr);
  const hybridHigherReport = JSON.parse(readFileSync(hybridHigherOutput, "utf8"));
  assert.equal(hybridHigherReport.tuple_enforcement, "hybrid-higher");
  assert.equal(hybridHigherReport.encoded_triple_orbit_limit, 1);
  assert.equal(hybridHigherReport.encoded_triple_selection, "max-blocked-combinations");
  assert.equal(hybridHigherReport.z3_formula_cache, true);
  assert.equal(hybridHigherReport.encoded_triple_coverability_orbits, 1);
  assert.ok(hybridHigherReport.encoded_triple_coverability_constraints > 0);
  assert.deepEqual(hybridHigherReport.trials[0].encoded_triple_orbit_scores, [17]);
  assert.ok(
    hybridHigherReport.encoded_triple_coverability_constraints
      <= hybridHigherReport.triple_coverability_constraint_count
  );
  const hybridHigherProposal = JSON.parse(readFileSync(join(directory, "hybrid-higher", "outer-witness-0000.json"), "utf8"));
  assert.equal(hybridHigherProposal.formula_cache_hit, false);
  assert.equal(
    hybridHigherProposal.triple_coverability_constraints,
    hybridHigherReport.encoded_triple_coverability_constraints
  );
  assert.equal(hybridHigherProposal.quadruple_coverability_constraints, 0);
  const persistedHybridTriples = JSON.parse(readFileSync(
    join(directory, "hybrid-higher", "triple-coverability.json"),
    "utf8"
  ));
  assert.ok(persistedHybridTriples.triple_orbit_scores[scoredTripleOrbitKey] >= 17);

  const hybridAllOutput = join(directory, "hybrid-all-summary.json");
  const hybridAllCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=hybrid-all",
    "--encoded-pair-orbit-limit=1",
    "--encoded-pair-selection=max-blocked-combinations",
    "--lookahead-conflict-encoding=grouped-pb",
    "--learn-pair-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-pair-report=${scoredPairPath}`,
    `--output-dir=${join(directory, "hybrid-all")}`,
    `--report-output=${hybridAllOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(hybridAllCegar.status, 0, hybridAllCegar.stderr);
  const hybridAllReport = JSON.parse(readFileSync(hybridAllOutput, "utf8"));
  assert.equal(hybridAllReport.tuple_enforcement, "hybrid-all");
  assert.equal(hybridAllReport.encoded_pair_coverability_orbits, 1);
  assert.deepEqual(hybridAllReport.encoded_pair_orbit_scores, [23]);
  assert.deepEqual(hybridAllReport.encoded_pair_orbit_keys, [scoredPairHighKey]);
  assert.ok(hybridAllReport.encoded_pair_coverability_constraints > 0);
  assert.ok(
    hybridAllReport.encoded_pair_coverability_constraints
      < hybridAllReport.pair_coverability_constraint_count
  );
  const hybridAllProposal = JSON.parse(readFileSync(join(directory, "hybrid-all", "outer-witness-0000.json"), "utf8"));
  assert.equal(
    hybridAllProposal.pair_coverability_constraints,
    hybridAllReport.encoded_pair_coverability_constraints
  );
  assert.equal(hybridAllProposal.triple_coverability_constraints, 0);
  const persistedHybridPairs = JSON.parse(readFileSync(
    join(directory, "hybrid-all", "pair-coverability.json"),
    "utf8"
  ));
  assert.equal(persistedHybridPairs.pair_orbit_scores[scoredPairHighKey], 23);

  const frequencyPairOutput = join(directory, "frequency-pair-summary.json");
  const frequencyPairCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=hybrid-all",
    "--encoded-pair-orbit-limit=1",
    "--encoded-pair-selection=frequency-impact",
    "--lookahead-conflict-encoding=grouped-pb",
    "--learn-pair-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-pair-report=${scoredPairPath}`,
    `--output-dir=${join(directory, "frequency-pair")}`,
    `--report-output=${frequencyPairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(frequencyPairCegar.status, 0, frequencyPairCegar.stderr);
  const frequencyPairReport = JSON.parse(readFileSync(frequencyPairOutput, "utf8"));
  assert.equal(frequencyPairReport.encoded_pair_selection, "frequency-impact");
  assert.deepEqual(frequencyPairReport.encoded_pair_orbit_keys, [scoredPairLowKey]);
  assert.ok(frequencyPairReport.encoded_pair_orbit_hits[0] >= 7);
  assert.equal(frequencyPairReport.pair_orbit_hits[scoredPairLowKey] >= 7, true);

  const weightedPairOutput = join(directory, "weighted-pair-summary.json");
  const weightedPairCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=hybrid-all",
    "--encoded-pair-orbit-limit=1",
    "--encoded-pair-selection=frequency-weighted-impact",
    "--lookahead-conflict-encoding=grouped-pb",
    "--learn-pair-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-pair-report=${scoredPairPath}`,
    `--output-dir=${join(directory, "weighted-pair")}`,
    `--report-output=${weightedPairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(weightedPairCegar.status, 0, weightedPairCegar.stderr);
  const weightedPairReport = JSON.parse(readFileSync(weightedPairOutput, "utf8"));
  assert.equal(weightedPairReport.encoded_pair_selection, "frequency-weighted-impact");
  assert.deepEqual(weightedPairReport.encoded_pair_orbit_keys, [scoredPairHighKey]);
  assert.ok(weightedPairReport.encoded_pair_orbit_scores[0] >= 23);

  const initialCellOutput = join(directory, "initial-cell-summary.json");
  const initialCellCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-cell-report=${cellPath}`,
    `--output-dir=${join(directory, "initial-cell")}`,
    `--report-output=${initialCellOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(initialCellCegar.status, 0, initialCellCegar.stderr);
  const initialCellReport = JSON.parse(readFileSync(initialCellOutput, "utf8"));
  assert.equal(initialCellReport.require_next_layer_coverability, false);
  assert.equal(initialCellReport.effective_next_layer_coverability, true);
  assert.ok(initialCellReport.initial_cell_coverability_constraints >= 1);
  const initialCellProposal = JSON.parse(readFileSync(join(directory, "initial-cell", "outer-witness-0000.json"), "utf8"));
  assert.equal(
    initialCellProposal.cell_coverability_constraints,
    initialCellReport.initial_cell_coverability_constraints
  );
  assert.equal(
    initialCellProposal.lookahead_target_cells,
    initialCellReport.initial_cell_coverability_constraints
  );

  const bootstrapPairOutput = join(directory, "bootstrap-pair-summary.json");
  const bootstrapPairCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--bootstrap-pair-distance=1",
    "--pair-encoding=witness-cnf",
    "--lookahead-conflict-encoding=grouped-pb",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--output-dir=${join(directory, "bootstrap-pair")}`,
    `--report-output=${bootstrapPairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(bootstrapPairCegar.status, 0, bootstrapPairCegar.stderr);
  const bootstrapPairReport = JSON.parse(readFileSync(bootstrapPairOutput, "utf8"));
  assert.equal(bootstrapPairReport.bootstrap_pair_distance, 1);
  assert.equal(bootstrapPairReport.initial_pair_coverability_constraints, 0);
  assert.ok(bootstrapPairReport.bootstrap_pair_coverability_constraints > 0);
  assert.equal(
    bootstrapPairReport.pair_coverability_constraint_count,
    bootstrapPairReport.bootstrap_pair_coverability_constraints
  );
  const bootstrapPairProposal = JSON.parse(readFileSync(join(directory, "bootstrap-pair", "outer-witness-0000.json"), "utf8"));
  assert.equal(
    bootstrapPairProposal.pair_coverability_constraints,
    bootstrapPairReport.bootstrap_pair_coverability_constraints
  );

  const positiveOutput = join(directory, "positive-summary.json");
  const positiveCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=2",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    "--random-seed=1",
    `--python=${python}`,
    `--output-dir=${join(directory, "positive")}`,
    `--report-output=${positiveOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(positiveCegar.status, 0, positiveCegar.stderr);
  const positiveReport = JSON.parse(readFileSync(positiveOutput, "utf8"));
  assert.equal(positiveReport.classification, "verified_inner_radius_witness");
  assert.equal(positiveReport.max_placements, 11);
  assert.equal(positiveReport.require_next_layer_coverability, true);
  assert.ok(positiveReport.radius_witness.placements > 0);
  assert.equal(positiveReport.warning, null);
  const positiveProposal = JSON.parse(readFileSync(join(directory, "positive", "outer-witness-0000.json"), "utf8"));
  assert.ok(positiveProposal.lookahead_target_cells > 0);
  assert.ok(positiveProposal.lookahead_raw_placements >= positiveProposal.lookahead_placements);
  assert.ok(positiveProposal.lookahead_conflicts > 0);
  const replayInput = join(directory, "replay-input");
  const replayOutput = join(directory, "replay-output.json");
  mkdirSync(replayInput);
  writeFileSync(join(replayInput, "outer-witness-0000.json"), `${JSON.stringify(positiveProposal)}\n`);
  const replayedRecurrence = spawnSync(process.execPath, [
    recurrenceReplay,
    "--id=p9-42947",
    "--layer=1",
    "--limit=1",
    `--input-root=${replayInput}`,
    `--base-pair-report=${pairPath}`,
    `--output=${replayOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(replayedRecurrence.status, 0, replayedRecurrence.stderr);
  const replayReport = JSON.parse(readFileSync(replayOutput, "utf8"));
  assert.equal(replayReport.verified_states, 1);
  assert.equal(replayReport.pair_defect_states + replayReport.pair_complete_states, 1);
  assert.ok(replayReport.pair_orbit_hits && typeof replayReport.pair_orbit_hits === "object");
  assert.match(replayReport.warning, /not a tiling, non-tiling, or aperiodicity certificate/);

  const batchCegarOutput = join(directory, "batch-cegar-summary.json");
  const batchCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=10",
    "--tuple-enforcement=lazy-all",
    "--learn-pair-coverability=true",
    "--pair-orbit-limit=0",
    "--pair-selection=max-blocked-combinations",
    "--z3-witness-batch-size=3",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--output-dir=${join(directory, "batch-cegar")}`,
    `--report-output=${batchCegarOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(batchCegar.status, 0, batchCegar.stderr);
  const batchCegarReport = JSON.parse(readFileSync(batchCegarOutput, "utf8"));
  assert.equal(batchCegarReport.z3_witness_batch_size, 3);
  assert.equal(batchCegarReport.classification, "verified_inner_radius_witness");
  assert.equal(batchCegarReport.trials.length, 2);
  assert.equal(batchCegarReport.trials[0].proposal_index, 0);
  assert.equal(batchCegarReport.trials[0].continuation_skipped, true);
  assert.ok(batchCegarReport.trials[0].pair_constraints_added > 0);
  assert.equal(batchCegarReport.trials[1].proposal_index, 1);
  assert.equal(batchCegarReport.trials[1].continuation_success, true);

  const interactiveCegarOutput = join(directory, "interactive-cegar-summary.json");
  const interactiveCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=3",
    "--min-placements=10",
    "--max-placements=10",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=lazy-higher",
    "--learn-pair-coverability=true",
    "--pair-orbit-limit=0",
    "--pair-selection=max-blocked-combinations",
    "--z3-interactive=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    "--lookahead-conflict-encoding=grouped-pb",
    `--python=${python}`,
    `--output-dir=${join(directory, "interactive-cegar")}`,
    `--report-output=${interactiveCegarOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(interactiveCegar.status, 0, interactiveCegar.stderr);
  const interactiveCegarReport = JSON.parse(readFileSync(interactiveCegarOutput, "utf8"));
  assert.equal(interactiveCegarReport.z3_interactive, true);
  assert.equal(interactiveCegarReport.trials.length, 3);
  assert.equal(interactiveCegarReport.trials[1].z3_interactive_clauses_applied, 3);
  assert.ok(interactiveCegarReport.trials[1].pair_constraints_added > 0);
  assert.equal(
    interactiveCegarReport.trials[2].z3_interactive_pairs_applied,
    interactiveCegarReport.trials[1].pair_constraints_added
  );
  assert.equal(
    interactiveCegarReport.trials[2].encoded_pair_coverability_constraints,
    interactiveCegarReport.trials[2].z3_interactive_pair_coverability_constraints
  );
  assert.equal(interactiveCegarReport.trials[2].z3_construction_milliseconds, 0);

  const pairOutput = join(directory, "pair-encoded.json");
  const pairEncoded = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    `--pair-coverability-report=${pairPath}`,
    `--output=${pairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(pairEncoded.status, 0, pairEncoded.stderr);
  const pairReport = JSON.parse(readFileSync(pairOutput, "utf8"));
  assert.equal(pairReport.z3_status, "sat");
  assert.ok(pairReport.pair_coverability_constraints > 0);
  assert.ok(pairReport.pair_coverability_terms > 0);

  const choicePairOutput = join(directory, "pair-choice-encoded.json");
  const choicePairEncoded = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    "--pair-encoding=choice-cnf",
    `--pair-coverability-report=${pairPath}`,
    `--output=${choicePairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(choicePairEncoded.status, 0, choicePairEncoded.stderr);
  const choicePairReport = JSON.parse(readFileSync(choicePairOutput, "utf8"));
  assert.equal(choicePairReport.z3_status, pairReport.z3_status);
  assert.equal(choicePairReport.pair_coverability_encoding, "choice-cnf");
  assert.equal(choicePairReport.pair_coverability_terms, 0);
  assert.ok(choicePairReport.pair_coverability_choice_variables > 0);
  assert.ok(choicePairReport.pair_coverability_incompatibilities >= 0);

  const witnessPairOutput = join(directory, "pair-witness-encoded.json");
  const witnessPairEncoded = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    "--pair-encoding=witness-cnf",
    `--pair-coverability-report=${pairPath}`,
    `--output=${witnessPairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(witnessPairEncoded.status, 0, witnessPairEncoded.stderr);
  const witnessPairReport = JSON.parse(readFileSync(witnessPairOutput, "utf8"));
  assert.equal(witnessPairReport.z3_status, pairReport.z3_status);
  assert.equal(witnessPairReport.pair_coverability_encoding, "witness-cnf");
  assert.ok(witnessPairReport.pair_coverability_terms > 0);
  assert.ok(witnessPairReport.pair_coverability_choice_variables > 0);
  assert.equal(witnessPairReport.pair_coverability_incompatibilities, 0);

  const formulaCache = join(directory, "pair-formula-cache.smt2");
  const cachedPairArguments = [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    "--pair-encoding=witness-cnf",
    `--pair-coverability-report=${pairPath}`,
    `--formula-cache=${formulaCache}`
  ];
  const cacheMissOutput = join(directory, "pair-cache-miss.json");
  const cacheMiss = spawnSync(python, [
    ...cachedPairArguments,
    `--output=${cacheMissOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(cacheMiss.status, 0, cacheMiss.stderr);
  const cacheMissReport = JSON.parse(readFileSync(cacheMissOutput, "utf8"));
  assert.equal(cacheMissReport.formula_cache_hit, false);
  const cacheHitOutput = join(directory, "pair-cache-hit.json");
  const cacheHit = spawnSync(python, [
    ...cachedPairArguments,
    "--random-seed=2",
    `--output=${cacheHitOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(cacheHit.status, 0, cacheHit.stderr);
  const cacheHitReport = JSON.parse(readFileSync(cacheHitOutput, "utf8"));
  assert.equal(cacheHitReport.z3_status, cacheMissReport.z3_status);
  assert.equal(cacheHitReport.formula_cache_hit, true);
  assert.equal(cacheHitReport.formula_cache_pairs_reused, pairReport.pair_coverability_constraints);
  assert.equal(cacheHitReport.pair_coverability_terms, cacheMissReport.pair_coverability_terms);
  assert.equal(cacheHitReport.pair_coverability_choice_variables, cacheMissReport.pair_coverability_choice_variables);
  const augmentedPairPath = join(directory, "pair-coverability-augmented.json");
  writeFileSync(augmentedPairPath, `${JSON.stringify({
    pairs: [
      [secondRing[0], secondRing.at(-1)],
      [secondRing[1], secondRing.at(-1)]
    ]
  })}\n`);
  const augmentedCacheOutput = join(directory, "pair-cache-augmented.json");
  const augmentedCache = spawnSync(python, [
    ...cachedPairArguments.filter(argument => !argument.startsWith("--pair-coverability-report=")),
    `--pair-coverability-report=${augmentedPairPath}`,
    `--output=${augmentedCacheOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(augmentedCache.status, 0, augmentedCache.stderr);
  const augmentedCacheReport = JSON.parse(readFileSync(augmentedCacheOutput, "utf8"));
  assert.equal(augmentedCacheReport.formula_cache_hit, true);
  assert.equal(augmentedCacheReport.formula_cache_pairs_reused, 1);
  assert.equal(augmentedCacheReport.formula_cache_pairs_added, 1);
  const augmentedCacheReplayOutput = join(directory, "pair-cache-augmented-replay.json");
  const augmentedCacheReplay = spawnSync(python, [
    ...cachedPairArguments.filter(argument => !argument.startsWith("--pair-coverability-report=")),
    `--pair-coverability-report=${augmentedPairPath}`,
    `--output=${augmentedCacheReplayOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(augmentedCacheReplay.status, 0, augmentedCacheReplay.stderr);
  const augmentedCacheReplayReport = JSON.parse(readFileSync(augmentedCacheReplayOutput, "utf8"));
  assert.equal(augmentedCacheReplayReport.formula_cache_hit, true);
  assert.equal(augmentedCacheReplayReport.formula_cache_pairs_reused, 2);
  assert.equal(augmentedCacheReplayReport.formula_cache_pairs_added, 0);
} finally {
  rmSync(directory, { recursive: true, force: true });
}

console.log("polycube-corona-z3-cegar regressions passed");
