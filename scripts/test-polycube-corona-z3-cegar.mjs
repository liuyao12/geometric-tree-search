#!/usr/bin/env node

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { polycubeKey } from "../assets/polycube-enumerator.js";
import { enumeratePolycubeCoronaPlacements } from "../assets/polycube-corona-search.js";

const python = process.env.PYTHON ?? "python3";
const solver = fileURLToPath(new URL("./solve_polycube_corona_z3.py", import.meta.url));
const cegar = fileURLToPath(new URL("./screen-polycube-corona-z3-cegar.mjs", import.meta.url));
const cegarSource = readFileSync(cegar, "utf8");
assert.match(cegarSource, /Keep resumable artifacts synchronized[\s\S]*?writeFileSync\(clausePath[\s\S]*?writeFileSync\(cellPath[\s\S]*?writeFileSync\(pairPath[\s\S]*?writeFileSync\(triplePath[\s\S]*?writeFileSync\(quadruplePath/);
assert.match(cegarSource, /const tripleAuditLimit = integerArg\("triple-audit-limit", tripleOrbitLimit \|\| 1, 1\)/);
assert.match(cegarSource, /limit: tripleAuditLimit \+ 1[\s\S]*?tripleAuditTruncated = incompatibleTripleAudit\.length > tripleAuditLimit/);
assert.match(cegarSource, /triple_audit_truncated: tripleAuditTruncated/);
assert.match(cegarSource, /--tuple-enforcement must be encoded, hybrid-higher, lazy-higher, or lazy-all/);
assert.match(cegarSource, /if \(pairConstraints\.length && encodePairCoverability\)/);
assert.match(cegarSource, /const encodedTripleSelection = selectEncodedTriples\(\)/);
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
  const triplePath = join(directory, "triple-coverability.json");
  writeFileSync(triplePath, `${JSON.stringify({
    triples: [[secondRing[0], secondRing[1], secondRing.at(-1)]]
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
    "--lookahead-conflict-encoding=grouped-pb",
    "--learn-triple-coverability=true",
    "--triple-max-cell-distance=6",
    "--triple-audit-limit=32",
    "--triple-orbit-limit=0",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-triple-report=${triplePath}`,
    `--initial-quadruple-report=${quadruplePath}`,
    `--output-dir=${join(directory, "hybrid-higher")}`,
    `--report-output=${hybridHigherOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(hybridHigherCegar.status, 0, hybridHigherCegar.stderr);
  const hybridHigherReport = JSON.parse(readFileSync(hybridHigherOutput, "utf8"));
  assert.equal(hybridHigherReport.tuple_enforcement, "hybrid-higher");
  assert.equal(hybridHigherReport.encoded_triple_orbit_limit, 1);
  assert.equal(hybridHigherReport.encoded_triple_coverability_orbits, 1);
  assert.ok(hybridHigherReport.encoded_triple_coverability_constraints > 0);
  assert.ok(
    hybridHigherReport.encoded_triple_coverability_constraints
      <= hybridHigherReport.triple_coverability_constraint_count
  );
  const hybridHigherProposal = JSON.parse(readFileSync(join(directory, "hybrid-higher", "outer-witness-0000.json"), "utf8"));
  assert.equal(
    hybridHigherProposal.triple_coverability_constraints,
    hybridHigherReport.encoded_triple_coverability_constraints
  );
  assert.equal(hybridHigherProposal.quadruple_coverability_constraints, 0);

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
} finally {
  rmSync(directory, { recursive: true, force: true });
}

console.log("polycube-corona-z3-cegar regressions passed");
