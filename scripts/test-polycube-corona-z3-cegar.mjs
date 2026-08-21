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
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === "p9-42947");
assert.ok(candidate);

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
    `--output=${boundedOutput}`
  ], { encoding: "utf8", timeout: 30_000 });
  assert.equal(bounded.status, 0, bounded.stderr);
  const boundedReport = JSON.parse(readFileSync(boundedOutput, "utf8"));
  assert.equal(boundedReport.z3_status, "unsat");
  assert.equal(boundedReport.classification, "placement_bound_exhausted");
  assert.equal(boundedReport.max_placements, 1);
  assert.match(boundedReport.warning, /not a non-tiling or aperiodicity certificate/);

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
} finally {
  rmSync(directory, { recursive: true, force: true });
}

console.log("polycube-corona-z3-cegar regressions passed");
