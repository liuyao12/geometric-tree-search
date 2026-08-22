#!/usr/bin/env node

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  retainSuccessfulFeedbackBatches,
  selectFeedbackBatch
} from "../assets/feedback-batch-policy.js";
import { polycubeKey } from "../assets/polycube-enumerator.js";
import {
  enumeratePolycubeCoronaPlacements,
  polycubeCellPairOrbitKeys,
  polycubeCellTripleOrbitKeys
} from "../assets/polycube-corona-search.js";

const python = process.env.PYTHON ?? "python3";
const solver = fileURLToPath(new URL("./solve_polycube_corona_z3.py", import.meta.url));
const cegar = fileURLToPath(new URL("./screen-polycube-corona-z3-cegar.mjs", import.meta.url));
const clauseReplay = fileURLToPath(new URL("./verify-polycube-corona-clause-report.mjs", import.meta.url));
const recurrenceReplay = fileURLToPath(new URL("./replay-polycube-pair-recurrence.mjs", import.meta.url));
const cegarSource = readFileSync(cegar, "utf8");
const retainedFeedback = retainSuccessfulFeedbackBatches({
  current: { clauses: 6, cells: 4 },
  attempted: { clauses: 6, cells: 4 },
  applied: { clauses: 2, cells: 1 },
  z3Status: "sat",
  backoffCount: 2
});
assert.deepEqual(retainedFeedback, {
  next: { clauses: 2, cells: 1 },
  reduced: true
});
assert.deepEqual(selectFeedbackBatch([1, 2, 3, 4], retainedFeedback.next.clauses), [1, 2]);
assert.deepEqual(selectFeedbackBatch([1, 2, 3], retainedFeedback.next.cells), [1]);
assert.deepEqual(
  retainSuccessfulFeedbackBatches({
    current: retainedFeedback.next,
    attempted: { clauses: 1, cells: 1 },
    applied: { clauses: 1, cells: 1 },
    z3Status: "sat",
    backoffCount: 0
  }),
  { next: { clauses: 2, cells: 1 }, reduced: false },
  "a short pending tail must not shrink the retained policy"
);
assert.deepEqual(
  retainSuccessfulFeedbackBatches({
    current: { clauses: 6, cells: 4 },
    attempted: { clauses: 6, cells: 4 },
    applied: { clauses: 0, cells: 0 },
    z3Status: "unknown",
    backoffCount: 2
  }),
  { next: { clauses: 6, cells: 4 }, reduced: false },
  "a fully rolled-back timeout must not become the next policy"
);
assert.match(cegarSource, /Keep resumable artifacts synchronized[\s\S]*?writeFileSync\(clausePath[\s\S]*?writeFileSync\(cellPath[\s\S]*?writeFileSync\(pairPath[\s\S]*?writeFileSync\(triplePath[\s\S]*?writeFileSync\(quadruplePath/);
assert.match(cegarSource, /const tripleAuditLimit = integerArg\("triple-audit-limit", tripleOrbitLimit \|\| 1, 1\)/);
assert.match(cegarSource, /limit: tripleAuditLimit \+ 1[\s\S]*?tripleAuditTruncated = incompatibleTripleAudit\.length > tripleAuditLimit/);
assert.match(cegarSource, /triple_audit_truncated: tripleAuditTruncated/);
assert.match(cegarSource, /--tuple-enforcement must be encoded, hybrid-higher, hybrid-all, lazy-higher, or lazy-all/);
assert.match(cegarSource, /--encoded-pair-selection must be first, recent, max-blocked-combinations, frequency-impact, frequency-weighted-impact, historical-cover, historical-core, or recent-defect-cover/);
assert.match(cegarSource, /--recent-defect-orbit-limit is only valid with --encoded-pair-selection=recent-defect-cover/);
assert.match(cegarSource, /--pair-soft-minimum is not yet supported with --z3-interactive=true/);
assert.match(cegarSource, /--pair-soft-minimum and --pair-soft-orbit-minimum are mutually exclusive/);
assert.match(cegarSource, /--encoded-triple-selection must be first, recent, or max-blocked-combinations/);
assert.match(cegarSource, /triple_orbit_scores: serializedTripleOrbitScores\(\)/);
assert.match(cegarSource, /--formula-cache=\$\{formulaCachePath\}/);
assert.match(cegarSource, /--max-witnesses=\$\{z3WitnessBatchSize\}/);
assert.match(cegarSource, /const processSatProposal =/);
assert.match(cegarSource, /solverArguments\.push\("--interactive-jsonl"\)/);
assert.match(cegarSource, /solverArguments\.push\("--interactive-replace-pairs"\)/);
assert.match(cegarSource, /--z3-timeout-retry-ms requires --z3-interactive=true/);
assert.match(cegarSource, /firstResult\.z3_status === "unknown"[\s\S]*?timeoutMs: z3TimeoutRetryMs[\s\S]*?clauses: \[\][\s\S]*?cells: \[\]/);
assert.match(cegarSource, /--feedback-timeout-backoff requires --z3-interactive=true/);
assert.match(cegarSource, /--z3-formula-cache-path requires --z3-formula-cache=true/);
assert.match(cegarSource, /z3FormulaCachePathArgument[\s\S]*?formulaCachePath/);
assert.match(cegarSource, /type: "rollback"[\s\S]*?Math\.ceil\(clausesToApply\.length \/ 2\)[\s\S]*?Math\.ceil\(cellsToApply\.length \/ 2\)/);
assert.match(cegarSource, /replace_pairs: encodedPairs\.constraints/);
assert.match(cegarSource, /interactive_clauses_applied/);
assert.match(cegarSource, /if \(encodedPairs\.constraints\.length\)/);
assert.match(cegarSource, /--pair-coverability-report=\$\{encodedPairPath\}/);
assert.match(cegarSource, /const encodedTriples = selectEncodedTriples\(\)/);
assert.match(cegarSource, /--triple-coverability-report=\$\{encodedTriplePath\}/);
assert.match(cegarSource, /if \(tupleEnforcement !== "encoded"\)[\s\S]*?continuation_skipped: true[\s\S]*?const continuation = searchPolycubeCorona/);
assert.match(
  cegarSource,
  /const immediateObstructions = continuation\.fixed_obstruction_nogoods[\s\S]*?learnedClauses\.reduce[\s\S]*?for \(const cellObstruction of cellObstructions\)/,
  "CEGAR must learn every immediate dead-cell obstruction returned by one exact continuation"
);
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
  assert.ok(
    learnedCellReport.cell_coverability_constraint_count > 1,
    "one exact continuation should promote every immediate dead cell"
  );
  assert.equal(learnedCellReport.trials[0].obstruction_kind, "immediate_dead_target");
  assert.equal(
    learnedCellReport.trials[0].cell_constraints_added,
    learnedCellReport.cell_coverability_constraint_count
  );
  assert.equal(
    learnedCellReport.trials[0].dead_target_cells.length,
    learnedCellReport.cell_coverability_constraint_count
  );
  assert.equal(learnedCellReport.trials[1].z3_status, "unsat");
  const learnedCellClauseReplayOutput = join(directory, "learned-cell-clause-replay.json");
  const learnedCellClauseReplay = spawnSync(process.execPath, [
    clauseReplay,
    "--id=p10-052670",
    "--layer=2",
    `--clause-report=${join(directory, "learned-cell", "forbidden-clauses.json")}`,
    "--node-limit=100000",
    "--time-ms=10000",
    `--output=${learnedCellClauseReplayOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(learnedCellClauseReplay.status, 0, learnedCellClauseReplay.stderr);
  const learnedCellClauseReplayReport = JSON.parse(readFileSync(learnedCellClauseReplayOutput, "utf8"));
  assert.equal(learnedCellClauseReplayReport.classification, "verified");
  assert.equal(learnedCellClauseReplayReport.verified_clauses, learnedCellReport.learned_clause_count);
  const learnedCellProposal = JSON.parse(readFileSync(join(directory, "learned-cell", "outer-witness-0001.json"), "utf8"));
  assert.equal(learnedCellProposal.require_next_layer_coverability, false);
  assert.equal(
    learnedCellProposal.cell_coverability_constraints,
    learnedCellReport.cell_coverability_constraint_count
  );
  assert.equal(
    learnedCellProposal.lookahead_target_cells,
    learnedCellReport.cell_coverability_constraint_count
  );

  const interactiveLearnedCellOutput = join(directory, "interactive-learned-cell-summary.json");
  const interactiveLearnedCellCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p10-052670",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=2",
    "--learn-cell-coverability=true",
    "--tuple-enforcement=lazy-all",
    "--z3-interactive=true",
    "--lookahead-conflict-encoding=grouped-pb",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--output-dir=${join(directory, "interactive-learned-cell")}`,
    `--report-output=${interactiveLearnedCellOutput}`
  ], { encoding: "utf8", timeout: 90_000 });
  assert.equal(interactiveLearnedCellCegar.status, 0, interactiveLearnedCellCegar.stderr);
  const interactiveLearnedCellReport = JSON.parse(readFileSync(interactiveLearnedCellOutput, "utf8"));
  assert.equal(interactiveLearnedCellReport.classification, "certified_non_tiler");
  assert.equal(interactiveLearnedCellReport.z3_interactive, true);
  assert.ok(interactiveLearnedCellReport.trials[0].cell_constraints_added > 1);
  assert.equal(
    interactiveLearnedCellReport.trials[1].z3_interactive_cells_applied,
    interactiveLearnedCellReport.trials[0].cell_constraints_added
  );
  assert.equal(
    interactiveLearnedCellReport.trials[1].z3_interactive_cell_coverability_constraints,
    interactiveLearnedCellReport.trials[0].cell_constraints_added
  );
  assert.equal(interactiveLearnedCellReport.trials[1].z3_construction_milliseconds, 0);

  const interactiveTimeoutRetryOutput = join(directory, "interactive-timeout-retry-summary.json");
  const interactiveTimeoutRetry = spawnSync(process.execPath, [
    cegar,
    "--id=p10-052670",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--tuple-enforcement=lazy-all",
    "--z3-interactive=true",
    "--lookahead-conflict-encoding=grouped-pb",
    "--z3-timeout-ms=1",
    "--z3-timeout-retry-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--output-dir=${join(directory, "interactive-timeout-retry")}`,
    `--report-output=${interactiveTimeoutRetryOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(interactiveTimeoutRetry.status, 0, interactiveTimeoutRetry.stderr);
  const interactiveTimeoutRetryReport = JSON.parse(readFileSync(interactiveTimeoutRetryOutput, "utf8"));
  assert.equal(interactiveTimeoutRetryReport.z3_timeout_ms, 1);
  assert.equal(interactiveTimeoutRetryReport.z3_timeout_retry_ms, 10000);
  assert.equal(interactiveTimeoutRetryReport.trials[0].z3_status, "sat");
  assert.equal(interactiveTimeoutRetryReport.trials[0].z3_timeout_retry_count, 1);
  assert.deepEqual(interactiveTimeoutRetryReport.trials[0].z3_timeout_schedule_ms, [1, 10000]);
  assert.ok(interactiveTimeoutRetryReport.trials[0].z3_initial_check_milliseconds >= 1);
  assert.ok(interactiveTimeoutRetryReport.trials[0].z3_retry_check_milliseconds >= 1);
  assert.equal(
    interactiveTimeoutRetryReport.trials[0].z3_check_milliseconds,
    interactiveTimeoutRetryReport.trials[0].z3_initial_check_milliseconds
      + interactiveTimeoutRetryReport.trials[0].z3_retry_check_milliseconds
  );

  const batchedCellFeedbackOutput = join(directory, "batched-cell-feedback-summary.json");
  const batchedCellFeedbackDirectory = join(directory, "batched-cell-feedback");
  const batchedCellFeedback = spawnSync(process.execPath, [
    cegar,
    "--id=p10-052670",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=2",
    "--learn-cell-coverability=true",
    "--cell-feedback-batch=2",
    "--tuple-enforcement=lazy-all",
    "--z3-interactive=true",
    "--lookahead-conflict-encoding=grouped-pb",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--output-dir=${batchedCellFeedbackDirectory}`,
    `--report-output=${batchedCellFeedbackOutput}`
  ], { encoding: "utf8", timeout: 90_000 });
  assert.equal(batchedCellFeedback.status, 0, batchedCellFeedback.stderr);
  const batchedCellFeedbackReport = JSON.parse(readFileSync(batchedCellFeedbackOutput, "utf8"));
  assert.equal(batchedCellFeedbackReport.classification, "certified_non_tiler");
  assert.equal(batchedCellFeedbackReport.cell_feedback_batch, 2);
  assert.ok(batchedCellFeedbackReport.cell_coverability_constraint_count > 2);
  assert.equal(batchedCellFeedbackReport.trials[1].z3_interactive_cells_applied, 2);
  assert.equal(batchedCellFeedbackReport.z3_interactive_cell_constraints_applied, 2);
  assert.equal(
    batchedCellFeedbackReport.z3_interactive_cell_constraints_deferred,
    batchedCellFeedbackReport.cell_coverability_constraint_count - 2
  );
  const appliedCellFeedback = JSON.parse(readFileSync(
    join(batchedCellFeedbackDirectory, "applied-cell-coverability.json"),
    "utf8"
  ));
  assert.equal(appliedCellFeedback.cells.length, 2);

  const resumedCellFeedbackOutput = join(directory, "resumed-cell-feedback-summary.json");
  const resumedCellFeedbackDirectory = join(directory, "resumed-cell-feedback");
  const resumedCellFeedback = spawnSync(process.execPath, [
    cegar,
    "--id=p10-052670",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--learn-cell-coverability=true",
    "--cell-feedback-batch=2",
    "--tuple-enforcement=lazy-all",
    "--z3-interactive=true",
    "--lookahead-conflict-encoding=grouped-pb",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--initial-cell-report=${join(batchedCellFeedbackDirectory, "applied-cell-coverability.json")}`,
    `--initial-deferred-cell-report=${join(batchedCellFeedbackDirectory, "cell-coverability.json")}`,
    `--python=${python}`,
    `--output-dir=${resumedCellFeedbackDirectory}`,
    `--report-output=${resumedCellFeedbackOutput}`
  ], { encoding: "utf8", timeout: 90_000 });
  assert.equal(resumedCellFeedback.status, 0, resumedCellFeedback.stderr);
  const resumedCellFeedbackReport = JSON.parse(readFileSync(resumedCellFeedbackOutput, "utf8"));
  assert.equal(resumedCellFeedbackReport.initial_cell_coverability_constraints, 2);
  assert.equal(
    resumedCellFeedbackReport.initial_deferred_cell_coverability_constraints,
    batchedCellFeedbackReport.cell_coverability_constraint_count - 2
  );
  assert.equal(resumedCellFeedbackReport.trials[0].z3_interactive_cells_applied, 2);
  assert.equal(resumedCellFeedbackReport.z3_interactive_cell_constraints_applied, 4);
  assert.equal(
    resumedCellFeedbackReport.z3_interactive_cell_constraints_deferred,
    batchedCellFeedbackReport.cell_coverability_constraint_count - 4
  );
  const resumedAppliedCellFeedback = JSON.parse(readFileSync(
    join(resumedCellFeedbackDirectory, "applied-cell-coverability.json"),
    "utf8"
  ));
  assert.deepEqual(
    resumedAppliedCellFeedback.cells,
    batchedCellFeedbackReport.cell_coverability_cells.slice(0, 4)
  );

  const batchedClauseFeedbackOutput = join(directory, "batched-clause-feedback-summary.json");
  const batchedClauseFeedbackDirectory = join(directory, "batched-clause-feedback");
  const batchedClauseFeedback = spawnSync(process.execPath, [
    cegar,
    "--id=p10-052670",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=2",
    "--clause-feedback-batch=2",
    "--tuple-enforcement=lazy-all",
    "--z3-interactive=true",
    "--lookahead-conflict-encoding=grouped-pb",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--output-dir=${batchedClauseFeedbackDirectory}`,
    `--report-output=${batchedClauseFeedbackOutput}`
  ], { encoding: "utf8", timeout: 90_000 });
  assert.equal(batchedClauseFeedback.status, 0, batchedClauseFeedback.stderr);
  const batchedClauseFeedbackReport = JSON.parse(readFileSync(batchedClauseFeedbackOutput, "utf8"));
  assert.equal(batchedClauseFeedbackReport.classification, "certified_non_tiler");
  assert.equal(batchedClauseFeedbackReport.clause_feedback_batch, 2);
  assert.ok(batchedClauseFeedbackReport.learned_clause_count > 2);
  assert.equal(batchedClauseFeedbackReport.trials[1].z3_interactive_clauses_applied, 2);
  assert.equal(batchedClauseFeedbackReport.z3_interactive_clauses_applied, 2);
  assert.equal(
    batchedClauseFeedbackReport.z3_interactive_clauses_deferred,
    batchedClauseFeedbackReport.learned_clause_count - 2
  );
  const appliedClauseFeedback = JSON.parse(readFileSync(
    join(batchedClauseFeedbackDirectory, "applied-forbidden-clauses.json"),
    "utf8"
  ));
  assert.equal(appliedClauseFeedback.clauses.length, 2);

  const resumedClauseFeedbackOutput = join(directory, "resumed-clause-feedback-summary.json");
  const resumedClauseFeedbackDirectory = join(directory, "resumed-clause-feedback");
  const resumedClauseFeedback = spawnSync(process.execPath, [
    cegar,
    "--id=p10-052670",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--clause-feedback-batch=2",
    "--tuple-enforcement=lazy-all",
    "--z3-interactive=true",
    "--lookahead-conflict-encoding=grouped-pb",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--initial-clause-report=${join(batchedClauseFeedbackDirectory, "applied-forbidden-clauses.json")}`,
    `--initial-deferred-clause-report=${join(batchedClauseFeedbackDirectory, "forbidden-clauses.json")}`,
    `--python=${python}`,
    `--output-dir=${resumedClauseFeedbackDirectory}`,
    `--report-output=${resumedClauseFeedbackOutput}`
  ], { encoding: "utf8", timeout: 90_000 });
  assert.equal(resumedClauseFeedback.status, 0, resumedClauseFeedback.stderr);
  const resumedClauseFeedbackReport = JSON.parse(readFileSync(resumedClauseFeedbackOutput, "utf8"));
  assert.equal(resumedClauseFeedbackReport.initial_applied_clause_count, 2);
  assert.equal(
    resumedClauseFeedbackReport.initial_deferred_clause_count,
    batchedClauseFeedbackReport.learned_clause_count - 2
  );
  assert.equal(resumedClauseFeedbackReport.trials[0].z3_interactive_clauses_applied, 2);
  assert.equal(resumedClauseFeedbackReport.z3_interactive_clauses_applied, 4);
  assert.equal(
    resumedClauseFeedbackReport.z3_interactive_clauses_deferred,
    batchedClauseFeedbackReport.learned_clause_count - 4
  );
  const resumedAppliedClauseFeedback = JSON.parse(readFileSync(
    join(resumedClauseFeedbackDirectory, "applied-forbidden-clauses.json"),
    "utf8"
  ));
  assert.deepEqual(
    resumedAppliedClauseFeedback.clauses,
    batchedClauseFeedbackReport.learned_clauses.slice(0, 4)
  );

  const rolledBackFeedbackOutput = join(directory, "rolled-back-feedback-summary.json");
  const rolledBackFeedbackDirectory = join(directory, "rolled-back-feedback");
  const rolledBackFeedback = spawnSync(process.execPath, [
    cegar,
    "--id=p10-052670",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--learn-cell-coverability=true",
    "--clause-feedback-batch=4",
    "--cell-feedback-batch=4",
    "--feedback-timeout-backoff=true",
    "--feedback-min-clause-batch=1",
    "--feedback-min-cell-batch=1",
    "--tuple-enforcement=lazy-all",
    "--z3-interactive=true",
    "--lookahead-conflict-encoding=grouped-pb",
    "--z3-timeout-ms=1",
    "--z3-timeout-retry-ms=2",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--initial-clause-report=${join(batchedClauseFeedbackDirectory, "applied-forbidden-clauses.json")}`,
    `--initial-deferred-clause-report=${join(batchedClauseFeedbackDirectory, "forbidden-clauses.json")}`,
    `--initial-cell-report=${join(batchedCellFeedbackDirectory, "applied-cell-coverability.json")}`,
    `--initial-deferred-cell-report=${join(batchedCellFeedbackDirectory, "cell-coverability.json")}`,
    `--python=${python}`,
    `--output-dir=${rolledBackFeedbackDirectory}`,
    `--report-output=${rolledBackFeedbackOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(rolledBackFeedback.status, 0, rolledBackFeedback.stderr);
  const rolledBackFeedbackReport = JSON.parse(readFileSync(rolledBackFeedbackOutput, "utf8"));
  assert.equal(rolledBackFeedbackReport.classification, "z3_incomplete");
  assert.equal(rolledBackFeedbackReport.feedback_timeout_backoff, true);
  assert.equal(rolledBackFeedbackReport.trials[0].z3_feedback_backoff_count, 2);
  assert.equal(rolledBackFeedbackReport.trials[0].z3_feedback_rolled_back, true);
  assert.deepEqual(
    rolledBackFeedbackReport.trials[0].z3_feedback_attempts.map(attempt => [
      attempt.clauses,
      attempt.cells,
      attempt.z3_status
    ]),
    [[4, 4, "unknown"], [2, 2, "unknown"], [1, 1, "unknown"]]
  );
  assert.equal(rolledBackFeedbackReport.trials[0].z3_interactive_clauses_applied, 0);
  assert.equal(rolledBackFeedbackReport.trials[0].z3_interactive_cells_applied, 0);
  assert.deepEqual(rolledBackFeedbackReport.trials[0].z3_feedback_batch_before, { clauses: 4, cells: 4 });
  assert.deepEqual(rolledBackFeedbackReport.trials[0].z3_feedback_batch_after, { clauses: 4, cells: 4 });
  assert.equal(rolledBackFeedbackReport.trials[0].z3_feedback_batch_sticky_reduction, false);
  assert.equal(rolledBackFeedbackReport.effective_clause_feedback_batch, 4);
  assert.equal(rolledBackFeedbackReport.effective_cell_feedback_batch, 4);
  assert.equal(rolledBackFeedbackReport.feedback_sticky_reduction_count, 0);
  assert.equal(rolledBackFeedbackReport.z3_interactive_clauses_applied, 2);
  assert.equal(rolledBackFeedbackReport.z3_interactive_cell_constraints_applied, 2);
  assert.equal(
    JSON.parse(readFileSync(join(rolledBackFeedbackDirectory, "applied-forbidden-clauses.json"), "utf8")).clauses.length,
    2
  );
  assert.equal(
    JSON.parse(readFileSync(join(rolledBackFeedbackDirectory, "applied-cell-coverability.json"), "utf8")).cells.length,
    2
  );

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
  for (let left = 0; left < secondRing.length && scoredPairsByOrbit.size < 3; left += 1) {
    for (let right = left + 1; right < secondRing.length && scoredPairsByOrbit.size < 3; right += 1) {
      const pair = [secondRing[left], secondRing[right]];
      scoredPairsByOrbit.set(pairOrbitKey(pair), pair);
    }
  }
  assert.equal(scoredPairsByOrbit.size, 3);
  const [scoredPairLow, scoredPairHigh, scoredPairThird] = [...scoredPairsByOrbit.values()];
  const scoredPairLowKey = pairOrbitKey(scoredPairLow);
  const scoredPairHighKey = pairOrbitKey(scoredPairHigh);
  const scoredPairThirdKey = pairOrbitKey(scoredPairThird);
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
    },
    pair_defect_orbit_sets: [
      [scoredPairLowKey],
      [scoredPairLowKey, scoredPairHighKey]
    ]
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
  const softPairOutput = join(directory, "soft-pair-worker.json");
  const softPairWorker = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    `--pair-coverability-report=${scoredPairPath}`,
    "--pair-encoding=witness-cnf",
    "--pair-soft-minimum=1",
    `--output=${softPairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(softPairWorker.status, 0, softPairWorker.stderr);
  const softPairWorkerReport = JSON.parse(readFileSync(softPairOutput, "utf8"));
  assert.equal(softPairWorkerReport.z3_status, "sat");
  assert.equal(softPairWorkerReport.pair_soft_minimum, 1);
  assert.ok(softPairWorkerReport.pair_soft_satisfied >= 1);
  const softOrbitPairPath = join(directory, "soft-orbit-pair-coverability.json");
  writeFileSync(softOrbitPairPath, `${JSON.stringify({
    pairs: [scoredPairLow, scoredPairHigh],
    orbit_groups: [[scoredPairLow], [scoredPairHigh]]
  })}\n`);
  const softOrbitPairOutput = join(directory, "soft-orbit-pair-worker.json");
  const softOrbitPairWorker = spawnSync(python, [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    "--require-next-layer-coverability",
    `--pair-coverability-report=${softOrbitPairPath}`,
    "--pair-encoding=witness-cnf",
    "--pair-soft-orbit-minimum=1",
    `--output=${softOrbitPairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(softOrbitPairWorker.status, 0, softOrbitPairWorker.stderr);
  const softOrbitPairWorkerReport = JSON.parse(readFileSync(softOrbitPairOutput, "utf8"));
  assert.equal(softOrbitPairWorkerReport.z3_status, "sat");
  assert.equal(softOrbitPairWorkerReport.pair_soft_orbit_minimum, 1);
  assert.ok(softOrbitPairWorkerReport.pair_soft_orbits_satisfied >= 1);
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

  const softHybridOutput = join(directory, "soft-hybrid-summary.json");
  const softHybridCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=hybrid-all",
    "--encoded-pair-orbit-limit=2",
    "--pair-soft-minimum=1",
    "--lookahead-conflict-encoding=grouped-pb",
    "--pair-encoding=witness-cnf",
    "--learn-pair-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-pair-report=${scoredPairPath}`,
    `--output-dir=${join(directory, "soft-hybrid")}`,
    `--report-output=${softHybridOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(softHybridCegar.status, 0, softHybridCegar.stderr);
  const softHybridReport = JSON.parse(readFileSync(softHybridOutput, "utf8"));
  assert.equal(softHybridReport.pair_soft_minimum, 1);
  assert.equal(softHybridReport.trials[0].z3_status, "sat");
  assert.ok(softHybridReport.trials[0].z3_pair_soft_satisfied >= 1);
  assert.notEqual(softHybridReport.classification, "certified_non_tiler");

  const softOrbitHybridOutput = join(directory, "soft-orbit-hybrid-summary.json");
  const softOrbitHybridCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=hybrid-all",
    "--encoded-pair-orbit-limit=2",
    "--pair-soft-orbit-minimum=1",
    "--lookahead-conflict-encoding=grouped-pb",
    "--pair-encoding=witness-cnf",
    "--learn-pair-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-pair-report=${scoredPairPath}`,
    `--output-dir=${join(directory, "soft-orbit-hybrid")}`,
    `--report-output=${softOrbitHybridOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(softOrbitHybridCegar.status, 0, softOrbitHybridCegar.stderr);
  const softOrbitHybridReport = JSON.parse(readFileSync(softOrbitHybridOutput, "utf8"));
  assert.equal(softOrbitHybridReport.pair_soft_orbit_minimum, 1);
  assert.equal(softOrbitHybridReport.trials[0].z3_status, "sat");
  assert.ok(softOrbitHybridReport.trials[0].z3_pair_soft_orbits_satisfied >= 1);
  assert.notEqual(softOrbitHybridReport.classification, "certified_non_tiler");

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

  const coverPairOutput = join(directory, "cover-pair-summary.json");
  const coverPairCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=hybrid-all",
    "--encoded-pair-orbit-limit=1",
    "--encoded-pair-selection=historical-cover",
    "--lookahead-conflict-encoding=grouped-pb",
    "--learn-pair-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-pair-report=${scoredPairPath}`,
    `--output-dir=${join(directory, "cover-pair")}`,
    `--report-output=${coverPairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(coverPairCegar.status, 0, coverPairCegar.stderr);
  const coverPairReport = JSON.parse(readFileSync(coverPairOutput, "utf8"));
  assert.equal(coverPairReport.encoded_pair_selection, "historical-cover");
  assert.deepEqual(coverPairReport.encoded_pair_orbit_keys, [scoredPairLowKey]);
  assert.ok(coverPairReport.encoded_pair_historical_sets_covered >= 2);
  assert.ok(coverPairReport.pair_defect_orbit_set_count >= 2);

  const corePairPath = join(directory, "core-pair-coverability.json");
  writeFileSync(corePairPath, `${JSON.stringify({
    pairs: [scoredPairLow, scoredPairHigh, scoredPairThird],
    pair_orbit_scores: {
      [scoredPairLowKey]: 5,
      [scoredPairHighKey]: 23,
      [scoredPairThirdKey]: 1
    },
    pair_orbit_hits: {
      [scoredPairLowKey]: 1,
      [scoredPairHighKey]: 2,
      [scoredPairThirdKey]: 1
    },
    pair_defect_orbit_sets: [
      [scoredPairLowKey],
      [scoredPairHighKey, scoredPairThirdKey],
      [scoredPairHighKey, scoredPairThirdKey]
    ]
  })}\n`);
  const corePairOutput = join(directory, "core-pair-summary.json");
  const corePairCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=hybrid-all",
    "--encoded-pair-orbit-limit=1",
    "--encoded-pair-selection=historical-core",
    "--lookahead-conflict-encoding=grouped-pb",
    "--learn-pair-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-pair-report=${corePairPath}`,
    `--output-dir=${join(directory, "core-pair")}`,
    `--report-output=${corePairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(corePairCegar.status, 0, corePairCegar.stderr);
  const corePairReport = JSON.parse(readFileSync(corePairOutput, "utf8"));
  assert.equal(corePairReport.encoded_pair_selection, "historical-core");
  assert.deepEqual(corePairReport.encoded_pair_orbit_keys, [scoredPairLowKey]);
  assert.equal(corePairReport.encoded_pair_historical_sets_covered, 1);

  const recentPairPath = join(directory, "recent-pair-coverability.json");
  writeFileSync(recentPairPath, `${JSON.stringify({
    pairs: [scoredPairLow, scoredPairHigh, scoredPairThird],
    pair_orbit_scores: {
      [scoredPairLowKey]: 5,
      [scoredPairHighKey]: 23,
      [scoredPairThirdKey]: 1
    },
    pair_defect_orbit_sets: [
      [scoredPairHighKey, scoredPairThirdKey],
      [scoredPairHighKey, scoredPairThirdKey],
      [scoredPairLowKey, scoredPairThirdKey]
    ]
  })}\n`);
  const recentPairOutput = join(directory, "recent-pair-summary.json");
  const recentPairCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=hybrid-all",
    "--encoded-pair-orbit-limit=2",
    "--encoded-pair-selection=recent-defect-cover",
    "--lookahead-conflict-encoding=grouped-pb",
    "--learn-pair-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-pair-report=${recentPairPath}`,
    `--output-dir=${join(directory, "recent-pair")}`,
    `--report-output=${recentPairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(recentPairCegar.status, 0, recentPairCegar.stderr);
  const recentPairReport = JSON.parse(readFileSync(recentPairOutput, "utf8"));
  assert.equal(recentPairReport.encoded_pair_selection, "recent-defect-cover");
  assert.deepEqual(new Set(recentPairReport.trials[0].encoded_pair_orbit_keys), new Set([
    scoredPairLowKey,
    scoredPairThirdKey
  ]));
  assert.equal(recentPairReport.trials[0].encoded_pair_recent_defect_size, 2);
  assert.equal(recentPairReport.trials[0].encoded_pair_recent_defect_orbits_selected, 2);
  assert.equal(recentPairReport.trials[0].encoded_pair_recent_defect_complete, true);

  const boundedRecentPairOutput = join(directory, "bounded-recent-pair-summary.json");
  const boundedRecentPairCegar = spawnSync(process.execPath, [
    cegar,
    "--id=p9-42947",
    "--outer-layer=1",
    "--inner-layer=2",
    "--iterations=1",
    "--max-placements=11",
    "--require-next-layer-coverability=true",
    "--tuple-enforcement=hybrid-all",
    "--encoded-pair-orbit-limit=2",
    "--encoded-pair-selection=recent-defect-cover",
    "--recent-defect-orbit-limit=1",
    "--lookahead-conflict-encoding=grouped-pb",
    "--learn-pair-coverability=true",
    "--z3-timeout-ms=10000",
    "--continuation-time-ms=10000",
    "--continuation-nodes=100000",
    `--python=${python}`,
    `--initial-pair-report=${recentPairPath}`,
    `--output-dir=${join(directory, "bounded-recent-pair")}`,
    `--report-output=${boundedRecentPairOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(boundedRecentPairCegar.status, 0, boundedRecentPairCegar.stderr);
  const boundedRecentPairReport = JSON.parse(readFileSync(boundedRecentPairOutput, "utf8"));
  assert.equal(boundedRecentPairReport.recent_defect_orbit_limit, 1);
  assert.equal(boundedRecentPairReport.trials[0].encoded_pair_recent_defect_size, 2);
  assert.equal(boundedRecentPairReport.trials[0].encoded_pair_recent_defect_orbits_selected, 1);
  assert.equal(boundedRecentPairReport.trials[0].encoded_pair_recent_defect_complete, false);

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

  const partialCellCache = join(directory, "partial-cell-formula-cache.smt2");
  const partialCellPath = join(directory, "partial-cell-coverability.json");
  writeFileSync(partialCellPath, `${JSON.stringify({ cells: [secondRing[0]] })}\n`);
  const partialCellArguments = [
    solver,
    `--key=${polycubeKey(candidate.voxels)}`,
    "--layer=1",
    "--timeout-ms=10000",
    "--backend=pb2bv-sat",
    "--max-placements=11",
    `--cell-coverability-report=${partialCellPath}`,
    `--formula-cache=${partialCellCache}`
  ];
  const partialCellMissOutput = join(directory, "partial-cell-cache-miss.json");
  const partialCellMiss = spawnSync(python, [
    ...partialCellArguments,
    `--output=${partialCellMissOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(partialCellMiss.status, 0, partialCellMiss.stderr);
  const partialCellMissReport = JSON.parse(readFileSync(partialCellMissOutput, "utf8"));
  assert.equal(partialCellMissReport.formula_cache_hit, false);
  assert.equal(partialCellMissReport.cell_coverability_constraints, 1);
  const partialCellHitOutput = join(directory, "partial-cell-cache-hit.json");
  const partialCellHit = spawnSync(python, [
    ...partialCellArguments,
    "--random-seed=2",
    `--output=${partialCellHitOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(partialCellHit.status, 0, partialCellHit.stderr);
  const partialCellHitReport = JSON.parse(readFileSync(partialCellHitOutput, "utf8"));
  assert.equal(partialCellHitReport.formula_cache_hit, true);
  assert.equal(partialCellHitReport.z3_status, partialCellMissReport.z3_status);
  assert.equal(partialCellHitReport.cell_coverability_constraints, 1);
  writeFileSync(partialCellPath, `${JSON.stringify({ cells: [secondRing[1]] })}\n`);
  const changedPartialCellOutput = join(directory, "partial-cell-cache-changed.json");
  const changedPartialCell = spawnSync(python, [
    ...partialCellArguments,
    `--output=${changedPartialCellOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(changedPartialCell.status, 0, changedPartialCell.stderr);
  assert.equal(
    JSON.parse(readFileSync(changedPartialCellOutput, "utf8")).formula_cache_hit,
    false,
    "changing the exact partial cell set must invalidate the formula cache"
  );
} finally {
  rmSync(directory, { recursive: true, force: true });
}

console.log("polycube-corona-z3-cegar regressions passed");
